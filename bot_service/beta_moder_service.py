import asyncio
import aio_pika
import json
import os
from dotenv import load_dotenv
from sqlalchemy import select
from database.engine import async_session
from database.models import User, Profile

load_dotenv()

async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode('utf-8'))
        action = data.get('action')
        t_id = str(data['telegram_id'])
        
        async with async_session() as session:
            res = await session.execute(select(User).where(User.telegram_id == t_id))
            user = res.scalar_one_or_none()
            
            if not user:
                user = User(telegram_id=t_id, username=data.get('username', 'unknown'))
                session.add(user)
                await session.flush()
            
            if action == 'update_city':
                prof_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
                profile = prof_res.scalar_one_or_none()
                if profile:
                    profile.search_city = data['search_city']
                    await session.commit()
                    
            elif action == 'create_profile':
                prof_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
                old_profile = prof_res.scalar_one_or_none()
                if old_profile:
                    await session.delete(old_profile)
                    await session.flush()

                profile = Profile(
                    user_id=user.id,
                    name=data['name'],
                    age=data['age'],
                    gender=data['gender'],
                    city=data['city'],
                    bio=data['bio'],
                    search_city=data['search_city']
                )
                session.add(profile)
                await session.commit()
                print(f"профиль сохранен в потсгрес: {data.get('name')}")

async def main():
    url = os.getenv("RABBITMQ_URL")
    conn = await aio_pika.connect_robust(url)
    channel = await conn.channel()
    queue = await channel.declare_queue("moderation_queue", durable=True)
    
    print("модер сервис запущен...")
    await queue.consume(process_message)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())