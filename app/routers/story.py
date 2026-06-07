from typing import Optional
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.claude import generate_story, generate_image_prompt
from app.services.image import generate_image
from app.services.tts import generate_audio

router = APIRouter()

THEMES = [
    "amizade", "coragem", "persistência", "generosidade",
    "paciência", "aventura", "curiosidade", "respeito",
]


@router.get("/playground", response_class=HTMLResponse)
def playground():
    theme_chips = "".join(
        f'<button type="button" class="chip" onclick="toggleTheme(this)" data-value="{t}">{t}</button>'
        for t in THEMES
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contigo — Playground</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Georgia, serif; background: #fdf8f0; color: #333; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40px 20px; }}
    h1 {{ font-size: 1.8rem; color: #7c4dbe; margin-bottom: 8px; }}
    p.subtitle {{ color: #888; font-size: 0.95rem; margin-bottom: 32px; }}

    .card {{ width: 100%; max-width: 600px; background: white; border-radius: 16px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 16px; }}
    .card h2 {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; color: #7c4dbe; margin-bottom: 16px; }}

    .row {{ display: flex; gap: 12px; }}
    .field {{ display: flex; flex-direction: column; gap: 6px; flex: 1; }}
    .field label {{ font-size: 0.85rem; color: #666; }}
    input[type=text], input[type=number], select {{
      padding: 10px 14px; border: 2px solid #e0d4f5; border-radius: 10px;
      font-size: 1rem; font-family: inherit; outline: none; transition: border 0.2s; width: 100%;
    }}
    input:focus, select:focus {{ border-color: #7c4dbe; }}

    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
    .chip {{
      padding: 6px 14px; border: 2px solid #e0d4f5; border-radius: 20px;
      background: white; font-size: 0.85rem; font-family: inherit; cursor: pointer;
      transition: all 0.15s; color: #555;
    }}
    .chip.active {{ background: #7c4dbe; border-color: #7c4dbe; color: white; }}

    .prompt-row {{ display: flex; gap: 10px; }}
    .prompt-row input {{ flex: 1; }}

    button.primary {{
      padding: 12px 24px; background: #7c4dbe; color: white; border: none;
      border-radius: 12px; font-size: 1rem; cursor: pointer; transition: background 0.2s; white-space: nowrap;
    }}
    button.primary:hover {{ background: #6a3daa; }}
    button.primary:disabled {{ background: #bbb; cursor: not-allowed; }}

    #result {{ width: 100%; max-width: 600px; margin-top: 8px; display: none; }}
    #result img {{ width: 100%; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.12); }}
    .story {{ font-size: 1.05rem; line-height: 1.85; }}
    .story p {{ margin-bottom: 14px; }}
    #loading {{ display: none; margin-top: 32px; text-align: center; color: #7c4dbe; font-size: 0.95rem; }}
    .spinner {{ width: 36px; height: 36px; border: 3px solid #e0d4f5; border-top-color: #7c4dbe; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    #error {{ display: none; margin-top: 16px; color: #c0392b; font-size: 0.9rem; max-width: 600px; }}
  </style>
</head>
<body>
  <h1>Contigo</h1>
  <p class="subtitle">Histórias infantis personalizadas com ilustração</p>

  <div class="card">
    <h2>Perfil da criança</h2>
    <div class="row">
      <div class="field">
        <label>Nome</label>
        <input id="child_name" type="text" placeholder="Ex: Pedro">
      </div>
      <div class="field" style="max-width:120px">
        <label>Idade</label>
        <input id="child_age" type="number" min="2" max="10" placeholder="5">
      </div>
    </div>
    <div class="field" style="margin-top:16px">
      <label>Temas (opcional)</label>
      <div class="chips">{theme_chips}</div>
    </div>
  </div>

  <div class="card">
    <h2>O que a criança quer ouvir hoje?</h2>
    <div class="prompt-row">
      <input id="prompt" type="text" placeholder="Ex: pikachu na floresta, goku no espaço...">
      <button class="primary" id="btn" onclick="generate()">Criar</button>
    </div>
  </div>

  <div id="loading">
    <div class="spinner"></div>
    Gerando história e ilustração...
  </div>

  <div id="error"></div>

  <div id="result">
    <img id="img" src="" alt="Ilustração">
    <div id="story" class="story"></div>
    <audio id="audio" controls style="width:100%;margin-top:24px;"></audio>
  </div>

  <script>
    document.getElementById("prompt").addEventListener("keydown", e => {{
      if (e.key === "Enter") generate();
    }});

    function toggleTheme(el) {{
      el.classList.toggle("active");
    }}

    async function generate() {{
      const prompt = document.getElementById("prompt").value.trim();
      if (!prompt) return;

      const params = new URLSearchParams({{ prompt }});
      const name = document.getElementById("child_name").value.trim();
      const age = document.getElementById("child_age").value.trim();
      const themes = [...document.querySelectorAll(".chip.active")].map(c => c.dataset.value);

      if (name) params.set("child_name", name);
      if (age) params.set("child_age", age);
      if (themes.length) params.set("themes", themes.join(","));

      document.getElementById("btn").disabled = true;
      document.getElementById("loading").style.display = "block";
      document.getElementById("result").style.display = "none";
      document.getElementById("error").style.display = "none";

      try {{
        const res = await fetch(`/story?${{params}}`, {{ method: "POST" }});
        if (!res.ok) throw new Error("Erro ao gerar história.");
        const data = await res.json();

        document.getElementById("img").src = data.image_url;
        document.getElementById("story").innerHTML = data.story
          .split("\\n")
          .filter(l => l.trim())
          .map(l => `<p>${{l}}</p>`)
          .join("");
        document.getElementById("audio").src = data.audio_url;
        document.getElementById("result").style.display = "block";
      }} catch (err) {{
        document.getElementById("error").textContent = err.message;
        document.getElementById("error").style.display = "block";
      }} finally {{
        document.getElementById("btn").disabled = false;
        document.getElementById("loading").style.display = "none";
      }}
    }}
  </script>
</body>
</html>"""


@router.post("/story")
def create_story(
    request: Request,
    prompt: str = Query(...),
    child_name: Optional[str] = Query(None),
    child_age: Optional[int] = Query(None),
    themes: Optional[str] = Query(None),
):
    theme_list = themes.split(",") if themes else []
    story = generate_story(prompt, child_name=child_name, child_age=child_age, themes=theme_list)

    image_prompt = generate_image_prompt(story)
    image_url = generate_image(image_prompt)

    audio_path = generate_audio(story)
    base = str(request.base_url).rstrip("/")
    audio_url = f"{base}/audio/{audio_path.name}"

    return JSONResponse({
        "story": story,
        "image_prompt": image_prompt,
        "image_url": image_url,
        "audio_url": audio_url,
    })
