from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from database.engine import async_session
from database.models import Profile, User
from sqlalchemy import select

router = Router()

async def get_start_kb(telegram_id: int):
    async with async_session() as session:
        query = select(Profile).join(User).where(User.telegram_id == str(telegram_id))
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

    if profile:
        if getattr(profile, 'is_approved', False):
            kb = [
                [KeyboardButton(text="Смотреть анкеты")],
                [KeyboardButton(text="Кому я нравлюсь?")],
                [
                    KeyboardButton(text="Мой профиль"),
                    KeyboardButton(text="Сменить город поиска")
                ],
                [KeyboardButton(text="Удалить анкету")]
            ]
        else:
            kb = [[KeyboardButton(text="Проверить статус")]]
    else:
        kb = [[KeyboardButton(text="Создать анкету")]]

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message):
    kb = await get_start_kb(message.from_user.id)
    await message.answer(
        "привет! я бот знакомств - meetme. выбери действие ниже 👇", reply_markup=kb
    )
