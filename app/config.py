import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

load_dotenv()

# Load secrets from .env
JWT_SECRET = os.getenv("JWT_SECRET")
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

# Ensure SERVICE_ACCOUNT_PATH exists
if not SERVICE_ACCOUNT_PATH:
    raise FileNotFoundError("FIREBASE_SERVICE_ACCOUNT_JSON is not set in .env")

# Convert relative path -> absolute path
if not os.path.isabs(SERVICE_ACCOUNT_PATH):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # go 1 level up (root)
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, SERVICE_ACCOUNT_PATH)

if not os.path.exists(SERVICE_ACCOUNT_PATH):
    raise FileNotFoundError(f"Firebase service account key not found: {SERVICE_ACCOUNT_PATH}")

# Initialize Firebase Admin SDK (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
