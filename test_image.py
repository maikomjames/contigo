"""
Script para testar localmente a geração de história + imagem.
Uso: python test_image.py "pikachu na floresta"
"""
import sys
from pathlib import Path

from app.services.claude import generate_story, generate_image_prompt
from app.services.image import generate_image

user_input = " ".join(sys.argv[1:]) or "pikachu na floresta"

print(f"\nInput: {user_input}")
print("Gerando história...")
story = generate_story(user_input)
print(f"\n--- HISTÓRIA ---\n{story}\n")

print("Gerando prompt da imagem...")
image_prompt = generate_image_prompt(story)
print(f"\n--- PROMPT ---\n{image_prompt}\n")

print("Gerando imagem...")
image_bytes = generate_image(image_prompt)

output = Path("test_output.png")
output.write_bytes(image_bytes)
print(f"Imagem salva em: {output.resolve()} ({len(image_bytes) // 1024}KB)")
