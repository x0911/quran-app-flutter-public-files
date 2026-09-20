#!/usr/bin/env python3
"""
prepare_audio_packs.py

Automates the download, maximum-compression zipping, and GitHub release upload
of all 42 Quran reciter audio packs to release v5.0.0 on x0911/quran-app-flutter-public-files.

Features:
- Resumable: checks existing assets on GitHub release v5.0.0 and skips already-uploaded packs.
- Disk-space safe: processes reciters one by one, deleting temp files & zip immediately after upload.
- Updates audio/catalog.json with exact byte sizes.
"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(REPO_DIR, 'audio')
CATALOG_PATH = os.path.join(AUDIO_DIR, 'catalog.json')
RECITERS_PATH = '/Users/dash/work/dr-raaef/quran-app-flutter/assets/reciters.json'
TEMP_WORK_DIR = os.path.join(REPO_DIR, 'temp_audio_work')

# EveryAyah folder names / mappings
EVERYAYAH_MAP = {
    'abdullah_basfar': 'Abdullah_Basfar_64kbps',
    'shatri': 'Abu_Bakr_Ash-Shaatree_128kbps',
    'alafasy': 'Alafasy_128kbps',
    'ghamdi': 'Ghamadi_40kbps',
    'ibrahim_walk': 'Ibrahim_Walk_192kbps_TEST',
    'hani_rifai': 'Hani_Rifai_192kbps',
    'husary_mujawwad': 'Husary_Mujawwad_64kbps',
    'hudhaify': 'Hudhaify_128kbps',
    'almuaiqly': 'Maher_AlMuaiqly_64kbps',
    'minsha_mujawwad': 'Minshawy_Mujawwad_64kbps',
    'tablawy': 'Mohammad_al_Tablaway_128kbps',
    'muhammad_ayyoub': 'Muhammad_Ayyoub_128kbps',
    'muhammad_jibreel': 'Muhammad_Jibreel_128kbps',
    'shuraym': 'Saood_ash-Shuraym_128kbps',
    'dussary': 'Yasser_Ad-Dussary_128kbps',
    'ayman_suwaid': 'Ayman_Sowaid_64kbps',
    'ibraheem_akhdar': 'Ibrahim_Akhdar_32kbps',
    'faras_abad': 'Fares_Abbad_64kbps',
    'ali_jabbar': 'Ali_Jaber_64kbps',
    'ahmed_bin_ali': 'ahmed_ibn_ali_al_ajamy_128kbps',
    'ibrahim_warsh': 'warsh/warsh_ibrahim_aldosary_128kbps',
    'Yasin-Al-Jazaery_warsh': 'warsh/warsh_yassin_al_jazaery_64kbps',
}

def get_uploaded_assets():
    try:
        res = subprocess.run(
            ['gh', 'release', 'view', 'v5.0.0', '--json', 'assets', '--jq', '.assets[].name'],
            cwd=REPO_DIR, capture_output=True, text=True, check=True
        )
        return set(res.stdout.strip().splitlines())
    except Exception as e:
        print(f"Warning getting release assets: {e}")
        return set()

def download_file(url, out_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp, open(out_path, 'wb') as f:
        shutil.copyfileobj(resp, f)

def download_surah_reciter(reciter_id, base_url, target_folder):
    os.makedirs(target_folder, exist_ok=True)
    urls = []
    for s in range(1, 115):
        s_str = f"{s:03d}.mp3"
        url = f"{base_url}{s_str}"
        out = os.path.join(target_folder, s_str)
        urls.append((url, out))

    def _dl(item):
        u, o = item
        if not os.path.exists(o) or os.path.getsize(o) == 0:
            download_file(u, o)

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(_dl, item) for item in urls]
        for f in as_completed(futures):
            f.result()

def build_and_upload_reciter(reciter, uploaded_assets):
    rid = reciter['id']
    zip_name = f"{rid}.zip"

    if zip_name in uploaded_assets:
        print(f"[{rid}] Already uploaded to v5.0.0. Skipping.")
        return True

    print(f"\n==========================================")
    print(f"Processing reciter: {rid} ({reciter['nameAr']})")
    print(f"==========================================")

    os.makedirs(TEMP_WORK_DIR, exist_ok=True)
    reciter_dir = os.path.join(TEMP_WORK_DIR, rid)
    final_zip = os.path.join(TEMP_WORK_DIR, zip_name)

    try:
        is_ayah = reciter.get('isAyahOnly', False)
        if not is_ayah:
            print(f"[{rid}] Downloading 114 Surahs from {reciter['baseUrl']}...")
            download_surah_reciter(rid, reciter['baseUrl'], reciter_dir)

            # Re-encode to 64kbps with ffmpeg to get minimum zip size (<1GB) and avoid GitHub upload limits
            print(f"[{rid}] Compressing 114 Surahs to 64kbps for lowest zip size...")
            def _compress_file(f):
                if f.endswith('.mp3'):
                    src = os.path.join(reciter_dir, f)
                    tmp_out = os.path.join(reciter_dir, f"cmp_{f}")
                    subprocess.run(['ffmpeg', '-i', src, '-b:a', '64k', '-y', tmp_out],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
                        os.replace(tmp_out, src)

            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(_compress_file, os.listdir(reciter_dir)))

            print(f"[{rid}] Creating zip at maximum compression...")
            with zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for f in sorted(os.listdir(reciter_dir)):
                    if f.endswith('.mp3'):
                        full = os.path.join(reciter_dir, f)
                        zf.write(full, arcname=f)
        else:
            folder = EVERYAYAH_MAP.get(rid, rid)
            if 'warsh' in folder:
                everyayah_zip = f"https://everyayah.com/data/{folder}/000_versebyverse.zip"
            else:
                everyayah_zip = f"https://everyayah.com/data/{folder}/000_versebyverse.zip"

            print(f"[{rid}] Fetching pre-packaged archive from EveryAyah: {everyayah_zip}")
            try:
                download_file(everyayah_zip, final_zip)
            except Exception as err:
                print(f"[{rid}] Direct zip failed ({err}). Downloading mirrored ayah files...")
                base_url = reciter['baseUrl']
                os.makedirs(reciter_dir, exist_ok=True)
                # Fallback per-surah download
                ayah_counts = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,
                               112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,
                               89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,
                               12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,
                               30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
                tasks = []
                for s_idx, count in enumerate(ayah_counts, start=1):
                    for a in range(1, count + 1):
                        fname = f"{s_idx:03d}{a:03d}.mp3"
                        u = f"{base_url}{fname}"
                        dst = os.path.join(reciter_dir, fname)
                        tasks.append((u, dst))
                def _dl(item):
                    u, dst = item
                    if not os.path.exists(dst) or os.path.getsize(dst) == 0:
                        download_file(u, dst)
                with ThreadPoolExecutor(max_workers=16) as ex:
                    list(ex.map(_dl, tasks))
                with zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                    for f in sorted(os.listdir(reciter_dir)):
                        if f.endswith('.mp3'):
                            zf.write(os.path.join(reciter_dir, f), arcname=f)

        zip_size = os.path.getsize(final_zip)
        print(f"[{rid}] Archive ready. Size: {zip_size / (1024*1024):.1f} MB ({zip_size} bytes)")

        print(f"[{rid}] Uploading to GitHub release v5.0.0...")
        subprocess.run(
            ['gh', 'release', 'upload', 'v5.0.0', final_zip, '--clobber'],
            cwd=REPO_DIR, check=True
        )
        print(f"[{rid}] Upload SUCCESS!")

        # Update catalog
        reciter['compressedSizeBytes'] = zip_size
        reciter['zipFileName'] = zip_name
        reciter['downloadUrl'] = f"https://github.com/x0911/quran-app-flutter-public-files/releases/download/v5.0.0/{zip_name}"

        return True
    except Exception as e:
        print(f"[{rid}] ERROR: {e}")
        return False
    finally:
        # Crucial: wipe temp directory to prevent disk exhaustion!
        if os.path.exists(reciter_dir):
            shutil.rmtree(reciter_dir, ignore_errors=True)
        if os.path.exists(final_zip):
            os.remove(final_zip)

def main():
    print("Starting Quran Audio Packs Builder for Release v5.0.0")
    uploaded = get_uploaded_assets()
    print(f"Currently uploaded assets on v5.0.0: {len(uploaded)}")

    with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    with open(RECITERS_PATH, 'r', encoding='utf-8') as f:
        full_reciters = json.load(f)
    base_url_map = {r['id']: r['baseUrl'] for r in full_reciters}

    # Process popular full-surah reciters first, then all remaining
    priority_order = [
        'husary', 'minshawi_murattal', 'sudais_murattal', 'qatami', 'abdul_basit_murattal',
        'abdul_basit_mujawwad', 'aziz_alili', 'salah_budair', 'sahl_yaseen', 'bandar_baleela',
        'mahmoud_ali_albana', 'abdulrahman_alshahat', 'abdurrashid_sufi', 'mostafa_ismaeel',
        'abdulaziz_zahrani', 'ahmad_nauina', 'akram_al_alaqmi', 'ali_hajjaj_alsouasi',
        'husary_iza3a', 'abdurrashid_sufi_shoba',
        # Ayah-only reciters
        'ghamdi', 'almuaiqly', 'shuraym', 'dussary', 'shatri', 'alafasy',
        'faras_abad', 'ali_jabbar', 'ibraheem_akhdar', 'Yasin-Al-Jazaery_warsh',
        'abdullah_basfar', 'hani_rifai', 'hudhaify', 'muhammad_jibreel',
        'muhammad_ayyoub', 'tablawy', 'ahmed_bin_ali', 'ayman_suwaid',
        'husary_mujawwad', 'minsha_mujawwad', 'ibrahim_walk', 'ibrahim_warsh'
    ]

    catalog_map = {r['id']: r for r in catalog}
    for rid, r in catalog_map.items():
        if rid in base_url_map:
            r['baseUrl'] = base_url_map[rid]

    ordered_list = [catalog_map[rid] for rid in priority_order if rid in catalog_map]

    success_count = 0
    for r in ordered_list:
        ok = build_and_upload_reciter(r, uploaded)
        if ok:
            success_count += 1
            # Save updated catalog (stripping baseUrl before writing to catalog.json)
            clean_catalog = []
            for item in catalog:
                copy_item = dict(item)
                copy_item.pop('baseUrl', None)
                clean_catalog.append(copy_item)
            with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(clean_catalog, f, ensure_ascii=False, indent=2)

    print(f"\nAll done! Processed {success_count}/{len(ordered_list)} reciters successfully.")

if __name__ == '__main__':
    main()
