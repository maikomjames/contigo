import anthropic
from app.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é um contador de histórias infantis especialista.
Crie histórias envolventes, com linguagem simples e adequada para crianças de 3 a 8 anos.
A história deve ter começo, meio e fim, com uma mensagem positiva sutil.
Escreva em português do Brasil. Máximo de 300 palavras."""


def generate_story(user_input: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Crie uma história infantil com: {user_input}",
            }
        ],
    )
    return message.content[0].text
