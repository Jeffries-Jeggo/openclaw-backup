#!/bin/bash
cd /home/ubuntu/.openclaw/workspace
today=$(date +%Y-%m-%d)
mkdir -p memory
logfile="memory/${today}.md"
changes=$(git status --porcelain 2>/dev/null || true)
if [ -n "$changes" ]; then
  git add .
  if git commit -m "Auto-backup ${today}" && git push origin main 2>&1; then
    result="success"
  else
    result="failed"
  fi
else
  result="no changes"
fi
echo "$(date): Auto-backup ${today}: ${result}" >> "${logfile}"
echo "Auto-backup ${today}: ${result}"