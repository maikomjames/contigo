from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.claude import generate_story, generate_image_prompt
from app.services.image import generate_image

router = APIRouter()


@router.get("/playground", response_class=HTMLResponse)
def playground():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contigo — Playground</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Georgia, serif; background: #fdf8f0; color: #333; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }
    h1 { font-size: 1.8rem; color: #7c4dbe; margin-bottom: 8px; }
    p.subtitle { color: #888; font-size: 0.95rem; margin-bottom: 32px; }
    .form { display: flex; gap: 10px; width: 100%; max-width: 600px; }
    input { flex: 1; padding: 12px 16px; border: 2px solid #e0d4f5; border-radius: 12px; font-size: 1rem; font-family: inherit; outline: none; transition: border 0.2s; }
    input:focus { border-color: #7c4dbe; }
    button { padding: 12px 24px; background: #7c4dbe; color: white; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
    button:hover { background: #6a3daa; }
    button:disabled { background: #bbb; cursor: not-allowed; }
    #result { width: 100%; max-width: 600px; margin-top: 40px; display: none; }
    #result img { width: 100%; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.12); }
    #result .story { font-size: 1.05rem; line-height: 1.85; }
    #result .story p { margin-bottom: 14px; }
    #result audio { width: 100%; margin-top: 24px; }
    #loading { display: none; margin-top: 40px; text-align: center; color: #7c4dbe; font-size: 0.95rem; }
    .spinner { width: 36px; height: 36px; border: 3px solid #e0d4f5; border-top-color: #7c4dbe; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
    @keyframes spin { to { transform: rotate(360deg); } }
    #error { display: none; margin-top: 24px; color: #c0392b; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Contigo</h1>
  <p class="subtitle">Histórias infantis personalizadas com ilustração</p>

  <div class="form">
    <input id="prompt" type="text" placeholder="Ex: pikachu na floresta, goku no espaço..." autofocus>
    <button id="btn" onclick="generate()">Criar história</button>
  </div>

  <div id="loading">
    <div class="spinner"></div>
    Gerando história e ilustração...
  </div>

  <div id="error"></div>

  <div id="result">
    <img id="img" src="" alt="Ilustração">
    <div id="story" class="story"></div>
  </div>

  <script>
    document.getElementById("prompt").addEventListener("keydown", e => {
      if (e.key === "Enter") generate();
    });

    async function generate() {
      const prompt = document.getElementById("prompt").value.trim();
      if (!prompt) return;

      document.getElementById("btn").disabled = true;
      document.getElementById("loading").style.display = "block";
      document.getElementById("result").style.display = "none";
      document.getElementById("error").style.display = "none";

      try {
        const res = await fetch(`/story?prompt=${encodeURIComponent(prompt)}`, { method: "POST" });
        if (!res.ok) throw new Error("Erro ao gerar história.");
        const data = await res.json();

        document.getElementById("img").src = data.image_url;
        document.getElementById("story").innerHTML = data.story
          .split("\\n")
          .filter(l => l.trim())
          .map(l => `<p>${l}</p>`)
          .join("");
        document.getElementById("result").style.display = "block";
      } catch (err) {
        document.getElementById("error").textContent = err.message;
        document.getElementById("error").style.display = "block";
      } finally {
        document.getElementById("btn").disabled = false;
        document.getElementById("loading").style.display = "none";
      }
    }
  </script>
</body>
</html>"""


@router.post("/story")
def create_story(prompt: str = Query(..., description="Ex: pikachu na floresta")):
    story = generate_story(prompt)

    image_prompt = generate_image_prompt(story)
    image_url = generate_image(image_prompt)

    return JSONResponse({
        "story": story,
        "image_prompt": image_prompt,
        "image_url": image_url,
    })
