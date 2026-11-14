"""Internet Explorer add-on registrations in the SOFTWARE and NTUSER.DAT hives, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "ieBrowserHelperObjects": {
        "name": "Internet Explorer Browser Helper Objects",
        "description": "Browser Helper Object keys in the SOFTWARE hive, native and Wow6432Node, with the name, the "
                       "NoExplorer and NoInternetExplorer values as stored, and the class name and InprocServer32 "
                       "path the same hive registers for the CLSID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none (vendored regfprobe)",
        "category": "Internet Explorer",
        "notes": "One row for each subkey of HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Browser Helper Objects (View Native) and of HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Browser Helper Objects (View Wow6432Node), read from the SOFTWARE hive; Microsoft lists both as where new browser helper object plugins for Internet Explorer appear, the second for 32-bit applications on 64-bit computers (https://github.com/MicrosoftDocs/azure-docs/blob/2630d5b2b4bc8245ab0b10a96ded21b0e720ffb1/articles/azure-change-tracking-inventory/overview-monitoring-agent.md#L92-L93). CLSID is the subkey's name and Name its unnamed value, which was empty on 1 of the cfreds_leakage_win7 rows, 1 of the lonewolf_win10 rows, 2 of the pc_mus_001_win11 rows and the one cfreds_hacking_case_winxp row. NoExplorer (as stored) and NoInternetExplorer (as stored) are those values' data as text; the tested keys stored them as REG_SZ on some keys and REG_DWORD on others, and each held 1 wherever it was present. A Microsoft IEInternals blog post of 11 April 2011 (https://learn.microsoft.com/en-us/archive/blogs/ieinternals/browser-helper-objects-for-windows-explorer) describes NoExplorer as a value that keeps a BHO from loading into Windows Explorer and NoInternetExplorer, from Internet Explorer 9, as keeping it from loading into Internet Explorer; it does not say what data the values must hold, so the columns show the data stored. NoExplorer (as stored) held 1 on all rows of hexordia_mvs2025_win11, ou_ransomware_server2022 and pc_mus_001_win11 and had no value on the cfreds_hacking_case_winxp row. NoInternetExplorer (as stored) had no value on all rows of every tested image except 1 lonewolf_win10 row and 1 windows11_arm_ie_addons_known_20261114 row. Class Name and InprocServer32 are the unnamed values of Classes\\CLSID\\<CLSID> and its InprocServer32 subkey in the same SOFTWARE hive, or of Classes\\Wow6432Node\\CLSID\\<CLSID> for the Wow6432Node view, the CLSID compared without case, as stored with variables not expanded; both were found for every tested row. Microsoft links HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Classes to HKEY_LOCAL_MACHINE\\SOFTWARE\\Classes\\Wow6432Node (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L112) and documents the unnamed value of a CLSID's InprocServer32 subkey as the in-process server's path (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/inprocserver32.md#L13-L21). Microsoft also says class registrations under HKEY_CURRENT_USER\\Software\\Classes have priority over those under HKEY_LOCAL_MACHINE\\Software\\Classes (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/hkey-classes-root-key.md#L13-L15). Per-user class registrations (UsrClass.dat, read by Per-User COM Registrations) are not read here, so a path shown is the machine-wide registration and is not established as the file that loaded for any user. Any other value under a BHO subkey is named in the run log; no tested key held one. Key Last Written (UTC) is the subkey's last-written time and is not established as the time the object was registered. Key is the subkey's path under the hive root and Source File the hive. Rows: pc_mus_001_win11 4 (1 Native, 3 Wow6432Node), cfreds_leakage_win7 3, hexordia_mvs2025_win11 3, lonewolf_win10 3, ou_ransomware_server2022 2, cfreds_hacking_case_winxp 1, and windows11_arm_ie_addons_known_20261114 6, of which 1 is a registration written for the test (NoInternetExplorer as a REG_DWORD, with its Classes entry) and 5 were already on the lab machine. The other tested images have no Browser Helper Objects subkey, or no SOFTWARE hive in the extraction. A run over a tree holding two volumes, each with its own SOFTWARE hive, and copies of the hives at paths the artifact does not declare gave exactly the rows of the two declared hives. A row records a registration in the hive, not that Internet Explorer ran or loaded the object. The hives are read with the vendored regfprobe (scripts/vendor/regfprobe.py); a dirty hive is read after the entries of its transaction logs that continue its sequence are applied, and the run log names each hive replayed and each dirty hive read as it is.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "puzzle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Browser Helper Objects subkey)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no Browser Helper Objects subkey)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no Browser Helper Objects subkey)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (no SOFTWARE hive in the extraction)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (no SOFTWARE hive in the extraction)",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 1 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 3 rows",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no SOFTWARE hive in the extraction)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE hive in the extraction)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE hive in the extraction)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE hive in the extraction)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 3 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no Browser Helper Objects subkey)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Browser Helper Objects subkey)",
            "windows11_arm_ie_addons_known_20261114": "Windows 11 25H2 build 26200 (ARM64) | 6 rows",
            "windows11_arm_usn_rewind_known_20261025": "Windows 11 25H2 build 26200 (NTFS test volume) | 0 rows (no SOFTWARE hive in the extraction)",
        },
    },
    "ieToolbarExtensions": {
        "name": "Internet Explorer Toolbar and Menu Extensions",
        "description": "Internet Explorer Extensions keys, machine-wide in the SOFTWARE hive (native and Wow6432Node) "
                       "and per user in NTUSER.DAT, with the button and menu text, the handler class, the program, "
                       "script, Explorer Bar or COM object each names, and the InprocServer32 path SOFTWARE registers "
                       "for that COM object.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none (vendored regfprobe)",
        "category": "Internet Explorer",
        "notes": "One row for each subkey named by a GUID of Software\\Microsoft\\Internet Explorer\\Extensions: Scope Machine for the SOFTWARE hive's key and its Wow6432Node counterpart (View Native or Wow6432Node; Microsoft lists both as where new Internet Explorer extensions such as custom tool menus and toolbar buttons appear, https://github.com/MicrosoftDocs/azure-docs/blob/2630d5b2b4bc8245ab0b10a96ded21b0e720ffb1/articles/azure-change-tracking-inventory/overview-monitoring-agent.md#L94-L95) and Scope User for the key in each NTUSER.DAT, under Users or Documents and Settings, where View is blank. Microsoft's archived Adding Toolbar Buttons tutorial (https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/aa753588(v=vs.85)) gives the HKEY_LOCAL_MACHINE key, says HKEY_CURRENT_USER can be used instead for per-user settings and that duplicate items in HKEY_CURRENT_USER override those in HKEY_LOCAL_MACHINE, and defines the values shown here: ButtonText the button's label, Icon the grayscale icons, HotIcon the color icons, Default Visible \"Yes\" for a button shown on the toolbar by default, CLSID {1FBA04EE-3024-11D2-8F1F-0000F87ABD16} (CLSID_Shell_ToolbarExtExec) for a button that runs a COM object, a script or a program and {E0DD6CAB-2D10-11D2-8F1A-0000F87ABD16} (CLSID_Shell_ToolbarExtBand) for one that opens an Explorer Bar, ClsidExtension the COM object's GUID, BandCLSID the Explorer Bar's CLSID, Script the full path of the script and Exec the full path of the program. CLSID Class gives that name when CLSID is one of the two, compared without case, and is blank otherwise. MenuText and ToolTip are not defined in that tutorial and are shown as stored. All values are shown as stored, as text, with variables not expanded. Other Values holds the key's other values as name=data joined with '; ', the unnamed value as (default). ClsidExtension InprocServer32 is the unnamed value of the InprocServer32 subkey of Classes\\CLSID\\<ClsidExtension> (Classes\\Wow6432Node\\CLSID for the Wow6432Node view) in the SOFTWARE hive; for a User row, the SOFTWARE hive on the same volume, the part of the path before its Users, Documents and Settings or Windows folder, and blank when no single SOFTWARE hive was read for that volume. Microsoft links HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Classes to HKEY_LOCAL_MACHINE\\SOFTWARE\\Classes\\Wow6432Node (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L112) and documents the unnamed value of a CLSID's InprocServer32 subkey as the in-process server's path (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/inprocserver32.md#L13-L21). Microsoft also says class registrations under HKEY_CURRENT_USER\\Software\\Classes have priority over those under HKEY_LOCAL_MACHINE\\Software\\Classes (https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/hkey-classes-root-key.md#L13-L15). Per-user class registrations (UsrClass.dat, read by Per-User COM Registrations) are not read here, so a path shown is the machine-wide registration and is not established as the file that loaded for any user. A subkey not named by a GUID is named in the run log and not reported: CmdMapping in the cfreds_hacking_case_winxp user hive. On the tested corpus images Scope held Machine on all rows, so User had no value on any corpus row; CLSID held {1FBA04EE-3024-11d2-8F1F-0000F87ABD16} on all rows of lonewolf_win10 and CLSID Class held CLSID_Shell_ToolbarExtExec on all corpus rows; Exec and BandCLSID had no value on any corpus row and Script was set only on the cfreds_hacking_case_winxp row, which has no value in ToolTip, Default Visible, ClsidExtension or ClsidExtension InprocServer32; Default Visible held Yes on all rows of lonewolf_win10 and windows11_arm_ie_addons_known_20261114; ToolTip had no value on the hexordia_mvs2025_win11 row or any windows11_arm_ie_addons_known_20261114 row; Icon and HotIcon were identical on every corpus row. Rows: lonewolf_win10 6 (3 Native, 3 Wow6432Node, the same three GUIDs in both), hexordia_mvs2025_win11 1, cfreds_hacking_case_winxp 1. No tested corpus image has a per-user Extensions subkey named by a GUID. windows11_arm_ie_addons_known_20261114 gives 5 rows: 1 Machine row already on the lab machine and 4 User rows written for the test with PowerShell, one each with Exec, Script, BandCLSID and ClsidExtension (whose Classes entry was written too); the User, Exec, Script, BandCLSID and CLSID_Shell_ToolbarExtBand branches are exercised only by those written values, which test the reader, not what Internet Explorer writes. Key Last Written (UTC) is the subkey's last-written time and is not established as the time the extension was added. Key is the subkey's path under the hive root, Source File the hive and User the profile folder name. A row records a registration in the hive, not that a button was shown or used. The hives are read with the vendored regfprobe (scripts/vendor/regfprobe.py); a dirty hive is read after the entries of its transaction logs that continue its sequence are applied, and the run log names each hive replayed and each dirty hive read as it is.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Documents and Settings/*/NTUSER.DAT',
                  '*/Documents and Settings/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg]'),
        "output_types": ["standard"],
        "artifact_icon": "tool",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Extensions subkey named by a GUID)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no Extensions subkey named by a GUID)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no Extensions subkey named by a GUID)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 1 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no Extensions subkey named by a GUID)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no Extensions subkey named by a GUID)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Extensions subkey named by a GUID)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no Extensions subkey named by a GUID)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Extensions subkey named by a GUID)",
            "windows11_arm_ie_addons_known_20261114": "Windows 11 25H2 build 26200 (ARM64) | 5 rows",
            "windows11_arm_usn_rewind_known_20261025": "Windows 11 25H2 build 26200 (NTFS test volume) | 0 rows (no SOFTWARE or NTUSER.DAT in the extraction)",
        },
    },
    "ieAddonUserRecords": {
        "name": "Internet Explorer Add-on Records (Ext)",
        "description": "Per-user keys named by an add-on CLSID under Software\\Microsoft\\Windows\\CurrentVersion\\Ext\\"
                       "Settings and Ext\\Stats in NTUSER.DAT, with their values as stored and the name the SOFTWARE "
                       "hive gives the CLSID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none (vendored regfprobe)",
        "category": "Internet Explorer",
        "notes": "One row for each subkey of Software\\Microsoft\\Windows\\CurrentVersion\\Ext\\Settings in each NTUSER.DAT, under Users or Documents and Settings (Key Group Settings), and for each subkey of each subkey of Software\\Microsoft\\Windows\\CurrentVersion\\Ext\\Stats (Key Group Stats, Subkey its name, iexplore on every tested row); a subkey of either key that holds values, or holds no subkeys, gives a row of its own with Subkey blank. CLSID is the name of the subkey under Settings or Stats. Values (as stored) is every value of the row's key as name=data joined with '; ', a binary value as hexadecimal. No Microsoft source found documents these keys or their values, so the meaning of Type, Flags, Count, Blocked, LoadTime and VerCache is not established and they are shown as stored. Time, a 16-byte binary value under Stats, read as eight little-endian 16-bit numbers in the order of the SYSTEMTIME structure's members (https://github.com/MicrosoftDocs/sdk-api/blob/3f565be3559f8ffffefc46d291fa6b0eae45459e/sdk-api-src/content/minwinbase/ns-minwinbase-systemtime.md#L61-L312), equaled the key's last-written time to the millisecond on all 7 Stats rows tested (cfreds_leakage_win7 4, lonewolf_win10 1, windows11_arm_ie_addons_known_20261114 2); it is left as hexadecimal in Values (as stored) because it repeats Key Last Written (UTC). Name is the unnamed value of the Browser Helper Objects subkey of the same CLSID, either view, in the SOFTWARE hive on the same volume (the part of the path before its Users, Documents and Settings or Windows folder), or else the class name under Classes\\CLSID or Classes\\Wow6432Node\\CLSID there; it is blank when none holds one or no single SOFTWARE hive was read for that volume (1 windows11_arm_ie_addons_known_20261114 row). Key Last Written (UTC) is the key's last-written time; what Internet Explorer did at that time is not established. User is the profile folder name, which held one value on all rows of each tested image, where one profile holds these keys; Source File is kept beside it because the folder name alone does not separate two hives of one user name on different volumes. Rows: cfreds_leakage_win7 6 (2 Settings, 4 Stats), lonewolf_win10 1, windows11_arm_ie_addons_known_20261114 3, all written by the lab machine itself. The other tested images hold no subkey of Ext\\Settings or Ext\\Stats, or no NTUSER.DAT in the extraction. A row records that Internet Explorer kept a per-user key for the CLSID, not that the user used the add-on. The hives are read with the vendored regfprobe (scripts/vendor/regfprobe.py); a dirty hive is read after the entries of its transaction logs that continue its sequence are applied, and the run log names each hive replayed and each dirty hive read as it is.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Documents and Settings/*/NTUSER.DAT',
                  '*/Documents and Settings/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg]'),
        "output_types": ["standard"],
        "artifact_icon": "bar-chart",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (no NTUSER.DAT in the extraction)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (no NTUSER.DAT in the extraction)",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 6 rows",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no NTUSER.DAT in the extraction)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no NTUSER.DAT in the extraction)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no NTUSER.DAT in the extraction)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no NTUSER.DAT in the extraction)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Ext\\Settings or Ext\\Stats subkey)",
            "windows11_arm_ie_addons_known_20261114": "Windows 11 25H2 build 26200 (ARM64) | 3 rows",
            "windows11_arm_usn_rewind_known_20261025": "Windows 11 25H2 build 26200 (NTFS test volume) | 0 rows (no NTUSER.DAT in the extraction)",
        },
    },
}

import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key

# (View, key path under the SOFTWARE root, the Classes CLSID key of that view under the SOFTWARE root)
BHO_VIEWS = (
    ('Native', r'Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects', r'Classes\CLSID'),
    ('Wow6432Node', r'Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects',
     r'Classes\Wow6432Node\CLSID'),
)
MACHINE_EXTENSION_VIEWS = (
    ('Native', r'Microsoft\Internet Explorer\Extensions', r'Classes\CLSID'),
    ('Wow6432Node', r'Wow6432Node\Microsoft\Internet Explorer\Extensions', r'Classes\Wow6432Node\CLSID'),
)
USER_EXTENSIONS = r'Software\Microsoft\Internet Explorer\Extensions'
USER_EXT = (('Settings', r'Software\Microsoft\Windows\CurrentVersion\Ext\Settings'),
            ('Stats', r'Software\Microsoft\Windows\CurrentVersion\Ext\Stats'))

# The two extension classes Microsoft's Adding Toolbar Buttons tutorial names for the CLSID value.
HANDLER_CLASSES = {
    '{1fba04ee-3024-11d2-8f1f-0000f87abd16}': 'CLSID_Shell_ToolbarExtExec',
    '{e0dd6cab-2d10-11d2-8f1a-0000f87abd16}': 'CLSID_Shell_ToolbarExtBand',
}
_GUID = re.compile(r'^\{[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\}$', re.I)
EXTENSION_VALUES = ('buttontext', 'menutext', 'tooltip', 'default visible', 'clsid', 'clsidextension', 'exec',
                    'script', 'bandclsid', 'icon', 'hoticon')


def as_text(data):
    """A value's data as stored, as text: a multi-string joined with ' | ', binary as hexadecimal."""
    if data is None:
        return ''
    if isinstance(data, list):
        return ' | '.join(str(item) for item in data if item != '')
    if isinstance(data, (bytes, bytearray)):
        return bytes(data).hex()
    return str(data)


