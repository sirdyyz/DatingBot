import asyncio
import json
import os
import sys
import logging

import aio_pika
from dotenv import load_dotenv
from models import ProfileCreateSchema
from pydantic import ValidationError
from sqlalchemy import select

from bot_service.database.engine import async_session
from bot_service.database.models import Profile, User

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        try:
            raw_data = json.loads(message.body.decode('utf-8'))
            data = ProfileCreateSchema(**raw_data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"ошибка валидации: {e}")
            return

        t_id = str(data.telegram_id)

        async with async_session() as session:
            res = await session.execute(select(User).where(User.telegram_id == t_id))
            user = res.scalar_one_or_none()

            if not user:
                user = User(telegram_id=t_id, username=data.username)
                session.add(user)
                await session.flush()

            if data.action == 'create_profile':
                prof_res = await session.execute(
                    select(Profile).where(Profile.user_id == user.id)
                )
                old_profile = prof_res.scalar_one_or_none()

                if old_profile:
                    await session.delete(old_profile)
                    await session.flush()

                profile = Profile(
                    user_id=user.id,
                    name=data.name,
                    age=data.age,
                    gender=data.gender,
                    city=data.city,
                    bio=data.bio,
                    search_city=data.search_city
                )
                session.add(profile)
                await session.flush()
                await session.commit()
                print(f"+ анкета на модерацию: {data.name}")

async def consume_rabbitmq():
    url = os.getenv("RABBITMQ_URL")
    if not url:
        logging.critical("переменной реббит нет в енве")
        return

    print(f"Попытка подключения к RabbitMQ по адресу: {url}")
    while True:
        try:
            conn = await aio_pika.connect_robust(url)
            channel = await conn.channel()
            queue = await channel.declare_queue("moderation_queue", durable=True)
            await queue.consume(process_message)
            await asyncio.Future()
        except Exception as e:
            print(f"ошибка RabbitMQ: {e}")
            await asyncio.sleep(5)
