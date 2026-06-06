from fastapi import FastAPI
from app.routers import webhook

app = FastAPI(title="Contigo")

app.include_router(webhook.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "Contigo"}
