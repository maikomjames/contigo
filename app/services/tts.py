import uuid
from pathlib import Path
from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

AUDIO_DIR = Path("/tmp/contigo_audio")
AUDIO_DIR.mkdir(exist_ok=True)


def generate_audio(text: str) -> Path:
    filename = f"{uuid.uuid4()}.mp3"
    filepath = AUDIO_DIR / filename

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="nova",
        input=text,
    ) as response:
        response.stream_to_file(filepath)

    return filepath
