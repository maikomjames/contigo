import logging
from app.services.twilio import send_message, send_media
from app.services.claude import generate_story, generate_image_prompt
from app.services.image import generate_image
from app.config import STRIPE_PAYMENT_LINK
from app.services.whatsapp_db import (
    get_whatsapp_profile, create_whatsapp_profile, update_whatsapp_profile,
    count_whatsapp_stories_today, log_whatsapp_story, is_whatsapp_premium,
    DAILY_LIMIT, THEMES_LIST,
)

logger = logging.getLogger(__name__)

WELCOME = (
    "Oi! Eu sou o *Contigo* ✨\n\n"
    "Crio histórias infantis personalizadas com ilustração.\n\n"
    "Vamos começar! Como se chama seu filho?"
)

THEMES_MSG = (
    "Que temas você quer trabalhar?\n\n"
    "1. amizade\n2. coragem\n3. persistência\n4. generosidade\n"
    "5. paciência\n6. aventura\n7. curiosidade\n8. respeito\n\n"
    "Digite os números separados por vírgula (ex: _1,3,6_) ou *pular* para escolher depois."
)

HELP = (
    "*Contigo* — Histórias infantis personalizadas ✨\n\n"
    "Envie qualquer mensagem para gerar uma história.\n\n"
    "*/perfil* — ver seu perfil\n"
    "*/ajuda* — mostrar este menu"
)

LIMIT_MSG = (
    "Você já usou sua história gratuita de hoje 🌟\n\n"
    "Assine o *Contigo Premium* para histórias ilimitadas:\n{link}"
)


def handle_message(from_number: str, body: str):
    phone = from_number.replace("whatsapp:", "")
    text = body.strip()

    if text.startswith("/"):
        _handle_command(from_number, phone, text.lower())
        return

    profile = get_whatsapp_profile(phone)

    if not profile:
        create_whatsapp_profile(phone)
        send_message(to=from_number, body=WELCOME)
        return

    step = profile.get("onboarding_step", "waiting_name")

    if step == "waiting_name":
        _handle_name(from_number, phone, text)
    elif step == "waiting_age":
        _handle_age(from_number, phone, text)
    elif step == "waiting_themes":
        _handle_themes(from_number, phone, text)
    elif step == "complete":
        _handle_story(from_number, phone, text, profile)


def _handle_command(from_number: str, phone: str, text: str):
    if text == "/ajuda":
        send_message(to=from_number, body=HELP)
        return

    if text == "/perfil":
        profile = get_whatsapp_profile(phone)
        if not profile or profile.get("onboarding_step") != "complete":
            send_message(to=from_number, body="Você ainda não completou o cadastro. Me conta como se chama seu filho!")
            return
        themes = ", ".join(profile.get("themes") or []) or "nenhum definido"
        premium = is_whatsapp_premium(phone)
        send_message(to=from_number, body=(
            f"*Seu perfil*\n\n"
            f"👦 Filho: {profile.get('child_name')}, {profile.get('child_age')} anos\n"
            f"🎯 Temas: {themes}\n"
            f"⭐ Premium: {'sim' if premium else 'não'}"
        ))
        return

    send_message(to=from_number, body="Comando não reconhecido. Tente */ajuda*.")


def _handle_name(from_number: str, phone: str, text: str):
    if len(text) < 2:
        send_message(to=from_number, body="Por favor, digite o nome do seu filho.")
        return
    name = text.strip().capitalize()
    update_whatsapp_profile(phone, child_name=name, onboarding_step="waiting_age")
    send_message(to=from_number, body=f"Que nome lindo! 😊 Quantos anos o {name} tem?")


def _handle_age(from_number: str, phone: str, text: str):
    try:
        age = int(text.strip())
        if not (2 <= age <= 12):
            raise ValueError
    except ValueError:
        send_message(to=from_number, body="Por favor, digite apenas o número da idade (ex: _5_).")
        return
    update_whatsapp_profile(phone, child_age=age, onboarding_step="waiting_themes")
    send_message(to=from_number, body=THEMES_MSG)


def _handle_themes(from_number: str, phone: str, text: str):
    selected = []
    if text.lower() != "pular":
        for part in text.replace(" ", ",").split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(THEMES_LIST):
                    selected.append(THEMES_LIST[idx])
            elif part.lower() in THEMES_LIST:
                selected.append(part.lower())

    update_whatsapp_profile(phone, themes=selected or None, onboarding_step="complete")
    profile = get_whatsapp_profile(phone)
    name = profile.get("child_name", "seu filho")
    send_message(to=from_number, body=(
        f"Perfeito! Tudo pronto 🎉\n\n"
        f"Agora me conta o que o {name} quer ouvir hoje!\n"
        f"Pode ser simples: _\"dinossauro na floresta\"_ ou _\"princesa no espaço\"_."
    ))


def _handle_story(from_number: str, phone: str, text: str, profile: dict):
    if not is_whatsapp_premium(phone):
        count = count_whatsapp_stories_today(phone)
        if count >= DAILY_LIMIT:
            link = f"{STRIPE_PAYMENT_LINK}?client_reference_id={phone}"
            send_message(to=from_number, body=LIMIT_MSG.format(link=link))
            return

    send_message(to=from_number, body="✨ Criando sua história, aguarde um momento...")

    try:
        story = generate_story(
            text,
            child_name=profile.get("child_name"),
            child_age=profile.get("child_age"),
            themes=profile.get("themes") or [],
        )
        send_message(to=from_number, body=story)
    except Exception as e:
        logger.error("Erro ao gerar história: %s", e)
        send_message(to=from_number, body="Ops, tive um problema. Tente novamente em instantes.")
        return

    try:
        image_prompt = generate_image_prompt(story)
        image_url = generate_image(image_prompt)
        logger.info("Imagem gerada: %s", image_url)
        send_media(to=from_number, body=" ", media_url=image_url)
    except Exception as e:
        logger.error("Erro ao gerar imagem: %s", e)

    log_whatsapp_story(phone, text)
