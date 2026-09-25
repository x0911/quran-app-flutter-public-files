import urllib.request
import zipfile
import sqlite3
import tempfile
import os
import shutil
import json
import time

REPO_ROOT = "/Users/dash/work/dr-raaef/quran-app-flutter-public-files"
PUB_CAT_PATH = os.path.join(REPO_ROOT, "translations", "catalog.json")
APP_CAT_PATH = "/Users/dash/work/dr-raaef/quran-app-flutter/assets/json/translations_catalog.json"
OUT_DIR = os.path.join(REPO_ROOT, "translations", "individual")

os.makedirs(OUT_DIR, exist_ok=True)

# Language localization dictionaries
LANG_NAMES_AR = {
    'aa': 'العفرية',
    'ak': 'الأكانية (أشانتي)',
    'am': 'الأمهرية',
    'as': 'الأسامية',
    'az': 'الأذربيجانية',
    'bn': 'البنغالية',
    'bs': 'البوسنية',
    'ceb': 'البيسايا (سيبوانو)',
    'de': 'الألمانية',
    'en': 'الإنجليزية',
    'es': 'الإسبانية',
    'fa': 'الفارسية',
    'ff': 'الفولانية',
    'fr': 'الفرنسية',
    'gu': 'الغوجاراتية',
    'ha': 'الهوسا',
    'hi': 'الهندية',
    'hr': 'الكرواتية',
    'id': 'الإندونيسية',
    'ja': 'اليابانية',
    'km': 'الخميرية',
    'kn': 'الكانادا',
    'ku': 'الكردية',
    'ky': 'القيرغيزية',
    'ln': 'اللينغالا',
    'lt': 'الليتوانية',
    'mdh': 'الماغوينداناو',
    'mk': 'المقدونية',
    'ml': 'المالايالامية',
    'mos': 'الموري',
    'nl': 'الهولندية',
    'nqo': 'الإنكو',
    'om': 'الأورومية',
    'pa': 'البنجابية',
    'ps': 'الباشتو',
    'pt': 'البرتغالية',
    'rn': 'الكيروندية',
    'ro': 'الرومانية',
    'rw': 'الكينيارواندية',
    'si': 'السنهالية',
    'so': 'الصومالية',
    'sq': 'الألبانية',
    'sr': 'الصربية',
    'sv': 'السويدية',
    'sw': 'السواحلية',
    'ta': 'التاميلية',
    'te': 'التيلوغوية',
    'tg': 'الطاجيكية',
    'th': 'التايلاندية',
    'tl': 'التاغالوغية',
    'tr': 'التركية',
    'ug': 'الأويغورية',
    'ur': 'الأردية',
    'uz': 'الأوزبكية',
    'vi': 'الفيتنامية',
    'yo': 'اليوروبية',
    'zh': 'الصينية'
}

# Known mappings to existing catalog files to prevent duplicate processing
KNOWN_MAPPING = {
    'amharic_sadiq': 'quran.ar.amharic.db',
    'assamese_rafeeq': 'quran.ar.asami.db',
    'bosnian_mihanovich': 'quran.ar.bosnian.db',
    'bosnian_rwwad': 'quran.ar.bosnian.rwwad.db',
    'german_bubenheim': 'quran.ar.german.db',
    'english_saheeh': 'quran.ar.english-saheh.db',
    'spanish_garcia': 'quran.ar.spanish.garcia.db',
    'spanish_montada_eu': 'quran.ar.spanish.eu.db',
    'spanish_montada_latin': 'quran.ar.spanish.latin.db',
    'french_hameedullah': 'quran.ar.french-hameedullah.db',
    'hausa_gummi': 'quran.ar.hausa.db',
    'hindi_omari': 'quran.ar.hindi.db',
    'indonesian_complex': 'quran.ar.indonesia-complex.db',
    'indonesian_sabiq': 'quran.ar.indonesia-sabiq.db',
    'indonesian_affairs': 'quran.ar.indonesia.db',
    'japanese_saeedsato': 'quran.ar.japanese.db',
    'khmer_rwwad': 'quran.ar.khemr.db',
    'kurdish_bamoki': 'quran.ar.kurdish.db',
    'oromo_ababor': 'quran.ar.oromo.db',
    'pashto_rwwad': 'quran.ar.pashto.db',
    'portuguese_nasr': 'quran.ar.port.db',
    'albanian_nahi': 'quran.ar.albanian.db',
    'tamil_baqavi': 'quran.ar.tamil.db',
    'tajik_arifi': 'quran.ar.tajiki.db',
    'tagalog_rwwad': 'quran.ar.taglog.db',
    'turkish_rwwad': 'quran.ar.turkish.rwwad.db',
    'turkish_shaban': 'quran.ar.turkish.shaban.db',
    'turkish_shahin': 'quran.ar.turkish.shahin.db',
    'uyghur_saleh': 'quran.ar.uyghur.db',
    'urdu_junagarhi': 'quran.ar.urdu.db',
    'uzbek_mansour': 'quran.ar.uzbek.db',
    'vietnamese_rwwad': 'quran.ar.vetnami.db',
    'chinese_makin': 'quran.ar.chinese.db',
    'yoruba_mikail': 'quran.ar.yoruba.db'
}

with open(PUB_CAT_PATH, 'r', encoding='utf-8') as f:
    cat_data = json.load(f)

