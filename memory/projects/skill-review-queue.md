# Skill Review Queue — Long-Term Self-Improvement

Started: 2026-03-24

## Methodology (dresden_k template)
1. Autonomous research overnight
2. Morning briefing with findings
3. Human decides what to build
4. Jeffries writes Claude Code prompt if needed
5. Test off-production before deploying

## Active Crons
- **11 PM**: Nightly Skill Reviewer — reviews 1 skill/night, reports to Will
- **3 AM**: dresden_k Research — scans r/openclaw for memory/skill innovations

## Skill Review Queue (in order)
1. ✅ xiaowenzhou/active-maintenance — "Automated system health and memory metabolism for OpenClaw"
   - Today: 2026-03-24
   - Status: pending review (runs tonight at 23:00)

## Security Protocol
- ALL skills assume insecure until proven otherwise
- **Cisco skill-scanner installed** at: `~/.openclaw/skills/cisco-ai-defense-skill-scanner/venv/bin/skill-scanner`
  - Run before ANY skill install: `skill-scanner scan <path-or-url> --output-format pretty`
  - HIGH/CRITICAL → do not install, report immediately
  - MEDIUM/LOW → proceed with caution, report findings
  - Clean → report "scan clean" before installing
- Check VirusTotal reports on ClawHub skill pages
- Never auto-install; always report first
- Flag: exec calls, credential handling, prompt injection, network exfiltration
- If in doubt, SKIP

## Memory Improvement Framework (from 5-layer Reddit post)
Target layers to build:
1. Structured facts database (SQLite entities/relationships)
2. Vector memory (ChromaDB or Qdrant — currently offline)
3. Episodic memory (importance-ranked events)
4. Procedural memory (what worked/didn't + effectiveness tracking)
5. Graph memory (entity relationships)
6. Memory decay system (full → summary → essence → hash)

## Current gaps in jeffries
- No structured facts store
- Qdrant offline (vector search unavailable)
- No episodic layer (importance weighting)
- No graph memory
- No memory decay/compression

## Ideas to Evaluate
- active-maintenance skill (memory metabolism)
- facts.db SQLite layer (structured storage)
- lossless-claw (LCM context engine)
- continuity plugin (cross-session memory)
- metabolism plugin (fact extraction)
