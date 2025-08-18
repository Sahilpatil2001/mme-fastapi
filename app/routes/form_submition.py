
# app/routes/answers.py
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List
from app.models.answers import StepAnswer, SubmissionCreate, SubmissionResponse, PyObjectId
from app.db.db import answers_collection  # your MongoDB collection
from bson import ObjectId
import logging

router = APIRouter()


# This is working code 
@router.post("/submit-form", response_model=SubmissionResponse, status_code=201)
async def submit_form(request: Request, payload: SubmissionCreate):
    try:
        user = getattr(request.state, "user", None)
        if not user or not user.get("uid"):
            raise HTTPException(status_code=401, detail="User ID is missing in token")

        if not payload.answers or len(payload.answers) == 0:
            raise HTTPException(status_code=400, detail="Answers are required")

        submission_doc = {
            "userId": user["uid"],
            "answers": [answer.dict() for answer in payload.answers]
        }

        result = answers_collection.insert_one(submission_doc)

        # Convert ObjectIds to strings for Pydantic
        submission_doc["_id"] = str(result.inserted_id)
        # submission_doc["userId"] = str(submission_doc["userId"])

        return submission_doc

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Submission error: {e}")
        raise HTTPException(status_code=500, detail="Server error")
