"""Display configurations GNOME's mutter keeps in monitors.xml, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxMonitorsXml": {
        "name": "Display Configurations (monitors.xml)",
        "description": "Monitors recorded in GNOME's monitors.xml, one row per monitor of each stored configuration: "
                       "connector, vendor, product and serial as the monitor reported them, with the mode and "
                       "position it was set to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads monitors.xml, where GNOME's mutter stores the display configurations a user applied, from "
                 "the user's configuration folder and from the system configuration folders such as /etc/xdg "
                 "(Reference: mutter 50.1, commit 8e9bb806da4a6a4fc87aa4a481b228dba6735cbd, "
                 "'src/backends/meta-monitor-config-store.c' lines 2828 to 2870, "
                 "https://gitlab.gnome.org/GNOME/mutter), and the backup monitors.xml~ that the save asks GLib to "
                 "make (lines 2582 to 2588). Only format version 2 is read, the one this mutter writes and accepts "
                 "(lines 30 and 276 to 287); a file with another version, and one that is not XML with a monitors "
                 "root, is counted in the run log. One row is reported per monitor of each configuration element, as "
                 "the source's own example lays them out (lines 36 to 101): State is Enabled for a monitor inside a "
                 "logicalmonitor, Disabled for one listed under disabled and For Lease for one under forlease. "
                 "Configuration is the number of the configuration element in the file. Connector, Vendor, Product "
                 "and Serial are the four parts of the monitor's specification as stored. Width, Height and Refresh "
                 "Rate are the mode stored for the monitor, X and Y the position of its logical monitor, and Scale, "
                 "Primary and Rotation the values stored for that logical monitor; mutter writes primary only when "
                 "it is yes (lines 2400 to 2401), so an empty Primary is a monitor that is not the primary one. "
                 "Layout Mode is the configuration's layoutmode when stored. Values are text as stored and an "
                 "element that is absent gives an empty cell. The file holds no times. mutter saves a change applied "
                 "as persistent at once and, when it is not confirmed, restores the previous configuration after 20 "
                 "seconds ('src/backends/meta-monitor-manager.c' lines 67, 1983 and 2024 to 2058), saving again. "
                 "ubuntu2604_arm64_monitors is known data from a VM running mutter 50.1 with one virtual monitor: a "
                 "1280 by 800 mode and then the original 1024 by 768 mode were applied as persistent over D-Bus, "
                 "without confirmation. A copy of the file taken 3 seconds after each request holds the mode "
                 "requested, with a modified time 1 second after the request; 20 seconds after the second file's "
                 "modified time the file was written again, without a request, holding the 1280 by 800 mode. The "
                 "original mode was then applied twice and the file still held it 30 seconds later. So the file is "
                 "the configuration last saved, which can be one mutter restored by itself, and for seconds it can "
                 "hold a change that was not kept. Through the four writes the file held one configuration element, "
                 "for the same monitor, and monitors.xml~ kept its earlier modified time and content. The capture's "
                 "2 rows are the file and its backup, each the virtual monitor on connector Virtual-1 at 1024 by 768 "
                 "with Vendor, Product and Serial stored as the word unknown; Rotation and Layout Mode were empty on "
                 "both rows. The four rows of the source's example (two enabled monitors, one disabled, one for "
                 "lease) were read as written there. Not exercised on real data: a physical monitor, more than one "
                 "monitor or configuration, a rotated, disabled or leased monitor, and the system and GDM copies of "
                 "the file.",
        "paths": ("*/.config/monitors.xml", "*/.config/monitors.xml~", "*/etc/xdg/monitors.xml"),
        "output_types": "standard",
        "artifact_icon": "monitor",
        "sample_data": {
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_monitors": "Ubuntu 26.04 LTS aarch64, mutter 50.1 | 2 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import xml.etree.ElementTree as ET
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc


def _text(element, path):
    """The text of the first element at path under element, stripped, or '' when there is none."""
    found = None if element is None else element.find(path)
    return (found.text or '').strip() if found is not None else ''


def _spec(element):
    return tuple(_text(element, 'monitorspec/' + name) for name in ('connector', 'vendor', 'product', 'serial'))


def monitor_rows(data):
    """The rows for the bytes of a monitors.xml in format version 2, in file order: (configuration number, state,
    connector, vendor, product, serial, width, height, rate, x, y, scale, primary, rotation, layout mode). None
    when the data is not XML with a monitors root, and False when its version is not 2."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None
    if root.tag != 'monitors':
        return None
    if root.get('version') != '2':
        return False
    rows = []
    for number, configuration in enumerate(root.findall('configuration'), 1):
        layout = _text(configuration, 'layoutmode')
        for logical in configuration.findall('logicalmonitor'):
            placed = tuple(_text(logical, name) for name in ('x', 'y', 'scale', 'primary'))
            rotation = _text(logical, 'transform/rotation')
            for monitor in logical.findall('monitor'):
                mode = tuple(_text(monitor, 'mode/' + name) for name in ('width', 'height', 'rate'))
                rows.append((number, 'Enabled') + _spec(monitor) + mode + placed + (rotation, layout))
        for tag, state in (('disabled', 'Disabled'), ('forlease', 'For Lease')):
            for holder in configuration.findall(tag):
                for spec in holder.findall('monitorspec'):
                    names = tuple(_text(spec, name) for name in ('connector', 'vendor', 'product', 'serial'))
                    rows.append((number, state) + names + ('',) * 8 + (layout,))
    return rows


@artifact_processor
def linuxMonitorsXml(context):
    data_headers = ('Configuration', 'State', 'Connector', 'Vendor', 'Product', 'Serial', 'Width', 'Height',
                    'Refresh Rate', 'X', 'Y', 'Scale', 'Primary', 'Rotation', 'Layout Mode', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = monitor_rows(data)
        if rows is None:
            problems['files that are not a monitors.xml, not read'] += 1
            continue
        if rows is False:
            problems['files in a format version other than 2, not read'] += 1
            continue
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Display Configurations (monitors.xml): '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
