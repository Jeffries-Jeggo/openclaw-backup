#!/usr/bin/env python3
"""
Redis cache for OpenClaw memory system.
"""
import redis
import json
import hashlib
import time
from typing import List, Dict, Any, Optional

class RedisCache:
    def __init__(self, host='localhost', port=6379, decode_responses=True):
        self.r = redis.Redis(host=host, port=port, decode_responses=decode_responses)
        try:
            self.r.ping()
        except redis.ConnectionError:
            print("Warning: Redis not available, caching disabled")
            self.r = None
    
    def is_available(self):
        return self.r is not None
    
    # Session context caching
    def cache_session_context(self, session_key: str, messages: List[Dict], ttl_seconds: int = 86400):
        """Cache recent conversation messages for a session."""
        if not self.is_available():
            return False
        key = f"session:{session_key}:recent"
        # Keep last 10 messages
        serialized = [json.dumps(m) for m in messages[-10:]]
        self.r.delete(key)
        if serialized:
            self.r.rpush(key, *serialized)
            self.r.expire(key, ttl_seconds)
        return True
    
    def get_session_context(self, session_key: str) -> List[Dict]:
        """Retrieve cached session context."""
        if not self.is_available():
            return []
        key = f"session:{session_key}:recent"
        messages = self.r.lrange(key, 0, -1)
        return [json.loads(m) for m in messages]
    
    # Memory caching
    def cache_memory(self, memory_id: str, content: str, metadata: Dict, ttl_seconds: Optional[int] = None):
        """Cache a memory with metadata."""
        if not self.is_available():
            return False
        # Store content
        self.r.set(f"memory:{memory_id}:content", content)
        # Store metadata as hash
        if metadata:
            self.r.hset(f"memory:{memory_id}:metadata", mapping=metadata)
        # Add to memory index
        self.r.zadd("memories:index", {memory_id: time.time()})
        if ttl_seconds:
            self.r.expire(f"memory:{memory_id}:content", ttl_seconds)
            self.r.expire(f"memory:{memory_id}:metadata", ttl_seconds)
        return True
    
    def get_cached_memory(self, memory_id: str) -> Optional[Dict]:
        """Retrieve a cached memory with metadata."""
        if not self.is_available():
            return None
        content = self.r.get(f"memory:{memory_id}:content")
        if content is None:
            return None
        metadata = self.r.hgetall(f"memory:{memory_id}:metadata")
        return {"content": content, "metadata": metadata}
    
    def search_cached_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Simple keyword search in cached memories.
        For production, use proper search (RedisSearch or external).
        """
        if not self.is_available():
            return []
        # Get all memory IDs from index
        memory_ids = self.r.zrange("memories:index", 0, -1)
        results = []
        for mem_id in memory_ids:
            content = self.r.get(f"memory:{mem_id}:content")
            if content and query.lower() in content.lower():
                metadata = self.r.hgetall(f"memory:{mem_id}:metadata")
                results.append({
                    "id": mem_id,
                    "content": content,
                    "metadata": metadata
                })
                if len(results) >= limit:
                    break
        return results
    
    # User preferences
    def cache_user_preferences(self, user_id: str, preferences: Dict):
        if not self.is_available():
            return False
        key = f"user:{user_id}:preferences"
        self.r.hset(key, mapping=preferences)
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict:
        if not self.is_available():
            return {}
        key = f"user:{user_id}:preferences"
        return self.r.hgetall(key)
    
    # Query cache (cache memory_search results)
    def cache_query(self, query: str, results: List[Dict], ttl_seconds: int = 3600):
        if not self.is_available():
            return False
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"query:{query_hash}"
        self.r.setex(key, ttl_seconds, json.dumps(results))
        return True
    
    def get_cached_query(self, query: str) -> Optional[List[Dict]]:
        if not self.is_available():
            return None
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"query:{query_hash}"
        cached = self.r.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    # Cleanup old entries (heartbeat task)
    def cleanup_old(self, max_age_days: int = 7):
        if not self.is_available():
            return 0
        cutoff = time.time() - (max_age_days * 86400)
        old_ids = self.r.zrangebyscore("memories:index", 0, cutoff)
        for mem_id in old_ids:
            self.r.delete(f"memory:{mem_id}:content")
            self.r.delete(f"memory:{mem_id}:metadata")
        self.r.zremrangebyscore("memories:index", 0, cutoff)
        return len(old_ids)

# Singleton instance
_cache = None

def get_cache():
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache

# Convenience functions
def cache_session(session_key, messages):
    return get_cache().cache_session_context(session_key, messages)

def get_session(session_key):
    return get_cache().get_session_context(session_key)

def cache_memory(memory_id, content, metadata=None):
    return get_cache().cache_memory(memory_id, content, metadata or {})

def search_cache(query, limit=10):
    return get_cache().search_cached_memories(query, limit)

if __name__ == "__main__":
    # Simple test
    cache = RedisCache()
    print("Redis available:", cache.is_available())
    if cache.is_available():
        # Test session caching
        cache.cache_session_context("test_session", [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ])
        print("Session context:", cache.get_session_context("test_session"))
        
        # Test memory caching
        cache.cache_memory("test_mem", "Teaching Harvard PDFs", {"tags": "teaching, pdf", "project": "harvard"})
        print("Cached memory:", cache.get_cached_memory("test_mem"))
        
        # Test search
        print("Search 'pdf':", cache.search_cached_memories("pdf"))