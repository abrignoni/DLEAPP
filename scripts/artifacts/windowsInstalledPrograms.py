"""Installed programs from the Windows Uninstall registry keys, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "installedPrograms": {
        "name": "Installed Programs (Uninstall Keys)",
        "description": "Entries in the Windows Uninstall registry keys, machine-wide in the "
                       "SOFTWARE hive (including the 32-bit view) and per user in each "
                       "NTUSER.DAT, with name, version, publisher, install location and "
                       "InstallDate as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads every subkey of Microsoft\\Windows\\CurrentVersion\\Uninstall in the SOFTWARE "
                 "hive, the same key under Wow6432Node (reported as the 32-bit view), and "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall in each NTUSER.DAT, where User "
                 "is the folder name under Users. A row is what was written under an Uninstall key; "
                 "that the program was still present at acquisition is not established. A subkey with "
                 "no DisplayName is skipped and the number skipped per hive is written to the run log:"
                 " 26, 40 and 26 in the SOFTWARE hives of pc_mus_001_win11, af_case2_win10 and "
                 "lonewolf_win10. For a Windows Installer product, Microsoft documents InstallDate as "
                 "the last time the product received service, replaced each time a patch is applied or"
                 " removed or the product is repaired, and as the install time only when it received "
                 "none; an entry not created by Windows Installer is outside that description, so "
                 "Install Date is reported as stored. Microsoft documents EstimatedSize as determined "
                 "and set by Windows Installer, without a unit, so it is also reported as stored. "
                 "System Component shows Yes where the SystemComponent value is 1. Key Last Written is"
                 " when the subkey was last written, which is not established as the install time. "
                 "Reference: Microsoft, 'Windows Installer Properties for the Uninstall Registry Key',"
                 " https://learn.microsoft.com/en-us/windows/win32/msi/uninstall-registry-key.",
        "paths": (
            '*/Windows/System32/config/SOFTWARE',
            '*/Users/*/NTUSER.DAT',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "list",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 22 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 19 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 25 rows",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_key,
                                      user_from_path, value_of)

# (view label, key path under the hive root)
_SOFTWARE_VIEWS = (
    ('Machine', r'Microsoft\Windows\CurrentVersion\Uninstall'),
    ('Machine, 32-bit view', r'Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
)
_NTUSER_VIEWS = (
    ('User', r'Software\Microsoft\Windows\CurrentVersion\Uninstall'),
)


def _text(value):
    if value is None:
        return ''
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if v not in (None, ''))
    return str(value)


def _program_rows(reg, views, user, relative):
    kept = skipped = 0
    rows = []
    for view, path in views:
        uninstall = open_key(reg, path)
        for entry in (uninstall.subkeys() if uninstall else []):
            name = _text(value_of(entry, 'DisplayName'))
            if not name:
                skipped += 1
                continue
            kept += 1
            system_component = value_of(entry, 'SystemComponent')
            rows.append((
                key_written_utc(entry),
                _text(value_of(entry, 'InstallDate')),
                name,
                _text(value_of(entry, 'DisplayVersion')),
                _text(value_of(entry, 'Publisher')),
                _text(value_of(entry, 'InstallLocation')),
                _text(value_of(entry, 'InstallSource')),
                _text(value_of(entry, 'UninstallString')),
                _text(value_of(entry, 'EstimatedSize')),
                'Yes' if system_component == 1 else '',
                view,
                user,
                entry.name(),
                relative,
            ))
    return rows, kept, skipped


@artifact_processor
def installedPrograms(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Install Date (as stored)', 'Name',
                    'Version', 'Publisher', 'Install Location', 'Install Source',
                    'Uninstall String', 'Estimated Size (as stored)', 'System Component',
                    'Registry View', 'User', 'Key Name', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Installed Programs: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'SOFTWARE', 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        is_software = os.path.basename(path).upper() == 'SOFTWARE'
        try:
            rows, _kept, skipped = _program_rows(
                Registry.Registry(path), _SOFTWARE_VIEWS if is_software else _NTUSER_VIEWS,
                '' if is_software else user_from_path(path), relative)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Installed Programs: could not read {relative}: {exc}')
            continue
        if skipped:
            logfunc(f'Installed Programs: {skipped} Uninstall subkey(s) with no DisplayName '
                    f'skipped in {relative}')
        data_list.extend(rows)
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
