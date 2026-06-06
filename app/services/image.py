import base64
from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_image(story: str) -> bytes:
    prompt = (
        f"Ilustração infantil colorida e fofa, estilo livro de histórias, "
        f"sem texto, baseada nesta história: {story[:300]}"
    )
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="low",
        n=1,
    )
    image_base64 = response.data[0].b64_json
    return base64.b64decode(image_base64)
