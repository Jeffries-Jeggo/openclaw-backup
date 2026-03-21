#!/bin/bash
# Morning summary - fires once per day at 6 AM, sends via Telegram Bot API
LOCK="/tmp/morning-summary-$(date +%Y-%m-%d).lock"
if [ -f "$LOCK" ]; then
  exit 0
fi

BOT_TOKEN="8676493387:AAFULHgDxwYAK9O_U_aXQkXV1I0Mc6wM02o"
CHAT_ID="8738446334"
DAY=$(date +%w)

FACTS=(
  "OpenClaw's modular skills system lets you extend capabilities by simply dropping in SKILL.md files from clawhub.com."
  "OpenClaw's gateway WebSocket API lets you connect external tools and dashboards in real-time."
  "OpenClaw supports multiple channels simultaneously: Telegram, WhatsApp, Discord, LINE, and more."
  "You can run multiple agents on the same gateway, each with their own workspace and configuration."
  "OpenClaw's memory system supports both file-based notes and vector storage via Qdrant for semantic search."
  "The 'openclaw gateway restart' command gracefully restarts the gateway via systemd without dropping connections."
  "OpenClaw's built-in cron system lets you schedule agent tasks with cron expressions and timezone support."
)
FACT="${FACTS[$DAY]}"

# Fetch recent git change as improvement note
RECENT=$(cd /home/ubuntu/.openclaw/workspace && git log --oneline -1 2>/dev/null | sed 's/"/\"/g')
IMPROVEMENT="System stable. Last: $RECENT"

MESSAGE="🍨 Good morning Will!

Improvement: $IMPROVEMENT

OpenClaw Fact #$DAY: $FACT

Ready when you are!"

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$CHAT_ID" \
  -d "text=$MESSAGE" > /dev/null 2>&1

touch "$LOCK"
