# from fastapi import APIRouter, HTTPException, status, Depends,Request
# from fastapi.responses import JSONResponse
# from datetime import datetime, date
# import bcrypt
# import os
# from jose import jwt, JWTError
# from app.config import JWT_SECRET
# from app.models.users import User
# from app.db.db import users_collection
# from app.services import firebase_service


# router = APIRouter()


# # ----------------------------
# # Registration
# # ----------------------------
# @router.post("/register")
# async def register_user(user: User):
#     try:
#         # Detect Google registration
#         is_google_user = bool(user.uid and not user.password)

#         # Validation
#         if is_google_user:
#             if not user.email or not user.uid or not user.firstName:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Missing required fields for Google registration: email, uid, firstName"
#                 )
#         else:
#             required = ["firstName", "lastName", "email", "password", "dob", "gender"]
#             missing = [f for f in required if not getattr(user, f)]
#             if missing:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"Missing required fields for non-Google user: {', '.join(missing)}"
#                 )

#         email = user.email
#         uid = user.uid
#         name = f"{user.firstName or ''} {user.lastName or ''}".strip()
#         photo_url = user.photoURL or None

#         # Check if user already in MongoDB
#         if users_collection.find_one({"email": email}):
#             return JSONResponse(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 content={"message": "User already exists in database."}
#             )

#         # Check Firebase
#         if firebase_service.get_user_by_email(email):
#             return JSONResponse(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 content={"message": "User already exists in Firebase. Try logging in."}
#             )

#         # Create Firebase user
#         firebase_user = firebase_service.create_user(
#             uid=uid or None,
#             email=email,
#             name=name,
#             photo_url=photo_url
#         )

#         # Prepare MongoDB document
#         mongo_user = user.dict()
#         mongo_user["uid"] = firebase_user.uid
#         mongo_user["createdAt"] = datetime.utcnow()
#         mongo_user["isGoogleUser"] = is_google_user

#         # Convert dob to datetime
#         if mongo_user.get("dob") and isinstance(mongo_user["dob"], date):
#             mongo_user["dob"] = datetime.combine(mongo_user["dob"], datetime.min.time())

#         # Hash password if not Google signup
#         if not is_google_user:
#             mongo_user["password"] = bcrypt.hashpw(
#                 mongo_user["password"].encode("utf-8"), bcrypt.gensalt()
#             ).decode("utf-8")
#         else:
#             mongo_user["password"] = None

#         users_collection.insert_one(mongo_user)

#         # Generate JWT token
#         token = firebase_service.generate_token(firebase_user.uid, firebase_user.email)

#         return JSONResponse(
#             status_code=status.HTTP_201_CREATED,
#             content={
#                 "success": True,
#                 "message": "Registration successful",
#                 "token": token,
#                 "user": {
#                     "id": firebase_user.uid,
#                     "email": firebase_user.email,
#                     "name": firebase_user.display_name,
#                     "photoURL": firebase_user.photo_url,
#                     "isGoogleUser": is_google_user
#                 }
#             }
#         )

#     except Exception as err:
#         print("Register Error:", err)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(err)
#         )


# # ----------------------------
# # Login
# # ----------------------------
# @router.post("/login")
# async def login_user(user: User):
#     try:
#         email = user.email
#         uid = user.uid
#         password = user.password

#         is_google_login = uid is not None and password is None

#         # Check Mongo
#         mongo_user = users_collection.find_one({"email": email})
#         if not mongo_user:
#             return JSONResponse(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 content={"message": "User not found. Please register first."}
#             )

#         # Check Firebase
#         firebase_user = firebase_service.get_user_by_email(email)
#         if not firebase_user:
#             return JSONResponse(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 content={"message": "User not found in Firebase. Please register first."}
#             )

#         # Google login flow
#         if is_google_login:
#             if firebase_user.uid != uid:
#                 return JSONResponse(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     content={"message": "Invalid Google UID."}
#                 )

#         # Normal login flow
#         else:
#             if not password or not mongo_user.get("password"):
#                 return JSONResponse(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     content={"message": "Password is required for email login."}
#                 )
#             if not bcrypt.checkpw(password.encode("utf-8"), mongo_user["password"].encode("utf-8")):
#                 return JSONResponse(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     content={"message": "Invalid email or password."}
#                 )

#         # Generate JWT token
#         token = firebase_service.generate_token(firebase_user.uid, firebase_user.email)

