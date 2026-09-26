"""Firefox SQLite readers. Author: @AlexisBrignoni, Codex.

Field definitions and validation boundaries: admin/docs/firefox-validation.md.
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath

from scripts.ilapfuncs import logfunc, open_sqlite_db_readonly
from scripts.macos_plists import unique_sources, user_from_path

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_TRANSITIONS = {1: 'LINK', 2: 'TYPED', 3: 'BOOKMARK', 4: 'EMBED',
                5: 'REDIRECT_PERMANENT', 6: 'REDIRECT_TEMPORARY', 7: 'DOWNLOAD',
                8: 'FRAMED_LINK', 9: 'RELOAD'}
_STATES = {1: 'FINISHED', 2: 'FAILED', 3: 'CANCELED', 4: 'PAUSED',
           6: 'BLOCKED_PARENTAL', 8: 'DIRTY', 9: 'BLOCKED_CONTENT_ANALYSIS'}


def timestamp(value, units=1_000_000):
    """Integer Unix timestamp; zero/NULL are left blank, preserving microseconds."""
    if value in (None, '', 0) or isinstance(value, bool):
        return ''
    try:
        seconds, remainder = divmod(int(value), units)
        return _EPOCH + timedelta(seconds=seconds, microseconds=remainder * (1_000_000 // units))
    except (TypeError, ValueError, OverflowError):
        return ''


def columns(db, table):
    """Names from a fixed, internal SQLite table identifier."""
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def optional(db, table, names, alias=''):
    present = columns(db, table)
    prefix = alias + '.' if alias else ''
    return ', '.join(f'{prefix}"{name}" AS "{name}"' if name in present
                     else f'NULL AS "{name}"' for name in names)


def read_artifact(context, filename, reader, label):
    """Read each profile independently, including WAL, with original-path provenance."""
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name == filename]
    paths, _ = unique_sources(context, found, sidecars=('-wal',), label=label)
    output, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        normalized = str(relative).replace('\\', '/')
        profile = PurePosixPath(normalized).parent.name
        user = user_from_path(relative)
        if not user:
            parts = normalized.split('/')
            if 'home' in parts and parts.index('home') + 1 < len(parts):
                user = parts[parts.index('home') + 1]
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        db.row_factory = sqlite3.Row
        try:
            rows = list(reader(db))
        except (sqlite3.Error, ValueError, TypeError, OverflowError) as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        finally:
            db.close()
        output.extend(tuple(row) + (profile, user, relative) for row in rows)
        sources.append(path)
    return output, '\n'.join(sources)


def visits(db):
    source = optional(db, 'moz_historyvisits', ('source',), 'v')
    for row in db.execute(f'''
            SELECT v.visit_date, v.id, v.place_id, p.url, p.title, v.visit_type,
                   v.from_visit, r.url AS referring_url, {source}
            FROM moz_historyvisits v LEFT JOIN moz_places p ON p.id=v.place_id
            LEFT JOIN moz_historyvisits rv ON rv.id=v.from_visit AND v.from_visit > 0
            LEFT JOIN moz_places r ON r.id=rv.place_id ORDER BY v.visit_date, v.id'''):
        yield (timestamp(row['visit_date']), row['id'], row['place_id'], row['url'],
               row['title'], row['visit_type'], _TRANSITIONS.get(row['visit_type'], 'Unknown'),
               row['source'], row['from_visit'], row['referring_url'])


def folder_path(items, parent):
    """Bounded parent walk: retain evidence of broken or cyclic hierarchies."""
    result, seen = [], set()
    while parent:
        if parent in seen:
            result.append(f'[cycle: {parent}]')
            break
        seen.add(parent)
        folder = items.get(parent)
        if folder is None:
            result.append(f'[missing: {parent}]')
            break
        result.append(folder['title'] or folder['guid'] or str(parent))
        parent = folder['parent']
    return ' / '.join(reversed(result))


def bookmarks(db):
    items = {row['id']: row for row in db.execute('SELECT * FROM moz_bookmarks')}
    urls = dict(db.execute('SELECT id, url FROM moz_places'))
    for row in sorted(items.values(), key=lambda r: r['id']):
        if row['type'] != 1:
            continue
        yield (timestamp(row['dateAdded']), timestamp(row['lastModified']), row['id'],
               row['guid'], row['title'], urls.get(row['fk']),
               folder_path(items, row['parent']), row['position'])


def downloads(db):
    """One record per annotated place, never multiply URL metadata by history visits."""
    if not columns(db, 'moz_annos') or not columns(db, 'moz_anno_attributes'):
        return
    grouped = {}
    for row in db.execute('''
            SELECT a.id, a.place_id, a.content, a.dateAdded, a.lastModified,
                   n.name, p.url FROM moz_annos a
            JOIN moz_anno_attributes n ON n.id=a.anno_attribute_id
            LEFT JOIN moz_places p ON p.id=a.place_id
            WHERE n.name IN ('downloads/destinationFileURI', 'downloads/metaData')
            ORDER BY a.lastModified, a.id'''):
        grouped.setdefault(row['place_id'], {})[row['name']] = row
    for place_id, entries in sorted(grouped.items()):
        target = entries.get('downloads/destinationFileURI')
        metadata = entries.get('downloads/metaData')
        base = metadata if metadata is not None else target
        raw = metadata['content'] if metadata is not None else ''
        parsed, status = {}, 'No metadata annotation'
        if metadata is not None:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError('metadata is not an object')
                status = 'Parsed'
            except (ValueError, TypeError):
                parsed, status = {}, 'Invalid metadata JSON'
        state = parsed.get('state')
        state_label = _STATES.get(state, 'Unknown') if isinstance(state, int) else ''
        yield (timestamp(parsed.get('endTime'), 1000), timestamp(base['dateAdded']),
               timestamp(base['lastModified']), place_id, base['url'],
               target['content'] if target is not None else '', state, state_label,
               parsed.get('fileSize'), parsed.get('deleted'), status, raw)


def cookies(db):
    version = db.execute('PRAGMA user_version').fetchone()[0]
    # Mozilla migration from schema 15 multiplies expiry by 1000; schema 16+ is ms.
    expiry_units = 1000 if version >= 16 else 1
    names = ('lastAccessed', 'creationTime', 'updateTime', 'expiry', 'id', 'host',
             'path', 'name', 'value', 'originAttributes', 'isSecure', 'isHttpOnly', 'sameSite')
    for row in db.execute(f'SELECT {optional(db, "moz_cookies", names)} '
                          'FROM moz_cookies ORDER BY lastAccessed, id'):
        yield (timestamp(row['lastAccessed']), timestamp(row['creationTime']),
               timestamp(row['updateTime']), timestamp(row['expiry'], expiry_units),
               *(row[name] for name in names[4:]))


def form_history(db):
    sources = {}
    if columns(db, 'moz_sources') and columns(db, 'moz_history_to_sources'):
        for row in db.execute('''SELECT h.history_id, s.source
                FROM moz_history_to_sources h JOIN moz_sources s ON s.id=h.source_id
                ORDER BY h.history_id, s.source'''):
            sources.setdefault(row[0], []).append(row[1])
    for row in db.execute('SELECT * FROM moz_formhistory ORDER BY lastUsed, id'):
        yield (timestamp(row['lastUsed']), timestamp(row['firstUsed']), row['id'],
               row['guid'], row['fieldname'], row['value'], row['timesUsed'],
               json.dumps(sources.get(row['id'], []), ensure_ascii=False))


def interactions(db):
    if not columns(db, 'moz_places_metadata'):
        return
    names = ('total_view_time', 'typing_time', 'key_presses', 'scrolling_time',
             'scrolling_distance', 'document_type')
    for row in db.execute(f'''
            SELECT m.created_at, m.updated_at, m.id, m.place_id, p.url, p.title,
                   r.url AS referring_url, {optional(db, 'moz_places_metadata', names, 'm')}
            FROM moz_places_metadata m LEFT JOIN moz_places p ON p.id=m.place_id
            LEFT JOIN moz_places r ON r.id=m.referrer_place_id ORDER BY m.created_at, m.id'''):
        yield (timestamp(row['created_at'], 1000), timestamp(row['updated_at'], 1000),
               row['id'], row['place_id'], row['url'], row['title'], row['referring_url'],
               *(row[name] for name in names))


def favicons(db):
    """One row per page-to-icon link, then one per icon that no link names."""
    link_expiry = 'l.expire_ms' if 'expire_ms' in columns(db, 'moz_icons_to_pages') else 'NULL'
    for row in db.execute(f'''SELECT i.expire_ms AS icon_expire, {link_expiry} AS link_expire,
            p.page_url, i.icon_url, i.width, i.root, i.flags, length(i.data) AS size, i.id
            FROM moz_icons_to_pages l JOIN moz_pages_w_icons p ON p.id=l.page_id
            JOIN moz_icons i ON i.id=l.icon_id ORDER BY p.page_url, i.width, i.id'''):
        yield (timestamp(row['icon_expire'], 1000), timestamp(row['link_expire'], 1000),
               row['page_url'], row['icon_url'], row['width'], row['root'], row['flags'],
               row['size'], row['id'])
    for row in db.execute('''SELECT i.expire_ms AS icon_expire, i.icon_url, i.width, i.root,
            i.flags, length(i.data) AS size, i.id FROM moz_icons i
            WHERE NOT EXISTS (SELECT 1 FROM moz_icons_to_pages l WHERE l.icon_id=i.id)
            ORDER BY i.icon_url, i.width, i.id'''):
        yield (timestamp(row['icon_expire'], 1000), '', '', row['icon_url'], row['width'],
               row['root'], row['flags'], row['size'], row['id'])


def snappy_raw_uncompress(data):
    """Raw Snappy (no framing), as google/snappy format_description.txt defines it.

    Raises ValueError on any malformed element, and unless the output is exactly
    the length the preamble declares.
    """
    data = bytes(data)
    size, shift, pos = 0, 0, 0
    while True:
        if pos >= len(data) or shift > 28:
            raise ValueError('bad Snappy length preamble')
        byte = data[pos]
        pos += 1
        size |= (byte & 0x7F) << shift
        if not byte & 0x80:
            break
        shift += 7
    out = bytearray()
    while pos < len(data):
        tag = data[pos]
        pos += 1
        kind = tag & 3
        if kind == 0:
            length = (tag >> 2) + 1
            if length > 60:
                extra = length - 60
                if pos + extra > len(data):
                    raise ValueError('truncated Snappy literal length')
                length = int.from_bytes(data[pos:pos + extra], 'little') + 1
                pos += extra
            if pos + length > len(data):
                raise ValueError('truncated Snappy literal')
            out += data[pos:pos + length]
            pos += length
            continue
        if kind == 1:
            if pos >= len(data):
                raise ValueError('truncated Snappy copy')
            length = ((tag >> 2) & 7) + 4
            offset = ((tag >> 5) << 8) | data[pos]
            pos += 1
        else:
            width = 2 if kind == 2 else 4
            if pos + width > len(data):
                raise ValueError('truncated Snappy copy')
            length = (tag >> 2) + 1
            offset = int.from_bytes(data[pos:pos + width], 'little')
            pos += width
        if offset == 0 or offset > len(out):
            raise ValueError('Snappy copy offset out of range')
        for _ in range(length):
            out.append(out[-offset])
    if len(out) != size:
        raise ValueError('Snappy output length differs from its preamble')
    return bytes(out)


def local_storage_value(value, conversion, compression):
    """A LocalStorage value as text, following Mozilla's LSValue conversion and compression types."""
    raw = bytes(value)
    if compression == 1:
        raw = snappy_raw_uncompress(raw)
    elif compression != 0:
        raise ValueError(f'unknown compression type {compression}')
    if conversion == 1:
        return raw.decode('utf-8')
    if conversion == 0:
        return raw.decode('utf-16-le', errors='replace')
    raise ValueError(f'unknown conversion type {conversion}')


