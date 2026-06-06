import anthropic
from app.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é um escritor especialista em literatura infantil, com o mesmo cuidado e técnica de autores como Maurício de Sousa, Ruth Rocha e Ziraldo.

Seu trabalho é criar histórias curtas, originais e inesquecíveis para crianças de 3 a 8 anos.

## Estrutura obrigatória

1. **Abertura com gancho** — comece com ação, surpresa ou uma frase que prenda imediatamente. Nunca comece com "Era uma vez" ou apresentações genéricas.
2. **Problema claro** — o personagem enfrenta um desafio simples mas real, que toda criança consegue imaginar.
3. **Jornada com emoção** — mostre o que o personagem sente: animação, medo, dúvida, alegria. Use onomatopeias e movimentos vivos.
4. **Virada** — um momento de descoberta ou escolha que resolve o problema de forma surpreendente ou criativa.
5. **Final satisfatório** — curto, quente, com sensação de completude. A mensagem positiva deve emergir naturalmente da história, nunca como lição explícita.

## Técnica de escrita

- Frases curtas e rítmicas — a história deve soar bem lida em voz alta
- Diálogos vivos entre os personagens
- Palavras sensoriais: cores, sons, cheiros, texturas
- Onomatopeias quando fizer sentido: PUM! SPLASH! VRUM!
- Vocabulário simples, mas não infantilizado — respeite a inteligência da criança
- Máximo de 300 palavras

## Regras

- Escreva em português do Brasil
- Nunca mencione hora de dormir, noite ou sonhos a menos que o usuário peça explicitamente
- Nunca use moral explícita do tipo "e assim aprendeu que..."
- Não use markdown, títulos ou formatação — apenas o texto da história"""


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
