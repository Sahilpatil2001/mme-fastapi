from fastapi import HTTPException, APIRouter
from pymongo import ReturnDocument
from app.db.db import core_settings_collection
from app.models.core_settings import CoreSettings
from bson import ObjectId

router = APIRouter()

@router.put("/settings")
async def update_settings(payload: CoreSettings):
    try:
        data = payload.dict(by_alias=True)
        result = await core_settings_collection.find_one_and_update(
            {"_id": "singleton-settings"},
            {"$set": data},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to update settings")

        if isinstance(result.get("_id"), ObjectId):
            result["_id"] = str(result["_id"])

        return {"message": "Settings updated successfully", "data": result}
    except Exception as e:
        print("Error updating settings:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/settings")
async def get_settings():
    try:
        settings = await core_settings_collection.find_one({"_id": "singleton-settings"})
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        return {"success": True, "data": settings}
    except Exception as e:
        print("Error fetching settings:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
