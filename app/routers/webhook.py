from fastapi import APIRouter, Form, BackgroundTasks, Response
from app.bot.handler import handle_message

router = APIRouter()


@router.post("/webhook")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(default=""),
    From: str = Form(...),
):
    # Retorna 200 imediatamente — Twilio não espera o processamento
    # Geração de história (Claude + imagem + áudio) roda em background
    background_tasks.add_task(handle_message, from_number=From, body=Body)
    return Response(status_code=200)
