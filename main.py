import os
import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from redis.asyncio import Redis
from dotenv import load_dotenv

from database import init_db, get_db, reset_items, Item, AsyncSessionLocal
from metrics import metrics_store
from pydantic import BaseModel

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
WRITE_BACK_FLUSH_DELAY = float(os.getenv("WRITE_BACK_FLUSH_DELAY", "0.02"))

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
UPDATE_QUEUE = "write_back_queue"

async def write_back_worker():
    while True:
        try:
            item_data = await redis_client.rpop(UPDATE_QUEUE)
            if item_data:
                data = json.loads(item_data)
                async with AsyncSessionLocal() as db:
                    await upsert_item(db, data["id"], data["payload"])
                    await db.commit()
                    metrics_store.db_queries += 1
                    metrics_store.write_back_flushes += 1
                print(f"write-back flush: объект {data['id']} сохранен в бд")
                await asyncio.sleep(WRITE_BACK_FLUSH_DELAY)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"ошибка воркера: {e}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(write_back_worker())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

class ItemCreate(BaseModel):
    id: int
    payload: str

async def upsert_item(db: AsyncSession, item_id: int, payload: str):
    statement = insert(Item).values(id=item_id, payload=payload)
    statement = statement.on_conflict_do_update(
        index_elements=[Item.id],
        set_={"payload": statement.excluded.payload},
    )
    await db.execute(statement)

@app.get("/lazy/{item_id}")
async def lazy_get(item_id: int, db: AsyncSession = Depends(get_db)):
    cached = await redis_client.get(f"lazy:{item_id}")
    if cached:
        metrics_store.cache_hits += 1
        return {"id": item_id, "payload": cached, "source": "cache"}
    
    metrics_store.cache_misses += 1
    metrics_store.db_queries += 1
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if item:
        await redis_client.set(f"lazy:{item_id}", item.payload)
        return {"id": item.id, "payload": item.payload, "source": "db"}
    return {"error": "not found"}

@app.post("/lazy")
async def lazy_post(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    metrics_store.db_queries += 1
    await upsert_item(db, item.id, item.payload)
    await db.commit()
    return {"status": "ok"}

@app.get("/through/{item_id}")
async def through_get(item_id: int, db: AsyncSession = Depends(get_db)):
    cached = await redis_client.get(f"through:{item_id}")
    if cached:
        metrics_store.cache_hits += 1
        return {"id": item_id, "payload": cached, "source": "cache"}
    
    metrics_store.cache_misses += 1
    metrics_store.db_queries += 1
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if item:
        await redis_client.set(f"through:{item_id}", item.payload)
        return {"id": item.id, "payload": item.payload, "source": "db"}
    return {"error": "not found"}

@app.post("/through")
async def through_post(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    metrics_store.db_queries += 1
    await upsert_item(db, item.id, item.payload)
    await db.commit()
    
    await redis_client.set(f"through:{item.id}", item.payload)
    return {"status": "ok"}

@app.get("/back/{item_id}")
async def back_get(item_id: int, db: AsyncSession = Depends(get_db)):
    cached = await redis_client.get(f"back:{item_id}")
    if cached:
        metrics_store.cache_hits += 1
        return {"id": item_id, "payload": cached, "source": "cache"}
    
    metrics_store.cache_misses += 1
    metrics_store.db_queries += 1
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if item:
        await redis_client.set(f"back:{item_id}", item.payload)
        return {"id": item.id, "payload": item.payload, "source": "db"}
    return {"error": "not found"}

@app.post("/back")
async def back_post(item: ItemCreate):
    await redis_client.set(f"back:{item.id}", item.payload)
    await redis_client.lpush(UPDATE_QUEUE, item.model_dump_json())
    return {"status": "ok", "notice": "saved_to_cache_only"}

@app.get("/metrics")
async def get_metrics():
    stats = metrics_store.get_stats()
    stats["write_back_queue_length"] = await redis_client.llen(UPDATE_QUEUE)
    return stats

@app.delete("/metrics/reset")
async def reset_metrics():
    metrics_store.reset()
    return {"status": "metrics reset"}

@app.post("/admin/reset")
async def reset_state():
    await redis_client.flushdb()
    await reset_items()
    metrics_store.reset()
    return {"status": "state reset", "seed_items": 1000}
