"""CryptnetUrlCache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each Windows profile can hold AppData/LocalLow/Microsoft/CryptnetUrlCache with two
folders, MetaData and Content, holding a file of the same name for each cached URL.
The MetaData file records the URL, two times, an E-Tag and a size in the layout
AbdulRhman Alfaifi's analysis describes; the Content file holds what was fetched.
This reads every MetaData file, pairs it with the Content file of the same name in the
same cache folder, and reports the Content file's size, SHA-256 and first bytes.
"""

import hashlib
import os
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc

_CACHE_FOLDER = '/appdata/locallow/microsoft/cryptneturlcache/'
_HEADER_LEN = 116

__artifacts_v2__ = {
    "windowsCryptnetUrlCache": {
        "name": "CryptnetUrlCache",
        "description": "URLs recorded in the CryptnetUrlCache MetaData files of each Windows "
                       "profile, with the recorded times, E-Tag and size, and the size, SHA-256 "
                       "and first bytes of the Content file of the same name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads every file in the MetaData folder of "
                 "AppData/LocalLow/Microsoft/CryptnetUrlCache in any profile the declared path "
                 "reaches, which includes Windows/System32/config/systemprofile, "
                 "Windows/SysWOW64/config/systemprofile and the LocalService and NetworkService "
                 "folders under Windows/ServiceProfiles; Velociraptor's Windows.Forensics.CertUtil "
                 "artifact reads the cache in Users and in the systemprofile folders "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/CertUtil.yaml#L40-L43). "
                 "Phill Moore found that running certutil -urlcache -split -f wrote a Content file and "
                 "a MetaData file of the same name there (Reference: Phill Moore, 'Certutil download "
                 "artefacts', https://thinkdfir.com/2020/07/30/certutil-download-artefacts/). The "
                 "MetaData fields follow AbdulRhman Alfaifi's analysis and parser (Reference: "
                 "AbdulRhman Alfaifi, 'Certutil Artifacts Analysis', "
                 "https://u0041.co/posts/articals/certutil-artifacts-analysis/; "
                 "https://github.com/AbdulRhmanAlfaifi/CryptnetURLCacheParser/blob/5dc1ca6e8c26735923cdc110fed18c310a405b92/CryptnetUrlCacheParser.py#L1-L14, "
                 "https://github.com/AbdulRhmanAlfaifi/CryptnetURLCacheParser/blob/5dc1ca6e8c26735923cdc110fed18c310a405b92/CryptnetUrlCacheParser.py#L68-L73). "
                 "Last Downloaded (UTC) is the FILETIME at offset 0x10, which the analysis describes "
                 "as the last time the file was downloaded, and Last-Modified (UTC) the FILETIME at "
                 "0x58, which it describes as the Last-Modified header of the response; a zero time is "
                 "shown blank, and Last-Modified was zero on 19 of the 145 tested files. File Size is "
                 "the 32-bit value at 0x70, the downloaded file's size by the analysis. URL and E-Tag "
                 "are the UTF-16LE strings after the 116-byte header, whose sizes sit at 0x0C and "
                 "0x64, shown without their terminating NUL; the analysis describes the second as the "
                 "response's E-Tag header, and it is shown as stored, quotation marks included. On the "
                 "tested images every MetaData file's length was exactly 116 bytes plus the two string "
                 "sizes, every URL ended in a NUL, and File Size equalled the size of the Content file "
                 "of the same name on all 145. Last Downloaded matched that Content file's "
                 "modification time within two seconds on 46 of the 145, so what the time records "
                 "beyond the analysis's description was not established. Cache File is the name the "
                 "two files share. The analysis gives that name as the MD5 of the URL in UTF-16LE: on "
                 "the tested images that held for all 45 names without an underscore, and for none of "
                 "the 100 names with one, not even for the part before the underscore; how those are "
                 "derived was not established. Content Size, Content SHA-256 and Content Header (hex) "
                 "are the size, SHA-256 and first eight bytes of the Content file of the same name in "
                 "the same cache folder, blank when there is none; every tested MetaData file had one. "
                 "Of the 145 Content files 120 began with 3082, 15 with MSCF (4D534346) and 3 with "
                 "3003, 7 were empty, and none began with MZ (4D5A), the header Velociraptor's "
                 "artifact checks for before it reads an executable's version information "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/CertUtil.yaml#L109-L114). "
                 "Profile Folder is the part of the path before AppData, and with Cache File it "
                 "identifies the MetaData file. On af_case2_win10 there were 11 rows, 6 in "
                 "Users/IEUser and 5 in the System32 systemprofile; on lonewolf_win10 92, 5 of them "
                 "under Windows/ServiceProfiles; and on pc_mus_001_win11 42, 2 of them under "
                 "Windows/ServiceProfiles. The 145 URLs all used http and named 37 hosts, most often "
                 "ocsp.digicert.com (48) and ctldl.windowsupdate.com (22). Values not reported include "
                 "the bytes the analysis leaves unknown, at 0x00 to 0x0B, 0x18 to 0x57, 0x60 to 0x63 "
                 "and 0x68 to 0x6F; the first 32-bit value was 112 in every tested file.",
        "paths": ('*/AppData/LocalLow/Microsoft/CryptnetUrlCache/*',),
        "output_types": ["standard"],
        "artifact_icon": "certificate",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 11 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 92 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 42 rows",
        },
    },
}


