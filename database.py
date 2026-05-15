import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, delete
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    payload = Column(String, nullable=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def reset_items():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Item))
        session.add_all(
            Item(id=item_id, payload=f"seed_{item_id}")
            for item_id in range(1, 1001)
        )
        await session.commit()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
