from pydantic import BaseModel


class ProfileCreateSchema(BaseModel):
    action: str
    telegram_id: int
    username: str | None = 'unknown'
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    city: str | None = None
    bio: str | None = None
    search_city: str
