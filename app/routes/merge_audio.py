# # NEW CODE 
# import os
# import re
# import time
# import subprocess
# from pathlib import Path
# from typing import List, Dict, Any, Optional

# from fastapi import APIRouter, Request, HTTPException, Response
# from fastapi.responses import JSONResponse

# from app.utils.generate_audio import generate_audio  # your ElevenLabs generator

# router = APIRouter()

# # Ensure audios folder exists
# audios_dir = Path(__file__).resolve().parent.parent / "audios"
# audios_dir.mkdir(exist_ok=True)


# # -----------------------------
# # 🔹 Helper: Parse text into chunks (sentences + pauses)
# # -----------------------------
# def parse_text_with_pauses(text: str) -> List[Dict[str, Any]]:
#     tokens = re.split(r'(\(\d+s-pause\))', text)
#     chunks: List[Dict[str, Any]] = []

#     for token in tokens:
#         token = token.strip()
#         if not token:
#             continue

#         pause_match = re.match(r"\((\d+)s-pause\)", token, re.IGNORECASE)
#         if pause_match:
#             chunks.append({"type": "pause", "duration": int(pause_match.group(1))})
#         else:
#             chunks.append({"type": "text", "sentence": token})

#     return chunks


# # -----------------------------
# # 🔹 Helper: Generate silence file if not exists
# # -----------------------------
# def get_silence_file(duration: int) -> str:
#     silence_path = audios_dir / f"silence_{duration}s.mp3"
#     if not silence_path.exists():
#         print(f"🎵 Generating silence {duration}s")
#         subprocess.run(
#             [
#                 "ffmpeg", "-y",
#                 "-f", "lavfi",
#                 "-i", "anullsrc=r=44100:cl=mono",
#                 "-t", str(duration),
#                 "-q:a", "9",
#                 "-acodec", "libmp3lame",
#                 str(silence_path)
#             ],
#             check=True
#         )
#     return str(silence_path)


# # -----------------------------
# # 🔹 API: Merge dynamic audio respecting pauses
# # -----------------------------
# @router.post("/merge-audio")
# async def merge_dynamic_audio(request: Request):
#     try:
#         body = await request.json()
#         print("📥 Incoming request body:", body)

#         sentences: List[str] = body.get("sentences")
#         voice_id: Optional[str] = body.get("voiceId")

#         if not voice_id or not isinstance(sentences, list) or not sentences:
#             raise HTTPException(status_code=400, detail="voiceId and sentences are required")

#         # Parse all sentences into text + pauses
#         all_chunks: List[Dict[str, Any]] = []
#         for line in sentences:
#             all_chunks.extend(parse_text_with_pauses(line))

#         if not all_chunks:
#             raise HTTPException(status_code=400, detail="No valid sentences or pauses found")

#         print("✅ Parsed chunks:", all_chunks)

#         # Cache silence files by duration
#         silence_cache: Dict[int, str] = {}

#         # Build list of audio files in exact order
#         final_files: List[str] = []
#         request_ids: List[str] = []

#         for chunk in all_chunks:
#             if chunk["type"] == "text":
#                 # Generate TTS per sentence
#                 tts_path = audios_dir / f"tts_{int(time.time()*1000)}.mp3"
#                 print(f"🎤 Generating TTS for: {chunk['sentence']}")
#                 res = await generate_audio(chunk["sentence"], str(tts_path), voice_id)
#                 request_id = res.get("request_id")
#                 if request_id:
#                     request_ids.append(request_id)
#                 if not tts_path.exists():
#                     raise HTTPException(status_code=500, detail="TTS generation failed")
#                 final_files.append(str(tts_path))
#             elif chunk["type"] == "pause":
#                 duration = chunk["duration"]
#                 if duration not in silence_cache:
#                     silence_cache[duration] = get_silence_file(duration)
#                 final_files.append(silence_cache[duration])

#         # -----------------------------
#         # 🔹 Merge all audio files into one
#         # -----------------------------
#         concat_file_path = audios_dir / f"concat_{int(time.time()*1000)}.txt"
#         with open(concat_file_path, "w", encoding="utf-8") as f:
#             for file in final_files:
#                 f.write(f"file '{Path(file).as_posix()}'\n")

#         output_path = audios_dir / f"Audio_{int(time.time()*1000)}.mp3"
#         subprocess.run(
#             [
#                 "ffmpeg", "-y",
#                 "-f", "concat",
#                 "-safe", "0",
#                 "-i", str(concat_file_path),
#                 "-c", "copy",
#                 str(output_path)
#             ],
#             check=True
#         )

#         print("✅ Final audio created:", output_path)

#         # Cleanup intermediate TTS files and concat list
#         for f in final_files:
#             if "tts_" in f and Path(f).exists():
#                 os.remove(f)
#         if concat_file_path.exists():
#             os.remove(concat_file_path)

#         # Return merged audio
#         audio_buffer = output_path.read_bytes()
#         headers = {}
#         if request_ids:
#             headers["request-id"] = ",".join(request_ids)
#             headers["Access-Control-Expose-Headers"] = "request-id"

