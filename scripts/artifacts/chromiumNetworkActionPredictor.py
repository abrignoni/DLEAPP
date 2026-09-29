"""Chromium Network Action Predictor parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the network_action_predictor table of each Chromium-based browser
profile's Network Action Predictor database: text typed into the omnibox paired
with a URL a suggestion led to, and how often that URL was or was not the one
opened. Sources are in the notes.
"""

__artifacts_v2__ = {
    "chromiumNetworkActionPredictor": {
        "name": "Chromium Network Action Predictor",
        "description": "Text entered in the omnibox of Chromium-based browser profiles, in lower "
                       "case, with each URL a suggestion led to and how often that URL was or "
                       "was not the one opened, from the Network Action Predictor database.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the network_action_predictor table of each Chromium-based browser profile's "
                 "Network Action Predictor database. Browser, Profile and User come from the path: the "
                 "browser from the user data folder, the profile from the folder inside it, and the user "
                 "from the home folder that holds it. A profile keeps one such database, so those columns "
                 "name the file a row came from, and the report's located-at line lists each file read. "
                 "Browser and User held one value on every row of both tested images, and Profile held one "
                 "value on every row of lonewolf_win10; on pc_mus_001_win11 the rows came from the Google "
                 "Chrome Default and Profile 2 databases, while its Microsoft Edge, Guest Profile and "
                 "System Profile databases held no rows. Only the Windows Google Chrome and Microsoft Edge "
                 "folders were exercised by a registered image; the other browsers' folders are matched by "
                 "the same paths and were not exercised. Databases under an application's EBWebView "
                 "folder, as for two Windows apps on pc_mus_001_win11, are outside these paths and not "
                 "read. The table holds an id, user_text, url, number_of_hits and number_of_misses "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor_table.cc#L221-L226), "
                 "the same columns as in the Chrome 65 source "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/chrome/browser/predictors/autocomplete_action_predictor_table.cc#L238-L243). "
                 "Chromium registers each set of omnibox suggestions with the text it was made for, "
                 "converted to lower case, keeping the URL each suggestion leads to "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.h#L101-L104 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L164-L198). "
                 "When a URL is opened from the omnibox with its suggestion list open, and not by paste "
                 "and go "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L298-L345), "
                 "each kept pair of text and URL gains a hit if its URL is the one opened and a miss "
                 "otherwise, and a pair not yet in the table is added with a new id "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L353-L391). "
                 "Chrome 65 did the same, counting only text that began the text in the omnibox when the "
                 "URL was opened "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/chrome/browser/predictors/autocomplete_action_predictor.cc#L110-L115 "
                 "with "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/chrome/browser/predictors/autocomplete_action_predictor.cc#L228-L236 "
                 "and "
                 "https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/chrome/browser/predictors/autocomplete_action_predictor.cc#L252-L292). "
                 "Typed Text is user_text, URL is url, Hits is number_of_hits and Misses is "
                 "number_of_misses, as stored. Typed Text is therefore text a set of suggestions was made "
                 "for, which can be a fragment of what was finally entered: 461 of lonewolf_win10's rows "
                 "and 31 of pc_mus_001_win11's had a Typed Text one character long, and no row on either "
                 "image held an upper-case letter. A row with Hits 0 is a URL that was suggested for the "
                 "text and was not the one opened. 117 of lonewolf_win10's 10,747 rows and 22 of "
                 "pc_mus_001_win11's 439 had Hits above zero. The table records no time. Chromium deletes "
                 "rows with the history they refer to, and all of them when all history is deleted "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L673-L697); "
                 "the current source also deletes, when the predictor starts, rows whose URL the history "
                 "service's in-memory database does not hold or last visited more than 14 days before "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L114 "
                 "with "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L504-L547 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L549-L572), "
                 "and keeps at most 2,000 rows, removing those it rates lowest "
                 "(https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L86-L88 "
                 "and "
                 "https://github.com/chromium/chromium/blob/a93bac421698a16f0417155675ec66d50e9becd2/chrome/browser/predictors/autocomplete_action_predictor.cc#L397-L399). "
                 "The Chrome 65 source has no such limit, and lonewolf_win10's Chrome profile held 10,747 "
                 "rows. So an absent pair is not evidence that the text was never entered. Not read: the "
                 "resource_prefetch_predictor tables in the same database, which hold Chromium's page "
                 "loading predictions."
                 " The folder webbrowser/chrome, which an LG webOS TV keeps on the volume it mounts at"
                 " /mnt/lg/cmn_data, is read as the user data folder of a browser named webOS webbrowser (field"
                 " mapped from a private sample); which app writes it is not established, and User is blank for it,"
                 " since it sits in no home folder.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Network Action Predictor*',
            '*/Library/Application Support/Google/Chrome/*/Network Action Predictor*',
            '*/.config/google-chrome/*/Network Action Predictor*',
            '*/AppData/Local/Chromium/User Data/*/Network Action Predictor*',
            '*/Library/Application Support/Chromium/*/Network Action Predictor*',
            '*/.config/chromium/*/Network Action Predictor*',
            '*/webbrowser/chrome/*/Network Action Predictor*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Network Action Predictor*',
            '*/Library/Application Support/Microsoft Edge/*/Network Action Predictor*',
            '*/.config/microsoft-edge/*/Network Action Predictor*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Network Action Predictor*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Network Action Predictor*',
            '*/.config/BraveSoftware/Brave-Browser/*/Network Action Predictor*',
            '*/AppData/Local/Vivaldi/User Data/*/Network Action Predictor*',
            '*/Library/Application Support/Vivaldi/*/Network Action Predictor*',
            '*/.config/vivaldi/*/Network Action Predictor*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Network Action Predictor*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Network Action Predictor*',
            '*/.config/opera/*/Network Action Predictor*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Network Action Predictor*',
            '*/Library/Application Support/com.operasoftware.Opera/Network Action Predictor*',
            '*/.config/opera/Network Action Predictor*',
        ),
        "output_types": "standard",
        "artifact_icon": "type",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 10,747 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 439 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (open_store, profile_stores, row_tail,
                                               table_columns)
from scripts.ilapfuncs import artifact_processor, logfunc


@artifact_processor
def chromiumNetworkActionPredictor(context):
    label = 'Chromium Network Action Predictor'
    data_list = []
    sources = []
    for store in profile_stores(context, {'Network Action Predictor'}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            if not table_columns(db, 'network_action_predictor'):
                continue
            rows = db.execute('''
                SELECT user_text, url, number_of_hits, number_of_misses
                FROM network_action_predictor ORDER BY user_text, url, id''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        tail = row_tail(store)[:3]
        for user_text, url, hits, misses in rows:
            data_list.append((user_text, url, hits, misses) + tail)
    data_headers = ('Typed Text', 'URL', 'Hits', 'Misses', 'Browser', 'Profile', 'User')
    return data_headers, data_list, '\n'.join(sources)
