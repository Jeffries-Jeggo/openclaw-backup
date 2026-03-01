# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

# Daily Improvement Task
- Every day (around 6am if possible), work on a self-initiated task to improve the user's pre-existing workflows.
- First, review relevant files (MEMORY.md, USER.md, AGENTS.md, etc.) to understand current workflows and identify areas for improvement.
- Choose one concrete improvement to implement.
- Present the completed task to the user as a surprise.

# Auto-Backup Task (Every Heartbeat)
- cd /home/ubuntu/.openclaw/workspace
- git add .
- If changes (git status --porcelain), commit with msg "Auto-backup [date]" and git push origin main
- Log success/failure to memory/YYYY-MM-DD.md