import json

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.ws_manager import manager

CHANNEL = "submission_updates"


async def listen_for_updates():
    client = aioredis.from_url(settings.celery_broker_url)
    pubsub = client.pubsub()
    await pubsub.subscribe(CHANNEL)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
        except (json.JSONDecodeError, TypeError):
            continue
        submission_id = data.get("submission_id")
        if submission_id:
            await manager.broadcast(submission_id, data)