def values_of(key):
    """{name in lower case: (name as stored, data as text)} of a key's values; the unnamed value is '(default)'."""
    held = {}
    if key is None:
        return held
    for value in key.values():
        name = value.name() or '(default)'
        held[name.lower()] = (name, as_text(value.value()))
    return held


def other_values(held, shown):
    """The values not shown in a column of their own, as name=data joined with '; '."""
    return '; '.join(f'{name}={data}' for lower, (name, data) in sorted(held.items()) if lower not in shown)


def profile_user(relative):
    """The folder name after the first Users or Documents and Settings folder of a path, or ''."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts):
        if part.lower() in ('users', 'documents and settings') and index + 1 < len(parts):
            return parts[index + 1]
    return ''


def volume_of(relative):
    """The part of a path within the extraction before its Users, Documents and Settings or Windows folder."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts):
        if part.lower() in ('users', 'documents and settings', 'windows'):
            return '/'.join(parts[:index]).lower()
    return None


class Classes:
    """The class name and InprocServer32 path a SOFTWARE hive registers for a CLSID, per view, looked up without case."""

    def __init__(self, reg):
        self._views = {}
        for path in {view[2] for view in BHO_VIEWS}:
            key = open_key(reg, path)
            self._views[path] = {sub.name().lower(): sub for sub in key.subkeys()} if key is not None else {}

    def lookup(self, view_path, clsid):
        """(class name, InprocServer32) as stored, or ('', '') when the view has no key of that name."""
        entry = self._views.get(view_path, {}).get(str(clsid).strip().lower())
        if entry is None:
            return '', ''
        server = None
        for sub in entry.subkeys():
            if sub.name().lower() == 'inprocserver32':
                server = sub
        name = values_of(entry).get('(default)', ('', ''))[1]
        return name, values_of(server).get('(default)', ('', ''))[1]


