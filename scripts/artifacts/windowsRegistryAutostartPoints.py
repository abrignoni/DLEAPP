"""Windows registry autostart points beyond the Run keys, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsRegistryAutostartPoints": {
        "name": "Registry Autostart Points",
        "description": "Registry values that name programs or DLLs Windows loads at boot or logon, beyond the Run "
                       "keys: Winlogon Userinit and Shell, AppInit_DLLs, Active Setup StubPath, Netsh helper DLLs, "
                       "BootExecute, the LSA package lists, print monitors and time providers.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each value read at eight kinds of registry location where Windows is told what "
                 "to load at boot or logon, with the last-written time of the key holding it. A default "
                 "installation has values in most of them, so a row is an entry to compare with what the "
                 "system should hold and is not by itself a finding; the Run keys are a separate artifact. "
                 "From the SOFTWARE hive, each also under WOW6432Node: (1) Winlogon, the Userinit and Shell "
                 "values of Microsoft\\Windows NT\\CurrentVersion\\Winlogon, which MITRE ATT&CK describes as "
                 "pointing to userinit.exe, the program executed when a user logs on, and to explorer.exe, the "
                 "system shell (T1547.004, https://attack.mitre.org/techniques/T1547/004/); the "
                 "Winlogon\\Notify key that page also names is not read, and none of the five tested SOFTWARE "
                 "hives holds it. (2) AppInit_DLLs, LoadAppInit_DLLs and RequireSignedAppInit_DLLs of "
                 "Microsoft\\Windows NT\\CurrentVersion\\Windows: DLLs named in AppInit_DLLs are loaded by "
                 "user32.dll into every process that loads user32.dll (T1546.010, "
                 "https://attack.mitre.org/techniques/T1546/010/), LoadAppInit_DLLs enables that with 1 and "
                 "disables it with 0, and RequireSignedAppInit_DLLs set to 1 loads only code-signed DLLs "
                 "(Microsoft, 'AppInit DLLs in Windows 7 and Windows Server 2008 R2', "
                 "https://learn.microsoft.com/en-us/windows/win32/win7appqual/appinit-dlls-in-windows-7-and-windows-server-2008-r2). "
                 "(3) Active Setup, the StubPath value of each subkey of Microsoft\\Active Setup\\Installed "
                 "Components, the program executed when a user logs in (T1547.014, "
                 "https://attack.mitre.org/techniques/T1547/014/); a subkey without a StubPath gives no row. "
                 "(4) Netsh Helper DLLs, every named value of Microsoft\\NetSh, where the paths of netsh.exe "
                 "helper DLLs are registered and loaded whenever netsh.exe runs (T1546.007, "
                 "https://attack.mitre.org/techniques/T1546/007/). From the SYSTEM hive, under the control set "
                 "its Select key names as Current: (5) BootExecute of Control\\Session Manager, by default "
                 "autocheck autochk * (T1547.001, https://attack.mitre.org/techniques/T1547/001/). (6) LSA "
                 "Packages, the Authentication Packages value of Control\\Lsa, DLLs the Local Security "
                 "Authority loads at system start (T1547.002, https://attack.mitre.org/techniques/T1547/002/), "
                 "its Security Packages value and the one under Control\\Lsa\\OSConfig, the security support "
                 "providers loaded at boot (T1547.005, https://attack.mitre.org/techniques/T1547/005/), and "
                 "its Notification Packages value, the registered password filters (T1556.002, "
                 "https://attack.mitre.org/techniques/T1556/002/). (7) Print Monitors, the Driver value of "
                 "each subkey of Control\\Print\\Monitors, a DLL the print spooler loads at boot (T1547.010, "
                 "https://attack.mitre.org/techniques/T1547/010/). (8) Time Providers, the DllName and Enabled "
                 "values of each subkey of Services\\W32Time\\TimeProviders, DLLs the time service loads when "
                 "listed and enabled (T1547.003, https://attack.mitre.org/techniques/T1547/003/). From each "
                 "NTUSER.DAT: the Userinit and Shell values of Software\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\Winlogon, the per-user key T1547.004 names. Value names are matched "
                 "without case. Key Last Written (UTC) is the last-written time of the key that holds the "
                 "value, the subkey for Active Setup, Print Monitors and Time Providers; it changes when any "
                 "value of that key is written, so it is not established as the time the reported value was "
                 "set. Location is the kind, with (Wow6432Node) or (OSConfig) appended. Entry is the subkey "
                 "name for the three kinds read per subkey, and Entry Label is that subkey's unnamed value, as "
                 "stored, which Active Setup components use for a name. Value is the value name and Data its "
                 "data as stored: a string unchanged, the strings of a multi-string joined with ' | ' without "
                 "the empty strings that end the list, a number as a number, binary data as hexadecimal. Scope "
                 "is Machine for SOFTWARE and SYSTEM and User for an NTUSER.DAT, User is the folder name under "
                 "Users in the NTUSER.DAT's path, Key is the key path under the hive root, and Source File is "
                 "the hive. Only the current control set is read; each of the five tested SYSTEM hives has "
                 "ControlSet001 alone. The tested data holds default values only. On pc_mus_001_win11 (72 "
                 "rows), af_case2_win10 (69), lonewolf_win10 (71), szechuan_win10 (69) and "
                 "windows11_arm_known_20261001 (72) every row has Scope Machine and an empty User, because no "
                 "NTUSER.DAT in them holds a Winlogon Userinit or Shell value. On all five, Winlogon Shell is "
                 "explorer.exe and Userinit names userinit.exe in system32 followed by a comma, the "
                 "WOW6432Node Winlogon key holds Shell and no Userinit, AppInit_DLLs is empty with "
                 "LoadAppInit_DLLs 0 in both keys and no RequireSignedAppInit_DLLs value, BootExecute is "
                 "autocheck autochk *, Authentication Packages is msv1_0, Notification Packages is scecli, "
                 "Security Packages is a pair of double quotes, the OSConfig key holds no value, and the time "
                 "providers are NtpClient with Enabled 1, NtpServer with Enabled 0 and VMICTimeProvider with "
                 "Enabled 1. Print Monitors gives 6 rows on four images and 7 on lonewolf_win10, Netsh Helper "
                 "DLLs 37 to 40 rows across the two keys, and Active Setup 9 to 11 rows of the 38 to 42 "
                 "subkeys. A value other than the defaults, a per-user row, an OSConfig row, a "
                 "RequireSignedAppInit_DLLs row, binary data and a current control set other than "
                 "ControlSet001 were tested with constructed input only. Whether Windows loads what a value "
                 "names was not tested: the presence of a row does not establish that the program or DLL ran, "
                 "and other autostart locations exist that this artifact does not read. Reading the hives "
                 "requires the python-registry package. A dirty hive is read after the entries of its .LOG1 "
                 "and .LOG2 transaction logs that continue its sequence are applied; the run log names each "
                 "hive replayed and each dirty hive read as it is, with the reason.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "play-circle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 69 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 71 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 72 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 69 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 72 rows",
            "windows11_arm_parallels": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (current_control_set, found_hives, key_written_utc, open_hive, open_key,
                                      user_from_path)

_WINLOGON = r'Microsoft\Windows NT\CurrentVersion\Winlogon'
_WINDOWS = r'Microsoft\Windows NT\CurrentVersion\Windows'
_ACTIVE_SETUP = r'Microsoft\Active Setup\Installed Components'
_APPINIT = ('appinit_dlls', 'loadappinit_dlls', 'requiresignedappinit_dlls')

# (Location for the row, key path under the hive root, value names read in lower case or None for every value,
# True when the values are read from each subkey of the key rather than from the key itself)
_SOFTWARE_POINTS = (
    ('Winlogon', _WINLOGON, ('userinit', 'shell'), False),
    ('Winlogon (Wow6432Node)', 'WOW6432Node\\' + _WINLOGON, ('userinit', 'shell'), False),
    ('AppInit_DLLs', _WINDOWS, _APPINIT, False),
    ('AppInit_DLLs (Wow6432Node)', 'WOW6432Node\\' + _WINDOWS, _APPINIT, False),
    ('Active Setup', _ACTIVE_SETUP, ('stubpath',), True),
    ('Active Setup (Wow6432Node)', 'WOW6432Node\\' + _ACTIVE_SETUP, ('stubpath',), True),
    ('Netsh Helper DLLs', r'Microsoft\NetSh', None, False),
    ('Netsh Helper DLLs (Wow6432Node)', r'WOW6432Node\Microsoft\NetSh', None, False),
)
# the same, under the control set the Select key names as current
_SYSTEM_POINTS = (
    ('BootExecute', r'Control\Session Manager', ('bootexecute',), False),
    ('LSA Packages', r'Control\Lsa', ('authentication packages', 'security packages', 'notification packages'),
     False),
    ('LSA Packages (OSConfig)', r'Control\Lsa\OSConfig', ('security packages',), False),
    ('Print Monitors', r'Control\Print\Monitors', ('driver',), True),
    ('Time Providers', r'Services\W32Time\TimeProviders', ('dllname', 'enabled'), True),
)
_NTUSER_POINTS = (
    ('Winlogon', 'Software\\' + _WINLOGON, ('userinit', 'shell'), False),
)


def _data(value):
    """A value's data for the row: a string as stored, the strings of a multi-string joined with ' | ' without the
    empty strings that end the list, a number as a number, and bytes as hexadecimal."""
    data = value.value()
    if isinstance(data, list):
        items = [str(item) for item in data]
        while items and items[-1] == '':
            items.pop()
        return ' | '.join(items)
    if isinstance(data, bytes):
        return data.hex()
    return data


def _default_value(key):
    """The data of a key's unnamed value as text, or ''."""
    for value in key.values():
        if value.name() in ('', '(default)'):
            data = _data(value)
            return data if isinstance(data, str) else str(data)
    return ''


