"""The records of an ESE table as ESE itself shows them.

The vendored reader's getNextRow returns every leaf node of a table, including a node
carrying ESE's deleted flag fNDDeleted (TAG_DEFUNCT in the reader). ESE's own code treats
such a node as not there unless its version store still holds an update to it, and a
database read from an image has no version store in use:
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079

TableRows walks a table the way getNextRow does, page by page and tag by tag, skips the
flagged nodes and counts them, and skips and counts a record the reader cannot convert,
so one bad record does not end the table. The vendored reader itself is left unchanged
(scripts/vendor/README.md).

A tagged column value too long for its record is stored apart in the table's long value
tree, and the record keeps only its long value ID, flagged fLongValue (0x01) and fSeparated
(0x04) in the item's header byte:
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L88-L115
The vendored reader returns those ID bytes as if they were the value. TableRows reads the
value from the long value tree instead. The record holds the ID little-endian; the tree's
keys hold it big-endian, alone for the value's root (its reference count and size) and
followed by a big-endian byte offset for each piece, and a 64-bit ID has its top bit set
(rec.hxx#L112, #L135-L149 and #L235-L253, lv.hxx#L36-L62 and #L99-L135 at the commit
above). ESE keeps no compressed bit: a piece that stores fewer bytes than the table's
chunk size, or than the rest of the value for the last piece, is compressed
(lv.cxx#L1307-L1327). Every piece starts at a multiple of the chunk size (lv.cxx#L1317),
so TableRows reads the chunk size off the tree; when no value has a second piece, the rest
of the value stands in for it. A value TableRows cannot assemble (a piece missing or
compressed, or the value encrypted) is left blank and counted, never shown as the ID. A
multi-valued column keeps the reader's reading: ESE marks a separated value inside such a
column's list of values, not in its header (tagfld.hxx#L501), and TableRows does not read
that list.
"""

import math
import struct
from binascii import hexlify

from scripts.vendor import impacket_ese

_LONG_VALUE = 0x01    # TAGFLD_HEADER fLongValue
_SEPARATED = 0x04     # TAGFLD_HEADER fSeparated
_MULTI_VALUES = 0x08  # TAGFLD_HEADER fMultiValues
_LV_ENCRYPTED = 0x01  # LVROOT2 fFlags fLVEncrypted


def _flags_always_present(database):
    """Whether every tagged item starts with its header byte, as the vendored reader decides it."""
    header = database._ESENT_DB__DBHeader  # pylint: disable=protected-access
    return (header['Version'] == 0x620 and header['FileFormatRevision'] >= 17
            and header['PageSize'] > 8192)


def tagged_items(data, flags_always):
    """{column id: (header byte, value bytes)} of a record's tagged columns.

    Laid out as the vendored reader reads them: after the fixed columns come the variable
    columns' end offsets and data, then the tagged directory of (id, offset) pairs.
    """
    header = impacket_ese.ESENT_DATA_DEFINITION_HEADER(data)
    variables = max(0, header['LastVariableDataType'] - 127)
    offset = header['VariableSizeOffset']
    if offset + 2 * variables > len(data):
        return {}
    end = 0
    for i in range(variables):
        item, = struct.unpack_from('<H', data, offset + 2 * i)
        if not item & 0x8000:
            end = item
    start = offset + 2 * variables + end
    if start + 4 > len(data):
        return {}
    first = start + (struct.unpack_from('<H', data, start + 2)[0] & 0x3fff)
    entries = []
    index = start
    while index + 4 <= len(data):
        ident, raw = struct.unpack_from('<HH', data, index)
        index += 4
        entries.append((ident, raw & 0x3fff, flags_always or bool(raw & 0x4000)))
        if index >= first:
            break
    items = {}
    for i, (ident, item_offset, has_flags) in enumerate(entries):
        stop = start + entries[i + 1][1] if i + 1 < len(entries) else len(data)
        chunk = bytes(data[start + item_offset:stop])
        items[ident] = (chunk[0], chunk[1:]) if has_flags and chunk else (0, chunk)
    return items


