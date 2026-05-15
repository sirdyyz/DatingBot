import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from recommendation_service.main import app, redis_client

redis_client.lpop = AsyncMock(return_value=None)
redis_client.rpush = AsyncMock()
redis_client.expire = AsyncMock()


@pytest.mark.asyncio
@patch("recommendation_service.main.async_session")
async def test_get_next_profile_user_not_found(mock_async_session):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_async_session.return_value.__aenter__.return_value = mock_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/next/fake_telegram_id_999")
    assert response.status_code == 200
    assert response.json() == {"status": "error"}


@pytest.mark.asyncio
async def test_action_invalid_data():
    bad_payload = {"from_telegram_id": "123"} 
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/action", json=bad_payload)
    assert response.status_code == 422