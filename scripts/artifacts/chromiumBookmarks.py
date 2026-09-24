__artifacts_v2__ = {
    "chromiumBookmarks": {
        "name": "Chromium Bookmarks",
        "description": "URL bookmarks from the Bookmarks and AccountBookmarks files of Google Chrome, "
                       "Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles, with the folder "
                       "path, the date added and the date last used.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Bookmarks and AccountBookmarks JSON files of each Chromium-based browser "
                 "profile, the two file names in bookmark_constants.cc "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/bookmarks/common/bookmark_constants.cc#L13-L16); "
                 "one row per bookmark of type url, and Store names the file. Folders are not rows of "
                 "their own. Folder Path joins the names of the folders above the bookmark with a > "
                 "separator, starting with the root folder's stored name, and Root is the key the root "
                 "sits under in the file, such as bookmark_bar, other or synced "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/bookmarks/browser/bookmark_codec.cc#L37-L40). "
                 "Date Added and Date Last Used are the date_added and date_last_used strings, "
                 "microseconds since 1601-01-01 UTC "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/bookmarks/browser/bookmark_codec.cc#L183-L186; "
                 "the Chrome 65 release wrote date_added with base::Time::ToInternalValue, "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/bookmarks/browser/bookmark_codec.cc#L126-L127, "
                 "which base/time/time.h describes as microseconds since the Windows epoch, "
                 "1601-01-01 UTC, "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/base/time/time.h#L5-L7); "
                 "Date Last Used is blank where the file has no value or 0. Browser, Profile and User come "
                 "from the path: the browser from the user data folder, the profile from the folder inside "
                 "it, and the user from the home folder that holds it; Source File names the file each row "
                 "came from, so rows from two profiles or two users stay apart. A profile under User "
                 "Data/Snapshots/<version>/ is reported with that path as its Profile, so a snapshot copy "
                 "is not merged with the live profile; no registered image carries one, and that branch "
                 "was exercised on a constructed tree only. No registered image produced a row: the one "
                 "Bookmarks file of pc_mus_001_win11 (Chrome Profile 2) and the one of lonewolf_win10 "
                 "(Chrome Default) each hold only their root folders, with no bookmarks under them, and no "
                 "AccountBookmarks file is present on either. The walk over nested folders, both file "
                 "names and the handling of an unreadable file were exercised on constructed files only. "
                 "Not read: Bookmarks.bak, present once on pc_mus_001_win11, and the "
                 "EncryptedBookmarks2 and EncryptedAccountBookmarks2 files, whose constants in "
                 "bookmark_constants.cc name them as encrypted bookmark files "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/bookmarks/common/bookmark_constants.cc#L17-L20). "
                 "No member of af_case2_win10 or "
                 "dleapp_macos_bigsur matched any of the declared paths. The user data folders read are "
                 "those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, "
                 "macOS and Linux, and a store directly inside an Opera user data folder is "
                 "reported with that folder as its Profile. Only the Windows Google Chrome "
                 "folder was exercised by a registered image, the Microsoft Edge profile of "
                 "pc_mus_001_win11 holding no Bookmarks file; a constructed tree exercised the "
                 "Brave macOS, Vivaldi Linux and Opera Windows folders, the last with its "
                 "profile kept directly in the user data folder, and the remaining folders were "
                 "exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical "
                 "is read once and counted in the run log, and copies that differ are both "
                 "read. The macOS Google Chrome folder was also exercised, on the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus "
                 "key), where each store was byte-identical under the two paths. "
                 "Not read: other Chrome "
                 "channels (Beta, Dev, Canary), extension storage partitions under a profile's Storage "
                 "folder, and WebView2 or Electron app profiles such as EBWebView folders, which share the "
                 "layout but sit in other applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Bookmarks*',
            '*/Library/Application Support/Google/Chrome/*/Bookmarks*',
            '*/.config/google-chrome/*/Bookmarks*',
            '*/AppData/Local/Chromium/User Data/*/Bookmarks*',
            '*/Library/Application Support/Chromium/*/Bookmarks*',
            '*/.config/chromium/*/Bookmarks*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Bookmarks*',
            '*/Library/Application Support/Microsoft Edge/*/Bookmarks*',
            '*/.config/microsoft-edge/*/Bookmarks*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Bookmarks*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Bookmarks*',
            '*/.config/BraveSoftware/Brave-Browser/*/Bookmarks*',
            '*/AppData/Local/Vivaldi/User Data/*/Bookmarks*',
            '*/Library/Application Support/Vivaldi/*/Bookmarks*',
            '*/.config/vivaldi/*/Bookmarks*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Bookmarks*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Bookmarks*',
            '*/.config/opera/*/Bookmarks*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Bookmarks*',
            '*/Library/Application Support/com.operasoftware.Opera/Bookmarks*',
            '*/.config/opera/Bookmarks*',
            '*/AppData/Local/Google/Chrome/User Data/*/AccountBookmarks*',
            '*/Library/Application Support/Google/Chrome/*/AccountBookmarks*',
            '*/.config/google-chrome/*/AccountBookmarks*',
            '*/AppData/Local/Chromium/User Data/*/AccountBookmarks*',
            '*/Library/Application Support/Chromium/*/AccountBookmarks*',
            '*/.config/chromium/*/AccountBookmarks*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/AccountBookmarks*',
            '*/Library/Application Support/Microsoft Edge/*/AccountBookmarks*',
            '*/.config/microsoft-edge/*/AccountBookmarks*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/AccountBookmarks*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/AccountBookmarks*',
            '*/.config/BraveSoftware/Brave-Browser/*/AccountBookmarks*',
            '*/AppData/Local/Vivaldi/User Data/*/AccountBookmarks*',
            '*/Library/Application Support/Vivaldi/*/AccountBookmarks*',
            '*/.config/vivaldi/*/AccountBookmarks*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/AccountBookmarks*',
            '*/Library/Application Support/com.operasoftware.Opera/*/AccountBookmarks*',
            '*/.config/opera/*/AccountBookmarks*',
            '*/AppData/Roaming/Opera Software/Opera Stable/AccountBookmarks*',
            '*/Library/Application Support/com.operasoftware.Opera/AccountBookmarks*',
            '*/.config/opera/AccountBookmarks*',
        ),
        "output_types": "standard",
        "artifact_icon": "bookmark",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (its one Bookmarks file holds root folders only)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (its one Bookmarks file holds root folders only)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import json

from scripts.chromium.browser_profiles import (profile_stores, row_tail,
                                               webkit_time)
from scripts.ilapfuncs import artifact_processor, logfunc


def _url_nodes(node, folders):
    """Yield (folder path, node) for each url node under `node`, depth first."""
    if not isinstance(node, dict):
        return
    if node.get('type') == 'url':
        yield ' > '.join(folders), node
        return
    children = node.get('children')
    if not isinstance(children, list):
        return
    path = folders + [str(node.get('name', ''))]
    for child in children:
        yield from _url_nodes(child, path)


@artifact_processor
def chromiumBookmarks(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Bookmarks', 'AccountBookmarks'},
                                'Chromium Bookmarks'):
        try:
            with open(store.path, 'r', encoding='utf-8') as handle:
                document = json.load(handle)
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            logfunc(f'Chromium Bookmarks: could not read {store.relative}: {ex}')
            continue
        roots = document.get('roots') if isinstance(document, dict) else None
        if not isinstance(roots, dict):
            logfunc(f'Chromium Bookmarks: {store.relative} has no roots object; not read')
            continue
        sources.append(store.path)
        for root_key, root in roots.items():
            for folder_path, node in _url_nodes(root, []):
                data_list.append((webkit_time(node.get('date_added')),
                                  webkit_time(node.get('date_last_used')),
                                  node.get('name', ''), node.get('url', ''), folder_path,
                                  root_key, store.name) + row_tail(store))
    data_headers = (('Date Added', 'datetime'), ('Date Last Used', 'datetime'), 'Name', 'URL',
                    'Folder Path', 'Root', 'Store', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
