import asyncio
import os
import sys

from celery import Celery
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_service.database.engine import async_session
from bot_service.database.models import Profile, ProfileStat

rabbitmq_url = os.getenv("RABBITMQ_URL") 

celery_app = Celery("dating_tasks", broker=rabbitmq_url)

celery_app.conf.beat_schedule = {
    "recalculate-ratings": {
        "task": "tasks.recalculate_ratings",
        "schedule": 300.0,
    },
}
celery_app.conf.timezone = "UTC"


async def _recalculate_ratings():
    async with async_session() as session:
        query = select(Profile, ProfileStat).join(ProfileStat)
        rows = (await session.execute(query)).all()

        for prof, stat in rows:
            base_rating = 15.0 if len(prof.bio) > 30 else 10.0
            conversion = (stat.likes_count / stat.visits_count * 100) if stat.visits_count > 0 else 0
            stat.rating = (base_rating * 0.4) + (conversion * 0.6)

        await session.commit()


@celery_app.task(name="tasks.recalculate_ratings")
def recalculate_ratings():
    asyncio.run(_recalculate_ratings())