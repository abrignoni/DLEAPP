"""Windows taskbar pin list (Taskband Favorites) for DLEAPP.

Author: @AlexisBrignoni, Claude.
Explorer keeps the programs pinned to the taskbar in the Favorites value of
Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Taskband in each user's NTUSER.DAT. No Microsoft
documentation of the value was found. The framing of the value is read as measured on the corpus and on known
data made on a Windows 11 VM (corpus key windows11_arm_taskband_known_20261104); each pin is a Windows shell
item list, read with the shell item and extension block layouts of libyal libfwsi and, for packaged apps, the
property store layout of libyal libfwps, as the notes say.
"""

import os
import struct
import uuid

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_lnk import parse_lnk, target_path
from scripts.windows_registry import Registry, filetime_bytes_utc, open_hive, open_key, user_from_path

_KEY = r'Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband'
_USER_PINNED = '1f3427c8-5c10-4210-aa03-2ee45287d668'
_APPS_FOLDER = '4234d49b-0245-4df3-b780-3893943456e1'
_PKEY_APPUSERMODEL_ID = ('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3', 5)
_PKEY_ITEMNAMEDISPLAY = ('b725f130-47ef-101a-a5f1-02608c9eebac', 10)
_PINS_FOLDER = 'internet explorer/quick launch/user pinned'

