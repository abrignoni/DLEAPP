"""Firefox session store readers. Author: @AlexisBrignoni, Claude.

Firefox writes its session state as JSON through IOUtils with compression on, which
stores the bytes 'mozLz40\\0', the uncompressed size as a little-endian 32-bit integer,
and one LZ4 block (dom/system and xpcom/ioutils IOUtils at mozilla-firefox/firefox
c32abda0190531351e22da36334f18f9e994d474). The LZ4 block decoder below follows
lz4/lz4 doc/lz4_Block_format.md at 0774d05537f9762f838f7ab541b7765f1a729cb5. The
structure of the JSON follows the typedefs in browser/components/sessionstore at the
same Firefox revision; the artifact notes cite the lines.
"""

import json
from pathlib import PurePosixPath

from scripts.firefox import timestamp
from scripts.ilapfuncs import logfunc
from scripts.macos_plists import unique_sources, user_from_path

MOZLZ4_MAGIC = b'mozLz40\x00'


def lz4_block_decompress(data, size):
    """One LZ4 block, which must decode to exactly `size` bytes."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(f'LZ4 input is {type(data).__name__}, not bytes')
    src, out, pos = bytes(data), bytearray(), 0

    def length(value):
        nonlocal pos
        if value != 15:
            return value
        while True:
            if pos >= len(src):
                raise ValueError('truncated LZ4 length')
            byte = src[pos]
            pos += 1
            value += byte
            if byte != 255:
                return value

    while True:
        if pos >= len(src):
            raise ValueError('truncated LZ4 block')
        token = src[pos]
        pos += 1
        literals = length(token >> 4)
        if pos + literals > len(src):
            raise ValueError('truncated LZ4 literals')
        out += src[pos:pos + literals]
        pos += literals
        if pos == len(src):
            break                        # the last sequence holds only literals
        if pos + 2 > len(src):
            raise ValueError('truncated LZ4 offset')
        offset = src[pos] | (src[pos + 1] << 8)
        pos += 2
        if offset == 0 or offset > len(out):
            raise ValueError('invalid LZ4 offset')
        match = length(token & 0x0F) + 4
        if len(out) + match > size:
            raise ValueError('LZ4 block decodes past its declared size')
        start = len(out) - offset
        while match:                     # a match may overlap the bytes it produces
            take = min(match, len(out) - start)
            out += out[start:start + take]
            start += take
            match -= take
    if len(out) != size:
        raise ValueError(f'LZ4 block decoded to {len(out)} bytes, not the declared {size}')
    return bytes(out)


def mozlz4_decompress(data):
    """The contents of a file IOUtils wrote with compression on."""
    data = bytes(data)
    if len(data) < 12 or data[:8] != MOZLZ4_MAGIC:
        raise ValueError('not a mozLz4 file')
    size = int.from_bytes(data[8:12], 'little')
    return b'' if size == 0 else lz4_block_decompress(data[12:], size)


def _load(path):
    with open(path, 'rb') as handle:
        data = handle.read()
    if data[:8] == MOZLZ4_MAGIC:
        data = mozlz4_decompress(data)
    elif data.lstrip()[:1] != b'{':
        raise ValueError('neither mozLz4 nor JSON')
    state = json.loads(data.decode('utf-8'))
    if not isinstance(state, dict):
        raise ValueError('session state is not a JSON object')
    return state


def _list(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text(value):
    return value if isinstance(value, str) else '' if value is None else str(value)


def _tab_rows(tab, scope, window_no, position, closed_at, updated, group):
    entries = _list(tab.get('entries'))
    current = tab.get('index')
    for number, entry in enumerate(entries, 1):
        yield (timestamp(tab.get('lastAccessed'), 1000), timestamp(closed_at, 1000),
               timestamp(updated, 1000), scope, window_no, position, number,
               'Yes' if number == current else 'No', _text(entry.get('url')),
               _text(entry.get('title')), _text(entry.get('originalURI')),
               _text(entry.get('hasUserInteraction')), _text(tab.get('userContextId')),
               _text(tab.get('pinned')), _text(tab.get('hidden')), group)


def _window_rows(window, kind, window_no, updated, prefix):
    names = {g.get('id'): _text(g.get('name')) for g in _list(window.get('groups'))}
    closed_window = window.get('closedAt') if kind == 'closed window' else None
    tab_scope = 'Tab in closed window' if kind == 'closed window' else 'Open tab'
    for position, tab in enumerate(_list(window.get('tabs')), 1):
        yield from _tab_rows(tab, prefix + tab_scope, window_no, position, closed_window,
                             updated, names.get(tab.get('groupId'), ''))
    closed_scope = 'Closed tab in closed window' if kind == 'closed window' else 'Closed tab'
    for position, closed in enumerate(_list(window.get('_closedTabs')), 1):
        state = closed.get('state') if isinstance(closed.get('state'), dict) else {}
        yield from _tab_rows(state, prefix + closed_scope, window_no, position,
                             closed.get('closedAt'), updated, '')
    for group in _list(window.get('closedGroups')):
        for position, closed in enumerate(_list(group.get('tabs')), 1):
            state = closed.get('state') if isinstance(closed.get('state'), dict) else {}
            yield from _tab_rows(state, prefix + 'Tab in closed group', window_no, position,
                                 closed.get('closedAt') or group.get('closedAt'), updated,
                                 _text(group.get('name')))


def session_rows(state, prefix=''):
    """Row values, less the file columns, for every tab history entry a state holds."""
    session = state.get('session') if isinstance(state.get('session'), dict) else {}
    updated = session.get('lastUpdate')
    for window_no, window in enumerate(_list(state.get('windows')), 1):
        yield from _window_rows(window, 'window', window_no, updated, prefix)
    for window_no, window in enumerate(_list(state.get('_closedWindows')), 1):
        yield from _window_rows(window, 'closed window', window_no, updated, prefix)
    for group in _list(state.get('savedGroups')):
        for position, closed in enumerate(_list(group.get('tabs')), 1):
            tab = closed.get('state') if isinstance(closed.get('state'), dict) else {}
            yield from _tab_rows(tab, prefix + 'Tab in saved group', '', position,
                                 closed.get('closedAt') or group.get('closedAt'), updated,
                                 _text(group.get('name')))
    last = state.get('lastSessionState')
    if isinstance(last, dict) and not prefix:
        yield from session_rows(last, 'Last session: ')


def read_session_store(context, label):
    """Rows from each profile's sessionstore file and sessionstore-backups copies."""
    found = []
    for path in context.get_files_found():
        posix = PurePosixPath(str(path).replace('\\', '/'))
        if posix.name.startswith('sessionstore.') or posix.parent.name == 'sessionstore-backups':
            found.append(str(path))
    paths, _ = unique_sources(context, found, label=label)
    output, sources, skipped = [], [], 0
    for path in paths:
        relative = context.get_relative_path(path)
        parts = str(relative).replace('\\', '/').split('/')
        in_backups = len(parts) >= 3 and parts[-2] == 'sessionstore-backups'
        profile = parts[-3] if in_backups else (parts[-2] if len(parts) >= 2 else '')
        user = user_from_path(relative)
        if not user and 'home' in parts and parts.index('home') + 1 < len(parts):
            user = parts[parts.index('home') + 1]
        try:
            state = _load(path)
        except (OSError, ValueError, TypeError, UnicodeDecodeError) as exc:
            skipped += 1
            logfunc(f'{label}: {relative} was not read ({exc})')
            continue
        rows = [row + (parts[-1], profile, user, relative) for row in session_rows(state)]
        output.extend(rows)
        sources.append(path)
    if skipped:
        logfunc(f'{label}: {skipped} file(s) could not be read as a session store')
    return output, '\n'.join(sources)
