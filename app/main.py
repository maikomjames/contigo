from fastapi import FastAPI
from app.routers import webhook, audio

app = FastAPI(title="Contigo")

app.include_router(webhook.router)
app.include_router(audio.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "Contigo"}
