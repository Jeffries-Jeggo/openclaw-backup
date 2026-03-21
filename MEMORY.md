# MEMORY.md - Long-Term Memory

_Learned lessons, important context, and things worth remembering across sessions._

## About will
- Timezone: Asia/Taipei
- Communicates via Telegram
- Uses multiple agents (main, samantha, evelyn, cody, health-tracker, lesson-planner)

## Key Preferences
- Best times: unclear, reaches out throughout the day
- Preferred channel: Telegram

## System Setup
- OpenClaw workspace: /home/ubuntu/.openclaw/workspace
- Gateway runs as systemd service
- Redis used for session memory acceleration
- Qdrant available for vector memory (optional)
- Daily heartbeat tasks: 24h-spend tracking, auto-backup, Redis+Qdrant sync

## Lessons Learned

### 2026-03-07
- Installed AgentGuard skill for prompt injection/command detection

### 2026-03-20
- Migrated default model provider from OpenRouter to MiniMax (M2.7)
- Updated all agents (main, samantha, evelyn, cody, health-tracker, lesson-planner) to use minimax/MiniMax-M2.7
- Updated heartbeat model to minimax/MiniMax-M2.7
- MiniMax API key stored as MINIMAX_API_KEY env var
- Provider: minimax, baseUrl: https://api.minimax.io/anthropic, api: anthropic-messages

## Archived
_Old verbose entries condensed and moved here_

### (pre-2026-03-20)
- Workspace bootstrap, AgentGuard install, Qdrant docker setup notes — all moved to daily memory files
- OpenClaw gateway Telegram groupPolicy warnings (resolved)
- Docker permission fix for Qdrant

_Review and update this file regularly via heartbeat memory maintenance._
### 2026-03-21
- WhatsApp gateway connected at 03:58:21 GMT+8.
### 2026-03-21
- WhatsApp gateway connected at 06:43:20 GMT+8.
### 2026-03-21
- WhatsApp gateway connected at 06:43:20 GMT+8.