#         return JSONResponse(
#             status_code=status.HTTP_200_OK,
#             content={
#                 "success": True,
#                 "message": "Login successful",
#                 "token": token,
#                 "user": {
#                     "id": firebase_user.uid,
#                     "email": firebase_user.email,
#                     "name": firebase_user.display_name or f"{mongo_user.get('firstName', '')} {mongo_user.get('lastName', '')}".strip(),
#                     "photoURL": firebase_user.photo_url or mongo_user.get("photoURL"),
#                     "isGoogleUser": mongo_user.get("isGoogleUser", False)
#                 }
#             }
#         )

#     except Exception as err:
#         print("Login Error:", err)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Server error during login"
#         )
    

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, date
import bcrypt
from app.config import JWT_SECRET
from app.models.users import User
from app.db.db import users_collection
from app.services import firebase_service

router = APIRouter()


# ----------------------------
# Registration
# ----------------------------
@router.post("/register")
async def register_user(user: User):
    try:
        is_google_user = bool(user.uid and not user.password)

        # Required fields check
        if is_google_user:
            missing = [f for f in ["email", "uid", "firstName"] if not getattr(user, f)]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields for Google registration: {', '.join(missing)}"
                )
        else:
            required = ["firstName", "lastName", "email", "password", "dob", "gender"]
            missing = [f for f in required if not getattr(user, f)]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields for non-Google user: {', '.join(missing)}"
                )

        email = user.email
        uid = user.uid
        name = f"{user.firstName or ''} {user.lastName or ''}".strip()
        photo_url = user.photoURL or None

        # Check MongoDB first
        if users_collection.find_one({"email": email}):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "User already exists in database. Try logging in."}
            )

        # Try fetching Firebase user but don’t fail if it doesn’t exist
        firebase_user = firebase_service.get_user_by_email(email)
        if not firebase_user:
            # Create Firebase user only if not already exists
            firebase_user = firebase_service.create_user(
                uid=uid or None,
                email=email,
                name=name,
                photo_url=photo_url
            )

        # Prepare MongoDB document
        mongo_user = user.dict()
        mongo_user["uid"] = firebase_user.uid
        mongo_user["createdAt"] = datetime.utcnow()
        mongo_user["isGoogleUser"] = is_google_user

        # Convert dob to datetime
        if mongo_user.get("dob") and isinstance(mongo_user["dob"], date):
            mongo_user["dob"] = datetime.combine(mongo_user["dob"], datetime.min.time())

        # Hash password for non-Google signup
        if not is_google_user:
            mongo_user["password"] = bcrypt.hashpw(
                mongo_user["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        else:
            mongo_user["password"] = None

        users_collection.insert_one(mongo_user)

        # Generate JWT token
        token = firebase_service.generate_token(firebase_user.uid, firebase_user.email)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "success": True,
                "message": "Registration successful",
                "token": token,
                "user": {
                    "id": firebase_user.uid,
                    "email": firebase_user.email,
                    "name": firebase_user.display_name,
                    "photoURL": firebase_user.photo_url,
                    "isGoogleUser": is_google_user
                }
            }
        )

    except Exception as err:
        print("Register Error:", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(err)
        )


# ----------------------------
# Login
# ----------------------------
@router.post("/login")
async def login_user(user: User):
    try:
        email = user.email
        uid = user.uid
        password = user.password

        is_google_login = uid is not None and password is None

        # Check MongoDB
        mongo_user = users_collection.find_one({"email": email})
        if not mongo_user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found. Please register first."}
            )

        # Check Firebase
        firebase_user = firebase_service.get_user_by_email(email)
        if not firebase_user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "User not found in Firebase. Please register first."}
            )

        # Google login flow
        if is_google_login:
            if firebase_user.uid != uid:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"message": "Invalid Google UID."}
                )

        # Normal login flow
        else:
            if not password or not mongo_user.get("password"):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": "Password is required for email login."}
                )
            if not bcrypt.checkpw(password.encode("utf-8"), mongo_user["password"].encode("utf-8")):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"message": "Invalid email or password."}
                )

        # Generate JWT token
        token = firebase_service.generate_token(firebase_user.uid, firebase_user.email)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": firebase_user.uid,
                    "email": firebase_user.email,
                    "name": firebase_user.display_name or f"{mongo_user.get('firstName', '')} {mongo_user.get('lastName', '')}".strip(),
                    "photoURL": firebase_user.photo_url or mongo_user.get("photoURL"),
                    "isGoogleUser": mongo_user.get("isGoogleUser", False)
                }
            }
        )

    except Exception as err:
        print("Login Error:", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error during login"
        )
