#!/usr/bin/env python3
"""
Cache a conversation turn to Redis.
To be called by the agent after each response.
"""
import os
import sys
import json
from memory_cache import get_memory_cache

def main():
    if len(sys.argv) < 4:
        print("Usage: cache_conversation.py <session_key> <user_message> <assistant_message>")
        sys.exit(1)
    
    session_key = sys.argv[1]
    user_message = sys.argv[2]
    assistant_message = sys.argv[3]
    
    mc = get_memory_cache()
    if not mc.is_available():
        print("Redis not available", file=sys.stderr)
        sys.exit(0)  # Not fatal
    
    success = mc.cache_current_session(session_key, user_message, assistant_message)
    if success:
        print(f"Cached conversation turn for session {session_key}")
        
        # Also create a memory entry for this conversation
        # Use first 100 chars as content
        content = f"User: {user_message[:100]}... | Assistant: {assistant_message[:100]}..."
        memory_id = f"conv:{session_key}:{hash(user_message) & 0xffffffff}"
        
        from redis_cache import get_cache
        cache = get_cache()
        metadata = {
            'type': 'conversation_turn',
            'session': session_key,
            'timestamp': os.environ.get('TIMESTAMP', ''),
            'source': 'telegram_direct'
        }
        cache.cache_memory(memory_id, content, metadata)
    else:
        print("Failed to cache conversation", file=sys.stderr)
    
    # Also sync recent memory files (opportunistic)
    # This could be heavy, maybe do it less frequently
    # mc.sync_all_memories()

if __name__ == "__main__":
    main()