from twilio.rest import Client
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_message(to: str, body: str):
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
        body=body,
    )


def send_media(to: str, body: str, media_url: str):
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
        body=body,
        media_url=[media_url],
    )


def send_audio(to: str, audio_url: str):
    client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=to,
        media_url=[audio_url],
    )
