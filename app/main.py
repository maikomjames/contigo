import logging
from fastapi import FastAPI
from app.routers import webhook, audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Contigo")

app.include_router(webhook.router)
app.include_router(audio.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "Contigo"}
