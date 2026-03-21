#!/usr/bin/env python3
"""
Warm up Redis cache with existing memories from MEMORY.md and daily logs.
"""
import os
import re
import json
import hashlib
from datetime import datetime
from redis_cache import get_cache

def parse_memory_md(filepath):
    """Parse MEMORY.md into structured memories."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    memories = []
    current_section = None
    lines = content.split('\n')
    
    # Simple parsing for demo
    # Look for headings and content
    for i, line in enumerate(lines):
        if line.startswith('## '):
            current_section = line[3:].strip()
        elif line.startswith('### '):
            current_section = line[4:].strip()
        elif line.strip() and current_section and not line.startswith('#'):
            # Create a memory from this line
            memory_id = hashlib.md5(f"{current_section}:{line}".encode()).hexdigest()[:8]
            memories.append({
                'id': memory_id,
                'content': line.strip(),
                'metadata': {
                    'section': current_section,
                    'source': 'MEMORY.md',
                    'timestamp': datetime.now().isoformat()
                }
            })
    
    return memories

def parse_daily_logs(log_dir, limit=50):
    """Parse recent daily logs."""
    memories = []
    if not os.path.exists(log_dir):
        return memories
    
    log_files = sorted(os.listdir(log_dir), reverse=True)[:5]
    for log_file in log_files:
        if log_file.endswith('.md'):
            with open(os.path.join(log_dir, log_file), 'r') as f:
                content = f.read()
            # Split by lines, take each line as potential memory
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    memory_id = hashlib.md5(f"{log_file}:{line}".encode()).hexdigest()[:8]
                    memories.append({
                        'id': memory_id,
                        'content': line.strip(),
                        'metadata': {
                            'source': 'daily_log',
                            'file': log_file,
                            'timestamp': datetime.now().isoformat()
                        }
                    })
    return memories

def warmup():
    cache = get_cache()
    if not cache.is_available():
        print("Redis not available, skipping warmup")
        return
    
    workspace = os.path.expanduser('~/.openclaw/workspace')
    
    # Load MEMORY.md
    memory_md = os.path.join(workspace, 'MEMORY.md')
    if os.path.exists(memory_md):
        memories = parse_memory_md(memory_md)
        for mem in memories:
            cache.cache_memory(mem['id'], mem['content'], mem['metadata'])
        print(f"Cached {len(memories)} memories from MEMORY.md")
    
    # Load daily logs
    log_dir = os.path.join(workspace, 'memory')
    if os.path.exists(log_dir):
        daily_memories = parse_daily_logs(log_dir)
        for mem in daily_memories:
            cache.cache_memory(mem['id'], mem['content'], mem['metadata'])
        print(f"Cached {len(daily_memories)} memories from daily logs")
    
    # Cache user preferences (hardcoded for now)
    preferences = {
        'timezone': 'Asia/Taipei',
        'interests': 'teaching, AI agents, memory systems',
        'projects': 'harvard-pdfs, cody-bot, health-tracker',
        'last_backup': datetime.now().isoformat()
    }
    cache.cache_user_preferences('will', preferences)
    print("Cached user preferences")
    
    # Show stats
    memory_ids = cache.r.zrange("memories:index", 0, -1)
    print(f"Total cached memories: {len(memory_ids)}")
    print("Sample memory IDs:", memory_ids[:5])

if __name__ == "__main__":
    warmup()