existing_sources = cat_data.get('sources', [])
existing_filenames = {s['fileName'].lower() for s in existing_sources}
existing_ids = {s['id'] for s in existing_sources}

# Fetch QuranEnc list
url = 'https://quranenc.com/api/v1/translations/list'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    qenc_list = json.loads(resp.read().decode('utf-8'))['translations']

print(f"Total translations on QuranEnc: {len(qenc_list)}")

next_id = 2001
while next_id in existing_ids:
    next_id += 1

newly_added_sources = []
new_zip_paths = []

for item in qenc_list:
    key = item['key']
    lang = item['language_iso_code']
    title = item['title']
    
    if key in KNOWN_MAPPING:
        continue
    
    file_name = f"quran.{lang}.{key}.db"
    zip_name = f"{file_name}.zip"
    
    if file_name.lower() in existing_filenames:
        continue
    
    print(f"\n--- Downloading & Converting {key} ({lang}) ---")
    print(f"Title: {title}")
    
    db_url = item.get('database_url') or f"https://quranenc.com/downloads/sqlite/{key}.zip"
    
    for attempt in range(3):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_src = os.path.join(tmpdir, "src.zip")
                dl_req = urllib.request.Request(db_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(dl_req, timeout=30) as r, open(zip_src, 'wb') as f:
                    f.write(r.read())
                
                with zipfile.ZipFile(zip_src, 'r') as z:
                    z.extractall(tmpdir)
                
                sqlite_file = None
                for root, _, files in os.walk(tmpdir):
                    for fn in files:
                        if fn.endswith('.sqlite') or fn.endswith('.db'):
                            sqlite_file = os.path.join(root, fn)
                            break
                    if sqlite_file:
                        break
                
                if not sqlite_file:
                    raise RuntimeError(f"No sqlite file in {db_url}")
                
                src_conn = sqlite3.connect(sqlite_file)
                src_cur = src_conn.cursor()
                src_cur.execute("SELECT sura, aya, translation FROM translations ORDER BY sura, aya;")
                rows = src_cur.fetchall()
                src_conn.close()
                
                if len(rows) != 6236:
                    print(f"  WARNING: verse count is {len(rows)} != 6236")
                
                # Build purified db
                dest_db = os.path.join(tmpdir, file_name)
                dest_conn = sqlite3.connect(dest_db)
                dest_cur = dest_conn.cursor()
                dest_cur.execute('''
                    CREATE TABLE verses (
                        surah INTEGER NOT NULL,
                        ayah  INTEGER NOT NULL,
                        text  TEXT NOT NULL,
                        PRIMARY KEY (surah, ayah)
                    ) WITHOUT ROWID;
                ''')
                dest_cur.executemany("INSERT INTO verses (surah, ayah, text) VALUES (?, ?, ?);", rows)
                dest_conn.commit()
                dest_cur.execute("PRAGMA page_size = 4096;")
                dest_cur.execute("PRAGMA journal_mode = OFF;")
                dest_cur.execute("VACUUM;")
                dest_conn.close()
                
                raw_size = os.path.getsize(dest_db)
                
                # Compress into .db.zip
                out_zip_path = os.path.join(OUT_DIR, zip_name)
                with zipfile.ZipFile(out_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                    z.write(dest_db, arcname=file_name)
                
                comp_size = os.path.getsize(out_zip_path)
                print(f"  Successfully created {zip_name}: Raw={raw_size}, Comp={comp_size}")
                
                # Title formatting
                lang_ar = LANG_NAMES_AR.get(lang, lang.upper())
                display_name_ar = f"ترجمة {lang_ar} ({title.split(' - ')[-1]})" if ' - ' in title else f"ترجمة {lang_ar}"
                
                source_record = {
                    "id": next_id,
                    "displayName": title,
                    "displayNameAr": display_name_ar,
                    "lang": lang,
                    "fileName": file_name,
                    "zipFileName": zip_name,
                    "rawSizeBytes": raw_size,
                    "slimSizeBytes": raw_size,
                    "compressedSizeBytes": comp_size,
                    "ayahCount": len(rows),
                    "downloadUrl": f"https://github.com/x0911/quran-app-flutter-public-files/releases/download/v4.0.0/{zip_name}"
                }
                
                existing_sources.append(source_record)
                existing_filenames.add(file_name.lower())
                existing_ids.add(next_id)
                newly_added_sources.append(source_record)
                new_zip_paths.append(out_zip_path)
                
                next_id += 1
                while next_id in existing_ids:
                    next_id += 1
                
                break
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)
            if attempt == 2:
                print(f"  FAILED to process {key}")

cat_data['sources'] = existing_sources
cat_data['totalSources'] = len(existing_sources)
cat_data['combinedZipSizeBytes'] = sum(s['compressedSizeBytes'] for s in existing_sources)
cat_data['combinedDbSizeBytes'] = sum(s['rawSizeBytes'] for s in existing_sources)

with open(PUB_CAT_PATH, 'w', encoding='utf-8') as f:
    json.dump(cat_data, f, ensure_ascii=False, indent=2)

with open(APP_CAT_PATH, 'w', encoding='utf-8') as f:
    json.dump(cat_data, f, ensure_ascii=False, indent=2)

print(f"\n==========================================")
print(f"Ingestion complete!")
print(f"Newly added translations: {len(newly_added_sources)}")
print(f"Total catalog sources: {cat_data['totalSources']}")
print(f"==========================================")
