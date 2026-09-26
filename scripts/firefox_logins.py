"""Firefox saved login readers. Author: @AlexisBrignoni, Claude.

Firefox keeps saved logins in logins.json (written by storage-json.sys.mjs, with a copy in
logins-backup.json) and in logins.db, the application-services logins store with a local
table loginsL and a mirror table loginsM. This module reports each login's metadata and
never reads or decrypts the encrypted username and password. The artifact notes cite the
sources.
"""

import json
import sqlite3
from pathlib import PurePosixPath

from scripts.firefox import optional, timestamp
from scripts.ilapfuncs import logfunc, open_sqlite_db_readonly
from scripts.macos_plists import unique_sources, user_from_path

# SyncStatus in application-services components/logins/src/schema.rs.
_SYNC_STATUS = {0: 'Synced', 1: 'Changed', 2: 'New'}
_DB_COMMON = ('timeCreated', 'timeLastUsed', 'timePasswordChanged', 'timeLastBreachAlertDismissed',
              'timesUsed', 'origin', 'formActionOrigin', 'httpRealm', 'usernameField',
              'passwordField', 'guid')
_DB_TABLES = (('loginsL', 'logins.db local (loginsL)', ('local_modified', 'is_deleted', 'sync_status')),
              ('loginsM', 'logins.db mirror (loginsM)', ('server_modified', 'is_overridden')))


def _text(value):
    return '' if value is None else str(value)


def _sync_status(value):
    if value is None:
        return ''
    name = _SYNC_STATUS.get(value)
    return f'{value} ({name})' if name else f'{value} (as stored)'


def _row(record, store, extra):
    """Row values, less the file columns, from a mapping keyed on the logins.db names."""
    ms = 1000
    return (timestamp(record.get('timeCreated'), ms), timestamp(record.get('timeLastUsed'), ms),
            timestamp(record.get('timePasswordChanged'), ms),
            timestamp(record.get('timeLastBreachAlertDismissed'), ms),
            timestamp(extra.get('local_modified'), ms), timestamp(extra.get('server_modified'), ms),
            _text(record.get('timesUsed')), _text(record.get('origin')),
            _text(record.get('formActionOrigin')), _text(record.get('httpRealm')),
            _text(record.get('usernameField')), _text(record.get('passwordField')),
            _text(record.get('guid')), store, _text(extra.get('is_deleted')),
            _sync_status(extra.get('sync_status')), _text(extra.get('is_overridden')))


def json_rows(data, store):
    """Rows from a parsed logins.json, its field names mapped to the logins.db ones."""
    logins = data.get('logins') if isinstance(data, dict) else None
    for login in logins if isinstance(logins, list) else []:
        if not isinstance(login, dict):
            continue
        record = dict(login)
        record['origin'] = login.get('hostname')
        record['formActionOrigin'] = login.get('formSubmitURL')
        yield _row(record, store, {})


def db_rows(db, label, relative):
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table, store, extra_names in _DB_TABLES:
        if table not in tables:
            continue
        names = _DB_COMMON + extra_names
        try:
            rows = db.execute(f'SELECT {optional(db, table, names)} FROM "{table}" ORDER BY id').fetchall()
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {table} in {relative}: {exc}')
            continue
        for values in rows:
            record = dict(zip(names, values))
            yield _row(record, store, {name: record[name] for name in extra_names})


def read_saved_logins(context, label):
    """Rows from each profile's logins.json, logins-backup.json and logins.db."""
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name in ('logins.json', 'logins-backup.json',
                                                                  'logins.db')]
    paths, _ = unique_sources(context, found, sidecars=('-wal',), label=label)
    output, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        parts = str(relative).replace('\\', '/').split('/')
        name, profile = parts[-1], parts[-2] if len(parts) >= 2 else ''
        user = user_from_path(relative)
        if not user and 'home' in parts and parts.index('home') + 1 < len(parts):
            user = parts[parts.index('home') + 1]
        if name == 'logins.db':
            db = open_sqlite_db_readonly(path)
            if db is None:
                continue
            try:
                rows = list(db_rows(db, label, relative))
            except sqlite3.Error as exc:
                logfunc(f'{label}: could not read {relative}: {exc}')
                continue
            finally:
                db.close()
        else:
            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    rows = list(json_rows(json.load(handle), name))
            except (OSError, ValueError, UnicodeDecodeError) as exc:
                logfunc(f'{label}: {relative} was not read ({exc})')
                continue
        output.extend(row + (profile, user, relative) for row in rows)
        sources.append(path)
    return output, '\n'.join(sources)
