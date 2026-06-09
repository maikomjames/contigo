import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from app.config import META_VERIFY_TOKEN
from app.bot.handler import handle_message
from app.services.meta import send_message, send_media

router = APIRouter()
logger = logging.getLogger(__name__)
_pool = ThreadPoolExecutor(max_workers=4)


@router.get("/whatsapp/webhook")
def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("/whatsapp/webhook")
async def receive(request: Request):
    data = await request.json()
    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        messages = value.get("messages", [])
        for msg in messages:
            if msg.get("type") != "text":
                continue
            from_number = msg["from"]  # plain number, no prefix
            body = msg["text"]["body"]
            _pool.submit(_process, from_number, body)
    except Exception as e:
        logger.error("Meta webhook parse error: %s", e)
    return JSONResponse({"ok": True})


def _process(from_number: str, body: str):
    try:
        handle_message(
            from_number=from_number,
            body=body,
            send_fn=send_message,
            send_media_fn=send_media,
        )
    except Exception as e:
        logger.error("Error processing message from %s: %s", from_number, e)