def _leaves(database, page_number, seen):
    """(page, tag flags, tag data) of every leaf tag under a tree's root page.

    A page number past the end of the file is not followed: the vendored reader's getPage
    waits for bytes a truncated file never gives."""
    total_pages = database._ESENT_DB__totalPages  # pylint: disable=protected-access
    if page_number in seen or not 0 < page_number <= total_pages:
        return
    seen.add(page_number)
    page = database.getPage(page_number)
    leaf = page.record['PageFlags'] & impacket_ese.FLAGS_LEAF
    for number in page.iterDataTagNums():
        flags, data = page.getTag(number)
        if leaf:
            yield page, flags, data
        elif not flags & impacket_ese.TAG_DEFUNCT:
            child = impacket_ese.ESENT_BRANCH_ENTRY(flags, data)['ChildPageNumber']
            yield from _leaves(database, child, seen)


def long_value_tree(database, table_name):
    """{ID key: (root data or None, [(offset, piece data), ...])} of a table's long value tree,
    leaving out the nodes ESE marks deleted."""
    tables = database._ESENT_DB__tables  # pylint: disable=protected-access
    table = tables.get(table_name.encode()) or tables.get(table_name)
    index = {}
    if not table:
        return index
    seen = set()
    for entry in table['LongValues'].values():
        header = impacket_ese.ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])
        root = impacket_ese.ESENT_CATALOG_DATA_DEFINITION_ENTRY(
            entry['EntryData'][len(header):])['FatherDataPageNumber']
        for page, flags, data in _leaves(database, root, seen):
            if flags & impacket_ese.TAG_DEFUNCT:
                continue
            position, common = 0, b''
            if flags & impacket_ese.TAG_COMMON:
                size, = struct.unpack_from('<H', data, 0)
                common = page.getTag(0)[1][:size]
                position = 2
            size, = struct.unpack_from('<H', data, position)
            position += 2
            index_node(index, bytes(common + data[position:position + size]), bytes(data[position + size:]))
    return index


def index_node(index, key, value):
    """File one long value tree node: an ID alone is a value's root, an ID and an offset a
    piece. A 64-bit ID has the top bit of its first byte set (lv.hxx FIsLVRootKey)."""
    id_length = 8 if key and key[0] & 0x80 else 4
    if len(key) == id_length:
        index.setdefault(key, [None, []])[0] = value
    elif len(key) == id_length + 4:
        index.setdefault(key[:id_length], [None, []])[1].append(
            (int.from_bytes(key[id_length:], 'big'), value))


def chunk_size(index):
    """The table's long value chunk size as the tree shows it, or None.

    Every piece starts at a multiple of the chunk size, so the greatest common divisor of the
    pieces' offsets is the chunk size once a value has a piece one chunk in."""
    size = 0
    for _root, pieces in index.values():
        for offset, _data in pieces:
            size = math.gcd(size, offset)
    return size or None


def long_value(index, stored_id, chunk=None):
    """(bytes, None) for the value a separated item names, or (None, reason).

    `chunk` is the table's chunk size (chunk_size); None makes the rest of the value stand in
    for it."""
    if len(stored_id) not in (4, 8):
        return None, 'an ID of unexpected length'
    root, pieces = index.get(bytes(stored_id[::-1]), (None, []))
    if root is None:
        return None, 'no root in the long value tree'
    if len(root) < 8:
        return None, 'a root shorter than ESE writes one'
    if len(root) > 8 and root[8] & _LV_ENCRYPTED:
        return None, 'the value is encrypted'
    total, = struct.unpack_from('<I', root, 4)
    pieces = sorted(pieces)
    value = bytearray()
    for offset, data in pieces:
        if offset < len(value):
            return None, 'two pieces at one offset'
        expected = chunk if chunk and offset + chunk < total else total - offset
        if len(data) < expected:
            return None, 'a compressed piece'
        if len(data) > expected:
            return None, 'a piece longer than ESE writes one'
        value.extend(data)
    if len(value) != total:
        return None, 'a piece missing from the long value tree'
    return bytes(value), None


def _as_reader_value(column, value):
    """The value in the form the vendored reader gives a column of this type."""
    if column['ColumnType'] in (impacket_ese.JET_coltypText, impacket_ese.JET_coltypLongText):
        return value.decode(impacket_ese.StringCodePages[column['CodePage']], 'replace')
    return hexlify(value)


