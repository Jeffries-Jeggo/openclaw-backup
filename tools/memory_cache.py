#!/usr/bin/env python3
import redis
import sys
import os
import json
import argparse
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def sync():
    print('Syncing memory files to Redis...')
    memories_dir = '/home/ubuntu/.openclaw/workspace/memory'
    if os.path.exists(memories_dir):
        count = 0
        for f in os.listdir(memories_dir):
            if f.endswith('.md'):
                path = os.path.join(memories_dir, f)
                try:
                    with open(path, 'r') as fd:
                        content = fd.read()
                    r.set(f'memory:{f}', content[:10000])  # truncate long files
                    count += 1
                except Exception as e:
                    print(f'Skip {f}: {e}')
        print(f'Synced {count} memory files.')
    else:
        print('No memory dir.')

def cleanup(days=30):
    cutoff = datetime.now().timestamp() - days*86400
    keys = r.keys('memory:*')
    deleted = 0
    for key in keys:
        ttl = r.ttl(key)
        if ttl == -1 or ttl < cutoff:  # -1 = no expiry
            r.delete(key)
            deleted += 1
    print(f'Cleaned {deleted} old/infinite TTL keys.')

def stats():
    info = r.info()
    db_info = info.get('db0', {})
    print(f'total_keys: {db_info.get("keys", 0)}')
    print(f'used_memory_human: {info.get("used_memory_human", "unknown")}')
    print(f'maxmemory: {info.get("maxmemory_human", "unlimited") or "unlimited"}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['sync', 'cleanup', 'stats'], nargs='?', default='stats')
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()
    
    if args.command == 'sync':
        sync()
    elif args.command == 'cleanup':
        cleanup(args.days)
    elif args.command == 'stats':
        stats()