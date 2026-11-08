__artifacts_v2__ = {
    "chromiumAppCache": {
        "name": "Chromium Application Cache",
        "description": "Sites set up for offline use through the HTML5 application cache of older Google "
                       "Chrome and Chromium builds on Windows: each cache group's manifest "
                       "URL and origin, its created and last access times, the time its cache was last "
                       "updated, the pages that used the manifest, and the number and total size of the "
                       "cached entries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per cache of each cache group in the Application Cache/Index SQLite database of a Chromium-based browser profile on Windows, the store of the HTML5 application cache; Chromium at d5e871096c2c285b2f93f7922b69c2edce5b1de1 has no content/browser/appcache folder. A group is one manifest; the Groups, Caches and Entries tables are those Chromium creates (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_database.cc#L58-L80). Its times are base::Time internal values, microseconds since 1601-01-01 UTC (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_database.cc#L419-L422 and #L559). Created is the group's creation_time and Last Access its last_access_time; both are set when the group is first stored (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_storage_impl.cc#L704-L706), and Last Access is set again each time the group's cache is loaded from the database (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_storage_impl.cc#L523-L532 and #L565-L575, https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_database.cc#L443-L449). Cache Updated is the cache's update_time, set when a new or updated cache is stored (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_update_job.cc#L770-L786). Last Full Update Check is last_full_update_check_time, set when a full update check completes, whether or not it stored a new cache (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_update_job.cc#L782-L783 and #L1286-L1288); the column came with schema version 7, whose upgrade fills it with the cache's update_time (https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_database.cc#L1237-L1262), and it is blank for a version 5 file. Manifest URL and Origin are the group's manifest_url and origin as stored. Pages Using the Manifest lists the URLs of the group's entries flagged MASTER (bit 0 of flags, https://github.com/chromium/chromium/blob/65.0.3325.181/content/browser/appcache/appcache_entry.h#L20-L29), the HTML5 term for a page added to the cache because it named the manifest (https://www.w3.org/TR/2011/WD-html5-20110525/offline.html). Entries is the number of the cache's rows in Entries and Entries Size (bytes) the sum of their response_size; Cache Size (bytes) is the cache's cache_size as stored. The cached responses themselves (the Cache folder beside Index, keyed by response id) are not read, and neither are the Namespaces, OnlineWhiteLists and DeletableResponseIds tables or first_evictable_error_time. Tested: lonewolf_win10 (Chrome 65.0.3325.181, schema version 7: 6 groups with one cache each, 698 entries) and cfreds_leakage_win7 (schema version 5: 1 group, 6 entries). On both, every group had one cache and every entry belonged to a cache that exists, each group had exactly one MASTER entry, Last Access was not earlier than Created, and Entries Size (bytes) equalled Cache Size (bytes) on every row. On lonewolf_win10 Last Access fell 7.4 days after Created on all 6 groups and Last Full Update Check fell after Cache Updated on all 6; on cfreds_leakage_win7 Created fell 35 milliseconds after Cache Updated and Last Full Update Check held no value. On lonewolf_win10 Origin held one value on all 6 rows, and Browser, Profile and User held one value on every row of both images, which each hold one profile with an application cache. No other Windows image in the corpus listings holds an Application Cache folder; the Microsoft Edge path is declared but no Edge Application Cache was tested.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Application Cache/Index*',
            '*/AppData/Local/Chromium/User Data/*/Application Cache/Index*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Application Cache/Index*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Application Cache/Index*',
            '*/AppData/Local/Vivaldi/User Data/*/Application Cache/Index*',
        ),
        "output_types": "standard",
        "artifact_icon": "download-cloud",
        "sample_data": {
            "lonewolf_win10": "Windows 10 Education build 16299, Google Chrome 65.0.3325.181, Application Cache schema version 7 | 6 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601, Google Chrome, Application Cache schema version 5 | 1 rows",
        },
    },
}

import os

from scripts.chromium.browser_profiles import webkit_time
from scripts.chromium.web_storage import profile_folders
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

# AppCacheEntry::Type, content/browser/appcache/appcache_entry.h at 65.0.3325.181.
_MASTER = 1 << 0

# last_full_update_check_time came with schema version 7 (UpgradeSchema in appcache_database.cc);
# version 5 files lack it, and it reads as NULL there.
_QUERY = '''
    SELECT g.group_id, g.origin, g.manifest_url, g.creation_time, g.last_access_time,
           {checked}, c.cache_id, c.update_time, c.cache_size
    FROM Groups g LEFT JOIN Caches c ON c.group_id = g.group_id
    ORDER BY g.group_id, c.cache_id
'''


def _time(value):
    return webkit_time(value) if isinstance(value, int) and value > 0 else ''


def read_groups(db):
    """One tuple per cache of each group of an open Index database, or None when a table is missing.

    (last access, created, cache updated, last full update check, manifest URL, origin, MASTER entry URLs,
    entries, entries size, cache size), times as datetimes or ''.
    """
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    if not {'Groups', 'Caches', 'Entries'} <= tables:
        return None
    entries = {}
    for cache_id, url, flags, size in db.execute('SELECT cache_id, url, flags, response_size FROM Entries ORDER BY url'):
        held = entries.setdefault(cache_id, [0, 0, []])
        held[0] += 1
        held[1] += size if isinstance(size, int) else 0
        if isinstance(flags, int) and flags & _MASTER:
            held[2].append(url or '')
    group_columns = {row[1] for row in db.execute('PRAGMA table_info(Groups)')}
    checked_column = 'g.last_full_update_check_time' if 'last_full_update_check_time' in group_columns else 'NULL'
    rows = []
    for (_group_id, origin, manifest_url, created, accessed, checked,
         cache_id, updated, cache_size) in db.execute(_QUERY.format(checked=checked_column)):
        count, total, masters = entries.get(cache_id, (0, 0, []))
        rows.append((_time(accessed), _time(created), _time(updated), _time(checked), manifest_url or '',
                     origin or '', '\n'.join(masters), count, total,
                     cache_size if isinstance(cache_size, int) else ''))
    return rows


@artifact_processor
def chromiumAppCache(context):
    label = 'Chromium Application Cache'
    data_list, sources = [], []
    for store in profile_folders(context, 'Application Cache', label):
        index = os.path.join(store.path, 'Index')
        if not os.path.isfile(index):
            continue
        db = open_sqlite_db_readonly(index)
        if db is None:
            continue
        try:
            rows = read_groups(db)
        finally:
            db.close()
        sources.append(index)
        if rows is None:
            logfunc(f'{label}: {store.relative}/Index lacks the Groups, Caches or Entries table')
            continue
        data_list.extend(row + (store.browser, store.profile, store.user) for row in rows)
        logfunc(f'{label}: {len(rows)} cache groups in {store.relative}/Index')
    data_headers = (('Last Access', 'datetime'), ('Created', 'datetime'), ('Cache Updated', 'datetime'),
                    ('Last Full Update Check', 'datetime'), 'Manifest URL', 'Origin', 'Pages Using the Manifest',
                    ('Entries', 'number'), ('Entries Size (bytes)', 'number'), ('Cache Size (bytes)', 'number'),
                    'Browser', 'Profile', 'User')
    return data_headers, data_list, '\n'.join(sources)
