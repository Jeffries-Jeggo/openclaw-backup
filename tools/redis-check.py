#!/usr/bin/env python3
import re
import subprocess
import sys

try:
    out = subprocess.check_output(['redis-cli', 'info', 'memory'], stderr=subprocess.DEVNULL).decode()
    match = re.search(r'^used_memory_human:\s*([\d.]+[MKGB]?)', out, re.MULTILINE)
    if match:
        val_str = match.group(1).strip()
        num_match = re.match(r'([\d.]+)', val_str)
        if num_match:
            num = float(num_match.group(1))
            unit = val_str[-1].upper() if len(val_str) > 1 and val_str[-1] in 'MKGB' else 'B'
            mult = {'B':1, 'K':1024, 'M':1048576, 'G':1073741824}.get(unit, 1)
            if num * mult > 100 * 1048576:
                print(f"WARN: Redis {val_str}")
except:
    pass  # Silent fail if redis down
