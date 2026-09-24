"""Locate, name and open the profile stores of Chromium-based browsers.

Used by the chromium* artifacts in scripts/artifacts. A store is one file in a
browser profile: History, Cookies, Login Data and the rest. This module works
out which browser, profile and user a staged file belongs to from its path,
opens SQLite stores read only, and converts Chromium's timestamps.

Where each browser keeps its user data folder:

* Google Chrome and Chromium: Chromium's docs/user_data_dir.md, lines 41 to 78,
  https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/docs/user_data_dir.md#L41-L78
* Microsoft Edge, Brave, Opera and Vivaldi: the folders Brave's importer reads,
  https://github.com/brave/brave-core/blob/c3c208b50d4198b432b0fd3956e8e19bd5fb5fbb/common/importer/chrome_importer_utils_win.cc#L59-L134
  https://github.com/brave/brave-core/blob/c3c208b50d4198b432b0fd3956e8e19bd5fb5fbb/common/importer/chrome_importer_utils_mac.mm#L33-L68
  https://github.com/brave/brave-core/blob/c3c208b50d4198b432b0fd3956e8e19bd5fb5fbb/common/importer/chrome_importer_utils_linux.cc#L45-L130

Each profile is a folder inside the user data folder (Default, Profile 2, ...).
When a browser's Local State lists no profile, Brave's importer reads the user
data folder itself as the profile, an empty profile id appended to the folder:
  https://github.com/brave/brave-core/blob/c3c208b50d4198b432b0fd3956e8e19bd5fb5fbb/common/importer/chrome_importer_utils.cc#L218-L224
  https://github.com/brave/brave-core/blob/c3c208b50d4198b432b0fd3956e8e19bd5fb5fbb/chromium_src/chrome/browser/importer/importer_list.cc#L49-L50
So a store directly inside a user data folder is read too, and its profile is
named after that folder.
"""

import datetime
import os
import sqlite3
from collections import namedtuple

from scripts.ilapfuncs import get_sqlite_db_path, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import canonical_relative, unique_sources

# (browser name, user data folder relative to the user's home folder)
BROWSER_ROOTS = (
    ('Google Chrome', ('AppData', 'Local', 'Google', 'Chrome', 'User Data')),
    ('Google Chrome', ('Library', 'Application Support', 'Google', 'Chrome')),
    ('Google Chrome', ('.config', 'google-chrome')),
    ('Chromium', ('AppData', 'Local', 'Chromium', 'User Data')),
    ('Chromium', ('Library', 'Application Support', 'Chromium')),
    ('Chromium', ('.config', 'chromium')),
    ('Microsoft Edge', ('AppData', 'Local', 'Microsoft', 'Edge', 'User Data')),
    ('Microsoft Edge', ('Library', 'Application Support', 'Microsoft Edge')),
    ('Microsoft Edge', ('.config', 'microsoft-edge')),
    ('Brave', ('AppData', 'Local', 'BraveSoftware', 'Brave-Browser', 'User Data')),
    ('Brave', ('Library', 'Application Support', 'BraveSoftware', 'Brave-Browser')),
    ('Brave', ('.config', 'BraveSoftware', 'Brave-Browser')),
    ('Vivaldi', ('AppData', 'Local', 'Vivaldi', 'User Data')),
    ('Vivaldi', ('Library', 'Application Support', 'Vivaldi')),
    ('Vivaldi', ('.config', 'vivaldi')),
    ('Opera', ('AppData', 'Roaming', 'Opera Software', 'Opera Stable')),
    ('Opera', ('Library', 'Application Support', 'com.operasoftware.Opera')),
    ('Opera', ('.config', 'opera')),
)

# The folders whose parent is a user's home folder.
_HOME_PARENTS = ('Users', 'home')

# Folders a profile keeps its own stores in. When one sits directly in a user
# data folder, the user data folder is read as the profile rather than the
# folder being read as a profile named Network or Extensions.
_PROFILE_SUBFOLDERS = ('Network', 'Extensions')

# A SQLite store's rollback journal or write-ahead log, which the store is read with.
_SIDECARS = ('-journal', '-wal')

# One store of one profile, located from its path inside the extraction.
#   path       the staged file this run reads
#   relative   that file's path inside the extraction, as reported
#   browser    the browser named by the user data folder
#   profile    the profile folder, relative to the user data folder
#   user       the home folder name the user data folder sits in, or ''
#   container  the profile folder's path inside the extraction; stores of one
#              profile share it and no two profiles do
#   name       the store's path inside the profile folder (History, Network/Cookies)
Store = namedtuple('Store', 'path relative browser profile user container name')


