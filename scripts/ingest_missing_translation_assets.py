import urllib.request
import zipfile
import sqlite3
import tempfile
import os
import shutil
import json

MISSING_ITEMS = [
    # 3 Translations
    {
        "id": 180,
        "displayName": "Spanish EU",
        "displayNameAr": "الترجمة الإسبانية (أوروبا)",
        "lang": "es",
        "fileName": "quran.ar.spanish.eu.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.spanish.eu.zip",
        "category": "translation"
    },
    {
        "id": 181,
        "displayName": "Spanish Latin",
        "displayNameAr": "الترجمة الإسبانية (أمريكا اللاتينية)",
        "lang": "es",
        "fileName": "quran.ar.spanish.latin.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.spanish.latin.zip",
        "category": "translation"
    },
    {
        "id": 1025,
        "displayName": "Yoruba",
        "displayNameAr": "ترجمة يوروبا",
        "lang": "yo",
        "fileName": "quran.ar.yoruba.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.yoruba.zip",
        "category": "translation"
    },
    # 8 Legacy Tafseers
    {
        "id": 1,
        "displayName": "Arabic Baghawy Tafseer",
        "displayNameAr": "تفسير البغوي",
        "lang": "ar",
        "fileName": "quran.ar.baghawy.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.baghawy.db.zip",
        "category": "tafsir"
    },
    {
        "id": 2,
        "displayName": "Arabic Ibn Kathir Tafseer",
        "displayNameAr": "تفسير ابن كثير",
        "lang": "ar",
        "fileName": "quran.ar.ibnkathir.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.ibnkathir.db.zip",
        "category": "tafsir"
    },
    {
        "id": 3,
        "displayName": "Arabic Al Moyassar Tafseer",
        "displayNameAr": "التفسير الميسر",
        "lang": "ar",
        "fileName": "quran.muyassar.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.muyassar.zip",
        "category": "tafsir"
    },
    {
        "id": 4,
        "displayName": "Arabic Qurtubi Tafseer",
        "displayNameAr": "تفسير القرطبي",
        "lang": "ar",
        "fileName": "quran.ar.qurtubi.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.qurtubi.db.zip",
        "category": "tafsir"
    },
    {
        "id": 5,
        "displayName": "Arabic Sa3di Tafseer",
        "displayNameAr": "تفسير السعدي",
        "lang": "ar",
        "fileName": "quran.ar.sa3dy.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.sa3dy.db.zip",
        "category": "tafsir"
    },
    {
        "id": 6,
        "displayName": "Arabic Tabari Tafseer",
        "displayNameAr": "تفسير الطبري",
        "lang": "ar",
        "fileName": "quran.ar.tabari.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.tabari.db.zip",
        "category": "tafsir"
    },
    {
        "id": 7,
        "displayName": "Arabic Tanweer Tafseer",
        "displayNameAr": "تفسير التحرير والتنوير",
        "lang": "ar",
        "fileName": "quran.ar.tanweer.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.tanweer.db.zip",
        "category": "tafsir"
    },
    {
        "id": 8,
        "displayName": "Arabic Waseet Tafseer",
        "displayNameAr": "تفسير الوسيط للطنطاوي",
        "lang": "ar",
        "fileName": "quran.ar.waseet.db",
        "sourceUrl": "https://library4islam.com/Quran/translations/quran.ar.waseet.db.zip",
        "category": "tafsir"
    },
]

REPO_ROOT = "/Users/dash/work/dr-raaef/quran-app-flutter-public-files"
TRANS_DIR = os.path.join(REPO_ROOT, "translations", "individual")
TAFSIR_DIR = os.path.join(REPO_ROOT, "tafseers", "individual")

os.makedirs(TRANS_DIR, exist_ok=True)
os.makedirs(TAFSIR_DIR, exist_ok=True)

processed_files = []

for item in MISSING_ITEMS:
    print(f"\nProcessing {item['id']}: {item['displayName']} ({item['fileName']})...")
    url = item['sourceUrl']
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_zip = os.path.join(tmpdir, "raw.zip")
        with urllib.request.urlopen(req) as resp, open(raw_zip, 'wb') as f:
            f.write(resp.read())
        
        # Extract source zip
        extract_dir = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(raw_zip, 'r') as z:
            z.extractall(extract_dir)
        
        # Locate the .db file (ignore __MACOSX and ._ files)
        found_db = None
        for root, _, files in os.walk(extract_dir):
            if "__MACOSX" in root:
                continue
            for fname in files:
                if fname.startswith("._") or fname.startswith("."):
                    continue
                if fname.endswith(".db") or fname.endswith(".sqlite") or "quran" in fname.lower():
                    found_db = os.path.join(root, fname)
                    break
            if found_db:
                break
        
        if not found_db:
            raise RuntimeError(f"Could not find valid db in {url}")
        
        print(f"  Found raw database file: {os.path.basename(found_db)}")
        
        # Rename/move to target standardized db filename
        target_db = os.path.join(tmpdir, item['fileName'])
        shutil.copy2(found_db, target_db)
        
        # Verify sqlite and record count
        conn = sqlite3.connect(target_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        print(f"  Tables: {tables}")
        
        count = 0
        for t in ['verses', 'verses_content', 'verse']:
            if t in tables:
                cur.execute(f"SELECT count(*) FROM {t};")
                count = cur.fetchone()[0]
                break
        print(f"  Ayah count: {count}")
        
        # Vacuum
        cur.execute("VACUUM;")
        conn.close()
        
        raw_size = os.path.getsize(target_db)
        
        # Create standard zip: <fileName>.zip containing only <fileName>
        out_dir = TRANS_DIR if item['category'] == 'translation' else TAFSIR_DIR
        out_zip = os.path.join(out_dir, f"{item['fileName']}.zip")
        
        with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            z.write(target_db, arcname=item['fileName'])
        
        comp_size = os.path.getsize(out_zip)
        print(f"  Created: {out_zip} (Raw: {raw_size} bytes, Compressed: {comp_size} bytes)")
        
        item['rawSizeBytes'] = raw_size
        item['compressedSizeBytes'] = comp_size
        item['ayahCount'] = count
        item['zipFileName'] = f"{item['fileName']}.zip"
        item['outZipPath'] = out_zip
        processed_files.append(item)

print("\n--- ALL 11 ITEMS PROCESSED SUCCESSFULLY ---")
for p in processed_files:
    print(f"{p['id']}: {p['zipFileName']} ({p['compressedSizeBytes']} bytes)")
