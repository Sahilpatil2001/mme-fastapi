# app/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from firebase_admin import auth as admin_auth
from datetime import datetime, timedelta, date
import bcrypt
import jwt
from app.config import JWT_SECRET
from app.models.users import User
from app.db.db import users_collection
from app.services import firebase_service

router = APIRouter()

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1


# ----------------------------
# Helper: Generate backend JWT
# ----------------------------
def create_backend_jwt(uid: str, email: str):
    payload = {
        "uid": uid,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


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

        # Check if user exists
        existing_user = await users_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists. Please log in."
            )

        # Case: Google registration
        if is_google_user:
            firebase_user = firebase_service.get_user_by_email(user.email)
            if not firebase_user:
                firebase_user = firebase_service.create_user(
                    uid=user.uid,
                    email=user.email,
                    name=f"{user.firstName or ''} {user.lastName or ''}".strip(),
                    photo_url=user.photoURL or None
                )
            uid = firebase_user.uid
            hashed_pw = None

        # Case: Normal registration
        else:
            uid = user.uid or str(datetime.utcnow().timestamp())  # fallback UID
            hashed_pw = bcrypt.hashpw(
                user.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

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
@router.post("/login")
async def login_user(user: User, request: Request):
    try:
        mongo_user = None

        # ----------------------------
        # Case 1: Google Login
        # ----------------------------
        if user.isGoogleUser or (user.uid and not user.password):
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Firebase token required for Google login"
                )

            fb_token = auth_header.split(" ")[1]
            

            try:
             print("🔑 Received Firebase token:", fb_token[:50], "...")
             decoded = admin_auth.verify_id_token(fb_token)
             print("✅ Decoded Firebase token:", decoded)
            
             # ✅ Verify Firebase ID token

                # decoded = admin_auth.verify_id_token(fb_token)
            except Exception as e:
                print("❌ Firebase token verification failed:", repr(e))
                raise HTTPException(status_code=401, detail="Invalid Firebase token")

            uid = decoded.get("uid")
            email = decoded.get("email")

            # ✅ Ensure user exists in Mongo
            mongo_user = await users_collection.find_one({"uid": uid})
            if not mongo_user:
                # auto-register new google user if not found
                new_user = {
                    "uid": uid,
                    "email": email,
                    "firstName": decoded.get("name", "").split(" ")[0] if decoded.get("name") else None,
                    "lastName": decoded.get("name", "").split(" ")[1] if decoded.get("name") and len(decoded.get("name").split(" ")) > 1 else None,
                    "photoURL": decoded.get("picture"),
                    "isGoogleUser": True,
                }
                await users_collection.insert_one(new_user)
                mongo_user = new_user

        # ----------------------------
        # Case 2: Manual Email/Password Login
        # ----------------------------
        else:
            if not user.email or not user.password:
                raise HTTPException(status_code=400, detail="Email and password required")

            mongo_user = await users_collection.find_one({"email": user.email})
            if not mongo_user:
                raise HTTPException(status_code=404, detail="User not found")

            if not mongo_user.get("password"):
                raise HTTPException(
                    status_code=400,
                    detail="This account was registered with Google. Use Google login."
                )

            if not bcrypt.checkpw(
                user.password.encode("utf-8"),
                mongo_user["password"].encode("utf-8")
            ):
                raise HTTPException(status_code=401, detail="Invalid credentials")

        # ✅ Issue backend JWT for both login types
        backend_token = create_backend_jwt(mongo_user["uid"], mongo_user["email"])

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Login successful",
                "backendToken": backend_token,
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
        print("Login Error:", err)
        raise HTTPException(status_code=500, detail="Server error during login")

