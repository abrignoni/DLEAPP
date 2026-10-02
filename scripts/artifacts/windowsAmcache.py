"""Windows Amcache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Amcache artifact; the implementation reads
the hive's on-disk structure directly and is not ported from that artifact.

The InventoryApplicationFile field meanings, including FileId being a SHA-1 of
the file (of its first 30 MiB when it is larger) prefixed with four zeroes, are
sourced from public Amcache research and measured on the test images (see the
artifact notes). The InventoryApplication values are compared with the Uninstall
keys they name, the InventoryApplicationShortcut paths with the link files, the
InventoryDriverBinary values with the driver files and the InventoryDevicePnp
values with the SYSTEM hive's Enum keys, on the same images. The
InventoryDeviceContainer entries are compared with the device entries that name
them, and the InventoryDriverPackage values with the driver store folder and the
INF file each names.
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
_DRIVER_PATH = "Root\\InventoryDriverBinary"
_DEVICE_PATH = "Root\\InventoryDevicePnp"
_CONTAINER_PATH = "Root\\InventoryDeviceContainer"
_PACKAGE_PATH = "Root\\InventoryDriverPackage"

__artifacts_v2__ = {
    "amcacheApplicationFiles": {
        "name": "Amcache Application Files",
        "description": "Files the system inventoried, from Amcache.hve InventoryApplicationFile: the file path, the "
                       "SHA-1 Amcache records for it, publisher, product and version, size and link date where the "
                       "entry holds them, the entry's key name, and the time the entry was written.",
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
                 "time. Entry Key is the subkey's name as stored: on every entry of the five tested images it is a "
                 "prefix, a vertical bar and 8 to 16 hexadecimal digits whose meaning was not established, and on "
                 "all 2,278 entries that hold a Name value the prefix is the first 16 characters of Name in lower "
                 "case. On windows11_arm_known_20261001, a capture made on 1 October 2026 of the hive of a Windows "
                 "11 build 26200 ARM64 virtual machine, 590 of the 2,179 entries hold only the FileId and ProgramId "
                 "values, so on those rows File Path, Name, Publisher, Product Name, Version, Size (bytes) and Link "
                 "Date are blank and Entry Key is all the row carries of the file's name; SHA-1 is blank on 120 of "
                 "the 590, whose FileId is empty. Those 590 entries were last written from August to October 2026, "
                 "and no entry of the four other images has that shape. The files of that machine were not captured, "
                 "so nothing on that image was compared with a file. An entry records that the file was inventoried; "
                 "this artifact does not treat "
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
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 2179 rows",
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
                 "StoreAppType, MSI Product Code is MsiProductCode, User SID is UserSid, Hidden ARP (as stored) is "
                 "HiddenArp, OS Version "
                 "At Install is OSVersionAtInstallTime, Program ID is ProgramId, and the other columns carry their "
                 "value's name. Microsoft's published field descriptions are for its InventoryApplicationAdd "
                 "diagnostic event, and none for the registry values was found; that event's fields carry the names "
                 "of 11 of the 15 values reported here, all but UninstallString, RegistryKeyPath, UserSid and "
                 "ProgramId "
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
                 "blank on the 50. User SID is blank on all 270, which hold no UserSid value. Each of the 50 "
                 "Registry Key Paths names an Uninstall key the same image holds: 48 "
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
                 "and which, of those three images, only szechuan_win10 holds, equal there to the key's last-written "
                 "time. pc_mus_001_win11 "
                 "(Windows 11 build 22621) holds the key with no subkeys. On windows11_arm_known_20261001, a capture "
                 "made on 1 October 2026 of the hive, the SOFTWARE hive and one user's NTUSER.DAT of a Windows 11 "
                 "build 26200 ARM64 virtual machine, the key holds 286 entries, all written within 3 seconds on 30 "
                 "July 2026, 63 days before the capture. Source was AppxPackage on 136, Msi on 123, AddRemoveProgram "
                 "on 23 and AddRemoveProgramPerUser on 4. No entry holds an OSVersionAtInstallTime or a Type value, "
                 "so OS Version At Install is blank on every row of that image. The 123 Msi entries hold a "
                 "MsiInstallDate value, equal to InstallDate on all 123 and not reported. Each entry also holds an "
                 "unnamed default value, 0 on all 286, which is not reported. User SID was filled on 15 entries and "
                 "held one value, the SID of the account the capture was made from: the 4 AddRemoveProgramPerUser "
                 "entries, whose Registry Key Path names that SID, and 11 Msi entries, whose Registry Key Path is "
                 "under HKEY_LOCAL_MACHINE. Registry Key Path and Install Date (as stored) are filled on the 150 "
                 "entries whose Source is not AppxPackage, and Package Full Name on the other 136. 149 of the 150 "
                 "Registry Key Paths name an Uninstall key the captured hives hold, 145 in SOFTWARE and 4 in the "
                 "user's hive; the other, an Msi entry, names a key the SOFTWARE hive does not hold. Name and "
                 "Publisher equalled the key's on all 149, and Version and Uninstall String on 146; the other 3 name "
                 "keys last written in September 2026, after the entries. On those 149, Hidden ARP (as stored) was 1 "
                 "on 115, each naming a key whose SystemComponent value is 1, and 0 on the other 34, none of which "
                 "does. Install Date (as stored) was the key's InstallDate followed by 00:00:00 on 127 and, on 17 "
                 "whose keys store no InstallDate, the key's last-written time in UTC, on a machine set 4 hours "
                 "behind UTC. The other 5 are the 3 whose keys were written after the entries and 2 AddRemoveProgram "
                 "entries whose keys store no InstallDate and which hold a time 5.4 and 5.7 hours before the key's "
                 "last-written time on the same day; that difference was not explained. Root Folder equalled the "
                 "key's InstallLocation on 16, was filled on 132 whose keys store none and differed from it on 1. "
                 "Store App Type was Win10StoreApp on 94 and CentennialStoreApp on 42 of the AppxPackage entries. "
                 "MSI Product Code was filled on all 123 Msi entries and on no other. Program ID equalled the "
                 "subkey's name on all 286, and 1,102 of the 2,179 Amcache Application Files rows of that image "
                 "carry a Program ID found here. 2 Uninstall keys with a DisplayName, both last written after the "
                 "newest entry, are named by no entry. The key's LastScanTime value there, read as a FILETIME, is "
                 "2.2 seconds after the newest entry was written and 4.1 hours before the key's own last-written "
                 "time. An "
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
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 286 rows",
        },
    },
    "amcacheShortcuts": {
        "name": "Amcache Shortcuts",
        "description": "Shortcut (.lnk) paths Windows inventoried, from Amcache.hve InventoryApplicationShortcut, "
                       "with the time each entry was written and, where the entry holds them, the shortcut's target "
                       "path, AUMID and program ID.",
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
                 "whose keys hold 53, 97 and 35 entries. Shortcut Path is ShortcutPath as stored, the only value an "
                 "entry holds on those three images, where Target Path, AUMID and Program ID are therefore blank on "
                 "every row. Every path is on drive C, ends in .lnk and appears once, and a link file exists "
                 "at each of the 185 paths on the same image. 52, 73 and 35 of the paths are under a Start Menu "
                 "folder, 1, 9 and 0 on a user's Desktop, and 15, on lonewolf_win10, under a Microsoft Office folder "
                 "in Program Files (x86). The key does not list every link: 53, 40 and 88 link files under Start "
                 "Menu folders and 1, 0 and 4 on users' Desktops have no entry. Key Last Write (UTC) is the entry's "
                 "registry last-written time: on each image all entries were written within 2 seconds of each other, "
                 "and the link files' own times were not compared with it. The subkey's name is not reported; it is "
                 "the first 16 characters of the link's file name in lower case, a vertical bar and 15 or 16 "
                 "hexadecimal digits whose meaning was not established. None of those three images holds an entry "
                 "whose link "
                 "file is gone, so an entry for a deleted link was not exercised. pc_mus_001_win11 (Windows 11 build "
                 "22621) has no InventoryApplicationShortcut key. On windows11_arm_known_20261001, a capture made on "
                 "1 October 2026 of the hive of a Windows 11 build 26200 ARM64 virtual machine, the key holds 124 "
                 "entries, all written within 2 seconds on 30 July 2026, 63 days before the capture, and each entry "
                 "also holds ShortcutTargetPath, ShortcutAumid and ShortcutProgramId values: Target Path is "
                 "ShortcutTargetPath, AUMID is ShortcutAumid and Program ID is ShortcutProgramId, each as stored. No "
                 "source describing those values was found. Each entry also holds an unnamed default value, 0 on all "
                 "124, which is not reported. Target Path and AUMID were filled on the same 120 entries and Program "
                 "ID on 22 of those. Each Target Path begins with a drive letter, and 91 of the 120, compared "
                 "without case, are the File Path of an Amcache Application Files row of the same image; the link "
                 "files were not captured, so Target Path was not compared with the target a link itself stores. "
                 "Each of the 22 Program IDs is the Program ID of an Amcache Application Files row and none is that "
                 "of an Amcache Applications row. AUMID begins with a GUID in braces on 85 entries and with a drive "
                 "letter on 3, and is other text on 32; what the GUIDs stand for was not established. Every Shortcut "
                 "Path there is on drive C, ends in .lnk and appears once: 117 are under a Start Menu folder, 5 on a "
                 "user's Desktop and 2 in a user's AppData\\Roaming\\Microsoft\\Internet Explorer\\Quick Launch\\User "
                 "Pinned\\TaskBar folder. The link files under the Start Menu and Desktop folders were listed at the "
                 "capture: one was listed at each of the 122 paths in those folders, and 28 listed link files, 27 "
                 "under Start Menu folders and 1 on a Desktop, have no entry; the 2 TaskBar paths are outside those "
                 "folders and were not checked against a file. The subkey names there have 14 to 16 hexadecimal "
                 "digits after the bar. An entry records that Windows inventoried the "
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
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 124 rows",
        },
    },
    "amcacheDrivers": {
        "name": "Amcache Drivers",
        "description": "Driver files Windows inventoried, from Amcache.hve InventoryDriverBinary: the driver's path, "
                       "the SHA-1 Amcache records for it, service, company, product and version, the in-box, signed "
                       "and kernel-mode values as stored, and the driver package name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryDriverBinary, a key Psmths's Amcache reference names among the hive's keys without "
                 "describing it (Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L41-L44). "
                 "Driver Path is the subkey's name. The other columns are values of the entry as stored, blank where "
                 "the entry lacks one: Driver Last Write (as stored) is DriverLastWriteTime, SHA-1 is DriverId "
                 "without its leading four zeroes (shown as stored when it does not have that shape), Driver Name is "
                 "DriverName, Company is DriverCompany, Driver Version is DriverVersion, In Box (as stored) is "
                 "DriverInBox, Signed (as stored) is DriverSigned, Kernel Mode (as stored) is DriverIsKernelMode, "
                 "INF is Inf, Driver Package is DriverPackageStrongName, PE Timestamp (as stored) is "
                 "DriverTimeStamp, and Service and Product carry their value's name. Microsoft's published field "
                 "descriptions are for its InventoryDriverBinaryAdd diagnostic event, and none for the registry "
                 "values was found; that event's fields carry the names of 11 of the 13 values reported here, all "
                 "but DriverId and DriverLastWriteTime (Microsoft, 'Required diagnostic events and fields for "
                 "Windows 10, versions 22H2 and 21H2', as updated 26 June 2026, "
                 "https://learn.microsoft.com/en-us/windows/privacy/required-windows-diagnostic-data-events-and-fields-2004#microsoftwindowsinventorycoreinventorydriverbinaryadd). "
                 "It describes DriverInBox as whether the driver is included with the operating system, DriverSigned "
                 "as whether the driver is signed, DriverIsKernelMode as whether it is a kernel mode driver, Service "
                 "as the name of the service installed for the device and DriverTimeStamp as the low 32 bits of the "
                 "driver file's time stamp. The figures below are from af_case2_win10, lonewolf_win10 and "
                 "szechuan_win10, Windows 10 builds 17763, 16299 and 19041, whose keys hold 358, 351 and 371 "
                 "entries; each driver file was copied out of the same image and compared. Driver Path is in lower "
                 "case with forward slashes and begins c:/ on all 1,080 entries, a file exists at that path on the "
                 "image for every one, and 354, 348 and 358 of the paths are under c:/windows/system32/drivers. "
                 "SHA-1 equalled the SHA-1 of the file on all 1,080; 6 of the files, 3 each on af_case2_win10 and "
                 "szechuan_win10, are stored on the volume in a WofCompressedData stream and were hashed after "
                 "decompressing it. Driver Last Write (as stored) is text in the form MM/DD/YYYY HH:MM:SS and "
                 "equalled the file's last-modified time in UTC, to the second, on all 1,080, on machines set to "
                 "time zones 4 to 8 hours behind UTC; it is the file's time, not a time the driver was loaded. PE "
                 "Timestamp (as stored) is a decimal number that equalled the TimeDateStamp of the file's PE header "
                 "on all 1,080; the PE format documentation describes that stamp as indicating when the file was "
                 "created "
                 "(https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L111). "
                 "Driver Name is the file name in Driver Path on all 1,080, and Driver Version, Product and Company "
                 "equalled the file version, ProductName and CompanyName of the file's version resource on all "
                 "1,080. Kernel Mode (as stored) was 1 on 346, 340 and 356 entries, each a file whose PE header "
                 "names the native subsystem, which that documentation gives to device drivers and native Windows "
                 "processes "
                 "(https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Debug/pe-format.md#L263), "
                 "and 0 on 12, 11 and 15, none of which does. In Box (as stored) was 0 on 11, 15 and 12 entries and "
                 "1 on the others. Signed (as stored) held one value, 1, on every entry of the three images; "
                 "signatures were not checked here. Service was filled on 358, 340 and 371 entries, and the SYSTEM "
                 "hive of the same image holds a Services key of that name for 346, 340 and 356. INF and Driver "
                 "Package were filled together, on 30, 59 and 48 entries. Key Last Write (UTC) is the entry's "
                 "registry last-written time, not a time the driver was installed or loaded: the entries of "
                 "af_case2_win10 and lonewolf_win10 were each written within 1 second and those of szechuan_win10 "
                 "within 8 seconds. Not reported: the entry values DriverCheckSum, DriverType, ImageSize, "
                 "ProductVersion and WdfVersion. pc_mus_001_win11 (Windows 11 build 22621) holds the key with no "
                 "subkeys. On windows11_arm_known_20261001, a capture made on 1 October 2026 of the hive and the "
                 "SYSTEM hive of a Windows 11 build 26200 ARM64 virtual machine, the key holds 317 entries, all "
                 "written within 1 second on 30 July 2026, 63 days before the capture; the driver files were not "
                 "captured, so no value was compared with a file there. Driver Path is in lower case with forward "
                 "slashes and begins c:/ on all 317, and 278 of the paths are under c:/windows/system32/drivers. "
                 "Signed (as stored) was 1 on all 317, In Box (as stored) was 0 on 10 and Kernel Mode (as stored) "
                 "was 1 on 299 and 0 on 18. Service was filled on all 317, and the SYSTEM hive holds a Services key "
                 "of that name for 299. INF and Driver Package were filled together, on 48 entries. Each entry there "
                 "also holds an unnamed default value, 0 on all 317, which is not reported. An entry records that "
                 "Windows inventoried the driver "
                 "file; this artifact does not treat it as proof that the driver was loaded. Reading the hive needs "
                 "the python-registry package. A dirty hive is read after the entries in its .LOG1 and .LOG2 "
                 "transaction logs that continue its sequence are applied, following Maxim Suhanov's 'Windows "
                 "registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the key holds no subkeys)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 358 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 351 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 371 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 317 rows",
        },
    },
    "amcacheDevices": {
        "name": "Amcache Devices",
        "description": "Plug and Play devices Windows inventoried, from Amcache.hve InventoryDevicePnp: the device "
                       "instance, model, manufacturer, class, service and driver, hardware IDs, and the install "
                       "dates where the entry holds them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryDevicePnp. No description of this key's values that could be relied on was found: "
                 "Microsoft's page for the InventoryDevicePnpAdd diagnostic event lists fields of these names, but "
                 "its descriptions do not line up with the names (it describes Enumerator as the date of the driver "
                 "loaded for the device), so they are not used here (Microsoft, 'Required diagnostic events and "
                 "fields for Windows 10, versions 22H2 and 21H2', as updated 26 June 2026, "
                 "https://learn.microsoft.com/en-us/windows/privacy/required-windows-diagnostic-data-events-and-fields-2004#microsoftwindowsinventorycoreinventorydevicepnpadd). "
                 "The statements here are measurements on af_case2_win10, lonewolf_win10 and szechuan_win10 (Windows "
                 "10 builds 17763, 16299 and 19041), whose keys hold 92, 131 and 201 entries, against the Enum key "
                 "of the current control set in each image's SYSTEM hive. Device is the subkey's name. The other "
                 "columns are values of the entry as stored, blank where the entry lacks one: Install Date (as "
                 "stored) is InstallDate, First Install Date (as stored) is FirstInstallDate, Bus Reported "
                 "Description is BusReportedDescription, Driver Name is DriverName, Driver SHA-1 is DriverId without "
                 "its leading four zeroes, Parent ID is ParentId, Container ID is ContainerId, Hardware IDs is HWID, "
                 "INF is Inf, and Model, Description, Manufacturer, Class, Enumerator and Service carry their "
                 "value's name. Device is in lower case with forward slashes and has three parts on all but 1 entry "
                 "of each image, whose Enumerator is ComputerHardwareId; on the others Enumerator is the first part. "
                 "Taken as three key names, one under the other, the parts name a key under Enum, compared without "
                 "case, for 91 of 91, 130 of 130 and 199 of 200 of those entries. Against those 420 Enum keys, "
                 "compared without case, Model equalled the DeviceDesc text and Manufacturer the Mfg text (the part "
                 "after the semicolon where the value begins with @) on all 420, Hardware IDs equalled the "
                 "HardwareID strings joined with commas on all 420, Service equalled Service on 418, and Description "
                 "equalled FriendlyName, or DeviceDesc where the key has no FriendlyName, on 418. Install Date (as "
                 "stored) and First Install Date (as stored) were blank on every entry of af_case2_win10 and "
                 "lonewolf_win10, whose entries hold no such values, and filled, as text in the form MM-DD-YYYY, on "
                 "200 of the 201 entries of szechuan_win10. Install Date (as stored) and First Install Date (as "
                 "stored) were identical on all 200. On all 199 of "
                 "those with an Enum key, each equalled the date, in UTC, of the time that key holds under "
                 "Properties\\{83da6326-97a6-4088-9453-a1923f573b29}\\0064 and \\0065; on 192 of them the date in the "
                 "machine's own time zone is a different day. 0064 and 0065 are 100 and 101 in hexadecimal, the "
                 "identifiers devpkey.h gives DEVPKEY_Device_InstallDate and DEVPKEY_Device_FirstInstallDate under "
                 "that GUID (mingw-w64, 'devpkey.h', "
                 "https://github.com/mingw-w64/mingw-w64/blob/49be363ce161977c8594534df488e298e775b8b2/mingw-w64-headers/include/devpkey.h#L105-L106), "
                 "which Microsoft documents as the time the device instance was last installed, changing with each "
                 "update of its driver, and the time it was first installed "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/devpkey-device-installdate.md#L30-L32, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/devpkey-device-firstinstalldate.md#L30). "
                 "Driver Name and Driver SHA-1 were filled together, on 74, 92 and 102 entries, and each Driver "
                 "SHA-1 is the SHA-1 of an Amcache Drivers row on the same image. Bus Reported Description was "
                 "filled on 49, 47 and 64 entries. Key Last Write (UTC) is the entry's registry last-written time: "
                 "92 of 92, 127 of 131 and 195 of 201 entries were written within a minute of the image's first, and "
                 "the last of the others 5.2 and 2.1 hours after it; what caused the later writes was not "
                 "established. Not reported: the entry's other values, among them ClassGuid, COMPID, MatchingID, "
                 "STACKID, Provider, DriverVerDate, DriverVerVersion, DriverPackageStrongName, DeviceState, "
                 "InstallState, ProblemCode and the four filter lists. pc_mus_001_win11 (Windows 11 build 22621) "
                 "holds the key with no subkeys. On windows11_arm_known_20261001, a capture made on 1 October 2026 "
                 "of the hive and the SYSTEM hive of a Windows 11 build 26200 ARM64 virtual machine, the key holds "
                 "81 entries, all written within 1 second on 30 July 2026, 63 days before the capture: 80 with "
                 "three-part names and 1 whose Enumerator is ComputerHardwareId. The parts name an Enum key for 77 "
                 "of the 80; the other 3, a storage volume and two audio endpoints, have none in the captured hive. "
                 "Against those 77 keys Model and Manufacturer matched on all 77, Hardware IDs and Service on 76 and "
                 "Description on 75. Install Date (as stored) and First Install Date (as stored) were filled on all "
                 "80 and differ from each other on 10. First Install Date (as stored) equalled the UTC date of the "
                 "Enum key's 0065 time on all 77. Install Date (as stored) equalled the UTC date of the 0064 time on "
                 "66; on the other 11 the Enum key holds a time later than the entry's last-written time. Driver "
                 "Name and Driver SHA-1 were filled together, on 68 entries, and each Driver SHA-1 is the SHA-1 of "
                 "an Amcache Drivers row of that image. Bus Reported Description was filled on 23 entries. Each "
                 "entry there also holds an unnamed default value, 0 on all 81, which is not reported. An entry "
                 "records that Windows "
                 "inventoried the device; this artifact does not treat it as proof of when the device was connected "
                 "or of who connected it. Reading the hive needs the python-registry package. A dirty hive is read "
                 "after the entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the key holds no subkeys)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 92 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 131 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 201 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 81 rows",
        },
    },
    "amcacheDeviceContainers": {
        "name": "Amcache Device Containers",
        "description": "Device containers Windows inventoried, from Amcache.hve InventoryDeviceContainer: the "
                       "identifier the hive gives the container, its friendly name, model, manufacturer and "
                       "categories, and the connected, active, paired, networked and machine-container values as "
                       "stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryDeviceContainer. Microsoft describes a container ID as the identification string "
                 "that groups the functional devices of one device installed in the computer, and calls each such "
                 "device instance the device container (Microsoft, 'Container ID', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/container-ids.md#L11-L13). "
                 "Container ID is the subkey's name. The other columns are values of the entry as stored, blank "
                 "where the entry lacks one: Friendly Name is FriendlyName, Model Name is ModelName, Model Number is "
                 "ModelNumber, Primary Category is PrimaryCategory, Machine Container (as stored) is "
                 "IsMachineContainer, Connected (as stored) is IsConnected, Active (as stored) is IsActive, Paired "
                 "(as stored) is IsPaired, Networked (as stored) is IsNetworked, Discovery Method is "
                 "DiscoveryMethod, State (as stored) is State, Model ID is ModelId, and Manufacturer, Categories and "
                 "Icon carry their value's name. Microsoft's published field descriptions are for its "
                 "InventoryDeviceContainerAdd diagnostic event, and none for the registry values was found; that "
                 "event's fields carry the names of 14 of the 15 values reported here, all but State (Microsoft, "
                 "'Required diagnostic events and fields for Windows 10, versions 22H2 and 21H2', as updated 26 June "
                 "2026, "
                 "https://learn.microsoft.com/en-us/windows/privacy/required-windows-diagnostic-data-events-and-fields-2004#microsoftwindowsinventorycoreinventorydevicecontaineradd). "
                 "It describes IsMachineContainer as whether the container is the root device itself, IsConnected as "
                 "the same as IsPresent for a physically attached device and a communication link for a wireless "
                 "one, IsActive as whether the device is connected or was seen in the last 14 days, IsPaired as "
                 "whether the device container requires pairing and IsNetworked as whether it is a networked device. "
                 "The figures below are from af_case2_win10, lonewolf_win10 and szechuan_win10 (Windows 10 builds "
                 "17763, 16299 and 19041), whose keys hold 7, 11 and 16 entries, against the Amcache Devices rows of "
                 "the same run and the SYSTEM hive of the same image. Container ID is a GUID in braces and lower "
                 "case on all 34 entries. It is the Container ID of Amcache Devices rows: 91 of 92, 125 of 131 and "
                 "194 of 201 device rows name a container that is a row here, and 6, 5 and 15 of the containers are "
                 "named by a device row. All 26 containers a device row names hold 1 in Connected (as stored), and 7 "
                 "of the 8 that none names hold 0. Container ID is not the container ID the SYSTEM hive records: "
                 "none of the 34 is the name of a key under Control\\DeviceContainers of the current control set, "
                 "which holds 7, 12 and 20 keys, and on none of the 91, 125 and 193 of those device rows that have a "
                 "key under Enum did it equal that key's ContainerID value. Across those rows each Container ID went "
                 "with one ContainerID value and each ContainerID value with one Container ID, 6, 5 and 14 pairs; "
                 "how the hive derives its identifier was not established. Of the 1, 6 and 7 device rows whose "
                 "Container ID is not a row here, 0, 5 and 6 have a key under Enum, and on all 11 the Container ID "
                 "equalled that key's ContainerID value. One entry of each image holds 1 in Machine Container (as "
                 "stored): its Friendly Name equalled the ComputerName value of the SYSTEM hive without case, its "
                 "Primary Category is computer, and the 84, 118 and 171 device rows that name it have Enum keys "
                 "whose ContainerID is {00000000-0000-0000-ffff-ffffffffffff}. State (as stored) is stored as a "
                 "number and the five values whose names begin with Is as text. On all 34 entries State (as stored) "
                 "equalled Connected (as stored) plus 8 times Active (as stored) plus 16 times Machine Container (as "
                 "stored): 25 on the 3 machine containers, 9 on 24 entries and 8 on 7. No description of State was "
                 "found. Active (as stored) held one value, 1, on all 34 entries, Paired (as stored) and Networked "
                 "(as stored) each held one value, 0, on all 34, and Connected (as stored) was 1 on 6, 6 and 15. "
                 "Discovery Method was blank on every entry of the three images. Model Number was blank on every "
                 "entry of af_case2_win10 and szechuan_win10 and filled on 1 of lonewolf_win10; Manufacturer was "
                 "blank on every entry of lonewolf_win10 and filled on 1 each of the other two. Friendly Name was "
                 "filled on 5, 5 and 11 entries, Model Name on 7, 10 and 16 and Model ID, a GUID in braces, on 6, 10 "
                 "and 15. Primary Category and Icon were filled on all 34, and Categories equalled Primary Category "
                 "on 7, 10 and 14. Key Last Write (UTC) is the entry's registry last-written time, not a time the "
                 "device was connected: the entries of each image were written within 3 seconds of each other, the "
                 "first of them within 1 second of the image's first Amcache Devices entry. pc_mus_001_win11 "
                 "(Windows 11 build 22621) holds the key with no subkeys. On windows11_arm_known_20261001, a capture "
                 "made on 1 October 2026 of the hive and the SYSTEM hive of a Windows 11 build 26200 ARM64 virtual "
                 "machine, the key holds 21 entries, all written within 1 second on 30 July 2026, 63 days before the "
                 "capture. 80 of its 81 device rows name a container that is a row here and 7 of the 21 containers "
                 "are named by a device row; the 7 hold 1 in Connected (as stored), and 13 of the other 14 hold 0. "
                 "None of the 21 is the name of a key under Control\\DeviceContainers, which holds 19, and on none of "
                 "the 77 device rows with a key under Enum did Container ID equal that key's ContainerID value; the "
                 "rows gave 5 pairs, each identifier with one of the other kind. One entry holds 1 in Machine "
                 "Container (as stored), and its Friendly Name equalled the ComputerName value without case. "
                 "Connected (as stored) was 1 on 8 entries and Active (as stored) 1 on 13; the 8 entries with 0 in "
                 "Active (as stored) all hold 0 in Connected (as stored). State (as stored) followed the same sum on "
                 "all 21: 0 on 8, 9 on 7, 8 on 5 and 25 on 1. Paired (as stored) and Networked (as stored) each held "
                 "one value, 0, on all 21 and Discovery Method was blank on all 21. Each entry there also holds an "
                 "unnamed default value, 0 on all 21, which is not reported. An entry records that Windows "
                 "inventoried the container; this artifact does not treat it as proof of when a device was connected "
                 "or of who connected it. Reading the hive needs the python-registry package. A dirty hive is read "
                 "after the entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "box",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the key holds no subkeys)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 7 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 11 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 16 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 21 rows",
        },
    },
    "amcacheDriverPackages": {
        "name": "Amcache Driver Packages",
        "description": "Driver packages Windows inventoried, from Amcache.hve InventoryDriverPackage: the package's "
                       "name, date, version, provider and device class, its directory, INF name, hardware IDs and "
                       ".sys file names, and the in-box and active values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one subkey of "
                 "Root\\InventoryDriverPackage. Driver Package is the subkey's name. The other columns are values of "
                 "the entry as stored, blank where the entry lacks one: Date (as stored) is Date, Class GUID is "
                 "ClassGuid, INF is Inf, Hardware IDs is Hwids, Files is SYSFILE, In Box (as stored) is DriverInBox, "
                 "Active (as stored) is IsActive, Submission ID is SubmissionId, and Version, Provider, Class and "
                 "Directory carry their value's name. Microsoft's published field descriptions are for its "
                 "InventoryDriverPackageAdd diagnostic event, and none for the registry values was found; that "
                 "event's fields carry the names of 9 of the 12 values reported here, all but Hwids, SYSFILE and "
                 "IsActive (Microsoft, 'Required diagnostic events and fields for Windows 10, versions 22H2 and "
                 "21H2', as updated 26 June 2026, "
                 "https://learn.microsoft.com/en-us/windows/privacy/required-windows-diagnostic-data-events-and-fields-2004#microsoftwindowsinventorycoreinventorydriverpackageadd). "
                 "It describes Date as the driver package date, Directory as the path to the driver package, "
                 "DriverInBox as whether the driver is included with the operating system, Inf as the INF name of "
                 "the driver package and SubmissionId as the HLK submission ID for the driver package. The figures "
                 "below are from af_case2_win10, lonewolf_win10 and szechuan_win10 (Windows 10 builds 17763, 16299 "
                 "and 19041), whose keys hold 3, 9 and 4 entries; the folder and the INF file each entry names were "
                 "looked up on the same image, and the SYSTEM hive of the same image was read. Driver Package has "
                 "the form of an INF file name, _amd64_ and 16 hexadecimal digits on all 16 entries. Directory is "
                 "c:\\windows\\system32\\driverstore\\filerepository\\ followed by Driver Package on all 16, and a folder "
                 "exists at that path on the image for all 16. Files is a list of file names ending .sys, joined "
                 "with commas: 6, 14 and 7 names, 3 of them on lonewolf_win10 with a subfolder before the name, and "
                 "a file of each name exists under Directory on the image for all 27. INF is of the form oemN.inf on "
                 "all 16, and a file of that name exists in Windows\\INF on the image for all 16. Each of those 16 "
                 "INF files holds one DriverVer directive, which Microsoft documents as "
                 "DriverVer=mm/dd/yyyy,w.x.y.z, the date of the driver package and a version number (Microsoft, 'INF "
                 "DriverVer Directive', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-driverver-directive.md#L24, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-driverver-directive.md#L29-L30, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-driverver-directive.md#L34-L35). "
                 "Date (as stored) is text in the form YYYY-M-D, without leading zeroes, and gave the directive's "
                 "date on all 16. Version equalled the directive's version as text on 14 and as four numbers on all "
                 "16; the other 2 INF files write parts with leading zeroes, as in 9.17.04.0002 against a stored "
                 "9.17.4.2. Class and Class GUID, stored in lower case, equalled the Class and ClassGuid entries of "
                 "the INF without case on all 16, and Provider equalled the INF's Provider entry, with its token "
                 "filled in from the INF's Strings section, on all 16 (Microsoft, 'INF Version Section', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-version-section.md#L61-L62, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-version-section.md#L73-L74, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/install/inf-version-section.md#L94-L95). "
                 "The SYSTEM hive's DriverDatabase\\DriverPackages key holds a subkey named as Driver Package for 2, "
                 "5 and 3 of the entries. On those 10 the subkey's default value equalled INF, its Provider value "
                 "equalled Provider, and its 48-byte Version value, read as a class GUID at byte 8, a FILETIME at "
                 "byte 24 and four 16-bit numbers at byte 32, gave Class GUID, the day in Date (as stored) and "
                 "Version. No description of that Version value or of the subkey's ImportDate value was found; the "
                 "reading is this comparison's. Key Last Write (UTC) is the entry's registry last-written time. It "
                 "is not the time the package's INF file was written to Windows\\INF: on all 16 entries it is 1.1 to "
                 "22.5 hours later than that file's last-modified time, which on the 10 with a DriverPackages subkey "
                 "is within 1 second of the subkey's ImportDate value read as a FILETIME. The entries of each image "
                 "were written within 13 seconds of each other; those of af_case2_win10 and lonewolf_win10 1.8 and "
                 "9.0 days before the image's first Amcache Drivers entry, and those of szechuan_win10 9 seconds "
                 "after it. In Box (as stored) held one value, 0, on all 16 entries. Active (as stored) was blank on "
                 "every entry of af_case2_win10 and lonewolf_win10, whose entries hold no IsActive value, and held "
                 "one value, 1, on all 4 of szechuan_win10. Submission ID was blank on 2 entries of lonewolf_win10 "
                 "and filled on the other 14. Provider held one value on every entry of af_case2_win10 and one on "
                 "every entry of szechuan_win10. Driver Package is the Driver Package of an Amcache Drivers row for "
                 "3, 9 and 3 of the entries, and every such row carries the entry's INF. INF is the INF of Amcache "
                 "Devices rows for 3, 9 and 4 of the entries: 4, 13 and 5 device rows, of which 4, 11 and 5 carry a "
                 "hardware ID that is in the entry's Hardware IDs. The key does not hold an entry for every "
                 "DriverPackages subkey of that kind: DriverDatabase\\DriverPackages holds 5, 6 and 5 subkeys whose "
                 "default value is of the form oemN.inf, of which 2, 5 and 3 are rows here, and 1, 4 and 1 rows have "
                 "no subkey there. pc_mus_001_win11 (Windows 11 build 22621) holds the key with no subkeys. On "
                 "windows11_arm_known_20261001, a capture made on 1 October 2026 of the hive and the SYSTEM hive of "
                 "a Windows 11 build 26200 ARM64 virtual machine, the key holds 31 entries; the folders and INF "
                 "files were not captured, so no value was compared with a file there. Driver Package has the same "
                 "form with _arm64_ on all 31, Directory is the same path followed by Driver Package on all 31, INF "
                 "is of the form oemN.inf on all 31, In Box (as stored) held one value, 0, and Active (as stored) "
                 "one value, 1, on all 31, and Submission ID was filled on all 31. DriverDatabase\\DriverPackages "
                 "holds a subkey for 26 of the 31, and on all 26 its default value, Provider and Version gave INF, "
                 "Provider, Class GUID, Date (as stored) and Version. Key Last Write (UTC) is 0.1 to 1,420.6 hours "
                 "later than the ImportDate value on those 26, within a day on 8. The 31 entries were written on 9 "
                 "dates from 9 August 2025 to 29 July 2026, 2 to 4 on each, where the capture's Amcache Drivers "
                 "entries were all written on 30 July 2026. 5 of the 31 are the Driver Package of an Amcache Drivers "
                 "row. DriverDatabase\\DriverPackages holds 67 subkeys whose default value is of the form oemN.inf, "
                 "of which 26 are rows here. Each entry there also holds FlightIds and RecoveryIds values, which are "
                 "not reported. An entry records that Windows inventoried the driver package; this artifact does not "
                 "treat it as proof that a driver of the package was loaded or that a device it names was connected. "
                 "Reading the hive needs the python-registry package. A dirty hive is read after the entries in its "
                 ".LOG1 and .LOG2 transaction logs that continue its sequence are applied, following Maxim Suhanov's "
                 "'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728); "
                 "the Amcache Application Files notes give the cases in which they are not applied, and the run log "
                 "names each hive replayed.",
        "paths": ('*/Windows/appcompat/Programs/Amcache.hve',
                  '*/Windows/appcompat/Programs/[Aa][Mm][Cc][Aa][Cc][Hh][Ee].[Hh][Vv][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "package",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the key holds no subkeys)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 3 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 9 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 4 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 31 rows",
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


def file_row(entry):
    written = entry.timestamp()
    if written is not None and written.tzinfo is None:
        written = written.replace(tzinfo=timezone.utc)
    size = _value(entry, 'Size')
    return (written,
            _value(entry, 'LowerCaseLongPath') or '',
            _sha1(_value(entry, 'FileId')),
            _value(entry, 'Name') or '',
            _value(entry, 'Publisher') or '',
            _value(entry, 'ProductName') or '',
            _value(entry, 'Version') or '',
            '' if size is None else size,
            _value(entry, 'LinkDate') or '',
            _value(entry, 'ProgramId') or '',
            entry.name())


@artifact_processor
def amcacheApplicationFiles(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'File Path', 'SHA-1',
                    'Name', 'Publisher', 'Product Name', 'Version', 'Size (bytes)',
                    'Link Date', 'Program ID', 'Entry Key')
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
                data_list.append(file_row(entry))
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
            _stored(entry, 'UserSid'), _stored(entry, 'HiddenArp'),
            _stored(entry, 'OSVersionAtInstallTime'), _stored(entry, 'ProgramId'))


def shortcut_row(entry):
    return (_written(entry), _stored(entry, 'ShortcutPath'), _stored(entry, 'ShortcutTargetPath'),
            _stored(entry, 'ShortcutAumid'), _stored(entry, 'ShortcutProgramId'))


def driver_row(entry):
    return (_written(entry), _stored(entry, 'DriverLastWriteTime'), entry.name(),
            _sha1(_value(entry, 'DriverId')), _stored(entry, 'DriverName'),
            _stored(entry, 'Service'), _stored(entry, 'DriverCompany'), _stored(entry, 'Product'),
            _stored(entry, 'DriverVersion'), _stored(entry, 'DriverInBox'),
            _stored(entry, 'DriverSigned'), _stored(entry, 'DriverIsKernelMode'),
            _stored(entry, 'Inf'), _stored(entry, 'DriverPackageStrongName'),
            _stored(entry, 'DriverTimeStamp'))


def device_row(entry):
    return (_written(entry), _stored(entry, 'InstallDate'), _stored(entry, 'FirstInstallDate'),
            entry.name(), _stored(entry, 'Model'), _stored(entry, 'Description'),
            _stored(entry, 'Manufacturer'), _stored(entry, 'Class'), _stored(entry, 'Enumerator'),
            _stored(entry, 'BusReportedDescription'), _stored(entry, 'Service'),
            _stored(entry, 'DriverName'), _sha1(_value(entry, 'DriverId')),
            _stored(entry, 'ParentId'), _stored(entry, 'ContainerId'), _stored(entry, 'HWID'),
            _stored(entry, 'Inf'))


def container_row(entry):
    return (_written(entry), entry.name(), _stored(entry, 'FriendlyName'), _stored(entry, 'ModelName'),
            _stored(entry, 'ModelNumber'), _stored(entry, 'Manufacturer'),
            _stored(entry, 'PrimaryCategory'), _stored(entry, 'Categories'),
            _stored(entry, 'IsMachineContainer'), _stored(entry, 'IsConnected'),
            _stored(entry, 'IsActive'), _stored(entry, 'IsPaired'), _stored(entry, 'IsNetworked'),
            _stored(entry, 'DiscoveryMethod'), _stored(entry, 'State'), _stored(entry, 'ModelId'),
            _stored(entry, 'Icon'))


def package_row(entry):
    return (_written(entry), _stored(entry, 'Date'), entry.name(), _stored(entry, 'Version'),
            _stored(entry, 'Provider'), _stored(entry, 'Class'), _stored(entry, 'ClassGuid'),
            _stored(entry, 'Directory'), _stored(entry, 'Inf'), _stored(entry, 'Hwids'),
            _stored(entry, 'SYSFILE'), _stored(entry, 'DriverInBox'), _stored(entry, 'IsActive'),
            _stored(entry, 'SubmissionId'))


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
                    'MSI Product Code', 'User SID', 'Hidden ARP (as stored)',
                    'OS Version At Install', 'Program ID')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _APPLICATION_PATH, application_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheShortcuts(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Shortcut Path', 'Target Path', 'AUMID',
                    'Program ID')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _SHORTCUT_PATH, shortcut_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheDrivers(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Driver Last Write (as stored)',
                    'Driver Path', 'SHA-1', 'Driver Name', 'Service', 'Company', 'Product',
                    'Driver Version', 'In Box (as stored)', 'Signed (as stored)',
                    'Kernel Mode (as stored)', 'INF', 'Driver Package',
                    'PE Timestamp (as stored)')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _DRIVER_PATH, driver_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheDevices(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Install Date (as stored)',
                    'First Install Date (as stored)', 'Device', 'Model', 'Description',
                    'Manufacturer', 'Class', 'Enumerator', 'Bus Reported Description', 'Service',
                    'Driver Name', 'Driver SHA-1', 'Parent ID', 'Container ID', 'Hardware IDs',
                    'INF')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _DEVICE_PATH, device_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheDeviceContainers(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Container ID', 'Friendly Name', 'Model Name',
                    'Model Number', 'Manufacturer', 'Primary Category', 'Categories',
                    'Machine Container (as stored)', 'Connected (as stored)', 'Active (as stored)',
                    'Paired (as stored)', 'Networked (as stored)', 'Discovery Method',
                    'State (as stored)', 'Model ID', 'Icon')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _CONTAINER_PATH, container_row)
    return data_headers, data_list, sources


@artifact_processor
def amcacheDriverPackages(context):
    data_headers = (('Key Last Write (UTC)', 'datetime'), 'Date (as stored)', 'Driver Package', 'Version',
                    'Provider', 'Class', 'Class GUID', 'Directory', 'INF', 'Hardware IDs', 'Files',
                    'In Box (as stored)', 'Active (as stored)', 'Submission ID')
    if Registry is None:
        logfunc('Amcache: the python-registry package is not installed')
        return data_headers, [], ''
    data_list, sources = _inventory_rows(context, _PACKAGE_PATH, package_row)
    return data_headers, data_list, sources
