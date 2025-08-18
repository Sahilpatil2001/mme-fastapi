from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

# Helper to handle MongoDB ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ElevenLabsSettings(BaseModel):
    model_id: str
    stability: float
    speed: float
    style: float
    voiceTags: str  # Use List[str] if you want an array


class CoreSettings(BaseModel):
    id: Optional[str] = Field(default="singleton-settings", alias="_id")
    elevenLabsSettings: ElevenLabsSettings
    gptScriptStageOne: str
    gptScriptStageTwo: str
    demoAudioScript: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
