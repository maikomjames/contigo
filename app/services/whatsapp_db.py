from datetime import date, datetime, timedelta, timezone
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

DAILY_LIMIT = 1
THEMES_LIST = [
    "amizade", "coragem", "persistência", "generosidade",
    "paciência", "aventura", "curiosidade", "respeito",
]

_db = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_whatsapp_profile(phone: str) -> dict | None:
    response = _db.table("whatsapp_profiles").select("*").eq("phone", phone).execute()
    return response.data[0] if response.data else None


def create_whatsapp_profile(phone: str):
    _db.table("whatsapp_profiles").insert({
        "phone": phone,
        "onboarding_step": "waiting_name",
    }).execute()


def update_whatsapp_profile(phone: str, **kwargs):
    kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
    _db.table("whatsapp_profiles").update(kwargs).eq("phone", phone).execute()


def count_whatsapp_stories_today(phone: str) -> int:
    today = date.today().isoformat()
    response = (
        _db.table("whatsapp_story_logs")
        .select("id", count="exact")
        .eq("phone", phone)
        .gte("created_at", f"{today}T00:00:00+00:00")
        .execute()
    )
    return response.count or 0


def log_whatsapp_story(phone: str, prompt: str):
    _db.table("whatsapp_story_logs").insert({
        "phone": phone,
        "prompt": prompt,
    }).execute()


def is_whatsapp_premium(phone: str) -> bool:
    try:
        response = (
            _db.table("whatsapp_profiles")
            .select("is_premium, premium_expires_at")
            .eq("phone", phone)
            .execute()
        )
        if not response.data:
            return False
        profile = response.data[0]
        if not profile.get("is_premium"):
            return False
        expires_at = profile.get("premium_expires_at")
        if not expires_at:
            return True
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return expiry > datetime.now(timezone.utc)
    except Exception:
        return False


def set_whatsapp_premium(phone: str, days: int = 30):
    expires_at = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    _db.table("whatsapp_profiles").update({
        "is_premium": True,
        "premium_expires_at": expires_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("phone", phone).execute()
