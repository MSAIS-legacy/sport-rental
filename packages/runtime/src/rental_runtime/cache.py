import logging

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Cache-aside. При недоступности Redis запрос обслуживается из PostgreSQL."""

    def __init__(self, url, namespace, ttl=60):
        self.client = redis.Redis.from_url(
            url, decode_responses=True, socket_connect_timeout=0.3, socket_timeout=0.3
        )
        self.namespace, self.ttl = namespace, ttl

    def get(self, key):
        try:
            return self.client.get(f"{self.namespace}:{key}")
        except redis.RedisError:
            logger.warning("Redis unavailable; reading database")
            return None

    def set(self, key, value):
        try:
            self.client.setex(f"{self.namespace}:{key}", self.ttl, value)
        except redis.RedisError:
            logger.warning("Redis unavailable; skipping cache write")
