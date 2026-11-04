"""Read the records of an Event Trace Log (.etl) file and decode manifest events from templates given to it.

Author: @AlexisBrignoni, Claude.

Nothing here writes a file or calls Windows. What is implemented, with the source of each layout:

* Buffers. The file is a run of fixed-size buffers, each a 0x48-byte WMI_BUFFER_HEADER (BufferSize at 0x00,
  the offset to the next buffer in the file; SavedOffset at 0x04, the bytes of the buffer in use; SequenceNumber
  at 0x18) followed by records (Geoff Chappell, WMI_BUFFER_HEADER,
  https://www.geoffchappell.com/studies/windows/km/ntoskrnl/inc/api/ntwmi/wmi_buffer_header/index.htm).
* Records. Each record starts on an 8-byte boundary, and its first dword has the high bit set; the byte at 0x02
  gives the header type and the record size is a 16-bit value (Geoff Chappell, Trace Headers,
  https://geoffchappell.com/studies/windows/km/ntoskrnl/inc/api/ntwmi/traceheaders/index.htm). The size is at
  0x04 for a SYSTEM_TRACE_HEADER, its compact form and a PERFINFO_TRACE_HEADER (types 0x01 to 0x04, 0x10, 0x11;
  https://www.geoffchappell.com/studies/windows/km/ntoskrnl/inc/api/ntwmi/traceheaders/system_trace_header.htm)
  and at 0x00 for an EVENT_HEADER (0x12, 0x13), an EVENT_TRACE_HEADER (0x0A, 0x14) and an instance header
  (0x0B, 0x15). A MESSAGE_TRACE_HEADER (WPP) is a first dword with 0x10000000 set and 0x40000000 clear, whose
  low word is the size, followed by optional members its OptionFlags select (Geoff Chappell,
  https://geoffchappell.com/studies/windows/km/ntoskrnl/inc/api/ntwmi/traceheaders/message_trace_header.htm).
  A dword without the high bit is taken as the end of the buffer's records (this reader's rule;
  on the corpus files it lost no event Get-WinEvent returned).
* The EVENT_HEADER is Microsoft's (evntcons.h,
  https://learn.microsoft.com/en-us/windows/win32/api/evntcons/ns-evntcons-event_header): Size, HeaderType,
  Flags, EventProperty, ThreadId, ProcessId, TimeStamp at 0x10, ProviderId at 0x18, the EVENT_DESCRIPTOR at 0x28
  (Id, Version, Channel, Level, Opcode, Task, Keyword; evntprov.h,
  https://learn.microsoft.com/en-us/windows/win32/api/evntprov/ns-evntprov-event_descriptor) and ActivityId,
  0x50 bytes in all. When Flags has EVENT_HEADER_FLAG_EXTENDED_INFO (0x0001), extended data items come first,
  each 8-byte aligned with its total size in its first word and a linkage bit saying another follows (Geoff
  Chappell, https://geoffchappell.com/studies/windows/km/ntoskrnl/inc/shared/evntcons/event_header.htm); the
  event's own data follows them. EVENT_HEADER_FLAG_32_BIT_HEADER (0x0020) and 64_BIT_HEADER (0x0040) give the
  pointer size of the event's data.
* The session. The first record of the file is a SYSTEM_TRACE_HEADER whose data is the TRACE_LOGFILE_HEADER
  (Microsoft, evntrace.h, https://learn.microsoft.com/en-us/windows/win32/api/evntrace/ns-evntrace-trace_logfile_header):
  BufferSize, Version, ProviderVersion (the build), NumberOfProcessors, EndTime, TimerResolution,
  MaximumFileSize (MB), LogFileMode, BuffersWritten, then StartBuffers, PointerSize, EventsLost and
  CpuSpeedInMHz, two pointers, TIME_ZONE_INFORMATION (172 bytes), BootTime, PerfFreq, StartTime, ReservedFlags
  (the clock type) and BuffersLost.
* Times. ReservedFlags 1 is the performance counter and 2 system time (WNODE_HEADER ClientContext,
  https://learn.microsoft.com/en-us/windows/win32/etw/wnode-header). For the performance counter a record's time
  is StartTime + int((TimeStamp - T0) * (10,000,000 / PerfFreq)) in FILETIME units, where T0 is the logfile
  header record's own time stamp: the scale is a floating-point multiply and the result is truncated. This rule
  was not found written down; it is the one that gave the same time, to the 100 ns, as Windows' Get-WinEvent
  (Windows 11 build 26200) for every record of six corpus Wifi*.etl files that Get-WinEvent returned, including
  one whose PerfFreq is not 10 MHz, where integer division and rounding each disagreed on some records. A system
  time stamp is taken as a FILETIME (documented, not exercised). The CPU cycle clock (3) is not converted: its
  times are None.

Not read: the data of WPP records (no format information is in the file), of system and PERFINFO records other
than the logfile header, and of classic and instance headers; their records are counted. Windows' Get-WinEvent
returns no event from a buffer that ends past MaximumFileSize (seen on two corpus files whose last buffer did);
this reader reads it, because its sequence number lay among the others' and its records framed like theirs.
"""

