"""Windows startup entries' enabled or disabled state (StartupApproved) and Startup folder items, for DLEAPP.

Author: @AlexisBrignoni, Claude.
Settings > Apps > Startup and Task Manager's Startup apps page record whether a Run key entry or a Startup
folder item may start, in the StartupApproved keys of the user's NTUSER.DAT and of the SOFTWARE hive. No
Microsoft documentation of the value layout was found; what is read here was measured on known data made on
a Windows 11 VM (corpus key windows11_arm_startupapproved_known_20261104), as the notes say.
"""

import os
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, filetime_utc, open_hive, open_key, user_from_path,
                                      value_of)

_USER_BASE = r'Software\Microsoft\Windows\CurrentVersion'
_MACHINE_BASE = r'Microsoft\Windows\CurrentVersion'
_SUBKEYS = ('Run', 'Run32', 'StartupFolder')
_IGNORED_FILES = ('desktop.ini',)

__artifacts_v2__ = {
    "startupApproved": {
        "name": "Startup Approved States",
        "description": "Whether a Run key entry or Startup folder item was enabled or disabled in Settings "
                       "or Task Manager, and when it was disabled, from the StartupApproved keys of NTUSER.DAT "
                       "and SOFTWARE, with the entry it names where the extraction still holds it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per value in the Run, Run32 and StartupFolder subkeys of "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved in each NTUSER.DAT "
                 "(Scope User) and of Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved in SOFTWARE "
                 "(Scope Machine). Entry Name is the value name. No Microsoft documentation of the value was "
                 "found, so the reading rests on known data made on Windows 11 build 26200 (corpus key "
                 "windows11_arm_startupapproved_known_20261104): a Run value and Startup folder items were "
                 "turned off and on in Settings > Apps > Startup and on Task Manager's Startup apps page, and the "
                 "values read after each change (mint/step_reads.txt beside the known data). Every value written was 12 bytes. Flags (as stored) is its first "
                 "byte in hex. Settings wrote 00 (on) and 01 (off) for a user entry and 05 (off) and 04 (on) for "
                 "a machine Run entry; Task Manager wrote 02 (on) and 03 (off), rewrote the other values it "
                 "listed to that form, keeping their times, and rewrote a machine Run value of 04 to 06. State is "
                 "Disabled when the low bit of that byte is set and Enabled when it is clear, which matched every "
                 "measured value; a flag byte not in that list was not exercised and is read by the same bit. "
                 "Disabled Time (UTC) is the little-endian Windows FILETIME in bytes 4 to 11: on each tested "
                 "disable it was the time of the change (Task Manager's matched the moment its button was pressed "
                 "to the microsecond), and a value of 0, which every tested Enable wrote, is shown blank. "
                 "Turning an entry back on cleared its time, so an Enabled row keeps no record of an earlier "
                 "disable. A Run or Startup folder entry that had no StartupApproved value yet showed as on in "
                 "Settings on the VM; Task Manager's shown state was not recorded. Command "
                 "or File is, for a Run row, the data of the value of the same name in the same hive's "
                 "CurrentVersion\\Run key and, for a StartupFolder row, the path of the file of that name in the "
                 "same user's Startup folder (Scope User) or the all-users Startup folder (Scope Machine) when the "
                 "extraction holds one. Entry Found says whether it was found. On the VM, deleting a disabled Run "
                 "value and a disabled Startup file left both StartupApproved values in place, unchanged, so a "
                 "Disabled row whose entry is not found records an entry that was there and was turned off. Run32 "
                 "values are listed as stored and are not looked up (Entry Found is blank), because which key "
                 "they name was not tested; no Run32 value was present on the VM or on any corpus image. Of the "
                 "eight corpus images in sample_data, Windows Server 2019 "
                 "(alihadi_threatsim_server2019) holds the only disabled values, flag 03, in the Default profile "
                 "and in one user's hive. The tested entries were toggled by those two tools only. User is taken "
                 "from the path. A row records the entry's setting, not that the program ran or who changed it. "
                 "A dirty hive is read after its .LOG1 and .LOG2 logs are applied when they can be, as in the "
                 "other registry artifacts; the run log says when one was read as it is. Startup entries of "
                 "packaged (Store) apps, which Settings and Task Manager also list, are not recorded in these "
                 "keys and are not covered here.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/[Ss]tart[Uu]p/*',
                  '*/ProgramData/Microsoft/Windows/Start Menu/Programs/[Ss]tart[Uu]p/*'),
        "output_types": ["standard"],
        "artifact_icon": "toggle-left",
        "sample_data": {
            "windows11_arm_startupapproved_known_20261104": "Windows 11 build 26200 | 5 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1 row",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 0 rows (no StartupApproved key)",
        },
    },
    "startupFolderItems": {
        "name": "Startup Folder Items",
        "description": "Files in each user's Startup folder and in the ProgramData Startup folder, with the "
                       "item's StartupApproved state where one is recorded.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "python-registry for the State column",
        "category": "Windows",
        "notes": "One row per file in a Startup folder: AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"
                 "\\Startup under each user (Location User), ProgramData\\Microsoft\\Windows\\Start Menu\\Programs"
                 "\\StartUp (Location All users), and Start Menu\\Programs\\Startup under Documents and Settings on "
                 "Windows XP (Location User, or All users for the All Users folder); the Windows XP folders were "
                 "seen only with desktop.ini. desktop.ini is not listed. "
                 "File is the file name and Size (bytes) the size of the extracted copy. State and Disabled Time "
                 "(UTC) are read from the StartupApproved StartupFolder value of the same name, in the user's "
                 "NTUSER.DAT for a User item and in SOFTWARE for an All users item, as described in Startup "
                 "Approved States; both are blank when there is no such value. On the VM an item had no value "
                 "until it was first toggled, and Settings showed it as on. A shortcut's "
                 "own target is not read here. No Windows corpus image surveyed held a file in a Startup folder other than "
                 "desktop.ini; the rows come from the VM known data. A file being in a Startup folder does not show "
                 "that it ran. User is taken from the path.",
        "paths": ('*/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/[Ss]tart[Uu]p/*',
                  '*/ProgramData/Microsoft/Windows/Start Menu/Programs/[Ss]tart[Uu]p/*',
                  '*/Documents and Settings/*/Start Menu/Programs/[Ss]tart[Uu]p/*',
                  '*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "windows11_arm_startupapproved_known_20261104": "Windows 11 build 26200 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (Startup folders hold only desktop.ini)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (Startup folders hold only desktop.ini)",
        },
    },
}


