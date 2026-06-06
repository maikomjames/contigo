import fal_client


def generate_image(image_prompt: str) -> bytes:
    prompt = (
        f"Children's book illustration, colorful, cute, safe for kids, no text. "
        f"{image_prompt}"
    )

    result = fal_client.subscribe(
        "fal-ai/flux-1/dev",
        arguments={
            "prompt": prompt,
            "image_size": "square_hd",
        },
    )

    image_url = result["images"][0]["url"]

    import httpx
    response = httpx.get(image_url)
    response.raise_for_status()
    return response.content
