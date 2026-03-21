#!/bin/bash
# Gateway stability monitor - logs restart count and any new restarts since last check
LOG="/home/ubuntu/.openclaw/workspace/memory/gateway-restart-log.txt"
LAST_COUNT_FILE="/tmp/gateway-restart-count.last"

# Get current restart count from systemd journal (only today's events)
RESTART_COUNT=$(journalctl --user -b --no-pager 2>/dev/null | grep -c "Started openclaw-gateway.service" || echo "0")

if [ -f "$LAST_COUNT_FILE" ]; then
    LAST_COUNT=$(cat "$LAST_COUNT_FILE")
    if [ "$RESTART_COUNT" != "$LAST_COUNT" ]; then
        NEW_RESTARTS=$((RESTART_COUNT - LAST_COUNT))
        echo "$(date): WARNING - Gateway restarted $NEW_RESTARTS time(s) since last check (total restarts today: $RESTART_COUNT)" >> "$LOG"
    fi
else
    echo "$(date): Gateway monitoring started. Total restarts today: $RESTART_COUNT" >> "$LOG"
fi

echo "$RESTART_COUNT" > "$LAST_COUNT_FILE"
