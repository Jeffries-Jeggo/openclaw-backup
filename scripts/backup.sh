#!/bin/bash
# Auto-backup script for workspace

cd /home/ubuntu/.openclaw/workspace
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

echo "## Backup - $DATE $TIME" >> memory/$DATE.md

git add .
if git status --porcelain | grep -q .; then
  git commit -m "Auto-backup $DATE"
  git push origin main
  echo "Changes committed and pushed."
else
  echo "No changes."
fi

echo "Backup complete."
