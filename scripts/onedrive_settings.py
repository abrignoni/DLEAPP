"""Read the OneDrive sync client's item lists from its settings folder on Windows.

Two stores, one per client generation:

- <account id>.dat, a header then fixed-size records, read for the two record layouts on the
  corpus (versions 0x2b and 0x36). The layouts follow Brian Maloney's OneDriveExplorer (MIT),
  https://github.com/Beercow/OneDriveExplorer/blob/dfec646a87911db8083749f2d625cfeb92fc84a1/OneDriveExplorer/ode/helpers/structures
  (DAT_FILE_v2b, DAT_FILE_v36, DAT_FOLDER_v29_v2c, DAT_FOLDER_v2d_v36) and the block sizes in
  https://github.com/Beercow/OneDriveExplorer/blob/dfec646a87911db8083749f2d625cfeb92fc84a1/OneDriveExplorer/ode/parsers/dat.py
- SyncEngineDatabase.db, SQLite, the od_ClientFile_Records and od_ClientFolder_Records tables.

Integers and the digest are returned as stored; strings are decoded from UTF-8 or UTF-16-LE and cut
at the first NUL. The artifact's notes say what each value was checked against.
"""

import struct

DAT_HEADER_SIZE = 536

# version: (record size, item header size, file layout, folder name offset)
# File layout: offsets of the local hash (20 bytes), lastChange (uint32 or None), size (uint64),
# file name (260 UTF-16 code units) and fileStatus (uint16).
_DAT_LAYOUTS = {
    0x2b: {'record': 1080, 'ids': 16, 'volume': 152,
           'file': {'hash': 176, 'last_change': None, 'size': 200, 'name': 208, 'status': 729},
           'folder': {'name': 176, 'status': 740}},
    0x36: {'record': 1232, 'ids': 24, 'volume': 160,
           'file': {'hash': 184, 'last_change': 208, 'size': 216, 'name': 224, 'status': 745},
           'folder': {'name': 184, 'status': 748}},
}
DAT_VERSIONS = tuple(sorted(_DAT_LAYOUTS))

FILE, FOLDER = 1, 2


class Item:
    """One file or folder record."""
    __slots__ = ('kind', 'resource_id', 'parent_id', 'name', 'size', 'local_hash', 'hash_algorithm',
                 'status', 'volume_id', 'item_index', 'last_change', 'disk_created', 'disk_accessed')

    def __init__(self, kind, resource_id, parent_id, name, **values):
        self.kind = kind
        self.resource_id = resource_id
        self.parent_id = parent_id
        self.name = name
        for slot in self.__slots__[4:]:
            setattr(self, slot, values.get(slot))


def _text(raw):
    return raw.split(b'\x00', 1)[0].decode('utf-8', 'replace')


def _wide(raw):
    return raw.decode('utf-16-le', 'replace').split('\x00', 1)[0]


def dat_version(data):
    """The version in a .dat header, or None when the data is shorter than the header."""
    if len(data) < DAT_HEADER_SIZE:
        return None
    return struct.unpack_from('<I', data, 0)[0]


def read_dat(data):
    """(items, record type counts, trailing bytes) of a .dat file of a known version.

    Raises ValueError for a version whose layout is not known.
    """
    version = dat_version(data)
    layout = _DAT_LAYOUTS.get(version)
    if layout is None:
        raise ValueError(f'version {version!r} has no known layout')
    size = layout['record']
    items, counts = [], {}
    offset = DAT_HEADER_SIZE
    while offset + size <= len(data):
        record = data[offset:offset + size]
        offset += size
        kind = record[0]
        counts[kind] = counts.get(kind, 0) + 1
        if kind not in (FILE, FOLDER):
            continue
        ids = layout['ids']
        resource_id = _text(record[ids:ids + 39])
        parent_id = _text(record[ids + 39:ids + 78])
        volume_id, item_index = struct.unpack_from('<QQ', record, layout['volume'])
        if kind == FILE:
            spots = layout['file']
            last_change = (struct.unpack_from('<I', record, spots['last_change'])[0]
                           if spots['last_change'] is not None else None)
            items.append(Item(FILE, resource_id, parent_id,
                              _wide(record[spots['name']:spots['name'] + 520]),
                              size=struct.unpack_from('<Q', record, spots['size'])[0],
                              local_hash=record[spots['hash']:spots['hash'] + 20],
                              status=struct.unpack_from('<H', record, spots['status'])[0],
                              volume_id=volume_id, item_index=item_index, last_change=last_change))
        else:
            spots = layout['folder']
            items.append(Item(FOLDER, resource_id, parent_id,
                              _wide(record[spots['name']:spots['name'] + 520]),
                              status=record[spots['status']], volume_id=volume_id, item_index=item_index))
    return items, counts, len(data) - offset


_FILE_COLUMNS = ('resourceID', 'parentResourceID', 'fileName', 'fileStatus', 'size', 'localHashDigest',
                 'localHashAlgorithm', 'volumeID', 'itemIndex', 'lastChange', 'diskCreationTime',
                 'diskLastAccessTime')
_FOLDER_COLUMNS = ('resourceID', 'parentResourceID', 'folderName', 'folderStatus', 'volumeID', 'itemIndex')


def _columns(db, table, wanted):
    present = {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}
    return [name for name in wanted if name in present]


def read_sync_engine(db):
    """The items of an open SyncEngineDatabase connection; a column a schema lacks reads as None."""
    items = []
    for table, wanted, kind in (('od_ClientFile_Records', _FILE_COLUMNS, FILE),
                                ('od_ClientFolder_Records', _FOLDER_COLUMNS, FOLDER)):
        present = _columns(db, table, wanted)
        if not present:
            continue
        query = 'SELECT ' + ', '.join(f'"{name}"' for name in present) + f' FROM "{table}"'
        for row in db.execute(query):
            value = dict(zip(present, row))
            common = {'volume_id': value.get('volumeID'), 'item_index': value.get('itemIndex')}
            if kind == FILE:
                items.append(Item(FILE, value.get('resourceID'), value.get('parentResourceID'),
                                  value.get('fileName'), size=value.get('size'),
                                  local_hash=value.get('localHashDigest'),
                                  hash_algorithm=value.get('localHashAlgorithm'),
                                  status=value.get('fileStatus'), last_change=value.get('lastChange'),
                                  disk_created=value.get('diskCreationTime'),
                                  disk_accessed=value.get('diskLastAccessTime'), **common))
            else:
                items.append(Item(FOLDER, value.get('resourceID'), value.get('parentResourceID'),
                                  value.get('folderName'), status=value.get('folderStatus'), **common))
    return items


def paths(items):
    """{id(item): path} built from the folder names of the same store, parent first.

    A chain stops at a parent the store holds no folder for (the drive root, which has no record)
    and at a parent already met on the chain.
    """
    folders = {item.resource_id: item for item in items if item.kind == FOLDER and item.resource_id}
    result = {}
    for item in items:
        names = [item.name or '']
        seen = {item.resource_id}
        parent = item.parent_id
        while parent in folders and parent not in seen:
            seen.add(parent)
            names.append(folders[parent].name or '')
            parent = folders[parent].parent_id
        result[id(item)] = '\\'.join(reversed(names))
    return result
