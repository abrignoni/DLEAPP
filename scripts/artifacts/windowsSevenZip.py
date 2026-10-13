"""7-Zip per-user configuration and history from NTUSER.DAT, for DLEAPP.

Author: @AlexisBrignoni, Claude.
Reads the HKCU\\Software\\7-Zip key that the 7-Zip File Manager and dialogs write; 7-Zip is Igor
Pavlov's open-source archiver (https://www.7-zip.org). The implementation reads the hive directly.
"""

__artifacts_v2__ = {
    "windowsSevenZip": {
        "name": "7-Zip",
        "description": "Per-user 7-Zip configuration and the folder and archive paths 7-Zip kept in its history, "
                       "read from the HKCU\\Software\\7-Zip key of each user's NTUSER.DAT: the install path, the "
                       "compression and extraction options, the File Manager panel folders, and the archive, "
                       "extraction, folder and copy history lists.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row per reported value under HKCU\\Software\\7-Zip in a user's NTUSER.DAT, with one row per "
                 "path in a history value, the key 7-Zip (Igor Pavlov's "
                 "open-source archiver, https://www.7-zip.org) writes. Key Last Written (UTC) is the last-written "
                 "time of the key the row came from, Category groups the rows, Name is the value name (with a "
                 "position number appended for a history entry), Value is the data as python-registry decodes it (a "
                 "number as its decimal, text as text, other binary as hex) and a decoded path for a history "
                 "entry, User is the folder after Users in the path and Source File is the hive. Config "
                 "rows: Path and Path64, the install folder (Install); Archiver, the archive format last chosen in "
                 "the compression dialog, Level, "
                 "the compression level, EncryptHeaders and ShowPassword (Compression); ShowPassword (Extraction); "
                 "and PanelPath0 and PanelPath1, the path saved for each File Manager panel, the folder shown or the "
                 "folder holding an archive the panel was inside (File Manager). "
                 "History rows come from four REG_BINARY values, each a list of UTF-16LE paths separated by UTF-16 "
                 "nulls, reported one path per row in the order stored with a position number from 1: ArcHistory, "
                 "the archive paths the compression dialog recorded (Archive history); PathHistory, the extraction "
                 "destinations (Extraction history); FolderHistory, the folders opened in the File Manager (Folder "
                 "history); and CopyHistory, the copy and move destinations (Copy history). Values are not "
                 "interpreted; a path in a history list is one 7-Zip recorded, not proof the user "
                 "acted on it at a known time, and the key's last-written time dates the most recent change to the "
                 "key, not each entry. FolderShortcuts and the File Manager layout values (column widths, window "
                 "position) are not reported. On af_case2_win10 and pc_mus_001_win11 only the install Path and "
                 "Path64 are present, one user each (2 rows); lonewolf_win10 and szechuan_win10 have no "
                 "HKCU\\Software\\7-Zip key (0 rows). On windows11_arm_known_20261001 and "
                 "windows11_arm_known_20261010 the 36 rows are 9 config values and 27 history paths (1 archive, 25 "
                 "folder, 1 copy; no extraction history), and on windows11_arm_7zip_known_20261010 the 39 rows are 9 "
                 "config values and 30 history paths (2 archive, 1 extraction, 26 folder, 1 copy). "
                 "User holds one value on every row of each tested image, each image having one user with a 7-Zip "
                 "key. Reading the hive requires python-registry; a dirty hive is read after "
                 "its transaction logs are applied, and the run log names each.",
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "archive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows (install path only)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no HKCU Software\\7-Zip key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows (install path only)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no HKCU Software\\7-Zip key)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 36 rows",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 36 rows",
            "windows11_arm_7zip_known_20261010": "Windows 11 build 26200 | 39 rows",
        },
    },
}

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, is_transaction_log, key_written_utc, open_hive, open_key, user_from_path

_LABEL = '7-Zip'
_ROOT = 'Software\\7-Zip'
# Config scalars: (category, subkey under Software\7-Zip or '' for the root, value name).
_CONFIG = (
    ('Install', '', 'Path'),
    ('Install', '', 'Path64'),
    ('Compression', 'Compression', 'Archiver'),
    ('Compression', 'Compression', 'Level'),
    ('Compression', 'Compression', 'EncryptHeaders'),
    ('Compression', 'Compression', 'ShowPassword'),
    ('Extraction', 'Extraction', 'ShowPassword'),
    ('File Manager', 'FM', 'PanelPath0'),
    ('File Manager', 'FM', 'PanelPath1'),
)
# History lists stored as REG_BINARY: UTF-16LE paths, each terminated by a UTF-16 null.
_HISTORY = (
    ('Archive history', 'Compression', 'ArcHistory'),
    ('Extraction history', 'Extraction', 'PathHistory'),
    ('Folder history', 'FM', 'FolderHistory'),
    ('Copy history', 'FM', 'CopyHistory'),
)


def _config_text(value):
    """A config value as stored: an int as its decimal, a string as itself, bytes as hex."""
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    return '' if value is None else str(value)


def history_paths(blob):
    """The paths in a 7-Zip history value: UTF-16LE strings separated by UTF-16 nulls, in stored order."""
    if not isinstance(blob, (bytes, bytearray)):
        return []
    return [part for part in bytes(blob).decode('utf-16-le', 'replace').split('\x00') if part]


def _value(key, name):
    """A value's data, or None when the key or value is absent."""
    if key is None:
        return None
    for value in key.values():
        if value.name() == name:
            try:
                return value.value()
            except Exception:  # pylint: disable=broad-exception-caught
                return None
    return None


def seven_zip_rows(reg, relative):
    """The rows for one NTUSER.DAT that holds Software\\7-Zip; [] when the key is absent."""
    root = open_key(reg, _ROOT)
    if root is None:
        return []
    user = user_from_path(relative)
    keys = {'': root}

    def sub(name):
        if name not in keys:
            keys[name] = open_key(reg, f'{_ROOT}\\{name}')
        return keys[name]

    rows = []
    for category, subkey, name in _CONFIG:
        key = root if subkey == '' else sub(subkey)
        data = _value(key, name)
        if data is not None:
            rows.append((key_written_utc(key), category, name, _config_text(data), user, relative))
    for category, subkey, name in _HISTORY:
        key = sub(subkey)
        paths = history_paths(_value(key, name))
        written = key_written_utc(key)
        for position, path in enumerate(paths, 1):
            rows.append((written, category, f'{name} #{position}', path, user, relative))
    return rows


@artifact_processor
def windowsSevenZip(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Category', 'Name', 'Value', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'NTUSER.DAT')):
        if is_transaction_log(source):
            continue
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative}: {exc}')
            continue
        rows = seven_zip_rows(reg, relative)
        if rows:
            data_list.extend(rows)
            sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
