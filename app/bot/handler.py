from app.services.twilio import send_message
from app.services.claude import generate_story

WELCOME = (
    "Oi! Eu sou o *Contigo* 🌙\n\n"
    "Crio histórias personalizadas para você ler para seu filho na hora de dormir.\n\n"
    "Me conta o que seu filho quer ouvir hoje — personagem, lugar, aventura. "
    "Pode ser simples: _\"dinossauro na floresta\"_ ou _\"princesa no espaço\"_."
)


def handle_message(from_number: str, body: str):
    text = body.strip()

    if not text:
        send_message(to=from_number, body=WELCOME)
        return

    send_message(to=from_number, body="✨ Criando sua história, aguarde um momento...")

    try:
        story = generate_story(text)
        send_message(to=from_number, body=story)
    except Exception:
        send_message(
            to=from_number,
            body="Ops, tive um problema para criar a história. Tente novamente em instantes.",
        )
