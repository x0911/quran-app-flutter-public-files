#!/usr/bin/env python3
"""
sync_catalog_sizes.py

Fetches the uploaded release assets from release v5.0.0,
updates audio/catalog.json with exact byte sizes,
and prints a progress report.
"""

import os
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
CATALOG_PATH = os.path.join(REPO_DIR, 'audio', 'catalog.json')

def main():
    print("Syncing audio/catalog.json with release v5.0.0 assets...")

    res = subprocess.run(
        ['gh', 'release', 'view', 'v5.0.0', '--json', 'assets'],
        cwd=REPO_DIR, capture_output=True, text=True, check=True
    )
    release_data = json.loads(res.stdout)
    assets = release_data.get('assets', [])

    asset_map = {a['name']: a['size'] for a in assets}
    print(f"Found {len(asset_map)} assets on release v5.0.0.")

    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    synced_count = 0
    for item in catalog:
        zip_name = item['zipFileName']
        if zip_name in asset_map:
            actual_size = asset_map[zip_name]
            item['compressedSizeBytes'] = actual_size
            synced_count += 1
            print(f"Synced {item['id']}: {actual_size / (1024*1024):.1f} MB")

    with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\nSuccessfully synced {synced_count}/{len(catalog)} reciters into {CATALOG_PATH}.")

if __name__ == '__main__':
    main()
