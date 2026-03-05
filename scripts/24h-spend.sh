#!/bin/bash
set -euo pipefail
cd /home/ubuntu/.openclaw/workspace

mkdir -p spend/logs spend

NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CUTOFF=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)

OUT="spend/24h-${NOW%T*}.md"
LOG="spend/logs/$(date +%Y-%m-%d_%H-%M-%S).log"

echo "=== 24h Spend Report ($NOW | cutoff: $CUTOFF) ===" > "$OUT"

# Sum ALL recent usage first (grand total)
jq -s --arg cutoff "$CUTOFF" '
def is_recent(line): (line.timestamp? | fromdateiso8601 // 0) >= ($cutoff | fromdateiso8601);

[.[]
  | select(.message? and .message.usage? and (is_recent(.)))
  | .message.usage.estimated_cost // 0
] | add | round(4)
' $(find /home/ubuntu/.openclaw/agents -name '*.jsonl' -not -name '*deleted*' -not -name '*reset*' -print) 2>/dev/null || echo "0.0000" >> "$OUT"

echo "\nGrand Total (24h): \$"$(jq -s --arg cutoff "$CUTOFF' $(find /home/ubuntu/.openclaw/agents -name '*.jsonl' -not -name '*deleted*' -not -name '*reset*' -print) 2>/dev/null || echo 0)".0000 USD" >> "$OUT"

# Per-agent/model summary
find /home/ubuntu/.openclaw/agents -name '*.jsonl' -not -name '*deleted*' -not -name '*reset*' | while read file; do
  agent=$(dirname "$file" | xargs basename)
  jq -s --arg cutoff "$CUTOFF" --arg agent "$agent" '
    def is_recent(line): (line.timestamp? | fromdateiso8601 // 0) >= ($cutoff | fromdateiso8601);
    group_by(.cwd? // "unknown") | .[] | select(.[0].cwd? | endswith("/$agent") or test("$agent"; "i"))
    | [ .[]
      | select(.message? and .message.usage? and (is_recent(.)))
      | {model: (.message.model // "unknown"), cost: (.message.usage.estimated_cost // 0 | tonumber), tokens: (.message.usage.total_tokens // 0 | tonumber)}
    ] | group_by(.model) | map({
      model: .[0].model,
      calls: length,
      total_cost: (map(.cost) | add | round(4)),
      total_tokens: (map(.tokens) | add)
    }) | "  \(.model): $\(.total_cost) (\(.total_tokens) tokens, \(.calls) calls)"
  ' "$file" >> "$OUT"
done

echo "\n(Per-agent/model above; 0s from config override - parse real estimated_cost)" >> "$OUT"

git add spend/ && git commit -m "24h-spend $NOW (all agents)" && git push origin main || true

echo "Saved: $OUT" | tee "$LOG"
