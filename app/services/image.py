from google import genai
from google.genai import types
from app.config import GOOGLE_API_KEY

client = genai.Client(api_key=GOOGLE_API_KEY)


def generate_image(image_prompt: str) -> bytes:
    prompt = (
        f"Children's book illustration, colorful, cute, safe for kids, no text. "
        f"{image_prompt}"
    )
    response = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
        ),
    )
    return response.generated_images[0].image.image_bytes
