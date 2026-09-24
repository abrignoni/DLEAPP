"""Firefox SQLite readers. Author: @AlexisBrignoni, Codex.

Field definitions and validation boundaries: admin/docs/firefox-corpus-20260924.md.
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