import collections
import struct
import uuid

BUFFER_HEADER = 0x48
_EVENT_HEADER = 0x50
_LOGFILE_HEADER_HOOK = 0x0000
_FILETIME_PER_SECOND = 10_000_000

_SYSTEM = {0x01: 'system32', 0x02: 'system64', 0x03: 'compact32', 0x04: 'compact64', 0x10: 'perfinfo32',
           0x11: 'perfinfo64'}
_SIZE_AT_ZERO = {0x0a: 'classic32', 0x14: 'classic64', 0x0b: 'instance32', 0x15: 'instance64'}
_EVENT = {0x12: 'event32', 0x13: 'event64'}

_FLAG_EXTENDED_INFO = 0x0001
_FLAG_32_BIT = 0x0020
_FLAG_64_BIT = 0x0040

CLOCK_PERFORMANCE_COUNTER = 1
CLOCK_SYSTEM_TIME = 2
CLOCK_CPU_CYCLE = 3


class EtlError(ValueError):
    """A file this reader cannot read as an ETL file."""


class EtlEvent:
    """One EVENT_HEADER record: its time, provider, descriptor and data."""

    __slots__ = ('filetime', 'provider', 'event_id', 'version', 'channel', 'level', 'opcode', 'task',
                 'keyword', 'process_id', 'thread_id', 'pointer_size', 'data', 'buffer', 'sequence', 'offset')

    def __init__(self, **values):
        for name, value in values.items():
            setattr(self, name, value)


