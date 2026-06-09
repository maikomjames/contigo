import logging
from fastapi import FastAPI
from app.routers import webhook, audio, story, stripe_router, whatsapp_meta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Contigo")

app.include_router(webhook.router)
app.include_router(audio.router)
app.include_router(story.router)
app.include_router(stripe_router.router)
app.include_router(whatsapp_meta.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "Contigo"}
