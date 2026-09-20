#!/usr/bin/env python3
"""
build_single_pack.py

Downloads, optimizes, zips, and uploads a single reciter audio pack
to release v5.0.0 on GitHub.
"""

import sys
import os
import json
import subprocess
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
RECITERS_FILE = os.path.join(REPO_DIR, 'audio', 'reciters.json')
WORK_DIR = os.path.join(REPO_DIR, 'work_audio')

EVERYAYAH_MAP = {
    'abdullah_basfar': 'Abdullah_Basfar_64kbps',
    'shatri': 'Abu_Bakr_Ash-Shaatree_128kbps',
    'alafasy': 'Alafasy_128kbps',
    'ghamdi': 'Ghamadi_40kbps',
    'ibrahim_walk': 'Ibrahim_Walk_192kbps_TEST',
    'hani_rifai': 'Hani_Rifai_64kbps',
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

def download_file(url, out_path):
    cmd = [
        'curl', '-sSL',
        '--retry', '5',
        '--retry-delay', '2',
        '--connect-timeout', '30',
        '-A', 'Mozilla/5.0',
        '-o', out_path,
        url
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"curl download failed for {url}: {res.stderr.decode()}")

def download_surah_reciter(base_url, target_folder):
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

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(_dl, item) for item in urls]
        for f in as_completed(futures):
            f.result()

def main():
    if len(sys.argv) < 2:
        print("Usage: build_single_pack.py <reciter_id>")
        sys.exit(1)

    reciter_id = sys.argv[1].strip()
    with open(RECITERS_FILE, 'r', encoding='utf-8') as f:
        reciters = json.load(f)

    reciter = next((r for r in reciters if r['id'] == reciter_id), None)
    if not reciter:
        print(f"Error: Reciter '{reciter_id}' not found in {RECITERS_FILE}")
        sys.exit(1)

    zip_name = f"{reciter_id}.zip"
    print(f"==================================================")
    print(f"Starting build for: {reciter_id} ({reciter['nameAr']})")
    print(f"==================================================")

    os.makedirs(WORK_DIR, exist_ok=True)
    reciter_dir = os.path.join(WORK_DIR, reciter_id)
    final_zip = os.path.join(WORK_DIR, zip_name)

    try:
        is_ayah = reciter.get('isAyahOnly', False)
        if not is_ayah:
            print(f"[{reciter_id}] Downloading 114 Surahs from {reciter['baseUrl']}...")
            download_surah_reciter(reciter['baseUrl'], reciter_dir)

            print(f"[{reciter_id}] Re-encoding 114 Surahs to 64kbps for maximum compression (<1GB)...")
            def _compress(f):
                if f.endswith('.mp3'):
                    src = os.path.join(reciter_dir, f)
                    tmp_out = os.path.join(reciter_dir, f"cmp_{f}")
                    subprocess.run(
                        ['ffmpeg', '-i', src, '-b:a', '64k', '-y', tmp_out],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
                        os.replace(tmp_out, src)

            with ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(_compress, os.listdir(reciter_dir)))

            print(f"[{reciter_id}] Packaging into {zip_name} with DEFLATE level 9...")
            with zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for f in sorted(os.listdir(reciter_dir)):
                    if f.endswith('.mp3'):
                        full = os.path.join(reciter_dir, f)
                        zf.write(full, arcname=f)
        else:
            folder = EVERYAYAH_MAP.get(reciter_id, reciter_id)
            everyayah_zip = f"https://everyayah.com/data/{folder}/000_versebyverse.zip"
            print(f"[{reciter_id}] Fetching EveryAyah archive: {everyayah_zip}...")
            try:
                download_file(everyayah_zip, final_zip)
            except Exception as err:
                print(f"[{reciter_id}] Direct zip download failed ({err}). Downloading per-ayah files...")
                os.makedirs(reciter_dir, exist_ok=True)
                base_url = reciter['baseUrl']
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

            # Safety check: ensure file is under 2 GiB (2147483648 bytes)
            zip_size = os.path.getsize(final_zip)
            if zip_size >= 2100000000:
                print(f"[{reciter_id}] Warning: Archive size ({zip_size} bytes) close to 2GB limit. Re-compressing...")
                extract_tmp = os.path.join(WORK_DIR, 'recompress_tmp')
                os.makedirs(extract_tmp, exist_ok=True)
                with zipfile.ZipFile(final_zip, 'r') as zr:
                    zr.extractall(extract_tmp)
                os.remove(final_zip)
                # Re-encode to 64k if larger
                def _compress_ayah(f):
                    if f.endswith('.mp3'):
                        src = os.path.join(extract_tmp, f)
                        tmp_out = os.path.join(extract_tmp, f"cmp_{f}")
                        subprocess.run(
                            ['ffmpeg', '-i', src, '-b:a', '64k', '-y', tmp_out],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                        if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
                            os.replace(tmp_out, src)
                with ThreadPoolExecutor(max_workers=8) as ex:
                    list(ex.map(_compress_ayah, os.listdir(extract_tmp)))
                with zipfile.ZipFile(final_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                    for f in sorted(os.listdir(extract_tmp)):
                        if f.endswith('.mp3'):
                            zf.write(os.path.join(extract_tmp, f), arcname=f)
                shutil.rmtree(extract_tmp, ignore_errors=True)

        final_size = os.path.getsize(final_zip)
        print(f"[{reciter_id}] Archive finalized: {final_size / (1024*1024):.1f} MB ({final_size} bytes)")

        print(f"[{reciter_id}] Uploading {zip_name} to GitHub release v5.0.0...")
        subprocess.run(
            ['gh', 'release', 'upload', 'v5.0.0', final_zip, '--clobber'],
            cwd=REPO_DIR, check=True
        )
        print(f"[{reciter_id}] Successfully uploaded {zip_name}!")

    finally:
        if os.path.exists(reciter_dir):
            shutil.rmtree(reciter_dir, ignore_errors=True)
        if os.path.exists(final_zip):
            os.remove(final_zip)

if __name__ == '__main__':
    main()
