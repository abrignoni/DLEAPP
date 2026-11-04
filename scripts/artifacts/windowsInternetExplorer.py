"""Internet Explorer 5 to 9 index.dat (MSIE Cache File) history, cache and cookie records for DLEAPP.

Author: @AlexisBrignoni, Claude.

Read with scripts/windows_msiecf.py, written from the libyal MSIE Cache File format specification and checked
record for record against libmsiecf; see the notes.
"""

import os
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, check_in_media, logfunc
from scripts.windows_msiecf import MsiecfError, fat_datetime, parse

_FILETIME_ZERO = datetime(1601, 1, 1, tzinfo=timezone.utc)
_RANGE = re.compile(r'MSHist01(\d{8})(\d{8})$', re.IGNORECASE)
_PERIODIC = re.compile(r'^:(\d{16}): ([^@]*)@(.*)$', re.DOTALL)

__artifacts_v2__ = {
    "ieHistory": {
        "name": "Internet Explorer History (index.dat)",
        "description": "URL records of Internet Explorer 5 to 9 from the History.IE5 index.dat files, the main one "
                       "and the periodic MSHist01 ones, with the times they hold and the account the record names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Internet Explorer",
        "notes": "One row per URL record of a History.IE5 index.dat: Main is the index.dat in History.IE5 itself, and the periodic files are those in MSHist01<start><end> folders, Daily when the folder's range is one day Weekly when it is seven days and Periodic for any other range (Date Range, from the folder name). Read with scripts/windows_msiecf.py, written from the libyal MSIE Cache File format specification (https://github.com/libyal/libmsiecf/blob/a99a703d190d62f6c21b6225cf84ce80037e45d5/documentation/MSIE%20Cache%20File%20(index.dat)%20format.asciidoc?plain=1#L538-L623 for the URL record): every 128-byte block from offset 0x4000 is checked for a URL, REDR or LEAK record signature (libmsiecf finds its records from the hash table and a block scan of its own; on the 25 corpus files below the two methods returned the same records), and Allocated says whether the file's allocation bitmap (#L359-L373) marks the record's blocks in use (Yes) or free (No); a record whose blocks are partly in use and partly free is skipped. On the 25 index.dat files of cfreds_hacking_case_winxp and cfreds_leakage_win7 the reader returned the same 1,361 records as libmsiecf 20260525 (its items and recovered items), with the same value in every field shown here. Only format version 5.2 is read (Internet Explorer 5 to 9); a file of another version is named in the run log and skipped. Text is decoded as Windows-1252. Index File is the index.dat a row came from and User the profile folder after Users or Documents and Settings in its path, blank outside a profile. The specification gives the record's two times per kind of file (#L1013-L1026): in the main History file both are the last visit in UTC, in a daily file the first is the last visit in UTC and the second the last visit in local time, and in a weekly file the first is the file's creation time and the second the last visit in local time. Last Visit (UTC) is therefore the first time for Main and Daily rows and blank for Weekly rows, and Last Visit (local, as stored) is the second time for Daily and Weekly rows, written as the date and time it holds, with no time zone recorded. On cfreds_hacking_case_winxp, whose SYSTEM hive gives Central Daylight Time (ActiveTimeBias 300 minutes, UTC-5), the two times of every one of the 60 Daily rows were five hours apart and those of the 85 Main rows equal on 84 and 30 milliseconds apart on the other, and on the 41 Weekly rows the second time was about 119 to 125 hours (118.9 to 125.4) before the first, varying from row to row. Account and URL come from the record's location, account@URL after a fixed prefix (a word and a colon in the main file, the date range between colons in a periodic one); the specification calls the part before @ the user name. Hits is the record's number of hits as stored. On cfreds_hacking_case_winxp the files gave 186 rows (85 Main, 60 Daily, 41 Weekly); cfreds_leakage_win7 has no History.IE5 index.dat with records. A row records that Internet Explorer kept a URL in its history, not who typed or followed it.",
        "paths": ('*/History.IE5/index.dat', '*/History.IE5/MSHist*/index.dat'),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "cfreds_hacking_case_winxp": "Windows XP | 186 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no history records)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no index.dat)",
        },
    },
    "ieCache": {
        "name": "Internet Explorer Cache (index.dat)",
        "description": "Cache records of Internet Explorer 5 to 9 from Content.IE5 index.dat files: the URL, when "
                       "the client last accessed it, the server's modification time, the cached file and, where it "
                       "is in the extraction, the file itself.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Internet Explorer",
        "notes": "One row per URL, REDR or LEAK record of a Content.IE5 index.dat (Temporary Internet Files, including the Low folder). Read with scripts/windows_msiecf.py, written from the libyal MSIE Cache File format specification (https://github.com/libyal/libmsiecf/blob/a99a703d190d62f6c21b6225cf84ce80037e45d5/documentation/MSIE%20Cache%20File%20(index.dat)%20format.asciidoc?plain=1#L538-L623 for the URL record): every 128-byte block from offset 0x4000 is checked for a URL, REDR or LEAK record signature (libmsiecf finds its records from the hash table and a block scan of its own; on the 25 corpus files below the two methods returned the same records), and Allocated says whether the file's allocation bitmap (#L359-L373) marks the record's blocks in use (Yes) or free (No); a record whose blocks are partly in use and partly free is skipped. On the 25 index.dat files of cfreds_hacking_case_winxp and cfreds_leakage_win7 the reader returned the same 1,361 records as libmsiecf 20260525 (its items and recovered items), with the same value in every field shown here. Only format version 5.2 is read (Internet Explorer 5 to 9); a file of another version is named in the run log and skipped. Text is decoded as Windows-1252. Index File is the index.dat a row came from and User the profile folder after Users or Documents and Settings in its path, blank outside a profile. For the cache the specification gives the first time as the client's last access and the second as the server's modification time, both in UTC (#L1013-L1021), shown as Last Accessed (UTC) and Server Modified (UTC). Last Checked (UTC) is the record's last checked FAT date and time (#L1104-L1136), read as UTC: it was within 2 seconds of Last Accessed on 520 of the 729 URL rows of cfreds_hacking_case_winxp and 301 of the 367 of cfreds_leakage_win7, within 10 minutes on 93 and 66 more, earlier on the other 116 of the Windows XP rows, and never about five hours away although that computer was set to UTC-5. Expires (as stored) is the record's expiration FAT date and time as stored, blank when 0 or 0xFFFFFFFF; its time zone was not established. Record Type: a REDR record holds only a location, shown as URL (#L1040-L1061); the specification describes a LEAK record as a cached URL record no longer considered part of the cache that was not removed (#L1063-L1102), and it holds a cached file name and size but no URL. Cached File Name is the record's cache folder, from the folder table in the file's header, and file name; Cached File shows that file where it is in the extraction in that folder beside the index.dat: 723 of the 724 allocated URL rows on cfreds_hacking_case_winxp and 365 of the 365 on cfreds_leakage_win7 had it. Cached File Size and Hits are as stored. Response Headers is the record's data up to the first NUL, which the specification gives as the headers of the HTTP response (#L695-L697). On cfreds_hacking_case_winxp the files gave 767 rows (729 URL, 19 REDR, 19 LEAK; 5 not allocated) and on cfreds_leakage_win7 384 rows (367 URL, 14 REDR, 3 LEAK; 5 not allocated). A row records that Internet Explorer cached a resource, not that anyone looked at it.",
        "paths": ('*/Content.IE5/index.dat', '*/Content.IE5/*/*'),
        "output_types": ["standard"],
        "artifact_icon": "archive",
        "sample_data": {
            "cfreds_hacking_case_winxp": "Windows XP | 767 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 384 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no index.dat)",
        },
    },
    "ieCookieIndex": {
        "name": "Internet Explorer Cookie Index (index.dat)",
        "description": "Cookie records of Internet Explorer 5 to 9 from the Cookies index.dat files: the account and "
                       "site the record names, the cookie file it points to, and its access and modification times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Internet Explorer",
        "notes": "One row per URL record of a Cookies index.dat (and Cookies\\\\Low). Read with scripts/windows_msiecf.py, written from the libyal MSIE Cache File format specification (https://github.com/libyal/libmsiecf/blob/a99a703d190d62f6c21b6225cf84ce80037e45d5/documentation/MSIE%20Cache%20File%20(index.dat)%20format.asciidoc?plain=1#L538-L623 for the URL record): every 128-byte block from offset 0x4000 is checked for a URL, REDR or LEAK record signature (libmsiecf finds its records from the hash table and a block scan of its own; on the 25 corpus files below the two methods returned the same records), and Allocated says whether the file's allocation bitmap (#L359-L373) marks the record's blocks in use (Yes) or free (No); a record whose blocks are partly in use and partly free is skipped. On the 25 index.dat files of cfreds_hacking_case_winxp and cfreds_leakage_win7 the reader returned the same 1,361 records as libmsiecf 20260525 (its items and recovered items), with the same value in every field shown here. Only format version 5.2 is read (Internet Explorer 5 to 9); a file of another version is named in the run log and skipped. Text is decoded as Windows-1252. Index File is the index.dat a row came from and User the profile folder after Users or Documents and Settings in its path, blank outside a profile. For cookies the specification gives the first time as the cookie's last access and the second as its modification time, both in UTC (#L1013-L1026), shown as Last Accessed (UTC) and Modified (UTC). Expires (as stored) is the record's expiration FAT date and time as stored, blank when 0 or 0xFFFFFFFF; its time zone was not established. Account and Site come from the record's location, 'Cookie:account@site/path'. Cookie File is the file name the record gives; this artifact does not read that file. Hits is as stored. On cfreds_hacking_case_winxp the user's Cookies index.dat gave 24 rows; the other Cookies index.dat files of the two tested images held no records. A row records that a cookie was kept, not that anyone chose to keep it.",
        "paths": ('*/Cookies/index.dat', '*/Cookies/Low/index.dat'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "cfreds_hacking_case_winxp": "Windows XP | 24 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no cookie records)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no index.dat)",
        },
    },
}


