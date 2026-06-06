from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

AUDIO_DIR = Path("/tmp/contigo_audio")


@router.get("/audio/{filename}")
def serve_audio(filename: str):
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    return FileResponse(filepath, media_type="audio/mpeg")
