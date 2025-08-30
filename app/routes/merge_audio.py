import os, shutil
import re
import time
import subprocess
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse

from app.utils.generate_audio import generate_audio  # 👈 your custom audio generator

router = APIRouter()

# Ensure audios folder exists
audios_dir = Path(__file__).resolve().parent.parent / "audios"
audios_dir.mkdir(exist_ok=True)


@router.post("/merge-audio")
async def merge_dynamic_audio(request: Request):
    try:
        body = await request.json()
        print("📥 Incoming request body:", body)
        print("PATH seen by FastAPI:", os.environ.get("PATH"))
        print("ffmpeg resolved to:", shutil.which("ffmpeg"))

        sentences: List[str] = body.get("sentences")
        voice_id: Optional[str] = body.get("voiceId")

        if not voice_id or not isinstance(sentences, list) or len(sentences) == 0:
            raise HTTPException(status_code=400, detail="voiceId and sentences are required")

        # -----------------------------
        # 🔹 Parse sentences + pauses
        # -----------------------------
        sentence_chunks = []
        for idx, line in enumerate(sentences):
            pause_match = re.search(r"\((\d+)s-pause\)", line, re.IGNORECASE)
            pause = int(pause_match.group(1)) if pause_match else None
            sentence = re.sub(r"\(\d+s-pause\)", "", line, flags=re.IGNORECASE).strip()

            sentence_chunks.append({
                "sentence": sentence,
                "pause": pause,
                "previousText": re.sub(r"\(\d+s-pause\)", "", sentences[idx - 1], flags=re.IGNORECASE).strip()
                if idx > 0 else None,
                "nextText": re.sub(r"\(\d+s-pause\)", "", sentences[idx + 1], flags=re.IGNORECASE).strip()
                if idx < len(sentences) - 1 else None,
            })

        print("✅ Parsed sentence chunks:", sentence_chunks)

        # -----------------------------
        # 🔹 Pre-generate silence files
        # -----------------------------
        silence_files = {}
        for chunk in sentence_chunks:
            pause = chunk["pause"]
            if pause and pause not in silence_files:
                silence_path = audios_dir / f"silence_{pause}s.mp3"
                if not silence_path.exists():
                    print(f"🎵 Generating silence {pause}s at {silence_path}")
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-f", "lavfi",
                        "-i", "anullsrc=r=44100:cl=mono",
                        "-t", str(pause),
                        "-q:a", "9",
                        "-acodec", "libmp3lame",
                        str(silence_path)
                    ], check=True)
                silence_files[pause] = str(silence_path)

        # -----------------------------
        # 🔹 Generate audios for each sentence
        # -----------------------------
        audio_files = []
        request_ids = []

        for i, chunk in enumerate(sentence_chunks):
            sentence, pause, prev_text, next_text = (
                chunk["sentence"], chunk["pause"], chunk["previousText"], chunk["nextText"]
            )

            sentence_path = audios_dir / f"temp_sentence_{int(time.time() * 1000)}_{i}.mp3"

            print(f"🎤 Generating audio for: '{sentence}' → {sentence_path}")

            res_request_id, saved_path = await generate_audio(
                sentence, str(sentence_path), voice_id, prev_text, next_text
            )

            if res_request_id:
                request_ids.append(res_request_id)
            else:
                print(f"⚠️ No request-id returned for: '{sentence}'")

            audio_files.append(saved_path)

            if pause and i < len(sentence_chunks) - 1:
                print(f"⏸ Adding silence of {pause}s after sentence {i}")
                audio_files.append(silence_files[pause])

        # -----------------------------
        # 🔹 Validate audio files
        # -----------------------------
        for file in audio_files:
            if not os.path.exists(file):
                raise HTTPException(status_code=500, detail=f"Missing audio file: {file}")

        # -----------------------------
        # 🔹 Concatenate with FFmpeg
        # -----------------------------
        concat_txt = "\n".join([f"file '{file.replace(os.sep, '/')}'" for file in audio_files])
        concat_file_path = audios_dir / f"concat_{int(time.time() * 1000)}.txt"
        concat_file_path.write_text(concat_txt)

        output_path = audios_dir / f"Audio_{int(time.time() * 1000)}.mp3"

        print("🔗 Merging audios with FFmpeg...")
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file_path),
                "-c", "copy",
                str(output_path)
            ], check=True)
        except subprocess.CalledProcessError as e:
            print("❌ FFmpeg merge failed:", e)
            raise HTTPException(status_code=500, detail="Failed to merge audio.")

        print("✅ Audio successfully merged:", output_path)

        # -----------------------------
        # 🔹 Cleanup temp files
        # -----------------------------
        for file in audio_files:
            if "temp_sentence_" in file and os.path.exists(file):
                os.remove(file)
        if concat_file_path.exists():
            os.remove(concat_file_path)

        # -----------------------------
        # 🔹 Return final audio + last 3 request IDs
        # -----------------------------
        audio_buffer = output_path.read_bytes()
        headers = {}

        if request_ids:
            last_three = ",".join(request_ids[-3:])
            headers["request-id"] = last_three
            headers["Access-Control-Expose-Headers"] = "request-id"

        return Response(content=audio_buffer, media_type="audio/mpeg", headers=headers)

    except Exception as e:
        print("🔥 Error in merge_dynamic_audio:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
