from app.services.twilio import send_message

WELCOME = (
    "Oi! Eu sou o *Contigo* 🌙\n\n"
    "Crio histórias personalizadas para você ler para seu filho na hora de dormir.\n\n"
    "Para começar, me conta: qual o nome do seu filho?"
)


def handle_message(from_number: str, body: str):
    # Fase 1: resposta fixa para validar o ciclo Twilio → FastAPI → WhatsApp
    # As próximas fases adicionarão onboarding, geração de história e pagamento
    send_message(to=from_number, body=WELCOME)
