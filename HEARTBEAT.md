# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

# Daily Improvement Task (6AM Asia/Taipei)
- Run session_status → check time (Asia/Shanghai == Taipei).
- If 5-7AM: Review MEMORY.md/USER.md/AGENTS.md → pick 1 workflow improvement (e.g. script/tool/skill).
- Implement → test.
- Send message (channel=telegram, to=8738446334): "🍨 Morning improvement: [summary + value] Ready when you are!"

# Auto-Backup Task (Every Heartbeat)
- cd /home/ubuntu/.openclaw/workspace
- git add .
- If changes (git status --porcelain), commit with msg "Auto-backup [date]" and git push origin main
- Log success/failure to memory/YYYY-MM-DD.md