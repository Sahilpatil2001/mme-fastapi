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
        user.isGoogleUser = is_google_user

        # -----------------------------
        # Validate required fields
        # -----------------------------
        if is_google_user:
            required_fields = ["email", "uid", "firstName"]
        else:
            required_fields = ["firstName", "lastName", "email", "password", "dob", "gender"]

        missing = [field for field in required_fields if not getattr(user, field)]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing)}"
            )

        # -----------------------------
        # Check MongoDB for existing user
        # -----------------------------
        if await users_collection.find_one({"email": user.email}):
            raise HTTPException(status_code=400, detail="User already exists. Please log in.")

        # -----------------------------
        # Firebase user creation
        # -----------------------------
        uid = None
        hashed_pw = None

        if is_google_user:
            try:
                fb_user = admin_auth.get_user_by_email(user.email)
                uid = fb_user.uid
            except admin_auth.UserNotFoundError:
                fb_user = admin_auth.create_user(
                    uid=user.uid,
                    email=user.email,
                    display_name=f"{user.firstName} {user.lastName or ''}".strip(),
                    photo_url=user.photoURL or None,
                )
                uid = fb_user.uid
        else:
            try:
                fb_user = admin_auth.create_user(
                    email=user.email,
                    password=user.password,
                    display_name=f"{user.firstName} {user.lastName}".strip(),
                )
                uid = fb_user.uid
            except Exception as fb_err:
                if "EMAIL_EXISTS" in str(fb_err):
                    fb_user = admin_auth.get_user_by_email(user.email)
                    uid = fb_user.uid
                else:
                    raise HTTPException(status_code=500, detail=f"Firebase error: {fb_err}")

            # Hash password for MongoDB
            hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # -----------------------------
        # Prepare MongoDB user doc
        # -----------------------------
        mongo_user = user.dict()
        mongo_user.update({
            "uid": uid,
            "password": hashed_pw,
            "isGoogleUser": is_google_user,
            "createdAt": datetime.utcnow()
        })

        # Convert dob string to datetime
        dob = mongo_user.get("dob")
        if dob:
            if isinstance(dob, str):
                try:
                    mongo_user["dob"] = datetime.fromisoformat(dob)
                except Exception:
                    mongo_user["dob"] = None
            elif isinstance(dob, date):
                mongo_user["dob"] = datetime.combine(dob, datetime.min.time())

        # -----------------------------
        # Insert into MongoDB
        # -----------------------------
        await users_collection.insert_one(mongo_user)

        # -----------------------------
        # Success Response
        # -----------------------------
        return JSONResponse(
            status_code=201,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# ----------------------------
# Login
# ----------------------------
@router.post("/login")
async def login_user(request: Request):
    """
    Login user with Firebase token verification.
    Backend ensures user exists in MongoDB.
    """
    try:
        # -----------------------------
        # Get Firebase ID token from headers
        # -----------------------------
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Firebase ID token")

        fb_token = auth_header.split(" ")[1]

        # -----------------------------
        # Verify Firebase token
        # -----------------------------
        try:
            decoded = admin_auth.verify_id_token(fb_token)
        except Exception as e:
            
            print("❌ Firebase token verification failed:", repr(e))
            raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

        uid = decoded.get("uid")
        email = decoded.get("email")
        display_name = decoded.get("name") or ""
        first_name = display_name.split(" ")[0] if display_name else None
        last_name = display_name.split(" ")[1] if display_name and len(display_name.split(" ")) > 1 else None
        photo_url = decoded.get("picture")
        is_google_user = decoded.get("firebase", {}).get("sign_in_provider") == "google.com"

        # -----------------------------
        # Ensure user exists in MongoDB
        # -----------------------------
        mongo_user = await users_collection.find_one({"uid": uid})

        # If Google login and user does not exist, create Mongo record
        if not mongo_user and is_google_user:
            mongo_user = {
                "uid": uid,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "photoURL": photo_url,
                "isGoogleUser": True,
                "createdAt": datetime.utcnow(),
                "password": None,
            }
            await users_collection.insert_one(mongo_user)

        # If manual login and user not in Mongo, error
        if not mongo_user:
            raise HTTPException(status_code=404, detail="User not found. Please register first.")

        # -----------------------------
        # Success response
        # -----------------------------
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

