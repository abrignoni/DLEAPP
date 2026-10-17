"""Read web server logs line by line for DLEAPP artifacts: Apache HTTP Server and nginx access logs in the
common, combined and vhost_combined forms, Apache and nginx error logs, and W3C extended logs (IIS and
HTTP.sys) by each file's own #Fields directive.

The access line forms are the documented ones: Apache's
    common          %h %l %u %t "%r" %>s %b
    combined        %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"
    vhost_combined  %v:%p followed by combined (Debian's apache2.conf)
(https://httpd.apache.org/docs/2.4/mod/mod_log_config.html, "Examples"), which nginx's predefined combined
format writes in the same shape ($remote_addr - $remote_user [$time_local] "$request" $status
$body_bytes_sent "$http_referer" "$http_user_agent",
https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format). A line in none of them is kept whole,
never dropped.

Files are read as a stream, a line at a time, gzip ones (found by their first two bytes, not their name)
included, so a multi-gigabyte log is never held in memory.
"""

import re
import zlib
from datetime import datetime, timedelta, timezone

GZIP_MAGIC = b'\x1f\x8b'

_MONTHS = {name: number for number, name in enumerate(
    ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), 1)}

# [18/Sep/2011:19:18:28 -0400], then the quoted request line; this anchors the fields before it.
_CLF_TIME = re.compile(r' \[(\d{2})/([A-Z][a-z]{2})/(\d{4}):(\d{2}):(\d{2}):(\d{2}) ([+-])(\d{2})(\d{2})\] "')
_QUOTED = r'"((?:[^"\\]|\\.)*)"'
_AFTER_TIME = re.compile(_QUOTED + r' (\d{3}|-) (\d+|-)(?: ' + _QUOTED + ' ' + _QUOTED + r')?(.*)$')
_VHOST = re.compile(r'\S+:\d+$')

NOT_PARSED = 'not parsed'


def _gunzip_chunks(handle):
    """Yield the decompressed bytes of a gzip file, member after member, as far as they go.

    Raises zlib.error or EOFError after yielding everything that could be decompressed, so a damaged or
    cut file gives up its readable start, partial last line included.
    """
    data = handle.read(1 << 20)
    while data:
        member = zlib.decompressobj(16 + zlib.MAX_WBITS)
        while True:
            out = member.decompress(data)
            if out:
                yield out
            if member.eof:
                data = member.unused_data
                break
            data = handle.read(1 << 20)
            if not data:
                tail = member.flush()
                if tail:
                    yield tail
                raise EOFError('gzip data ends before the end of its stream')
        if not data:
            data = handle.read(1 << 20)
        if data and data[:2] != GZIP_MAGIC:
            raise zlib.error('bytes after the last gzip member')


def _split_lines(chunks):
    """Yield the lines of a byte stream, each with its line feed, the last one perhaps without."""
    pending = b''
    for chunk in chunks:
        pending += chunk
        start = 0
        while True:
            end = pending.find(b'\n', start)
            if end < 0:
                break
            yield pending[start:end + 1]
            start = end + 1
        pending = pending[start:]
    if pending:
        yield pending


def open_lines(path, counts):
    """Yield (line number, text, cut) for each line of a log file, decompressing gzip by content.

    Lines are split at line feeds only, as a line counter counts them, and decoded as UTF-8 with
    undecodable bytes replaced. A gzip stream that ends early or is damaged yields every line that could
    be decompressed and counts the file; its last line, when it has no line feed, comes with cut True,
    because the damage may have cut it. A file that cannot be opened counts and yields nothing.
    """
    try:
        handle = open(path, 'rb')
    except OSError:
        counts['files that could not be read'] += 1
        return
    with handle:
        compressed = handle.read(2) == GZIP_MAGIC
        handle.seek(0)
        if not compressed:
            for number, raw in enumerate(handle, 1):
                yield number, _text(raw), False
            return
        held, number = None, 0
        state = {'damaged': False}

        def chunks():
            try:
                yield from _gunzip_chunks(handle)
            except (EOFError, zlib.error):
                state['damaged'] = True

        for raw in _split_lines(chunks()):
            if held is not None:
                yield number, _text(held), False
            number += 1
            held = raw
        if state['damaged']:
            counts['files whose gzip data ends early or is damaged (lines before that point read)'] += 1
        if held is not None:
            yield number, _text(held), state['damaged'] and not held.endswith(b'\n')


