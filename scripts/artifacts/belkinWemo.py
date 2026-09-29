"""Belkin WeMo settings from its libnvram store and the XML files on its settings volume, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "belkinWemoNvram": {
        "name": "Belkin WeMo NVRAM Settings",
        "description": "Name and value strings from a Belkin libnvram store (NVRM header), the store format "
                       "of Belkin's libnvram library for WeMo devices.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Belkin WeMo",
        "notes": "Reads nvram.bin, the one-file volume qnxprobe 1.54 and later gives a libnvram store found "
                 "in a raw flash dump. The layout is env_image_gemtek in Belkin's own libnvram.c (its header "
                 "carries Belkin's copyright), as found in a public copy of the WeMo firmware tree (https://github.com/svenschwermer/wemo/blob/46d0ccd248806e8e07210f9b34166b127e9d3d52/"
                 "package/belkin_nvram_bd/src/libnvram.c#L97-L108): 'NVRM', a CRC-32, an entry count and the "
                 "offset of the end of the data, then NUL-separated strings. A file is read only when it opens "
                 "with 'NVRM' and the CRC-32 of the bytes after the 16-byte header equals the stored one, as "
                 "libnvram checks it (lines 853 to 874); a file that fails gives no row and is counted in the "
                 "run log. One row per string, up to the first empty one, in stored order (Position, from 1). "
                 "Name is the text before the first '=' and Value the rest, as stored, including any secret or "
                 "key; a string with no '=' is its own Name with Value blank. Bytes after the empty string are "
                 "not read. The header's entry count and end of data are not reported or checked, as the CRC-32 does not "
                 "cover them; a store whose count differs from the strings read is counted in the run log. Folder names the volume the "
                 "store came from, and holds one value on every row from one store. What each name means, and when a value was set, are not established; field "
                 "mapped from a private sample. The store records no time, and none is reported. Validated only against a "
                 "private sample; sample_data is left empty for that reason.",
        "paths": ("*/nvram.bin",),
        "output_types": "standard",
        "artifact_icon": "settings",
        "sample_data": {},
    },
    "belkinWemoDevice": {
        "name": "Belkin WeMo Device Description",
        "description": "Name, model, serial number, MAC address, UDN, firmware version and icon from a Belkin WeMo "
                       "device's setup.xml, the UPnP device description kept on its flash.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Belkin WeMo",
        "notes": "One row per setup.xml whose root element holds a device element in the urn:Belkin:device-1-0 "
                 "namespace. A WeMo serves a file of this shape over UPnP at /setup.xml, as recorded in pywemo's "
                 "test data "
                 "(https://github.com/pywemo/pywemo/blob/6dea7394e5f1e1958cdecbe78f41aafab101f110/tests/vcr/tests.ouimeaux_device.test_switch/WeMo_US_2.00.2769.PVT.yaml#L14-L26). "
                 "Friendly Name, Model Name, Model Number, Model Description, Serial Number, UDN, Hardware "
                 "Version, Firmware Version and Device Type are the friendlyName, modelName, modelNumber, "
                 "modelDescription, serialNumber, UDN, hwVersion, firmwareVersion and deviceType elements, as "
                 "stored; the UPnP Device Architecture 1.0 defines all but hwVersion and firmwareVersion "
                 "(https://upnp.org/specs/arch/UPnP-arch-DeviceArchitecture-v1.0.pdf, section 2.1). MAC Address "
                 "(as stored), Binary State (as stored) and Icon Version (as stored) are the macAddress, "
                 "binaryState and iconVersion elements, which the specification does not define; what they mean, "
                 "and when a value was written, are not established. Other Fields lists, as JSON, any other "
                 "element of the device that holds text and no child elements; the service and icon lists are not "
                 "listed there. Icon is the file named icon.jpg in the same folder as the setup.xml, used when "
                 "the icon list's first url names that file, with its format taken from its bytes, not from its "
                 "name or the mimetype element; the Icon column is blank when the url names another file or no "
                 "such file is present. Whether the icon was chosen by a person is not established. Modified "
                 "(UTC) is the modified time the filesystem records for setup.xml; whether the device's clock was "
                 "set when the file was written is not established. A setup.xml inside a firmware image's "
                 "sbin/web folder belongs to the firmware image and is not read; the run log counts those. Folder "
                 "names the volume the file came from. The other XML files beside setup.xml, such as "
                 "eventservice.xml, are UPnP service descriptions (root element scpd), which list the actions and "
                 "state variables a service offers; they are not read. Field mapped from a private sample. "
                 "Validated only against a private sample; sample_data is left empty for that reason.",
        "paths": ("*/setup.xml", "*/icon.jpg"),
        "output_types": "standard",
        "artifact_icon": "plug",
        "sample_data": {},
    },
    "belkinWemoManufactureData": {
        "name": "Belkin WeMo Manufacture Data",
        "description": "The fields of a Belkin WeMo device's ManufactureData.xml: serial number, MAC addresses, "
                       "SSID, firmware version and country codes, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-29",
        "last_update_date": "2026-09-29",
        "requirements": "none",
        "category": "Belkin WeMo",
        "notes": "One row per ManufactureData.xml whose root element is ManufactureData. Serial Number, STA MAC "
                 "Address, AP MAC Address, SSID (as stored), Firmware Version, Country Code and Target Country "
                 "are the SerialNumber, STAMacAddress, APMacAddress, SSID, FirmwareVersion, CountryCode and "
                 "TargetCountry elements, as stored. Serial Number, STA MAC Address, AP MAC Address, SSID (as "
                 "stored), Firmware Version, Country Code and Target Country are blank when their element is "
                 "missing or empty, and Other Fields is blank when the file holds no other element with text. No "
                 "published definition of this file's fields was found, so what each field means, including which "
                 "network the SSID names and which interface each MAC address belongs to, is not established; "
                 "field mapped from a private sample. Other Fields lists, as JSON, any other element that holds "
                 "text and no child elements. Modified (UTC) is the modified time the filesystem records for the "
                 "file; whether the device's clock was set when the file was written is not established. Folder "
                 "names the volume the file came from. Validated only against a private sample; sample_data is "
                 "left empty for that reason.",
        "paths": ("*/ManufactureData.xml",),
        "output_types": "standard",
        "artifact_icon": "list",
        "sample_data": {},
    },
}

import binascii
import json
import os
import struct
import xml.etree.ElementTree as ET
from collections import Counter

from scripts.ilapfuncs import artifact_processor, check_in_media, logfunc
from scripts.linux_links import recorded_time, seeker_of

MAGIC = b'NVRM'
HEADER = 16


def nvram_strings(data):
    """The NUL-separated strings after the header, up to the first empty one."""
    out = []
    pos = HEADER
    while pos < len(data):
        end = data.find(b'\x00', pos)
        if end < 0:
            end = len(data)
        if end == pos:
            break
        out.append(data[pos:end])
        pos = end + 1
    return out


def nvram_header(data):
    """(count, end of data) as the header stores them, for a store whose CRC-32 holds, else None."""
    if len(data) < HEADER or data[:4] != MAGIC:
        return None
    stored, count, eod = struct.unpack_from('<III', data, 4)
    if binascii.crc32(data[HEADER:]) != stored:
        return None
    return count, eod


@artifact_processor
def belkinWemoNvram(context):
    data_headers = ('Name', 'Value', 'Position', 'Folder')
    rows = []
    read = []
    counts = Counter()
    found = []
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) != 'nvram.bin':
            continue
        found.append((context.get_relative_path(path), path))
    for relative, path in sorted(found):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            counts['files that could not be read'] += 1
            continue
        header = nvram_header(data)
        if header is None:
            counts['files without an NVRM header whose CRC-32 holds, not read'] += 1
            continue
        strings = nvram_strings(data)
        if header[0] != len(strings):
            counts['stores whose header count differs from the strings read'] += 1
        for position, item in enumerate(strings, 1):
            name, _sep, value = item.partition(b'=')
            rows.append((name.decode('utf-8', 'backslashreplace'), value.decode('utf-8', 'backslashreplace'),
                         position, os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Belkin WeMo NVRAM Settings: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)


BELKIN_NS = '{urn:Belkin:device-1-0}'
DEVICE_COLUMNS = ('friendlyName', 'modelName', 'modelNumber', 'modelDescription', 'serialNumber', 'macAddress',
                  'UDN', 'firmwareVersion', 'hwVersion', 'binaryState', 'iconVersion', 'deviceType')
MANUFACTURE_COLUMNS = ('SerialNumber', 'STAMacAddress', 'APMacAddress', 'SSID', 'FirmwareVersion', 'CountryCode',
                       'TargetCountry')
FIRMWARE_WEB = '/sbin/web/'


def _found(context, name):
    """(relative path, staged path) for the files found with this base name, directories left out, in order."""
    out = []
    for path in (str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path) != name:
            continue
        out.append((context.get_relative_path(path), path))
    return sorted(out)


def _xml_root(path):
    """The parsed root element of an XML file, or None. The parser accepts a UTF-8 byte order mark."""
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
        return ET.fromstring(data)
    except (OSError, ET.ParseError):
        return None


def _leaf_texts(element, prefix=''):
    """{tag: text} for the children of element that hold text and no children, the namespace prefix removed."""
    out = {}
    for child in element:
        if len(child):
            continue
        tag = child.tag[len(prefix):] if prefix and child.tag.startswith(prefix) else child.tag
        text = (child.text or '').strip()
        if text and tag not in out:
            out[tag] = text
    return out


@artifact_processor
def belkinWemoDevice(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Friendly Name', 'Model Name', 'Model Number',
                    'Model Description', 'Serial Number', 'MAC Address (as stored)', 'UDN', 'Firmware Version',
                    'Hardware Version', 'Binary State (as stored)', 'Icon Version (as stored)', 'Device Type',
                    ('Icon', 'media'), 'Other Fields', 'Folder')
    seeker = seeker_of(context)
    icons = {}
    for relative, path in _found(context, 'icon.jpg'):
        icons[os.path.dirname('/' + relative.replace('\\', '/').lstrip('/'))] = path
    rows = []
    read = []
    counts = Counter()
    for relative, path in _found(context, 'setup.xml'):
        folder = os.path.dirname('/' + relative.replace('\\', '/').lstrip('/'))
        if FIRMWARE_WEB in folder + '/':
            counts['setup.xml files inside a firmware image\'s sbin/web folder, not read'] += 1
            continue
        root = _xml_root(path)
        device = root.find(BELKIN_NS + 'device') if root is not None else None
        if device is None:
            counts['setup.xml files that are not a Belkin device description, not read'] += 1
            continue
        fields = _leaf_texts(device, BELKIN_NS)
        shown = [fields.pop(tag, '') for tag in DEVICE_COLUMNS]
        icon_ref = ''
        url = device.findtext(f'{BELKIN_NS}iconList/{BELKIN_NS}icon/{BELKIN_NS}url') or ''
        name = url.strip().replace('\\', '/').rsplit('/', 1)[-1]
        icon_path = icons.get(folder) if name == 'icon.jpg' else None
        if icon_path:
            icon_ref = check_in_media(icon_path, name) or ''
            read.append(icon_path)
        elif url.strip():
            counts['icons named by setup.xml and not found in its folder'] += 1
        rows.append((recorded_time(seeker, path, None), *shown, icon_ref,
                     json.dumps(fields, sort_keys=True, ensure_ascii=False) if fields else '',
                     os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Belkin WeMo Device Description: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)


@artifact_processor
def belkinWemoManufactureData(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'Serial Number', 'STA MAC Address', 'AP MAC Address',
                    'SSID (as stored)', 'Firmware Version', 'Country Code', 'Target Country', 'Other Fields',
                    'Folder')
    seeker = seeker_of(context)
    rows = []
    read = []
    counts = Counter()
    for relative, path in _found(context, 'ManufactureData.xml'):
        root = _xml_root(path)
        if root is None or root.tag != 'ManufactureData':
            counts['files that are not a ManufactureData element, not read'] += 1
            continue
        fields = _leaf_texts(root)
        shown = [fields.pop(tag, '') for tag in MANUFACTURE_COLUMNS]
        rows.append((recorded_time(seeker, path, None), *shown,
                     json.dumps(fields, sort_keys=True, ensure_ascii=False) if fields else '',
                     os.path.dirname(relative)))
        read.append(path)
    if counts:
        logfunc('Belkin WeMo Manufacture Data: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)