#         return Response(content=audio_buffer, media_type="audio/mpeg", headers=headers)

#     except HTTPException:
#         raise
#     except Exception as e:
#         print("🔥 Unexpected error:", str(e))
#         return JSONResponse(status_code=500, content={"error": str(e)})





# NEW Code
import os
import re
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse

from app.utils.generate_audio import generate_audio  # your ElevenLabs generator

router = APIRouter()

# Ensure audios folder exists
audios_dir = Path(__file__).resolve().parent.parent / "audios"
audios_dir.mkdir(exist_ok=True)


# -----------------------------
# 🔹 Helper: Parse text into chunks (sentences + pauses)
# -----------------------------
def parse_text_with_pauses(text: str) -> List[Dict[str, Any]]:
    tokens = re.split(r'(\(\d+s-pause\))', text)
    chunks: List[Dict[str, Any]] = []

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        pause_match = re.match(r"\((\d+)s-pause\)", token, re.IGNORECASE)
        if pause_match:
            chunks.append({"type": "pause", "duration": int(pause_match.group(1))})
        else:
            chunks.append({"type": "text", "sentence": token})
    return chunks


# -----------------------------
# 🔹 Helper: Generate silence file if not exists
# -----------------------------
def get_silence_file(duration: int) -> str:
    silence_path = audios_dir / f"silence_{duration}s.mp3"
    if not silence_path.exists():
        print(f"🎵 Generating silence {duration}s")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=mono",
                "-t", str(duration),
                "-q:a", "9",
                "-acodec", "libmp3lame",
                str(silence_path)
            ],
            check=True
        )
    return str(silence_path)


# -----------------------------
# 🔹 Helper: Sanitize first sentence for filename
# -----------------------------
def sanitize_filename(text: str) -> str:
    safe_text = re.sub(r'[^a-zA-Z0-9]+', '_', text.strip().lower())
    return safe_text[:50]  # limit length to avoid very long filenames


# -----------------------------
# 🔹 API: Merge dynamic audio respecting pauses
# -----------------------------
@router.post("/merge-audio")
async def merge_dynamic_audio(request: Request):
    try:
        body = await request.json()
        print("📥 Incoming request body:", body)

        sentences: List[str] = body.get("sentences")
        voice_id: Optional[str] = body.get("voiceId")

        if not voice_id or not isinstance(sentences, list) or not sentences:
            raise HTTPException(status_code=400, detail="voiceId and sentences are required")

        # Parse all sentences into text + pauses
        all_chunks: List[Dict[str, Any]] = []
        for line in sentences:
            all_chunks.extend(parse_text_with_pauses(line))
        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid sentences or pauses found")

        print("✅ Parsed chunks:", all_chunks)

        # Cache silence files by duration
        silence_cache: Dict[int, str] = {}

        # Build list of audio files in exact order
        final_files: List[str] = []
        request_ids: List[str] = []

        for chunk in all_chunks:
            if chunk["type"] == "text":
                # Generate TTS per sentence
                tts_path = audios_dir / f"tts_{int(time.time()*1000)}.mp3"
                print(f"🎤 Generating TTS for: {chunk['sentence']}")
                res = await generate_audio(chunk["sentence"], str(tts_path), voice_id)
                request_id = res.get("request_id")
                if request_id:
                    request_ids.append(request_id)
                if not tts_path.exists():
                    raise HTTPException(status_code=500, detail="TTS generation failed")
                final_files.append(str(tts_path))
            elif chunk["type"] == "pause":
                duration = chunk["duration"]
                if duration not in silence_cache:
                    silence_cache[duration] = get_silence_file(duration)
                final_files.append(silence_cache[duration])

        # -----------------------------
        # 🔹 Generate final filename starting with first sentence
        # -----------------------------
        first_sentence_text = all_chunks[0]['sentence'] if all_chunks else "audio"
        safe_name = sanitize_filename(first_sentence_text)
        output_path = audios_dir / f"{safe_name}_{int(time.time()*1000)}.mp3"

        # -----------------------------
        # 🔹 Merge all audio files into one
        # -----------------------------
        concat_file_path = audios_dir / f"concat_{int(time.time()*1000)}.txt"
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for file in final_files:
                f.write(f"file '{Path(file).as_posix()}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file_path),
                "-c", "copy",
                str(output_path)
            ],
            check=True
        )

        print("✅ Final audio created:", output_path)

        # Cleanup intermediate TTS files and concat list
        for f in final_files:
            if "tts_" in f and Path(f).exists():
                os.remove(f)
        if concat_file_path.exists():
            os.remove(concat_file_path)

        # Return merged audio
        audio_buffer = output_path.read_bytes()
        headers = {}
        if request_ids:
            headers["request-id"] = ",".join(request_ids)
            headers["Access-Control-Expose-Headers"] = "request-id"

        return Response(content=audio_buffer, media_type="audio/mpeg", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        print("🔥 Unexpected error:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
