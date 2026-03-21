---
name: nutrition-tracker
description: Log meals from natural language and get nutrition tracking with charts. Searches USDA database (or built-in common foods), logs to local markdown files and Google Sheets. Evening summary with calorie progress bar, macro pie chart, and 7-day trend chart.
homepage: https://github.com/openclaw/skills
metadata:
  {
    openclaw:
      {
        emoji: "🍽️",
        requires:
          {
            bins: ["curl", "jq", "python3", "gog"],
            env: ["NUTRITION_SHEET_ID"],
            python_pkgs: ["matplotlib"],
          },
        primaryEnv: "NUTRITION_SHEET_ID",
      },
  }
---

# Nutrition Tracker

Track calories, protein, fat, and carbs from natural language meal descriptions.
Logs to `logs/food/YYYY-MM-DD.md` and Google Sheets. Evening summary with charts.

**Daily goal:** 2400 kcal

---

## Setup

### 1. Google Sheet

Create a Google Sheet with these column headers in Row 1:
```
Date | Meal | Food | Amount_g | Cals | Protein_g | Carbs_g | Fat_g
```

Share the sheet and set the env var:
```bash
export NUTRITION_SHEET_ID="your-sheet-id-here"
```

### 2. Install matplotlib (if not present)
```bash
pip3 install matplotlib --break-system-packages
```

---

## Core Commands

### Log a Meal

**Input:** Natural language like `"I had 200g chicken breast for lunch"`

**What to do:**
1. Run `nutrition_lookup.py` to get macros
2. Append to `logs/food/YYYY-MM-DD.md` (markdown table)
3. Append row to Google Sheets via `gog sheets append`
4. Reply with plain text confirmation

**Lookup script** (`skills/nutrition-tracker/nutrition_lookup.py`):
```bash
python3 skills/nutrition-tracker/nutrition_lookup.py "200g chicken breast"
python3 skills/nutrition-tracker/nutrition_lookup.py "beef noodles"          # uses built-in common foods
python3 skills/nutrition-tracker/nutrition_lookup.py "search:salmon"         # USDA API search
```

**Append to sheet:**
```bash
gog sheets append "$NUTRITION_SHEET_ID" "FoodLog!A:H" \
  --values-json '[["2026-03-20", "lunch", "Chicken Breast", "200", "1 serving", "240", "46", "0", "2"]]' \
  --insert INSERT_ROWS
```

### Evening Summary

**Input:** `"show me today's nutrition"` or `"evening summary"`

**What to do:**
1. Run `nutrition_charts.py` to generate charts
2. Read today's log from `logs/food/YYYY-MM-DD.md`
3. Reply with text summary + chart images

**Chart script** (`skills/nutrition-tracker/nutrition_charts.py`):
```bash
python3 skills/nutrition-tracker/nutrition_charts.py 2026-03-20
# Outputs:
#   logs/nutrition-cal-2026-03-20.png  — calorie progress bar
#   logs/nutrition-macro-2026-03-20.png — macro pie chart
#   logs/nutrition-trend-2026-03-20.png — 7-day calorie trend
```

### Weekly Trends

**Input:** `"show me this week's nutrition trends"`

Read last 7 days from `logs/food/` and generate trend charts.

---

## Log File Format

Path: `logs/food/YYYY-MM-DD.md`

```markdown
# YYYY-MM-DD Food Log

## Breakfast

| Item | Amount | Fat g | Protein g | Carbs g | Cals |
|------|--------|-------|-----------|---------|------|
| Greek yogurt | 100g | 4 | 10 | 4 | 97 |
| **Breakfast Total** | | **4** | **10** | **4** | **~97** |

## Lunch

...

## Daily Totals

| Fat g | Protein g | Carbs g | Cals |
|-------|-----------|---------|------|
| **XX** | **XX** | **XX** | **~XXXX** |
```

---

## Food Data Sources

| Source | Coverage | API Key |
|--------|----------|---------|
| Built-in common foods (Taiwanese/Chinese/generic) | ~30 items | None |
| USDA FoodData Central (Foundation + SR Legacy) | 300,000+ generic foods | `DEMO_KEY` (works) |

**Lookup priority:**
1. Built-in common foods (instant, no network)
2. USDA API search (requires network, ~10s)

---

## Reply Templates

### After logging a meal:
```
✅ Logged: 200g Chicken Breast (raw)
   Calories: 240 kcal
   Protein:  46.0g
   Carbs:    0.0g
   Fat:      2.0g
```

### Evening summary:
```
🍽️ Evening Summary — 2026-03-20

📊 Daily Totals
   Calories:  2,200 / 2,400 kcal  ████████████████████░░░░  92%
   Protein:   141g
   Fat:       78g
   Carbs:     310g

🕐 Last meal: Dinner @ 20:08

[Chart images: calorie bar → macro pie → 7-day trend]

💡 You hit 92% of your calorie goal today. Protein was strong at 141g.
```
