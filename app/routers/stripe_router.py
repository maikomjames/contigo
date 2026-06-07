import logging
import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.services.database import set_premium_expiry

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY


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
        user_id = session.get("client_reference_id")
        if user_id:
            set_premium_expiry(user_id)
            logger.info("Premium ativado: user=%s", user_id)
        else:
            logger.warning("checkout.session.completed sem client_reference_id")

    return JSONResponse({"ok": True})
