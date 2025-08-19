from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from firebase_admin import auth as admin_auth
from app.db.db import users_collection

# Endpoints that don't require authentication
PUBLIC_PATHS = ["/api/register", "/api/login", "/docs", "/openapi.json"]

class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow OPTIONS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for public endpoints
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)

        # Get Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="No token provided")

        # Expect format: "Bearer <firebase_token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header format")

        fb_token = parts[1]  # Firebase ID token from frontend

        try:
            # Verify Firebase ID token
            decoded_token = admin_auth.verify_id_token(fb_token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")

            # Fetch user from MongoDB (must await with Motor!)
            user = await users_collection.find_one({"uid": uid}, {"password": 0})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Attach user to request state
            request.state.user = user

        except Exception as e:
            print("Firebase token verification failed:", e)
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return await call_next(request)
