#!/bin/bash
# graceful-restart.sh — Safe gateway restart with automatic backup
set -e

GATEWAY_JSON="$HOME/.openclaw/openclaw.json"
BACKUP_DIR="$HOME/.openclaw/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create a backup before any changes (caller should already have done this, but double-check)
if [ ! -f "$BACKUP_DIR/openclaw-$TIMESTAMP.json" ]; then
    cp "$GATEWAY_JSON" "$BACKUP_DIR/openclaw-$TIMESTAMP.json"
    echo "[graceful-restart] Backup created: openclaw-$TIMESTAMP.json"
fi

# Validate JSON
python3 -m json.tool "$GATEWAY_JSON" > /dev/null || {
    echo "[graceful-restart] ERROR: Invalid JSON in openclaw.json"
    exit 1
}

# Validate config
validate_output=$(openclaw config validate 2>&1)
if [ $? -ne 0 ]; then
    echo "[graceful-restart] ERROR: Config validation failed"
    echo "$validate_output"
    exit 1
fi

# Restart gateway
echo "[graceful-restart] Restarting gateway..."
openclaw gateway restart

# Wait for it to come up
echo "[graceful-restart] Waiting for gateway..."
for i in {1..30}; do
    sleep 2
    if curl -s "http://127.0.0.1:18789/healthz" > /dev/null 2>&1; then
        echo "[graceful-restart] Gateway is up after $((i*2)) seconds"
        exit 0
    fi
done

echo "[graceful-restart] WARNING: Gateway did not come up within 60 seconds"
exit 1
