from firebase_admin import auth as admin_auth, exceptions
from jose import jwt
from datetime import datetime, timedelta
from app.config import JWT_SECRET


# -------------------------
# Firebase Service Functions
# -------------------------

def create_user(uid: str = None, email: str = None, name: str = None, photo_url: str = None):
    """
    Create a new Firebase user.
    """
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
    """
    Fetch a Firebase user by email. Returns None if not found.
    """
    try:
        return admin_auth.get_user_by_email(email)
    except exceptions.NotFoundError:
        return None
    except Exception as e:
        raise RuntimeError(f"Error fetching user by email: {str(e)}")


def verify_user(uid: str, email: str):
    """
    Ensure UID matches the given email’s Firebase user.
    """
    user = get_user_by_email(email)
    if not user:
        return None
    if user.uid != uid:
        raise ValueError("Firebase UID mismatch.")
    return user


def generate_token(uid: str, email: str, expires_in_days: int = 7):
    """
    Generate JWT token for a Firebase user.
    """
    token_payload = {
        "id": uid,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=expires_in_days)
    }
    return jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
