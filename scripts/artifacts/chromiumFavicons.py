"""Chromium Favicons database parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each Chromium-based browser profile keeps a Favicons SQLite database mapping page URLs
to the icons shown for them: icon_mapping (page_url, icon_id), favicons (url, icon_type)
and favicon_bitmaps (the stored image of each size, with last_updated and
last_requested). This reports one row per icon_mapping row with its icon, and whether
the History database of the same profile lists the page URL.
"""

import sqlite3

from scripts.chromium.browser_profiles import (enum_label, open_store, profile_stores,
                                               table_columns, webkit_time)
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc


# favicons.icon_type holds 1 << (IconType - 1) (see notes), so these are the IconType
# names of the persisted values.
_ICON_TYPES = {1: 'kFavicon', 2: 'kTouchIcon', 4: 'kTouchPrecomposedIcon', 8: 'kWebManifestIcon'}
_PAGE_URL_TYPES = {0: 'kRegular', 1: 'kRedirect'}

__artifacts_v2__ = {
    "chromiumFavicons": {
        "name": "Chromium Favicons",
        "description": "Page URLs the Favicons databases of Google Chrome, Microsoft Edge, "
                       "Brave, Vivaldi, Opera and Chromium profiles map to an icon, with the "
                       "icon's URL, type, stored sizes, times and image, and whether the same "
                       "profile's History database lists the page URL.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads each Chromium-based browser profile's Favicons database, one row per "
                 "icon_mapping row, which Chromium's source describes as a page URL and the ID of an "
                 "icon mapped to it, joined to that icon's favicons row (its URL and type) and to its "
                 "favicon_bitmaps rows, one per stored size "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_database.cc#L41-L90; "
                 "Chrome 65: "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/thumbnail_database.cc#L37-L78). "
                 "Browser, Profile and User come from the path as in the other Chromium artifacts: the "
                 "browser from the user data folder, the profile from the folder inside it and the "
                 "user from the home folder that holds it; together they identify the file. Browser, "
                 "Profile and User each held one value on every row of lonewolf_win10, which carries "
                 "one Chrome profile in one home folder, and User held one value on every row of "
                 "pc_mus_001_win11. Page URL is page_url and Icon URL is the icon's url, as stored. "
                 "Icon Type is icon_type named through Chromium's IconType: the database stores 1 "
                 "shifted left by the IconType value less one "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_database.cc#L993-L998; "
                 "Chrome 65: "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/thumbnail_database.cc#L1010-L1015), "
                 "so 1, 2, 4 and 8 are kFavicon, kTouchIcon, kTouchPrecomposedIcon and "
                 "kWebManifestIcon "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon_base/favicon_types.h#L36-L42). "
                 "Icon Type held kFavicon (1) on 699 of the 700 lonewolf_win10 rows and kTouchIcon (2) "
                 "on the other, and kFavicon (1) on every pc_mus_001_win11 row. Sizes lists the width "
                 "x height of each stored bitmap of the icon, and Icon renders the largest one as "
                 "media; every row on the tested images had one. Last Updated and Last Requested are "
                 "the latest last_updated and last_requested of those bitmaps, read as microseconds "
                 "since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/sql/statement.cc#L529-L535; "
                 "Chrome 65: "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/history/core/browser/thumbnail_database.cc#L485-L486 "
                 "and "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7), "
                 "with a zero value shown blank. Chromium's source describes last_updated as the time "
                 "the favicon was inserted, used to decide when to download it again and 0 when the "
                 "bitmap was explicitly expired, and last_requested as the time the bitmap was last "
                 "requested, non-zero only for a bitmap fetched on demand "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_database.cc#L76-L90). "
                 "No row on the tested images had both: Last Updated was set on 699 lonewolf_win10 "
                 "rows and 599 pc_mus_001_win11 rows, Last Requested on 1 and 4, and 38 "
                 "pc_mus_001_win11 rows had neither. In History is Yes when the urls table of the "
                 "History database in the same profile folder lists Page URL exactly, No when it does "
                 "not, and blank when no readable History sits beside the Favicons database. It was No "
                 "on 5 of the 700 lonewolf_win10 rows and on 13 of the 641 pc_mus_001_win11 rows (4 in "
                 "one Chrome profile and 9 in Microsoft Edge). Why a page URL mapped to an icon is "
                 "missing from History was not established, and No does not by itself establish a "
                 "visit. On lonewolf_win10 the History database had a rollback journal SQLite treats "
                 "as hot, so it was read as found, with the journal ignored, and the run log says so. "
                 "Page URL Type is page_url_type named through PageUrlType, 0 kRegular and 1 kRedirect "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_types.h#L26-L35), "
                 "a column the database carries from its version 9 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_database.cc#L103, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/favicon/core/favicon_database.cc#L127); "
                 "every database on the tested Windows images is version 8, as its meta table records, "
                 "so Page URL Type was empty on every row there. On the public MacBook Pro logical "
                 "extraction (macOS 15.4 build 24E248, not a registered corpus key), whose Chrome app "
                 "bundle holds framework versions 143.0.7499.42 and 143.0.7499.170, the Chrome Default "
                 "profile's database is version 9: of its 68 rows, Page URL Type was kRegular (0) on "
                 "49 and kRedirect (1) on 19, Icon Type was kFavicon (1) on all, Last Updated was set "
                 "on all and Last Requested on none, and In History was No on 2. Its Favicons and "
                 "History copies under System/Volumes/Data/Users/ were byte-identical to those under "
                 "Users/ and were not read again. Tested: Chrome 65.0.3325.181 on lonewolf_win10 and "
                 "Chrome 108.0.5359.125 and Microsoft Edge 108.0.1462.54 on pc_mus_001_win11, whose "
                 "rows come from the Chrome Default and Profile 2 profiles and the Edge Default "
                 "profile; its Chrome Guest Profile and System Profile databases held no mapping. No "
                 "member of af_case2_win10 or dleapp_macos_bigsur matched the declared paths. When a "
                 "logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, with any "
                 "-journal or -wal beside it, is read once and counted in the run log, and copies that "
                 "differ are both read. Values not reported include the meta table and the "
                 "favicon_bitmaps rows of icons no page URL maps to.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Favicons*',
            '*/Library/Application Support/Google/Chrome/*/Favicons*',
            '*/.config/google-chrome/*/Favicons*',
            '*/AppData/Local/Chromium/User Data/*/Favicons*',
            '*/Library/Application Support/Chromium/*/Favicons*',
            '*/.config/chromium/*/Favicons*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Favicons*',
            '*/Library/Application Support/Microsoft Edge/*/Favicons*',
            '*/.config/microsoft-edge/*/Favicons*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Favicons*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Favicons*',
            '*/.config/BraveSoftware/Brave-Browser/*/Favicons*',
            '*/AppData/Local/Vivaldi/User Data/*/Favicons*',
            '*/Library/Application Support/Vivaldi/*/Favicons*',
            '*/.config/vivaldi/*/Favicons*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Favicons*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Favicons*',
            '*/.config/opera/*/Favicons*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Favicons*',
            '*/Library/Application Support/com.operasoftware.Opera/Favicons*',
            '*/.config/opera/Favicons*',
            '*/AppData/Local/Google/Chrome/User Data/*/History*',
            '*/Library/Application Support/Google/Chrome/*/History*',
            '*/.config/google-chrome/*/History*',
            '*/AppData/Local/Chromium/User Data/*/History*',
            '*/Library/Application Support/Chromium/*/History*',
            '*/.config/chromium/*/History*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/History*',
            '*/Library/Application Support/Microsoft Edge/*/History*',
            '*/.config/microsoft-edge/*/History*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/History*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/History*',
            '*/.config/BraveSoftware/Brave-Browser/*/History*',
            '*/AppData/Local/Vivaldi/User Data/*/History*',
            '*/Library/Application Support/Vivaldi/*/History*',
            '*/.config/vivaldi/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/History*',
            '*/Library/Application Support/com.operasoftware.Opera/*/History*',
            '*/.config/opera/*/History*',
            '*/AppData/Roaming/Opera Software/Opera Stable/History*',
            '*/Library/Application Support/com.operasoftware.Opera/History*',
            '*/.config/opera/History*',
        ),
        "output_types": "standard",
        "artifact_icon": "image",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 700 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 641 rows",
        },
    },
}


