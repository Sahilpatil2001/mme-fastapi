from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.elevenlabs_service import get_all_voices

router = APIRouter()

@router.get("/voices")
async def get_voices():
    try:
        voices = get_all_voices()
        return JSONResponse(content={"voices": [v.dict() for v in voices]})
    except Exception as e:
        print("Error fetching voices:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch voices")