def approved_value(raw):
    """(flags hex, state, disabled time) for one StartupApproved value's bytes."""
    if not isinstance(raw, (bytes, bytearray)) or not raw:
        return '', '', ''
    flags = f'{raw[0]:02x}'
    state = 'Disabled' if raw[0] & 1 else 'Enabled'
    stamp = filetime_utc(struct.unpack_from('<Q', bytes(raw), 4)[0]) if len(raw) >= 12 else ''
    return flags, state, stamp


def _norm(path):
    return path.replace('\\', '/')


def startup_location(relative):
    """('User' or 'All users', user) for a file in a Startup folder, or None for any other path."""
    parts = _norm(relative).split('/')
    lowered = [part.lower() for part in parts]
    if len(parts) < 2 or lowered[-2] != 'startup' or lowered[-3:-1] != ['programs', 'startup']:
        return None
    if 'programdata' in lowered:
        return 'All users', ''
    if 'documents and settings' in lowered:
        index = lowered.index('documents and settings')
        name = parts[index + 1] if index + 1 < len(parts) else ''
        return ('All users', '') if name.lower() == 'all users' else ('User', name)
    if 'users' in lowered and 'appdata' in lowered:
        return 'User', user_from_path(relative)
    return None


def _startup_files(context):
    """{(location, user lowered, file name lowered): (source, relative)} for every Startup folder file."""
    found = {}
    for source in [str(f) for f in context.get_files_found()]:
        if not os.path.isfile(source):
            continue
        relative = context.get_relative_path(source)
        place = startup_location(relative)
        name = os.path.basename(source)
        if place is None or name.lower() in _IGNORED_FILES:
            continue
        location, user = place
        found[(location, user.lower(), name.lower())] = (source, relative)
    return found


