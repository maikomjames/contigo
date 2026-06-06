from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

AUDIO_DIR = Path("/tmp/contigo_audio")
IMAGE_DIR = Path("/tmp/contigo_images")


@router.get("/audio/{filename}")
def serve_audio(filename: str):
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    return FileResponse(filepath, media_type="audio/mpeg")


@router.get("/images/{filename}")
def serve_image(filename: str):
    filepath = IMAGE_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    return FileResponse(filepath, media_type="image/png")
