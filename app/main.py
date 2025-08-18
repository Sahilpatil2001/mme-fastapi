from fastapi import FastAPI
from app.routes import auth
from fastapi.middleware.cors import CORSMiddleware
from app.middlewares.auth_middleware import AuthMiddleware
from app.routes import form_submition

app = FastAPI(title="Firebase Auth API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# -------- The Auth Middleware -----------
app.add_middleware(AuthMiddleware)


# Routes

app.include_router(auth.router, prefix="/api")
app.include_router(form_submition.router, prefix="/api")
# Include routes
app.include_router(auth.router, tags=["Authentication"])

