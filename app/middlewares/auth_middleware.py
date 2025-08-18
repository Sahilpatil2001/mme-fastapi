from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from firebase_admin import auth as admin_auth
from app.db.db import users_collection

PUBLIC_PATHS = ["/api/register", "/api/login", "/docs", "/openapi.json"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # OPTIONS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Public endpoints
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)

        # Read Authorization header
        auth_header = request.headers.get("authorization")
        # print("Authorization header:", auth_header)  # debug

        if not auth_header:
            raise HTTPException(status_code=401, detail="No token provided")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth header format")

        token = parts[1]

        try:
            decoded_token = admin_auth.verify_id_token(token)
            uid = decoded_token.get("uid")
            email = decoded_token.get("email")

            user = users_collection.find_one({"uid": uid}, {"password": 0})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            request.state.user = user

        except Exception as e:
            print("Token verification failed:", e)
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return await call_next(request)