def read_local_storage(context, label):
    """Rows from each profile's storage/default/<origin>/ls/data.sqlite."""
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name == 'data.sqlite'
             and PurePosixPath(str(p).replace('\\', '/')).parent.name == 'ls']
    paths, _ = unique_sources(context, found, sidecars=('-wal',), label=label)
    output, sources, failed, mismatched = [], [], 0, 0
    for path in paths:
        relative = context.get_relative_path(path)
        parts = str(relative).replace('\\', '/').split('/')
        # <profile>/storage/default/<origin>/ls/data.sqlite: count back from the store,
        # so a folder named storage higher up the path is not read as the profile.
        profile = parts[-6] if len(parts) >= 6 and parts[-5:-3] == ['storage', 'default'] else ''
        user = user_from_path(relative)
        if not user and 'home' in parts and parts.index('home') + 1 < len(parts):
            user = parts[parts.index('home') + 1]
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            origin = ''
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='database'").fetchone():
                found_origin = db.execute('SELECT origin FROM database LIMIT 1').fetchone()
                origin = found_origin[0] if found_origin else ''
            rows = db.execute('SELECT key, utf16_length, conversion_type, compression_type, value '
                              'FROM data ORDER BY key').fetchall()
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        finally:
            db.close()
        for key, utf16_length, conversion, compression, value in rows:
            try:
                text = local_storage_value(value, conversion, compression)
                if len(text.encode('utf-16-le')) // 2 != utf16_length:
                    mismatched += 1
            except (ValueError, TypeError, UnicodeDecodeError):
                text = ''
                failed += 1
            output.append((origin, key, text, utf16_length, conversion, compression,
                           len(value) if value is not None else '', profile, user, relative))
        sources.append(path)
    if failed:
        logfunc(f'{label}: {failed} value(s) could not be decoded and are left blank')
    if mismatched:
        logfunc(f'{label}: {mismatched} decoded value(s) differ in length from the stored UTF-16 length')
    return output, '\n'.join(sources)
