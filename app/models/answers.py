# # app/models/answers.py
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
