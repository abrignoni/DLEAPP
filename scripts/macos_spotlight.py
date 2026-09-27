"""Reader for the Apple Spotlight metadata store (store.db and .store.db), for DLEAPP.

Author: @AlexisBrignoni, Claude.

Written from the store database layout that libyal's dtformats documents ("Apple Spotlight store
file formats"), with three rules measured on real stores where that document is silent or reads
differently:

* the dbStr-N.map.data files start each value with its size as a little-endian base-128 integer;
* a list of variable-size integers (value type 0x07 with the list bit of the property type set) is
  prefixed by the list's size as 64-bit integers, eight bytes per value;
* a localized string is the first of its language versions that is not empty.

`Store(path).items()` yields every record of every record page; `Item.attributes` maps each
attribute name to its decoded value.
"""

import os
import struct
import zlib

_PAGE = 0x1000
_RECORD_PAGE = 0x09
_LZ4 = 0x1000
_LOCALIZED = '\x16\x02'


class StoreError(ValueError):
    """The data is not a store database, or a part of one, that this reader can read."""


def varint(data, offset):
    """(value, next offset) of a Spotlight variable-size integer: the number of leading 1 bits of
    the first byte is the number of bytes that follow, and the value is the first byte's remaining
    bits followed by those bytes, most significant first."""
    if offset >= len(data):
        raise StoreError('variable-size integer runs past the end of the data')
    first = data[offset]
    extra = 0
    while extra < 8 and first & (0x80 >> extra):
        extra += 1
    value = first & ((1 << (7 - extra)) - 1) if extra <= 4 else 0
    end = offset + 1 + extra
    if end > len(data):
        raise StoreError('variable-size integer runs past the end of the data')
    for byte in data[offset + 1:end]:
        value = (value << 8) | byte
    return value, end


def leb128(data, offset):
    """(value, next offset) of a little-endian base-128 integer."""
    value = shift = 0
    while True:
        if offset >= len(data) or shift > 63:
            raise StoreError('base-128 integer runs past the end of the data')
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return value, offset


def lz4_block(source, size, prefix=b''):
    """The size bytes one LZ4 block decompresses to; a match may reach back into prefix, the
    output of the block before it."""
    out = bytearray(prefix)
    start = len(out)
    i = 0
    try:
        while i < len(source):
            token = source[i]
            i += 1
            literal = token >> 4
            if literal == 15:
                while True:
                    byte = source[i]
                    i += 1
                    literal += byte
                    if byte != 255:
                        break
            out += source[i:i + literal]
            i += literal
            if i >= len(source):
                break
            distance = source[i] | (source[i + 1] << 8)
            i += 2
            length = token & 15
            if length == 15:
                while True:
                    byte = source[i]
                    i += 1
                    length += byte
                    if byte != 255:
                        break
            length += 4
            if distance == 0 or distance > len(out):
                raise StoreError('LZ4 match reaches before the start of the data')
            for _ in range(length):
                out.append(out[-distance])
    except IndexError as error:
        raise StoreError('LZ4 block ends inside a sequence') from error
    if len(out) - start != size:
        raise StoreError('LZ4 block did not give its recorded size')
    return bytes(out[start:])


def lz4_stream(data):
    """The output of a chain of bv41 (compressed) and bv4- (stored) blocks, up to bv4$."""
    blocks, offset, previous = [], 0, b''
    while offset + 4 <= len(data):
        marker = data[offset:offset + 4]
        if marker == b'bv4$':
            return b''.join(blocks)
        if marker == b'bv41':
            size, packed = struct.unpack_from('<II', data, offset + 4)
            block = lz4_block(data[offset + 12:offset + 12 + packed], size, previous)
            offset += 12 + packed
        elif marker == b'bv4-':
            (size,) = struct.unpack_from('<I', data, offset + 4)
            block = data[offset + 8:offset + 8 + size]
            offset += 8 + size
        else:
            raise StoreError('unknown LZ4 block marker')
        blocks.append(block)
        previous = block
    raise StoreError('LZ4 data has no end marker')


def localized(versions):
    """The first language version of a localized string that is not empty."""
    for version in versions:
        text = version.split(_LOCALIZED, 1)[0]
        if text:
            return text
    return ''


class Item:
    """One record: the identifier (a file system identifier in a volume's store), the flags byte,
    the item identifier, the parent's identifier, the record's last update time in microseconds
    since 1970, and the attributes by name. complete is False when a value could not be decoded
    and the attributes after it were not read."""

    __slots__ = ('identifier', 'flags', 'item_identifier', 'parent', 'updated', 'attributes', 'complete')

    def __init__(self, identifier, flags, item_identifier, parent, updated):
        self.identifier = identifier
        self.flags = flags
        self.item_identifier = item_identifier
        self.parent = parent
        self.updated = updated
        self.attributes = {}
        self.complete = True


