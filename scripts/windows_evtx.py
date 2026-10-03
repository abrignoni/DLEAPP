"""Windows event log (EVTX) record helpers for DLEAPP.

Author: @AlexisBrignoni, Claude.

Shared by the event log artifacts. Each record is rendered to XML by
python-evtx and read with ElementTree.

`read_event_records(context, file_name, label, ...)` reads every matched copy
of one log and returns the parsed records it kept, each with the staged path it
was read from as `source`, and the paths it read. A
record python-evtx cannot render (the call raises) or whose XML does not parse
is counted and skipped instead of ending the read of the rest of the file, and
the count is written to the run log for each file.

`log_records(log, label, relative_source)` yields the records of an open
python-evtx log, and every artifact that reads a log reads it through this.
python-evtx's Evtx.records() reads only as many chunks as the file header's
chunk count (FileHeader.chunks, python-evtx v0.8.1,
https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Evtx.py#L223-L242).
libyal's description of the format says that the header of a log marked dirty
(flag 0x0001) can count fewer chunks than the file holds, that Event Viewer
seems to correct such a file, and that libevtx keeps scanning for chunks after
the last one the header indicates ('Dirty file with invalid number of chunks',
https://github.com/libyal/libevtx/blob/53ff3377d1360a9a3a428e7190c289757ccbf82b/documentation/Windows%20XML%20Event%20Log%20(EVTX).asciidoc?plain=1#L1817-L1842).
So for a log marked dirty this also reads each chunk after the counted ones
that carries the chunk signature and whose header and data checksums match,
and skips a record there whose number was already read. A log not marked dirty
is read exactly as python-evtx reads it.

`utc_from_system_time(value)` parses TimeCreated SystemTime. python-evtx 0.8.x
renders it as '2018-03-27 09:35:33.595600+00:00' and 0.7.x as
'2018-03-27 09:35:33.595600'; both come from the record's FILETIME converted in
UTC (python-evtx Evtx/BinaryParser.py, parse_filetime, which this module
replaces with an exact conversion, below). Those two forms and
'2018-03-27T09:35:33.5956Z' are accepted, and a value with no offset is taken
as UTC for that reason. python-evtx renders a zero FILETIME
as 0001-01-01 00:00:00; that is returned as '' rather than as a date.

python-evtx 0.8.1 renders one array value type, the array of UTF-16 strings
(0x81), as <string> pieces inside one element; for any other array type its
value lookup raises KeyError (get_variant_value,
https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L439-L474),
and the record cannot be rendered. libyal's description of the format gives
the arrays of fixed-width values as their elements stored one after another,
little-endian
(https://github.com/libyal/libevtx/blob/53ff3377d1360a9a3a428e7190c289757ccbf82b/documentation/Windows%20XML%20Event%20Log%20(EVTX).asciidoc?plain=1#L894-L940).
This module adds the arrays whose element size that description gives and for
which python-evtx has a value type of that size: 8, 16, 32 and 64-bit integers
(0x83 to 0x8a), 32 and 64-bit floating point (0x8b, 0x8c), GUID (0x8f),
FILETIME (0x91), system time (0x92) and 32 and 64-bit hexadecimal integers
(0x94, 0x95). Each element is rendered by python-evtx's own value type, and the
array as <string> pieces like a string array, which classic_strings splits.
An array whose size is not a whole number of elements still raises. Arrays of
booleans, size types, SIDs and ASCII strings are left as python-evtx has them.

A record can carry a ProcessingErrorData element in place of EventData, which
Microsoft's event schema describes as details of the error that occurred while
trying to render the event: the error code, the name of the data item that
caused it, and the event's binary data (Microsoft's event schema,
https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/eventschema-processingerrordata-eventtype-element.md?plain=1#L20).
EventRecord keeps those three as fields named ProcessingErrorData.ErrorCode,
ProcessingErrorData.DataItemName and ProcessingErrorData.EventPayload (the
binary data as python-evtx renders it, Base64 text), so an artifact that lists
a record's fields shows them; they are not added to the positional values.
ErrorCode 15005 is ERROR_EVT_INVALID_EVENT_DATA, 'The event data raised by the
publisher is not compatible with the event template definition in the
publisher's manifest'
(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/Debug/system-error-codes--12000-15999-.md?plain=1#L3526-L3536).
EventRecord also keeps the RelatedActivityID of the record's Correlation element.

python-evtx 0.8.1 turns a FILETIME (the record's TimeCreated and any FILETIME
value) into a datetime through a floating-point number, float(qword) * 1e-7
(parse_filetime,
https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113).
A FILETIME of this century is larger than 2^53, the largest integer a float
holds exactly, so the result can differ from the stored count by a microsecond
or two. This module replaces that function with integer arithmetic: the count
of 100-nanosecond intervals since 1601-01-01 UTC, cut to whole microseconds.
Zero, and a count outside the dates Python can hold, still give
python-evtx's 0001-01-01.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

try:
    import Evtx.BinaryParser as evtx_binary
    import Evtx.Evtx as evtx
    import Evtx.Nodes as evtx_nodes
except ImportError:
    evtx = None
    evtx_nodes = None
    evtx_binary = None

from scripts.ilapfuncs import logfunc

# Array value type: (python-evtx value type of one element, element size in bytes).
_ARRAY_ELEMENTS = {
    0x83: ('SignedByteTypeNode', 1),
    0x84: ('UnsignedByteTypeNode', 1),
    0x85: ('SignedWordTypeNode', 2),
    0x86: ('UnsignedWordTypeNode', 2),
    0x87: ('SignedDwordTypeNode', 4),
    0x88: ('UnsignedDwordTypeNode', 4),
    0x89: ('SignedQwordTypeNode', 8),
    0x8A: ('UnsignedQwordTypeNode', 8),
    0x8B: ('FloatTypeNode', 4),
    0x8C: ('DoubleTypeNode', 8),
    0x8F: ('GuidTypeNode', 16),
    0x91: ('FiletimeTypeNode', 8),
    0x92: ('SystemtimeTypeNode', 16),
    0x94: ('Hex32TypeNode', 4),
    0x95: ('Hex64TypeNode', 8),
}


def _array_value_class(element_name, element_size):
    """A python-evtx value type for an array of fixed-width values."""
    element_class = getattr(evtx_nodes, element_name)

    class ArrayTypeNode(evtx_nodes.VariantTypeNode):
        """Elements stored one after another; rendered as <string> pieces."""

        def __init__(self, buf, offset, chunk, parent, length=None):
            if length is None:
                raise NotImplementedError('an array value outside a substitution has no size')
            if length % element_size:
                raise ValueError(f'array of {length} bytes is not a whole number of {element_size}-byte values')
            super().__init__(buf, offset, chunk, parent, length=length)
            self._array_parent = parent

        def tag_length(self):
            return self._length

        def string(self):
            pieces = []
            for index in range(self._length // element_size):
                element = element_class(self._buf, self.offset() + index * element_size, self._chunk,
                                        self._array_parent, length=element_size)
                pieces.append(f'<string>{element.string()}</string>\n')
            return ''.join(pieces)

    ArrayTypeNode.__name__ = f'Array{element_name}'
    return ArrayTypeNode


def _install_array_values():
    """Route the array types above to their classes; any other type goes to python-evtx."""
    if evtx_nodes is None or getattr(evtx_nodes.get_variant_value, 'dleapp_arrays', False):
        return
    original = evtx_nodes.get_variant_value
    classes = {value_type: _array_value_class(name, size) for value_type, (name, size) in _ARRAY_ELEMENTS.items()}

    def get_variant_value(buf, offset, chunk, parent, type_, length=None):
        array_class = classes.get(type_)
        if array_class is not None:
            return array_class(buf, offset, chunk, parent, length=length)
        return original(buf, offset, chunk, parent, type_, length=length)

    get_variant_value.dleapp_arrays = True
    get_variant_value.original = original
    evtx_nodes.get_variant_value = get_variant_value


_install_array_values()

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _install_exact_filetime():
    """Replace python-evtx's float FILETIME conversion with an exact one, keeping its form of result."""
    if evtx_binary is None or getattr(evtx_binary.parse_filetime, 'dleapp_exact', False):
        return
    original = evtx_binary.parse_filetime
    aware = original(116444736000000000).tzinfo is not None  # 1970-01-01: 0.8.x is aware, 0.7.x naive

    def parse_filetime(qword):
        if qword == 0:
            return datetime.min
        try:
            when = _FILETIME_EPOCH + timedelta(microseconds=qword // 10)
        except (OverflowError, ValueError):
            return datetime.min
        return when if aware else when.replace(tzinfo=None)

    parse_filetime.dleapp_exact = True
    parse_filetime.original = original
    evtx_binary.parse_filetime = parse_filetime


_install_exact_filetime()

_SYSTEM_TIME = re.compile(
    r'^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.(\d+))?\s*(Z|[+-]\d{2}:\d{2})?$',
    re.IGNORECASE)

# Classic (non-manifest) providers store their insertion strings as a string
# array, which python-evtx renders inside one <Data> element as
# <string>...</string> pieces.
_CLASSIC_STRING = re.compile(r'<string>(.*?)</string>', re.DOTALL)


def utc_from_system_time(value):
    """Return an aware UTC datetime for an EVTX SystemTime rendering, or ''."""
    match = _SYSTEM_TIME.match((value or '').strip())
    if not match:
        return ''
    date_part, time_part, fraction, offset = match.groups()
    fraction = (fraction or '').ljust(6, '0')[:6]
    if not offset or offset.upper() == 'Z':
        offset = '+00:00'
    try:
        parsed = datetime.fromisoformat(f'{date_part}T{time_part}.{fraction}{offset}')
    except ValueError:
        return ''
    if parsed.year == 1:
        return ''
    return parsed.astimezone(timezone.utc)


def classic_strings(values):
    """Split classic insertion strings rendered as <string> pieces; keep others."""
    strings = []
    for value in values:
        pieces = _CLASSIC_STRING.findall(value or '')
        if pieces:
            strings.extend(pieces)
        else:
            strings.append(value or '')
    return strings


def hex_status(value):
    """Render a stored unsigned status number as '0x........ (decimal)'."""
    text = (value or '').strip()
    if not text.isdigit():
        return text
    return f'0x{int(text):08X} ({text})'


class EventRecord:
    """The System fields and the event data of one parsed record."""

    __slots__ = ('provider', 'event_id', 'version', 'level', 'time', 'record_id',
                 'computer', 'user_sid', 'process_id', 'channel', 'activity_id', 'fields',
                 'values', 'user_data_name', 'source', 'related_activity_id', 'processing_error')

    def __init__(self, root, source=''):
        self.source = source
        system = root.find('{*}System')
        self.provider = ''
        self.event_id = ''
        self.version = ''
        self.level = ''
        self.time = ''
        self.record_id = ''
        self.computer = ''
        self.user_sid = ''
        self.process_id = ''
        self.channel = ''
        self.activity_id = ''
        self.related_activity_id = ''
        if system is not None:
            provider = system.find('{*}Provider')
            self.provider = provider.get('Name', '') if provider is not None else ''
            self.event_id = _text(system, 'EventID')
            self.version = _text(system, 'Version')
            self.level = _text(system, 'Level')
            created = system.find('{*}TimeCreated')
            self.time = utc_from_system_time(
                created.get('SystemTime') if created is not None else '')
            self.record_id = _text(system, 'EventRecordID')
            self.computer = _text(system, 'Computer')
            self.channel = _text(system, 'Channel')
            security = system.find('{*}Security')
            self.user_sid = (security.get('UserID') or '') if security is not None else ''
            execution = system.find('{*}Execution')
            self.process_id = (execution.get('ProcessID') or '') if execution is not None else ''
            correlation = system.find('{*}Correlation')
            self.activity_id = ((correlation.get('ActivityID') or '')
                                if correlation is not None else '')
            self.related_activity_id = ((correlation.get('RelatedActivityID') or '')
                                        if correlation is not None else '')
        self.fields = {}
        self.values = []
        self.user_data_name = ''
        self.processing_error = {}
        event_data = root.find('{*}EventData')
        user_data = root.find('{*}UserData')
        processing_error = root.find('{*}ProcessingErrorData')
        if processing_error is not None:
            for item in processing_error:
                name = item.tag.split('}')[-1]
                self.processing_error[name] = item.text or ''
                self.fields[f'ProcessingErrorData.{name}'] = item.text or ''
        if event_data is not None:
            for item in event_data.findall('{*}Data'):
                text = item.text or ''
                self.values.append(text)
                name = item.get('Name')
                if name:
                    self.fields[name] = text
        elif user_data is not None and len(user_data):
            self.user_data_name = user_data[0].tag.split('}')[-1]
            for item in user_data[0]:
                name = item.tag.split('}')[-1]
                text = item.text or ''
                self.values.append(text)
                self.fields[name] = text

    def get(self, name):
        """The named event data field as stored, stripped; '' when absent."""
        return (self.fields.get(name) or '').strip()


def _text(parent, name):
    element = parent.find('{*}' + name)
    return element.text.strip() if element is not None and element.text else ''


def _intact(chunk):
    """Whether a chunk carries the chunk signature and both of its checksums match."""
    try:
        return bool(chunk.check_magic()
                    and chunk.calculate_header_checksum() == chunk.header_checksum()
                    and chunk.calculate_data_checksum() == chunk.data_checksum())
    except Exception:  # pylint: disable=broad-exception-caught
        return False


def log_records(log, label='', relative_source=''):
    """Every record of an open python-evtx log, with the chunks a dirty header does not count.

    The counted chunks are read as python-evtx reads them. For a log marked dirty,
    each later chunk is read when it is intact (_intact), a record whose number was
    already read is skipped, and a chunk whose records stop parsing part way through
    keeps the records read before that point. The run log names the log and says how
    many records came from chunks the header does not count.
    """
    header = log.get_file_header()
    counted = header.chunk_count()
    dirty = header.is_dirty()
    seen = set()
    added = read_chunks = failed_checksum = stopped = 0
    for index, chunk in enumerate(header.chunks(include_inactive=dirty)):
        if index < counted:
            for record in chunk.records():
                if dirty:
                    seen.add(record.record_num())
                yield record
            continue
        if not chunk.check_magic():
            continue
        if not _intact(chunk):
            failed_checksum += 1
            continue
        read_chunks += 1
        records = chunk.records()
        while True:
            try:
                record = next(records)
                number = record.record_num()
            except StopIteration:
                break
            except Exception:  # pylint: disable=broad-exception-caught
                stopped += 1
                break
            if number in seen:
                continue
            seen.add(number)
            added += 1
            yield record
    if read_chunks or failed_checksum:
        message = (f'{label}: {relative_source} is marked dirty; {added} record(s) were read '
                   f'from {read_chunks} chunk(s) after the {counted} its header counts')
        if failed_checksum:
            message += f', and {failed_checksum} chunk(s) after them failed their checksums and were not read'
        if stopped:
            message += f'; {stopped} of those chunk(s) stopped parsing part way through'
        logfunc(message)


def read_event_records(context, file_name, label, event_ids=None, provider=None):
    """Read every copy of one event log in files_found.

    Returns (records, sources): the parsed EventRecord objects whose Event ID is
    in `event_ids` (and whose provider is `provider`, when given), in file order,
    and the staged paths that were read.
    """
    records = []
    sources = []
    if evtx is None:
        logfunc(f'{label}: python-evtx is not installed (pip install python-evtx)')
        return records, sources
    wanted = file_name.lower()
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(wanted)]:
        if os.path.isdir(source):
            continue
        relative_source = context.get_relative_path(source)
        read = unrendered = unparsed = 0
        try:
            with evtx.Evtx(source) as log:
                sources.append(source)
                for record in log_records(log, label, relative_source):
                    read += 1
                    try:
                        xml_text = record.xml()
                    except Exception:  # pylint: disable=broad-exception-caught
                        unrendered += 1
                        continue
                    try:
                        root = ElementTree.fromstring(xml_text)
                    except ElementTree.ParseError:
                        unparsed += 1
                        continue
                    parsed = EventRecord(root, source)
                    if event_ids is not None and parsed.event_id not in event_ids:
                        continue
                    if provider is not None and parsed.provider != provider:
                        continue
                    records.append(parsed)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{label}: could not read {relative_source}: {exc}')
        logfunc(f'{label}: {read} records in {relative_source}; '
                f'{unrendered} could not be rendered by python-evtx and '
                f'{unparsed} did not parse as XML')
    return records, sources
