#!/bin/bash
# Food log entry script
# Usage: ./food-log.sh add "<food description>"
#        ./food-log.sh summary

FOOD_DIR="/home/ubuntu/.openclaw/workspace-lulu/food-logs"
BOT_TOKEN="8676493387:AAFULHgDxwYAK9O_U_aXQkXV1I0Mc6wM02o"
CHAT_ID="8738446334"

TODAY=$(date +%Y-%m-%d)
LOG_FILE="$FOOD_DIR/$TODAY.md"

if [ ! -f "$LOG_FILE" ]; then
  cat > "$LOG_FILE" << 'EOF'
# Food Log — YYYY-MM-DD

## Entries

| Time | Food | Fat (g) | Protein (g) | Carbs (g) | Calories |
|------|------|---------|-------------|-----------|----------|

## Totals

| | Fat (g) | Protein (g) | Carbs (g) | Calories |
|-|---------|-------------|-----------|----------|
| **Total** | 0 | 0 | 0 | 0 |

EOF
  sed -i "s/YYYY-MM-DD/$TODAY/" "$LOG_FILE"
fi

if [ "$1" = "add" ]; then
  shift
  FOOD="$*"
  TIME=$(date +%H:%M)
  echo "[$TIME] $FOOD" >> "$LOG_FILE"
  echo "Logged: $FOOD at $TIME"
elif [ "$1" = "today" ]; then
  cat "$LOG_FILE"
elif [ "$1" = "summary" ]; then
  MESSAGE=$(tail -20 "$LOG_FILE" 2>/dev/null)
  echo "=== Today's Food Log ==="
  cat "$LOG_FILE"
else
  echo "Usage: food-log.sh add <food> | today | summary"
fi
