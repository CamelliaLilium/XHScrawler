from .abs_cache import AbstractCache
from .local_cache import ExpiringLocalCache
from .redis_cache import RedisCache


class CacheFactory:
    """缓存工厂类"""
    
    @staticmethod
    def create_cache(cache_type: str = "local", **kwargs) -> AbstractCache:
        """创建缓存实例
        
        Args:
            cache_type: 缓存类型 ("local" 或 "redis")
            **kwargs: 缓存初始化参数
            
        Returns:
            AbstractCache: 缓存实例
        """
        if cache_type.lower() == "redis":
            return RedisCache(**kwargs)
        else:
            return ExpiringLocalCache()
