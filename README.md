# Contigo

Bot de WhatsApp que cria histórias infantis personalizadas com IA — para pais que querem transformar a hora de dormir em um momento especial com seus filhos.

O pai configura os temas que quer trabalhar com a criança (paciência, amizade, coragem...) e o filho escolhe o personagem e o cenário. O Contigo gera uma história narrada, com imagem ilustrativa, feita sob medida para aquela noite.

## Como funciona

```
Pai abre o WhatsApp → manda o que o filho quer → recebe história + imagem + áudio
```

Na primeira vez, o bot guia o pai por um setup rápido: nome da criança, idioma, temas a abordar e tom da história. Depois disso, basta mandar o pedido do filho.

**Plano grátis:** 1 história por dia  
**Plano pago:** ilimitado + narração em áudio + biblioteca salva

## Stack

- **Backend:** Python + FastAPI
- **Canal:** WhatsApp via Twilio
- **IA:** Claude API (histórias) · DALL-E 3 (imagens) · OpenAI TTS (narração)
- **Banco:** Supabase
- **Pagamentos:** Stripe
- **Hospedagem:** Railway

## Rodando localmente

```bash
# 1. Clonar o repositório
git clone git@github.com:maikomjames/contigo.git
cd contigo

# 2. Criar ambiente virtual e instalar dependências
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves

# 4. Iniciar o servidor
uvicorn app.main:app --reload
```

O servidor sobe em `http://localhost:8000`. O endpoint de saúde responde em `GET /`.

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição |
|---|---|
| `TWILIO_ACCOUNT_SID` | Account SID do Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token do Twilio |
| `TWILIO_WHATSAPP_FROM` | Número do Twilio no formato `whatsapp:+14155238886` |
| `ANTHROPIC_API_KEY` | Chave da API da Anthropic (Claude) |
| `OPENAI_API_KEY` | Chave da API da OpenAI (DALL-E + TTS) |
| `SUPABASE_URL` | URL do projeto no Supabase |
| `SUPABASE_KEY` | Chave anon do Supabase |
| `STRIPE_SECRET_KEY` | Chave secreta do Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret do webhook do Stripe |
| `STRIPE_PAYMENT_LINK` | Link do checkout de assinatura |

## Deploy no Railway

1. Conecte o repositório no [Railway](https://railway.app)
2. Configure as variáveis de ambiente no painel do Railway
3. O Railway detecta o `railway.toml` e faz o deploy automaticamente
4. Use a URL gerada pelo Railway como webhook no Twilio:
   ```
   https://seu-app.railway.app/webhook
   ```

## Estrutura do projeto

```
app/
├── main.py              # Entry point FastAPI
├── config.py            # Variáveis de ambiente
├── routers/
│   └── webhook.py       # POST /webhook — recebe mensagens do Twilio
├── bot/
│   └── handler.py       # Lógica de resposta do bot
└── services/
    ├── twilio.py        # Envio de mensagens e mídia
    ├── claude.py        # Geração de histórias (Fase 2)
    ├── image.py         # Geração de imagens (Fase 2)
    └── tts.py           # Narração em áudio (Fase 2)
```

## Plano de construção

| Fase | O que entrega | Status |
|---|---|---|
| 1 — Bot respondendo | Webhook funcionando, bot responde no WhatsApp | ✅ |
| 2 — Geração de história | História + imagem + áudio a partir de um input | 🔜 |
| 3 — Perfil e setup | Onboarding conversacional, histórias personalizadas | 🔜 |
| 4 — Limite e pagamento | Freemium com Stripe | 🔜 |
| 5 — Robustez | Erros, comandos, testes com usuários reais | 🔜 |
