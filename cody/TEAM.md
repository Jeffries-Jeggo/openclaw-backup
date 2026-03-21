# TEAM.md - Locked Team Roles & Models
# Saved per user spec (output $0.5-3/M where applicable; alts free).
# Models: OpenRouter IDs. Prices/ctx approx (fluctuate).
# Usage: \"set up a team for [project]\" → spawn these as sub-agents.

manager:
  role: Manager
  model: openrouter/x-ai/grok-4.1-fast  # Me (Cody): Agentic/tools, planning. Ctx: 2M. $0.30/$1.50

roles:
  Coder:
    model: moonshotai/kimi-k2.5  # SWE-Bench top, visual coding. Ctx: 1M+. $0.25/$1.00
  DesignerUI:
    model: qwen/qwen3-vl-72b-instruct  # Free alt, UI sketches→code. Ctx: 128k. Free
  BackendDB:
    model: deepseek/deepseek-v3.2  # Backend logic. Ctx: 128k. $0.14/$0.28
  TesterQA:
    model: openrouter/x-ai/grok-4.1-fast  # Bug/test gen. Ctx: 2M. $0.30/$1.50
  Deployer:
    model: deepseek/deepseek-r1-distill-qwen-32b  # Free reasoning/scripts alt. Ctx: 128k. Free

# Defaults: mode=run, runTimeoutSeconds=300, cleanup=delete
# Tweak: \"change [role] to [model]\"