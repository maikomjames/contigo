import logging
from typing import Callable
from urllib.parse import quote, unquote
from app.services.claude import generate_story, generate_image_prompt, clarify_input
from app.services.image import generate_image
from app.config import STRIPE_PAYMENT_LINK
from app.services.whatsapp_db import (
    get_whatsapp_profile, create_whatsapp_profile, update_whatsapp_profile,
    count_whatsapp_stories_today, log_whatsapp_story, is_whatsapp_premium,
    DAILY_LIMIT, THEMES_LIST,
)

logger = logging.getLogger(__name__)

MAX_CHARS = 1500


def _send_long(recipient: str, text: str, send_fn: Callable):
    """Split text on paragraph breaks and send in multiple messages if needed."""
    paragraphs = text.split("\n\n")
    chunk = ""
    for para in paragraphs:
        candidate = (chunk + "\n\n" + para).strip() if chunk else para
        if len(candidate) <= MAX_CHARS:
            chunk = candidate
        else:
            if chunk:
                send_fn(to=recipient, body=chunk)
            # paragraph itself longer than limit — split by newline
            if len(para) > MAX_CHARS:
                for line in para.split("\n"):
                    send_fn(to=recipient, body=line)
            else:
                chunk = para
    if chunk:
        send_fn(to=recipient, body=chunk)

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


def handle_message(
    from_number: str,
    body: str,
    send_fn: Callable,
    send_media_fn: Callable,
):
    # from_number can be plain phone (Meta) or "whatsapp:+55..." (Twilio)
    phone = from_number.replace("whatsapp:", "").lstrip("+")
    # keep the original for sending back
    recipient = from_number
    text = body.strip()

    if text.startswith("/"):
        _handle_command(recipient, phone, text.lower(), send_fn)
        return

    profile = get_whatsapp_profile(phone)

    if not profile:
        create_whatsapp_profile(phone)
        send_fn(to=recipient, body=WELCOME)
        return

    step = profile.get("onboarding_step", "waiting_name")

    if step == "waiting_name":
        _handle_name(recipient, phone, text, send_fn)
    elif step == "waiting_age":
        _handle_age(recipient, phone, text, send_fn)
    elif step == "waiting_themes":
        _handle_themes(recipient, phone, text, send_fn)
    elif step == "complete":
        _handle_story(recipient, phone, text, profile, send_fn, send_media_fn)
    elif step.startswith("waiting_clarification:"):
        original_input = unquote(step[len("waiting_clarification:"):])
        combined = f"{original_input}. {text}"
        update_whatsapp_profile(phone, onboarding_step="complete")
        _handle_story(recipient, phone, combined, profile, send_fn, send_media_fn)


def _handle_command(recipient: str, phone: str, text: str, send_fn: Callable):
    if text == "/ajuda":
        send_fn(to=recipient, body=HELP)
        return

    if text == "/perfil":
        profile = get_whatsapp_profile(phone)
        if not profile or profile.get("onboarding_step") != "complete":
            send_fn(to=recipient, body="Você ainda não completou o cadastro. Me conta como se chama seu filho!")
            return
        themes = ", ".join(profile.get("themes") or []) or "nenhum definido"
        premium = is_whatsapp_premium(phone)
        send_fn(to=recipient, body=(
            f"*Seu perfil*\n\n"
            f"👦 Filho: {profile.get('child_name')}, {profile.get('child_age')} anos\n"
            f"🎯 Temas: {themes}\n"
            f"⭐ Premium: {'sim' if premium else 'não'}"
        ))
        return

    send_fn(to=recipient, body="Comando não reconhecido. Tente */ajuda*.")


def _handle_name(recipient: str, phone: str, text: str, send_fn: Callable):
    if len(text) < 2:
        send_fn(to=recipient, body="Por favor, digite o nome do seu filho.")
        return
    name = text.strip().capitalize()
    update_whatsapp_profile(phone, child_name=name, onboarding_step="waiting_age")
    send_fn(to=recipient, body=f"Que nome lindo! 😊 Quantos anos o {name} tem?")


def _handle_age(recipient: str, phone: str, text: str, send_fn: Callable):
    try:
        age = int(text.strip())
        if not (2 <= age <= 12):
            raise ValueError
    except ValueError:
        send_fn(to=recipient, body="Por favor, digite apenas o número da idade (ex: _5_).")
        return
    update_whatsapp_profile(phone, child_age=age, onboarding_step="waiting_themes")
    send_fn(to=recipient, body=THEMES_MSG)


def _handle_themes(recipient: str, phone: str, text: str, send_fn: Callable):
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
    send_fn(to=recipient, body=(
        f"Perfeito! Tudo pronto 🎉\n\n"
        f"Agora me conta o que o {name} quer ouvir hoje!\n"
        f"Pode ser simples: _\"dinossauro na floresta\"_ ou _\"princesa no espaço\"_."
    ))


def _handle_story(recipient: str, phone: str, text: str, profile: dict, send_fn: Callable, send_media_fn: Callable):
    if not is_whatsapp_premium(phone):
        count = count_whatsapp_stories_today(phone)
        if count >= DAILY_LIMIT:
            link = f"{STRIPE_PAYMENT_LINK}?client_reference_id={quote(phone)}"
            send_fn(to=recipient, body=LIMIT_MSG.format(link=link))
            return

    questions = clarify_input(text)
    if questions:
        update_whatsapp_profile(phone, onboarding_step=f"waiting_clarification:{quote(text)}")
        send_fn(to=recipient, body=f"Para criar a melhor história possível, me conta mais:\n\n{questions}")
        return

    send_fn(to=recipient, body="✨ Criando sua história, aguarde um momento...")

    try:
        story = generate_story(
            text,
            child_name=profile.get("child_name"),
            child_age=profile.get("child_age"),
            themes=profile.get("themes") or [],
        )
        _send_long(recipient, story, send_fn)
    except Exception as e:
        logger.error("Erro ao gerar história: %s", e)
        send_fn(to=recipient, body="Ops, tive um problema. Tente novamente em instantes.")
        return

    try:
        image_prompt = generate_image_prompt(story, user_input=text)
        image_url = generate_image(image_prompt)
        logger.info("Imagem gerada: %s", image_url)
        send_media_fn(to=recipient, body=" ", media_url=image_url)
    except Exception as e:
        logger.error("Erro ao gerar imagem: %s", e)

    log_whatsapp_story(phone, text)
