"""Windows Amcache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Amcache artifact; the implementation reads
the hive's on-disk structure directly and is not ported from that artifact.

The InventoryApplicationFile field meanings, including FileId being a SHA-1 of
the file (of its first 30 MiB when it is larger) prefixed with four zeroes, are
sourced from public Amcache research and measured on the test images (see the
artifact notes). The InventoryApplication values are compared with the Uninstall
keys they name, and the InventoryApplicationShortcut paths with the link files
on the same images.
"""

from datetime import timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import open_hive

# Amcache.hve records metadata about executables the system has seen, under
# Root\InventoryApplicationFile: the full path, a SHA-1 of the file (stored as
# FileId), publisher and version strings, size, and the PE link date. It
# documents that a file was inventoried, not that it was run.

_INVENTORY_PATH = "Root\\InventoryApplicationFile"
_APPLICATION_PATH = "Root\\InventoryApplication"
_SHORTCUT_PATH = "Root\\InventoryApplicationShortcut"

__artifacts_v2__ = {
    "amcacheApplicationFiles": {
        "name": "Amcache Application Files",
        "description": "Executables the system inventoried, from Amcache.hve InventoryApplicationFile: the "
                       "file path, the SHA-1 Amcache records for it, publisher, product and version, size, "
                       "link date, and the time the entry was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one "
                 "InventoryApplicationFile entry, a key Psmths's Amcache reference lists from Windows "
                 "10 build 14393 and describes as updated only when the Microsoft Compatibility "
                 "Appraiser task runs (Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L68-L69). "
                 "File Path is LowerCaseLongPath as stored; every value on af_case2_win10, "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10 was lowercase. SHA-1 is the "
                 "FileId value without its leading four "
                 "zeroes "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L76) "
                 "and is shown as stored when FileId does not have that shape. It covers the file's "
                 "first 31,457,280 bytes (30 MiB), or the whole file when the file is smaller, as that "
                 "reference's warning describes "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L82-L83). "
                 "Hashed against the files at File Path, it matched the first 30 MiB of all 8 files "
                 "larger than that on the two images (6 on lonewolf_win10 and 2 on pc_mus_001_win11), "
                 "whose whole-file SHA-1 differs, and the whole file on 48 of 50 smaller files sampled "
                 "there; the other 2, on lonewolf_win10, hashed differently. Name, Publisher, Product "
                 "Name and Version are the Name, Publisher, ProductName and Version values as stored. "
                 "On those 58 files, Name was the file's name, compared without case, on all 58, and "
                 "Publisher, Product Name and Version equalled the CompanyName, ProductName and "
                 "FileVersion strings of the file's version resource, compared without case, on 55, 54 "
                 "and 54 of the 55 that carry them. Size (bytes) is the Size value, which equalled the "
                 "file's size in bytes on all 58. Link Date is the LinkDate value as stored; on 56 of "
                 "the 58 it was the TimeDateStamp of the file's PE header written as a UTC time, and "
                 "on lonewolf_win10 one was blank and one differed. The PE format documentation "
                 "describes that stamp as indicating when the file was created "
                 "(https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L111), "
                 "so it is not a time the file ran or was installed. Program ID is the ProgramId "
                 "value, which Psmths describes as the installed program the file is tied to, listed "
                 "under InventoryApplication, the key the Amcache Applications artifact reports "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L75). "
                 "Key Last Write (UTC) is the entry's registry LastWrite time; it is not an execution "
                 "time. An entry records that the file was inventoried; this artifact does not treat "
                 "it as proof that the file ran or of who ran it. Reading the hive needs the "
                 "python-registry package. A dirty hive, one whose base block's two sequence numbers "
                 "differ, is read after the entries in its .LOG1 and .LOG2 transaction logs that "
                 "continue its sequence are applied, following Maxim Suhanov's 'Windows registry file "
                 "format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a "
                 "replay that would give a key an earlier last-written time than the hive already "
                 "holds, a check added here beyond the specification; the run log names each hive "
                 "replayed, with the sequence numbers applied, and each dirty hive read as it is, with "
                 "the reason.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "hash",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 146 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 153 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 292 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 98 rows",
        },
    },
    "amcacheApplications": {
        "name": "Amcache Applications",
        "description": "Applications Windows inventoried, from Amcache.hve InventoryApplication: name, version, "
                       "publisher, how the entry was sourced, install date as stored, install folder, uninstall "
                       "command and the Uninstall registry key or package the entry names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryApplication, a key Psmths's Amcache reference lists from Windows 10 build 14393, "
                 "describes as holding one subkey per installed program, named by its ProgramId, and describes as "
                 "updated only when the Microsoft Compatibility Appraiser task runs, so that software installed "
                 "since that task last ran may be missing (Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L46-L49). "
                 "Every column after the first is a value of the entry as stored, blank where the entry lacks it: "
                 "Install Date (as stored) is InstallDate, Root Folder is RootDirPath, Store App Type is "
                 "StoreAppType, MSI Product Code is MsiProductCode, Hidden ARP (as stored) is HiddenArp, OS Version "
                 "At Install is OSVersionAtInstallTime, Program ID is ProgramId, and the other columns carry their "
                 "value's name. Microsoft's published field descriptions are for its InventoryApplicationAdd "
                 "diagnostic event, and none for the registry values was found; that event's fields carry the names "
                 "of 11 of the 14 values reported here, all but UninstallString, RegistryKeyPath and ProgramId "
                 "(Microsoft, 'Required diagnostic events and fields for Windows 10, versions 22H2 and 21H2', as "
                 "updated 26 June 2026, "
                 "https://learn.microsoft.com/en-us/windows/privacy/required-windows-diagnostic-data-events-and-fields-2004#microsoftwindowsinventorycoreinventoryapplicationadd). "
                 "The figures below are from af_case2_win10, lonewolf_win10 and szechuan_win10, Windows 10 builds "
                 "17763, 16299 and 19041, whose keys hold 95, 90 and 85 entries. Source was AppxPackage on 77, 65 "
                 "and 78 entries, Msi on 11, 18 and 5, AddRemoveProgram on 6, 6 and 2, and AddRemoveProgramPerUser "
                 "on 1, 1 and 0. Psmths describes AddRemoveProgram as software installed by an executable, Msi as "
                 "software installed from a .msi file by the Windows Installer service and AppXPackage as software "
                 "installed through the Windows Store, with a mention of the Get-AppxPackage PowerShell command, and "
                 "lists no per-user value "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L62-L66). "
                 "Registry Key Path and Install Date (as stored) are filled on the 50 entries whose Source is not "
                 "AppxPackage and blank on the 220 whose Source is; Package Full Name is filled on those 220 and "
                 "blank on the 50. Each of the 50 Registry Key Paths names an Uninstall key the same image holds: 48 "
                 "in the SOFTWARE hive and 2, written as HKEY_USERS and a user's SID, in one user's NTUSER.DAT, "
                 "found there by the key's name without matching the SID to the hive. Name, Version and Publisher "
                 "equalled that key's DisplayName, DisplayVersion and Publisher on all 50. Uninstall String equalled "
                 "its UninstallString on 48, 4 of them blank in both, and on the other 2 lacked only a trailing "
                 "space the Uninstall key holds. Root Folder equalled the key's InstallLocation on 34, 12 of them "
                 "blank in both, and was filled on the other 16, whose keys store no InstallLocation; how Windows "
                 "chose those folders was not established. Hidden ARP (as stored) was 1 on 20 of the 50, each naming "
                 "a key whose SystemComponent value is 1, and 0 on the other 30, none of which names such a key; "
                 "Microsoft describes the event's HiddenArp field as showing whether a program hides itself from the "
                 "installed-programs list. Install Date (as stored) is text in the form MM/DD/YYYY HH:MM:SS and is "
                 "not typed as a time, because it holds two kinds of value. On 33 of the 50 it is the Uninstall "
                 "key's InstallDate value, a date, followed by 00:00:00. On 14, whose Uninstall keys store no "
                 "InstallDate, it is that key's last-written time in UTC, to the second, on machines set to time "
                 "zones 4 to 8 hours behind UTC. The other 3 name Uninstall keys that were last written after the "
                 "Amcache entry was: 1 holds a time 4 seconds before the key's present last-written time, and 2 hold "
                 "the date 03/27/2018 where the key now stores 20180406, so on those 3 the entry differs from what "
                 "the Uninstall key holds now. Microsoft describes the event's InstallDate field as a best guess "
                 "based on folder creation dates; folder creation times were not compared here. OS Version At "
                 "Install held one value on every entry of an image, 10.0.0.17763, 10.0.0.16299 and 10.0.0.19041; "
                 "Microsoft describes the event field as the OS version at the time of the application's install. "
                 "Store App Type was blank on every entry of af_case2_win10 and lonewolf_win10, and on "
                 "szechuan_win10 held Win10StoreApp on 71 and CentennialStoreApp on 7 of the AppxPackage entries. "
                 "MSI Product Code was filled on 11 of 11, 16 of 18 and 5 of 5 Msi entries and on no other entry. "
                 "Program ID equalled the subkey's name on all 270 entries and is the value the Amcache Application "
                 "Files artifact reports for a file: 83 of 153, 123 of 292 and 83 of 98 of that artifact's rows on "
                 "these images carry a Program ID found here. Key Last Write (UTC) is the entry's registry "
                 "last-written time, not an install time: the entries of lonewolf_win10 were all written within 3 "
                 "seconds, those of szechuan_win10 within 51 seconds and those of af_case2_win10 within 5 minutes. "
                 "The key does not list every Uninstall key: 1 Uninstall key with a DisplayName on af_case2_win10, "
                 "last written after the newest entry, and 4 on szechuan_win10, all in user hives and 1 of them last "
                 "written after the newest entry, are named by no entry; lonewolf_win10 has none. Not reported: the "
                 "entry values Type ('Application' on all 270), Language, MsiPackageCode, ManifestPath, "
                 "BundleManifestPath, InboxModernApp and ProgramInstanceId, and the key's own LastScanTime value, "
                 "which Psmths describes as the last time the Appraiser ran "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L47) "
                 "and which only szechuan_win10 holds, equal there to the key's last-written time. pc_mus_001_win11 "
                 "(Windows 11 build 22621) holds the key with no subkeys, so no Windows 11 entry was tested. An "
                 "entry records that Windows inventoried the application; this artifact does not treat it as proof "
                 "that the application was run. Reading the hive needs the python-registry package. A dirty hive is "
                 "read after the entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are "
                 "applied, following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the key holds no subkeys)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 95 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 90 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 85 rows",
        },
    },
    "amcacheShortcuts": {
        "name": "Amcache Shortcuts",
        "description": "Shortcut (.lnk) paths Windows inventoried, from Amcache.hve InventoryApplicationShortcut, "
                       "with the time each entry was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryApplicationShortcut, a key Psmths's Amcache reference names among the hive's keys "
                 "without describing it (Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L41-L44). "
                 "No source describing its values was found, so the statements here are measurements on "
                 "af_case2_win10, lonewolf_win10 and szechuan_win10 (Windows 10 builds 17763, 16299 and 19041), "
                 "whose keys hold 53, 97 and 35 entries. Shortcut Path is ShortcutPath, the only value an entry "
                 "holds, as stored. Every path is on drive C, ends in .lnk and appears once, and a link file exists "
                 "at each of the 185 paths on the same image. 52, 73 and 35 of the paths are under a Start Menu "
                 "folder, 1, 9 and 0 on a user's Desktop, and 15, on lonewolf_win10, under a Microsoft Office folder "
                 "in Program Files (x86). The key does not list every link: 53, 40 and 88 link files under Start "
                 "Menu folders and 1, 0 and 4 on users' Desktops have no entry. Key Last Write (UTC) is the entry's "
                 "registry last-written time: on each image all entries were written within 2 seconds of each other, "
                 "and the link files' own times were not compared with it. The subkey's name is not reported; it is "
                 "the first 16 characters of the link's file name in lower case, a vertical bar and 15 or 16 "
                 "hexadecimal digits whose meaning was not established. No tested image holds an entry whose link "
                 "file is gone, so an entry for a deleted link was not exercised. pc_mus_001_win11 (Windows 11 build "
                 "22621) has no InventoryApplicationShortcut key. An entry records that Windows inventoried the "
                 "link; this artifact does not treat it as proof that the link or its target was used. Reading the "
                 "hive needs the python-registry package. A dirty hive is read after the entries in its .LOG1 and "
                 ".LOG2 transaction logs that continue its sequence are applied, following Maxim Suhanov's 'Windows "
                 "registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the hive has no InventoryApplicationShortcut key)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 53 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 97 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 35 rows",
        },
    },
}


