import os
from fastapi import HTTPException, Request
from firebase_admin import auth as admin_auth

# ✅ Decode Firebase token only
def decode_firebase_token(token: str):
    try:
        decoded_token = admin_auth.verify_id_token(token)  # uses firebase_service init
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
