"""Windows Amcache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Amcache artifact; the implementation reads
the hive's on-disk structure directly and is not ported from that artifact.

The InventoryApplicationFile field meanings, including FileId being a SHA-1 of
the file (of its first 30 MiB when it is larger) prefixed with four zeroes, are
sourced from public Amcache research and measured on the test images (see the
artifact notes).
"""

from datetime import timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Amcache.hve records metadata about executables the system has seen, under
# Root\InventoryApplicationFile: the full path, a SHA-1 of the file (stored as
# FileId), publisher and version strings, size, and the PE link date. It
# documents that a file was inventoried, not that it was run.

_INVENTORY_PATH = "Root\\InventoryApplicationFile"

__artifacts_v2__ = {
    "amcacheApplicationFiles": {
        "name": "Amcache Application Files",
        "description": "Executables the system inventoried, from Amcache.hve InventoryApplicationFile: the "
                       "file path, the SHA-1 Amcache records for it, publisher, product and version, size, "
                       "link date, and the time the entry was written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-26",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from Amcache.hve, named in the report's located-at line. Each row is one "
                 "InventoryApplicationFile entry, a key Psmths's Amcache reference lists from Windows "
                 "10 build 14393 and describes as updated only when the Microsoft Compatibility "
                 "Appraiser task runs (Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L68-L69). "
                 "File Path is LowerCaseLongPath as stored; every value on lonewolf_win10 and "
                 "pc_mus_001_win11 was lowercase. SHA-1 is the FileId value without its leading four "
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
                 "under InventoryApplication, a key this artifact does not read "
                 "(https://github.com/Psmths/windows-forensic-artifacts/blob/a1cfae67e3b347b7f3336dece5c3527a11b73e00/execution/amcache.md#L75). "
                 "Key Last Write (UTC) is the entry's registry LastWrite time; it is not an execution "
                 "time. An entry records that the file was inventoried; this artifact does not treat "
                 "it as proof that the file ran or of who ran it. Reading the hive needs the "
                 "python-registry package; its .LOG1/.LOG2 transaction logs are not replayed.",
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
