"""Windows Run and RunOnce autostart keys parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange artifact that reads the same registry
keys; the implementation reads the keys directly and is not ported from that
artifact.
"""

import os

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The Run and RunOnce keys list programs set to start automatically. The
# machine-wide entries live in the SOFTWARE hive under
# Microsoft\Windows\CurrentVersion\Run and RunOnce, with the keys 32-bit
# applications write on 64-bit Windows under WOW6432Node at the hive's root, and
# the per-user entries in each NTUSER.DAT under
# Software\Microsoft\Windows\CurrentVersion\Run and RunOnce. A RunOnce value is
# deleted before its command runs, so that key is often empty at acquisition time.
# These are common autostart and persistence locations.

# (Key label for the row, subkey path under the hive root)
_SOFTWARE_KEYS = (
    ('Run', r"Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce', r"Microsoft\Windows\CurrentVersion\RunOnce"),
    ('Run (Wow6432Node)', r"WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce (Wow6432Node)', r"WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
)
_NTUSER_KEYS = (
    ('Run', r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce', r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
)

__artifacts_v2__ = {
    "runKeys": {
        "name": "Run and RunOnce Keys",
        "description": "Autostart entries from the Windows registry Run and "
                       "RunOnce keys, machine-wide from the SOFTWARE hive and "
                       "per user from each NTUSER.DAT.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per value in the Windows Run and RunOnce autostart keys."
                 " The machine-wide keys are read from the SOFTWARE hive under "
                 "Microsoft\\Windows\\CurrentVersion\\Run and RunOnce and under "
                 "WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run and RunOnce, "
                 "where Microsoft says HKEY_LOCAL_MACHINE\\Software is redirected "
                 "for 32-bit applications on 64-bit Windows (Reference: Microsoft,"
                 " 'Registry Redirector', "
                 "https://learn.microsoft.com/en-us/windows/win32/winprog64/registry-redirector)."
                 " The per-user keys are read from each NTUSER.DAT under "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Run and RunOnce only: "
                 "Microsoft lists HKEY_CURRENT_USER\\SOFTWARE as shared, not "
                 "redirected (Reference: Microsoft, 'Registry Keys Affected by "
                 "WOW64', "
                 "https://learn.microsoft.com/en-us/windows/win32/winprog64/shared-registry-keys),"
                 " and no NTUSER.DAT on pc_mus_001_win11, af_case2_win10 or "
                 "lonewolf_win10 has a Software\\Wow6432Node Run or RunOnce key. "
                 "The hive is named in Source File. Name is the value name as "
                 "stored and Command is the value data as stored, neither "
                 "interpreted. Key records which key an entry came from, Run or "
                 "RunOnce, with (Wow6432Node) appended for the WOW6432Node keys; "
                 "on an image whose entries all sit in one key the Key column is "
                 "constant. The WOW6432Node Run key holds 1 value on "
                 "pc_mus_001_win11, its Run and RunOnce keys hold 1 value each on "
                 "lonewolf_win10, and both are present and empty on "
                 "af_case2_win10. Scope is Machine for the SOFTWARE hive and User "
                 "for an NTUSER.DAT, and is constant on an image whose entries all"
                 " come from one of the two. User is taken from the NTUSER.DAT "
                 "path and is blank on every machine-wide row. By default a "
                 "RunOnce value is deleted before its command runs, so that key is"
                 " often empty at acquisition time and a hive can contribute no "
                 "RunOnce rows. These are common autostart and persistence "
                 "locations: the presence of an entry does not establish that the "
                 "program ran, and the absence of an entry is not evidence that a "
                 "program was not set to start automatically. Reading the hives "
                 "requires the python-registry package. The parser reads offline "
                 "hives and does not replay their transaction logs (.LOG1/.LOG2). "
                 "Key layout and the RunOnce deletion behavior: Microsoft, 'Run "
                 "and RunOnce Registry Keys', "
                 "https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys."
                 " These keys as a persistence location: MITRE ATT&CK T1547.001, "
                 "https://attack.mitre.org/techniques/T1547/001/.",
        "paths": (
            '*/Windows/System32/config/SOFTWARE',
            '*/Users/*/NTUSER.DAT',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "play",
        "sample_data": {
                     "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
                     "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
                     "lonewolf_win10": "Windows 10 Education build 16299 | 10 rows",
                 },
    },
}


def _user_from_path(source):
    parts = source.replace('\\', '/').split('/')
    for index, part in enumerate(parts):
        if part.lower() == 'users' and index + 1 < len(parts):
            return parts[index + 1]
    return ''


def _open(reg, path):
    try:
        return reg.open(path)
    except Registry.RegistryKeyNotFoundException:
        return None


def _run_rows(reg, key_defs, scope, user, relative_source):
    """Yield one row tuple for every named value under each Run/RunOnce key."""
    for key_label, key_path in key_defs:
        key = _open(reg, key_path)
        if key is None:
            continue
        for value in key.values():
            name = value.name()
            if not name:
                continue
            command = value.value()
            if not isinstance(command, str):
                command = str(command)
            yield (name, command, key_label, scope, user, relative_source)


@artifact_processor
def runKeys(context):
    data_headers = ('Name', 'Command', 'Key', 'Scope', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Run and RunOnce Keys: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).upper() in ('SOFTWARE', 'NTUSER.DAT')]:
        relative_source = context.get_relative_path(source)
        is_software = os.path.basename(source).upper() == 'SOFTWARE'
        key_defs = _SOFTWARE_KEYS if is_software else _NTUSER_KEYS
        scope = 'Machine' if is_software else 'User'
        user = '' if is_software else _user_from_path(source)
        rows_here = 0
        try:
            reg = Registry.Registry(source)
            for row in _run_rows(reg, key_defs, scope, user, relative_source):
                data_list.append(row)
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Run and RunOnce Keys: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
