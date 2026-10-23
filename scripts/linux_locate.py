"""Readers for the three locate database formats: plocate, mlocate and GNU findutils LOCATE02.

Author: @AlexisBrignoni, Claude.

Written from the formats' own documentation and the programs that write and read them; no
code is taken from any of them. The sources, pinned to a commit, are cited in the notes of
scripts/artifacts/linuxLocateDatabases.py, which uses this module.

Each reader takes the database's bytes and returns a LocateDatabase: the header fields, the
configuration block, the paths in stored order, and the problems met while reading. A reader
that meets damage keeps what it read before it and says where it stopped, rather than
returning nothing.
"""

import struct
from datetime import datetime, timedelta, timezone

PLOCATE_MAGIC = b'\0plocate'
MLOCATE_MAGIC = b'\0mlocate'
LOCATE02_MAGIC = b'\0LOCATE02\0'

FORMAT_PLOCATE = 'plocate'
FORMAT_MLOCATE = 'mlocate'
FORMAT_LOCATE02 = 'GNU locate (LOCATE02)'

TYPE_DIRECTORY = 'directory'
TYPE_OTHER = 'not a directory'
TYPE_ROOT = 'directory (database root)'
TYPE_UNRECORDED = 'not recorded'

ZSTD_MISSING = ('the file names are compressed with zstd, which needs Python 3.14 or the backports.zstd or '
                'zstandard package, so no path was read')

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_NSEC = 1_000_000_000

# struct Header in plocate's db.h, in the byte order of the machine that wrote it. Offsets are the
# same on 32-bit and 64-bit builds: every 64-bit field already falls on a multiple of 8.
_PLOCATE_HEADER = 'IIIIQQIIQQQQQQQ?'
_PLOCATE_HEADER_V0 = 'IIIIQQ'


def _zstd_backend():
    """('stdlib' or 'backports', module) or ('zstandard', module), or (None, None) when none is installed."""
    try:
        from compression import zstd  # pylint: disable=import-error,import-outside-toplevel
        return 'stdlib', zstd
    except ImportError:
        pass
    try:
        from backports import zstd as backport  # pylint: disable=import-error,import-outside-toplevel
        return 'backports', backport
    except ImportError:
        pass
    try:
        import zstandard  # pylint: disable=import-error,import-outside-toplevel
        return 'zstandard', zstandard
    except ImportError:
        return None, None


_ZSTD_KIND, _ZSTD = _zstd_backend()


def zstd_available():
    return _ZSTD is not None


class _Zstd:
    """Decompresses zstd frames, with a dictionary when one is given."""

    def __init__(self, dictionary=b''):
        if _ZSTD is None:
            raise ValueError(ZSTD_MISSING)
        self.kind = _ZSTD_KIND
        self.dictionary = None
        if dictionary:
            if self.kind == 'zstandard':
                self.dictionary = _ZSTD.ZstdCompressionDict(dictionary)
            else:
                self.dictionary = _ZSTD.ZstdDict(dictionary)

    def decompress(self, data):
        try:
            if self.kind == 'zstandard':
                if self.dictionary is None:
                    decompressor = _ZSTD.ZstdDecompressor()
                else:
                    decompressor = _ZSTD.ZstdDecompressor(dict_data=self.dictionary)
                return decompressor.decompressobj().decompress(data)
            if self.dictionary is None:
                return _ZSTD.decompress(data)
            return _ZSTD.decompress(data, zstd_dict=self.dictionary)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Each backend raises its own error class (ZstdError in all three, from different modules).
            raise ValueError(f'zstd data could not be decoded ({exc})') from exc


