#!/usr/bin/env python3
import redis
import sys
import json
from datetime import datetime

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

if len(sys.argv) != 4:
    print('Usage: cache_conversation.py &quot;SESSION_KEY&quot; &quot;USER_MSG&quot; &quot;AI_RESPONSE&quot;')
    sys.exit(1)

session_key, user_msg, ai_response = sys.argv[1:]

data = {
    'user': user_msg,
    'ai': ai_response,
    'ts': datetime.now().isoformat()
}

r.set(f&quot;chat:{session_key}:latest&quot;, json.dumps(data))
r.expire(f&quot;chat:{session_key}:latest&quot;, 86400*7)  # 7 days

print(f&quot;Cached chat for {session_key}&quot;)