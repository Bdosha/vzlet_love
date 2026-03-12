from decouple import config

BOT_TOKEN = config("BOT_TOKEN", cast=str)
CONFIRM_CHAT = config('CONFIRM_CHAT', cast=int)
CHANNEL = config('CHANNEL', cast=int)

ADMINS = [int(i) for i in config('ADMINS').split(',')]
IS_HOLIDAY = config('IS_HOLIDAY', cast=bool, default=False)

from aiogram.types import User


def fmt_user(user: User) -> str:
    """id=123 | @username | name="Иван Петров" """
    parts = [f"id={user.id}"]
    if user.username:
        parts.append(f"@{user.username}")
    name = " ".join(filter(None, [user.first_name or "", user.last_name or ""]))
    if name:
        parts.append(f'name="{name}"')
    return " | ".join(parts)


def fmt_text(text: str | None, limit: int = 80) -> str:
    if not text:
        return "<пусто>"
    snippet = text.replace("\n", " ").strip()
    return snippet[:limit] + ("…" if len(snippet) > limit else "")
