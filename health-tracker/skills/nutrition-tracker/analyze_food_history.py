#!/usr/bin/env python3
"""
analyze_food_history.py — Scan food logs and find commonly eaten items
that should be added to the built-in nutrition list.
"""
import os, re, sys
from collections import defaultdict
from datetime import datetime, timedelta

LOG_DIR = "logs/food"

BUILTIN_FOODS = {
    "lu rou fan", "beef noodles", "bubble tea", "tapioca pearls",
    "cong zha bing", "gua bao", "fried rice", "xiao long bao",
    "soy milk", "turnip cake", "shrimp rolls", "ba wan",
    "chicken breast", "rice", "egg", "banana", "milk", "bread",
    "broccoli", "salmon", "oatmeal", "greek yogurt", "almonds",
    "avocado", "sweet potato", "potato", "pasta", "beef", "pork", "tofu",
}

def is_separator(line):
    s = line.strip()
    if not (s.startswith('|') and s.endswith('|')):
        return False
    inner = s[1:-1].replace('|', '').replace(' ', '')
    return len(inner) > 0 and all(c == '-' for c in inner)

SKIP = {'fat','protein','carbs','cals','calories','meal','item','amount',
        'notes','total','breakfast','lunch','dinner','snack',
        'fat g','protein g','carbs g','cal','kcal'}

def extract(date_str):
    path = f"{LOG_DIR}/{date_str}.md"
    if not os.path.exists(path):
        return []
    with open(path) as f:
        content = f.read()
    foods = []
    for line in content.split('\n'):
        if is_separator(line) or not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.split('|')[1:-1]]
        if len(cols) < 2:
            continue
        item = cols[0].lower()
        if not item or item in SKIP or 'total' in item or 'daily' in item:
            continue
        # Skip purely numeric, dashed, or bold-number cells like **14**
        if re.match(r'^[\d.\-]+$', item) or re.match(r'^\*+[\d.]+\*+$', item):
            continue
        # Remove amount suffixes: "100g", "2 large", "chicken breast 200g"
        clean = re.sub(r'\d+\s*(?:g|ml|kg|cups?|tbsp|tsp|medium|large|small|bowls?|serving)?\s*', '', item, flags=re.I)
        clean = re.sub(r'[~()\[\]]+', '', clean).strip(' -_')
        if clean and len(clean) > 2 and clean not in SKIP:
            foods.append(clean)
    return foods

def analyze(days=30):
    today = datetime.now()
    freq = defaultdict(lambda: {"count": 0, "dates": []})
    for i in range(days):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        seen = set()
        for food in extract(date):
            if food not in seen:
                freq[food]["count"] += 1
                freq[food]["dates"].append(date)
                seen.add(food)
    return freq

def get_candidates(min_count=2, days=30):
    return sorted(
        [(f, v["count"], v["dates"]) for f, v in analyze(days).items()
         if f not in BUILTIN_FOODS and v["count"] >= min_count],
        key=lambda x: (-x[1], x[0])
    )

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    min_count = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    candidates = get_candidates(min_count, days)
    if candidates:
        print(f"=== Food History ({days} days, min {min_count}x) ===")
        for food, count, dates in candidates:
            print(f'  - "{food}" ({count}x: {", ".join(dates)})')
        print(f"\n{len(candidates)} candidate(s) found. Edit nutrition_lookup.py COMMON_FOODS to add.")
    else:
        print(f"No new foods found (>= {min_count}x in {days} days). Keep logging!")
