#!/bin/bash
cd /home/ubuntu/.openclaw/workspace
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)
mkdir -p memory
if git status --porcelain | grep -q .; then
  git add .
  git commit -m "Auto-backup ${DATE}"
  if git push origin main; then
    echo "Auto-backup ${DATE} ${TIME}: success." >> memory/${DATE}.md
  else
    echo "Auto-backup ${DATE} ${TIME}: push failed." >> memory/${DATE}.md
  fi
else
  echo "Auto-backup ${DATE} ${TIME}: No changes." >> memory/${DATE}.md
fi