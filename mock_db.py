#MSYS_NO_PATHCONV=1 docker exec -it dating_bot env PYTHONPATH=/app:/app/bot_service python /app/mock_db.py
import asyncio
import random

from sqlalchemy import select

from bot_service.database.engine import async_session
from bot_service.database.models import Profile, ProfileStat, User

NAMES = ["ксения", "мария", "иван", "дарья", "артем", "елена", "дмитрий", "ольга", "михаил", "ирина"]
CITIES = ["Сочи", "Краснодар", "Санкт-Петербург"]
BIOS = [
    "......................",
    "......................",
    "......................",
    "......................",
    "......................"
]

async def spawn():
    async with async_session() as session:

        for i in range(10):
            t_id = str(100 + i)
            res = await session.execute(select(User).where(User.telegram_id == t_id))
            if res.scalar_one_or_none():
                continue

            user = User(telegram_id=t_id, username=f"mock_user_{i}")
            session.add(user)
            await session.flush()

            bio = random.choice(BIOS)
            profile = Profile(
                user_id=user.id,
                name=random.choice(NAMES),
                age=random.randint(18, 35),
                gender=random.choice(["👨🏼", "👩🏼"]),
                city=random.choice(CITIES),
                bio=bio,
                search_city=random.choice(CITIES),
                is_approved=True
            )
            session.add(profile)
            await session.flush()

            rating = 15.0 if len(bio) > 30 else 10.0
            stat = ProfileStat(profile_id=profile.id, rating=rating)
            session.add(stat)

        await session.commit()
        print("+ 10 мок анкет")

if __name__ == "__main__":
    asyncio.run(spawn())
