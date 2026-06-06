from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_image(story: str) -> str:
    prompt = (
        f"Ilustração infantil colorida e fofa, estilo livro de histórias, "
        f"sem texto, baseada nesta história: {story[:300]}"
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return response.data[0].url
