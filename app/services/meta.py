import logging
import httpx
from app.config import META_PHONE_NUMBER_ID, META_ACCESS_TOKEN

logger = logging.getLogger(__name__)

BASE_URL = f"https://graph.facebook.com/v20.0/{META_PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}


def _phone(number: str) -> str:
    return number.replace("whatsapp:", "").replace("+", "").strip()


def send_message(to: str, body: str):
    phone = _phone(to)
    try:
        r = httpx.post(BASE_URL, headers=HEADERS, json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": body},
        })
        if not r.is_success:
            logger.error("Meta send_message 400+ to=%s status=%s body=%s", phone, r.status_code, r.text)
        r.raise_for_status()
    except httpx.HTTPStatusError:
        pass
    except Exception as e:
        logger.error("Meta send_message error to=%s: %s", phone, e)


def send_media(to: str, body: str = "", media_url: str = ""):
    phone = _phone(to)
    try:
        r = httpx.post(BASE_URL, headers=HEADERS, json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {"link": media_url, "caption": body.strip()},
        })
        if not r.is_success:
            logger.error("Meta send_media 400+ to=%s status=%s body=%s", phone, r.status_code, r.text)
        r.raise_for_status()
    except httpx.HTTPStatusError:
        pass
    except Exception as e:
        logger.error("Meta send_media error to=%s: %s", phone, e)
