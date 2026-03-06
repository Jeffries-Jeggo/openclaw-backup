#!/bin/bash
cd /home/ubuntu/.openclaw/workspace || exit 1
git add .
if git status --porcelain | grep -q .; then
  git commit -m "Auto-backup $(date +%Y-%m-%d)"
  git push origin main || echo "Push failed"
fi
echo "Auto-backup complete."