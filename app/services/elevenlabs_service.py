import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

def get_all_voices():
    """Fetch all available voices from ElevenLabs"""
    response = client.voices.get_all()
    return response.voices if response and hasattr(response, "voices") else []
