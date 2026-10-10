"""Earlier Windows installations recorded in the SYSTEM hive's Setup key (Source OS), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsUpgradeHistory": {
        "name": "Upgrade History (Source OS)",
        "description": "Earlier Windows installations a system was upgraded from, one row per Source OS key of the "
                       "SYSTEM hive: the product, build and install time of the earlier installation and the "
                       "time in the key's name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each subkey of the SYSTEM hive's Setup key whose name has the form Source OS "
                 "(Updated on <date and time>). No Microsoft description of these keys was found, so nothing "
                 "here rests on one: the artifact reports what the key stores, and what follows was measured on "
                 "pc_mus_001_win11, the only tested extraction that has such a key. The key holds values with "
                 "the names Windows uses for the installed system under Microsoft\\Windows NT\\CurrentVersion of "
                 "the SOFTWARE hive, and on that image they describe another installation than the current one: "
                 "Product Name Windows 10 Home, Display Version 22H2, Release ID 2009, Build 19045 and UBR 2006, "
                 "where the SOFTWARE hive of the same image holds build 22621. Install Date (UTC) is the key's "
                 "InstallDate value read as seconds since 1970 and Install Time (UTC) its InstallTime value read "
                 "as a FILETIME, as the Windows System Information artifact reads the values of the same names; "
                 "on the image the two are the same second, 2022-11-11 16:10:44 UTC. Updated On (Key Name) is "
                 "the date and time in the key's name, as written there and not converted: it holds no time "
                 "zone. On the image it is 11/22/2022 19:09:57, and read with the hive's time zone bias of 300 "
                 "minutes it is 33 minutes 32 seconds before the InstallDate of the current installation in the "
                 "SOFTWARE hive and 19 minutes 10 seconds before the key's last-written time, which is "
                 "consistent with a local time written when the upgrade to the current installation ran; the "
                 "order of day and month in the name on systems with other regional settings was not tested. Key "
                 "Last Written (UTC) is the last-written time of the key. The same image's Setup\\Upgrade key "
                 "holds a DownlevelBuildNumber of 10.0.19045, the Build of the row; that key is not read. "
                 "Edition ID, Registered Owner, Registered Organization, Product ID and System Root are the "
                 "values of those names as stored, and a value that is absent or binary gives an empty cell. "
                 "Registered Organization was empty on the one row. A system that was never upgraded in place "
                 "has no such key: af_case2_win10, lonewolf_win10, szechuan_win10 and the two Windows 11 build "
                 "26200 captures have none and give no row, so absence of a row is not evidence about how "
                 "Windows was installed beyond that. More than one key in a hive, a key without the install "
                 "values and a hive that cannot be read were tested with constructed input only. Source File is "
                 "the hive. Reading the hive requires the python-registry package; a dirty hive is read after "
                 "its transaction logs are applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "arrow-up-circle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Source OS key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Source OS key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no Source OS key)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no Source OS key)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no Source OS key)",
        },
    },
}

import re

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc, found_hives, key_written_utc, open_hive, open_key, unix_utc

_NAME = re.compile(r'Source OS \(Updated on (.*)\)\Z', re.IGNORECASE)
# the values shown as text columns, in column order
_TEXT = ('ProductName', 'DisplayVersion', 'ReleaseId', 'CurrentBuild', 'UBR', 'EditionID', 'RegisteredOwner',
         'RegisteredOrganization', 'ProductId', 'SystemRoot')


def _text(data):
    """A value's data for a text column: a string or a number as stored, '' for a missing value or binary data."""
    return '' if data is None or isinstance(data, (bytes, list)) else data


def source_os_rows(reg):
    """The rows for one SYSTEM hive, one per Setup subkey named Source OS (Updated on ...): (install date, install
    time, updated on, key last written, the _TEXT values, key path)."""
    rows = []
    setup = open_key(reg, 'Setup')
    for key in (setup.subkeys() if setup is not None else []):
        match = _NAME.match(key.name())
        if not match:
            continue
        stored = {value.name().lower(): value.value() for value in key.values()}
        text = tuple(_text(stored.get(name.lower())) for name in _TEXT)
        rows.append((unix_utc(stored.get('installdate')), filetime_utc(stored.get('installtime')), match.group(1),
                     key_written_utc(key)) + text + ('Setup\\' + key.name(),))
    return rows


@artifact_processor
def windowsUpgradeHistory(context):
    data_headers = (('Install Date (UTC)', 'datetime'), ('Install Time (UTC)', 'datetime'), 'Updated On (Key Name)',
                    ('Key Last Written (UTC)', 'datetime'), 'Product Name', 'Display Version', 'Release ID',
                    'Build', 'UBR', 'Edition ID', 'Registered Owner', 'Registered Organization', 'Product ID',
                    'System Root', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Upgrade History (Source OS): the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SYSTEM')):
        relative = context.get_relative_path(source)
        try:
            rows = source_os_rows(open_hive(source, context))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Upgrade History (Source OS): could not read {relative}: {exc}')
            continue
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
