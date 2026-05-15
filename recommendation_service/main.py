import uvicorn
from fastapi import FastAPI
from recommendation_service.models import ActionModel
from recommendation_service.rec_db import async_session, redis_client
from sqlalchemy import delete, desc, not_, select

from bot_service.database.models import Like, Profile, ProfileStat, User, Visit

app = FastAPI()

@app.get("/next/{telegram_id}")
async def get_next_profile(telegram_id: str):
    cached_id = await redis_client.lpop(f"user:{telegram_id}:recs")
    if cached_id:
        async with async_session() as session:
            prof = await session.get(Profile, int(cached_id))
            if prof and prof.is_approved:
                st_res = await session.execute(
                    select(ProfileStat.rating).where(ProfileStat.profile_id == prof.id)
                )
                rating = st_res.scalar() or 10.0
                return {
                    "status": "ok",
                    "profile": {
                        "id": prof.id, "name": prof.name, "age": prof.age,
                        "city": prof.city, "bio": prof.bio, "rating": round(rating, 1)
                    }
                }

    async with async_session() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_res.scalar_one_or_none()
        if not user:
            return {"status": "error"}

        prof_res = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        my_prof = prof_res.scalar_one_or_none()
        if not my_prof:
            return {"status": "error"}

        async def fetch_profiles(u_id, s_city):
            v_res = await session.execute(
                select(Visit.to_user_id).where(Visit.from_user_id == u_id)
            )
            viewed = [v[0] for v in v_res.all()]
            viewed.append(u_id)

            q = (
                select(Profile, ProfileStat.rating)
                .join(ProfileStat)
                .where(
                    Profile.is_approved == True,
                    Profile.city == s_city,
                    not_(Profile.user_id.in_(viewed))
                )
                .order_by(desc(ProfileStat.rating), desc(Profile.id))
                .limit(10)
            )
            res = await session.execute(q)
            return res.all()

        rows = await fetch_profiles(user.id, my_prof.search_city)

        if not rows:
            await session.execute(delete(Visit).where(Visit.from_user_id == user.id))
            await session.commit()
            rows = await fetch_profiles(user.id, my_prof.search_city)

        if not rows:
            return {"status": "empty"}

        target_prof, rating = rows[0]

        if len(rows) > 1:
            ids_to_cache = [r[0].id for r in rows[1:]]
            await redis_client.rpush(f"user:{telegram_id}:recs", *ids_to_cache)
            await redis_client.expire(f"user:{telegram_id}:recs", 3600)

        return {
            "status": "ok",
            "profile": {
                "id": target_prof.id, "name": target_prof.name, "age": target_prof.age,
                "city": target_prof.city, "bio": target_prof.bio,
                "rating": round(rating, 1)
            }
        }

@app.post("/action")
async def process_action(data: ActionModel):
    async with async_session() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == data.from_telegram_id)
        )
        from_user = user_res.scalar_one_or_none()
        if not from_user:
            return {"status": "error"}

        to_prof = await session.get(Profile, data.to_profile_id)
        if not to_prof:
            return {"status": "error"}
        to_user_id = to_prof.user_id

        session.add(Visit(from_user_id=from_user.id, to_user_id=to_user_id))

        stat_res = await session.execute(
            select(ProfileStat).where(ProfileStat.profile_id == data.to_profile_id)
        )
        stat = stat_res.scalar_one()
        stat.visits_count += 1

        is_match = False
        if data.action == 'like':
            session.add(Like(from_user_id=from_user.id, to_user_id=to_user_id))
            stat.likes_count += 1

            match_res = await session.execute(
                select(Like).where(
                    Like.from_user_id == to_user_id, Like.to_user_id == from_user.id
                )
            )
            if match_res.scalar_one_or_none():
                is_match = True

        await session.commit()
        return {"status": "ok", "is_match": is_match}

@app.get("/who-liked-me/{telegram_id}")
async def get_who_liked_me(telegram_id: str):
    async with async_session() as session:
        user_res = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
            )
        user = user_res.scalar_one_or_none()
        if not user:
            return {"status": "error"}

        viewed_res = await session.execute(
            select(Visit.to_user_id).where(Visit.from_user_id == user.id)
        )
        viewed_ids = [v[0] for v in viewed_res.all()]

        query = (
            select(Profile, ProfileStat.rating)
            .join(ProfileStat).join(Like, Like.from_user_id == Profile.user_id)
            .where(Like.to_user_id == user.id)
        )

        if viewed_ids:
            query = query.where(not_(Profile.user_id.in_(viewed_ids)))

        query = query.limit(1)

        result = await session.execute(query)
        row = result.first()

        if not row:
            return {"status": "empty"}

        p, rating = row
        return {
            "status": "ok",
            "profile": {
                "id": p.id, "name": p.name, "age": p.age,
                "city": p.city, "bio": p.bio, "rating": round(rating, 1)
            }
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