def _profile_user(relative):
    """The folder after Users or Documents and Settings in a path within the extraction, or ''."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings'):
            return parts[index + 1]
    return ''


def _filetime(value):
    if not value or value >= 0x7FFFFFFFFFFFFFFF:
        return ''
    try:
        return _FILETIME_ZERO + timedelta(microseconds=value // 10)
    except OverflowError:
        return ''


def _fat_utc(value):
    parts = fat_datetime(value)
    return datetime(*parts, tzinfo=timezone.utc) if parts else ''


def _fat_text(value):
    parts = fat_datetime(value)
    return '%04d-%02d-%02d %02d:%02d:%02d' % parts if parts else ''


def _local_text(value):
    stamp = _filetime(value)
    return stamp.strftime('%Y-%m-%d %H:%M:%S') if stamp else ''


def _files(context, name='index.dat'):
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isfile(path) and os.path.basename(path).lower() == name:
            relative = context.get_relative_path(path)
            try:
                with open(path, 'rb') as handle:
                    _version, directories, records = parse(handle.read())
            except (OSError, MsiecfError) as exc:
                logfunc(f'Internet Explorer: {relative} was not read ({exc})')
                continue
            yield path, relative, directories, records


def _account_and_url(location, prefix):
    """(account, url) from 'Visited: account@url' or 'Cookie:account@site/path'."""
    if location.startswith(prefix) and '@' in location:
        account, url = location[len(prefix):].split('@', 1)
        return account.strip(), url
    return '', location


@artifact_processor
def ieHistory(context):
    data_headers = (('Last Visit (UTC)', 'datetime'), 'Last Visit (local, as stored)', 'Container', 'Date Range',
                    'Account', 'URL', 'Hits', 'Allocated', 'Index File', 'User')
    data_list, sources = [], []
    for path, relative, _directories, records in _files(context):
        folder = os.path.basename(os.path.dirname(relative.replace('\\', '/')))
        matched = _RANGE.search(folder)
        if matched:
            start, end = (datetime.strptime(value, '%Y%m%d') for value in matched.groups())
            container = 'Daily' if (end - start).days == 1 else 'Weekly' if (end - start).days == 7 else 'Periodic'
            date_range = f'{start:%Y-%m-%d} to {end:%Y-%m-%d}'
        else:
            container, date_range = 'Main', ''
        rows = 0
        for record in records:
            if record['type'] != 'URL':
                continue
            location = record['location']
            if container == 'Main':
                account, url = _account_and_url(location, 'Visited:')
            else:
                periodic = _PERIODIC.match(location)
                account, url = (periodic.group(2), periodic.group(3)) if periodic else ('', location)
            utc = _filetime(record['primary']) if container in ('Main', 'Daily') else ''
            local = _local_text(record['secondary']) if container != 'Main' else ''
            data_list.append((utc, local, container, date_range, account, url, record['hits'],
                              'Yes' if record['allocated'] else 'No', relative,
                              _profile_user(relative)))
            rows += 1
        if rows:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ieCache(context):
    data_headers = (('Last Accessed (UTC)', 'datetime'), ('Server Modified (UTC)', 'datetime'),
                    ('Last Checked (UTC)', 'datetime'), 'Expires (as stored)', 'Record Type', 'URL',
                    ('Cached File', 'media'), 'Cached File Name', 'Cached File Size', 'Hits', 'Response Headers',
                    'Allocated', 'Index File', 'User')
    data_list, sources = [], []
    staged = {}
    for found in context.get_files_found():
        found = str(found)
        if os.path.isfile(found):
            parts = found.replace('\\', '/').split('/')
            staged[(os.path.dirname(os.path.dirname(found)), parts[-2].lower(), parts[-1].lower())] = found
    for path, relative, directories, records in _files(context):
        base = os.path.dirname(path)
        rows = 0
        for record in records:
            kind = record['type']
            name = record.get('filename', '')
            folder = directories[record['directory']] if 'directory' in record and record['directory'] < len(directories) else ''
            cached = '\\'.join(part for part in (folder, name) if part) if name else ''
            media = ''
            if name and folder:
                file_path = staged.get((base, folder.lower(), name.lower()))
                if file_path:
                    media = check_in_media(file_path, name) or ''
            if kind == 'URL':
                headers = record['data'].split(b'\x00')[0].decode('cp1252', 'replace').strip()
                data_list.append((_filetime(record['primary']), _filetime(record['secondary']),
                                  _fat_utc(record['last_checked']), _fat_text(record['expiration']), kind,
                                  record['location'], media, cached, record['size'], record['hits'], headers,
                                  'Yes' if record['allocated'] else 'No', relative,
                                  _profile_user(relative)))
            elif kind == 'REDR':
                data_list.append(('', '', '', '', kind, record['location'], '', '', '', '', '',
                                  'Yes' if record['allocated'] else 'No', relative,
                                  _profile_user(relative)))
            else:
                data_list.append(('', '', '', '', kind, '', media, cached, record['size'], '', '',
                                  'Yes' if record['allocated'] else 'No', relative,
                                  _profile_user(relative)))
            rows += 1
        if rows:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ieCookieIndex(context):
    data_headers = (('Last Accessed (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'Expires (as stored)',
                    'Account', 'Site', 'Cookie File', 'Hits', 'Allocated', 'Index File', 'User')
    data_list, sources = [], []
    for path, relative, _directories, records in _files(context):
        rows = 0
        for record in records:
            if record['type'] != 'URL':
                continue
            account, site = _account_and_url(record['location'], 'Cookie:')
            data_list.append((_filetime(record['primary']), _filetime(record['secondary']),
                              _fat_text(record['expiration']), account, site, record['filename'], record['hits'],
                              'Yes' if record['allocated'] else 'No', relative,
                              _profile_user(relative)))
            rows += 1
        if rows:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
