#!/usr/bin/env python3
"""
nutrition_lookup.py — Search food and return nutrition data per 100g
Sources: USDA (primary), hardcoded common foods (fallback)
"""
import sys
import json
import re
import subprocess
import argparse

USDA_API_KEY = "DEMO_KEY"
USDA_BASE = "https://api.nal.usda.gov/fdc/v1"

# Hardcoded common foods (per 100g) — fallback when API fails
COMMON_FOODS = {
    # Taiwanese / Chinese foods
    "lu rou fan": {"name": "Lu Rou Fan (Braised Pork Rice)", "cals": 250, "protein": 12, "carbs": 30, "fat": 10},
    "beef noodles": {"name": "Beef Noodles", "cals": 150, "protein": 10, "carbs": 20, "fat": 4},
    "bubble tea": {"name": "Bubble Tea (full sugar)", "cals": 85, "protein": 2, "carbs": 18, "fat": 1.5},
    "tapioca pearls": {"name": "Tapioca Pearls (boba)", "cals": 130, "protein": 0, "carbs": 32, "fat": 0},
    "cong zha bing": {"name": "Cong Zha Bing (Scallion Pancake)", "cals": 280, "protein": 6, "carbs": 35, "fat": 14},
    "gua bao": {"name": "Gua Bao (Steamed Pork Bun)", "cals": 220, "protein": 8, "carbs": 28, "fat": 9},
    "fried rice": {"name": "Fried Rice", "cals": 180, "protein": 5, "carbs": 25, "fat": 7},
    "xiao long bao": {"name": "Xiao Long Bao", "cals": 220, "protein": 9, "carbs": 24, "fat": 10},
    "soy milk": {"name": "Soy Milk", "cals": 45, "protein": 3.5, "carbs": 3, "fat": 1.8},
    "turnip cake": {"name": "Turnip Cake", "cals": 160, "protein": 3, "carbs": 25, "fat": 6},
    "shrimp rolls": {"name": "Shrimp Rolls", "cals": 200, "protein": 12, "carbs": 20, "fat": 8},
    "ba wan": {"name": "Ba Wan (Taiwanese Meatball)", "cals": 180, "protein": 9, "carbs": 18, "fat": 8},
    # Generic common foods
    "chicken breast": {"name": "Chicken Breast, raw", "cals": 120, "protein": 23, "carbs": 0, "fat": 1},
    "rice": {"name": "White Rice (cooked)", "cals": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
    "egg": {"name": "Whole Egg", "cals": 155, "protein": 13, "carbs": 1.1, "fat": 11},
    "banana": {"name": "Banana", "cals": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    "milk": {"name": "Whole Milk", "cals": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3},
    "bread": {"name": "White Bread", "cals": 265, "protein": 9, "carbs": 49, "fat": 3.2},
    "broccoli": {"name": "Broccoli", "cals": 34, "protein": 2.8, "carbs": 7, "fat": 0.4},
    "salmon": {"name": "Salmon, raw", "cals": 208, "protein": 20, "carbs": 0, "fat": 13},
    "oatmeal": {"name": "Oatmeal (cooked)", "cals": 68, "protein": 2.4, "carbs": 12, "fat": 1.4},
    "greek yogurt": {"name": "Greek Yogurt, plain", "cals": 97, "protein": 9, "carbs": 4, "fat": 5},
    "almonds": {"name": "Almonds", "cals": 579, "protein": 21, "carbs": 22, "fat": 50},
    "avocado": {"name": "Avocado", "cals": 160, "protein": 2, "carbs": 9, "fat": 15},
    "sweet potato": {"name": "Sweet Potato", "cals": 86, "protein": 1.6, "carbs": 20, "fat": 0.1},
    "potato": {"name": "Potato", "cals": 77, "protein": 2, "carbs": 17, "fat": 0.1},
    "pasta": {"name": "Pasta (cooked)", "cals": 131, "protein": 5, "carbs": 25, "fat": 1.1},
    "beef": {"name": "Beef, raw", "cals": 250, "protein": 26, "carbs": 0, "fat": 15},
    "pork": {"name": "Pork, raw", "cals": 242, "protein": 27, "carbs": 0, "fat": 14},
    "tofu": {"name": "Tofu (firm)", "cals": 144, "protein": 17, "carbs": 3, "fat": 9},
}


def usda_search(query, page_size=5):
    """Search USDA food database. Returns list of dicts with name + macros per 100g."""
    url = f"{USDA_BASE}/search"
    params = {
        "query": query,
        "pageSize": page_size,
        "dataType": "Foundation,SR Legacy",
        "api_key": USDA_API_KEY,
    }
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "10",
             f"{url}?query={query}&pageSize={page_size}&dataType=Foundation,SR Legacy&api_key={USDA_API_KEY}"],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        foods = []
        for food in data.get("foods", [])[:page_size]:
            macros = {"cals": None, "protein": None, "carbs": None, "fat": None}
            for n in food.get("foodNutrients", []):
                nid = str(n.get("nutrientId", ""))
                val = n.get("value")
                if nid == "2047":
                    macros["cals"] = val  # Energy Atwater
                elif nid == "1003":
                    macros["protein"] = val
                elif nid == "1004":
                    macros["fat"] = val
                elif nid == "1005":
                    macros["carbs"] = val
            # Skip if no macros found
            if any(v is not None for v in macros.values()):
                foods.append({
                    "name": food.get("description", "Unknown"),
                    "cals": macros["cals"] or 0,
                    "protein": macros["protein"] or 0,
                    "carbs": macros["carbs"] or 0,
                    "fat": macros["fat"] or 0,
                })
        return foods
    except Exception as e:
        return []


def parse_meal(user_input):
    """Parse natural language meal: '200g chicken breast' or 'chicken breast 200g'"""
    user_input = user_input.strip().lower()
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(g|gram|grams|kg|ml|l)\s+(.+)',
        r'(.+?)\s+(\d+(?:\.\d+)?)\s*(g|gram|grams|kg|ml|l)\b',
        r'(\d+(?:\.\d+)?)\s*(cups?|cup|tbsp|tsp|pieces?|slices?|bowls?|medium|large|small|handful)s?\s+(.+)',
        r'(.+?)\s+(\d+(?:\.\d+)?)\s*(cups?|cup|tbsp|tsp|pieces?|slices?|bowls?|medium|large|small|handful)\b',
    ]
    unit_map_g = {
        'g': 1, 'gram': 1, 'grams': 1, 'kg': 1000, 'ml': 1, 'l': 1000,
        'cups': 240, 'cup': 240, 'tbsp': 15, 'tsp': 5,
        'medium': 120, 'large': 150, 'small': 80, 'handful': 30,
        'pieces': 40, 'piece': 40, 'slices': 30, 'slice': 30, 'bowls': 300, 'bowl': 300,
    }
    for p in patterns:
        m = re.search(p, user_input, re.I)
        if m:
            amount = float(m.group(1))
            unit = m.group(2 if len(m.groups()) == 3 else 2).lower()
            food = (m.group(3) if len(m.groups()) == 3 else m.group(1)).strip()
            g = amount * unit_map_g.get(unit, 100)
            return food, int(g)
    return user_input, 100  # default 100g