def _value(entry, name):
    try:
        return entry.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return None


def _sha1(file_id):
    if isinstance(file_id, str) and len(file_id) == 44 and file_id.startswith('0000'):
        return file_id[4:]
    return file_id or ''


def _inventory_key(hive_path):
    reg = open_hive(hive_path)
    try:
        return reg.open(_INVENTORY_PATH)
    except Registry.RegistryKeyNotFoundException:
        return None


@artifact_processor
def amcacheApplicationFiles(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'File Path', 'SHA-1',
                    'Name', 'Publisher', 'Product Name', 'Version', 'Size (bytes)',
                    'Link Date', 'Program ID')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('amcache.hve')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            inventory = _inventory_key(source)
            if inventory is None:
                continue
            for entry in inventory.subkeys():
                written = entry.timestamp()
                if written is not None and written.tzinfo is None:
                    written = written.replace(tzinfo=timezone.utc)
                size = _value(entry, 'Size')
                data_list.append((
                    written,
                    _value(entry, 'LowerCaseLongPath') or '',
                    _sha1(_value(entry, 'FileId')),
                    _value(entry, 'Name') or '',
                    _value(entry, 'Publisher') or '',
                    _value(entry, 'ProductName') or '',
                    _value(entry, 'Version') or '',
                    '' if size is None else size,
                    _value(entry, 'LinkDate') or '',
                    _value(entry, 'ProgramId') or ''))
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Amcache: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)


