"""Windows user Credential Manager files (metadata, not decrypted) for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each file in a user profile's Microsoft\\Credentials folder wraps one DPAPI blob. The blob's header, which is not
encrypted, names the master key that protects it, a description and the cipher and hash it uses. This artifact
does not decrypt the blob; it reports only the header, and whether the named master key's file is in the
extraction.
"""

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import user_from_path

try:
    from scripts.vendor.dpapiprobe.credvault import CredentialFile
except ImportError:
    CredentialFile = None

_LABEL = 'Windows User Credential Files'
# Microsoft's ALG_ID values for the identifiers dpapiprobe handles (see notes).
_ALGORITHMS = {0x8004: 'CALG_SHA1', 0x8009: 'CALG_HMAC', 0x800C: 'CALG_SHA_256', 0x800E: 'CALG_SHA_512',
               0x6603: 'CALG_3DES', 0x660E: 'CALG_AES_128', 0x660F: 'CALG_AES_192', 0x6610: 'CALG_AES_256'}

__artifacts_v2__ = {
    "userCredentialFiles": {
        "name": "Windows User Credential Files",
        "description": "Credential Manager files in user profiles, not decrypted: the master key each needs, its "
                       "description, cipher and hash, and whether that master key's file is in the extraction.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none (vendored dpapiprobe)",
        "category": "Windows",
        "notes": "One row per file in the Microsoft\\Credentials folder of a user profile's AppData\\Local or AppData\\Roaming. The files of the LocalSystem, LocalService and NetworkService profiles are decrypted by Windows System Credential Manager and are not listed here. Each file holds a DPAPI blob. This artifact does not decrypt it: it reads the blob's header, which is stored in the clear, with the vendored dpapiprobe library (scripts/vendor/dpapiprobe, https://github.com/abrignoni/dpapiprobe/blob/ee51cba374c1f703577d916df43af03f9b9cdd10/dpapiprobe/blob.py#L31-L48). Master Key GUID is the GUID of the master key the blob names, Description the blob's description, and Cipher and Hash its algorithm identifiers, given by their ALG_ID name from Microsoft's table (https://github.com/MicrosoftDocs/win32/blob/ca74834093fa2f82c608f87b28f030b2f88462b1/desktop-src/SecCrypto/alg-id.md#L21-L65) or in hex when the value is not one of the eight this artifact names. Master Key File Found is Yes when a file named with that GUID is in a Microsoft\\Protect\\<SID> folder of the same profile's AppData\\Roaming, and User SID is the name of that folder; the master key file is itself protected and is not opened here. Created (UTC) and Modified (UTC) are the created and modified times the tool's image reader reports for the file, as in DPAPI Master Key Files; they are blank for a folder or archive input, whose copy's times are not the evidence's (exercised with a unit test only). On pc_mus_001_win11 the three files' times equalled the $STANDARD_INFORMATION created and modified times The Sleuth Kit 4.15.0 istat reports. Location is Local or Roaming, from the folder the file is in, and User the profile folder. On the tested images the master key file was found for all 17 user-profile files; the description was Local Credential Data on the 15 Local files and Enterprise Credential Data on the 2 Roaming files (lonewolf_win10); the cipher and hash were CALG_AES_256 and CALG_SHA_512 on 12 files and CALG_3DES and CALG_SHA1 on 5 (ou_ransomware_server2022 and szechuan_win10). The blob's flags were 0x20000000 on every tested file, so they are not shown. A file that does not read as a DPAPI blob is logged and skipped. A row records that a saved credential file exists in the profile, not what it holds, whom it is for or when it was used.",
        "paths": ('*/AppData/Local/Microsoft/Credentials/*',
                  '*/AppData/Roaming/Microsoft/Credentials/*',
                  '*/AppData/Roaming/Microsoft/Protect/*/*'),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows (2 Roaming)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no user-profile credential files)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no user-profile credential files)",
        },
    },
}


def _instant(value):
    """A FileInfo time (seconds since 1970, UTC) as an aware datetime, or ''."""
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _algorithm(value):
    return _ALGORITHMS.get(value, f'0x{value:04X}')


def _profile_root(relative):
    """The path up to and including AppData, which pairs a credential file with its own profile's Protect folder."""
    parts = relative.replace('\\', '/').split('/')
    lowered = [part.lower() for part in parts]
    return '/'.join(parts[:lowered.index('appdata') + 1]).lower() if 'appdata' in lowered else ''


@artifact_processor
def userCredentialFiles(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'File', 'Location', 'Master Key GUID', 'Master Key File Found', 'User SID', 'Description',
                    'Cipher', 'Hash', 'User')
    data_list = []
    sources = []
    if CredentialFile is None:
        logfunc(f'{_LABEL}: the vendored dpapiprobe library is not available')
        return data_headers, data_list, ''
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    # Only a disk image gives the evidence's own times; a folder or archive gives the times of the copy.
    from_image = hasattr(seeker, 'stream_list')
    found = [str(f) for f in context.get_files_found() if os.path.isfile(str(f))]
    keys = {}
    for path in found:
        relative = context.get_relative_path(path)
        parts = relative.replace('\\', '/').split('/')
        if len(parts) >= 3 and parts[-3].lower() == 'protect' and parts[-2].upper().startswith('S-1-'):
            keys[(_profile_root(relative), parts[-1].lower())] = parts[-2]
    for path in sorted(found):
        relative = context.get_relative_path(path)
        parts = relative.replace('\\', '/').split('/')
        lowered = [part.lower() for part in parts]
        if (len(parts) < 2 or lowered[-2] != 'credentials' or 'systemprofile' in lowered
                or 'serviceprofiles' in lowered):
            continue
        try:
            with open(path, 'rb') as handle:
                blob = CredentialFile(handle.read()).blob
        except (OSError, ValueError, IndexError) as exc:
            logfunc(f'{_LABEL}: {relative} did not read as a credential file ({type(exc).__name__})')
            continue
        sid = keys.get((_profile_root(relative), blob.mk_guid.lower()))
        info = infos.get(path)
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        location = 'Local' if 'local' in lowered[-5:-2] else 'Roaming'
        data_list.append((created, modified, parts[-1], location, blob.mk_guid, 'Yes' if sid else 'No', sid or '', blob.description,
                          _algorithm(blob.alg_crypt), _algorithm(blob.alg_hash),
                          user_from_path(context.get_relative_path(path))))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
