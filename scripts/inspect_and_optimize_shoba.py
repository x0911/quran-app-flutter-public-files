#!/usr/bin/env python3
import os
import sys
import zipfile
import io
from PIL import Image

def analyze_zip(zip_path):
    if not os.path.exists(zip_path):
        print(f"File not found: {zip_path}")
        return

    print(f"Analyzing {zip_path} (size: {os.path.getsize(zip_path):,} bytes)...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        infolist = zf.infolist()
        print(f"Total entries: {len(infolist)}")
        
        total_uncompressed = sum(info.file_size for info in infolist)
        total_compressed = sum(info.compress_size for info in infolist)
        print(f"Total uncompressed size: {total_uncompressed:,} bytes ({total_uncompressed / (1024*1024):.2f} MB)")
        print(f"Total compressed size: {total_compressed:,} bytes ({total_compressed / (1024*1024):.2f} MB)")

        sample_infos = [info for info in infolist if info.filename.lower().endswith('.png')][:5]
        for info in sample_infos:
            data = zf.read(info.filename)
            img = Image.open(io.BytesIO(data))
            print(f"  {info.filename}: {img.size} ({img.mode}), orig size: {len(data):,} bytes")

if __name__ == '__main__':
    zip_path = sys.argv[1] if len(sys.argv) > 1 else '/Users/dash/work/dr-raaef/quran-app-flutter-public-files/shoba/images_1260_shoba.zip'
    analyze_zip(zip_path)
