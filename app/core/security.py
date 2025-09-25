import os
import time
from fastapi import HTTPException, Request
from firebase_admin import auth as admin_auth
MAX_CLOCK_SKEW_SECONDS = 5

# ✅ Decode Firebase token only
def decode_firebase_token(token: str):
    try:
        decoded_token = admin_auth.verify_id_token(token)  

          # Manually allow small clock skew
        now = int(time.time())
        if "iat" in decoded_token and decoded_token["iat"] > now + MAX_CLOCK_SKEW_SECONDS:
            raise HTTPException(
                status_code=401,
                detail="Invalid Firebase token: Token issued in the future (clock skew).",
            )
        
        return {"uid": decoded_token["uid"], "email": decoded_token.get("email")}
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {e}")

# ✅ Extract Firebase token from request headers
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header.split(" ")[1]

    print("🔑 Incoming Firebase token (first 50 chars):", token[:50])  # DEBUG

    return decode_firebase_token(token)
