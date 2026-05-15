import os
import sys

import redis.asyncio as redis

from bot_service.database.engine import async_session as async_session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

redis_client = redis.Redis(host='dating_redis', port=6379, decode_responses=True)
