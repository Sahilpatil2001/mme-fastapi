# full GPT script generation (no ElevenLabs audio)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.db import core_settings_collection
from openai import OpenAI
import os

load_dotenv()

router = APIRouter(prefix="/api", tags=["ChatGPT"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_gpt(payload: ChatRequest):
    try:
        # 🔹 Fetch admin settings (for prompt context)
        settings = await core_settings_collection.find_one({"_id": "singleton-settings"})
        if not settings:
            raise HTTPException(status_code=404, detail="Admin settings not found")

        gpt_stage1 = settings.get("gptScriptStageOne", "")
        gpt_stage2 = settings.get("gptScriptStageTwo", "")
        demo_audio = settings.get("demoAudioScript", "")

        # 🔹 Construct the prompt
        final_prompt = f"""
You are an expert voice script writer. 
Generate a **TTS-ready narration script** with natural pauses and clear pacing for voiceover.

Use formatting cues like:
- [Pause 1s]
- [Pause 2s]
- [Soft tone]
- [Emphasis]
Keep it natural and human-like.

User Message:
{payload.message}

Admin Context:
Stage 1: {gpt_stage1}
Stage 2: {gpt_stage2}
Demo Audio Script: {demo_audio}
"""

        print("🧠 Sending prompt to GPT...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate natural, human-like TTS narration scripts."},
                {"role": "user", "content": final_prompt},
            ],
        )

        gpt_output = response.choices[0].message.content.strip()
        print("✅ GPT Output:", gpt_output)

        return {
            "success": True,
            "gpt_script": gpt_output,
            "message": "GPT script generated successfully."
        }

    except Exception as e:
        print("❌ Error in chat_with_gpt:", str(e))
        raise HTTPException(status_code=500, detail=f"GPT generation failed: {str(e)}")
