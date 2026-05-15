import pytest
from pydantic import ValidationError

from models import ProfileCreateSchema


def test_profile_schema_valid_data():
    valid_data = {
        "telegram_id": 123456789,
        "username": "sirdyyz",
        "name": "ксюша",
        "age": 18,
        "gender": "👨🏼",
        "city": "Сочи",
        "bio": "...............................",
        "search_city": "Сочи",
        "action": "create_profile"
    }
  
    schema = ProfileCreateSchema(**valid_data)
    assert schema.name == "ксюша"
    assert schema.age == 18


def test_profile_schema_invalid_age():
    invalid_data = {
        "telegram_id": 123456789,
        "name": "ксюша",
        "age": "восемнадцать",  # ошибка тут
        "gender": "👨🏼",
        "city": "сочи",
        "bio": "............",
        "search_city": "Сочи",
        "action": "create_profile"
    }
    
    with pytest.raises(ValidationError):
        ProfileCreateSchema(**invalid_data)