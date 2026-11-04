"""Windows KnownDLLs list and logon banner for DLEAPP.

Author: @AlexisBrignoni, Claude.

KnownDLLs is read from the SYSTEM hive's current control set, Session Manager\\KnownDLLs, the key Microsoft names
as the list of known DLLs. The logon banner ("Interactive logon: Message title/text for users attempting to log
on") is read from the SOFTWARE hive, from the values Windows' own security policy export maps that setting to, and
from the Winlogon values Microsoft lists for the same dialog in its msgina.dll (standard GINA) feature
documentation.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (current_control_set, found_hives, key_written_utc, open_hive,
                                      open_key)

_SESSION_MANAGER = r'Control\Session Manager'
_BANNER_KEYS = (('Policies\\System', r'Microsoft\Windows\CurrentVersion\Policies\System'),
                ('Winlogon', r'Microsoft\Windows NT\CurrentVersion\Winlogon'))
_BANNER_VALUES = ('LegalNoticeCaption', 'LegalNoticeText')

__artifacts_v2__ = {
    "knownDlls": {
        "name": "KnownDLLs",
        "description": "The values of the KnownDLLs key of the SYSTEM hive's current control set, one per listed "
                       "DLL plus the DllDirectory values where present, with the key's last-written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none (vendored regfprobe)",
        "category": "Windows",
        "notes": "One row per value of SYSTEM\\\\<current control set>\\\\Control\\\\Session Manager\\\\KnownDLLs, the "
                 "current control set being the one the Select key's Current value names, or ControlSet001 when Select "
                 "has no Current value. Microsoft describes the "
                 "list of known DLLs as one step of the DLL search order: if a DLL is on the list for that version "
                 "of Windows, the system uses its copy of the known DLL, and the list on a system is in that registry "
                 "key (https://github.com/MicrosoftDocs/win32/blob/129846d6c4f059b97adb840af9d5fca1c35b2c1e/"
                 "desktop-src/Dlls/dynamic-link-library-search-order.md#L24). Name is the value name and DLL its "
                 "string data, read up to the first NUL; a REG_EXPAND_SZ value is shown unexpanded. On "
                 "cfreds_leakage_win7, alihadi_challenge3_win81 and szechuan_dc01_server2012r2 the key also held "
                 "DllDirectory and DllDirectory32, and on cfreds_hacking_case_winxp DllDirectory, whose data is a "
                 "folder, not a DLL. Key Last Written (UTC) is the KnownDLLs key's last-written time, so it is the same on "
                 "every row of one hive and does not date any one entry. Other values of the Session Manager key are "
                 "not read. On the tested images most names were shared: "
                 "on the ten tested Windows 7 and later images the key held 30 to 36 values, 22 names were on every one "
                 "of them, and an image had at most 4 names that no more than one other of them had; on "
                 "cfreds_hacking_case_winxp it held 21. A row records an entry "
                 "of the list, not that the DLL was loaded. A dirty hive is read after its .LOG1 and .LOG2 logs are "
                 "applied when they can be, as in the other registry artifacts.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 35 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 32 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 31 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 32 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 36 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 30 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 31 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 32 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 35 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 31 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 21 rows",
        },
    },
    "logonBanner": {
        "name": "Logon Banner",
        "description": "The caption and text of the legal notice Windows can show before logon, from the SOFTWARE "
                       "hive, where set.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none (vendored regfprobe)",
        "category": "Windows",
        "notes": "One row per non-empty LegalNoticeCaption or LegalNoticeText string value in two keys of the SOFTWARE "
                 "hive. "
                 "Microsoft\\\\Windows\\\\CurrentVersion\\\\Policies\\\\System is where Windows' own security policy "
                 "export (secedit /export) puts the settings Interactive logon: Message title and Message text for "
                 "users attempting to log on, measured on the known data (corpus key "
                 "windows11_arm_logon_banner_known_20261104, Windows 11 build 26200): a two-line banner set with "
                 "secedit /configure was stored there as two REG_SZ values, the lines joined by CR LF, and the key's "
                 "last-written time was the moment it was set. Microsoft\\\\Windows NT\\\\CurrentVersion\\\\Winlogon is "
                 "where Microsoft lists LegalNoticeCaption and LegalNoticeText as the caption and message of the "
                 "legal notice dialog box, in its msgina.dll (standard GINA) feature documentation "
                 "(https://github.com/MicrosoftDocs/win32/blob/"
                 "3c1fd9cf483eb6d4026c4a4d0ae9461e7308572e/desktop-src/SecAuthN/msgina-dll-features.md#L18-L31); "
                 "setting the banner through secedit left those empty on the known data. Key names which of the two "
                 "the row is from, Value the value name as stored and Text its string data up to the first NUL. "
                 "String values only; a value of another type is not shown. Key Last Written (UTC) is that "
                 "key's last-written time, which dates the last change to any value of the key, not this value. "
                 "Microsoft gives the setting's default as no message "
                 "(https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc779661(v=ws.10)); "
                 "on the ten tested Windows 7 and later images all four values were present and empty, so they gave no "
                 "rows. A "
                 "set banner shows the setting, not that anyone saw it. A dirty hive is read after its .LOG1 and .LOG2 "
                 "logs are applied when they can be, as in the other registry artifacts.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "message-square",
        "sample_data": {
            "windows11_arm_logon_banner_known_20261104": "Windows 11 build 26200 (ARM64), test banner set with secedit | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the values are empty)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the values are empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the values are empty)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the values are empty)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (the values are empty)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (the values are empty)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (the values are empty)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (the values are empty)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (the values are empty)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (the values are empty)",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 0 rows (no non-empty value)",
        },
    },
}


@artifact_processor
def knownDlls(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Name', 'DLL', 'Source File')
    data_list = []
    sources = []
    label = 'KnownDLLs'
    for source in found_hives(context, 'SYSTEM'):
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        control_set = current_control_set(reg)
        key = open_key(reg, control_set + '\\' + _SESSION_MANAGER + r'\KnownDLLs')
        if key is None:
            logfunc(f'{label}: {relative} has no {control_set}\\{_SESSION_MANAGER}\\KnownDLLs key')
            continue
        written = key_written_utc(key)
        rows = 0
        for value in key.values():
            data_list.append((written, value.name(), str(value.value()), relative))
            rows += 1
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def logonBanner(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Key', 'Value', 'Text', 'Source File')
    data_list = []
    sources = []
    label = 'Logon Banner'
    for source in found_hives(context, 'SOFTWARE'):
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        rows = 0
        for key_label, path in _BANNER_KEYS:
            key = open_key(reg, path)
            if key is None:
                continue
            for value in key.values():
                if value.name().lower() not in {name.lower() for name in _BANNER_VALUES}:
                    continue
                text = value.value()
                if not isinstance(text, str) or not text.strip('\x00').strip():
                    continue
                data_list.append((key_written_utc(key), key_label, value.name(), text, relative))
                rows += 1
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
