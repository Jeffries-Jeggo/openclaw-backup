#!/usr/bin/env python3
import redis
import sys
import json
import re

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

query = sys.argv[1] if len(sys.argv) > 1 else ''

keys = r.keys('chat:*')
results = []

for key in keys:
    data_str = r.get(key)
    if data_str:
        data = json.loads(data_str)
        score = len(re.findall(re.escape(query.lower()), (data.get('user','') + data.get('ai','')).lower()))
        if score > 0:
            results.append((score, key, data))

results.sort(reverse=True)
for score, key, data in results[:5]:
    print(f&quot;Score {score}: {key} - {data['ts'][:16]}&quot;)
    print(f&quot;User: {data['user'][:100]}...&quot;)
    print(f&quot;AI: {data['ai'][:100]}...&quot;)
    print('---')