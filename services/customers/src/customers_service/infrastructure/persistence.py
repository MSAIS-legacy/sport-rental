from rental_runtime.cache import RedisCache
from rental_runtime.database import Database, SQLUnitOfWork

from ..domain.errors import NotFound


def create_uow_factory(url, redis_url=None):
    database = Database(url)
    cache = RedisCache(redis_url, "customers") if redis_url else None
    return lambda: SQLUnitOfWork(database, NotFound, cache)
