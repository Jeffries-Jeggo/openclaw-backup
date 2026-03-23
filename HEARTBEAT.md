# HEARTBEAT.md - Proactive Tasks

# 24h Spend Tracker
# REMOVED 2026-03-24 - redundant with session_status; no longer run as cron

# Daily 6 AM Summary → Handled by cron (0 6 * * * openclaw heartbeat main)
# See HEARTBEAT.md for the cron setup. Morning summary runs via openclaw heartbeat, not here.

# Auto-Backup Task (Every Heartbeat)
- cd /home/ubuntu/.openclaw/workspace
- git add .
- If changes (git status --porcelain), commit with msg "Auto-backup [date]" and git push origin main
- Log success/failure to memory/YYYY-MM-DD.md

# Redis + Qdrant Sync (Every 6 hours)
- If ! test -f /tmp/redis-last-sync || find /tmp/redis-last-sync -mmin +360; then
  - Redis: systemctl is-active redis-server && redis-cli ping | grep PONG && cd ~/.openclaw/workspace && python3 tools/memory_cache.py sync && python3 tools/memory_cache.py cleanup --days 30
  - Qdrant: docker ps | grep qdrant && cd ~/.openclaw/workspace/tools && . qdrant_venv/bin/activate && python3 qdrant_memory.py sync && deactivate
  - Log to memory/YYYY-MM-DD.md: "Redis+Qdrant sync completed"
  - touch /tmp/redis-last-sync
- fi

# Redis Monitoring (lightweight)
- If systemctl is-active redis-server; then python3 tools/redis-check.py >> memory/YYYY-MM-DD.md; fi
