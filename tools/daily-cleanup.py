#!/usr/bin/env python3
import re, glob, os
mem_dir = '../memory'
for fname in glob.glob(f'{mem_dir}/*.md'):
    with open(fname, 'r') as fh:
        content = fh.read()
    # Count and summarize duplicate sync lines
    sync_matches = re.findall(r'^Redis\+Qdrant sync: .*\n?', content, re.M)
    if len(sync_matches) > 5:
        summary = f'Redis+Qdrant synced {len(sync_matches)} times (summarized).\n'
        content = re.sub(r'(Redis\+Qdrant sync: .*\n){5,}', summary, content, 1)
        with open(fname, 'w') as fh:
            fh.write(content)
        print(f'Summarized {len(sync_matches)} sync lines in {fname}')
print('Daily cleanup complete.')
