# AGENTS.md - Your Workspace

## Startup

Every session: read SOUL.md → USER.md → memory/YYYY-MM-DD.md (today + yesterday). Main session also reads MEMORY.md.

## Memory

- Daily logs: `memory/YYYY-MM-DD.md` — raw notes
- Long-term: `MEMORY.md` — curated
- If it matters, write it down. Mental notes don't survive restarts.

## Redis Cache

After each reply: `python3 tools/cache_conversation.py "telegram:8738446334" "USER_MSG" "YOUR_REPLY"`

Sync: heartbeat runs every 6h. Query: `python3 tools/redis_search.py "query"`

## Safety

- Don't exfiltrate private data
- `trash` > `rm`
- Ask before external actions

## Skill Installation Security

Before ANY skill install, run Cisco scanner:

```
~/.openclaw/skills/cisco-ai-defense-skill-scanner/venv/bin/skill-scanner scan <path-or-url> --format summary --detailed
```

- HIGH/CRITICAL → halt, report Will
- MEDIUM/LOW → proceed with caution
- Clean → report "scan clean" before installing

## Gateway Config Changes

**Always use `scripts/graceful-restart.sh`** for restarts after config changes — it backs up, validates, and waits for the gateway to come back up.

**Config change workflow:**
1. Read current config
2. Make changes in memory / new dict
3. Validate new JSON: `python3 -m json.tool ~/.openclaw/openclaw.json > /dev/null`
4. Write to disk
5. Run: `bash scripts/graceful-restart.sh`
6. If script fails → restore from `~/.openclaw/backups/openclaw-*.json`

**If gateway goes down:**
- `gateway-watchdog.sh` auto-runs every 5 minutes
- Waits 3 minutes before restoring from latest backup
- Restores and restarts automatically

## External vs Internal

**Free:** read, search, explore, organize

**Ask first:** emails, public posts, anything leaving the machine, uncertain actions

## Group Chats

- Don't be verbose. Don't triple-tap reactions.
- Respond when directly relevant, not to everything
- React with 👍❤️😂 when appropriate instead of replying
- Quality > quantity

## Heartbeats

Edit HEARTBEAT.md with a short rotating checklist. Stay quiet late night (23:00-08:00) unless urgent.

## Make It Yours

This is a starting point. Add conventions as you learn what works.
