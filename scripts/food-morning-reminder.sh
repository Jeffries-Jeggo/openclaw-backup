#!/bin/bash
# Morning food logging reminder
BOT_TOKEN="8676493387:AAFULHgDxwYAK9O_U_aXQkXV1I0Mc6wM02o"
CHAT_ID="8738446334"
FOOD_DIR="/home/ubuntu/.openclaw/workspace-lulu/food-logs"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$FOOD_DIR/$TODAY.md"

MESSAGE="🌅 Morning, Lulu!

Don't forget to log your meals today! 

Just send me what you eat and I'll look up the macros for you. E.g. '2 eggs and toast' or 'salad with chicken breast'"

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$CHAT_ID" \
  -d "text=$MESSAGE" > /dev/null 2>&1
