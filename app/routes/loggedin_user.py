# app/routes/user.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from firebase_admin import auth as admin_auth
from datetime import datetime
from app.db.db import users_collection

router = APIRouter()

# ----------------------------
# Helper: Verify Firebase token
# ----------------------------
async def verify_token(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Firebase ID token")

    fb_token = auth_header.split(" ")[1]

    try:
        decoded = admin_auth.verify_id_token(fb_token)
        return decoded
    except Exception as e:
        print("❌ Token verification failed:", e)
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ----------------------------
# Get current user profile
# ----------------------------
@router.get("/user")
async def get_user(decoded: dict = Depends(verify_token)):
    uid = decoded.get("uid")
    user = await users_collection.find_one({"uid": uid})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 🔄 If Google user → refresh data from Firebase
    if user.get("isGoogleUser"):
        try:
            fb_user = admin_auth.get_user(uid)
            first_name = fb_user.display_name.split(" ")[0] if fb_user.display_name else ""
            last_name = (
                fb_user.display_name.split(" ")[1]
                if fb_user.display_name and len(fb_user.display_name.split(" ")) > 1
                else ""
            )

            # Update MongoDB record with latest Firebase values
            await users_collection.update_one(
                {"uid": uid},
                {
                    "$set": {
                        "firstName": first_name,
                        "lastName": last_name,
                        "photoURL": fb_user.photo_url,
                    }
                },
            )

            # refresh local doc
            user.update(
                {
                    "firstName": first_name,
                    "lastName": last_name,
                    "photoURL": fb_user.photo_url,
                }
            )
        except Exception as e:
            print("⚠️ Failed to refresh Google user from Firebase:", e)

    return {
        "name": user.get("firstName", ""),
        "fullName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
        "dob": user.get("dob"),
        "age": user.get("age", ""),
        "gender": user.get("gender", ""),
        "email": user.get("email", ""),
        "isGoogleUser": user.get("isGoogleUser", False),
        "photoURL": user.get("photoURL", ""),
    }


# ----------------------------
# Update user profile (only non-Google)
# ----------------------------
@router.put("/user/me")
async def update_user(request: Request, decoded: dict = Depends(verify_token)):
    uid = decoded.get("uid")
    body = await request.json()

    user = await users_collection.find_one({"uid": uid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ❌ Block manual update for Google users
    if user.get("isGoogleUser"):
        raise HTTPException(
            status_code=403,
            detail="Google user profile is managed by Firebase and cannot be updated manually.",
        )

    update_doc = {
        "firstName": body.get("name") or user.get("firstName"),
        "lastName": body.get("fullName", "").replace(user.get("firstName", ""), "").strip() or user.get("lastName"),
        "dob": body.get("dob") or user.get("dob"),
        "age": body.get("age") or user.get("age"),
        "gender": body.get("gender") or user.get("gender"),
        "photoURL": body.get("photoURL") or user.get("photoURL"),
    }

    await users_collection.update_one({"uid": uid}, {"$set": update_doc})

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Profile updated successfully",
            "user": update_doc,
        },
    )
