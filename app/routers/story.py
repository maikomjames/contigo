from typing import Optional
from fastapi import APIRouter, Query, Request, Header, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.claude import generate_story, generate_image_prompt
from app.services.image import generate_image
from app.services.tts import generate_audio
from app.services.database import get_user_from_token, count_stories_today, is_premium, log_story, ensure_profile, get_profile, DAILY_LIMIT
from app.config import SUPABASE_URL, SUPABASE_KEY, STRIPE_PAYMENT_LINK

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
  <title>Contigo</title>
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
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
    input[type=text], input[type=number], input[type=email], input[type=password] {{
      padding: 10px 14px; border: 2px solid #e0d4f5; border-radius: 10px;
      font-size: 1rem; font-family: inherit; outline: none; transition: border 0.2s; width: 100%;
    }}
    input:focus {{ border-color: #7c4dbe; }}

    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
    .chip {{ padding: 6px 14px; border: 2px solid #e0d4f5; border-radius: 20px; background: white; font-size: 0.85rem; font-family: inherit; cursor: pointer; transition: all 0.15s; color: #555; }}
    .chip.active {{ background: #7c4dbe; border-color: #7c4dbe; color: white; }}

    .prompt-row {{ display: flex; gap: 10px; }}
    .prompt-row input {{ flex: 1; }}

    button.primary {{ padding: 12px 24px; background: #7c4dbe; color: white; border: none; border-radius: 12px; font-size: 1rem; cursor: pointer; transition: background 0.2s; white-space: nowrap; }}
    button.primary:hover {{ background: #6a3daa; }}
    button.primary:disabled {{ background: #bbb; cursor: not-allowed; }}
    button.secondary {{ padding: 8px 16px; background: transparent; color: #7c4dbe; border: 2px solid #e0d4f5; border-radius: 10px; font-size: 0.9rem; cursor: pointer; font-family: inherit; }}
    button.secondary:hover {{ border-color: #7c4dbe; }}

    .auth-tabs {{ display: flex; gap: 0; margin-bottom: 20px; border-bottom: 2px solid #e0d4f5; }}
    .auth-tab {{ padding: 8px 20px; border: none; background: none; cursor: pointer; font-family: inherit; font-size: 0.95rem; color: #888; border-bottom: 2px solid transparent; margin-bottom: -2px; }}
    .auth-tab.active {{ color: #7c4dbe; border-bottom-color: #7c4dbe; font-weight: bold; }}

    .user-bar {{ width: 100%; max-width: 600px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; font-size: 0.85rem; color: #888; }}
    .limit-badge {{ background: #f3eeff; color: #7c4dbe; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; }}
    .limit-badge.esgotado {{ background: #fde8e8; color: #c0392b; }}

    #result {{ width: 100%; max-width: 600px; margin-top: 8px; display: none; }}
    #result img {{ width: 100%; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.12); }}
    .story {{ font-size: 1.05rem; line-height: 1.85; }}
    .story p {{ margin-bottom: 14px; }}

    #loading {{ display: none; margin-top: 32px; text-align: center; color: #7c4dbe; font-size: 0.95rem; }}
    .spinner {{ width: 36px; height: 36px; border: 3px solid #e0d4f5; border-top-color: #7c4dbe; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    #error {{ display: none; margin-top: 16px; color: #c0392b; font-size: 0.9rem; max-width: 600px; }}
    .upgrade-banner {{ background: #f3eeff; border: 2px solid #e0d4f5; border-radius: 12px; padding: 16px 20px; text-align: center; display: none; width: 100%; max-width: 600px; margin-top: 16px; }}
    .upgrade-banner p {{ color: #555; margin-bottom: 12px; font-size: 0.95rem; }}
  </style>
</head>
<body>
  <h1>Contigo</h1>
  <p class="subtitle">Histórias infantis personalizadas com ilustração</p>

  <!-- AUTH -->
  <div id="auth-section" class="card" style="max-width:600px;width:100%;">
    <div class="auth-tabs">
      <button class="auth-tab active" onclick="switchTab('login')">Entrar</button>
      <button class="auth-tab" onclick="switchTab('signup')">Criar conta</button>
    </div>
    <div id="tab-login">
      <div class="field" style="margin-bottom:12px">
        <label>E-mail</label>
        <input id="login-email" type="email" placeholder="seu@email.com">
      </div>
      <div class="field" style="margin-bottom:20px">
        <label>Senha</label>
        <input id="login-password" type="password" placeholder="••••••••">
      </div>
      <button class="primary" style="width:100%" onclick="login()">Entrar</button>
    </div>
    <div id="tab-signup" style="display:none">
      <div class="field" style="margin-bottom:12px">
        <label>E-mail</label>
        <input id="signup-email" type="email" placeholder="seu@email.com">
      </div>
      <div class="field" style="margin-bottom:20px">
        <label>Senha</label>
        <input id="signup-password" type="password" placeholder="mínimo 6 caracteres">
      </div>
      <button class="primary" style="width:100%" onclick="signup()">Criar conta</button>
    </div>
    <div id="auth-error" style="display:none;color:#c0392b;font-size:0.85rem;margin-top:12px;"></div>
  </div>

  <!-- APP -->
  <div id="app-section" style="display:none;width:100%;display:none;flex-direction:column;align-items:center;">
    <div class="user-bar">
      <span id="user-email-display"></span>
      <div style="display:flex;gap:8px;align-items:center;">
        <span id="limit-display" class="limit-badge"></span>
        <button class="secondary" onclick="logout()">Sair</button>
      </div>
    </div>

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

    <div class="upgrade-banner" id="upgrade-banner">
      <p>Você usou sua história gratuita de hoje. Assine para gerar histórias ilimitadas.</p>
      <button class="primary" onclick="openCheckout()">Assinar agora</button>
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
  </div>

  <script>
    const {{ createClient }} = supabase
    const sb = createClient('{SUPABASE_URL}', '{SUPABASE_KEY}')
    let currentSession = null

    async function init() {{
      const {{ data: {{ session }} }} = await sb.auth.getSession()
      if (session) showApp(session)
      else showAuth()
    }}

    sb.auth.onAuthStateChange((event, session) => {{
      if (session) showApp(session)
      else showAuth()
    }})

    function showAuth() {{
      currentSession = null
      document.getElementById('auth-section').style.display = 'block'
      document.getElementById('app-section').style.display = 'none'
    }}

    function showApp(session) {{
      currentSession = session
      document.getElementById('auth-section').style.display = 'none'
      document.getElementById('app-section').style.display = 'flex'
      document.getElementById('user-email-display').textContent = session.user.email
      updateLimitDisplay()
    }}

    const PAYMENT_LINK = '{STRIPE_PAYMENT_LINK}'

    function openCheckout() {{
      const url = `${{PAYMENT_LINK}}?client_reference_id=${{currentSession.user.id}}&prefilled_email=${{encodeURIComponent(currentSession.user.email)}}`
      window.open(url, '_blank')
    }}

    async function updateLimitDisplay() {{
      const res = await fetch('/story/usage', {{
        headers: {{ 'Authorization': `Bearer ${{currentSession.access_token}}` }}
      }})
      if (!res.ok) return
      const data = await res.json()
      const el = document.getElementById('limit-display')
      const banner = document.getElementById('upgrade-banner')
      const btn = document.getElementById('btn')
      if (data.is_premium) {{
        el.textContent = 'ilimitado'
        el.className = 'limit-badge'
        banner.style.display = 'none'
        btn.disabled = false
      }} else {{
        const remaining = Math.max(0, {DAILY_LIMIT} - data.count_today)
        el.textContent = `${{remaining}} história${{remaining !== 1 ? 's' : ''}} hoje`
        el.className = remaining === 0 ? 'limit-badge esgotado' : 'limit-badge'
        banner.style.display = remaining === 0 ? 'block' : 'none'
        btn.disabled = remaining === 0
      }}
    }}

    function switchTab(tab) {{
      document.getElementById('tab-login').style.display = tab === 'login' ? 'block' : 'none'
      document.getElementById('tab-signup').style.display = tab === 'signup' ? 'block' : 'none'
      document.querySelectorAll('.auth-tab').forEach((t, i) => t.classList.toggle('active', (i === 0) === (tab === 'login')))
      document.getElementById('auth-error').style.display = 'none'
    }}

    async function login() {{
      const email = document.getElementById('login-email').value.trim()
      const password = document.getElementById('login-password').value
      const {{ error }} = await sb.auth.signInWithPassword({{ email, password }})
      if (error) showAuthError(error.message)
    }}

    async function signup() {{
      const email = document.getElementById('signup-email').value.trim()
      const password = document.getElementById('signup-password').value
      const {{ error }} = await sb.auth.signUp({{ email, password }})
      if (error) showAuthError(error.message)
      else showAuthError('Verifique seu e-mail para confirmar o cadastro.', '#27ae60')
    }}

    async function logout() {{
      await sb.auth.signOut()
    }}

    function showAuthError(msg, color = '#c0392b') {{
      const el = document.getElementById('auth-error')
      el.textContent = msg
      el.style.color = color
      el.style.display = 'block'
    }}

    function toggleTheme(el) {{
      el.classList.toggle('active')
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      document.getElementById('prompt').addEventListener('keydown', e => {{
        if (e.key === 'Enter') generate()
      }})
    }})

    async function generate() {{
      const prompt = document.getElementById('prompt').value.trim()
      if (!prompt) return

      const params = new URLSearchParams({{ prompt }})
      const name = document.getElementById('child_name').value.trim()
      const age = document.getElementById('child_age').value.trim()
      const themes = [...document.querySelectorAll('.chip.active')].map(c => c.dataset.value)
      if (name) params.set('child_name', name)
      if (age) params.set('child_age', age)
      if (themes.length) params.set('themes', themes.join(','))

      document.getElementById('btn').disabled = true
      document.getElementById('loading').style.display = 'block'
      document.getElementById('result').style.display = 'none'
      document.getElementById('error').style.display = 'none'
      document.getElementById('upgrade-banner').style.display = 'none'

      try {{
        const res = await fetch(`/story?${{params}}`, {{
          method: 'POST',
          headers: {{ 'Authorization': `Bearer ${{currentSession.access_token}}` }}
        }})

        if (res.status === 402) {{
          document.getElementById('upgrade-banner').style.display = 'block'
          return
        }}
        if (!res.ok) throw new Error('Erro ao gerar história.')
        const data = await res.json()

        document.getElementById('img').src = data.image_url
        document.getElementById('story').innerHTML = data.story
          .split('\\n').filter(l => l.trim()).map(l => `<p>${{l}}</p>`).join('')
        document.getElementById('audio').src = data.audio_url
        document.getElementById('result').style.display = 'block'
        updateLimitDisplay()
      }} catch (err) {{
        document.getElementById('error').textContent = err.message
        document.getElementById('error').style.display = 'block'
      }} finally {{
        document.getElementById('btn').disabled = false
        document.getElementById('loading').style.display = 'none'
      }}
    }}

    init()
  </script>
</body>
</html>"""


@router.get("/story/usage")
def story_usage(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = authorization.split(" ")[1]
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401)
    profile = get_profile(user.id, token)
    premium = is_premium(user.id, token)
    count = count_stories_today(user.id, token)
    return JSONResponse({
        "is_premium": premium,
        "count_today": count,
        "daily_limit": DAILY_LIMIT,
        "premium_expires_at": profile.get("premium_expires_at"),
    })


@router.post("/story")
def create_story(
    request: Request,
    prompt: str = Query(...),
    child_name: Optional[str] = Query(None),
    child_age: Optional[int] = Query(None),
    themes: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    token = authorization.split(" ")[1]

    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    ensure_profile(user.id, token)

    if not is_premium(user.id, token):
        count = count_stories_today(user.id, token)
        if count >= DAILY_LIMIT:
            raise HTTPException(status_code=402, detail="Limite diário atingido")

    theme_list = themes.split(",") if themes else []
    story = generate_story(prompt, child_name=child_name, child_age=child_age, themes=theme_list)

    image_prompt = generate_image_prompt(story)
    image_url = generate_image(image_prompt)

    audio_path = generate_audio(story)
    base = str(request.base_url).rstrip("/")
    audio_url = f"{base}/audio/{audio_path.name}"

    log_story(user.id, prompt, token)

    return JSONResponse({
        "story": story,
        "image_prompt": image_prompt,
        "image_url": image_url,
        "audio_url": audio_url,
    })
