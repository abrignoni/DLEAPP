"""Windows UserAssist parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange UserAssist artifact; the implementation
reads the value structure directly and is not ported from that artifact.

The 72-byte Windows 7+ Count value layout (session id @0, run count @4, focus
count @8, focus time ms @12, last-execution FILETIME @60) and the ROT13 name
encoding are sourced from public UserAssist research (see the artifact notes).
"""

import codecs
import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Explorer records GUI program launches per user under
# NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist.
# Each GUID subkey has a Count subkey whose values are ROT13-encoded program
# names with a fixed binary structure holding the run count, focus count and
# focus time, and the last execution time as a FILETIME.

_UA_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
_EPOCH_1601 = datetime(1601, 1, 1, tzinfo=timezone.utc)

__artifacts_v2__ = {
    "userAssist": {
        "name": "UserAssist",
        "description": "GUI program launches recorded per user in the Explorer "
                       "UserAssist keys: the program, its run count, focus count "
                       "and focus time, and the last time it was executed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each NTUSER.DAT, named in Source File. Program is the "
                 "value name with its ROT13 encoding reversed and is shown as "
                 "stored; it is a path or a KnownFolder-GUID path, and does not by "
                 "itself establish who ran it. Run Count, Focus Count and Focus "
                 "Time (ms) are read from the fixed 72-byte Windows 7+ Count "
                 "structure at offsets 4, 8 and 12. Last Executed (UTC) is the "
                 "FILETIME at offset 60, decoded to UTC, and is blank when the "
                 "structure recorded no time (a zero FILETIME). Entries whose data "
                 "is not the 72-byte structure, including the UEME_CTLSESSION "
                 "control value, are skipped. UserAssist Key (GUID) is the parent "
                 "GUID as stored, not interpreted. Reading the hives requires the "
                 "python-registry package. Structure and ROT13 encoding: Kaspersky "
                 "Securelist, 'What is UserAssist and how to use it in IR "
                 "activities?', "
                 "https://securelist.com/userassist-artifact-forensic-value-for-incident-response/116911/",
        "paths": (r"*/Users/*/NTUSER.DAT",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 94 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 45 rows",
        },
    },
}


def _utc_from_filetime(value):
    if not value:
        return ''
    try:
        return _EPOCH_1601 + timedelta(microseconds=int(value) / 10)
    except (OverflowError, TypeError, ValueError):
        return ''


def _rot13(name):
    try:
        return codecs.decode(name, 'rot_13')
    except (TypeError, ValueError):
        return name


def _user_assist_key(hive_path):
    reg = Registry.Registry(hive_path)
    try:
        return reg.open(_UA_PATH)
    except Registry.RegistryKeyNotFoundException:
        return None


@artifact_processor
def userAssist(context):
    data_headers = (('Last Executed (UTC)', 'datetime'), 'Program', 'Run Count',
                    'Focus Count', 'Focus Time (ms)', 'UserAssist Key (GUID)',
                    'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('UserAssist: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).upper().endswith('NTUSER.DAT')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            root = _user_assist_key(source)
            if root is None:
                continue
            for guid in root.subkeys():
                try:
                    count = guid.subkey('Count')
                except Registry.RegistryKeyNotFoundException:
                    continue
                for value in count.values():
                    data = value.value()
                    if not isinstance(data, bytes) or len(data) != 72:
                        continue
                    run_count, focus_count, focus_ms = struct.unpack_from('<III', data, 4)
                    filetime = struct.unpack_from('<Q', data, 60)[0]
                    data_list.append((
                        _utc_from_filetime(filetime), _rot13(value.name()),
                        run_count, focus_count, focus_ms, guid.name(),
                        relative_source))
                    rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'UserAssist: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