class Store:
    """A store database file, read whole. The dbStr-N.map files beside it hold the attribute
    tables when the file header names no block for them."""

    def __init__(self, path):
        self.path = path
        self.folder = os.path.dirname(path)
        with open(path, 'rb') as handle:
            self.data = handle.read()
        if len(self.data) < _PAGE or self.data[:4] != b'8tsd':
            raise StoreError('not a Spotlight store database')
        (self.flags,) = struct.unpack_from('<I', self.data, 4)
        (self.map_offset, self.map_size, _page_size, types_block, values_block, _unknown_block,
         lists_block, localized_block) = struct.unpack_from('<8I', self.data, 36)
        self.recorded_path = self.data[324:580].split(b'\x00', 1)[0].decode('utf-8', 'replace')
        self.types = self._types(types_block)
        self.values = self._values(values_block)
        self.lists = self._index_lists(lists_block, 4)
        self.localized = self._index_lists(localized_block, 5)
        self.record_blocks = self._map()
        self.incomplete = 0
        self.unreadable_pages = 0

    # ---- pages ----------------------------------------------------------------------------------
    def _page(self, block):
        offset = block * _PAGE
        if offset + 20 > len(self.data) or self.data[offset:offset + 4] != b'2pbd':
            raise StoreError(f'no property page at block {block}')
        size, used, kind, uncompressed = struct.unpack_from('<4I', self.data, offset + 4)
        return offset, size, used, kind, uncompressed

    def _chain(self, block):
        """(used size, data after the 20-byte page header) of each page of a property table."""
        seen = set()
        while block and block not in seen:
            seen.add(block)
            offset, size, used, _kind, _uncompressed = self._page(block)
            data = self.data[offset + 20:offset + size]
            yield used, data
            (block,) = struct.unpack_from('<I', data, 0)

    def _map(self):
        """Block numbers of the record pages, from the map pages."""
        blocks, offset, end = [], self.map_offset, self.map_offset + self.map_size
        while offset < end:
            size, count = struct.unpack_from('<II', self.data, offset + 4)
            if size == 0:
                break
            for index in range(count):
                blocks.append(struct.unpack_from('<I', self.data, offset + 20 + 16 * index + 8)[0])
            offset += size
        return blocks

    # ---- attribute tables -------------------------------------------------------------------------
    def _streams(self, number):
        """The values of dbStr-number.map.data by table index, each still carrying its size prefix."""
        base = os.path.join(self.folder, f'dbStr-{number}.map.')
        try:
            with open(base + 'header', 'rb') as handle:
                header = handle.read()
            with open(base + 'offsets', 'rb') as handle:
                offsets = handle.read()
            with open(base + 'data', 'rb') as handle:
                data = handle.read()
            size, _buckets, count = struct.unpack_from('<III', header, 20)
            points = struct.unpack_from(f'<{count}I', offsets, 0)
        except (OSError, struct.error):
            return {}
        values = {}
        for index in range(1, count):
            stop = points[index + 1] if index + 1 < count else size
            values[index] = data[points[index]:stop]
        return values

    @staticmethod
    def _sized(value):
        """The part of a dbStr value its base-128 size prefix covers, or None when the prefix does
        not cover the rest of the value exactly."""
        try:
            size, start = leb128(value, 0)
        except StoreError:
            return None
        return value[start:] if start + size == len(value) else None

    def _types(self, block):
        table = {}
        if block:
            for used, data in self._chain(block):
                offset = 12
                while offset < used - 20:
                    index, value_type, property_type = struct.unpack_from('<IBB', data, offset)
                    end = data.index(b'\x00', offset + 6)
                    table[index] = (value_type, property_type, data[offset + 6:end].decode('utf-8', 'replace'))
                    offset = end + 1
            return table
        for index, value in self._streams(1).items():
            body = self._sized(value)
            if body is None or len(body) < 3:
                continue
            table[index] = (body[0], body[1], body[2:].split(b'\x00', 1)[0].decode('utf-8', 'replace'))
        return table

    def _values(self, block):
        table = {}
        if block:
            for used, data in self._chain(block):
                offset = 12
                while offset < used - 20:
                    (index,) = struct.unpack_from('<I', data, offset)
                    end = data.index(b'\x00', offset + 4)
                    table[index] = data[offset + 4:end].decode('utf-8', 'replace')
                    offset = end + 1
            return table
        for index, value in self._streams(2).items():
            body = self._sized(value)
            if body is not None:
                table[index] = body.split(b'\x00', 1)[0].decode('utf-8', 'replace')
        return table

    def _index_lists(self, block, number):
        """Lists of values-table indexes (property pages of type 0x81, or dbStr-number), each as
        the list of value names it points to. An index list's size is a Spotlight integer, and its
        indexes start after the bytes that make that size a multiple of four."""
        table = {}
        if block:
            for used, data in self._chain(block):
                offset = 12
                while offset < used - 20:
                    (index,) = struct.unpack_from('<I', data, offset)
                    size, start = varint(data, offset + 4)
                    padding = size % 4
                    indexes = struct.unpack_from(f'<{(size - padding) // 4}I', data, start + padding)
                    table[index] = [self.values.get(i, '') for i in indexes]
                    offset = start + size
            return table
        for index, value in self._streams(number).items():
            body = self._sized(value)
            if body is None:
                continue
            try:
                size, start = varint(body, 0)
                padding = size % 4
                indexes = struct.unpack_from(f'<{(size - padding) // 4}I', body, start + padding)
            except (StoreError, struct.error):
                continue
            table[index] = [self.values.get(i, '') for i in indexes]
        return table

    # ---- records -----------------------------------------------------------------------------------
    def record_page(self, block):
        """The records data of one record page, decompressed."""
        offset, size, used, kind, uncompressed = self._page(block)
        if kind & 0xFF != _RECORD_PAGE:
            raise StoreError(f'block {block} is not a record page')
        data = self.data[offset + 20:offset + size]
        if not uncompressed:
            return data[:used - 20]
        if kind & _LZ4 and data[:4] in (b'bv41', b'bv4-'):
            return lz4_stream(data)
        if data[:1] == b'\x78':
            try:
                return zlib.decompressobj().decompress(data)
            except zlib.error as error:
                raise StoreError(f'block {block} does not decompress') from error
        raise StoreError(f'block {block} is compressed in a way this reader does not read')

    def items(self):
        """Every record of every record page, in page order. A page that cannot be read is
        skipped and counted in unreadable_pages."""
        for block in self.record_blocks:
            try:
                data = self.record_page(block)
            except (StoreError, struct.error):
                self.unreadable_pages += 1
                continue
            offset = 0
            while offset + 4 <= len(data):
                (size,) = struct.unpack_from('<I', data, offset)
                if size == 0 or offset + 4 + size > len(data):
                    break
                try:
                    yield self._record(data[offset + 4:offset + 4 + size])
                except StoreError:
                    self.incomplete += 1
                offset += 4 + size

    def _record(self, record):
        identifier, at = varint(record, 0)
        if at >= len(record):
            raise StoreError('record ends inside its header')
        flags = record[at]
        item_identifier, at = varint(record, at + 1)
        parent, at = varint(record, at)
        updated, at = varint(record, at)
        item = Item(identifier, flags, item_identifier, parent, updated)
        type_index = 0
        try:
            while at < len(record):
                step, at = varint(record, at)
                type_index += step
                kind = self.types.get(type_index)
                if kind is None:
                    raise StoreError(f'attribute type {type_index} is not in the types table')
                value_type, property_type, name = kind
                value, at = self._value(value_type, property_type, name, record, at)
                item.attributes[name] = value
        except (StoreError, IndexError, struct.error):
            item.complete = False
            self.incomplete += 1
        return item

    def _value(self, value_type, property_type, name, data, at):
        many = property_type & 0x02
        if name == 'kMDStoreAccumulatedSizes':
            return data[at:], len(data)
        if value_type in (0x00, 0x02, 0x06):
            return varint(data, at)
        if value_type == 0x07:
            if not many:
                return varint(data, at)
            size, at = varint(data, at)
            values = []
            for _ in range(size // 8):
                value, at = varint(data, at)
                values.append(value)
            return values, at
        if value_type == 0x08:
            if not many:
                return data[at], at + 1
            size, at = varint(data, at)
            return list(data[at:at + size]), at + size
        if value_type in (0x09, 0x0A, 0x0C):
            width, code = (4, 'f') if value_type == 0x09 else (8, 'd')
            if not many:
                return struct.unpack_from('<' + code, data, at)[0], at + width
            size, at = varint(data, at)
            return list(struct.unpack_from(f'<{size // width}{code}', data, at)), at + size
        if value_type == 0x0B:
            size, at = varint(data, at)
            if at + size > len(data):
                raise StoreError('string runs past the end of the record')
            strings = [text.decode('utf-8', 'replace') for text in data[at:at + size].split(b'\x00')[:-1]]
            if property_type & 0x03 == 0x03:
                return localized(strings), at + size
            if property_type & 0x03 == 0x02:
                return strings, at + size
            return (strings[0] if strings else ''), at + size
        if value_type == 0x0E:
            size, at = varint(data, at)
            return data[at:at + size], at + size
        if value_type == 0x0F:
            index, at = varint(data, at)
            if property_type & 0x03 == 0x03:
                return localized(self.localized.get(index, [])), at
            if property_type & 0x03 == 0x02:
                return self.lists.get(index, []), at
            return self.values.get(index, ''), at
        raise StoreError(f'value type 0x{value_type:02x} is not decoded')