class EtlFile:
    """The session header, the records and the problems of one ETL file's bytes.

    `kinds` counts every record by header kind; `problems` counts each thing the walk could not read,
    by what it was. `events()` yields the EVENT_HEADER records in file order (buffers are per processor,
    so file order is not time order)."""

    def __init__(self, data):
        self.data = data
        self.kinds = collections.Counter()
        self.problems = collections.Counter()
        if len(data) < BUFFER_HEADER + 0x20:
            raise EtlError('the file is shorter than one buffer header and one record')
        self.buffer_size = struct.unpack_from('<I', data, 0)[0]
        if self.buffer_size < BUFFER_HEADER + 0x20 or self.buffer_size > len(data):
            raise EtlError(f'a first buffer of {self.buffer_size} bytes')
        self.header = self._logfile_header()
        self._t0 = self.header['header_timestamp']

    # ------------------------------------------------------------------ session header

    def _logfile_header(self):
        record = BUFFER_HEADER
        marker, size, hook = struct.unpack_from('<IHH', self.data, record)
        if not marker & 0x80000000 or (marker >> 16) & 0xff not in (0x01, 0x02) or hook != _LOGFILE_HEADER_HOOK:
            raise EtlError('the first record is not a logfile header (SYSTEM_TRACE_HEADER, hook 0)')
        o = record + 0x20
        if size < 0x20 + 248:
            raise EtlError(f'a logfile header record of {size} bytes')
        values = struct.unpack_from('<IIIIqIIIIIIII', self.data, o)
        names = ('buffer_size', 'version', 'build', 'processors', 'end_time', 'timer_resolution',
                 'maximum_file_size_mb', 'log_file_mode', 'buffers_written', 'start_buffers', 'pointer_size',
                 'events_lost', 'cpu_mhz')
        header = dict(zip(names, values))
        if header['pointer_size'] not in (4, 8):
            raise EtlError(f"a logfile header pointer size of {header['pointer_size']}")
        time_zone = o + 56 + 2 * header['pointer_size']
        after = (time_zone + 172 - o + 7) & ~7
        header['tz_bias_minutes'] = struct.unpack_from('<i', self.data, time_zone)[0]
        (header['boot_time'], header['perf_freq'], header['start_time'],
         header['clock_type'], header['buffers_lost']) = struct.unpack_from('<qqqII', self.data, o + after)
        header['header_timestamp'] = struct.unpack_from('<q', self.data, record + 0x10)[0]
        if header['buffer_size'] != self.buffer_size:
            raise EtlError(f"the logfile header names {header['buffer_size']}-byte buffers, the file has "
                           f'{self.buffer_size}')
        if header['clock_type'] == CLOCK_PERFORMANCE_COUNTER and header['perf_freq'] <= 0:
            raise EtlError('a performance counter clock with no frequency')
        return header

    def filetime(self, stamp):
        """The FILETIME of a record time stamp, or None when the clock is not one this reader converts."""
        clock = self.header['clock_type']
        if clock == CLOCK_PERFORMANCE_COUNTER:
            return self.header['start_time'] + int((stamp - self._t0) * (_FILETIME_PER_SECOND / self.header['perf_freq']))
        if clock == CLOCK_SYSTEM_TIME:
            return stamp
        return None

    # ------------------------------------------------------------------ records

    def buffers(self):
        """(index, offset, sequence number, end of the bytes in use) for each buffer in file order."""
        offset = 0
        index = 0
        data = self.data
        while offset + BUFFER_HEADER <= len(data):
            size, saved = struct.unpack_from('<II', data, offset)
            if size != self.buffer_size:
                self.problems[f'buffers of {size} bytes, not {self.buffer_size}; the walk stopped there'] += 1
                return
            if offset + size > len(data):
                self.problems['a last buffer cut short by the end of the file, not read'] += 1
                return
            if saved > size or saved < BUFFER_HEADER:
                self.problems['buffers whose bytes in use lie outside the buffer, not read'] += 1
            else:
                yield index, offset, struct.unpack_from('<q', data, offset + 0x18)[0], offset + saved
            offset += size
            index += 1
        if offset != len(data):
            self.problems['bytes after the last whole buffer, not read'] += 1

    def events(self):
        data = self.data
        for index, start, sequence, end in self.buffers():
            position = start + BUFFER_HEADER
            while position + 8 <= end:
                marker = struct.unpack_from('<I', data, position)[0]
                if not marker & 0x80000000:
                    break
                htype = (marker >> 16) & 0xff
                if marker & 0x10000000 and not marker & 0x40000000:
                    kind, size = 'wpp', marker & 0xffff
                elif htype in _SYSTEM:
                    kind, size = _SYSTEM[htype], struct.unpack_from('<H', data, position + 4)[0]
                elif htype in _EVENT or htype in _SIZE_AT_ZERO:
                    kind, size = _EVENT.get(htype) or _SIZE_AT_ZERO[htype], marker & 0xffff
                else:
                    self.problems[f'records of header type {htype:#04x}, which ended their buffer'] += 1
                    break
                if size < 8 or position + size > end:
                    self.problems['records whose size runs past the buffer, which ended their buffer'] += 1
                    break
                self.kinds[kind] += 1
                if htype in _EVENT:
                    event = self._event(position, size, index, sequence)
                    if event is not None:
                        yield event
                position += (size + 7) & ~7

    def _event(self, position, size, index, sequence):
        data = self.data
        if size < _EVENT_HEADER:
            self.problems['event records shorter than an EVENT_HEADER'] += 1
            return None
        flags = struct.unpack_from('<H', data, position + 4)[0]
        thread_id, process_id, stamp = struct.unpack_from('<IIq', data, position + 8)
        provider = str(uuid.UUID(bytes_le=bytes(data[position + 0x18:position + 0x28])))
        event_id, version, channel, level, opcode, task, keyword = struct.unpack_from('<HBBBBHQ', data, position + 0x28)
        body = position + _EVENT_HEADER
        end = position + size
        if flags & _FLAG_EXTENDED_INFO:
            while True:
                if body + 8 > end:
                    self.problems['event records whose extended data runs past the record'] += 1
                    return None
                item_size, _ext_type, linkage = struct.unpack_from('<HHH', data, body)
                if item_size < 8:
                    self.problems['event records with an extended data item under 8 bytes'] += 1
                    return None
                body += (item_size + 7) & ~7
                if not linkage & 1:
                    break
            if body > end:
                self.problems['event records whose extended data runs past the record'] += 1
                return None
        if flags & _FLAG_32_BIT:
            pointer = 4
        elif flags & _FLAG_64_BIT:
            pointer = 8
        else:
            pointer = 8 if (struct.unpack_from('<I', data, position)[0] >> 16) & 0xff == 0x13 else 4
        return EtlEvent(filetime=self.filetime(stamp), provider=provider, event_id=event_id, version=version,
                        channel=channel, level=level, opcode=opcode, task=task, keyword=keyword,
                        process_id=process_id, thread_id=thread_id, pointer_size=pointer,
                        data=bytes(data[body:end]), buffer=index, sequence=sequence, offset=position)