__artifacts_v2__ = {
    "windowsTaskbandPins": {
        "name": "Taskbar Pins",
        "description": "The programs pinned to each user's taskbar, from the Taskband Favorites value of "
                       "NTUSER.DAT, in the order the value stores them (on known data the taskbar's left to right "
                       "order), with the time stored in each pin item (on known data the time of pinning) where the "
                       "item carries one, and the pin's shortcut in the taskbar pins folder where the extraction "
                       "holds it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none (vendored regfprobe)",
        "category": "Windows",
        "notes": "One row per pin in the Favorites value of Software\\Microsoft\\Windows\\CurrentVersion\\Explorer"
                 "\\Taskband in each NTUSER.DAT. No Microsoft documentation of the value was found. Its framing "
                 "is read as measured: a 0x00 byte, then for each pin a 32-bit length and a shell item list of "
                 "that length followed by one byte, 0x00 between pins and 0xFF after the last. This consumed the "
                 "value exactly on all 21 hives that hold one across the 15 corpus images surveyed (14 hold "
                 "one) and at every step of the known data; any other byte, or a length past the end, is named in the run log and stops "
                 "the read of that value. Eric Zimmerman's RegistryPlugins Taskband plugin reads the value with "
                 "the same framing, one leading byte, then per pin a 32-bit length and a one-byte separator (https://github.com/EricZimmerman/RegistryPlugins/blob/"
                 "bf564d6c4fcabf67b5ce4428ddf5e4a769b1e9ba/RegistryPlugin.Taskband/Taskband.cs#L76-L92). Shell "
                 "items and their extension blocks are read with the layouts of libyal libfwsi "
                 "(https://github.com/libyal/libfwsi/blob/996128afc64961dbfddf17b176ceff21c499b7d3/documentation/"
                 "Windows%20Shell%20Item%20format.asciidoc). What the columns mean rests on known data made on "
                 "Windows 11 build 26200 (corpus key windows11_arm_taskband_known_20261104): a Win32 program and "
                 "a packaged app were pinned from their taskbar buttons, one was dragged to the first place, one "
                 "of those pins and a default pin were unpinned, and the value was read after each step "
                 "(mint/steps beside the known data). Position is the pin's place in the value, from 1. At every "
                 "step the App IDs of the pins in value order equalled those of the pinned taskbar buttons from "
                 "left to right as UI Automation listed them, and dragging a pin to the first place moved it "
                 "first in the value. Pinned (UTC) is the FILETIME in the pin item's 0xbeef002b extension block, "
                 "which libfwsi does not describe. The two pins made on the VM held a time 0.27 and 0.04 seconds "
                 "after the menu click and before the key was written; the reorder and an Explorer restart left "
                 "every pin's time unchanged. The Win32 pin made on the VM held the last access time its new "
                 "shortcut had when the key was written; the default File Explorer pin's time did not match its "
                 "shortcut's access time when it was read. The four default pins on the VM held times within 1.3 seconds of the creation "
                 "times of the pins folder's files. Pinned (UTC) is blank when the item has no such block, which "
                 "was so on every row of the corpus hives of Windows 7 (build 7601), Windows 8.1 and Server 2012 "
                 "R2 (build 9600), and builds 16299 and 17763 (Windows 10 and Server 2019), so on "
                 "cfreds_leakage_win7 Pinned (UTC) has no value on any row; it held a time on every row of builds "
                 "19041, 20348, 22621, 26100 and 26200. App ID (as stored) is the text of the item's first "
                 "0xbeef001d block or, for a packaged app whose item has no such block, System.AppUserModel.ID "
                 "from its property store (the 2 packaged pins of alihadi_challenge3_win81), and Pin Type (as stored) that of its 0xbeef001e block, read from byte 10 of "
                 "the block as RegistryPlugins' ExtensionBlocks library reads them "
                 "(https://github.com/EricZimmerman/ExtensionBlocks/blob/6dd29c0318c15d16ac86755dba021f35913461d1/"
                 "ExtensionBlocks/Beef001e.cs#L16-L22). App ID equalled the taskbar button's app ID on every pin "
                 "at every step. Seven items held two 0xbeef001d blocks (the Outlook pin on five corpus hives "
                 "and on the known data, and Calculator on the known data); the first is reported, and Outlook's "
                 "second differed from it in the case of one letter. For a Win32 program App ID held a known "
                 "folder GUID and the program's file name ({1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\charmap.exe on "
                 "the VM); on the corpus 40 of the 46 Shortcut rows hold a bare identifier instead. Both pins made on the VM were UserPinned; the four default pins there were "
                 "SystemPinned (three) and ProgrammableRestored (Outlook). What wrote each value on the corpus "
                 "images is not established; the items of Windows 7, 8.1 and Server 2012 R2 have no 0xbeef001e "
                 "block, so Pin Type is blank on all their rows, and on szechuan_win10 Pin Type held SystemPinned "
                 "on all 16 rows. Kind is Shortcut when the item list is the User Pinned folder, one or more "
                 "folders and a file (one folder on every pin seen), Packaged app when it is the Applications "
                 "folder and an item with the APPS signature, and "
                 "Other with the root as stored otherwise (none seen); on cfreds_leakage_win7 Kind held Shortcut "
                 "on all 12 rows. For a Shortcut, Shortcut File is the file's long name from its 0xbeef0004 "
                 "block, Shortcut Found says whether the same user's AppData\\Roaming\\Microsoft\\Internet "
                 "Explorer\\Quick Launch\\User Pinned folder in the extraction holds a file of that name in that "
                 "folder, and Shortcut Target is the local path, share path or rebuilt shell path that the shell "
                 "link parser of Recent Shell Links (LNK) returns for that file; for File Explorer's link on "
                 "Windows 8.1 and later it is a GUID in braces. It is blank where the link holds none of those "
                 "(6 of 12 rows on cfreds_leakage_win7, 1 of 3 on szechuan_dc01_server2012r2). Shortcut Found "
                 "was Yes on all 38 shortcut pins of the corpus images that hold the folder. On the VM pinning a "
                 "Win32 program created its shortcut in that folder and unpinning deleted it, a default pin's "
                 "included; a packaged app's pin had no file. A shortcut put in the folder without pinning did "
                 "not appear on the taskbar, also after Explorer restarted, and the value did not change, so on "
                 "that VM a file in the folder was not by itself a pin. For a "
                 "Packaged app, App Name is System.ItemNameDisplay "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/"
                 "desktop-src/properties/props-system-itemnamedisplay.md?plain=1#L18-L20) from the item's "
                 "property store, read with the layout of libyal libfwps "
                 "(https://github.com/libyal/libfwps/blob/4798bd0c448c9b7f833d51a7835d9d5b2f20c8f9/documentation/"
                 "Windows%20Property%20Store%20format.asciidoc); App Name is blank on every Shortcut row, so on "
                 "cfreds_leakage_win7 it holds no value. User is taken from the path, and held one value on "
                 "images where one profile holds the value. Not read: FavoritesResolve, which holds one shell "
                 "link per pin to the pin's shortcut file or the Applications folder (everything above comes "
                 "from Favorites); FavoritesChanges, which rose by 2 per pin and by 1 per reorder and unpin on the "
                 "VM; FavoritesRemovedChanges, which did not change; and the AuxilliaryPins subkey. A row records "
                 "that the pin was in the list when the hive was written, not that the program ran or who pinned "
                 "it. A dirty hive is read after its .LOG1 and .LOG2 logs are applied when they can be, as in the "
                 "other registry artifacts. Start menu pins are not covered.",
        "paths": ('*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt]',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Users/*/AppData/Roaming/Microsoft/Internet Explorer/Quick Launch/User Pinned/*'),
        "output_types": ["standard"],
        "artifact_icon": "pin",
        "sample_data": {
            "windows11_arm_taskband_known_20261104": "Windows 11 build 26200 | 4 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 7 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 4 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 4 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 16 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 4 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 6 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 6 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 3 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 12 rows",
            "cfreds_hacking_case_winxp": "Windows XP | 0 rows (no Taskband key)",
        },
    },
}


def favorites_entries(data):
    """The shell item list of each pin in a Favorites value, and a problem string or ''."""
    entries = []
    if not data:
        return entries, ''
    pos = 0
    while pos < len(data):
        marker = data[pos]
        if marker == 0xFF and pos == len(data) - 1 and entries:
            return entries, ''
        if marker != 0x00:
            return entries, f'byte 0x{marker:02x} at offset {pos} where 0x00 or a final 0xff was expected'
        if pos + 5 > len(data):
            return entries, f'value ends at offset {len(data)} inside a pin length'
        size = struct.unpack_from('<I', data, pos + 1)[0]
        start = pos + 5
        if start + size > len(data):
            return entries, f'pin at offset {pos} claims {size} bytes, past the end of the value'
        entries.append(bytes(data[start:start + size]))
        pos = start + size
    return entries, 'value ends without the final 0xff'


def shell_items(id_list):
    """The shell items of an item id list, up to its terminator (libfwsi)."""
    items = []
    pos = 0
    while pos + 2 <= len(id_list):
        size = struct.unpack_from('<H', id_list, pos)[0]
        if size == 0:
            break
        if size < 3 or pos + size > len(id_list):
            return None
        items.append(id_list[pos:pos + size])
        pos += size
    return items


def extension_blocks(item):
    """{block type: block bytes} for the extension blocks of a shell item, walked from the first extension
    block offset in the item's last two bytes (libfwsi, Extension blocks)."""
    blocks = {}
    if len(item) < 12:
        return blocks
    pos = struct.unpack_from('<H', item, len(item) - 2)[0]
    if pos < 4 or pos + 8 > len(item):
        return blocks
    while pos + 8 <= len(item) - 2:
        size, _version, signature = struct.unpack_from('<HHI', item, pos)
        if size < 10 or signature >> 16 != 0xBEEF or pos + size > len(item):
            break
        blocks.setdefault(signature & 0xFFFF, item[pos:pos + size])
        pos += size
    return blocks


def _utf16z(data, pos):
    end = pos
    while end + 1 < len(data) and data[end:end + 2] != b'\x00\x00':
        end += 2
    return data[pos:end].decode('utf-16-le', 'replace')


def block_text(block):
    """The UTF-16 text of a 0xbeef001d or 0xbeef001e block, from byte 10 to the end-of-string."""
    return _utf16z(block, 10) if block and len(block) > 12 else ''


def long_name(block):
    """The long name in a 0xbeef0004 block, at the long name offset stored at byte 16 (libfwsi)."""
    if not block or len(block) < 18:
        return ''
    offset = struct.unpack_from('<H', block, 16)[0]
    return _utf16z(block, offset) if 18 <= offset < len(block) else ''


def _guid(data):
    return str(uuid.UUID(bytes_le=bytes(data[:16])))


def property_values(data, start):
    """{(format id, property id): string} for the VT_LPWSTR numeric records of the property sets from start,
    per libfwps: each set is a size, "1SPS", a format id and records, and a size of 0 ends the run."""
    values = {}
    pos = start
    while pos + 4 <= len(data):
        size = struct.unpack_from('<I', data, pos)[0]
        if size == 0 or size < 24 or pos + size > len(data) or data[pos + 4:pos + 8] != b'1SPS':
            break
        format_id = _guid(data[pos + 8:pos + 24])
        record = pos + 24
        while record + 13 <= pos + size and format_id != 'd5cdd505-2e9c-101b-9397-08002b2cf9ae':
            record_size = struct.unpack_from('<I', data, record)[0]
            if record_size == 0 or record + record_size > pos + size:
                break
            prop_id = struct.unpack_from('<I', data, record + 4)[0]
            if struct.unpack_from('<H', data, record + 9)[0] == 0x1F and record_size >= 17:
                count = struct.unpack_from('<I', data, record + 13)[0]
                text = data[record + 17:record + 17 + 2 * count].decode('utf-16-le', 'replace').rstrip('\x00')
                values[(format_id, prop_id)] = text
            record += record_size
        pos += size
    return values


def apps_properties(item):
    """The property values of an Applications folder item with the APPS signature (libfwsi). Its property
    sets begin at byte 22 on every such item read for this artifact; anything else yields nothing."""
    if len(item) < 30 or item[6:10] != b'APPS' or item[26:30] != b'1SPS':
        return {}
    return property_values(item, 22)


def read_pin(id_list):
    """(kind, shortcut folder parts, shortcut file, app id, pin type, pin time, app name) for one pin."""
    items = shell_items(id_list)
    if not items:
        return None
    last = items[-1]
    blocks = extension_blocks(last)
    app_id = block_text(blocks.get(0x1D))
    pin_type = block_text(blocks.get(0x1E))
    stamp = filetime_bytes_utc(blocks[0x2B][8:16]) if len(blocks.get(0x2B, b'')) >= 18 else ''
    root = _guid(items[0][4:20]) if items[0][2] == 0x1F and len(items[0]) >= 20 else ''
    if root == _APPS_FOLDER and len(items) == 2 and last[6:10] == b'APPS':
        props = apps_properties(last)
        return ('Packaged app', [], '', app_id or props.get(_PKEY_APPUSERMODEL_ID, ''), pin_type, stamp,
                props.get(_PKEY_ITEMNAMEDISPLAY, ''))
    if root == _USER_PINNED and len(items) >= 3 and all(0x30 <= item[2] <= 0x3F for item in items[1:]):
        folders = [long_name(extension_blocks(item).get(0x04)) for item in items[1:-1]]
        return 'Shortcut', folders, long_name(blocks.get(0x04)), app_id, pin_type, stamp, ''
    return f'Other ({{{root}}})' if root else 'Other', [], '', app_id, pin_type, stamp, ''


def _pins_files(context):
    """{(user lowered, path below User Pinned lowered): (source, relative)} for files in pins folders."""
    found = {}
    for source in sorted(str(f) for f in context.get_files_found()):
        if not os.path.isfile(source):
            continue
        relative = context.get_relative_path(source)
        lowered = relative.replace('\\', '/').lower()
        index = lowered.find('/appdata/roaming/microsoft/' + _PINS_FOLDER + '/')
        if index < 0:
            continue
        below = lowered[index + len('/appdata/roaming/microsoft/' + _PINS_FOLDER + '/'):]
        found[(user_from_path(relative).lower(), below)] = (source, relative)
    return found


def _shortcut_target(source):
    try:
        with open(source, 'rb') as handle:
            parsed = parse_lnk(handle.read())
    except OSError as exc:
        logfunc(f'Taskbar Pins: could not read the shortcut {os.path.basename(source)}: {exc}')
        return ''
    if parsed.get('error'):
        logfunc(f"Taskbar Pins: the shortcut {os.path.basename(source)} is not a readable shell link: "
                f"{parsed['error']}")
        return ''
    return target_path(parsed)


@artifact_processor
def windowsTaskbandPins(context):
    data_headers = (('Pinned (UTC)', 'datetime'), 'Position', 'User', 'Kind', 'App ID (as stored)', 'App Name',
                    'Shortcut File', 'Shortcut Found', 'Shortcut Target', 'Pin Type (as stored)')
    data_list = []
    sources = []
    label = 'Taskbar Pins'
    files = _pins_files(context)
    for source in sorted(str(f) for f in context.get_files_found()):
        if os.path.basename(source).upper() != 'NTUSER.DAT' or not os.path.isfile(source):
            continue
        relative = context.get_relative_path(source)
        user = user_from_path(relative)
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        key = open_key(reg, _KEY)
        if key is None:
            continue
        try:
            favorites = key.value('Favorites').raw_data()
        except Registry.RegistryValueNotFoundException:
            continue
        sources.append(source)
        entries, problem = favorites_entries(favorites)
        if problem:
            logfunc(f'{label}: {relative}: Favorites read stopped after {len(entries)} pin(s): {problem}')
        for position, id_list in enumerate(entries, 1):
            pin = read_pin(id_list)
            if pin is None:
                logfunc(f'{label}: {relative}: pin {position} is not a readable shell item list')
                continue
            kind, folders, shortcut, app_id, pin_type, stamp, app_name = pin
            found, target = '', ''
            if kind == 'Shortcut':
                hit = files.get((user.lower(), '/'.join(folders + [shortcut]).lower()))
                found = 'Yes' if hit else 'No'
                target = _shortcut_target(hit[0]) if hit else ''
                if hit:
                    sources.append(hit[0])
            data_list.append((stamp, position, user, kind, app_id, app_name, shortcut, found, target, pin_type))
    return data_headers, data_list, '\n'.join(sources)
