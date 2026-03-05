# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

# Daily Improvement Task (6AM Asia/Taipei)
- Run session_status → check time (Asia/Shanghai == Taipei).
- If 5-7AM: Review MEMORY.md/USER.md/AGENTS.md → pick 1 workflow improvement (e.g. script/tool/skill).
- Implement → test.
- Send message (channel=telegram, to=8738446334): "🍨 Morning improvement: [summary + value] Ready when you are!"

# Test Heartbeat (one-time, next poll)
- If ! test -f /tmp/heartbeat-reindeer-test-done: message(action=send, channel=telegram, to=8738446334) "🍨 Heartbeat test: Reindeer facts! 🦌 Migrate 3k+km/year, females grow antlers (unique), domesticated for sleds, 800 subspecies, glow-in-dark nose myth (Rudolph)."
- touch /tmp/heartbeat-reindeer-test-done

# Auto-Backup Task (Every Heartbeat)
- cd /home/ubuntu/.openclaw/workspace
- git add .
- If changes (git status --porcelain), commit with msg "Auto-backup [date]" and git push origin main
- Log success/failure to memory/YYYY-MM-DD.md

# 24h Spend Tracker (Daily 6AM + Every Heartbeat if changed)
- cd /home/ubuntu/.openclaw/workspace && ./scripts/24h-spend.sh


# Redis Cache Maintenance (Every 6 hours)
- If ! test -f /tmp/redis-last-sync || find /tmp/redis-last-sync -mmin +360 2>/dev/null | grep -q .; then
  - Check Redis: systemctl is-active redis-server && redis-cli ping 2>&1 | grep -q PONG
  - If active:
    - cd ~/.openclaw/workspace && python3 tools/memory_cache.py sync 2>&1 | tail -5
    - cd ~/.openclaw/workspace && python3 tools/memory_cache.py cleanup --days 30 2>&1 | tail -2
    - cd ~/.openclaw/workspace && python3 tools/memory_cache.py stats 2>&1 | grep -E "(total_keys|used_memory_human)" | head -5
    - Log to memory/YYYY-MM-DD.md: "Redis sync: [timestamp] keys=[total_keys] mem=[used_memory_human]"
  - touch /tmp/redis-last-sync
- fi

# Qdrant Reminder (Wed March 11, 2026 6AM)
- Run session_status → get current date/time
- If date=2026-03-11 AND hour=5-7 (Asia/Shanghai): 
  - message(action=send, channel=telegram, to=8738446334): "🍨 **Reminder**: Time to check out Qdrant for advanced memory (vector search after Redis)! Details in MEMORY.md. Ready?"
  - Log to memory/2026-03-11.md: "Qdrant reminder sent"

# Redis Monitoring (Every heartbeat, lightweight)
- If systemctl is-active redis-server; then
  - Check memory: redis-cli info memory | grep -E "used_memory_human|maxmemory" | head -2
  - If used_memory_human > 100MB: log warning to memory/YYYY-MM-DD.md
- fi