def _utf16(raw):
    return raw.decode('utf-16-le', 'replace').rstrip('\x00')


def parse_metadata(data):
    """The fields of a CryptnetUrlCache MetaData file; raises ValueError when it is too short."""
    if len(data) < _HEADER_LEN:
        raise ValueError(f'{len(data)} bytes, shorter than the {_HEADER_LEN}-byte header')
    url_size, etag_size = struct.unpack_from('<I', data, 12)[0], struct.unpack_from('<I', data, 100)[0]
    if _HEADER_LEN + url_size + etag_size > len(data):
        raise ValueError('the URL and E-Tag sizes run past the end of the file')
    url_end = _HEADER_LEN + url_size
    return {'downloaded': struct.unpack_from('<Q', data, 16)[0],
            'last_modified': struct.unpack_from('<Q', data, 88)[0],
            'file_size': struct.unpack_from('<I', data, 112)[0],
            'url': _utf16(data[_HEADER_LEN:url_end]),
            'etag': _utf16(data[url_end:url_end + etag_size])}


def cache_parts(relative):
    """(cache folder key, 'metadata' or 'content', file name) of a path in a cache, or None."""
    path = '/' + relative.replace('\\', '/').lstrip('/')
    at = path.lower().find(_CACHE_FOLDER)
    if at < 0:
        return None
    rest = path[at + len(_CACHE_FOLDER):].split('/')
    if len(rest) != 2 or rest[0].lower() not in ('metadata', 'content') or not rest[1]:
        return None
    return path[:at + len(_CACHE_FOLDER)].lower(), rest[0].lower(), rest[1]


def profile_folder(relative):
    """The part of a cache file's path before AppData."""
    path = '/' + relative.replace('\\', '/').lstrip('/')
    at = path.lower().find(_CACHE_FOLDER)
    return path[1:at] if at >= 0 else os.path.dirname(path[1:])


def content_facts(path):
    """(size, SHA-256, first 8 bytes in hex) of a Content file."""
    digest = hashlib.sha256()
    first = b''
    with open(path, 'rb') as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            if not first:
                first = chunk[:8]
            digest.update(chunk)
    return os.path.getsize(path), digest.hexdigest(), first.hex().upper()


@artifact_processor
def windowsCryptnetUrlCache(context):
    data_headers = (('Last Downloaded (UTC)', 'datetime'), 'URL', 'File Size', 'E-Tag',
                    ('Last-Modified (UTC)', 'datetime'), 'Profile Folder', 'Cache File',
                    'Content Size', 'Content SHA-256', 'Content Header (hex)')
    metadata, contents = [], {}
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        parts = cache_parts(relative)
        if parts is None:
            continue
        folder, kind, name = parts
        if kind == 'metadata':
            metadata.append((relative, path, folder, name))
        else:
            contents[(folder, name.upper())] = path
    data_list = []
    sources = []
    unreadable = 0
    for relative, path, folder, name in sorted(set(metadata)):
        with open(path, 'rb') as handle:
            data = handle.read()
        try:
            fields = parse_metadata(data)
        except ValueError as ex:
            unreadable += 1
            logfunc(f'CryptnetUrlCache: {relative}: {ex}')
            continue
        sources.append(path)
        content = contents.get((folder, name.upper()))
        size = sha256 = header = ''
        if content:
            size, sha256, header = content_facts(content)
            sources.append(content)
        data_list.append((filetime_utc(fields['downloaded']), fields['url'], fields['file_size'],
                          fields['etag'], filetime_utc(fields['last_modified']),
                          profile_folder(relative), name, size, sha256, header))
    if unreadable:
        logfunc(f'CryptnetUrlCache: {unreadable} MetaData files could not be read')
    missing = sum(1 for row in data_list if row[7] == '')
    if missing:
        logfunc(f'CryptnetUrlCache: {missing} MetaData files have no Content file of the same name')
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[1]))
    return data_headers, data_list, '\n'.join(sources)
