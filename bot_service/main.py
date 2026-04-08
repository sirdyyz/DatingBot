import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.start import router as start_router
from handlers.profile import router as profile_router
from handlers.common import router as common_router
from database.engine import init_models

logging.basicConfig(level=logging.INFO)

async def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        raise ValueError("в енв нет токена бота")
    
    await init_models()

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(common_router)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("запуск бота")
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("бот остановлен")