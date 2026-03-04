#!/usr/bin/env python3
"""
Memory caching integration for OpenClaw.
Bridges file-based memory system with Redis cache.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from redis_cache import get_cache

class MemoryCache:
    def __init__(self):
        self.cache = get_cache()
        self.workspace = os.path.expanduser('~/.openclaw/workspace')
    
    def is_available(self):
        return self.cache.is_available()
    
    # Query caching
    def cache_memory_search(self, query: str, results: list, ttl_seconds: int = 3600):
        """Cache memory_search results for a query."""
        if not self.is_available():
            return False
        return self.cache.cache_query(query, results, ttl_seconds)
    
    def get_cached_memory_search(self, query: str):
        """Get cached memory_search results."""
        if not self.is_available():
            return None
        return self.cache.get_cached_query(query)
    
    # Memory synchronization
    def sync_memory_file(self, filepath: str, source_type: str = 'memory'):
        """
        Sync a memory file to Redis cache.
        source_type: 'memory_md', 'daily_log', 'project', 'person'
        """
        if not self.is_available() or not os.path.exists(filepath):
            return 0
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Simple chunking: split by lines, consider each non-empty line as a memory
            lines = content.split('\n')
            count = 0
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Create memory ID from filepath + line number
                    memory_id = hashlib.md5(f"{filepath}:{i}".encode()).hexdigest()[:12]
                    metadata = {
                        'source': source_type,
                        'file': os.path.basename(filepath),
                        'line': i,
                        'timestamp': datetime.now().isoformat()
                    }
                    if self.cache.cache_memory(memory_id, line, metadata):
                        count += 1
            return count
        except Exception as e:
            print(f"Error syncing {filepath}: {e}")
            return 0
    
    def sync_all_memories(self):
        """Sync all memory files to Redis cache."""
        if not self.is_available():
            return {'total': 0, 'details': {}}
        
        results = {}
        
        # MEMORY.md
        memory_md = os.path.join(self.workspace, 'MEMORY.md')
        if os.path.exists(memory_md):
            count = self.sync_memory_file(memory_md, 'memory_md')
            results['MEMORY.md'] = count
        
        # Daily logs
        log_dir = os.path.join(self.workspace, 'memory')
        if os.path.exists(log_dir):
            daily_count = 0
            for log_file in os.listdir(log_dir):
                if log_file.endswith('.md'):
                    count = self.sync_memory_file(
                        os.path.join(log_dir, log_file),
                        'daily_log'
                    )
                    daily_count += count
            results['daily_logs'] = daily_count
        
        # Project files (optional)
        project_dir = os.path.join(self.workspace, 'memory', 'projects')
        if os.path.exists(project_dir):
            project_count = 0
            for proj_file in os.listdir(project_dir):
                if proj_file.endswith('.md'):
                    count = self.sync_memory_file(
                        os.path.join(project_dir, proj_file),
                        'project'
                    )
                    project_count += count
            results['projects'] = project_count
        
        total = sum(results.values())
        results['total'] = total
        return results
    
    # Session context management
    def cache_current_session(self, session_key: str, user_message: str, assistant_response: str):
        """Cache the current conversation turn."""
        if not self.is_available():
            return False
        
        # Get existing session context
        existing = self.cache.get_session_context(session_key)
        
        # Add new messages
        new_messages = existing + [
            {"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": assistant_response, "timestamp": datetime.now().isoformat()}
        ]
        
        # Keep last 20 messages max
        if len(new_messages) > 20:
            new_messages = new_messages[-20:]
        
        return self.cache.cache_session_context(session_key, new_messages)
    
    def get_session_history(self, session_key: str, limit: int = 10):
        """Get recent session history."""
        if not self.is_available():
            return []
        messages = self.cache.get_session_context(session_key)
        return messages[-limit:] if messages else []
    
    # Cleanup
    def cleanup_old_memories(self, max_age_days: int = 30):
        """Remove old cached memories."""
        if not self.is_available():
            return 0
        return self.cache.cleanup_old(max_age_days)
    
    def cleanup_old_sessions(self, max_age_days: int = 7):
        """Remove old session data."""
        if not self.is_available():
            return 0
        
        # This is a simple implementation - in production you'd track session keys
        # For now, we'll rely on Redis TTL for session keys
        return 0
    
    # Statistics
    def get_stats(self):
        """Get cache statistics."""
        if not self.is_available():
            return {}
        
        try:
            # Get Redis info
            info = self.cache.r.info()
            
            stats = {
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'uptime_in_days': info.get('uptime_in_days'),
            }
            
            # Count our keys
            memory_keys = len(self.cache.r.keys('memory:*'))
            session_keys = len(self.cache.r.keys('session:*'))
            query_keys = len(self.cache.r.keys('query:*'))
            user_keys = len(self.cache.r.keys('user:*'))
            
            stats.update({
                'memory_keys': memory_keys,
                'session_keys': session_keys,
                'query_keys': query_keys,
                'user_keys': user_keys,
                'total_keys': memory_keys + session_keys + query_keys + user_keys
            })
            
            return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

# Singleton instance
_memory_cache = None

def get_memory_cache():
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache

# CLI interface
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenClaw Memory Cache Manager')
    parser.add_argument('action', choices=['sync', 'cleanup', 'stats', 'cache_session', 'get_session', 'cache_query', 'get_query'],
                        help='Action to perform')
    parser.add_argument('--file', help='File to sync (for sync action)')
    parser.add_argument('--session', help='Session key (for session actions)')
    parser.add_argument('--query', help='Query (for query actions)')
    parser.add_argument('--user', help='User message (for cache_session)')
    parser.add_argument('--assistant', help='Assistant response (for cache_session)')
    parser.add_argument('--days', type=int, default=30, help='Days threshold for cleanup')
    
    args = parser.parse_args()
    mc = get_memory_cache()
    
    if not mc.is_available():
        print("Redis not available")
        sys.exit(1)
    
    if args.action == 'sync':
        if args.file:
            count = mc.sync_memory_file(args.file)
            print(f"Synced {count} memories from {args.file}")
        else:
            results = mc.sync_all_memories()
            print(f"Sync complete: {json.dumps(results, indent=2)}")
    
    elif args.action == 'cleanup':
        count = mc.cleanup_old_memories(args.days)
        print(f"Cleaned up {count} old memories")
    
    elif args.action == 'stats':
        stats = mc.get_stats()
        print("Cache Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.action == 'cache_session':
        if not args.session or not args.user or not args.assistant:
            print("Error: --session, --user, and --assistant required")
            sys.exit(1)
        success = mc.cache_current_session(args.session, args.user, args.assistant)
        print(f"Session cached: {success}")
    
    elif args.action == 'get_session':
        if not args.session:
            print("Error: --session required")
            sys.exit(1)
        messages = mc.get_session_history(args.session)
        print(f"Session history ({len(messages)} messages):")
        for msg in messages:
            print(f"  {msg['role']}: {msg['content'][:100]}...")
    
    elif args.action == 'cache_query':
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        # For demo, cache empty results
        mc.cache_memory_search(args.query, [])
        print(f"Query cached: {args.query}")
    
    elif args.action == 'get_query':
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        results = mc.get_cached_memory_search(args.query)
        print(f"Cached results: {results}")