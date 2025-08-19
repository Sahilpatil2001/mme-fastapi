import firebase_admin
from firebase_admin import auth as admin_auth, credentials, exceptions
from datetime import datetime
import os

# -------------------------
# Initialize Firebase
# -------------------------
if not firebase_admin._apps:  # prevent re-initialization
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"))
    firebase_admin.initialize_app(cred)


# -------------------------
# Firebase Service Functions
# -------------------------

def create_user(uid: str = None, email: str = None, name: str = None, photo_url: str = None):
    try:
        user = admin_auth.create_user(
            uid=uid,
            email=email,
            display_name=name,
            photo_url=photo_url
        )
        return user
    except exceptions.AlreadyExistsError:
        raise ValueError("User already exists with this UID or email")
    except Exception as e:
        raise RuntimeError(f"Failed to create Firebase user: {str(e)}")


def get_user_by_email(email: str):
    try:
        return admin_auth.get_user_by_email(email)
    except exceptions.NotFoundError:
        return None
    except Exception as e:
        raise RuntimeError(f"Error fetching user by email: {str(e)}")


def verify_user(uid: str, email: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if user.uid != uid:
        raise ValueError("Firebase UID mismatch.")
    return user


def generate_firebase_custom_token(uid: str):
    try:
        custom_token_bytes = admin_auth.create_custom_token(uid)
        return custom_token_bytes.decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"Failed to generate Firebase custom token: {str(e)}")
