from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import get_current_user  # 👈 reuse shared logic
from app.db.db import users_collection

# Routes that do NOT require auth
PUBLIC_PATHS = ["/api/register", "/api/login", "/docs", "/openapi.json"]

class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("👉 Request path:", request.url.path)

        # Allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for public endpoints
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)

        try:
            # 🔑 Decode token using security.py (Firebase OR backend JWT)
            user = get_current_user(request)

            # If Firebase, ensure the user exists in MongoDB
            if "uid" in user:
                db_user = await users_collection.find_one({"uid": user["uid"]}, {"password": 0})
                if not db_user:
                    return JSONResponse({"detail": "User not found"}, status_code=404)
                request.state.user = db_user
            else:
                # For backend JWT (already contains uid/email)
                request.state.user = user

        except Exception as e:
            print("🔥 Middleware auth error:", repr(e))
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        return await call_next(request)
