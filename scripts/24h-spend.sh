#!/bin/bash
set -euo pipefail
cd /home/ubuntu/.openclaw/workspace

mkdir -p spend/logs spend

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CUTOFF=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)

OUT="spend/24h-${NOW%T*}.md"
LOG="spend/logs/$(date +%Y-%m-%d_%H-%M-%S).log"

echo "=== 24h Spend Report ($NOW | cutoff: $CUTOFF) ===" > "$OUT"

# Find all jsonl sessions across agents
find /home/ubuntu/.openclaw/agents -name '*.jsonl' -not -name '*deleted*' -not -name '*reset*' -exec cat {} \; | \
jq -s --arg cutoff "$CUTOFF" '
  # Filter lines from last 24h
  def is_recent: (.[0].timestamp // empty) >= ($cutoff | fromdateiso8601);

  reduce .[] as $line ({}; 
    if $line.message and $line.message.usage and ($line | is_recent) then
      .[($line.cwd // "unknown") // "global"] += [
        {
          session: ($line.sessionId // "unknown"),
          ts: $line.timestamp,
          model: ($line.message.model // "unknown"),
          input: $line.message.usage.input // 0,
          output: $line.message.usage.completion_tokens // 0 | tonumber,
          total_tokens: $line.message.usage.total_tokens // 0 | tonumber,
          cost: ($line.message.usage.estimated_cost // 0) | tonumber
        }
      ]
    else . end
  ) |
  to_entries[] | 
  "Agent: \(.key)\n" +
  (.value | 
    group_by(.model) | 
    map({
      model: .[0].model,
      calls: length,
      total_input: (map(.input | tonumber) | add),
      total_output: (map(.output | tonumber) | add),
      total_tokens: (map(.total_tokens | tonumber) | add),
      total_cost: (map(.cost | tonumber) | add)
    } | 
    "\n  \(.model): $\(.total_cost | round(4)) USD (\(.total_tokens) tokens | \(.calls) calls | in:\(.total_input) out:\(.total_output))"
  )
' >> "$OUT"

# Grand total
TOTAL=$(jq -s --arg cutoff "$CUTOFF" '
reduce .[] as $line ({}; 
  if $line.message and $line.message.usage and (.[0].timestamp // empty) >= ($cutoff | fromdateiso8601) then
    .total_cost += ($line.message.usage.estimated_cost // 0 | tonumber)
  else . end
) | .total_cost | round(4)
' /home/ubuntu/.openclaw/agents/*/*.jsonl 2>/dev/null || echo 0)

echo "\n=== GRAND TOTAL (24h): \$$TOTAL USD ===" >> "$OUT"

git add spend/ && git commit -m "24h-spend $NOW (cutoff $CUTOFF)" && git push origin main || true

echo "Saved: $OUT (total: \$$TOTAL)" | tee "$LOG"
