"""
Cache module for EmoJourney.
Provides a simple in-memory cache for API responses with TTL.
"""
import time
from typing import Dict, Any, Optional, Tuple

class Cache:
    """Simple in-memory cache with time-to-live functionality."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            ttl: Time-to-live in seconds for cached items (default 1 hour)
        """
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Check if the cache entry has expired
        if time.time() - timestamp > self.ttl:
            # Remove expired entry
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Store an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self.cache.clear()
    
    def remove(self, key: str) -> None:
        """
        Remove a specific key from the cache.
        
        Args:
            key: The cache key to remove
        """
        if key in self.cache:
            del self.cache[key]
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            Number of items in the cache
        """
        return len(self.cache)
    
    def is_enabled(self) -> bool:
        """
        Check if the cache is enabled.
        
        Returns:
            True if the cache is enabled (ttl > 0)
        """
        return self.ttl > 0


# Create a global instance for easy import
emotion_cache = Cache(ttl=3600)  # 1 hour TTL 