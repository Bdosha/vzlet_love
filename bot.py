import asyncio
import logging

from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

import database
import postcard
from config import BOT_TOKEN, CONFIRM_CHAT, CHANNEL, ADMINS, IS_HOLIDAY

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

BAN_TEXT = 'Вы были заблокированы в боте. Для разблокировки обращайтесь к @bdosha06'


class Form(StatesGroup):
    broadcast = State()
    send_to_chat = State()


async def register_user(use: CallbackQuery | Message) -> None:
    await database.upsert_user(use.from_user.id, use.from_user.username)


# ── Admin ─────────────────────────────────────────────────────────────────────

@dp.message(Command('log'))
async def cmd_log(message: Message):
    if message.from_user.id not in ADMINS:
        return
    try:
        await message.answer_document(FSInputFile(path='nohup.out'))
    except Exception:
        await message.answer('Лог-файл пустой или не найден')
    database.export_sheet()
    await message.answer_document(FSInputFile(path='Пользователи.xlsx'))


@dp.message(Command('unban'))
async def cmd_unban(message: Message):
    if message.from_user.id not in ADMINS:
        return
    try:
        user_id = int(message.text.split()[-1])
        await database.unban(user_id)
        await message.answer('Разбанен')
    except ValueError:
        await message.answer('Укажите ID: /unban 123456789')


# ── Start ─────────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await register_user(message)
    if await database.check_ban(message.from_user.id):
        await message.answer(BAN_TEXT)
        return
    await state.clear()
    keyboard = [[KeyboardButton(text='💌 Написать в канал')]]
    if IS_HOLIDAY:
        keyboard.append([KeyboardButton(text='✍️ Сделать открытку')])
    keys = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keyboard)
    text = (
        'Привет! Как насчет небольшого олимпиадного признания в любви? ❤️\n'
        'А может лучше сделаем открытку? 🌠'
        if IS_HOLIDAY
        else 'Привет! Как насчет небольшого олимпиадного признания в любви? ❤️'
    )
    await message.answer(text, reply_markup=keys)


# ── Write to channel ──────────────────────────────────────────────────────────

@dp.message(F.text == '💌 Написать в канал')
async def make_post(message: Message, state: FSMContext):
    await register_user(message)
    await state.set_state(Form.send_to_chat)
    await message.answer('Напиши сообщение')


@dp.message(Form.send_to_chat)
async def receive_post(message: Message, state: FSMContext):
    await register_user(message)
    if await database.check_ban(message.from_user.id):
        await message.answer(BAN_TEXT)
        await state.clear()
        return
    confirm = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💌 Отправить в канал', callback_data='send_post')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='unpublic')],
        ]
    )
    await message.copy_to(message.from_user.id, reply_markup=confirm)
    await state.clear()


@dp.callback_query(F.data == 'send_post')
async def cb_send_post(callback: CallbackQuery):
    if await database.check_ban(callback.from_user.id):
        await callback.message.answer(BAN_TEXT)
        return
    mod_buttons = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text='✅', callback_data='public'),
            InlineKeyboardButton(text='🚷 БАН', callback_data=f'ban_{callback.from_user.id}'),
            InlineKeyboardButton(text='❌', callback_data='unpublic'),
        ]]
    )
    await bot.copy_message(
        from_chat_id=callback.from_user.id,
        chat_id=CONFIRM_CHAT,
        message_id=callback.message.message_id,
        reply_markup=mod_buttons,
    )
    await callback.answer('Сообщение отправлено на модерацию', show_alert=True)
    await callback.message.edit_reply_markup()


@dp.callback_query(F.data == 'public')
async def cb_public(callback: CallbackQuery):
    await bot.copy_message(
        from_chat_id=CONFIRM_CHAT,
        chat_id=CHANNEL,
        message_id=callback.message.message_id,
    )
    await callback.message.edit_reply_markup()


@dp.callback_query(F.data == 'unpublic')
async def cb_unpublic(callback: CallbackQuery):
    await callback.message.edit_reply_markup()


@dp.callback_query(F.data.startswith('ban_'))
async def cb_ban(callback: CallbackQuery):
    user_id = int(callback.data.split('_', 1)[1])
    await database.ban(user_id)
    await callback.answer(f'Автор сообщения забанен. ID: {user_id}', show_alert=True)
    await callback.message.edit_reply_markup()


# ── Broadcast ─────────────────────────────────────────────────────────────────

@dp.message(Command('broadcast'))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        return
    await message.answer('Напиши объявление')
    await state.set_state(Form.broadcast)


@dp.message(Form.broadcast)
async def receive_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS:
        await state.clear()
        return
    await state.clear()
    confirm_btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm')]]
    )
    await bot.copy_message(
        from_chat_id=message.from_user.id,
        chat_id=message.from_user.id,
        message_id=message.message_id,
        reply_markup=confirm_btn,
    )


@dp.callback_query(F.data == 'confirm')
async def cb_confirm_broadcast(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    users = await database.all_users()
    msg = await callback.message.answer('Рассылка начата...')
    await callback.message.edit_reply_markup()
    sent = 0
    for user in users:
        try:
            await bot.copy_message(
                from_chat_id=callback.from_user.id,
                chat_id=user,
                message_id=callback.message.message_id,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning('Broadcast skip %s: %s', user, e)
    await msg.edit_text(f'Рассылка завершена. Доставлено: {sent}/{len(users)}')


# ── Fallback ──────────────────────────────────────────────────────────────────

@dp.message(F.chat.type == 'private')
async def fallback(message: Message):
    await message.answer('Неизвестная команда')


@dp.channel_post()
async def channel_post(message: Message):
    logger.info('Channel post in chat %s', message.chat.id)


if IS_HOLIDAY:
    postcard.register(dp)
    logger.info('Режим праздника: открытки включены')
else:
    logger.info('Режим праздника выключен: открытки недоступны')


async def on_startup():
    await database.init_db()
    logger.info('БД инициализирована')


if __name__ == '__main__':
    logger.info('Бот запущен')
    dp.run_polling(bot, on_startup=on_startup)
