import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rabbitmq import consume_rabbitmq

from bot_service.database.engine import async_session
from bot_service.database.models import Profile, ProfileStat


app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_rabbitmq())

@app.get("/", response_class=HTMLResponse)
async def admin_panel():
    async with async_session() as session:
        res = await session.execute(select(Profile).where(Profile.is_approved == False))
        profiles = res.scalars().all()

        html = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Панель Модерации</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <nav class="navbar navbar-dark bg-dark mb-4">
                <div class="container">
                    <span class="navbar-brand mb-0 h1"> Meet.Me | Модерация</span>
                </div>
            </nav>
            <div class="container">
                <h2 class="mb-4">анкеты на проверку</h2>
                <div class="row row-cols-1 row-cols-md-3 g-4">
        """

        if not profiles:
            html += "<div class='col-12'><p class='text-muted fs-5'>нет новых анкет для проверки</p></div>"

        for p in profiles:
            html += f"""
                <div class="col">
                    <div class="card h-100 shadow-sm border-0">
                        <div class="card-body">
                            <h5 class="card-title fw-bold text-primary">{p.name}, {p.age}</h5>
                            <h6 class="card-subtitle mb-3 text-muted">📍 {p.city} ➡️ {p.search_city}</h6>
                            <p class="card-text fst-italic">"{p.bio}"</p>
                        </div>
                        <div class="card-footer bg-white border-top-0 d-flex justify-content-between pb-3">
                            <a href="/reject/{p.id}" class="btn btn-outline-danger btn-sm">отклонить</a>
                            <a href="/approve/{p.id}" class="btn btn-success btn-sm px-4">одобрить</a>
                        </div>
                    </div>
                </div>
            """

        html += """
                </div>
            </div>
        </body>
        </html>
        """
        return html

@app.get("/approve/{profile_id}")
async def approve_profile(profile_id: int):
    async with async_session() as session:
        profile = await session.get(Profile, profile_id)
        if profile:
            profile.is_approved = True

            base_rating = 10.0
            if profile.bio and len(profile.bio) >= 30:
                base_rating += 5.0

            stat = ProfileStat(profile_id=profile.id, rating=base_rating)
            session.add(stat)

            await session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/reject/{profile_id}")
async def reject_profile(profile_id: int):
    async with async_session() as session:
        profile = await session.get(Profile, profile_id)
        if profile:
            await session.delete(profile)
            await session.commit()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