def bho_rows(reg, classes):
    """(key last written, view, CLSID, name, NoExplorer, NoInternetExplorer, class name, InprocServer32, key) for
    each subkey of the two Browser Helper Objects keys; any other value is named in the run log."""
    rows = []
    for view, path, classes_path in BHO_VIEWS:
        parent = open_key(reg, path)
        if parent is None:
            continue
        for entry in parent.subkeys():
            held = values_of(entry)
            class_name, server = classes.lookup(classes_path, entry.name())
            others = other_values(held, ('(default)', 'noexplorer', 'nointernetexplorer'))
            if others:
                logfunc(f'IE Browser Helper Objects: {path}\\{entry.name()} also holds {others}')
            rows.append((key_written_utc(entry), view, entry.name(), held.get('(default)', ('', ''))[1],
                         held.get('noexplorer', ('', ''))[1], held.get('nointernetexplorer', ('', ''))[1],
                         class_name, server, f'{path}\\{entry.name()}'))
    return rows


def extension_rows(parent, path, classes, classes_path):
    """(key last written, GUID, ButtonText, MenuText, ToolTip, Default Visible, CLSID, CLSID class, ClsidExtension,
    ClsidExtension InprocServer32, Exec, Script, BandCLSID, Icon, HotIcon, other values, key) for each subkey."""
    rows = []
    if parent is None:
        return rows
    for entry in parent.subkeys():
        if not _GUID.match(entry.name()):
            logfunc(f'IE Toolbar and Menu Extensions: {path}\\{entry.name()} is not named by a GUID; not reported')
            continue
        held = values_of(entry)
        get = {name: held.get(name, ('', ''))[1] for name in EXTENSION_VALUES}
        server = ''
        if get['clsidextension'] and classes is not None:
            server = classes.lookup(classes_path, get['clsidextension'])[1]
        rows.append((key_written_utc(entry), entry.name(), get['buttontext'], get['menutext'], get['tooltip'],
                     get['default visible'], get['clsid'], HANDLER_CLASSES.get(get['clsid'].strip().lower(), ''),
                     get['clsidextension'], server, get['exec'], get['script'], get['bandclsid'], get['icon'],
                     get['hoticon'], other_values(held, EXTENSION_VALUES), f'{path}\\{entry.name()}'))
    return rows


