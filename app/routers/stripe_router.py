import re
import logging
import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.services.database import set_premium_expiry
from app.services.whatsapp_db import set_whatsapp_premium

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="stripe-signature")):
    body = await request.body()
    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        logger.error("Webhook inválido: %s", e)
        raise HTTPException(status_code=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        ref = session.get("client_reference_id")
        if ref:
            if UUID_RE.match(ref):
                set_premium_expiry(ref)
                logger.info("Premium web ativado: user=%s", ref)
            else:
                set_whatsapp_premium(ref)
                logger.info("Premium WhatsApp ativado: phone=%s", ref)
        else:
            logger.warning("checkout.session.completed sem client_reference_id")

    return JSONResponse({"ok": True})
