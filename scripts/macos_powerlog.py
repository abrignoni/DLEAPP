"""Read macOS PowerLog databases: the live database and its gzip archives.

powerlogd keeps its live database at
/private/var/db/powerlog/Library/BatteryLife/CurrentPowerlog.PLSQL, beside its -wal and
-shm, and archives as Archives/powerlog_<date>_<id>.PLSQL.gz in the same folder.

Every table carries a 'timestamp' column, read here as Unix seconds. PowerLog's
PLStorageOperator_EventForward_TimeOffset table records, per entry, a 'system' value in
seconds; a stored time is corrected by adding the value of the entry in effect at it, which
is the latest entry at or before it, or the oldest entry for a time older than all of them.
That is the correction iLEAPP's PowerLog artifacts apply
(https://github.com/abrignoni/iLEAPP/blob/bb6942ccbb27ada88c256ed5b91e283ba84ca9f7/scripts/artifacts/powerlog.py#L1437-L1452),
with one difference: the entries are taken from every database in the same PowerLog folder,
live and archived, rather than from the one database the row is in. A database can hold
rows stored before its own first entry, and the folder's other databases can hold entries
for that period.

A column whose value is a list is stored in a side table named
<table>_Array_<column>, whose FK_ID holds the ID of the row the entry belongs to.
"""

import bisect
import contextlib
import gzip
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import get_sqlite_db_path

OFFSET_TABLE = 'PLStorageOperator_EventForward_TimeOffset'
_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SQLITE_MAGIC = b'SQLite format 3\x00'


def powerlog_paths(files_found):
    """The PowerLog databases among files_found, as sorted (path, is_archive) pairs.

    A live database ends .PLSQL and an archive .PLSQL.gz; sidecars and directories are
    not databases and are skipped."""
    found = set()
    for path in files_found:
        path = str(path)
        if os.path.isdir(path):
            continue
        name = os.path.basename(path)
        if name.endswith('.PLSQL'):
            found.add((path, False))
        elif name.endswith('.PLSQL.gz'):
            found.add((path, True))
    return sorted(found)


class PowerLogDatabase:
    """One PowerLog database, opened read-only, with its time offset entries loaded."""

    def __init__(self, source, open_path, immutable):
        self.source = source
        uri = f'file:{get_sqlite_db_path(open_path)}?mode=ro'
        if immutable:
            uri += '&immutable=1'
        self.connection = sqlite3.connect(uri, uri=True)
        self.own_offsets = []
        if {'timestamp', 'system'} <= set(self.columns(OFFSET_TABLE)):
            self.own_offsets = self.connection.execute(
                f'SELECT "timestamp", "system" FROM "{OFFSET_TABLE}" '
                'WHERE "timestamp" IS NOT NULL AND "system" IS NOT NULL').fetchall()
        self.use_offsets(self.own_offsets)

    def use_offsets(self, entries):
        """Correct times with these (timestamp, system) entries from now on."""
        entries = sorted(set(entries))
        self.offset_times = [stamp for stamp, _ in entries]
        self.offsets = [offset for _, offset in entries]

    def close(self):
        self.connection.close()

    def columns(self, table):
        """Column names of table, [] when the database has no such table."""
        return [row[1] for row in self.connection.execute(f'PRAGMA table_info("{table}")')]

    def rows(self, table, wanted):
        """Rows of table as dicts over the wanted columns, in stored time order.

        A wanted column this database's schema lacks is read as NULL, so every row has
        the same keys whatever the macOS release. [] when the table is absent."""
        present = set(self.columns(table))
        if not present:
            return []
        select = ', '.join(f'"{name}"' if name in present else f'NULL AS "{name}"'
                           for name in wanted)
        order = ', '.join(f'"{name}"' for name in ('timestamp', 'ID') if name in present)
        query = f'SELECT {select} FROM "{table}"' + (f' ORDER BY {order}' if order else '')
        return [dict(zip(wanted, row)) for row in self.connection.execute(query)]

    def side_values(self, table, column):
        """{row ID: [values in stored order]} from the <table>_Array_<column> side table,
        {} when the database has none."""
        side = f'{table}_Array_{column}'
        if not {'FK_ID', 'value'} <= set(self.columns(side)):
            return {}
        values = {}
        for parent, value in self.connection.execute(
                f'SELECT "FK_ID", "value" FROM "{side}" ORDER BY "ID"'):
            values.setdefault(parent, []).append(value)
        return values

    def corrected(self, raw):
        """(corrected UTC datetime, offset applied in seconds) for a stored time.

        (None, None) for a missing value or one at or before zero, which is not a clock
        reading. With no offset entries the time is returned uncorrected, offset None."""
        try:
            raw = float(raw)
        except (TypeError, ValueError):
            return None, None
        if raw <= 0:
            return None, None
        offset = None
        if self.offset_times:
            index = max(bisect.bisect_right(self.offset_times, raw) - 1, 0)
            offset = self.offsets[index]
        try:
            return _UNIX_EPOCH + timedelta(seconds=raw + (offset or 0)), offset
        except OverflowError:
            return None, None