def _text(raw):
    return raw.rstrip(b'\n').rstrip(b'\r').decode('utf-8', errors='replace')


def _zone(sign, hours, minutes):
    delta = timedelta(hours=int(hours), minutes=int(minutes))
    return timezone(-delta if sign == '-' else delta)


def clf_time(match):
    """The UTC time of a [dd/Mon/yyyy:HH:MM:SS +zzzz] stamp, or '' when it is not a calendar time."""
    day, month, year, hour, minute, second, sign, zone_h, zone_m = match.groups()
    month_number = _MONTHS.get(month)
    if month_number is None:
        return ''
    try:
        local = datetime(int(year), month_number, int(day), int(hour), int(minute), int(second),
                         tzinfo=_zone(sign, zone_h, zone_m))
    except ValueError:
        return ''
    return local.astimezone(timezone.utc)


def split_request(request):
    """(method, path, query, protocol) of a request line 'METHOD target PROTOCOL', blanks otherwise."""
    parts = request.split(' ')
    if len(parts) != 3 or not parts[0] or not parts[1]:
        return '', '', '', ''
    method, target, protocol = parts
    path, _, query = target.partition('?')
    return method, path, query, protocol


class AccessLine:
    """The fields of one access log line; field names follow the Apache format strings."""

    __slots__ = ('time', 'recorded', 'virtual_host', 'client', 'logname', 'user', 'request', 'status',
                 'size', 'referer', 'agent', 'other', 'form', 'raw')

    def __init__(self):
        self.time = self.recorded = self.virtual_host = self.client = self.logname = self.user = ''
        self.request = self.status = self.size = self.referer = self.agent = self.other = ''
        self.form = NOT_PARSED
        self.raw = ''


def parse_access_line(text, time_cache=None):
    """An AccessLine for one line in the common, combined or vhost_combined form.

    A line that is none of them comes back with form 'not parsed' and the whole line in raw.
    time_cache, a one-entry dict, saves converting the same stamp twice in a row.
    """
    line = AccessLine()
    match = _CLF_TIME.search(text)
    rest = _AFTER_TIME.match(text, match.end() - 1) if match else None
    if not rest:
        line.raw = text
        return line
    before = text[:match.start()].split(' ')
    if len(before) >= 4 and _VHOST.match(before[0]):
        line.virtual_host = before[0]
        before = before[1:]
        vhost = True
    else:
        vhost = False
    if len(before) < 3:
        line.raw = text
        return line
    line.client, line.logname = before[0], before[1]
    line.user = ' '.join(before[2:])
    stamp = text[match.start() + 2:match.end() - 3]
    line.recorded = stamp
    if time_cache is not None and time_cache.get('stamp') == stamp:
        line.time = time_cache['time']
    else:
        line.time = clf_time(match)
        if time_cache is not None:
            time_cache['stamp'], time_cache['time'] = stamp, line.time
    line.request, line.status, line.size, referer, agent, trailing = rest.groups()
    if referer is None:
        form = 'common'
    else:
        line.referer, line.agent = referer, agent
        form = 'combined'
    if vhost:
        form = 'vhost_' + form
    if trailing:
        line.other = trailing.strip()
        form += ' with trailing fields'
    line.form = form
    return line


