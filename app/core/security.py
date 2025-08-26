import os
import jwt
from fastapi import HTTPException, Request
from firebase_admin import auth as admin_auth

JWT_SECRET = os.getenv("JWT_SECRET", "SECRET_KEY")
JWT_ALGORITHM = "HS256"

# ✅ Decode backend JWT
def decode_backend_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"uid": payload.get("uid"), "email": payload.get("email")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Backend token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid backend token")

# ✅ Decode Firebase token
def decode_firebase_token(token: str):
    try:
        decoded_token = admin_auth.verify_id_token(token)  # uses firebase_service init
        return {"uid": decoded_token["uid"], "email": decoded_token.get("email")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {e}")

# ✅ Extract from request headers
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header.split(" ")[1]

    print("🔑 Incoming token (first 50 chars):", token[:50])  # DEBUG

    # Try Firebase first
    try:
        user = decode_firebase_token(token)
        print("✅ Firebase user decoded:", user)  # DEBUG
        return user
    except Exception as e:
        print("❌ Firebase decode failed:", e)

    # Fallback: Backend JWT
    try:
        user = decode_backend_jwt(token)
        print("✅ Backend JWT decoded:", user)  # DEBUG
        return user
    except Exception as e:
        print("❌ Backend decode failed:", e)
        raise HTTPException(status_code=401, detail="Invalid token (Firebase or Backend)")