def ext_rows(reg):
    """(key last written, kind, CLSID, subkey, values, key) for each CLSID key under Ext\\Settings, and for each
    CLSID key under Ext\\Stats and each of its subkeys."""
    rows = []
    for kind, path in USER_EXT:
        parent = open_key(reg, path)
        if parent is None:
            continue
        for entry in parent.subkeys():
            subs = list(entry.subkeys())
            held = values_of(entry)
            if held or not subs:
                rows.append((key_written_utc(entry), kind, entry.name(), '', other_values(held, ()),
                             f'{path}\\{entry.name()}'))
            for sub in subs:
                rows.append((key_written_utc(sub), kind, entry.name(), sub.name(), other_values(values_of(sub), ()),
                             f'{path}\\{entry.name()}\\{sub.name()}'))
    return rows


def machine_hives(context, label):
    """{volume: (Classes, opened hive, staged path) or None when the volume has more than one SOFTWARE hive}."""
    machines = {}
    for source in sorted(found_hives(context, 'SOFTWARE')):
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            classes = Classes(reg)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        volume = volume_of(relative)
        if volume in machines:
            logfunc(f'{label}: more than one SOFTWARE hive for {volume or "the extraction root"}; '
                    f'CLSIDs of its users are not resolved')
            machines[volume] = None
        else:
            machines[volume] = (classes, reg, source)
    return machines


