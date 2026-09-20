#!/usr/bin/env python3
"""
test_ogg_conversion.py

Experiments with converting Quran audio (e.g. Surah Al-Baqara) from MP3 to OGG (Opus)
to compare file size and acoustic quality.
Uploads the resulting sample files directly to GitHub Release v5.0.0.
"""

import sys
import os
import json
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
RECITERS_FILE = os.path.join(REPO_DIR, 'audio', 'reciters.json')
WORK_DIR = os.path.join(REPO_DIR, 'work_experiment')

def download_file(url, out_path):
    cmd = [
        'curl', '-sSLf',
        '--retry', '5',
        '--retry-delay', '2',
        '--connect-timeout', '30',
        '-A', 'Mozilla/5.0',
        '-o', out_path,
        url
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        if os.path.exists(out_path):
            os.remove(out_path)
        raise RuntimeError(f"curl download failed for {url}: {res.stderr.decode()}")

def main():
    reciter_id = sys.argv[1].strip() if len(sys.argv) > 1 else 'minshawi_murattal'
    surah_str = sys.argv[2].strip() if len(sys.argv) > 2 else '002'

    with open(RECITERS_FILE, 'r', encoding='utf-8') as f:
        reciters = json.load(f)

    reciter = next((r for r in reciters if r['id'] == reciter_id), None)
    if not reciter:
        print(f"Error: Reciter '{reciter_id}' not found in {RECITERS_FILE}")
        sys.exit(1)

    print(f"==================================================")
    print(f"Audio Codec Experiment: MP3 vs OGG (Opus)")
    print(f"Reciter: {reciter_id} ({reciter['nameAr']} / {reciter['nameEn']})")
    print(f"Surah: {surah_str} (Al-Baqara)")
    print(f"==================================================")

    os.makedirs(WORK_DIR, exist_ok=True)
    source_url = f"{reciter['baseUrl']}{surah_str}.mp3"
    raw_mp3 = os.path.join(WORK_DIR, f"raw_{surah_str}.mp3")

    print(f"Downloading source audio from {source_url}...")
    download_file(source_url, raw_mp3)
    raw_size = os.path.getsize(raw_mp3)
    print(f"Source file downloaded: {raw_size / (1024*1024):.2f} MB ({raw_size} bytes)")

    # 1. Standard 64kbps MP3 (current app standard)
    mp3_64k = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}_64k.mp3")
    print("Generating 64kbps MP3 (current app standard)...")
    subprocess.run(
        ['ffmpeg', '-i', raw_mp3, '-b:a', '64k', '-y', mp3_64k],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    mp3_64k_size = os.path.getsize(mp3_64k)

    # 2. 32kbps OGG (Opus codec, high vocal clarity)
    ogg_32k = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}_32k.ogg")
    print("Generating 32kbps OGG Opus (vocal clarity mode)...")
    subprocess.run(
        ['ffmpeg', '-i', raw_mp3, '-c:a', 'libopus', '-b:a', '32k', '-vbr', 'on', '-y', ogg_32k],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    ogg_32k_size = os.path.getsize(ogg_32k)

    # 3. 24kbps OGG (Opus codec, WhatsApp voice note style ultra-compact)
    ogg_24k = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}_24k.ogg")
    print("Generating 24kbps OGG Opus (WhatsApp voice note bitrate)...")
    subprocess.run(
        ['ffmpeg', '-i', raw_mp3, '-c:a', 'libopus', '-b:a', '24k', '-vbr', 'on', '-y', ogg_24k],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    ogg_24k_size = os.path.getsize(ogg_24k)

    # Friendly aliases
    main_mp3 = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}.mp3")
    main_ogg = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}.ogg")
    shutil.copyfile(mp3_64k, main_mp3)
    shutil.copyfile(ogg_32k, main_ogg)

    # Also keep source if desired
    source_mp3 = os.path.join(WORK_DIR, f"sample_al_baqara_{reciter_id}_128k_source.mp3")
    shutil.copyfile(raw_mp3, source_mp3)

    files_to_upload = [main_mp3, main_ogg, ogg_24k, source_mp3]

    print("\n==================================================")
    print("COMPARISON SUMMARY (Surah Al-Baqara ~2 hours):")
    print("==================================================")
    print(f"1. Original Source MP3 (128k):     {raw_size / (1024*1024):>6.2f} MB (100%)")
    print(f"2. Current App MP3 (64k):          {mp3_64k_size / (1024*1024):>6.2f} MB ({(mp3_64k_size/raw_size)*100:.1f}%)")
    print(f"3. OGG Opus (32k vocal mode):      {ogg_32k_size / (1024*1024):>6.2f} MB ({(ogg_32k_size/raw_size)*100:.1f}%)  <-- 50% smaller than 64k MP3!")
    print(f"4. OGG Opus (24k WhatsApp mode):   {ogg_24k_size / (1024*1024):>6.2f} MB ({(ogg_24k_size/raw_size)*100:.1f}%)  <-- 63% smaller than 64k MP3!")
    print("==================================================\n")

    print("Uploading sample files to GitHub Release v5.0.0...")
    for f in files_to_upload:
        fname = os.path.basename(f)
        print(f"Uploading {fname}...")
        subprocess.run(['gh', 'release', 'upload', 'v5.0.0', f, '--clobber'], cwd=REPO_DIR, check=True)

    print("\nUpload complete! Direct listening links:")
    base_release_url = "https://github.com/x0911/quran-app-flutter-public-files/releases/download/v5.0.0"
    for f in files_to_upload:
        fname = os.path.basename(f)
        size_mb = os.path.getsize(f) / (1024*1024)
        print(f"- {fname} ({size_mb:.2f} MB): {base_release_url}/{fname}")

if __name__ == '__main__':
    main()
