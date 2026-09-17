"""Windows Amcache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Amcache artifact; the implementation reads
the hive's on-disk structure directly and is not ported from that artifact.

The InventoryApplicationFile field meanings, including FileId being the file's
SHA-1 prefixed with four zeroes, are sourced from public Amcache research (see
the artifact notes).
"""

from datetime import timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Amcache.hve records metadata about executables the system has seen, under
# Root\InventoryApplicationFile: the full path, the file's SHA-1 (stored as
# FileId), publisher and version resource strings, size, and the PE compile
# date. It documents that a file was present, not that it was run.

_INVENTORY_PATH = "Root\\InventoryApplicationFile"

__artifacts_v2__ = {
    "amcacheApplicationFiles": {
        "name": "Amcache Application Files",
        "description": "Executables the system inventoried, from Amcache.hve "
                       "InventoryApplicationFile: the file path, its SHA-1, "
                       "publisher, product and version, size, PE link date, and "
                       "the time the entry was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one "
                 "InventoryApplicationFile entry. File Path is LowerCaseLongPath "
                 "as stored (lowercased by Windows). SHA-1 is the FileId value "
                 "with its leading four zeroes removed; FileId is the file's "
                 "SHA-1 (of the first 31 MiB on Windows 8 and later) and is shown "
                 "as stored when it does not have that shape. Name, Publisher, "
                 "Product Name and Version are the file's version-resource "
                 "strings as stored. Size is in bytes. Link Date is the PE "
                 "header compile time as stored and is the time the file was "
                 "built, not a time it ran or was installed; its timezone is not "
                 "recorded, so it is shown as stored and not converted. Program "
                 "ID links a file to an installed application; a blank or zero "
                 "Program ID means the file was not tied to one. Key Last Write "
                 "(UTC) is the entry's registry LastWrite time, which is when "
                 "Amcache wrote the entry and approximates when the file was "
                 "first inventoried; it is not an execution time. Presence of an "
                 "entry records that the file was seen on the system, not that it "
                 "was run and not who ran it. Reading the hive needs the "
                 "python-registry package; its .LOG1/.LOG2 transaction logs are "
                 "not replayed. Field meanings: Psmths, 'windows-forensic-"
                 "artifacts', https://github.com/Psmths/windows-forensic-artifacts/"
                 "blob/main/execution/amcache.md",
        "paths": ("*/Windows/appcompat/Programs/Amcache.hve",),
        "output_types": ["standard"],
        "artifact_icon": "hash",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 146 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 153 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 290 rows",
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
    reg = Registry.Registry(hive_path)
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