def scale_macros(food_per_100g, amount_g):
    """Scale macros from per-100g to actual amount."""
    factor = amount_g / 100.0
    return {
        "name": food_per_100g["name"],
        "cals": round(food_per_100g.get("cals", 0) * factor, 1),
        "protein": round(food_per_100g.get("protein", 0) * factor, 1),
        "carbs": round(food_per_100g.get("carbs", 0) * factor, 1),
        "fat": round(food_per_100g.get("fat", 0) * factor, 1),
        "amount_g": amount_g,
    }


def find_food(query):
    """Find food: check common foods first, then USDA."""
    query_lower = query.lower()
    # Check common foods (partial match)
    for key, food in COMMON_FOODS.items():
        if key in query_lower or query_lower in key:
            return food
    # Search USDA
    results = usda_search(query)
    if results:
        return results[0]
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nutrition lookup")
    parser.add_argument("food", help="Food name or 'search:query'")
    parser.add_argument("--amount", "-a", type=int, default=100, help="Amount in grams")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    food_name, amount = parse_meal(args.food) if not args.food.startswith("search:") else (args.food[7:], args.amount)
    food_per_100g = find_food(food_name)
    if food_per_100g:
        result = scale_macros(food_per_100g, amount)
        if args.json:
            print(json.dumps(result))
        else:
            print(f"{result['name']} ({amount}g)")
            print(f"  Calories: {result['cals']} kcal")
            print(f"  Protein:  {result['protein']}g")
            print(f"  Carbs:    {result['carbs']}g")
            print(f"  Fat:      {result['fat']}g")
    else:
        print("Food not found", file=sys.stderr)
        sys.exit(1)
