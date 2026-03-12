from decouple import config

BOT_TOKEN = config("BOT_TOKEN", cast=str)
CONFIRM_CHAT = config('CONFIRM_CHAT', cast=int)
CHANNEL = config('CHANNEL', cast=int)

ADMINS = [int(i) for i in config('ADMINS').split(',')]
IS_HOLIDAY = config('IS_HOLIDAY', cast=bool, default=False)