def bho_name(reg, clsid):
    """The unnamed value of a Browser Helper Objects subkey of this CLSID, either view, or ''."""
    for _view, path, _classes in BHO_VIEWS:
        parent = open_key(reg, path)
        if parent is None:
            continue
        for entry in parent.subkeys():
            if entry.name().lower() == clsid.lower():
                name = values_of(entry).get('(default)', ('', ''))[1]
                if name:
                    return name
    return ''


@artifact_processor
def ieBrowserHelperObjects(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'View', 'CLSID', 'Name', 'NoExplorer (as stored)',
                    'NoInternetExplorer (as stored)', 'Class Name', 'InprocServer32', 'Key', 'Source File')
    data_list, sources = [], []
    machines = machine_hives(context, 'IE Browser Helper Objects')
    for volume in sorted(machines, key=lambda item: item or ''):
        if machines[volume] is None:
            continue
        classes, reg, source = machines[volume]
        relative = context.get_relative_path(source)
        data_list.extend(row + (relative,) for row in bho_rows(reg, classes))
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ieToolbarExtensions(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Scope', 'User', 'View', 'Extension GUID', 'ButtonText',
                    'MenuText', 'ToolTip', 'Default Visible', 'CLSID', 'CLSID Class', 'ClsidExtension',
                    'ClsidExtension InprocServer32', 'Exec', 'Script', 'BandCLSID', 'Icon', 'HotIcon', 'Other Values',
                    'Key', 'Source File')
    label = 'IE Toolbar and Menu Extensions'
    data_list, sources = [], []
    machines = machine_hives(context, label)
    for volume in sorted(machines, key=lambda item: item or ''):
        if machines[volume] is None:
            continue
        classes, reg, source = machines[volume]
        relative = context.get_relative_path(source)
        for view, path, classes_path in MACHINE_EXTENSION_VIEWS:
            for row in extension_rows(open_key(reg, path), path, classes, classes_path):
                data_list.append((row[0], 'Machine', '', view) + row[1:] + (relative,))
        sources.append(source)
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        machine = machines.get(volume_of(relative))
        try:
            reg = open_hive(source, context)
            rows = extension_rows(open_key(reg, USER_EXTENSIONS), USER_EXTENSIONS,
                                  machine[0] if machine else None, r'Classes\CLSID')
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        data_list.extend((row[0], 'User', profile_user(relative), '') + row[1:] + (relative,) for row in rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def ieAddonUserRecords(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Key Group', 'CLSID', 'Subkey', 'Name',
                    'Values (as stored)', 'Key', 'Source File')
    label = 'IE Add-on Records (Ext)'
    data_list, sources = [], []
    machines = machine_hives(context, label)
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        relative = context.get_relative_path(source)
        machine = machines.get(volume_of(relative))
        try:
            rows = ext_rows(open_hive(source, context))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        user = profile_user(relative)
        for written, kind, clsid, subkey, held, key in rows:
            name = ''
            if machine is not None:
                classes, reg, _source = machine
                name = bho_name(reg, clsid) or classes.lookup(r'Classes\CLSID', clsid)[0] \
                    or classes.lookup(r'Classes\Wow6432Node\CLSID', clsid)[0]
            data_list.append((written, user, kind, clsid, subkey, name, held, key, relative))
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
