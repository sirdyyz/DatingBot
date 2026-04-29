from aiogram import Router, types

router = Router()

@router.message()
async def echo_handler(message: types.Message):
    await message.answer(
        "непонятная команда. выберите действие из меню ниже 👇"
    )