# Error logs. Apache 2.4 writes "[%{u}t] [%-m:%l] [pid %P:tid %T] ... [client %a] %M" by default for
# threaded MPMs (core documentation, ErrorLogFormat), and 2.2 "[%t] [%l] [client %a] %M"; nginx writes
# "yyyy/mm/dd hh:mm:ss [level] pid#tid: *connection message".
_APACHE_ERROR = re.compile(
    r'\[(?P<time>[A-Z][a-z]{2} [A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2}(?:\.\d+)? \d{4})\] '
    r'\[(?:(?P<module>[^:\]\s]*):)?(?P<level>[^\]\s]+)\] '
    r'(?:\[pid (?P<pid>\d+)(?::tid (?P<tid>\d+))?\] )?'
    r'(?:\[client (?P<client>[^\]]+)\] )?(?P<message>.*)$')
_NGINX_ERROR = re.compile(
    r'(?P<time>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>[a-z]+)\] (?P<pid>\d+)#(?P<tid>\d+): '
    r'(?P<message>.*)$')
_NGINX_CLIENT = re.compile(r', client: ([^,]+)')


def local_iso(recorded, form):
    """The written time of an error line as ISO 8601 text with no zone, or '' when it is not a date."""
    try:
        if form == 'nginx':
            when = datetime.strptime(recorded, '%Y/%m/%d %H:%M:%S')
        else:
            text = re.sub(r'\s+', ' ', recorded)
            day_name, month, day, clock, year = text.split(' ')
            del day_name
            whole, _, fraction = clock.partition('.')
            when = datetime(int(year), _MONTHS[month], int(day), *map(int, whole.split(':')),
                            int((fraction or '0')[:6].ljust(6, '0')))
    except (ValueError, KeyError):
        return ''
    return when.isoformat(sep=' ')


def parse_error_line(text):
    """(time as recorded, local time, module, level, pid, tid, client, message, form) for an error line.

    A line in neither form gives form 'not parsed' with the whole line as the message.
    """
    match = _APACHE_ERROR.match(text)
    if match:
        recorded = match.group('time')
        return (recorded, local_iso(recorded, 'apache'), match.group('module') or '', match.group('level'),
                match.group('pid') or '', match.group('tid') or '', match.group('client') or '',
                match.group('message'), 'Apache')
    match = _NGINX_ERROR.match(text)
    if match:
        recorded = match.group('time')
        client = _NGINX_CLIENT.search(match.group('message'))
        return (recorded, local_iso(recorded, 'nginx'), '', match.group('level'), match.group('pid'),
                match.group('tid'), client.group(1) if client else '', match.group('message'), 'nginx')
    return ('', '', '', '', '', '', '', text, NOT_PARSED)


# W3C extended log format (https://www.w3.org/TR/WD-logfile.html): directives begin with '#', and
# '#Fields:' names the fields of the lines after it, separated by spaces. IIS and HTTP.sys write the
# date and time fields in UTC (https://learn.microsoft.com/en-us/windows/win32/http/w3c-logging).

def w3c_records(lines, counts):
    """Yield (line number, {field: value}, unparsed text) for each data line of a W3C extended log.

    Each '#Fields:' directive applies to the lines after it, until the next one. A data line before any
    '#Fields:' directive, or with a different number of values than its directive names, is yielded with
    an empty dict and its text, never dropped.
    """
    fields = None
    for number, text, _cut in lines:
        if not text.strip():
            continue
        if text.startswith('#'):
            if text.startswith('#Fields:'):
                fields = text[len('#Fields:'):].split()
                counts['#Fields directives'] += 1
            continue
        values = text.split(' ')
        if fields is None or len(values) != len(fields):
            counts['W3C lines that do not match their #Fields directive, kept whole'] += 1
            yield number, {}, text
            continue
        yield number, dict(zip(fields, values)), ''


def w3c_time(record):
    """The UTC time of a W3C record's date and time fields, or ''."""
    date, clock = record.get('date', ''), record.get('time', '')
    if not date or not clock:
        return ''
    try:
        return datetime.fromisoformat(f'{date}T{clock}').replace(tzinfo=timezone.utc)
    except ValueError:
        return ''



def unix_utc(value):
    """A Unix seconds value read back from the LAVA database as an aware UTC datetime, or ''."""
    if value in (None, ''):
        return ''
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ''
