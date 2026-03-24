#!/bin/bash
# Evening food summary — sent at 7:30 PM
BOT_TOKEN="8676493387:AAFULHgDxwYAK9O_U_aXQkXV1I0Mc6wM02o"
LULU_CHAT_ID="8025038227"
FOOD_DIR="/home/ubuntu/.openclaw/workspace-lulu/food-logs"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$FOOD_DIR/$TODAY.md"

if [ ! -f "$LOG_FILE" ]; then
  MESSAGE="🍽️ Hey Lulu!

You haven't logged any food today. Don't worry about it — just start fresh tomorrow!"
else
  FAT=$(grep -oP '(?<=\| \*\*Total\*\* \| )[\d.]+' "$LOG_FILE" | head -1 || echo "0")
  PROTEIN=$(grep -oP '(?<=\| \*\*Total\*\* \| \| )[\d.]+' "$LOG_FILE" | head -1 || echo "0")
  CARBS=$(grep -oP '(?<=\| \*\*Total\*\* \| \| \| )[\d.]+' "$LOG_FILE" | head -1 || echo "0")
  CALS=$(grep -oP '(?<=\| \*\*Total\*\* \| \| \| \| )[\d.]+' "$LOG_FILE" | head -1 || echo "0")
  
  MESSAGE="🍽️ Evening check-in, Lulu!

📊 Today's macros:
• Fat: ${FAT}g
• Protein: ${PROTEIN}g  
• Carbs: ${CARBS}g
• Calories: ${CALS}

Keep up the good work! 💪"
fi

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$LULU_CHAT_ID" \
  -d "text=$MESSAGE" > /dev/null 2>&1
