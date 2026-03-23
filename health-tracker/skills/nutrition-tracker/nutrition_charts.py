#!/usr/bin/env python3
"""
nutrition_charts.py — Generate daily nutrition charts for evening summary.
Reads from logs/food/YYYY-MM-DD.md and produces:
  1. Calorie progress bar chart
  2. Macro pie chart
  3. Daily trend (if multiple days available)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import os
import re
from datetime import datetime, timedelta

LOG_DIR = "logs/food"
OUT_DIR = "logs"
GOALS = {'cal': 2200}

def parse_daily_log(date_str):
    """Parse a food log markdown file and return totals."""
    path = f"{LOG_DIR}/{date_str}.md"
    if not os.path.exists(path):
        return None
    with open(path) as f:
        content = f.read()
    totals = {'cals': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
    idx = content.find('Daily Totals')
    if idx >= 0:
        section = content[idx:idx+300]
        nums = re.findall(r'\*\*~?(\d+(?:\.\d+)?)\*\*', section)
        if len(nums) >= 4:
            totals['fat'] = float(nums[0])
            totals['protein'] = float(nums[1])
            totals['carbs'] = float(nums[2])
            totals['cals'] = float(nums[3])
    return totals

def make_progress_chart(totals, date_str):
    """Horizontal bar showing calories consumed vs goal."""
    fig, ax = plt.subplots(figsize=(9, 3))
    consumed = totals['cals']
    goal = GOALS['cal']
    remaining = max(0, goal - consumed)
    pct = min(consumed / goal * 100, 100)
    color = '#4CAF50' if consumed <= goal else '#ef5350'
    ax.barh('Calories', consumed, color=color, label=f'Consumed: {consumed:.0f} kcal')
    if remaining > 0:
        ax.barh('Calories', remaining, left=consumed, color='#e0e0e0', label=f'Remaining: {remaining:.0f} kcal')
    ax.axvline(goal, color='red', linestyle='--', linewidth=1.5)
    ax.text(goal + 20, 0, f'Goal: {goal}', va='center', fontsize=9, color='red')
    ax.set_xlim(0, goal * 1.35)
    ax.set_xlabel('kcal')
    ax.set_title(f'Daily Calories — {date_str} ({pct:.0f}% of goal)', fontsize=12)
    ax.legend(loc='lower right')
    plt.tight_layout()
    out = f"{OUT_DIR}/nutrition-cal-{date_str}.png"
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    return out

def make_macro_pie(totals, date_str):
    """Pie chart of macro calorie distribution."""
    fat_cals = totals['fat'] * 9
    protein_cals = totals['protein'] * 4
    carbs_cals = totals['carbs'] * 4
    total = fat_cals + protein_cals + carbs_cals
    if total == 0:
        return None
    fig, ax = plt.subplots(figsize=(6, 6))
    macros = [fat_cals, protein_cals, carbs_cals]
    labels = [f'Fat\n{totals["fat"]:.0f}g ({fat_cals:.0f} kcal)',
              f'Protein\n{totals["protein"]:.0f}g ({protein_cals:.0f} kcal)',
              f'Carbs\n{totals["carbs"]:.0f}g ({carbs_cals:.0f} kcal)']
    colors = ['#FF6B6B', '#4ECDC4', '#FFE66D']
    wedges, texts, autotexts = ax.pie(macros, labels=labels, colors=colors,
                                       autopct='%1.0f%%', startangle=90,
                                       textprops={'fontsize': 11})
    ax.set_title(f'Macro Distribution — {date_str}', fontsize=12)
    plt.tight_layout()
    out = f"{OUT_DIR}/nutrition-macro-{date_str}.png"
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    return out

def make_trend_chart(dates_range, date_str):
    """Line chart of calorie trend over the past N days."""
    fig, ax = plt.subplots(figsize=(9, 3))
    labels, cals_vals, protein_vals = [], [], []
    for d in dates_range:
        t = parse_daily_log(d)
        if t:
            labels.append(d[-5:])  # MM-DD
            cals_vals.append(t['cals'])
            protein_vals.append(t['protein'])
    if not labels:
        return None
    ax.plot(labels, cals_vals, 'o-', color='#4CAF50', linewidth=2, markersize=6, label='Calories')
    ax.axhline(GOALS['cal'], color='red', linestyle='--', label=f'Goal: {GOALS["cal"]}')
    ax.set_xlabel('Date')
    ax.set_ylabel('kcal')
    ax.set_title('Calorie Trend (last 7 days)', fontsize=12)
    ax.legend()
    plt.tight_layout()
    out = f"{OUT_DIR}/nutrition-trend-{date_str}.png"
    plt.savefig(out, dpi=130, bbox_inches='tight')
    plt.close()
    return out

if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    totals = parse_daily_log(date)
    if not totals:
        print(f"No log found for {date}")
        sys.exit(1)
    print(f"Parsed totals: {totals}")
    cal_chart = make_progress_chart(totals, date)
    macro_chart = make_macro_pie(totals, date)
    # 7-day trend
    dates = [(datetime.strptime(date, '%Y-%m-%d') - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    trend_chart = make_trend_chart(dates, date)
    print(f"Charts: {cal_chart} {macro_chart} {trend_chart}")
