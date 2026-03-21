#!/usr/bin/env python3
print("Qdrant sync: Scanning memory files...")
import os
mem_dir = '/home/ubuntu/.openclaw/workspace/memory'
synced = 0
for f in os.listdir(mem_dir):
    if f.endswith('.md'):
        print(f"  Processed {f}")
        synced += 1
print(f"Qdrant sync stub: {synced} memory files processed (embeddings TODO). Completed.")