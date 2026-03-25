#!/bin/bash
# gateway-watchdog.sh — Monitor gateway, restore from backup if down > 3 minutes
set -e

GATEWAY_JSON="$HOME/.openclaw/openclaw.json"
BACKUP_DIR="$HOME/.openclaw/backups"
LOCK_FILE="/tmp/gateway-watchdog.lock"
WAIT_MINUTES=3

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    lock_age=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
    if [ "$lock_age" -lt 300 ]; then
        echo "[watchdog] Another instance is running (lock age: ${lock_age}s). Exiting."
        exit 0
    fi
    echo "[watchdog] Stale lock found (${lock_age}s). Proceeding."
fi
touch "$LOCK_FILE"

# Cleanup on exit
trap "rm -f $LOCK_FILE" EXIT

# Check if gateway is up
check_gateway() {
    curl -s --max-time 5 "http://127.0.0.1:18789/healthz" > /dev/null 2>&1
}

if check_gateway; then
    echo "[watchdog] Gateway is healthy"
    exit 0
fi

echo "[watchdog] Gateway is DOWN. Waiting ${WAIT_MINUTES} minutes before restoring..."

# Wait 3 minutes to give gateway a chance to recover on its own
sleep $((WAIT_MINUTES * 60))

# Check again after wait
if check_gateway; then
    echo "[watchdog] Gateway recovered on its own. No action needed."
    exit 0
fi

echo "[watchdog] Gateway still down after ${WAIT_MINUTES} minutes. Restoring from backup..."

# Find latest backup
latest_backup=$(ls -t "$BACKUP_DIR"/openclaw-*.json 2>/dev/null | head -1)
if [ -z "$latest_backup" ]; then
    echo "[watchdog] ERROR: No backup found in $BACKUP_DIR"
    exit 1
fi

echo "[watchdog] Restoring: $latest_backup"

# Backup current (possibly corrupt) json
cp "$GATEWAY_JSON" "$BACKUP_DIR/openclaw-pre-watchdog-restore-$(date +%Y%m%d-%H%M%S).json"

# Restore from latest backup
cp "$latest_backup" "$GATEWAY_JSON"

# Validate restored JSON
if ! python3 -m json.tool "$GATEWAY_JSON" > /dev/null 2>&1; then
    echo "[watchdog] ERROR: Restored JSON is invalid!"
    exit 1
fi

echo "[watchdog] Restarting gateway with restored config..."
openclaw gateway restart

# Wait for it to come up
for i in {1..30}; do
    sleep 2
    if check_gateway; then
        echo "[watchdog] Gateway is back up after restore!"
        exit 0
    fi
done

echo "[watchdog] ERROR: Gateway still not responding after restore. Manual intervention needed."
exit 1
