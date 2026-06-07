from datetime import date
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


def is_premium(user_id: str, token: str) -> bool:
    try:
        response = (
            _client(token)
            .table("profiles")
            .select("is_premium")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if response and response.data:
            return bool(response.data.get("is_premium"))
        return False
    except Exception:
        return False


def log_story(user_id: str, prompt: str, token: str):
    _client(token).table("story_logs").insert({
        "user_id": user_id,
        "prompt": prompt,
    }).execute()
