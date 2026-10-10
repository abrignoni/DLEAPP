"""Monitors Windows recorded under Enum\\DISPLAY in the SYSTEM hive, with the identity in each monitor's EDID.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsMonitorEdid": {
        "name": "Monitors (EDID)",
        "description": "Monitors Windows recorded in the SYSTEM hive, one row per monitor instance, with the "
                       "manufacturer, product code, serial number, date of manufacture and name read from the "
                       "EDID data the monitor supplied.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each monitor instance under Enum\\DISPLAY of the SYSTEM hive's current control "
                 "set: Monitor ID is the name of the key under DISPLAY, Instance the name of the key under "
                 "that, Device Description the instance's DeviceDesc value as stored, and Key Last Written "
                 "(UTC) the last-written time of the instance key, which changes when any of its values is "
                 "written and is not established as the time the monitor was connected. The other columns come "
                 "from the EDID value of the instance's Device Parameters key, the data a monitor supplies to "
                 "describe itself (Microsoft, 'Overriding monitor EDIDs with an INF', "
                 "https://learn.microsoft.com/en-us/windows-hardware/drivers/display/overriding-monitor-edids); "
                 "an instance without that value, such as Default_Monitor, gives a row with those columns "
                 "empty. The first 128-byte block is read with the layout the Linux kernel's EDID header "
                 "defines (Reference: Linux v6.12, "
                 "https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/include/drm/drm_edid.h "
                 "lines 276 to 300 and 155 to 189): Manufacturer ID is the three letters packed in bytes 8 and "
                 "9 (lines 367 to 379), Product Code bytes 10 and 11 read low byte first and shown as four "
                 "hexadecimal digits (line 336), Serial Number the 32-bit number in bytes 12 to 15 read low "
                 "byte first, Week and Year the week and the year of manufacture, the year stored as a count "
                 "from 1990, and EDID Version the version and revision bytes. A Week of 0 means no week is "
                 "given and a Week of 255 means Year is a model year "
                 "(https://github.com/torvalds/linux/blob/adc218676eef25575469234709c2d87185ca223a/drivers/gpu/drm/drm_edid.c "
                 "lines 2728 to 2738). Monitor Name, Serial Text and Other Text are the text of the display "
                 "descriptors tagged 0xfc, 0xff and 0xfe (drm_edid.h lines 178 to 181), up to the line feed "
                 "that ends each, with bytes outside ASCII shown as escapes. Checksum Valid is Yes when the "
                 "block's 128 bytes add up to a multiple of 256, and EDID Size is the size of the stored "
                 "value; extension blocks are not read. A value that is shorter than a block or does not begin "
                 "with the EDID header (drm_edid.c lines 1754 to 1756) gives a row with only its size and a "
                 "line in the run log, tested with constructed input only. Serial Number is 0 on many "
                 "monitors, which then carry their serial, if any, in Serial Text. Three checks were made on "
                 "the four distinct EDID values of the six tested extractions (one on lonewolf_win10, one on "
                 "pc_mus_001_win11 and two on the build 26200 captures, whose Windows key names are SEC5441, "
                 "BOE0736 and PRL5000): Manufacturer ID followed by Product Code equals the Monitor ID Windows "
                 "gave the key on every row that has an EDID; every checksum is valid; and an independent "
                 "reader, pyedid 1.0.3, returns the same manufacturer, week, year, version and monitor name. "
                 "pyedid reads the product code and the serial number high byte first, so those two fields "
                 "were not compared with it: the product code rests on the kernel definition and on Windows' "
                 "own key names, and the byte order of Serial Number on the kernel source alone. Rows: "
                 "af_case2_win10 2 and szechuan_win10 3, all Default_Monitor without an EDID; lonewolf_win10 "
                 "4, three instances of one panel whose Serial Number is 0 and one Default_Monitor; "
                 "pc_mus_001_win11 1, with Serial Number 0, Week 1 and a 256-byte value; and the two build "
                 "26200 captures 2 each, a virtual monitor named Parallels Vu with a serial number, and one "
                 "Default_Monitor. On af_case2_win10 and szechuan_win10 the columns Manufacturer ID, Product "
                 "Code, Serial Number, Week, Year, EDID Version, Monitor Name, Serial Text, Other Text, EDID "
                 "Size and Checksum Valid were empty on every row, no row there having an EDID. On "
                 "szechuan_win10 Device Description held one value on all 3 rows, the description Windows "
                 "gives a monitor that is not Plug and Play. On lonewolf_win10 Monitor Name was empty on all 4 "
                 "rows, and Serial Number and Week were identical on all 4 rows, both 0 on the three panel "
                 "rows and both empty on the Default_Monitor row. On the two build 26200 captures Other Text "
                 "was empty on both rows. Serial Text was empty on every row of all six, so that column is "
                 "exercised with constructed input only. A row shows that Windows recorded the monitor on this "
                 "system, not when or how often it was connected. Source File is the hive. Reading the hive "
                 "requires the python-registry package; a dirty hive is read after its transaction logs are "
                 "applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "monitor",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 3 rows",
            "windows11_arm_7zip_known_20261010": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 2 rows",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 2 rows",
        },
    },
}

import struct

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import current_control_set, found_hives, key_written_utc, open_hive, open_key

_HEADER = b'\x00\xff\xff\xff\xff\xff\xff\x00'
# display descriptor tags and the column each fills
_TEXT_TAGS = {0xfc: 'name', 0xff: 'serial', 0xfe: 'text'}


def _descriptor_text(raw):
    """The text of a display descriptor's 13 bytes: up to the first line feed, without the spaces that pad it."""
    return raw.split(b'\n', 1)[0].decode('ascii', errors='backslashreplace').rstrip(' ')


