import json
import logging
from typing import Optional, Callable, Awaitable
import asyncio

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self._url = redis_url
        self._conn: Optional[aioredis.Redis] = None
        self._pubsub: Optional = None

    async def connect(self):
        self._conn = aioredis.from_url(self._url, decode_responses=True)
        self._pubsub = self._conn.pubsub()
        logger.info(f"Conectado a Redis: {self._url}")

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self._conn:
            await self._conn.close()
        logger.info("Desconectado de Redis")

    async def publish(self, channel: str, data: dict):
        if self._conn is None:
            raise RuntimeError("Redis no conectado")
        await self._conn.publish(channel, json.dumps(data))

    async def subscribe(self, channel: str, handler: Callable[[dict], Awaitable[None]]):
        if self._pubsub is None:
            raise RuntimeError("Redis no conectado")
        await self._pubsub.subscribe(channel)
        logger.info(f"Suscrito a canal: {channel}")
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error en handler de {channel}: {e}")

    async def try_lock(self, key: str, ttl: int = 300) -> bool:
        if self._conn is None:
            return False
        result = await self._conn.setnx(f"lock:{key}", "1")
        if result:
            await self._conn.expire(f"lock:{key}", ttl)
        return bool(result)

    async def release_lock(self, key: str):
        if self._conn is None:
            return
        await self._conn.delete(f"lock:{key}")
