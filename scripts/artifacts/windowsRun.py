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
from scripts.windows_registry import open_hive, user_from_path

# The Run and RunOnce keys list programs set to start automatically. The
# machine-wide entries live in the SOFTWARE hive under
# Microsoft\Windows\CurrentVersion\Run and RunOnce, with the keys 32-bit
# applications write on 64-bit Windows under WOW6432Node at the hive's root, and
# the per-user entries in each NTUSER.DAT under
# Software\Microsoft\Windows\CurrentVersion\Run and RunOnce. A RunOnce value is
# deleted before its command runs, so a value whose command has run is no longer there.
# These are common autostart and persistence locations. Two more are read with them:
# the Policies\Explorer\Run key, machine-wide and per user, and the Load value of
# each user's Software\Microsoft\Windows NT\CurrentVersion\Windows key.

# (Key label for the row, subkey path under the hive root)
_SOFTWARE_KEYS = (
    ('Run', r"Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce', r"Microsoft\Windows\CurrentVersion\RunOnce"),
    ('Run (Wow6432Node)', r"WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce (Wow6432Node)', r"WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"),
    ('Policies\\Explorer\\Run', r"Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
)
_NTUSER_KEYS = (
    ('Run', r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ('RunOnce', r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ('Policies\\Explorer\\Run', r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
)
# (Key label for the row, subkey path under the hive root, names of the values read from it,
# in lower case): a key that holds other values too, of which only these are autostart entries.
_NTUSER_VALUES = (
    ('Windows NT\\CurrentVersion\\Windows', r"Software\Microsoft\Windows NT\CurrentVersion\Windows",
     ('load',)),
)

__artifacts_v2__ = {
    "runKeys": {
        "name": "Run and RunOnce Keys",
        "description": "Autostart entries from the Windows registry Run and "
                       "RunOnce keys, the Policies\\Explorer\\Run keys and each user's Load "
                       "value, machine-wide from the SOFTWARE hive and "
                       "per user from each NTUSER.DAT.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per value in the Windows Run and RunOnce autostart keys and in the "
                 "Policies\\Explorer\\Run keys, and one for the Load value of each user's Windows "
                 "NT\\CurrentVersion\\Windows key."
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
                 " and no NTUSER.DAT under Users on pc_mus_001_win11, af_case2_win10, "
                 "lonewolf_win10 or szechuan_win10 has a Software\\Wow6432Node Run or RunOnce key. "
                 "The hive is named in Source File. Source File is kept because Scope and User "
                 "identify a hive only while the extraction holds each hive once: the declared "
                 "paths also match a second copy, such as one under a Windows.old folder, which "
                 "would share its Scope and User with the first. No tested image holds a second "
                 "copy, and on windows11_arm_known_20261001, with one SOFTWARE hive and one "
                 "NTUSER.DAT, Scope alone separates the two files. Name is the value name as "
                 "stored and Command is the value data as stored, neither "
                 "interpreted. Key records which key an entry came from, Run or "
                 "RunOnce, with (Wow6432Node) appended for the WOW6432Node keys, "
                 "Policies\\Explorer\\Run, or Windows NT\\CurrentVersion\\Windows for a Load value; "
                 "on an image whose entries all sit in one key the Key column is "
                 "constant. The WOW6432Node Run key holds 1 value on "
                 "pc_mus_001_win11, its Run and RunOnce keys hold 1 value each on "
                 "lonewolf_win10, and both are present and empty on af_case2_win10 and "
                 "szechuan_win10. Policies\\Explorer\\Run is read from the SOFTWARE hive under "
                 "Microsoft\\Windows\\CurrentVersion and from each NTUSER.DAT under "
                 "Software\\Microsoft\\Windows\\CurrentVersion; MITRE ATT&CK describes the values of "
                 "these two keys as created by policy settings that specify startup programs (MITRE "
                 "ATT&CK T1547.001, "
                 "https://attack.mitre.org/techniques/T1547/001/). "
                 "The WOW6432Node path of the machine-wide key is not read: Microsoft's 'Registry "
                 "Keys Affected by WOW64' page lists "
                 "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies as shared "
                 "(https://learn.microsoft.com/en-us/windows/win32/winprog64/shared-registry-keys), "
                 "and none of the five tested SOFTWARE hives holds a Policies\\Explorer\\Run key "
                 "under WOW6432Node. The Load value of each NTUSER.DAT's Software\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\Windows key is read, matched by name without case, and that "
                 "key's other values are not reported; MITRE ATT&CK describes programs listed in "
                 "that value as run automatically for the logged-on user "
                 "(https://attack.mitre.org/techniques/T1547/001/). "
                 "On lonewolf_win10 the machine-wide Policies\\Explorer\\Run key holds 1 value, 1 of "
                 "that image's 11 rows; no other public image holds either Policies\\Explorer\\Run "
                 "key, and no NTUSER.DAT under Users on the four public images holds a Load value. "
                 "On windows11_arm_known_20261001, known data made on a Windows 11 build 26200 "
                 "ARM64 virtual machine on 1 October 2026, one made-up value was added with reg.exe "
                 "to the machine-wide Policies\\Explorer\\Run key, one to the user's, and a Load "
                 "value to the user's Windows key, and the hives were saved before the three were "
                 "removed; 3 of that capture's 5 rows are those values, each with the command "
                 "written. Whether Windows starts the commands in these values was not tested. "
                 "Scope is Machine for the SOFTWARE hive and User "
                 "for an NTUSER.DAT, and is constant on an image whose entries all"
                 " come from one of the two. User is the folder name under Users in the "
                 "NTUSER.DAT's path within the extraction and is blank on every machine-wide "
                 "row. By default a "
                 "RunOnce value is deleted before its command runs, so a RunOnce value whose "
                 "command has run is no longer in the key, and a hive can contribute no RunOnce "
                 "rows. These are common autostart and persistence "
                 "locations: the presence of an entry does not establish that the "
                 "program ran, and the absence of an entry is not evidence that a "
                 "program was not set to start automatically. Reading the hives "
                 "requires the python-registry package. A dirty hive, one whose base block's two "
                 "sequence numbers differ, is read after the entries in its .LOG1 and .LOG2 "
                 "transaction logs that continue its sequence are applied, following Maxim "
                 "Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither "
                 "is a replay that would give a key an earlier last-written time than the hive "
                 "already holds, a check added here beyond the specification; the run log names "
                 "each hive replayed, with the sequence numbers applied, and each dirty hive "
                 "read as it is, with the reason. "
                 "Key layout and the RunOnce deletion behavior: Microsoft, 'Run "
                 "and RunOnce Registry Keys', "
                 "https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys."
                 " These keys as a persistence location: MITRE ATT&CK T1547.001, "
                 "https://attack.mitre.org/techniques/T1547/001/.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "play",
        "sample_data": {
                     "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 9 rows",
                     "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
                     "lonewolf_win10": "Windows 10 Education build 16299 | 11 rows",
                     "szechuan_win10": "Windows 10 2004 build 19041 | 11 rows",
                     "windows11_arm_known_20261001": "Windows 11 build 26200 | 5 rows",
                 },
    },
}


def _open(reg, path):
    try:
        return reg.open(path)
    except Registry.RegistryKeyNotFoundException:
        return None


def _run_rows(reg, key_defs, scope, user, relative_source, value_defs=()):
    """Yield one row tuple for every named value under each key of key_defs, and for each
    value named in value_defs that its key holds."""
    for key_label, key_path, wanted in ([(label, path, None) for label, path in key_defs]
                                        + list(value_defs)):
        key = _open(reg, key_path)
        if key is None:
            continue
        for value in key.values():
            name = value.name()
            if not name or (wanted is not None and name.lower() not in wanted):
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
        value_defs = () if is_software else _NTUSER_VALUES
        scope = 'Machine' if is_software else 'User'
        user = '' if is_software else user_from_path(relative_source)
        rows_here = 0
        try:
            reg = open_hive(source, context)
            for row in _run_rows(reg, key_defs, scope, user, relative_source, value_defs):
                data_list.append(row)
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Run and RunOnce Keys: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
