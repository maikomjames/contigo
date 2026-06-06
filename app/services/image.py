from google import genai
from google.genai import types
from app.config import GOOGLE_API_KEY

client = genai.Client(api_key=GOOGLE_API_KEY)


def generate_image(image_prompt: str) -> bytes:
    prompt = (
        f"Children's book illustration, colorful, cute, safe for kids, no text. "
        f"{image_prompt}"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return part.inline_data.data

    raise ValueError("Nenhuma imagem retornada pelo Gemini")
