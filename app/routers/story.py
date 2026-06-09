import asyncio
import json
from typing import Optional
from fastapi import APIRouter, Query, Request, Header, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from app.services.claude import generate_story_stream, generate_image_prompt, clarify_input
from app.services.image import generate_image
from app.services.tts import generate_audio
from app.services.database import get_user_from_token, count_stories_today, is_premium, log_story, ensure_profile, get_profile, DAILY_LIMIT
from app.config import SUPABASE_URL, SUPABASE_KEY, STRIPE_PAYMENT_LINK

router = APIRouter()

THEMES = [
    "amizade", "coragem", "persistência", "generosidade",
    "paciência", "aventura", "curiosidade", "respeito",
]


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


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
  <script src="https://cdn.tailwindcss.com/3.4.17"></script>
  <link href="https://fonts.googleapis.com/css2?family=Alegreya:wght@400;700&family=Alegreya+Sans:wght@400;500;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <style>
    body {{ font-family: 'Alegreya Sans', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Alegreya', serif; }}
    input, textarea, select {{ font-family: 'Alegreya Sans', sans-serif; }}

    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(12px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-10px); }} }}
    @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
    @keyframes shimmer {{ 0% {{ background-position:-200% 0; }} 100% {{ background-position:200% 0; }} }}

    .fade-in {{ animation: fadeIn 0.5s ease; }}
    .float-anim {{ animation: float 2.2s ease-in-out infinite; }}

    .chip {{
      padding: 5px 14px; border: 2px solid #ddd6fe; border-radius: 9999px;
      background: white; font-size: 0.82rem; font-family: 'Alegreya Sans', sans-serif;
      cursor: pointer; transition: all 0.15s; color: #7c3aed; font-weight: 500;
    }}
    .chip.active {{ background: #7c3aed; border-color: #7c3aed; color: white; }}

    .auth-tab {{
      padding: 8px 22px; border: none; background: none; cursor: pointer;
      font-family: 'Alegreya Sans', sans-serif; font-size: 1rem; color: #a78bfa;
      border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s;
    }}
    .auth-tab.active {{ color: #7c3aed; border-bottom-color: #7c3aed; font-weight: 700; }}

    .limit-badge {{
      font-size: 0.78rem; font-weight: 600; padding: 3px 12px; border-radius: 9999px;
      background: #ede9fe; color: #7c3aed;
    }}
    .limit-badge.esgotado {{ background: #fee2e2; color: #dc2626; }}

    .skeleton {{
      background: linear-gradient(90deg, #f3e8ff 25%, #ede9fe 50%, #f3e8ff 75%);
      background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 24px; height: 280px;
    }}
    .status-spinner {{
      width: 15px; height: 15px; border: 2px solid #ddd6fe;
      border-top-color: #7c3aed; border-radius: 50%;
      animation: spin 0.8s linear infinite; flex-shrink: 0;
    }}
    .story-body {{ font-size: 1.05rem; line-height: 1.9; color: #374151; white-space: pre-wrap; }}
    .story-body p {{ margin-bottom: 1rem; white-space: normal; }}
    .audio-placeholder {{ text-align:center; color:#c4b5fd; font-size:0.85rem; padding:16px 0; }}

    #btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  </style>
</head>
<body style="background: linear-gradient(160deg, #f3e8ff 0%, #ede9fe 50%, #faf5ff 100%); min-height:100vh;">

  <!-- Header -->
  <div style="text-align:center; padding:40px 16px 28px;">
    <h1 style="font-size:2.8rem; color:#4c1d95; font-weight:700; margin:0;">Contigo</h1>
    <p style="color:#7c3aed; font-size:1.05rem; margin:6px 0 0;">Histórias que aquecem o coração</p>
  </div>

  <!-- AUTH -->
  <div id="auth-section" class="fade-in" style="max-width:440px; margin:0 auto; padding:0 16px 60px;">
    <div style="background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border-radius:28px; box-shadow:0 8px 40px rgba(124,58,237,0.12); border:1px solid #ede9fe; padding:32px;">
      <div style="display:flex; border-bottom:2px solid #ede9fe; margin-bottom:24px;">
        <button class="auth-tab active" onclick="switchTab('login')">Entrar</button>
        <button class="auth-tab" onclick="switchTab('signup')">Criar conta</button>
      </div>
      <div id="tab-login">
        <div style="margin-bottom:14px;">
          <label style="display:block; font-size:0.85rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">E-mail</label>
          <input id="login-email" type="email" placeholder="seu@email.com" style="width:100%; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; transition:border 0.2s; box-sizing:border-box;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
        <div style="margin-bottom:24px;">
          <label style="display:block; font-size:0.85rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">Senha</label>
          <input id="login-password" type="password" placeholder="••••••••" style="width:100%; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; transition:border 0.2s; box-sizing:border-box;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
        <button onclick="login()" style="width:100%; padding:13px; border-radius:9999px; background:#7c3aed; color:white; font-weight:700; font-size:1rem; font-family:inherit; border:none; cursor:pointer; box-shadow:0 4px 16px rgba(124,58,237,0.35);">Entrar</button>
      </div>
      <div id="tab-signup" style="display:none;">
        <div style="margin-bottom:14px;">
          <label style="display:block; font-size:0.85rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">E-mail</label>
          <input id="signup-email" type="email" placeholder="seu@email.com" style="width:100%; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; transition:border 0.2s; box-sizing:border-box;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
        <div style="margin-bottom:24px;">
          <label style="display:block; font-size:0.85rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">Senha</label>
          <input id="signup-password" type="password" placeholder="mínimo 6 caracteres" style="width:100%; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; transition:border 0.2s; box-sizing:border-box;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
        <button onclick="signup()" style="width:100%; padding:13px; border-radius:9999px; background:#7c3aed; color:white; font-weight:700; font-size:1rem; font-family:inherit; border:none; cursor:pointer; box-shadow:0 4px 16px rgba(124,58,237,0.35);">Criar conta</button>
      </div>
      <div id="auth-error" style="display:none; font-size:0.85rem; margin-top:14px;"></div>
    </div>
  </div>

  <!-- APP -->
  <div id="app-section" style="display:none; flex-direction:column; align-items:center; width:100%; max-width:600px; margin:0 auto; padding:0 16px 60px;">

    <!-- User bar -->
    <div style="display:flex; justify-content:space-between; align-items:center; width:100%; margin-bottom:16px; padding:0 4px;">
      <span id="user-email-display" style="font-size:0.82rem; color:#7c3aed;"></span>
      <div style="display:flex; gap:8px; align-items:center;">
        <span id="limit-display" class="limit-badge"></span>
        <button onclick="logout()" style="font-size:0.82rem; padding:4px 14px; border-radius:9999px; border:1.5px solid #ddd6fe; background:white; color:#7c3aed; cursor:pointer; font-family:inherit;">Sair</button>
      </div>
    </div>

    <!-- Profile card -->
    <div style="width:100%; background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border-radius:28px; box-shadow:0 4px 24px rgba(124,58,237,0.1); border:1px solid #ede9fe; padding:24px; margin-bottom:14px;">
      <h2 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#7c3aed; margin:0 0 16px;">👦 Perfil da criança</h2>
      <div style="display:flex; gap:12px; margin-bottom:16px;">
        <div style="flex:1;">
          <label style="display:block; font-size:0.8rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">Nome</label>
          <input id="child_name" type="text" placeholder="Ex: Pedro" style="width:100%; border:2px solid #ddd6fe; border-radius:12px; padding:9px 14px; font-size:0.95rem; outline:none; box-sizing:border-box; transition:border 0.2s;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
        <div style="width:100px;">
          <label style="display:block; font-size:0.8rem; font-weight:600; color:#6d28d9; margin-bottom:6px;">Idade</label>
          <input id="child_age" type="number" min="2" max="12" placeholder="5" style="width:100%; border:2px solid #ddd6fe; border-radius:12px; padding:9px 14px; font-size:0.95rem; outline:none; box-sizing:border-box; transition:border 0.2s;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        </div>
      </div>
      <div>
        <label style="display:block; font-size:0.8rem; font-weight:600; color:#6d28d9; margin-bottom:8px;">Temas (opcional)</label>
        <div style="display:flex; flex-wrap:wrap; gap:8px;">{theme_chips}</div>
      </div>
    </div>

    <!-- Prompt card -->
    <div style="width:100%; background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border-radius:28px; box-shadow:0 4px 24px rgba(124,58,237,0.1); border:1px solid #ede9fe; padding:24px; margin-bottom:14px;">
      <h2 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#7c3aed; margin:0 0 14px;">✨ O que a criança quer ouvir hoje?</h2>
      <div style="display:flex; gap:10px;">
        <input id="prompt" type="text" placeholder="Ex: pikachu na floresta, goku no espaço..." style="flex:1; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; transition:border 0.2s;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'">
        <button id="btn" onclick="generate()" style="padding:10px 22px; border-radius:9999px; background:#7c3aed; color:white; font-weight:700; font-size:0.95rem; font-family:inherit; border:none; cursor:pointer; white-space:nowrap; box-shadow:0 4px 14px rgba(124,58,237,0.3);">Criar ✨</button>
      </div>
    </div>

    <!-- Clarification card -->
    <div id="clarification-card" class="fade-in" style="display:none; width:100%; background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border-radius:28px; box-shadow:0 4px 24px rgba(124,58,237,0.1); border:1px solid #ede9fe; padding:24px; margin-bottom:14px;">
      <h2 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#7c3aed; margin:0 0 14px;">🤔 Conta mais um pouco</h2>
      <div id="clarification-questions" style="font-size:0.95rem; color:#4b5563; line-height:1.85; margin-bottom:16px; white-space:pre-wrap;"></div>
      <textarea id="clarification-answer" rows="3" placeholder="Ex: na floresta com Tails, enfrentando um robô gigante..." style="width:100%; border:2px solid #ddd6fe; border-radius:14px; padding:10px 16px; font-size:0.95rem; outline:none; resize:vertical; box-sizing:border-box; transition:border 0.2s;" onfocus="this.style.borderColor='#7c3aed'" onblur="this.style.borderColor='#ddd6fe'"></textarea>
      <button onclick="generateWithClarification()" style="margin-top:12px; width:100%; padding:13px; border-radius:9999px; background:#7c3aed; color:white; font-weight:700; font-size:1rem; font-family:inherit; border:none; cursor:pointer; box-shadow:0 4px 16px rgba(124,58,237,0.3);">Gerar história ✨</button>
    </div>

    <!-- Upgrade banner -->
    <div id="upgrade-banner" class="fade-in" style="display:none; width:100%; background:rgba(245,243,255,0.95); border:1.5px solid #ddd6fe; border-radius:28px; padding:24px; text-align:center; margin-bottom:14px;">
      <p style="color:#6d28d9; margin-bottom:14px; font-size:0.95rem; line-height:1.6;">Você usou sua história gratuita de hoje.<br>Assine para gerar histórias ilimitadas.</p>
      <button onclick="openCheckout()" style="padding:12px 32px; border-radius:9999px; background:#7c3aed; color:white; font-weight:700; font-size:1rem; font-family:inherit; border:none; cursor:pointer; box-shadow:0 4px 16px rgba(124,58,237,0.3);">Assinar agora ⭐</button>
    </div>

    <!-- Loading -->
    <div id="loading" style="display:none; text-align:center; padding:60px 0;">
      <div style="font-size:3.5rem; margin-bottom:16px;" class="float-anim">📚</div>
      <p style="color:#7c3aed; font-size:1rem; font-weight:500;">Iniciando...</p>
    </div>

    <!-- Error -->
    <div id="error" style="display:none; color:#dc2626; font-size:0.9rem; padding:16px 0;"></div>

    <!-- Result -->
    <div id="result" style="display:none; width:100%;" class="fade-in">

      <!-- Status -->
      <div id="status-msg" style="display:none; align-items:center; justify-content:center; gap:8px; color:#7c3aed; font-size:0.88rem; font-weight:500; padding:8px 0 12px;">
        <span class="status-spinner"></span>
        <span id="status-text"></span>
      </div>

      <!-- Image -->
      <div id="img-container" style="margin-bottom:16px;"></div>

      <!-- Story card -->
      <div style="background:rgba(255,255,255,0.92); backdrop-filter:blur(8px); border-radius:28px; box-shadow:0 4px 24px rgba(124,58,237,0.1); border:1px solid #ede9fe; padding:28px; margin-bottom:16px;">
        <div id="story" class="story-body"></div>
      </div>

      <!-- Audio -->
      <div id="audio-container"></div>

    </div>
  </div>

  <script>
    const {{ createClient }} = supabase
    const sb = createClient('{SUPABASE_URL}', '{SUPABASE_KEY}')
    let currentSession = null
    let pendingPrompt = ''

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
        el.textContent = 'ilimitado ⭐'
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
      else showAuthError('Verifique seu e-mail para confirmar o cadastro.', '#16a34a')
    }}

    async function logout() {{
      await sb.auth.signOut()
    }}

    function showAuthError(msg, color = '#dc2626') {{
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

    function setStatus(msg) {{
      const el = document.getElementById('status-msg')
      document.getElementById('status-text').textContent = msg
      el.style.display = msg ? 'flex' : 'none'
    }}

    function generateWithClarification() {{
      const answers = document.getElementById('clarification-answer').value.trim()
      const enriched = answers ? `${{pendingPrompt}}. ${{answers}}` : pendingPrompt
      document.getElementById('clarification-card').style.display = 'none'
      document.getElementById('clarification-answer').value = ''
      generate(true, enriched)
    }}

    async function generate(skipClarification = false, overridePrompt = null) {{
      const prompt = overridePrompt || document.getElementById('prompt').value.trim()
      if (!prompt) return

      const params = new URLSearchParams({{ prompt }})
      if (skipClarification) params.set('skip_clarification', '1')
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
      document.getElementById('img-container').innerHTML = ''
      document.getElementById('story').innerHTML = ''
      document.getElementById('audio-container').innerHTML = ''
      document.getElementById('clarification-card').style.display = 'none'
      setStatus('')
      pendingPrompt = prompt

      let storyText = ''
      let resultShown = false

      function showResult() {{
        if (!resultShown) {{
          resultShown = true
          document.getElementById('loading').style.display = 'none'
          document.getElementById('result').style.display = 'block'
        }}
      }}

      try {{
        const res = await fetch(`/story?${{params}}`, {{
          method: 'POST',
          headers: {{ 'Authorization': `Bearer ${{currentSession.access_token}}` }}
        }})

        if (res.status === 402) {{
          document.getElementById('loading').style.display = 'none'
          document.getElementById('upgrade-banner').style.display = 'block'
          return
        }}
        if (!res.ok) {{
          const err = await res.json().catch(() => ({{}}))
          throw new Error(err.detail || 'Erro ao gerar história.')
        }}

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {{
          const {{ done, value }} = await reader.read()
          if (done) break

          buffer += decoder.decode(value, {{ stream: true }})

          let idx
          while ((idx = buffer.indexOf('\\n\\n')) !== -1) {{
            const line = buffer.slice(0, idx)
            buffer = buffer.slice(idx + 2)
            if (!line.startsWith('data: ')) continue

            let data
            try {{ data = JSON.parse(line.slice(6)) }} catch {{ continue }}

            switch (data.type) {{
              case 'clarification':
                document.getElementById('loading').style.display = 'none'
                document.getElementById('clarification-questions').textContent = data.questions
                document.getElementById('clarification-card').style.display = 'block'
                document.getElementById('btn').disabled = false
                break

              case 'progress':
                showResult()
                setStatus(data.message)
                if (data.message.includes('ilustração')) {{
                  document.getElementById('img-container').innerHTML = '<div class="skeleton"></div>'
                }} else if (data.message.includes('narração')) {{
                  document.getElementById('audio-container').innerHTML = '<p class="audio-placeholder">Gerando narração...</p>'
                }}
                break

              case 'story_chunk':
                showResult()
                storyText += data.text
                document.getElementById('story').textContent = storyText
                break

              case 'story_done':
                document.getElementById('story').innerHTML = storyText
                  .split('\\n').filter(l => l.trim()).map(l => `<p>${{l}}</p>`).join('')
                break

              case 'image_url':
                document.getElementById('img-container').innerHTML =
                  `<img src="${{data.url}}" alt="Ilustração" style="width:100%;border-radius:24px;box-shadow:0 8px 32px rgba(124,58,237,0.18);margin-bottom:4px;">`
                break

              case 'image_error':
                document.getElementById('img-container').innerHTML = ''
                break

              case 'audio_url':
                document.getElementById('audio-container').innerHTML =
                  `<div style="background:rgba(255,255,255,0.92);border-radius:24px;box-shadow:0 4px 20px rgba(124,58,237,0.1);border:1px solid #ede9fe;padding:20px 24px;">
                    <p style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.1em;color:#7c3aed;font-weight:700;margin:0 0 12px;">🎙 Narração</p>
                    <audio controls style="width:100%;" src="${{data.url}}"></audio>
                  </div>`
                break

              case 'audio_error':
                document.getElementById('audio-container').innerHTML = ''
                break

              case 'done':
                setStatus('')
                updateLimitDisplay()
                break

              case 'error':
                throw new Error(data.message || 'Erro desconhecido')
            }}
          }}
        }}
      }} catch (err) {{
        document.getElementById('error').textContent = err.message
        document.getElementById('error').style.display = 'block'
        if (!resultShown) document.getElementById('loading').style.display = 'none'
      }} finally {{
        document.getElementById('btn').disabled = false
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
async def create_story(
    request: Request,
    prompt: str = Query(...),
    child_name: Optional[str] = Query(None),
    child_age: Optional[int] = Query(None),
    themes: Optional[str] = Query(None),
    skip_clarification: bool = Query(False),
    authorization: Optional[str] = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    token = authorization.split(" ")[1]

    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    await asyncio.to_thread(ensure_profile, user.id, token)

    if not is_premium(user.id, token):
        count = count_stories_today(user.id, token)
        if count >= DAILY_LIMIT:
            raise HTTPException(status_code=402, detail="Limite diário atingido")

    theme_list = themes.split(",") if themes else []
    base_url = str(request.base_url).rstrip("/")
    user_id = user.id

    async def stream():
        story_text = ""
        try:
            if not skip_clarification:
                questions = await asyncio.to_thread(clarify_input, prompt)
                if questions:
                    yield _sse({"type": "clarification", "questions": questions})
                    return

            yield _sse({"type": "progress", "message": "Escrevendo a história..."})

            async for chunk in generate_story_stream(
                prompt, child_name=child_name, child_age=child_age, themes=theme_list
            ):
                story_text += chunk
                yield _sse({"type": "story_chunk", "text": chunk})

            yield _sse({"type": "story_done"})

            await asyncio.to_thread(log_story, user_id, prompt, token)

            yield _sse({"type": "progress", "message": "Criando ilustração..."})
            try:
                image_prompt = await asyncio.to_thread(generate_image_prompt, story_text, prompt)
                image_url = await asyncio.to_thread(generate_image, image_prompt)
                yield _sse({"type": "image_url", "url": image_url})
            except Exception:
                yield _sse({"type": "image_error"})

            yield _sse({"type": "progress", "message": "Gerando narração..."})
            try:
                audio_path = await asyncio.to_thread(generate_audio, story_text)
                audio_url = f"{base_url}/audio/{audio_path.name}"
                yield _sse({"type": "audio_url", "url": audio_url})
            except Exception:
                yield _sse({"type": "audio_error"})

            yield _sse({"type": "done"})

        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
