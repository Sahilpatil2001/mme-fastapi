# app/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from firebase_admin import auth as admin_auth
from datetime import datetime, date
import bcrypt
from app.models.users import User
from app.db.db import users_collection
from app.services import firebase_service

router = APIRouter()


# ----------------------------
# Registration
# ----------------------------
@router.post("/register")
async def register_user(user: User, request: Request):
    try:
        is_google_user = bool(user.uid and not user.password)

        required = (
            ["email", "uid", "firstName"] if is_google_user
            else ["firstName", "lastName", "email", "password", "dob", "gender"]
        )
        missing = [f for f in required if not getattr(user, f)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        # Check if user exists in MongoDB
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists. Please log in."
            )

        # -------------------------------
        # Case: Google registration
        # -------------------------------
        if is_google_user:
            try:
                firebase_user = admin_auth.get_user_by_email(user.email)
            except:
                firebase_user = admin_auth.create_user(
                    uid=user.uid,
                    email=user.email,
                    display_name=f"{user.firstName or ''} {user.lastName or ''}".strip(),
                    photo_url=user.photoURL or None
                )
            uid = firebase_user.uid
            hashed_pw = None

        # -------------------------------
        # Case: Manual registration
        # -------------------------------
        else:
            # 1. Create user in Firebase
            firebase_user = admin_auth.create_user(
                email=user.email,
                password=user.password,
                display_name=f"{user.firstName or ''} {user.lastName or ''}".strip(),
            )
            uid = firebase_user.uid

            # 2. Hash password for MongoDB (not same as Firebase storage)
            hashed_pw = bcrypt.hashpw(
                user.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

        # -------------------------------
        # Save to MongoDB
        # -------------------------------
        mongo_user = user.dict()
        mongo_user["uid"] = uid
        mongo_user["password"] = hashed_pw
        mongo_user["createdAt"] = datetime.utcnow()
        mongo_user["isGoogleUser"] = is_google_user

        if mongo_user.get("dob") and isinstance(mongo_user["dob"], date):
            mongo_user["dob"] = datetime.combine(mongo_user["dob"], datetime.min.time())

        await users_collection.insert_one(mongo_user)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Registration successful",
                "user": {
                    "id": uid,
                    "email": user.email,
                    "firstName": user.firstName,
                    "lastName": user.lastName,
                    "photoURL": user.photoURL,
                    "isGoogleUser": is_google_user,
                }
            }
        )

    except HTTPException:
        raise
    except Exception as err:
        print("Register Error:", err)
        raise HTTPException(status_code=500, detail="Server error during registration")



# ----------------------------
# Login
# ----------------------------
@router.post("/login")
async def login_user(request: Request):
    """
    Login with Firebase only.
    Expect client to send Firebase ID token in Authorization header.
    """
    try:
        # 🔑 Expect Firebase ID token from frontend
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Firebase ID token")

        fb_token = auth_header.split(" ")[1]

        # ✅ Verify Firebase token
        try:
            decoded = admin_auth.verify_id_token(fb_token)
        except Exception as e:
            print("❌ Firebase token verification failed:", repr(e))
            raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

        uid = decoded.get("uid")
        email = decoded.get("email")

        # 🔍 Ensure user exists in MongoDB
        mongo_user = await users_collection.find_one({"uid": uid})
        if not mongo_user:
            new_user = {
                "uid": uid,
                "email": email,
                "firstName": decoded.get("name", "").split(" ")[0] if decoded.get("name") else None,
                "lastName": decoded.get("name", "").split(" ")[1] if decoded.get("name") and len(decoded.get("name").split(" ")) > 1 else None,
                "photoURL": decoded.get("picture"),
                "isGoogleUser": bool(decoded.get("firebase", {}).get("sign_in_provider") == "google.com"),
                "createdAt": datetime.utcnow(),
            }
            await users_collection.insert_one(new_user)
            mongo_user = new_user

        # ✅ Return user profile (no backend token)
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": mongo_user["uid"],
                    "email": mongo_user["email"],
                    "firstName": mongo_user.get("firstName"),
                    "lastName": mongo_user.get("lastName"),
                    "photoURL": mongo_user.get("photoURL"),
                    "isGoogleUser": mongo_user.get("isGoogleUser", False),
                }
            }
        )

    except HTTPException:
        raise
    except Exception as err:
        print("🔥 Login Error:", err)
        raise HTTPException(status_code=500, detail="Server error during login")