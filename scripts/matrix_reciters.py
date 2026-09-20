#!/usr/bin/env python3
import sys
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
RECITERS_FILE = os.path.join(REPO_DIR, 'audio', 'reciters.json')

with open(RECITERS_FILE, 'r', encoding='utf-8') as f:
    reciters = json.load(f)

all_ids = [r['id'] for r in reciters]

target = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else 'all'

if target.lower() == 'all':
    selected = all_ids
else:
    requested = [x.strip() for x in target.split(',') if x.strip()]
    selected = [rid for rid in requested if rid in all_ids]
    if not selected:
        selected = all_ids

print(f"Selected {len(selected)} reciters: {selected}")

github_output = os.environ.get('GITHUB_OUTPUT')
if github_output:
    with open(github_output, 'a') as f:
        f.write(f"reciters={json.dumps(selected)}\n")
else:
    print(f"reciters={json.dumps(selected)}")
