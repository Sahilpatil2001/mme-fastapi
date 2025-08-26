# # app/models/submission.py
from pydantic import BaseModel, Field
from typing import List, Any
from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

# ---------------------------
# Custom ObjectId for Pydantic v2
# ---------------------------
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

# ---------------------------
# Step Answer Model
# ---------------------------
class StepAnswer(BaseModel):
    stepNumber: int
    stepTitle: str
    question: str
    answer: Any

# ---------------------------
# Request Model
# ---------------------------
class SubmissionCreate(BaseModel):
    answers: List[StepAnswer]

# ---------------------------
# Response Model
# ---------------------------
class SubmissionResponse(BaseModel):
    id: str = Field(..., alias="_id")
    userId: str
    answers: List[StepAnswer]


    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}




# # # NEw Code 
# # # app/routes/form_submission.py
# from fastapi import APIRouter, Request, HTTPException
# from app.models.answers import SubmissionCreate, SubmissionResponse
# from app.db.db import answers_collection
# import logging

# router = APIRouter()

# @router.post("/submit-form", response_model=SubmissionResponse, status_code=201)
# async def submit_form(request: Request, payload: SubmissionCreate):
#     try:
#         user = getattr(request.state, "user", None)
#         if not user or not user.get("uid"):
#             raise HTTPException(status_code=401, detail="User ID is missing in token")

#         if not payload.answers or len(payload.answers) == 0:
#             raise HTTPException(status_code=400, detail="Answers are required")

#         # Build the MongoDB doc (don’t add _id manually, Mongo will handle it)
#         submission_doc = {
#             "userId": user["uid"],
#             "answers": [answer.dict() for answer in payload.answers],
#         }

#         result = await answers_collection.insert_one(submission_doc)

#         # Response should match SubmissionResponse
#         response_doc = {
#             "id": str(result.inserted_id),   # ✅ use "id"
#             "userId": submission_doc["userId"],
#             "answers": submission_doc["answers"],
#         }

#         return response_doc

#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Submission error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))
