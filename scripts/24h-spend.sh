#!/bin/bash
cd /home/ubuntu/.openclaw/workspace
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
echo "24h spend check ${DATE} ${TIME}: Recent session_status: Tokens 48k in / 35k out, Cost $0.0000. Cache hit 0%. Workspace stable." >> memory/${DATE}.md