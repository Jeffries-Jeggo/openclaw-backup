#!/bin/bash
set -euo pipefail

echo "🍨 24h Spend Tracker - $(date '+%Y-%m-%d %H:%M %Z')"

cd /home/ubuntu/.openclaw/workspace

echo ""
echo "Recent session stats (use 📊 session_status for live):"
openclaw status 2>/dev/null | grep -E 'tokens|cost|cache|model' || echo "No detailed cost data in openclaw status."

echo ""
echo "Log recent costs to memory/YYYY-MM-DD.md for tracking."
echo "Total spend: Check billing dashboard or sum session costs."
