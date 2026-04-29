import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from database.engine import async_session
from database.models import Profile, ProfileStat, User
from rabbitmq import send_to_moderation
from sqlalchemy import select

router = Router()

class ProfileForm(StatesGroup):
    name = State()
    age = State()
    gender = State()
    city = State()
    bio = State()
    search_city = State()

gender_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="👨🏼"), KeyboardButton(text="👩🏼")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(F.text == "Проверить статус")
async def check_mod_status(message: Message):
    async with async_session() as session:
        query = select(
            Profile
        ).join(User).where(User.telegram_id == str(message.from_user.id))
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

    from handlers.start import get_start_kb
    kb = await get_start_kb(message.from_user.id)

    if not profile:
        await message.answer(
            "твою анкету отклонили модераторы \n" \
            "пожалуйста, создай новую без нарушений правил",
            reply_markup=kb
        )
    elif getattr(profile, 'is_approved', False) == False:
        await message.answer("анкета еще на проверке. модераторы скоро её посмотрят")
    else:
        await message.answer(
            "ура! твоя анкета одобрена, теперь ты можешь искать пару",
            reply_markup=kb
        )

@router.message(StateFilter('*'), Command("cancel"))
@router.message(StateFilter('*'), F.text.lower() == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    from handlers.start import get_start_kb
    kb = await get_start_kb(message.from_user.id)

    await message.answer(
        "отменяем..",
        reply_markup=kb
    )

@router.message(F.text.in_({"Создать анкету", "Поменять анкету"}))
@router.message(Command("profile"))
async def start_profile_creation(message: Message, state: FSMContext):
    await message.answer(
        "как тебя зовут?\n",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(ProfileForm.name)

@router.message(ProfileForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("сколько тебе лет?")
    await state.set_state(ProfileForm.age)

@router.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("введи возраст числом")
        return

    await state.update_data(age=int(message.text))
    await message.answer("твой пол?", reply_markup=gender_kb)
    await state.set_state(ProfileForm.gender)

@router.message(ProfileForm.gender)
async def process_gender(message: Message, state: FSMContext):
    allowed_genders = ["👨🏼", "👩🏼"]

    if message.text not in allowed_genders:
        await message.answer("выбери пол, нажав на одну из кнопок ниже 👇")
        return

    await state.update_data(gender=message.text)
    await message.answer("из какого ты города?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProfileForm.city)

@router.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext):
    city_name = message.text.strip()

    if len(city_name) < 3 or not city_name.replace(" ", "").replace("-", "").isalpha():
        await message.answer("введи реальный город (только буквы, минимум 3 символа)")
        return

    await state.update_data(city=city_name.capitalize())
    await message.answer("напиши пару слов о себе (bio, минимум 10 символов)")
    await state.set_state(ProfileForm.bio)

@router.message(ProfileForm.bio)
async def process_bio(message: Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("напиши хотя бы пару предложений о себе")
        return

    await state.update_data(bio=message.text)
    await message.answer("в каком городе будем искать пару?")
    await state.set_state(ProfileForm.search_city)

@router.message(F.text == "Сменить город поиска")
async def change_search_city_only(message: Message, state: FSMContext):
    async with async_session() as session:
        query = select(
            Profile
        ).join(User).where(User.telegram_id == str(message.from_user.id))
        p = (await session.execute(query)).scalar_one_or_none()
        if not p:
            from handlers.start import get_start_kb
            kb = await get_start_kb(message.from_user.id)
            await message.answer(
                "у тебя нет анкеты, нажми «создать анкету»", reply_markup=kb
            )
            return

    await message.answer(
        "введи новый город для поиска\n",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(ProfileForm.search_city)

@router.message(ProfileForm.search_city)
async def process_search_city(message: Message, state: FSMContext):
    city_name = message.text.strip()

    if len(city_name) < 3 or not city_name.replace(" ", "").replace("-", "").isalpha():
        await message.answer("введи реальный город для поиска (минимум 3 буквы)")
        return

    search_city_capitalized = city_name.capitalize()
    await state.update_data(search_city=search_city_capitalized)

    data = await state.get_data()

    if data.get('name') is None:
        async with async_session() as session:
            query = select(
                Profile
            ).join(User).where(User.telegram_id == str(message.from_user.id))
            p = (await session.execute(query)).scalar_one_or_none()
            if p:
                p.search_city = search_city_capitalized
                await session.commit()
                text = "📍 город поиска успешно " \
                f"изменен на: <b>{search_city_capitalized}</b>"
            else:
                text = "у тебя нет анкеты"

        from handlers.start import get_start_kb
        kb = await get_start_kb(message.from_user.id)
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        profile_text = (
            f"<b>твоя анкета успешно собрана!</b>\n\n"
            f"👤 <b>имя:</b> {data.get('name')}\n"
            f"<b>возраст:</b> {data.get('age')}\n"
            f"🚻 <b>пол:</b> {data.get('gender')}\n"
            f"<b>твой город:</b> {data.get('city')}\n"
            f"<b>о себе:</b> {data.get('bio')}\n\n"
            f"📍 <b>ищем пару в городе:</b> {data.get('search_city')}"
        )

        data['action'] = 'create_profile'
        data['telegram_id'] = message.from_user.id
        data['username'] = message.from_user.username

        try:
            await send_to_moderation(data)
        except Exception as e:
            logging.error(f"ошибка отправки в RabbitMQ: {e}")
            await message.answer("проблема с сервером модерации")
            await state.clear()
            return

        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Проверить статус")]],
            resize_keyboard=True
        )

        await message.answer(
            profile_text + "\n\n⏳ <b>анкета отправлена на проверку модераторам</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )

    await state.clear()

@router.message(F.text == "Мой профиль")
async def show_my_profile(message: Message):
    telegram_id = str(message.from_user.id)

    async with async_session() as session:
        query = (
            select(Profile, ProfileStat.rating)
            .join(User)
            .join(ProfileStat, ProfileStat.profile_id == Profile.id)
            .where(User.telegram_id == telegram_id)
        )
        result = await session.execute(query)
        row = result.first()

        if row:
            profile, rating = row
            profile_text = (
                f"👤 <b>твоя текущая анкета:</b>\n\n"
                f"<b>имя:</b> {profile.name}\n"
                f"<b>возраст:</b> {profile.age}\n"
                f"🚻 <b>пол:</b> {profile.gender}\n"
                f"⭐ <b>твой рейтинг: {round(rating, 1)}</b>\n"
                f"<b>твой город:</b> {profile.city}\n"
                f"<b>о себе:</b> {profile.bio}\n\n"
                f"📍 <b>ищем пару в:</b> {profile.search_city}"
            )
            await message.answer(profile_text, parse_mode="HTML")
        else:
            await message.answer("у тебя еще нет анкеты или она на модерации")

@router.message(F.text == "Удалить анкету")
async def delete_profile_handler(message: Message):
    t_id = str(message.from_user.id)
    async with async_session() as session:
        query = select(Profile).join(User).where(User.telegram_id == t_id)
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

        if profile:
            await session.delete(profile)
            await session.commit()

            from handlers.start import get_start_kb
            kb = await get_start_kb(message.from_user.id)
            await message.answer("твоя анкета удалена", reply_markup=kb)
        else:
            await message.answer("у тебя нет анкеты")
