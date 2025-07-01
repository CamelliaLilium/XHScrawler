import redis
from typing import Any, Optional
from .abs_cache import AbstractCache


class RedisCache(AbstractCache):
    """Redis缓存实现"""
    
    def __init__(self, host='localhost', port=6379, db=0, **kwargs):
        self.redis_client = redis.Redis(host=host, port=port, db=db, **kwargs)
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            return value.decode('utf-8') if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, expire_time: int = 0) -> None:
        try:
            if expire_time > 0:
                self.redis_client.setex(key, expire_time, str(value))
            else:
                self.redis_client.set(key, str(value))
        except Exception:
            pass
    
    async def delete(self, key: str) -> None:
        try:
            self.redis_client.delete(key)
        except Exception:
            pass
    
    async def exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False
