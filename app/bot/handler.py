import uuid
import logging
from pathlib import Path
from app.services.twilio import send_message, send_media, send_audio
from app.services.claude import generate_story
from app.services.image import generate_image
from app.services.tts import generate_audio
from app.config import PUBLIC_URL

logger = logging.getLogger(__name__)

IMAGE_DIR = Path("/tmp/contigo_images")
IMAGE_DIR.mkdir(exist_ok=True)

WELCOME = (
    "Oi! Eu sou o *Contigo* 🌙\n\n"
    "Crio histórias personalizadas para você ler para seu filho na hora de dormir.\n\n"
    "Me conta o que seu filho quer ouvir hoje — personagem, lugar, aventura. "
    "Pode ser simples: _\"dinossauro na floresta\"_ ou _\"princesa no espaço\"_."
)


def handle_message(from_number: str, body: str):
    text = body.strip()

    if not text:
        send_message(to=from_number, body=WELCOME)
        return

    send_message(to=from_number, body="✨ Criando sua história, aguarde um momento...")

    try:
        story = generate_story(text)
        send_message(to=from_number, body=story)
    except Exception as e:
        logger.error("Erro ao gerar história: %s", e)
        send_message(
            to=from_number,
            body="Ops, tive um problema para criar a história. Tente novamente em instantes.",
        )
        return

    try:
        image_bytes = generate_image(story)
        filename = f"{uuid.uuid4()}.png"
        filepath = IMAGE_DIR / filename
        filepath.write_bytes(image_bytes)
        image_url = f"https://{PUBLIC_URL}/images/{filename}"
        logger.info("Imagem gerada: %s", image_url)
        send_media(to=from_number, body=" ", media_url=image_url)
    except Exception as e:
        logger.error("Erro ao gerar imagem: %s", e)

    try:
        audio_path = generate_audio(story)
        audio_url = f"https://{PUBLIC_URL}/audio/{audio_path.name}"
        logger.info("Áudio gerado: %s", audio_url)
        send_audio(to=from_number, audio_url=audio_url)
    except Exception as e:
        logger.error("Erro ao gerar áudio: %s", e)
