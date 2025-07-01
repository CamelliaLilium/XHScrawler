import time
from typing import Any, Optional
from .abs_cache import AbstractCache


class ExpiringLocalCache(AbstractCache):
    """带过期时间的本地内存缓存"""
    
    def __init__(self):
        self._cache = {}
        self._expire_times = {}
    
    def _is_expired(self, key: str) -> bool:
        """检查key是否过期"""
        if key not in self._expire_times:
            return False
        return time.time() > self._expire_times[key]
    
    async def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        if self._is_expired(key):
            await self.delete(key)
            return None
            
        return self._cache[key]
    
    async def set(self, key: str, value: Any, expire_time: int = 0) -> None:
        self._cache[key] = value
        if expire_time > 0:
            self._expire_times[key] = time.time() + expire_time
    
    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
        self._expire_times.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        if key not in self._cache:
            return False
        
        if self._is_expired(key):
            await self.delete(key)
            return False
            
        return True
