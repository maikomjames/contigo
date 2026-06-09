import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Form, Response
from app.bot.handler import handle_message
from app.services.twilio import send_message, send_media

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


def _process(from_number: str, body: str):
    handle_message(from_number=from_number, body=body, send_fn=send_message, send_media_fn=send_media)


@router.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(...),
):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, _process, From, Body)
    return Response(status_code=200)
