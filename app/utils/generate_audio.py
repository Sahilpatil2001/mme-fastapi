# utils/generate_audio.py
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load .env file

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

async def generate_audio(
    text: str,
    output_path: str,
    voice_id: str,
    previous_text: str | None = None,
    next_text: str | None = None,
) -> tuple[str | None, str]:
  
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "previous_text": previous_text,
        "next_text": next_text,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print("❌ ElevenLabs error response:", response.text)
            response.raise_for_status()

        request_id = response.headers.get("request-id")or response.headers.get("Request-Id")

        if request_id:
            print(f"✅ request-id found: {request_id}")
        else:
            print("⚠️ No request-id found in response headers")
            print("Available headers:", dict(response.headers))

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save audio file
        with open(output_path, "wb") as f:
            f.write(response.content)

        return {
            "request_id": request_id,
            "output_path": str(Path(output_path).resolve())
        }