@contextlib.contextmanager
def open_databases(files_found, log, describe):
    """Open every PowerLog database in files_found read-only and yield the list.

    A live database is opened where the seeker staged it, so SQLite reads the -wal and
    -shm staged beside it. An archive is decompressed into a temporary folder, opened as
    immutable because it has no sidecars, and removed with the folder on exit. Each
    database then corrects times with the offset entries of its whole folder (see
    share_offsets). log takes a message and describe turns a staged path into the path
    reported."""
    databases = []
    with tempfile.TemporaryDirectory(prefix='dleapp_powerlog_') as scratch:
        try:
            for index, (path, archive) in enumerate(powerlog_paths(files_found)):
                open_path = path
                try:
                    if archive:
                        open_path = os.path.join(scratch, f'{index}.PLSQL')
                        with gzip.open(path, 'rb') as source, open(open_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    with open(open_path, 'rb') as handle:
                        if handle.read(len(_SQLITE_MAGIC)) != _SQLITE_MAGIC:
                            log(f'PowerLog: {describe(path)} is not a SQLite database')
                            continue
                    databases.append(PowerLogDatabase(path, open_path, archive))
                except (OSError, EOFError, sqlite3.Error) as exc:
                    log(f'PowerLog: could not read {describe(path)}: {type(exc).__name__}')
            share_offsets(databases, log, describe)
            yield databases
        finally:
            for database in databases:
                database.close()


# The firmlinked Data view and the System/Volumes/Update/mnt1 view of private/var/.
_FOLDER_VIEWS = re.compile(r'/(?:System/Volumes/Update/mnt1/|System/Volumes/Data/)+private/var/')


def powerlog_folder(path):
    """The PowerLog folder a database belongs to: the folder holding it, or that folder's
    parent for a database in Archives or Quarantine, with the firmlinked
    System/Volumes/Data/private/var/ and System/Volumes/Update/mnt1/private/var/ read as
    private/var/, since a logical extraction of a Mac can carry the folder under those paths."""
    folder = os.path.dirname(str(path).replace('\\', '/'))
    if os.path.basename(folder) in ('Archives', 'Quarantine'):
        folder = os.path.dirname(folder)
    return _FOLDER_VIEWS.sub('/private/var/', folder)


def share_offsets(databases, log, describe):
    """Give every database the offset entries of all the databases in its PowerLog folder.

    Entries a folder's databases give different values for at one time are all kept, and
    the disagreement is logged."""
    folders = {}
    for database in databases:
        folders.setdefault(powerlog_folder(database.source), []).append(database)
    for members in folders.values():
        entries = {entry for database in members for entry in database.own_offsets}
        values = {}
        for stamp, offset in entries:
            values.setdefault(stamp, set()).add(offset)
        disagreeing = sum(1 for offsets in values.values() if len(offsets) > 1)
        if disagreeing:
            log(f'PowerLog: the databases beside {describe(members[0].source)} give '
                f'different offsets for {disagreeing} entry times; all are kept')
        for database in members:
            database.use_offsets(entries)


def merge_sources(records):
    """Collapse records that are identical apart from their source.

    records is an iterable of (values, source) with values a tuple. A record held by
    several sources is kept as many times as the one source holding it most often, so a
    repeat within one database survives while a copy in another does not; each kept
    record lists every source that held it. The result is [(values, [sources])] in
    first-seen order."""
    counts = {}
    for values, source in records:
        per_source = counts.setdefault(values, {})
        per_source[source] = per_source.get(source, 0) + 1
    merged = []
    for values, per_source in counts.items():
        merged.extend((values, list(per_source)) for _ in range(max(per_source.values())))
    return merged
