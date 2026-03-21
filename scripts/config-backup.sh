#!/bin/bash
# config-backup.sh
# Call BEFORE editing openclaw.json. Makes a timestamped backup and
# schedules a gateway health check in 3 minutes. If gateway goes down,
# it auto-reverts to this backup.
#
# Usage: /home/ubuntu/.openclaw/workspace/scripts/config-backup.sh

CONFIG="/home/ubuntu/.openclaw/openclaw.json"
BACKUP_DIR="/home/ubuntu/.openclaw/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP="$BACKUP_DIR/openclaw.json.$TIMESTAMP.bak"
WAIT_SECONDS=${1:-180}  # default 3 minutes, override with arg

mkdir -p "$BACKUP_DIR"

# Make a timestamped backup
cp "$CONFIG" "$BACKUP"
echo "[$(date)] Backed up openclaw.json → $BACKUP"

# Keep only the last 10 backups (prune older ones)
ls -t "$BACKUP_DIR"/openclaw.json.*.bak 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null

# Schedule safety check via background sleep+nohup
# (at(1) not available on this system)
(
    sleep "$WAIT_SECONDS"
    /home/ubuntu/.openclaw/workspace/scripts/gateway-update-safety.sh
) &
disown
echo "[$(date)] Safety rollback check scheduled in ${WAIT_SECONDS}s (PID $!)."
