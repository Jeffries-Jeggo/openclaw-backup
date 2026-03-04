#!/usr/bin/env python3
"""
CLI to search Redis cache.
"""
import sys
from redis_cache import get_cache

def search(query, limit=10):
    cache = get_cache()
    if not cache.is_available():
        print("Redis not available")
        return []
    results = cache.search_cached_memories(query, limit)
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: redis_search.py <query> [limit]")
        sys.exit(1)
    query = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    results = search(query, limit)
    print(f"Found {len(results)} results for '{query}':")
    for i, res in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"ID: {res['id']}")
        print(f"Content: {res['content']}")
        print(f"Metadata: {res['metadata']}")