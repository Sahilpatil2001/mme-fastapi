# app/routes/form_submission.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.answers import SubmissionCreate, SubmissionResponse
from app.db.db import answers_collection
from bson import ObjectId
import logging

# ✅ Import the shared auth logic
from app.core.security import get_current_user  

router = APIRouter()

@router.post("/submit-form", response_model=SubmissionResponse, status_code=201)
async def submit_form(
    payload: SubmissionCreate,
    user: dict = Depends(get_current_user)   # 🔑 User automatically extracted
):
    try:
        # ✅ Ensure answers exist
        if not payload.answers or len(payload.answers) == 0:
            raise HTTPException(status_code=400, detail="Answers are required")

        # ✅ Build the submission doc
        submission_doc = {
            "userId": user["uid"],
            "answers": [answer.dict() for answer in payload.answers],
        }

        # ✅ Insert into Mongo
        result = await answers_collection.insert_one(submission_doc)
        submission_doc["_id"] = str(result.inserted_id)

        return submission_doc

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Submission error: {e}")
        raise HTTPException(status_code=500, detail="Server error")
