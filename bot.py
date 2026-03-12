from aiogram import F, Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery,
                           Message,
                           FSInputFile,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup,
                           KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.fsm.state import State, StatesGroup

import asyncio

import database
from create_picture import create_picture
from config import BOT_TOKEN, CONFIRM_CHAT, CHANNEL, ADMINS

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

temp_data = {}


class Form(StatesGroup):
    broadcast = State()
    send_to_chat = State()
    make_text = State()
    make_p_from = State()
    make_p_for = State()


def banned(use):
    return database.check_ban(use.from_user.id)


def get_user_info(use: CallbackQuery | Message):
    database.start_command(use.from_user.id)
    database.set_username(use.from_user.id, use.from_user.username)
    if isinstance(use, CallbackQuery):
        return use.from_user.username, use.from_user.id, use.data
    return use.from_user.username, use.from_user.id, use.text


@dp.message(Command('log'))
async def log(message: Message):
    if message.from_user.id in ADMINS:
        try:
            await message.answer_document(FSInputFile(path='nohup.out'))
        except:
            await message.answer('Файл пустой')
        database.export_sheet()
        await message.answer_document(FSInputFile(path='Пользователи.xlsx'))


@dp.message(Command('unban'))
async def log(message: Message):
    if message.from_user.id in ADMINS:
        try:
            user_id = int(message.text.split()[-1])
            database.unban(user_id)
            await message.answer('Разбанен')
        except ValueError:
            await message.answer('Нет ID')


@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    if banned(message):
        await message.answer('Вы были заблокированы в боте. Для разблокировки обращайтесь к @bdosha06')
        return
    print(*get_user_info(message))
    await state.clear()
    temp_data[message.from_user.id] = []
    keys = ReplyKeyboardMarkup(resize_keyboard=True,
                               keyboard=[[KeyboardButton(text='💌 Написать в канал')],
                                         [KeyboardButton(text='✍️ Сделать открытку')]])

    await message.answer(
        'Привет! Как насчет небольшого олимпиадного признания в любви? ❤️\nА может лучше сделаем открытку? 🌠',
        reply_markup=keys)


@dp.message(F.text == '💌 Написать в канал')
async def make_post(message: Message, state: FSMContext):
    print(*get_user_info(message))
    temp_data[message.from_user.id] = []
    await state.set_state(Form.send_to_chat)
    await message.answer('Напиши cообщение')


@dp.message(F.text == '✍️ Сделать открытку')
async def make_picture(message: Message):
    print(*get_user_info(message))
    chose_color = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🧡 Оранжевый', callback_data='orange')],
                         [InlineKeyboardButton(text='🩵 Голубой', callback_data='blue')],
                         [InlineKeyboardButton(text='💚 Зелёный', callback_data='green')]])

    await message.answer('Выбери цвет фона для открытки', reply_markup=chose_color)


@dp.callback_query(F.data.in_(['orange', 'blue', 'green']))
async def choose_color(callback: CallbackQuery, state: FSMContext):
    print(*get_user_info(callback))
    temp_data[callback.from_user.id] = [callback.data]
    await callback.answer()
    await callback.message.edit_text('Напиши текст для открытки')
    await state.set_state(Form.make_text)


@dp.message(F.from_user.id == F.chat.id and Form.make_text)
async def text_for_picture(message: Message, state: FSMContext):  #
    print(*get_user_info(message))
    temp_data[message.from_user.id].append(message.text)
    await message.answer('Напиши от кого эта открытка (макс 8 символов)')
    await state.set_state(Form.make_p_from)


@dp.message(F.from_user.id == F.chat.id and Form.make_p_from)
async def author_of_picture(message: Message, state: FSMContext):  #
    print(*get_user_info(message))
    if len(message.text) > 8:
        await message.answer('Слишком много символов')
        return
    temp_data[message.from_user.id].append(message.text)

    await message.answer('Напиши для кого эта открытка (макс 12 символов)')
    await state.set_state(Form.make_p_for)