def locate(relative_path):
    """Browser, profile, user and store name of one path inside an extraction.

    Returns (browser, profile, user, container, name), or None when the path is
    not inside a known user data folder. A profile under Snapshots/<version>/
    keeps that prefix, so a snapshot never reads as the live profile.
    """
    parts = [part for part in str(relative_path).replace('\\', '/').split('/') if part]
    for browser, root in BROWSER_ROOTS:
        width = len(root)
        for start in range(len(parts) - width):
            if tuple(parts[start:start + width]) != root:
                continue
            home = parts[:start]
            rest = parts[start + width:]
            if len(home) >= 2 and home[-2] in _HOME_PARENTS:
                user = home[-1]
            elif home and home[-1] == 'root':
                user = 'root'
            else:
                user = ''
            if len(rest) >= 4 and rest[0] == 'Snapshots':
                profile_parts, name_parts = rest[:3], rest[3:]
            elif len(rest) >= 2 and rest[0] not in _PROFILE_SUBFOLDERS:
                profile_parts, name_parts = rest[:1], rest[1:]
            else:
                profile_parts, name_parts = [], rest
            container = '/'.join(parts[:start + width] + profile_parts)
            profile = '/'.join(profile_parts) or root[-1]
            return browser, profile, user, container, '/'.join(name_parts)
    return None


def profile_stores(context, names, label=''):
    """The staged files that are one of `names` in a browser profile.

    `names` holds store paths inside a profile folder ('History',
    'Network/Cookies'). Each staged file is returned once however many
    patterns matched it, directories are skipped, and the result is sorted by
    its path inside the extraction so the row order does not depend on the
    order the patterns were searched in.

    On a Mac logical extraction a profile can sit under Users/ and under
    System/Volumes/Data/Users/, where firmlinks expose one folder twice. A store
    whose copy under the second path is byte-identical, with any -journal or -wal
    beside it, is returned once (the run log counts it under `label`); copies that
    differ are both returned. `container` leaves out the System/Volumes/Data/
    prefix, so the two views of one profile share it.
    """
    stores = {}
    for found in context.get_files_found():
        path = str(found)
        if path in stores or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        located = locate(canonical_relative(relative))
        if located is None:
            continue
        browser, profile, user, container, name = located
        if name not in names:
            continue
        stores[path] = Store(path, relative, browser, profile, user, container, name)
    kept, _skipped = unique_sources(context, stores, sidecars=_SIDECARS, label=label)
    return sorted((stores[path] for path in kept), key=lambda store: store.relative)


def open_store(store, label):
    """Open a SQLite store read only. Returns a connection, or None when it cannot be read.

    A database left with a rollback journal that SQLite treats as hot cannot be
    opened through a read-only handle, because replaying the journal writes to
    the database. Such a database is read as found, with the journal ignored
    (SQLite's immutable open), and the log says so.
    """
    db = open_sqlite_db_readonly(store.path)
    if db is None:
        return None
    try:
        db.execute('SELECT count(*) FROM sqlite_master').fetchone()
        db.text_factory = _text
        return db
    except sqlite3.DatabaseError as ex:
        db.close()
        if not (isinstance(ex, sqlite3.OperationalError) and 'readonly' in str(ex).lower()):
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            return None
    try:
        db = sqlite3.connect(f'file:{get_sqlite_db_path(store.path)}?mode=ro&immutable=1', uri=True)
        db.execute('SELECT count(*) FROM sqlite_master').fetchone()
    except sqlite3.DatabaseError as ex:
        logfunc(f'{label}: could not read {store.relative} with its journal ignored: {ex}')
        return None
    logfunc(f'{label}: {store.relative} has a rollback journal SQLite treats as hot; '
            f'read the database as found, with the journal ignored')
    db.text_factory = _text
    return db


def _text(value):
    return value.decode('utf-8', 'replace')


def table_columns(db, table):
    """The column names of `table`, or an empty set when it does not exist."""
    return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}


def select_list(present, wanted, prefix=''):
    """A SELECT list naming each wanted column, with NULL for any the table lacks."""
    return ', '.join(f'{prefix}{column}' if column in present else f'NULL AS {column}'
                     for column in wanted)


_WINDOWS_EPOCH = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc)


def webkit_time(value):
    """A Chromium time, microseconds since 1601-01-01 UTC, as a datetime.

    Returns '' for a missing, zero, negative or out of range value.
    """
    try:
        microseconds = int(value)
    except (TypeError, ValueError):
        return ''
    if microseconds <= 0:
        return ''
    try:
        return _WINDOWS_EPOCH + datetime.timedelta(microseconds=microseconds)
    except OverflowError:
        return ''


def unix_time(value):
    """Seconds since 1970-01-01 UTC as a datetime; '' for missing, zero or out of range."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return ''
    if seconds <= 0:
        return ''
    try:
        return datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def enum_label(names, value):
    """'NAME (n)' for a stored enum value, 'unknown (n)' when the value is not in `names`."""
    if value is None or value == '':
        return ''
    try:
        number = int(value)
    except (TypeError, ValueError):
        return str(value)
    return f'{names.get(number, "unknown")} ({number})'


def row_tail(store):
    """The columns every Chromium row ends with: browser, profile, user and source file."""
    return (store.browser, store.profile, store.user, store.relative)
