from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractCache(ABC):
    """抽象缓存类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, expire_time: int = 0) -> None:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        pass
