import json
import os

import aio_pika
from dotenv import load_dotenv

load_dotenv()

async def send_to_moderation(profile_data: dict):
    url = os.getenv("RABBITMQ_URL")
    print(url)
    connection = await aio_pika.connect_robust(url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("moderation_queue", durable=True)

        message = aio_pika.Message(
            body=json.dumps(profile_data).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await channel.default_exchange.publish(message, routing_key="moderation_queue")
