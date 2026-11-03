__artifacts_v2__ = {
    "chromiumCacheRecords": {
        "name": "Chromium Cache Records",
        "description": "Entries of the HTTP disk cache of Google Chrome, Microsoft Edge, Brave, Vivaldi and "
                       "Chromium profiles on Windows: cached URL, HTTP status, content type, body size, the "
                       "entry's created and last used times, the request and response times, and the cached "
                       "picture, video or audio.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "NOTES_CACHE",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Cache/*',
            '*/AppData/Local/Chromium/User Data/*/Cache/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Cache/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Cache/*',
            '*/AppData/Local/Vivaldi/User Data/*/Cache/*',
        ),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {},
    },
}

import os
from urllib.parse import urlsplit

from scripts.chromium import blockfile_cache
from scripts.chromium.browser_profiles import row_tail
from scripts.chromium.http_cache import parse_response_info, split_key, stored_body
from scripts.chromium.simple_cache import base_time_to_datetime
from scripts.chromium.web_storage import profile_folders
from scripts.ilapfuncs import artifact_processor, check_in_embedded_media, logfunc

# The cache folder inside a profile: Cache_Data inside Cache from Chrome 91, Cache
# itself before.
_CACHE_FOLDERS = ('Cache/Cache_Data', 'Cache')
_MEDIA_TYPES = ('image/', 'video/', 'audio/')


def _host(url):
    try:
        return urlsplit(url).hostname or ''
    except ValueError:
        return ''


def _media(entry, folder, content_type, headers, extra_flags):
    """The checked-in body of a picture, video or audio entry, or ''."""
    if not content_type.startswith(_MEDIA_TYPES) or entry.body_size <= 0:
        return ''
    body = stored_body(entry.read_body(), extra_flags,
                       headers.get('content-encoding', '').strip().lower())
    if not body:
        return ''
    extension = content_type.split('/', 1)[1].split('+')[0] or None
    return check_in_embedded_media(entry.body_source or folder, body,
                                   force_type=content_type, force_extension=extension) or ''


@artifact_processor
def chromiumCacheRecords(context):
    label = 'Chromium Cache Records'
    data_list = []
    sources = []
    for folder_name in _CACHE_FOLDERS:
        for store in profile_folders(context, folder_name, label):
            index = os.path.join(store.path, 'index')
            if not os.path.isfile(index):
                continue
            files = [os.path.join(store.path, name) for name in sorted(os.listdir(store.path))]
            rows = 0
            for entry in blockfile_cache.iter_entries(files, folder_names=(os.path.basename(store.path),)):
                prefix, isolation, url = split_key(entry.key)
                parsed = parse_response_info(entry.response_info)
                if parsed is None:
                    request_time = response_time = None
                    status_line, headers, extra_flags = '', {}, 0
                else:
                    request_time, response_time, status_line, headers, extra_flags = parsed
                content_type = headers.get('content-type', '').split(';')[0].strip().lower()
                pieces = status_line.split()
                status = pieces[1] if len(pieces) > 1 and pieces[0].startswith('HTTP/') else ''
                data_list.append((entry.last_used, entry.created, base_time_to_datetime(response_time),
                                  base_time_to_datetime(request_time), url, _host(url), status,
                                  content_type, entry.body_size,
                                  _media(entry, store.path, content_type, headers, extra_flags), entry.reuse_count,
                                  isolation, prefix) + row_tail(store))
                rows += 1
            if rows:
                sources.append(index)
            else:
                logfunc(f'{label}: {store.relative} has no blockfile index with entries')
    data_headers = (('Last Used', 'datetime'), ('Created', 'datetime'), ('Response Time', 'datetime'),
                    ('Request Time', 'datetime'), 'URL', 'Host', 'HTTP Status', 'Content Type',
                    'Body Size (bytes)', ('Cached Media', 'media'), 'Reuse Count', 'Isolation Key',
                    'Key Prefix', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