def directory_time(seconds, nanoseconds):
    """The UTC datetime of a stored directory time, '' for the stored 0 or a value a datetime cannot hold.

    Nanoseconds are cut to the microseconds a datetime holds."""
    if seconds == 0 and nanoseconds == 0:
        return ''
    try:
        return _EPOCH + timedelta(seconds=seconds, microseconds=nanoseconds // 1000)
    except OverflowError:
        return ''


def text(raw):
    """A stored path or value as text. Bytes that are not UTF-8 are shown as backslash escapes."""
    return raw.decode('utf-8', 'backslashreplace')


class Entry:
    """One path in a locate database.

    time is the directory time stored for this entry when it is a directory, and
    container_time the one stored for the directory it is listed in, each a (seconds,
    nanoseconds) pair or None when the format stores none for it."""

    __slots__ = ('path', 'kind', 'time', 'container_time')

    def __init__(self, path, kind, time=None, container_time=None):
        self.path = path
        self.kind = kind
        self.time = time
        self.container_time = container_time


class LocateDatabase:
    """What a reader found in one database."""

    def __init__(self, fmt):
        self.format = fmt
        self.version = ''
        self.root = None
        self.visibility = None
        self.configuration = {}
        self.entries = []
        self.problems = []
        self.extra = {}
        self.paths_read = True

    def latest_directory_time(self):
        latest = None
        for entry in self.entries:
            for stamp in (entry.time, entry.container_time):
                if stamp and stamp != (0, 0) and (latest is None or stamp > latest):
                    latest = stamp
        return latest

    def counts(self):
        directories = sum(1 for e in self.entries if e.kind in (TYPE_DIRECTORY, TYPE_ROOT))
        others = sum(1 for e in self.entries if e.kind == TYPE_OTHER)
        zero = sum(1 for e in self.entries if e.kind in (TYPE_DIRECTORY, TYPE_ROOT) and e.time == (0, 0))
        return len(self.entries), directories, others, zero


def detect(data):
    """The format whose magic the bytes start with, or None."""
    if data.startswith(PLOCATE_MAGIC):
        return FORMAT_PLOCATE
    if data.startswith(MLOCATE_MAGIC):
        return FORMAT_MLOCATE
    if data.startswith(LOCATE02_MAGIC):
        return FORMAT_LOCATE02
    return None


def read(data):
    """Read a locate database of any of the three formats, or raise ValueError for anything else."""
    fmt = detect(data)
    if fmt == FORMAT_PLOCATE:
        return read_plocate(data)
    if fmt == FORMAT_MLOCATE:
        return read_mlocate(data)
    if fmt == FORMAT_LOCATE02:
        return read_locate02(data)
    raise ValueError('not a plocate, mlocate or LOCATE02 database (no magic at the start)')


def parse_configuration(block):
    """The configuration block mlocate and plocate store: a name, its values and an empty string, each
    NUL-terminated, repeated. Returns ({name: [values]}, problem or None)."""
    found = {}
    parts = block.split(b'\0')
    if block.endswith(b'\0'):
        parts = parts[:-1]
    else:
        return found, 'the configuration block does not end with a NUL byte'
    i = 0
    while i < len(parts):
        name = text(parts[i])
        i += 1
        values = []
        while i < len(parts) and parts[i] != b'':
            values.append(text(parts[i]))
            i += 1
        if i >= len(parts):
            found[name] = values
            return found, f'the values of {name} are not ended by an empty string'
        i += 1
        found[name] = values
    return found, None


def _parent(path):
    cut = path.rfind(b'/')
    if cut <= 0:
        return b'/'
    return path[:cut]


def _plocate_header(data):
    for order in ('<', '>'):
        (version,) = struct.unpack_from(order + 'I', data, 8)
        if version in (0, 1):
            break
    else:
        raise ValueError(f'plocate header version {struct.unpack_from("<I", data, 8)[0]} is neither 0 nor 1 in '
                         'either byte order')
    names = ('version', 'hashtable_size', 'extra_ht_slots', 'num_docids', 'hash_table_offset',
             'filename_index_offset', 'max_version', 'dictionary_length', 'dictionary_offset',
             'directory_data_length', 'directory_data_offset', 'next_dictionary_length',
             'next_dictionary_offset', 'conf_block_length', 'conf_block_offset', 'check_visibility')
    layout = _PLOCATE_HEADER if version == 1 else _PLOCATE_HEADER_V0
    if len(data) < 8 + struct.calcsize(order + layout):
        raise ValueError('the file is shorter than a plocate header')
    values = struct.unpack_from(order + layout, data, 8)
    header = dict(zip(names, values))
    header['order'] = order
    if version == 0:
        header.update(max_version=0, dictionary_length=0, dictionary_offset=0, directory_data_length=0,
                      directory_data_offset=0, conf_block_length=0, conf_block_offset=0, check_visibility=None)
    return header


def _slice(data, offset, length, what):
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ValueError(f'the {what} at offset {offset}, {length} bytes, runs past the end of the file '
                         f'({len(data)} bytes)')
    return data[offset:offset + length]


def read_plocate(data):
    """Read a plocate database (plocate 1.1.0 and later write version 1; version 0 is read the same way,
    without the dictionary and the fields that came after it)."""
    db = LocateDatabase(FORMAT_PLOCATE)
    header = _plocate_header(data)
    order = header['order']
    db.version = f"version {header['version']}, max_version {header['max_version']}"
    db.extra['byte order'] = 'little-endian' if order == '<' else 'big-endian'
    db.extra['filename blocks'] = header['num_docids']
    # plocate treats a database whose max_version is below 2 as asking for the visibility check.
    if header['max_version'] >= 2:
        db.visibility = 1 if header['check_visibility'] else 0
    if header['max_version'] >= 2 and header['conf_block_length']:
        try:
            block = _slice(data, header['conf_block_offset'], header['conf_block_length'], 'configuration block')
            db.configuration, problem = parse_configuration(block)
            if problem:
                db.problems.append(problem)
        except ValueError as exc:
            db.problems.append(str(exc))

    if not zstd_available():
        db.problems.append(ZSTD_MISSING)
        db.paths_read = False
        return db

    dictionary = b''
    if header['dictionary_length']:
        try:
            dictionary = _slice(data, header['dictionary_offset'], header['dictionary_length'], 'zstd dictionary')
        except ValueError as exc:
            db.problems.append(str(exc))
            db.paths_read = False
            return db
    decoder = _Zstd(dictionary)

    count = header['num_docids']
    try:
        index = _slice(data, header['filename_index_offset'], (count + 1) * 8, 'filename index')
    except ValueError as exc:
        db.problems.append(str(exc))
        db.paths_read = False
        return db
    offsets = struct.unpack(f'{order}{count + 1}Q', index)

    paths = []
    for block in range(count):
        start, end = offsets[block], offsets[block + 1]
        if not start <= end <= len(data):
            db.problems.append(f'filename block {block} has offsets {start} to {end}, outside the file; '
                               f'read stopped there with {len(paths):,} paths read')
            break
        try:
            names = decoder.decompress(data[start:end])
        except ValueError as exc:
            db.problems.append(f'filename block {block}: {exc}; read stopped there with {len(paths):,} paths read')
            break
        paths.extend(names.split(b'\0'))

    kinds, times = _plocate_directory_data(db, data, header, len(paths))
    directory_times = {}
    for i, path in enumerate(paths):
        kind = kinds[i] if kinds is not None else TYPE_UNRECORDED
        own = times[i] if kinds is not None else None
        if kind == TYPE_DIRECTORY:
            directory_times[path] = own
        container = directory_times.get(_parent(path))
        db.entries.append(Entry(text(path), kind, own, container))
    return db


def _plocate_directory_data(db, data, header, path_count):
    """Per path, whether it is a directory and its stored time, from the directory data updatedb writes:
    one byte 0 for a path that is not a directory, or one byte 1 followed by a 64-bit seconds and a 32-bit
    nanoseconds field. Returns (kinds, times), or (None, None) when the database holds none."""
    if header['max_version'] < 2 or not header['directory_data_length']:
        return None, None
    order = header['order']
    try:
        raw = _slice(data, header['directory_data_offset'], header['directory_data_length'], 'directory data')
        stream = _Zstd().decompress(raw)
    except ValueError as exc:
        db.problems.append(f'directory data: {exc}; entry types not given')
        return None, None
    kinds, times = [], []
    pos = 0
    record = struct.Struct(order + 'qi')
    while len(kinds) < path_count and pos < len(stream):
        flag = stream[pos]
        if flag == 0:
            kinds.append(TYPE_OTHER)
            times.append(None)
            pos += 1
        elif flag == 1 and pos + 1 + record.size <= len(stream):
            seconds, nanoseconds = record.unpack_from(stream, pos + 1)
            kinds.append(TYPE_DIRECTORY)
            times.append((seconds, nanoseconds))
            pos += 1 + record.size
        else:
            db.problems.append(f'directory data byte {pos} is {flag}, not a directory marker; entry types '
                               f'given for the first {len(kinds):,} paths only')
            break
    if len(kinds) < path_count:
        if pos >= len(stream):
            db.problems.append(f'directory data covers {len(kinds):,} of {path_count:,} paths')
        kinds.extend([TYPE_UNRECORDED] * (path_count - len(kinds)))
        times.extend([None] * (path_count - len(times)))
    elif pos != len(stream):
        db.problems.append(f'directory data has {len(stream) - pos:,} bytes after the last path')
    return kinds, times


def _cstring(data, pos, what):
    end = data.find(b'\0', pos)
    if end == -1:
        raise ValueError(f'{what} at offset {pos} has no terminating NUL byte')
    return data[pos:end], end + 1


def read_mlocate(data):
    """Read an mlocate database (file format version 0, the only one mlocate.db(5) defines)."""
    db = LocateDatabase(FORMAT_MLOCATE)
    if len(data) < 16:
        raise ValueError('the file is shorter than an mlocate header')
    conf_size = struct.unpack_from('>I', data, 8)[0]
    db.version = str(data[12])
    db.visibility = data[13]
    if data[12] != 0:
        db.problems.append(f'file format version {data[12]}; mlocate.db(5) defines only version 0')
    root, pos = _cstring(data, 16, 'the database root')
    db.root = text(root)
    try:
        block = _slice(data, pos, conf_size, 'configuration block')
    except ValueError as exc:
        db.problems.append(str(exc))
        db.paths_read = False
        return db
    db.configuration, problem = parse_configuration(block)
    if problem:
        db.problems.append(problem)
    pos += conf_size

    directories = []
    try:
        while pos < len(data):
            if pos + 16 > len(data):
                raise ValueError(f'a directory header at offset {pos} runs past the end of the file')
            seconds, nanoseconds = struct.unpack_from('>QI', data, pos)
            if nanoseconds >= _NSEC:
                db.problems.append(f'directory header at offset {pos} has {nanoseconds} nanoseconds')
            path, pos = _cstring(data, pos + 16, 'a directory path')
            names = []
            while True:
                if pos >= len(data):
                    raise ValueError(f'the entries of {text(path)} have no end marker')
                kind = data[pos]
                if kind == 2:
                    pos += 1
                    break
                if kind not in (0, 1):
                    raise ValueError(f'entry type {kind} at offset {pos} is not 0, 1 or 2')
                name, pos = _cstring(data, pos + 1, 'a file name')
                names.append((name, kind))
            directories.append((path, (seconds, nanoseconds), names))
    except ValueError as exc:
        db.problems.append(f'{exc}; read stopped there with {len(directories):,} directories read')

    times = {path: stamp for path, stamp, _ in directories}
    db.entries.append(Entry(db.root, TYPE_ROOT, times.get(root), None))
    for path, stamp, names in directories:
        prefix = path if path.endswith(b'/') else path + b'/'
        for name, kind in names:
            full = prefix + name
            if kind == 1:
                db.entries.append(Entry(text(full), TYPE_DIRECTORY, times.get(full), stamp))
            else:
                db.entries.append(Entry(text(full), TYPE_OTHER, None, stamp))
    db.extra['directory records'] = len(directories)
    return db


def read_locate02(data):
    """Read a GNU findutils LOCATE02 database: front-coded paths after a dummy LOCATE02 entry."""
    db = LocateDatabase(FORMAT_LOCATE02)
    db.version = 'LOCATE02'
    pos = len(LOCATE02_MAGIC)
    previous = b''
    count = 0
    try:
        while pos < len(data):
            code = data[pos]
            pos += 1
            if code == 0x80:
                if pos + 2 > len(data):
                    raise ValueError(f'a two-byte count at offset {pos} runs past the end of the file')
                count += struct.unpack_from('>h', data, pos)[0]
                pos += 2
            elif code > 127:
                count += code - 256
            else:
                count += code
            if count < 0 or count > len(previous):
                raise ValueError(f'shared prefix length {count} at offset {pos} is outside the previous path '
                                 f'({len(previous)} bytes)')
            rest, pos = _cstring(data, pos, 'a path')
            previous = previous[:count] + rest
            db.entries.append(Entry(text(previous), TYPE_UNRECORDED))
    except ValueError as exc:
        db.problems.append(f'{exc}; read stopped there with {len(db.entries):,} paths read')
    return db
