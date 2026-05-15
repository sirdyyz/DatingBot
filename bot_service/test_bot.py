import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message

from bot_service.handlers.common import echo_handler


@pytest.mark.asyncio
async def test_echo_handler():
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()
    await echo_handler(mock_message)
    mock_message.answer.assert_called_once_with(
        "непонятная команда. выберите действие из меню ниже 👇"
    )