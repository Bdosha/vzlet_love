from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import database
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


def _wrap_text(text: str, max_chars: int = 27, max_lines: int = 5) -> str:
    words = text.split(' ') if ' ' in text else list(text)
    lines: list[str] = ['']
    for word in words:
        if len(lines[-1] + word) > max_chars:
            lines.append(word)
        else:
            lines[-1] += ' ' + word
    if len(lines) > max_lines:
        return 'Слишком много символов :('
    return '\n'.join(lines)


def create_picture(color: str, text: str, p_from: str, p_for: str) -> BytesIO:
    img = Image.open(f'patterns/{color}.png')
    draw = ImageDraw.Draw(img)

    big_font = ImageFont.truetype('patterns/baloo-cyrillic.ttf', 125)
    small_font = ImageFont.truetype('patterns/baloo-cyrillic.ttf', 100)

    draw.text((230, 550), _wrap_text(text), font=big_font, fill='#313131')
    draw.text((630, 1360), p_from, font=small_font, fill='#313131')
    draw.text((485, 1473), p_for, font=small_font, fill='#313131')

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


class PostcardForm(StatesGroup):
    make_text = State()
    make_p_from = State()
    make_p_for = State()


async def _register_user(use: CallbackQuery | Message) -> None:
    await database.upsert_user(use.from_user.id, use.from_user.username)


async def make_picture(message: Message):
    await _register_user(message)
    chose_color = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🧡 Оранжевый', callback_data='orange')],
            [InlineKeyboardButton(text='🩵 Голубой', callback_data='blue')],
            [InlineKeyboardButton(text='💚 Зелёный', callback_data='green')],
        ]
    )
    await message.answer('Выбери цвет фона для открытки', reply_markup=chose_color)


async def choose_color(callback: CallbackQuery, state: FSMContext):
    await _register_user(callback)
    await state.update_data(color=callback.data)
    await callback.answer()
    await callback.message.edit_text('Напиши текст для открытки')
    await state.set_state(PostcardForm.make_text)


async def text_for_picture(message: Message, state: FSMContext):
    await _register_user(message)
    await state.update_data(text=message.text)
    await message.answer('Напиши от кого эта открытка (макс 8 символов)')
    await state.set_state(PostcardForm.make_p_from)


async def author_of_picture(message: Message, state: FSMContext):
    await _register_user(message)
    if len(message.text) > 8:
        await message.answer('Слишком много символов, максимум 8')
        return
    await state.update_data(p_from=message.text)
    await message.answer('Напиши для кого эта открытка (макс 12 символов)')
    await state.set_state(PostcardForm.make_p_for)


async def getter_of_picture(message: Message, state: FSMContext):
    await _register_user(message)
    if len(message.text) > 12:
        await message.answer('Слишком много символов, максимум 12')
        return
    data = await state.get_data()
    await state.clear()
    buf = create_picture(data['color'], data['text'], data['p_from'], message.text)
    photo = BufferedInputFile(buf.read(), filename='postcard.png')
    await message.answer('А вот и открытка!')
    await message.answer_photo(photo)


def register(dp: Dispatcher) -> None:
    dp.message.register(make_picture, F.text == '✍️ Сделать открытку')
    dp.callback_query.register(choose_color, F.data.in_({'orange', 'blue', 'green'}))
    dp.message.register(text_for_picture, PostcardForm.make_text)
    dp.message.register(author_of_picture, PostcardForm.make_p_from)
    dp.message.register(getter_of_picture, PostcardForm.make_p_for)
