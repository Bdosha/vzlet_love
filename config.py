import logging
from aiogram.types import User

from aiogram import Bot, Dispatcher
from decouple import config

BOT_TOKEN = config("BOT_TOKEN", cast=str)
CONFIRM_CHAT = config('CONFIRM_CHAT', cast=int)
CHANNEL = config('CHANNEL', cast=int)

ADMINS = [int(i) for i in config('ADMINS').split(',')]
IS_HOLIDAY = config('IS_HOLIDAY', cast=bool, default=False)

LOG_FMT = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_fh = logging.FileHandler("bot.log", mode="a", encoding="utf-8")
_fh.setFormatter(LOG_FMT)

_ch = logging.StreamHandler()
_ch.setFormatter(LOG_FMT)

logging.basicConfig(level=logging.WARNING, handlers=[_ch])

logger = logging.getLogger("love")
logger.setLevel(logging.INFO)
logger.addHandler(_fh)
logger.addHandler(_ch)
logger.propagate = False

BAN_TEXT = 'Вы были заблокированы в боте. Для разблокировки обращайтесь к @bdosha06'

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


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
