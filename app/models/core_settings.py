from pydantic import BaseModel, Field, validator
from typing import List

class ElevenLabsSettings(BaseModel):
    model_id: str
    stability: float
    speed: float
    style: float
    voiceTags: List[str]

    @validator("voiceTags", pre=True)
    def split_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",")]
        return v

class CoreSettings(BaseModel):
    id: str = Field(default="singleton-settings", alias="_id")
    elevenLabsSettings: ElevenLabsSettings
    gptScriptStageOne: str
    gptScriptStageTwo: str
    demoAudioScript: str

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        # Reorder manually
        return {
            "_id": d["_id"],
            "elevenLabsSettings": d["elevenLabsSettings"],
            "gptScriptStageOne": d["gptScriptStageOne"],
            "gptScriptStageTwo": d["gptScriptStageTwo"],
            "demoAudioScript": d["demoAudioScript"],
        }
