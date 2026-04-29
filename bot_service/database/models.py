import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[str] = mapped_column(String, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column()
    gender: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    bio: Mapped[str] = mapped_column(Text)
    search_city: Mapped[str] = mapped_column(String)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Like(Base):
    __tablename__ = "likes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class Visit(Base):
    __tablename__ = "visits"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

class ProfileStat(Base):
    __tablename__ = "profile_stats"
    profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    visits_count: Mapped[int] = mapped_column(Integer, default=0)
    matches_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=10.0)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
