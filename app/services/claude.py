import anthropic
from anthropic import AsyncAnthropic
from app.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
async_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é um escritor especialista em literatura infantil brasileira, com a mesma qualidade de Maurício de Sousa, Ruth Rocha e Ana Maria Machado.

Seu trabalho é criar histórias do tipo que a criança pede para ouvir de novo — e depois de novo.

## Estrutura obrigatória

1. **Abertura com impacto** — comece no meio da ação ou com uma imagem/situação inesperada. Nunca "Era uma vez" ou frases de apresentação.
2. **Problema concreto** — um desafio visual e imediato que qualquer criança consegue imaginar claramente.
3. **Escalada com humor** — a situação complica de forma engraçada ou absurda antes de melhorar. Inclua pelo menos um momento de humor genuíno: confusão, reviravolta cômica ou diálogo inesperado.
4. **Repetição que cria expectativa** — use pelo menos uma estrutura de repetição ("primeiro X tentou... depois Y tentou... então...") para criar ritmo e antecipação do que vem.
5. **Virada que vem de dentro** — a solução deve emergir da criatividade ou coragem do protagonista, não de um adulto ou de pura sorte.
6. **Final curto e quente** — uma frase ou imagem que deixa a criança sorrindo ou com vontade de mais. Nunca uma lição explícita.

## Técnica de escrita

- Frases curtas e rítmicas — deve soar bem lida em voz alta
- Diálogos com personalidade — cada personagem fala de um jeito
- Palavras sensoriais: cores, sons, cheiros, texturas
- Onomatopeias quando fizer sentido: PUM! SPLASH! VRUM! GRRR!
- Adapte ao vocabulário da idade: até 5 anos, frases curtíssimas e palavras do cotidiano; 6 anos ou mais, pode ter mais nuance
- Entre 600 e 700 palavras

## Regras

- Escreva em português do Brasil
- Nunca mencione hora de dormir, noite ou sonhos a menos que o usuário peça
- Nunca use moral explícita do tipo "e assim aprendeu que..."
- Comece com o título da história em uma linha, seguido de uma linha em branco e então o texto
- O título deve ser curto, criativo e instigante — sem "A História de" ou fórmulas genéricas
- Sem markdown, asteriscos ou qualquer formatação — apenas título, linha em branco e texto"""


def _build_content(user_input: str, child_age: int | None, themes: list[str] | None) -> str:
    context_parts = []
    if child_age:
        context_parts.append(f"tem {child_age} anos")
    if themes:
        context_parts.append(f"trabalhe sutilmente o(s) tema(s): {', '.join(themes)}")
    context = ". ".join(context_parts) + "." if context_parts else ""
    content = f"Crie uma história infantil com: {user_input}"
    if context:
        content += f"\n\nContexto: {context}"
    return content


def generate_story(
    user_input: str,
    child_name: str | None = None,
    child_age: int | None = None,
    themes: list[str] | None = None,
) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_content(user_input, child_age, themes)}],
    )
    return message.content[0].text


async def generate_story_stream(
    user_input: str,
    child_name: str | None = None,
    child_age: int | None = None,
    themes: list[str] | None = None,
):
    async with async_client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_content(user_input, child_age, themes)}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


def clarify_input(user_input: str) -> str | None:
    """Returns clarification questions if input is vague, None if clear enough."""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                f"Avalie se esse pedido de história infantil tem detalhes suficientes para gerar uma história ótima.\n\n"
                f"Pedido: \"{user_input}\"\n\n"
                f"O pedido é SUFICIENTE se mencionar pelo menos 2 destes elementos: personagem(ns), cenário/local, situação/desafio.\n"
                f"O pedido é VAGO se for apenas um nome, uma palavra solta ou não tiver contexto.\n\n"
                f"Se SUFICIENTE: responda exatamente: OK\n"
                f"Se VAGO: escreva 2 perguntas curtas e simpáticas em português para obter os detalhes que faltam. "
                f"Sem texto introdutório — apenas as perguntas numeradas."
            )
        }]
    )
    result = message.content[0].text.strip()
    return None if result == "OK" else result


def generate_image_prompt(story: str, user_input: str = "") -> str:
    user_input_line = f"User request: {user_input}\n\n" if user_input else ""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=250,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are an art director creating an illustration prompt for a children's book.\n\n"
                    f"{user_input_line}"
                    f"Read the story below and identify the single most visually striking scene.\n\n"
                    f"Write an image generation prompt in English (max 80 words). Rules:\n"
                    f"- START with the main character — put them first and most prominent\n"
                    f"- If the character is a named pop culture figure (Sonic, Goku, Pikachu, Naruto, Spider-Man, etc.), "
                    f"describe their iconic visual appearance in detail right after the name: colors, outfit, distinctive features. "
                    f"Example: 'Sonic the Hedgehog, blue anthropomorphic hedgehog with red sneakers and white gloves'\n"
                    f"- Describe the setting, colors and mood\n"
                    f"- Keep the scene simple: one main character, one action, one location\n"
                    f"- End with: children's book illustration, vibrant colors, cartoon style, no text\n\n"
                    f"Reply with ONLY the prompt. No titles, labels, markdown or explanations.\n\n"
                    f"Story:\n{story}"
                ),
            }
        ],
    )
    lines = message.content[0].text.strip().splitlines()
    clean_lines = [l for l in lines if not l.startswith("#")]
    return " ".join(clean_lines).strip()
