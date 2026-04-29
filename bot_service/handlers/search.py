import aiohttp
from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

router = Router()

async def get_next_recommendation(telegram_id: str):
    url = f"http://recommendation_service:8001/next/{telegram_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            print(f"ошибка запроса: {e}")
    return None

async def get_who_liked_me(telegram_id: str):
    url = f"http://recommendation_service:8001/who-liked-me/{telegram_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            print(f"ошибка запроса фанатов: {e}")
    return None

@router.message(F.text == "Смотреть анкеты")
async def show_recommendations_command(message: Message):
    await show_recommendations(message, message.from_user.id)

@router.message(F.text == "Кому я нравлюсь?")
async def show_fans_command(message: Message):
    # сначала сами берем данные о тех, кто лайкнул
    data = await get_who_liked_me(str(message.from_user.id))
    await show_recommendations(message, message.from_user.id, data=data, is_fan=True)

async def show_recommendations(message: Message, user_id: int, data=None, is_fan=False):
    if data is None and is_fan:
        await message.answer("ошибка при поиске фанатов. попробуй позже")
        return

    if not data:
        data = await get_next_recommendation(str(user_id))

    if not data or data.get("status") == "error":
        await message.answer("ошибка при поиске анкет. попробуй позже")
        return

    if data.get("status") == "empty":
        msg = "анкеты в твоем городе пока закончились, зайди позже" if not is_fan else "тебя еще никто не лайкнул"
        await message.answer(msg)
        return

    prof = data["profile"]
    rating = prof.get('rating', 0)

    header = "<b>у тебя новый лайк!</b>\n\n" if is_fan else ""

    text = (
        f"{header}"
        f"<b>{prof['name']}</b>, {prof['age']}\n"
        f"⭐ рейтинг: <b>{rating}</b>\n"
        f"📍 город: {prof['city']}\n\n"
        f"{prof['bio']}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="лайкнуть в ответ" if is_fan else "лайк", callback_data=f"like_{prof['id']}"),
        InlineKeyboardButton(text="дальше", callback_data=f"skip_{prof['id']}")
    ]])

    if isinstance(message, Message):
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("like_") | F.data.startswith("skip_"))
async def process_action(callback: CallbackQuery):
    action, prof_id = callback.data.split("_")
    user_id = callback.from_user.id

    payload = {
        "from_telegram_id": str(user_id),
        "to_profile_id": int(prof_id),
        "action": action
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("http://recommendation_service:8001/action", json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("is_match"):
                    await callback.message.answer("<b>это метч!</b>", parse_mode="HTML")

    try:
        await callback.message.delete()
    except:
        pass

    await show_recommendations(callback, user_id)
    await callback.answer()
