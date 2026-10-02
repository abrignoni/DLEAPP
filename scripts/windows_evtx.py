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
UTC (python-evtx Evtx/BinaryParser.py, parse_filetime). Those two forms and
'2018-03-27T09:35:33.5956Z' are accepted, and a value with no offset is taken
as UTC for that reason. python-evtx renders a zero FILETIME
as 0001-01-01 00:00:00; that is returned as '' rather than as a date.
"""

import os
import re
from datetime import datetime, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import logfunc

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
                 'values', 'user_data_name', 'source')

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
        self.fields = {}
        self.values = []
        self.user_data_name = ''
        event_data = root.find('{*}EventData')
        user_data = root.find('{*}UserData')
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
