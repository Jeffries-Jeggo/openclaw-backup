#!/bin/bash
# gateway-update-safety.sh
# Run a few minutes after an openclaw.json edit.
# If gateway is down, revert to the most recent backup.

CONFIG="/home/ubuntu/.openclaw/openclaw.json"
BACKUP_DIR="/home/ubuntu/.openclaw/backups"
GATEWAY_PORT=18789
CHECK_TIMEOUT=5
WAIT_MINUTES=3

mkdir -p "$BACKUP_DIR"

# Find the most recent backup
LATEST=$(ls -t "$BACKUP_DIR"/openclaw.json.*.bak 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "[$(date)] No backup found to revert to. Skipping."
    exit 0
fi

# Check if gateway is up
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $CHECK_TIMEOUT "http://127.0.0.1:$GATEWAY_PORT/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "[$(date)] Gateway is healthy (HTTP $HTTP_CODE). No revert needed."
    # Backup is still good — keep it for a few more hours in case of delayed crash
    exit 0
fi

echo "[$(date)] Gateway is DOWN (HTTP $HTTP_CODE). Reverting to $LATEST..."

# Revert config
cp "$LATEST" "$CONFIG"
echo "[$(date)] Reverted openclaw.json from $LATEST" | tee -a /home/ubuntu/.openclaw/workspace/memory/gateway-revert-log.txt

# Restart gateway
systemctl --user restart openclaw-gateway
echo "[$(date)] Gateway restart triggered after revert." | tee -a /home/ubuntu/.openclaw/workspace/memory/gateway-revert-log.txt
