# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from openai import OpenAI
# import os

# load_dotenv()

# router = APIRouter(prefix="/api", tags=["ChatGPT"])

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# class ChatRequest(BaseModel):
#     message: str

# @router.post("/chat")
# async def chat_with_gpt(request: ChatRequest):
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": request.message}
#             ],
#         )
#         return {"reply": response.choices[0].message.content}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# ----------------//////==========----------------------------


# # new code for gpt working with eleven-labs settings
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from dotenv import load_dotenv
# from app.db.db import core_settings_collection
# from app.models.answers import SubmissionCreate
# # from app.core.security import get_current_user
# from openai import OpenAI
# import os

# load_dotenv()

# router = APIRouter(prefix="/api", tags=["ChatGPT"])

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# class ChatRequest(BaseModel):
#     message: str

# @router.post("/chat")
# async def chat_with_gpt(payload: ChatRequest):
#     try:
#         # ✅ Fetch Admin Settings
#         settings = await core_settings_collection.find_one({"_id": "singleton-settings"})
#         if not settings:
#             raise HTTPException(status_code=404, detail="Admin settings not found")

#         eleven_labs = settings.get("elevenLabsSettings", {})
#         gpt_stage1 = settings.get("gptScriptStageOne", "")
#         gpt_stage2 = settings.get("gptScriptStageTwo", "")
#         demo_audio = settings.get("demoAudioScript", "")

#         # ✅ Build GPT Prompt (use the provided message directly)
#         final_prompt = f"""
# You are an AI creative assistant.

# User Message:
# {payload.message}

# Here are the current ElevenLabs settings:
# - Model ID: {eleven_labs.get('model_id', 'N/A')}
# - Stability: {eleven_labs.get('stability', 'N/A')}
# - Speed: {eleven_labs.get('speed', 'N/A')}
# - Style: {eleven_labs.get('style', 'N/A')}
# - Voice Tags: {eleven_labs.get('voiceTags', 'N/A')}

# Existing GPT scripts from Admin:
# Stage 1 Script: {gpt_stage1}
# Stage 2 Script: {gpt_stage2}
# Demo Audio Script: {demo_audio}

# 🎯 TASK: Based on the user's input and admin settings, generate a creative GPT prompt for personalized voice or content output.
# """

#         # ✅ Call GPT
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You generate smart and creative prompts for voice AI systems."},
#                 {"role": "user", "content": final_prompt},
#             ],
#         )

#         gpt_output = response.choices[0].message.content

#         return {
#             "success": True,
#             "reply": gpt_output,

#             "basePromptUsed": final_prompt
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"GPT generation failed: {str(e)}")




# full GPT + ElevenLabs integration
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.db import core_settings_collection
from openai import OpenAI
import requests
import os
import tempfile

load_dotenv()

router = APIRouter(prefix="/api", tags=["ChatGPT"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_gpt(payload: ChatRequest):
    try:
        settings = await core_settings_collection.find_one({"_id": "singleton-settings"})
        if not settings:
            raise HTTPException(status_code=404, detail="Admin settings not found")

        eleven_labs = settings.get("elevenLabsSettings", {})
        gpt_stage1 = settings.get("gptScriptStageOne", "")
        gpt_stage2 = settings.get("gptScriptStageTwo", "")
        demo_audio = settings.get("demoAudioScript", "")

        final_prompt = f"""
You are an AI creative assistant.

User Message:
{payload.message}

Here are the current ElevenLabs settings:
{eleven_labs}

Existing GPT scripts from Admin:
Stage 1: {gpt_stage1}
Stage 2: {gpt_stage2}
Demo Audio Script: {demo_audio}

🎯 TASK: Based on the user's input and admin settings, generate a creative, natural, TTS-ready script.
"""

        print("🧠 Sending prompt to GPT...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate voice narration scripts formatted for ElevenLabs TTS."},
                {"role": "user", "content": final_prompt},
            ],
        )

        gpt_output = response.choices[0].message.content.strip()
        print("✅ GPT Output:", gpt_output)

        voice_id = eleven_labs.get("voice_id", "EXAVITQu4vr4xnSDxMaL")
        model_id = eleven_labs.get("model_id", "eleven_turbo_v2")

        tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }

        tts_payload = {
            "model_id": model_id,
            "text": gpt_output,
            "voice_settings": {
                "stability": float(eleven_labs.get("stability", 0.5)),
                "similarity_boost": float(eleven_labs.get("similarity_boost", 0.5))
            }
        }

        print("🎙️ Sending to ElevenLabs...")
        tts_response = requests.post(tts_url, json=tts_payload, headers=headers)
        print("🔊 ElevenLabs Response:", tts_response.status_code, tts_response.text[:300])

        if tts_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"ElevenLabs API error: {tts_response.text}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(tts_response.content)
            temp_audio.flush()
        audio_path = temp_audio.name

        return {
            "success": True,
            "gpt_script": gpt_output,
            "audio_file": audio_path,
            "message": "GPT script generated and converted to ElevenLabs TTS successfully."
        }

    except Exception as e:
        print("❌ Error in chat_with_gpt:", str(e))
        raise HTTPException(status_code=500, detail=f"GPT or TTS generation failed: {str(e)}")