def _stored(entry, name):
    """The value as stored, or '' when the entry has no such value (a stored 0 stays 0)."""
    value = _value(entry, name)
    return '' if value is None else value


def _written(entry):
    written = entry.timestamp()
    if written is not None and written.tzinfo is None:
        written = written.replace(tzinfo=timezone.utc)
    return written


def application_row(entry):
    return (_written(entry), _stored(entry, 'InstallDate'), _stored(entry, 'Name'),
            _stored(entry, 'Version'), _stored(entry, 'Publisher'), _stored(entry, 'Source'),
            _stored(entry, 'StoreAppType'), _stored(entry, 'RootDirPath'),
            _stored(entry, 'UninstallString'), _stored(entry, 'RegistryKeyPath'),
            _stored(entry, 'PackageFullName'), _stored(entry, 'MsiProductCode'),
            _stored(entry, 'HiddenArp'), _stored(entry, 'OSVersionAtInstallTime'),
            _stored(entry, 'ProgramId'))


def shortcut_row(entry):
    return (_written(entry), _stored(entry, 'ShortcutPath'))


def _inventory_rows(context, key_path, row_of):
    """One row per subkey of key_path in each Amcache.hve found, and the hives read."""
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('amcache.hve')]:
        relative_source = context.get_relative_path(source)
        try:
            reg = open_hive(source)
            try:
                key = reg.open(key_path)
            except Registry.RegistryKeyNotFoundException:
                key = None
            if key is not None:
                for entry in key.subkeys():
                    data_list.append(row_of(entry))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Amcache: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
    return data_list, "\n".join(sources)


@artifact_processor
def amcacheApplications(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Install Date (as stored)', 'Name',
                    'Version', 'Publisher', 'Source', 'Store App Type', 'Root Folder',
                    'Uninstall String', 'Registry Key Path', 'Package Full Name',
                    'MSI Product Code', 'Hidden ARP (as stored)', 'OS Version At Install',
                    'Program ID')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _APPLICATION_PATH, application_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheShortcuts(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Shortcut Path')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _SHORTCUT_PATH, shortcut_row)
    return data_headers, data_list, sources
