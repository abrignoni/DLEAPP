"""Microsoft Office file and place most-recently-used lists, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "officeFileMru": {
        "name": "Office File and Place MRU",
        "description": "Documents and folders listed in each Office application's File MRU "
                       "and Place MRU registry lists in NTUSER.DAT, with the time stored in "
                       "each entry.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads each Software\\Microsoft\\Office\\<version>\\<application> key in each NTUSER.DAT "
                 "for File MRU and Place MRU subkeys, including those under User MRU\\<account key>, "
                 "and reports each value named Item N; other values in those keys are not reported. An"
                 " item's data is a run of bracketed fields, an asterisk and the path; an item whose "
                 "text lacks that form is reported with that text as Path and no Entry Time. Entry "
                 "Time is the field beginning with T, read as a hexadecimal FILETIME as RegRipper's "
                 "msoffice plugin reads it; on every item on the registered images it is the second of"
                 " three fields, the one that plugin reads. What event that time records is not "
                 "established: on lonewolf_win10 two Place MRU entries have a shortcut of the same "
                 "name in the user's Office Recent folder, and their stored times differ from those "
                 "shortcuts' modification times by 4.4 and 21.5 hours. Account Key is the User MRU "
                 "subkey name as stored and is blank for a list outside User MRU. No NTUSER.DAT on "
                 "pc_mus_001_win11 or af_case2_win10 has a Software\\Microsoft\\Office key. On "
                 "lonewolf_win10 all nine items are under Office Version 16.0 in one user's hive, so "
                 "Office Version and User each hold one value there. Reference: Harlan Carvey, "
                 "'RegRipper3.0 msoffice.pl', "
                 "https://github.com/keydet89/RegRipper3.0/blob/ec96dd4a6a5c3ea70d8fece9b47a374f83582335/plugins/msoffice.pl#L303-L310.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Office key in any NTUSER.DAT)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Office key in any NTUSER.DAT)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 9 rows",
        },
    },
}

import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, filetime_utc, found_hives, open_key,
                                      user_from_path)

_OFFICE = r'Software\Microsoft\Office'
_ITEM = re.compile(r'^Item \d+$')
_ENTRY = re.compile(r'^((?:\[[^\]]*\])*)\*(.*)$', re.S)


def _parse_entry(data):
    """(time, path) from '[F...][T<hex FILETIME>][O...]*<path>', or ('', data)."""
    match = _ENTRY.match(data or '')
    if not match:
        return '', data or ''
    when = ''
    for token in re.findall(r'\[([^\]]*)\]', match.group(1)):
        if token[:1] == 'T':
            try:
                when = filetime_utc(int(token[1:], 16))
            except ValueError:
                when = ''
    return when, match.group(2)


def _lists(reg):
    """(office version, application, account key, list name, key) for every MRU list."""
    office = open_key(reg, _OFFICE)
    for version in (office.subkeys() if office else []):
        for app in version.subkeys():
            base = rf'{_OFFICE}\{version.name()}\{app.name()}'
            for kind in ('File MRU', 'Place MRU'):
                legacy = open_key(reg, rf'{base}\{kind}')
                if legacy is not None:
                    yield version.name(), app.name(), '', kind, legacy
            user_mru = open_key(reg, rf'{base}\User MRU')
            for account in (user_mru.subkeys() if user_mru else []):
                for kind in ('File MRU', 'Place MRU'):
                    key = open_key(reg, rf'{base}\User MRU\{account.name()}\{kind}')
                    if key is not None:
                        yield version.name(), app.name(), account.name(), kind, key


@artifact_processor
def officeFileMru(context):
    data_headers = (('Entry Time (UTC)', 'datetime'), 'Path', 'Application', 'Office Version',
                    'List', 'Item', 'Account Key', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Office File and Place MRU: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(path)
        try:
            for version, app, account, kind, key in _lists(Registry.Registry(path)):
                for value in key.values():
                    if not _ITEM.match(value.name()):
                        continue
                    data = value.value()
                    when, target = _parse_entry(data if isinstance(data, str) else '')
                    data_list.append((when, target, app, version, kind, value.name(),
                                      account, user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Office File and Place MRU: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