def point_rows(reg, points, prefix=''):
    """The rows for the autostart points of one hive: (key last written, location, entry, entry label, value name,
    data, key path)."""
    rows = []
    for location, path, wanted, per_subkey in points:
        path = prefix + path
        key = open_key(reg, path)
        if key is None:
            continue
        holders = ([(sub.name(), _default_value(sub), sub) for sub in key.subkeys()] if per_subkey
                   else [('', '', key)])
        for entry, label, holder in holders:
            for value in holder.values():
                name = value.name()
                if name in ('', '(default)') or (wanted is not None and name.lower() not in wanted):
                    continue
                rows.append((key_written_utc(holder), location, entry, label, name, _data(value),
                             path + ('\\' + entry if per_subkey else '')))
    return rows


@artifact_processor
def windowsRegistryAutostartPoints(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Location', 'Entry', 'Entry Label', 'Value', 'Data',
                    'Scope', 'User', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Registry Autostart Points: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SOFTWARE', 'SYSTEM', 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        name = os.path.basename(source).upper()
        user = user_from_path(relative) if name == 'NTUSER.DAT' else ''
        try:
            reg = open_hive(source, context)
            if name == 'SYSTEM':
                rows = point_rows(reg, _SYSTEM_POINTS, current_control_set(reg) + '\\')
            else:
                rows = point_rows(reg, _SOFTWARE_POINTS if name == 'SOFTWARE' else _NTUSER_POINTS)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Registry Autostart Points: could not read {relative}: {exc}')
            continue
        scope = 'User' if name == 'NTUSER.DAT' else 'Machine'
        data_list.extend(row[:6] + (scope, user, row[6], relative) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
