"""Read the TeleGuard Windows SQLite layout supplied with this contribution.

Stored values define the output. No client version range, transport protocol or
meaning of undocumented state codes is inferred.
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from scripts.ilapfuncs import logfunc, open_sqlite_db_readonly

DB_NAME = 'teleguard_database.db'
SIDECARS = ('-wal', '-shm', '-journal')
LANGUAGE_PREFERENCE = ('de', 'en')
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MIN_MILLISECONDS = Decimal('-62135596800000')
MAX_MILLISECONDS = Decimal('253402300799999.999')
MESSAGE_COLUMNS = ('id', 'chatId', 'sender', 'receiver', 'content', 'createDate',
                   'userTime', 'type', 'status', 'isEdited', 'metadata', 'parentId')


def readable_path(path):
    """Preserve the seeker spelling, including relative and extended paths."""
    return os.fspath(path)


def databases(context):
    """Unique main stores, preserving each source instance."""
    found, seen = [], set()
    for item in context.get_files_found():
        path = readable_path(item)
        key = os.path.normcase(os.path.abspath(path))
        if key in seen or not os.path.isfile(path):
            continue
        seen.add(key)
        if os.path.basename(path).casefold() == DB_NAME:
            relative = context.get_relative_path(path).replace('\\', '/')
            found.append((path, relative))
    return sorted(found, key=lambda entry: entry[1])


def quote_name(name):
    """Quote a SQLite identifier."""
    return '"' + name.replace('"', '""') + '"'


def table_names(db):
    """Declared tables compared case-insensitively."""
    return {row[0].casefold() for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}


def columns(db, table):
    """Declared columns, retaining their actual spelling."""
    return {row[1] for row in db.execute('PRAGMA table_info(' + quote_name(table) + ')')}


def open_db(path, label, required=('messages',)):
    """Open through the read-only helper and validate identity/content fields."""
    # The Windows SQLite helper adds an extended-length prefix. Resolve relative
    # staging paths before that prefix is added; keep the seeker's original
    # spelling in databases() for source attribution and portable baselines.
    db = open_sqlite_db_readonly(os.path.abspath(path))
    if db is None:
        logfunc(f'{label}: could not open the staged database')
        return None
    try:
        declared = table_names(db)
        missing = sorted(table for table in required if table.casefold() not in declared)
        if missing:
            logfunc(f'{label}: declares no {", ".join(missing)} table; not parsed')
            db.close()
            return None
        for table in required:
            needed = ('id', 'chatId', 'content') if table == 'messages' else ('serverId',)
            present = {column.casefold() for column in columns(db, table)}
            if any(column.casefold() not in present for column in needed):
                logfunc(f'{label}: {table} lacks required identity/content columns; not parsed')
                db.close()
                return None
    except sqlite3.Error as exc:
        logfunc(f'{label}: database schema could not be read: {exc}')
        db.close()
        return None
    return db


def select(db, table, wanted, order=''):
    """Read known columns; absent optional columns remain NULL."""
    present = {column.casefold(): column for column in columns(db, table)}
    if not present:
        return []
    names = ', '.join(quote_name(present[column.casefold()])
                      if column.casefold() in present else 'NULL AS ' + quote_name(column)
                      for column in wanted)
    rows = db.execute(f'SELECT {names} FROM {quote_name(table)} {order}')
    return [dict(zip(wanted, row)) for row in rows]


def message_rows(db):
    """Every stored message, including malformed metadata in its raw column."""
    rows = select(db, 'messages', MESSAGE_COLUMNS)
    for row in rows:
        row['metadata_json'] = decoded_json(row['metadata'])
    return rows


def local_account(db):
    """Resolve the local id/alias; account keys are never reported."""
    if 'service' not in table_names(db):
        logfunc('TeleGuard: no service table; message direction is unknown')
        return '', ''
    try:
        rows = db.execute('SELECT data FROM service WHERE id = ?', ('user',)).fetchmany(2)
    except sqlite3.Error as exc:
        logfunc(f'TeleGuard: account row could not be read: {exc}')
        return '', ''
    if len(rows) != 1:
        logfunc('TeleGuard: no unique account row in service; message direction is unknown')
        return '', ''
    account = decoded_json(rows[0][0])
    identifier, alias = account.get('serverId'), account.get('alias')
    if not isinstance(identifier, str) or not identifier:
        logfunc('TeleGuard: no usable local account id; message direction is unknown')
        return '', ''
    return identifier, alias if isinstance(alias, str) else ''


def contact_labels(db):
    """Aliases inside this store; no cross-profile lookup."""
    return {row['serverId']: row['alias'] for row in
            select(db, 'contacts', ('serverId', 'alias'))
            if row['serverId'] and row['alias']}


def contact_types(db):
    """Stored codes, without interpretation."""
    return {row['serverId']: row['type'] for row in
            select(db, 'contacts', ('serverId', 'type')) if row['serverId']}


def reference_counts(db):
    """Count chat/sender/receiver references inside this database only."""
    counts = {}
    for row in select(db, 'messages', ('chatId', 'sender', 'receiver')):
        for position, field in enumerate(('chatId', 'sender', 'receiver')):
            if row[field] is not None and row[field] != '':
                counts.setdefault(row[field], [0, 0, 0])[position] += 1
    return {key: tuple(value) for key, value in counts.items()}


def display_name(identifier, labels, local_id, local_alias):
    """Display name while leaving stored ids available separately."""
    if identifier is None or identifier == '':
        return ''
    if identifier == local_id:
        return local_alias or identifier
    return labels.get(identifier) or identifier


def direction(sender, local_id):
    """Direction is known only when sender and local account id are known."""
    if not sender or not local_id:
        return ''
    return 'Outgoing' if sender == local_id else 'Incoming'


def utc(value):
    """Known Unix milliseconds, preserving fractions and negative dates.

    Null/empty, booleans, non-finite and out-of-range inputs are blank. Zero is
    the Unix epoch; no undocumented zero-as-missing sentinel is assumed.
    """
    if value is None or value == '' or isinstance(value, bool):
        return ''
    try:
        milliseconds = Decimal(str(value))
        if not milliseconds.is_finite() or not MIN_MILLISECONDS <= milliseconds <= MAX_MILLISECONDS:
            raise ValueError('out-of-range milliseconds')
        return EPOCH + timedelta(microseconds=int(milliseconds * 1000))
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        logfunc('TeleGuard: an invalid timestamp was left blank; message row retained')
        return ''


def decoded_json(value):
    """Decode JSON objects only; rows keep original stored text separately."""
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError, UnicodeDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def localized_text(content, metadata):
    """Choose de/en/first text; Content (as stored) preserves the full map."""
    if not content or metadata.get('isLocalized') != 1:
        return content or ''
    variants = decoded_json(content)
    for language in LANGUAGE_PREFERENCE:
        value = variants.get(language)
        if isinstance(value, str) and value:
            return value
    return next((value for value in variants.values() if isinstance(value, str) and value), content)


def media_files(metadata):
    """mediaFiles objects ordered by usable order, then stored position."""
    entries = metadata.get('mediaFiles')
    if not isinstance(entries, list):
        return []

    def order(item):
        position, entry = item
        try:
            value = Decimal(str(entry.get('order')))
            if value.is_finite():
                return 0, value, position
        except (InvalidOperation, ValueError, TypeError):
            pass
        return 1, Decimal(0), position

    usable = [(position, entry) for position, entry in enumerate(entries)
              if isinstance(entry, dict)]
    return [entry for _, entry in sorted(usable, key=order)]


def attachment_entries(metadata):
    """mediaFiles references plus additional id-to-name files references."""
    result = [dict(entry, reference_field='mediaFiles') for entry in media_files(metadata)]
    names = {entry.get('name') for entry in result if isinstance(entry.get('name'), str)}
    files = metadata.get('files')
    if isinstance(files, dict):
        for identifier, name in files.items():
            if isinstance(name, str) and name and name not in names:
                result.append({'id': identifier, 'name': name,
                               'mediaType': metadata.get('mediaType'), 'reference_field': 'files'})
                names.add(name)
    return result


def attachment_names(entry):
    """Distinct stored filenames for one reference, preserving field order."""
    result, seen = [], set()
    for field in ('name', 'cacheName', 'thumbnailCacheName'):
        name = entry.get(field)
        if isinstance(name, str) and name and name.casefold() not in seen:
            result.append(name)
            seen.add(name.casefold())
    return result


def media_names(metadata):
    """Stored filenames, counting an alias only once per attachment reference."""
    return [name for entry in attachment_entries(metadata) for name in attachment_names(entry)]


def conversation_id(relative, chat_id):
    """The source instance participates in conversation identity."""
    return f'{relative} :: {chat_id}'


def contained(path, root):
    """Containment of staged paths, guarding separators, links and drives."""
    path, root = (os.path.normcase(os.path.realpath(item)) for item in (path, root))
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


def media_profile(database, stores):
    """Profile whose shared cache has exactly one staged main-store owner.

    Only the observed AppData/Roaming/TeleGuard location establishes a profile.
    A draft database is not a main store; another main-store copy in the same
    profile makes the shared cache unattributable, so it is left unassigned.
    """
    root = os.path.abspath(os.path.dirname(database))
    if tuple(part.casefold() for part in root.replace('\\', '/').split('/')[-3:]) != (
            'appdata', 'roaming', 'teleguard'):
        return None
    profile = os.path.dirname(os.path.dirname(os.path.dirname(root)))
    if sum(contained(path, profile) for path, _ in stores) != 1:
        return None
    return profile


def profile_media_path(path, profile):
    """Only the two observed media folders inside the same source profile."""
    if profile is None or not contained(path, profile):
        return False
    parts = tuple(part.casefold() for part in
                  os.path.relpath(path, profile).replace('\\', '/').split('/'))
    roots = (('appdata', 'local', 'temp', 'teleguard', 'images'),
             ('downloads', 'teleguard'))
    return any(len(parts) > len(root) and parts[:len(root)] == root for root in roots)


def media_index(context, database):
    """Name -> candidates in this store and its attributable profile media.

    Equal basenames remain ambiguous. A first-hit join is never made.
    """
    root = os.path.dirname(database)
    stores = databases(context)
    profile = media_profile(database, stores)
    other_roots = {os.path.dirname(path) for path, _ in stores
                   if os.path.normcase(os.path.dirname(path)) != os.path.normcase(root)}
    index, seen = {}, set()
    for item in context.get_files_found():
        path = readable_path(item)
        key = os.path.normcase(os.path.abspath(path))
        if key in seen or not os.path.isfile(path):
            continue
        if not contained(path, root) and not profile_media_path(path, profile):
            continue
        seen.add(key)
        if any(contained(other, root) and contained(path, other) for other in other_roots):
            continue
        base = os.path.basename(path).casefold()
        if (base == DB_NAME or any(base == DB_NAME + suffix for suffix in SIDECARS)
                or base.startswith('teleguard_temp.db') or base.endswith('.log')):
            continue
        index.setdefault(base, []).append(path)
    return {name: tuple(sorted(paths)) for name, paths in index.items()}


def resolve_media(index, *names):
    """Use the union of valid stored filenames; never prefer an original or thumb."""
    names = [value for value in names
             if isinstance(value, str) and value and value not in ('.', '..')
             and '/' not in value and '\\' not in value]
    if not names:
        return None, 'Invalid reference'
    candidates = sorted({path for value in names for path in index.get(value.casefold(), ())})
    if len(candidates) == 1:
        return candidates[0], 'Matched'
    return None, 'Ambiguous' if candidates else 'Missing'
