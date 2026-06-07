from datetime import date, datetime, timedelta, timezone
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

DAILY_LIMIT = 1


def _client(token: str):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.postgrest.auth(token)
    return client


def get_user_from_token(token: str):
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client.auth.get_user(token).user
    except Exception:
        return None


def count_stories_today(user_id: str, token: str) -> int:
    today = date.today().isoformat()
    response = (
        _client(token)
        .table("story_logs")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", f"{today}T00:00:00+00:00")
        .execute()
    )
    return response.count or 0


def ensure_profile(user_id: str, token: str):
    _client(token).table("profiles").upsert(
        {"id": user_id, "is_premium": False},
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()


def get_profile(user_id: str, token: str) -> dict:
    try:
        response = (
            _client(token)
            .table("profiles")
            .select("is_premium, premium_expires_at")
            .eq("id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        return {}
    except Exception:
        return {}


def is_premium(user_id: str, token: str) -> bool:
    try:
        response = (
            _client(token)
            .table("profiles")
            .select("is_premium, premium_expires_at")
            .eq("id", user_id)
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


def set_premium_expiry(user_id: str, days: int = 30):
    expires_at = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.rpc("set_user_premium", {"p_user_id": user_id, "p_expires_at": expires_at}).execute()


def log_story(user_id: str, prompt: str, token: str):
    _client(token).table("story_logs").insert({
        "user_id": user_id,
        "prompt": prompt,
    }).execute()
