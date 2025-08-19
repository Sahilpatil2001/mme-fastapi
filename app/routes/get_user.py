# app/routes/users.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/get-user")
async def get_user(request: Request):
    # User is attached by FirebaseAuthMiddleware
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # isplay name → fallback to email
    display_name = (
        user.get("name")
        or user.get("displayName")
        or (user.get("email").split("@")[0] if user.get("email") else None)
    )
    

    return JSONResponse(
        content={
            "uid": str(user.get("uid")),
            "email": user.get("email"),
            "name": display_name,  # ✅ fallback logic
            "photoURL": user.get("photoURL"),
            "isGoogleUser": user.get("isGoogleUser", False),
        }
    )