def _hives(context):
    """(source, relative, is machine, user) for each SOFTWARE and NTUSER.DAT found."""
    for source in sorted(str(f) for f in context.get_files_found()):
        name = os.path.basename(source).upper()
        if name not in ('SOFTWARE', 'NTUSER.DAT') or not os.path.isfile(source):
            continue
        relative = context.get_relative_path(source)
        machine = name == 'SOFTWARE'
        yield source, relative, machine, '' if machine else user_from_path(context.get_relative_path(source))


def _approved_values(reg, machine):
    """(subkey, value name, raw bytes) for every StartupApproved value in one hive."""
    base = (_MACHINE_BASE if machine else _USER_BASE) + r'\Explorer\StartupApproved'
    for subkey in _SUBKEYS:
        key = open_key(reg, base + '\\' + subkey)
        if key is None:
            continue
        for value in key.values():
            yield subkey, value.name(), value.raw_data()


@artifact_processor
def startupApproved(context):
    data_headers = (('Disabled Time (UTC)', 'datetime'), 'Entry Name', 'State', 'Flags (as stored)', 'Key',
                    'Scope', 'Entry Found', 'Command or File', 'User', 'Source File')
    data_list = []
    sources = []
    label = 'Startup Approved States'
    if Registry is None:
        logfunc(f'{label}: the python-registry package is not installed')
        return data_headers, data_list, ''
    files = _startup_files(context)
    for source, relative, machine, user in _hives(context):
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        run_key = open_key(reg, (_MACHINE_BASE if machine else _USER_BASE) + r'\Run')
        rows_here = 0
        for subkey, name, raw in _approved_values(reg, machine):
            flags, state, stamp = approved_value(raw)
            found, target = '', ''
            if subkey == 'Run':
                command = value_of(run_key, name)
                found = 'No' if command is None else 'Yes'
                target = '' if command is None else str(command)
            elif subkey == 'StartupFolder':
                hit = files.get(('All users' if machine else 'User', user.lower(), name.lower()))
                found = 'No' if hit is None else 'Yes'
                target = '' if hit is None else context.get_relative_path(hit[0])
            data_list.append((stamp, name, state, flags, subkey, 'Machine' if machine else 'User', found, target,
                              user, relative))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def startupFolderItems(context):
    data_headers = (('Disabled Time (UTC)', 'datetime'), 'File', 'Location', 'State', 'Size (bytes)', 'User',
                    'Source File')
    data_list = []
    sources = []
    label = 'Startup Folder Items'
    states = {}
    if Registry is not None:
        for source, relative, machine, user in _hives(context):
            try:
                reg = open_hive(source, context)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logfunc(f'{label}: could not read {relative}: {exc}')
                continue
            for subkey, name, raw in _approved_values(reg, machine):
                if subkey == 'StartupFolder':
                    states[('All users' if machine else 'User', user.lower(), name.lower())] = approved_value(raw)
    else:
        logfunc(f'{label}: the python-registry package is not installed, so State is blank')
    for (location, user_key, name_key), (source, relative) in sorted(_startup_files(context).items()):
        _flags, state, stamp = states.get((location, user_key, name_key), ('', '', ''))
        user = startup_location(context.get_relative_path(source))[1]
        data_list.append((stamp, os.path.basename(source), location, state, os.path.getsize(source), user,
                          relative))
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
