#!/usr/bin/env python3
"""
Analyze OpenClaw session logs to calculate token usage and cost by model.
"""

import os
import json
from datetime import datetime
from collections import defaultdict

def analyze_sessions(sessions_dir, target_date):
    """Analyze session files for a specific date."""
    
    model_stats = defaultdict(lambda: {
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0,
        'cost': 0.0,
        'requests': 0
    })
    
    if not os.path.exists(sessions_dir):
        print(f"Directory not found: {sessions_dir}")
        return model_stats
    
    for filename in os.listdir(sessions_dir):
        if not filename.endswith('.jsonl'):
            continue
        
        filepath = os.path.join(sessions_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        # Check if this is a message entry with usage data
                        if entry.get('type') == 'message':
                            message = entry.get('message', {})
                            usage = message.get('usage', {})
                            
                            # Get the model from the message
                            model = message.get('model', 'unknown')
                            
                            # Check the timestamp
                            timestamp = entry.get('timestamp', '')
                            if not timestamp.startswith(target_date):
                                continue
                            
                            # Add up the stats
                            stats = model_stats[model]
                            stats['input_tokens'] += usage.get('input', 0)
                            stats['output_tokens'] += usage.get('output', 0)
                            stats['total_tokens'] += usage.get('totalTokens', 0)
                            
                            # Get cost - it might be a dict or float
                            cost_data = usage.get('cost', {})
                            if isinstance(cost_data, dict):
                                stats['cost'] += cost_data.get('total', 0.0)
                            elif isinstance(cost_data, (int, float)):
                                stats['cost'] += cost_data
                            
                            stats['requests'] += 1
                            
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    return model_stats

def main():
    target_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Analyzing usage for: {target_date}")
    print("=" * 80)
    
    # Analyze main agent sessions
    sessions_dir = '/home/ubuntu/.openclaw/agents/main/sessions'
    model_stats = analyze_sessions(sessions_dir, target_date)
    
    # Also check lesson-planner if it exists
    lesson_planner_dir = '/home/ubuntu/.openclaw/agents/lesson-planner/sessions'
    if os.path.exists(lesson_planner_dir):
        lesson_stats = analyze_sessions(lesson_planner_dir, target_date)
        # Merge stats
        for model, stats in lesson_stats.items():
            model_stats[model]['input_tokens'] += stats['input_tokens']
            model_stats[model]['output_tokens'] += stats['output_tokens']
            model_stats[model]['total_tokens'] += stats['total_tokens']
            model_stats[model]['cost'] += stats['cost']
            model_stats[model]['requests'] += stats['requests']
    
    if not model_stats:
        print("No usage data found for today.")
        return
    
    # Print results
    print(f"{'Model':<45} {'Input':>10} {'Output':>10} {'Total':>12} {'Cost':>12} {'Requests':>10}")
    print("-" * 100)
    
    total_input = 0
    total_output = 0
    total_tokens = 0
    total_cost = 0.0
    total_requests = 0
    
    for model, stats in sorted(model_stats.items()):
        print(f"{model:<45} {stats['input_tokens']:>10,} {stats['output_tokens']:>10,} {stats['total_tokens']:>12,} ${stats['cost']:>11.6f} {stats['requests']:>10}")
        
        total_input += stats['input_tokens']
        total_output += stats['output_tokens']
        total_tokens += stats['total_tokens']
        total_cost += stats['cost']
        total_requests += stats['requests']
    
    print("-" * 100)
    print(f"{'TOTAL':<45} {total_input:>10,} {total_output:>10,} {total_tokens:>12,} ${total_cost:>11.6f} {total_requests:>10}")
    print("=" * 80)

if __name__ == '__main__':
    main()