class TableRows:
    """Iterate the records of one table; `deleted` and `unreadable` count what was skipped.

    `cap` bounds the number of tags visited, so a corrupt page's forward pointer cannot
    loop forever. `errors` keeps the first few conversion errors for the run log.
    `long_value_columns` names the columns whose separated values are read from the long
    value tree (a set of names or a test of a name); None reads every column's.
    """

    def __init__(self, database, table_name, cap=5_000_000, long_value_columns=None):
        self.database = database
        self.table_name = table_name
        self.cap = cap
        self.long_value_columns = long_value_columns
        self.deleted = 0
        self.unreadable = 0
        self.errors = []
        self.capped = False
        self.found = None
        self.long_values = 0
        self.long_values_blank = 0
        self.long_value_errors = []
        self._tree = None
        self._chunk = None

    def __iter__(self):
        database = self.database
        cursor = database.openTable(self.table_name)
        self.found = cursor is not None
        if cursor is None:
            return
        to_record = database._ESENT_DB__tagToRecord  # pylint: disable=protected-access
        tagged = {column['Record']['Identifier']: (name, column['Record'])
                  for name, column in cursor['TableData']['Columns'].items()
                  if column['Record']['Identifier'] > 255 and self._wanted(name)}
        flags_always = _flags_always_present(database) if tagged else False
        visited = 0
        while True:
            page = cursor['CurrentPageData']
            cursor['CurrentTag'] += 1
            if cursor['CurrentTag'] >= page.tagCount or not page.record['PageFlags'] & impacket_ese.FLAGS_LEAF:
                if page.record['NextPageNumber'] == 0:
                    return
                cursor['CurrentPageData'] = database.getPage(page.record['NextPageNumber'])
                cursor['CurrentTag'] = cursor['CurrentPageData'].firstDataTag - 1
                continue
            visited += 1
            if visited > self.cap:
                self.capped = True
                return
            flags, data = page.getTag(cursor['CurrentTag'])
            for special in (impacket_ese.FLAGS_SPACE_TREE, impacket_ese.FLAGS_INDEX,
                            impacket_ese.FLAGS_LONG_VALUE):
                if page.record['PageFlags'] & special:
                    raise ValueError(f'{self.table_name}: a table walk reached a page with flags '
                                     f'{page.record["PageFlags"]:#x}')
            if flags & impacket_ese.TAG_DEFUNCT:
                self.deleted += 1
                continue
            try:
                entry = impacket_ese.ESENT_LEAF_ENTRY(flags, data)
                record = to_record(cursor, entry['EntryData'])
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.unreadable += 1
                if len(self.errors) < 3:
                    self.errors.append(f'{type(exc).__name__}: {exc}')
                continue
            if tagged:
                self._read_separated(entry['EntryData'], record, tagged, flags_always)
            yield record

    def _wanted(self, name):
        wanted = self.long_value_columns
        if wanted is None:
            return True
        name = name.decode('latin-1') if isinstance(name, (bytes, bytearray)) else name
        return wanted(name) if callable(wanted) else name in wanted

    def _read_separated(self, data, record, tagged, flags_always):
        """Replace each separated value's ID with the value from the long value tree."""
        for ident, (header, stored) in tagged_items(data, flags_always).items():
            if (ident not in tagged or header & _MULTI_VALUES
                    or header & (_LONG_VALUE | _SEPARATED) != _LONG_VALUE | _SEPARATED):
                continue
            name, column = tagged[ident]
            if self._tree is None:
                self._tree = long_value_tree(self.database, self.table_name)
                self._chunk = chunk_size(self._tree)
            value, reason = long_value(self._tree, stored, self._chunk)
            if value is None:
                record[name] = None
                self.long_values_blank += 1
                if reason not in self.long_value_errors:
                    self.long_value_errors.append(reason)
            else:
                record[name] = _as_reader_value(column, value)
                self.long_values += 1

    def summary(self):
        """A run-log sentence for what was skipped, or '' when nothing was."""
        parts = []
        if self.deleted:
            parts.append(f'{self.deleted} record(s) ESE marks deleted (fNDDeleted) were not read')
        if self.unreadable:
            parts.append(f'{self.unreadable} record(s) the ESE reader could not convert were skipped'
                         + (f' ({"; ".join(self.errors)})' if self.errors else ''))
        if self.long_values:
            parts.append(f'{self.long_values} value(s) stored apart from their record were read from '
                         'the long value tree')
        if self.long_values_blank:
            parts.append(f'{self.long_values_blank} value(s) stored apart from their record could not be '
                         f'assembled and are blank ({"; ".join(self.long_value_errors)})')
        if self.capped:
            parts.append(f'the walk stopped after {self.cap:,} records')
        return f'{self.table_name}: ' + '; '.join(parts) if parts else ''