def edid_fields(raw):
    """The identity fields of the first 128-byte block of an EDID: a dict with manufacturer (three letters), product
    (four hexadecimal digits), serial (number), week, year, version, name, serial_text, text and checksum_ok. None
    when the data is shorter than a block or does not start with the EDID header."""
    if len(raw) < 128 or raw[:8] != _HEADER:
        return None
    packed, product, serial, week, year, version, revision = struct.unpack_from('>H', raw, 8) + struct.unpack_from(
        '<HIBBBB', raw, 10)
    letters = ''.join(chr(64 + ((packed >> shift) & 0x1f)) for shift in (10, 5, 0))
    texts = {'name': [], 'serial': [], 'text': []}
    for start in (54, 72, 90, 108):
        block = raw[start:start + 18]
        if block[:3] == b'\x00\x00\x00' and block[3] in _TEXT_TAGS:
            texts[_TEXT_TAGS[block[3]]].append(_descriptor_text(block[5:18]))
    return {'manufacturer': letters, 'product': f'{product:04X}', 'serial': serial, 'week': week,
            'year': year + 1990, 'version': f'{version}.{revision}', 'name': ' | '.join(texts['name']),
            'serial_text': ' | '.join(texts['serial']), 'text': ' | '.join(texts['text']),
            'checksum_ok': sum(raw[:128]) % 256 == 0}


def monitor_rows(reg, control_set):
    """The rows for one SYSTEM hive: (key last written, monitor id, instance, device description, manufacturer,
    product, serial, week, year, version, name, serial text, other text, EDID size, checksum, key path), and the
    number of EDID values that are not an EDID."""
    rows, unread = [], 0
    base = control_set + '\\Enum\\DISPLAY'
    display = open_key(reg, base)
    for model in (display.subkeys() if display is not None else []):
        for instance in model.subkeys():
            description = ''
            for value in instance.values():
                if value.name().lower() == 'devicedesc' and isinstance(value.value(), str):
                    description = value.value()
            raw = None
            parameters = open_key(reg, f'{base}\\{model.name()}\\{instance.name()}\\Device Parameters')
            for value in (parameters.values() if parameters is not None else []):
                if value.name().lower() == 'edid':
                    raw = value.raw_data()
            fields = edid_fields(raw) if raw is not None else None
            if raw is not None and fields is None:
                unread += 1
            start = (key_written_utc(instance), model.name(), instance.name(), description)
            path = f'{base}\\{model.name()}\\{instance.name()}'
            if fields is None:
                rows.append(start + ('',) * 9 + ('' if raw is None else len(raw), '', path))
            else:
                rows.append(start + (fields['manufacturer'], fields['product'], fields['serial'], fields['week'],
                                     fields['year'], fields['version'], fields['name'], fields['serial_text'],
                                     fields['text'], len(raw), 'Yes' if fields['checksum_ok'] else 'No', path))
    return rows, unread


@artifact_processor
def windowsMonitorEdid(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Monitor ID', 'Instance', 'Device Description',
                    'Manufacturer ID', 'Product Code', 'Serial Number', 'Week', 'Year', 'EDID Version',
                    'Monitor Name', 'Serial Text', 'Other Text', 'EDID Size', 'Checksum Valid', 'Key',
                    'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Monitors (EDID): the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SYSTEM')):
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            rows, unread = monitor_rows(reg, current_control_set(reg))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Monitors (EDID): could not read {relative}: {exc}')
            continue
        if unread:
            logfunc(f'Monitors (EDID): {unread} EDID values of {relative} are not an EDID block and were not read')
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