# @router.post("/chat")
# async def chat_with_gpt(payload: ChatRequest):
#     try:
#         # ✅ Step 1: Fetch admin settings
#         settings = await core_settings_collection.find_one({"_id": "singleton-settings"})
#         if not settings:
#             raise HTTPException(status_code=404, detail="Admin settings not found")

#         eleven_labs = settings.get("elevenLabsSettings", {})
#         gpt_stage1 = settings.get("gptScriptStageOne", "")
#         gpt_stage2 = settings.get("gptScriptStageTwo", "")
#         demo_audio = settings.get("demoAudioScript", "")

#         # ✅ Step 2: Build GPT prompt
#         final_prompt = f"""
# You are an AI creative assistant.

# User Message:
# {payload.message}

# Here are the current ElevenLabs settings:
# - Model ID: {eleven_labs.get('model_id', 'N/A')}
# - Stability: {eleven_labs.get('stability', 'N/A')}
# - Speed: {eleven_labs.get('speed', 'N/A')}
# - Style: {eleven_labs.get('style', 'N/A')}
# - Voice Tags: {eleven_labs.get('voiceTags', 'N/A')}

# Existing GPT scripts from Admin:
# Stage 1 Script: {gpt_stage1}
# Stage 2 Script: {gpt_stage2}
# Demo Audio Script: {demo_audio}

# 🎯 TASK: Based on the user's input and admin settings, generate a creative and natural TTS-ready script for ElevenLabs voice generation. Include pacing and emotion.
# """

#         # ✅ Step 3: Get GPT output
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You generate voice narration scripts formatted for ElevenLabs TTS."},
#                 {"role": "user", "content": final_prompt},
#             ],
#         )

#         gpt_output = response.choices[0].message.content.strip()

#         # ✅ Step 4: Prepare for ElevenLabs TTS
#         voice_id = eleven_labs.get("voice_id", "EXAVITQu4vr4xnSDxMaL")  # fallback voice
#         model_id = eleven_labs.get("model_id", "eleven_turbo_v2")

#         tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

#         headers = {
#             "xi-api-key": ELEVEN_API_KEY,
#             "Content-Type": "application/json"
#         }

#         tts_payload = {
#             "model_id": model_id,
#             "text": gpt_output,
#             "voice_settings": {
#                 "stability": float(eleven_labs.get("stability", 0.5)),
#                 "similarity_boost": float(eleven_labs.get("style", 0.5))
#             }
#         }

#         # ✅ Step 5: Call ElevenLabs API
#         tts_response = requests.post(tts_url, json=tts_payload, headers=headers)

#         if tts_response.status_code != 200:
#             raise HTTPException(status_code=500, detail=f"ElevenLabs API error: {tts_response.text}")

#         # ✅ Step 6: Save audio temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
#             temp_audio.write(tts_response.content)
#             audio_path = temp_audio.name

#         # ✅ Step 7: Return success response
#         return {
#             "success": True,
#             "gpt_script": gpt_output,
#             "audio_file": audio_path,
#             "message": "GPT script generated and converted to ElevenLabs TTS successfully."
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"GPT or TTS generation failed: {str(e)}")
