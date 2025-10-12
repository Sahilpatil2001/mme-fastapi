# main.py
from fastapi import FastAPI
from app.routes import auth
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.auth_middleware import FirebaseAuthMiddleware
from app.routes import (
    auth,
    form_submition,
    core_settings,
    get_user,
    voices,
    loggedin_user,
    merge_audio,
    chatgpt  # 👈 import your new ChatGPT route
)
app = FastAPI(title="Firebase Auth API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# -------- The Auth Middleware -----------
app.add_middleware(FirebaseAuthMiddleware)


# Routes
app.include_router(auth.router, tags=["Authentication"])
app.include_router(auth.router, prefix="/api")
app.include_router(get_user.router, prefix="/api")
app.include_router(loggedin_user.router, prefix="/api")
app.include_router(merge_audio.router, prefix="/api")
app.include_router(form_submition.router, prefix="/api", tags=["Form"])
app.include_router(voices.router, prefix="/api")
app.include_router(core_settings.router, prefix="/api/admin", tags=["Settings"])
app.include_router(chatgpt.router)