# ---------------------------------------------------------------------- templates

def decode(data, fields, pointer_size):
    """{name: value} for an event's data read with a manifest template, and the bytes left over.

    `fields` is a sequence of (name, in_type) or (name, in_type, length), where length is a number of bytes
    or the name of an earlier field holding it, as the manifest's data element gives them. In-type sizes
    follow the manifest InputType definitions
    (https://learn.microsoft.com/en-us/windows/win32/wes/eventmanifestschema-inputtype-complextype):
    win:Boolean is 32 bits and win:Pointer is the event's pointer size. A UnicodeString with no length runs
    to its NUL. Raises ValueError when the data ends early."""
    values = {}
    position = 0
    for field in fields:
        name, in_type = field[0], field[1]
        length = field[2] if len(field) > 2 else None
        if isinstance(length, str):
            length = values[length]
        if in_type == 'win:UnicodeString':
            if length is None:
                end = position
                while True:
                    if end + 2 > len(data):
                        raise ValueError(f'{name}: no NUL before the data ends')
                    if data[end:end + 2] == b'\x00\x00':
                        break
                    end += 2
                values[name] = data[position:end].decode('utf-16-le', errors='replace')
                position = end + 2
            else:
                values[name] = data[position:position + 2 * length].decode('utf-16-le', errors='replace')
                position += 2 * length
            continue
        if in_type == 'win:Binary':
            if length is None or position + length > len(data):
                raise ValueError(f'{name}: binary data runs past the event')
            values[name] = bytes(data[position:position + length])
            position += length
            continue
        if in_type == 'win:GUID':
            if position + 16 > len(data):
                raise ValueError(f'{name}: the data ends early')
            values[name] = str(uuid.UUID(bytes_le=bytes(data[position:position + 16])))
            position += 16
            continue
        code = {'win:UInt8': '<B', 'win:UInt16': '<H', 'win:UInt32': '<I', 'win:UInt64': '<Q',
                'win:Int32': '<i', 'win:Int64': '<q', 'win:Boolean': '<I', 'win:HexInt32': '<I',
                'win:HexInt64': '<Q'}.get(in_type)
        if in_type == 'win:Pointer':
            code = '<I' if pointer_size == 4 else '<Q'
        if code is None:
            raise ValueError(f'{name}: in-type {in_type} is not read by this module')
        width = struct.calcsize(code)
        if position + width > len(data):
            raise ValueError(f'{name}: the data ends early')
        value = struct.unpack_from(code, data, position)[0]
        values[name] = bool(value) if in_type == 'win:Boolean' else value
        position += width
    return values, len(data) - position