@dp.message(F.from_user.id == F.chat.id and Form.make_p_for)
async def getter_of_picture(message: Message, state: FSMContext):  #
    print(*get_user_info(message))
    if len(message.text) > 12:
        await message.answer('Слишком много символов')
        return
    temp_data[message.from_user.id].append(message.text)

    await message.answer("А вот и открытка!")
    photo = FSInputFile(f"pictures/{create_picture(*temp_data[message.from_user.id])}.png")
    await message.answer_photo(photo)
    await state.clear()


@dp.message(Command('broadcast'))
async def broadcast_command(message: Message, state: FSMContext):
    print(*get_user_info(message))
    if not message.from_user.id in ADMINS:
        return
    await message.answer('Напиши объявление')
    await state.set_state(Form.broadcast)


@dp.message(F.from_user.id.in_(ADMINS) and Form.broadcast)
async def broadcast(message: Message, state: FSMContext):
    print(*get_user_info(message))
    await state.clear()
    confirm_broadcast = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=f'✅ Подтвердить',
        callback_data='confirm')]])
    await bot.copy_message(from_chat_id=message.from_user.id, chat_id=message.from_user.id,
                           message_id=message.message_id,
                           reply_markup=confirm_broadcast)


@dp.callback_query(F.data == 'confirm')
async def cansel(callback: CallbackQuery):
    print(*get_user_info(callback))
    users = database.all_users()
    msg = await callback.message.answer("Рассылка начата")
    await callback.message.edit_reply_markup(None)
    for user in users:
        try:
            await bot.copy_message(from_chat_id=callback.from_user.id, chat_id=user,
                                   message_id=callback.message.message_id)
            print('Сообщение отправлено', user)
            await asyncio.sleep(2.1)
        except:
            pass
    await msg.edit_text('Рассылка завершена')


@dp.callback_query(F.data == 'send_post')
async def cansel(callback: CallbackQuery):
    if banned(callback):
        await message.answer('Вы были заблокированы в боте. Для разблокировки обращайтесь к @bdosha06')
        return
    confirm = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='✅', callback_data='public'),
                          InlineKeyboardButton(text='🚷 БАН', callback_data=f'{callback.from_user.id}'),
                          InlineKeyboardButton(text='❌', callback_data='unpublic')]])
    await bot.copy_message(from_chat_id=callback.from_user.id, chat_id=CONFIRM_CHAT,
                           message_id=callback.message.message_id,
                           reply_markup=confirm)
    await callback.answer('Сообщение отправлено', show_alert=True)
    await callback.message.edit_reply_markup()


@dp.callback_query(F.data == 'public')
async def cansel(callback: CallbackQuery):
    await bot.copy_message(from_chat_id=CONFIRM_CHAT,
                           chat_id=CHANNEL,
                           message_id=callback.message.message_id)
    await callback.message.edit_reply_markup()


@dp.callback_query(F.data == 'unpublic')
async def cansel(callback: CallbackQuery):
    await callback.message.edit_reply_markup()


@dp.callback_query()
async def cansel(callback: CallbackQuery):
    database.ban(user_id=callback.data)
    await callback.answer(f'Автор сообщения был забанен, Скриньте {callback.data}', show_alert=True)
    await callback.message.edit_reply_markup()


@dp.message(F.from_user.id == F.chat.id and Form.send_to_chat)
async def message(message: Message, state: FSMContext):  #
    if banned(message):
        await message.answer('Вы были заблокированы в боте. Для разблокировки обращайтесь к @bdosha06')
        return
    print(*get_user_info(message))
    confirm = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='💌 Отправить в канал', callback_data='send_post')],
                         [InlineKeyboardButton(text='❌ Отмена', callback_data='unpublic')]])
    await message.copy_to(message.from_user.id, reply_markup=confirm)


@dp.message(F.from_user.id == F.chat.id)
async def message(message: Message):  #
    await message.answer('Неизвестная команда', )


@dp.channel_post()
async def message(message: Message):  #
    print(message.chat.id)


if __name__ == '__main__':
    print('Бот запущен')
    dp.run_polling(bot)
