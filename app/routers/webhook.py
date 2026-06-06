import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Form, Response
from app.bot.handler import handle_message

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


@router.post("/webhook")
async def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(...),
):
    # Roda em thread pool para não bloquear o event loop
    # e não depender do ciclo de vida do request do FastAPI
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, handle_message, From, Body)
    return Response(status_code=200)
