import anthropic
from app.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é um contador de histórias infantis especialista.
Crie histórias envolventes, com linguagem simples e adequada para crianças de 3 a 8 anos.
A história deve ter começo, meio e fim, com uma mensagem positiva sutil.
Escreva em português do Brasil. Máximo de 300 palavras.
Não mencione hora de dormir, noite ou sonhos a menos que o usuário peça explicitamente."""


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


def generate_image_prompt(story: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Based on this children's story, write a short image generation prompt "
                    f"(max 50 words) for a colorful, cute, child-safe illustration. "
                    f"Describe only the main scene with characters and setting. No text in image. "
                    f"Reply with ONLY the prompt text, no titles, no labels, no markdown. "
                    f"Story: {story[:500]}"
                ),
            }
        ],
    )
    # Remove qualquer linha que seja um header markdown (ex: # Image Generation Prompt)
    lines = message.content[0].text.strip().splitlines()
    clean_lines = [l for l in lines if not l.startswith("#")]
    return " ".join(clean_lines).strip()
