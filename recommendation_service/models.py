from pydantic import BaseModel


class ActionModel(BaseModel):
    from_telegram_id: str
    to_profile_id: int
    action: str  # 'like' или 'skip'