def _history_urls(store, label):
    """The url values of a History store's urls table, or None when it cannot be read."""
    db = open_store(store, label)
    if db is None:
        return None
    try:
        if not table_columns(db, 'urls'):
            return None
        return {row[0] for row in db.execute('SELECT url FROM urls')}
    except sqlite3.Error as ex:
        logfunc(f'{label}: could not read {store.relative}: {ex}')
        return None
    finally:
        db.close()


def _bitmaps(db):
    """{icon_id: (latest last_updated, latest last_requested, sizes, largest image)}."""
    icons = {}
    for icon_id, updated, requested, width, height, image in db.execute(
            'SELECT icon_id, last_updated, last_requested, width, height, image_data '
            'FROM favicon_bitmaps ORDER BY icon_id, width, height, id'):
        latest_updated, latest_requested, sizes, largest = icons.get(icon_id, (0, 0, [], None))
        size = f'{width}x{height}'
        if size not in sizes:
            sizes.append(size)
        if image and (largest is None or (width or 0) * (height or 0) >= largest[0]):
            largest = ((width or 0) * (height or 0), image)
        icons[icon_id] = (max(latest_updated, updated or 0),
                          max(latest_requested, requested or 0), sizes, largest)
    return icons


@artifact_processor
def chromiumFavicons(context):
    label = 'Chromium Favicons'
    data_headers = (('Last Updated', 'datetime'), ('Last Requested', 'datetime'), 'Page URL',
                    'In History', 'Icon URL', 'Icon Type', 'Sizes', ('Icon', 'media'),
                    'Page URL Type', 'Browser', 'Profile', 'User')
    stores = profile_stores(context, {'Favicons', 'History'}, label)
    histories = {store.container: store for store in stores if store.name == 'History'}
    data_list = []
    sources = []
    for store in (s for s in stores if s.name == 'Favicons'):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            mapping = table_columns(db, 'icon_mapping')
            if not mapping or not table_columns(db, 'favicons') or not table_columns(
                    db, 'favicon_bitmaps'):
                logfunc(f'{label}: {store.relative} lacks the icon_mapping, favicons or '
                        f'favicon_bitmaps table')
                continue
            url_type = 'm.page_url_type' if 'page_url_type' in mapping else 'NULL'
            rows = db.execute(f'SELECT m.page_url, m.icon_id, f.url, f.icon_type, {url_type} '
                              'FROM icon_mapping m LEFT JOIN favicons f ON f.id = m.icon_id '
                              'ORDER BY m.id').fetchall()
            icons = _bitmaps(db)
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        history = histories.get(store.container)
        urls = _history_urls(history, label) if history is not None else None
        if history is not None and urls is not None:
            sources.append(history.path)
        absent = 0
        for page_url, icon_id, icon_url, icon_type, page_url_type in rows:
            updated, requested, sizes, largest = icons.get(icon_id, (0, 0, [], None))
            media = check_in_embedded_media(store.path, largest[1]) if largest else None
            in_history = '' if urls is None else ('Yes' if page_url in urls else 'No')
            absent += in_history == 'No'
            data_list.append((webkit_time(updated), webkit_time(requested), page_url,
                              in_history, icon_url or '', enum_label(_ICON_TYPES, icon_type),
                              ', '.join(sizes), media or '',
                              enum_label(_PAGE_URL_TYPES, page_url_type),
                              store.browser, store.profile, store.user))
        logfunc(f'{label}: {len(rows)} page URLs in {store.relative}; '
                + (f'{absent} not listed in the urls table of {history.relative}'
                   if urls is not None else 'no readable History beside it'))
    return data_headers, data_list, '\n'.join(sources)
