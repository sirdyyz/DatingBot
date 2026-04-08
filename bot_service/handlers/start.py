from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Profile

router = Router()

async def get_start_kb(telegram_id: int):
    async with async_session() as session:
        query = select(Profile).join(User).where(User.telegram_id == str(telegram_id))
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

    if profile:
        kb = [
            [KeyboardButton(text="Смотреть анкеты")],
            [KeyboardButton(text="Мой профиль"), KeyboardButton(text="Сменить город поиска")],
            [KeyboardButton(text="Удалить анкету")]
        ]
    else:
        kb = [
            [KeyboardButton(text="Создать анкету")]
        ]
        
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = await get_start_kb(message.from_user.id)
    await message.answer(
        "Привет. Я бот знакомств - MeetMe. Выбери действие ниже 👇",
        reply_markup=kb
    )