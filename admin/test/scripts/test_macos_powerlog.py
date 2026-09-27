"""Pin the PowerLog reading in scripts/macos_powerlog.py and scripts/artifacts/macosPowerLog.py.

Every database below is built by the test with the table layouts the artifacts read; no value
comes from a real device. Expected times are written out as literals, never computed with the
code under test.
"""
import fnmatch
import gzip
import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_powerlog as mpl  # pylint: disable=wrong-import-position
from scripts.artifacts import macosPowerLog as artifact  # pylint: disable=wrong-import-position

UTC = timezone.utc
FOLDER = 'private/var/db/powerlog/Library/BatteryLife'
POWER_STATE = 'PLSleepWakeAgent_EventForward_PowerState'
SCHEMA = (
    'CREATE TABLE PLStorageOperator_EventForward_TimeOffset (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, baseband REAL, kernel REAL, system REAL)',
    f'CREATE TABLE {POWER_STATE} (ID INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, '
    'timestampLogged REAL, Capabilities INTEGER, CurrentMachWakeTime INTEGER, '
    'DriverWakeReason INTEGER, Event INTEGER, KernelSleepDate REAL, Reason INTEGER, '
    'SleepTriggers TEXT, State INTEGER, UUID TEXT, WakeType INTEGER)',
    f'CREATE TABLE {POWER_STATE}_Array_WakeType (ID INTEGER PRIMARY KEY AUTOINCREMENT, '
    'FK_ID INTEGER, value TEXT)',
    f'CREATE TABLE {POWER_STATE}_Array_Reason (ID INTEGER PRIMARY KEY AUTOINCREMENT, '
    'FK_ID INTEGER, value TEXT)',
    f'CREATE TABLE {POWER_STATE}_Array_DriverWakeReason (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, FK_ID INTEGER, value INTEGER)',
    'CREATE TABLE PLSleepWakeAgent_EventForward_UserIdle (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, Idle INTEGER)',
    'CREATE TABLE PLApplicationAgent_EventForward_FrontmostApp (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, ASN INTEGER, ApplicationType INTEGER, BundleID TEXT)',
    'CREATE TABLE PLLocaleAgent_EventForward_TimeZone (ID INTEGER PRIMARY KEY AUTOINCREMENT, '
    'timestamp REAL, CountryCode TEXT, LocaleId TEXT, SecondsFromGMT INTEGER, '
    'TimeZoneIsInDST INTEGER, TimeZoneName TEXT, Trigger TEXT)',
    'CREATE TABLE PLPeripheralAgent_EventForward_ClamshellState (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, closed INTEGER)',
    'CREATE TABLE PLPeripheralAgent_EventForward_DeviceState (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, BusVersionOrSpeed INTEGER, DeviceName TEXT, DeviceType INTEGER, '
    'IsBuiltin INTEGER, NowConnected INTEGER, ProductID INTEGER, RegisterEntryID INTEGER, '
    'ThunderboltRevisionID INTEGER, VendorID INTEGER)',
    'CREATE TABLE PLAudioAgent_EventForward_AudioDevice (ID INTEGER PRIMARY KEY AUTOINCREMENT, '
    'timestamp REAL, timestampLogged REAL, DeviceID INTEGER, IsInput INTEGER, IsRunning INTEGER, '
    'SourceID INTEGER, TransType INTEGER, Volume REAL)',
    'CREATE TABLE PLApplicationAgent_EventForward_AppLifecycle (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, ASN INTEGER, BundleID TEXT, Event INTEGER, PID INTEGER, '
    'ParentASN INTEGER)',
    # The older layout: no ExtensionName, BTCompanionIn or BTCompanionOut column.
    'CREATE TABLE PLProcessNetworkAgent_EventInterval_UsageDiff (ID INTEGER PRIMARY KEY '
    'AUTOINCREMENT, timestamp REAL, BundleName TEXT, CellIn INTEGER, CellOut INTEGER, '
    'ProcessName TEXT, WifiIn INTEGER, WifiOut INTEGER, WiredIn INTEGER, WiredOut INTEGER, '
    'timestampEnd REAL)',
    'CREATE TABLE PLDisplayAgent_Aggregate_ScreenOn (ID INTEGER PRIMARY KEY AUTOINCREMENT, '
    'timestamp REAL, timeInterval REAL, ScreenOn INTEGER)',
)
MIDNIGHT = 1767225600.0          # 2026-01-01 00:00:00 UTC


def fill(con, offsets=(), states=(), arrays=(), idle=(), frontmost=(), zones=(), lids=(),
         devices=(), audio=(), lifecycle=(), network=(), screen=(), schema=SCHEMA):
    for statement in schema:
        con.execute(statement)
    con.executemany('INSERT INTO PLStorageOperator_EventForward_TimeOffset '
                    '(timestamp, system) VALUES (?, ?)', offsets)
    con.executemany(f'INSERT INTO {POWER_STATE} (ID, timestamp, timestampLogged, State, Event, '
                    'SleepTriggers, Capabilities, UUID, WakeType, Reason, DriverWakeReason, '
                    'CurrentMachWakeTime, KernelSleepDate) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 12345, 1767000000.0)', states)
    for column, parent, value in arrays:
        con.execute(f'INSERT INTO {POWER_STATE}_Array_{column} (FK_ID, value) VALUES (?, ?)',
                    (parent, value))
    con.executemany('INSERT INTO PLSleepWakeAgent_EventForward_UserIdle (timestamp, Idle) '
                    'VALUES (?, ?)', idle)
    con.executemany('INSERT INTO PLApplicationAgent_EventForward_FrontmostApp '
                    '(timestamp, ASN, ApplicationType, BundleID) VALUES (?, ?, ?, ?)', frontmost)
    con.executemany('INSERT INTO PLLocaleAgent_EventForward_TimeZone (timestamp, CountryCode, '
                    'LocaleId, SecondsFromGMT, TimeZoneIsInDST, TimeZoneName, Trigger) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)', zones)
    con.executemany('INSERT INTO PLPeripheralAgent_EventForward_ClamshellState (timestamp, closed) '
                    'VALUES (?, ?)', lids)
    con.executemany('INSERT INTO PLPeripheralAgent_EventForward_DeviceState (timestamp, DeviceName, '
                    'NowConnected, IsBuiltin, DeviceType, VendorID, ProductID, RegisterEntryID, '
                    'BusVersionOrSpeed, ThunderboltRevisionID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)',
                    devices)
    con.executemany('INSERT INTO PLAudioAgent_EventForward_AudioDevice (timestamp, timestampLogged, '
                    'DeviceID, IsInput, IsRunning, SourceID, TransType, Volume) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', audio)
    con.executemany('INSERT INTO PLApplicationAgent_EventForward_AppLifecycle (timestamp, BundleID, '
                    'Event, PID, ASN, ParentASN) VALUES (?, ?, ?, ?, ?, ?)', lifecycle)
    con.executemany('INSERT INTO PLProcessNetworkAgent_EventInterval_UsageDiff (timestamp, '
                    'timestampEnd, BundleName, ProcessName, WifiIn, WifiOut, WiredIn, WiredOut, CellIn, '
                    'CellOut) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', network)
    con.executemany('INSERT INTO PLDisplayAgent_Aggregate_ScreenOn (timestamp, timeInterval, ScreenOn) '
                    'VALUES (?, ?, ?)', screen)
    con.commit()


def write_archive(path, **tables):
    """A database written in rollback-journal mode and gzipped to path."""
    with tempfile.TemporaryDirectory() as scratch:
        plain = os.path.join(scratch, 'a.PLSQL')
        con = sqlite3.connect(plain)
        fill(con, **tables)
        con.close()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(plain, 'rb') as source, gzip.open(path, 'wb') as target:
            shutil.copyfileobj(source, target)


def write_live(path, **tables):
    """A WAL-mode database copied, with its -wal and -shm, while its writer still holds the
    WAL open and uncheckpointed, so every row is in the copied -wal and not in the main file."""
    with tempfile.TemporaryDirectory() as scratch:
        original = os.path.join(scratch, 'CurrentPowerlog.PLSQL')
        con = sqlite3.connect(original)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA wal_autocheckpoint=0')
        fill(con, **tables)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for suffix in ('', '-wal', '-shm'):
            shutil.copyfile(original + suffix, path + suffix)
        con.close()


class Context:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


def walk(root):
    return sorted(os.path.join(folder, name) for folder, _, names in os.walk(root)
                  for name in names)


class CorrectedTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.scratch)

    def database(self, offsets):
        path = os.path.join(self.scratch, f'{len(os.listdir(self.scratch))}.PLSQL')
        con = sqlite3.connect(path)
        fill(con, offsets=offsets)
        con.close()
        database = mpl.PowerLogDatabase(path, path, immutable=True)
        self.addCleanup(database.close)
        return database

    def test_entry_at_or_before_the_time_applies(self):
        database = self.database([(MIDNIGHT, 2.0), (MIDNIGHT + 74400, -5.5)])
        self.assertEqual(database.corrected(MIDNIGHT + 14400.5),
                         (datetime(2026, 1, 1, 4, 0, 2, 500000, tzinfo=UTC), 2.0))
        self.assertEqual(database.corrected(MIDNIGHT + 74400),
                         (datetime(2026, 1, 1, 20, 39, 54, 500000, tzinfo=UTC), -5.5))
        self.assertEqual(database.corrected(MIDNIGHT + 84400.25),
                         (datetime(2026, 1, 1, 23, 26, 34, 750000, tzinfo=UTC), -5.5))

    def test_a_time_before_every_entry_takes_the_oldest(self):
        database = self.database([(MIDNIGHT, 2.0), (MIDNIGHT + 74400, -5.5)])
        self.assertEqual(database.corrected(MIDNIGHT - 5600),
                         (datetime(2025, 12, 31, 22, 26, 42, tzinfo=UTC), 2.0))

    def test_no_entries_leaves_the_time_uncorrected(self):
        database = self.database([])
        self.assertEqual(database.corrected(MIDNIGHT + 4400),
                         (datetime(2026, 1, 1, 1, 13, 20, tzinfo=UTC), None))

    def test_values_that_are_not_clock_readings(self):
        database = self.database([(MIDNIGHT, 2.0)])
        for raw in (None, 0, 0.0, -0.000778, 'text'):
            self.assertEqual(database.corrected(raw), (None, None), raw)

    def test_entries_with_a_missing_value_are_ignored(self):
        database = self.database([(MIDNIGHT, None), (None, 7.0), (MIDNIGHT + 10, 1.0)])
        self.assertEqual((database.offset_times, database.offsets), ([MIDNIGHT + 10], [1.0]))


class ReaderTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.scratch)

    def test_database_paths(self):
        folder = os.path.join(self.scratch, FOLDER)
        os.makedirs(os.path.join(folder, 'Archives'))
        names = ['CurrentPowerlog.PLSQL', 'CurrentPowerlog.PLSQL-wal', 'CurrentPowerlog.PLSQL-shm',
                 'Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz', 'notes.txt']
        for name in names:
            pathlib.Path(folder, name).write_bytes(b'')
        # A directory whose name ends like a database is not one.
        os.makedirs(os.path.join(folder, 'Quarantine', 'folder.PLSQL'))
        found = [os.path.join(folder, name) for name in names] + [
            os.path.join(folder, 'Archives'), os.path.join(folder, 'Quarantine', 'folder.PLSQL')]
        self.assertEqual(mpl.powerlog_paths(found),
                         [(os.path.join(folder, 'Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz'), True),
                          (os.path.join(folder, 'CurrentPowerlog.PLSQL'), False)])

    def test_rows_read_absent_columns_as_null_and_absent_tables_as_empty(self):
        path = os.path.join(self.scratch, 'x.PLSQL')
        con = sqlite3.connect(path)
        con.execute('CREATE TABLE PLSleepWakeAgent_EventForward_UserIdle '
                    '(ID INTEGER PRIMARY KEY, timestamp REAL)')
        con.executemany('INSERT INTO PLSleepWakeAgent_EventForward_UserIdle VALUES (?, ?)',
                        [(2, 20.0), (1, 30.0), (3, 20.0)])
        con.commit()
        con.close()
        database = mpl.PowerLogDatabase(path, path, immutable=True)
        self.addCleanup(database.close)
        self.assertEqual(database.rows('PLSleepWakeAgent_EventForward_UserIdle',
                                       ('ID', 'timestamp', 'Idle')),
                         [{'ID': 2, 'timestamp': 20.0, 'Idle': None},
                          {'ID': 3, 'timestamp': 20.0, 'Idle': None},
                          {'ID': 1, 'timestamp': 30.0, 'Idle': None}])
        self.assertEqual(database.rows('PLLocaleAgent_EventForward_TimeZone', ('ID',)), [])
        self.assertEqual(database.side_values(POWER_STATE, 'WakeType'), {})

    def test_side_values_group_by_row_in_stored_order(self):
        path = os.path.join(self.scratch, 'y.PLSQL')
        con = sqlite3.connect(path)
        fill(con, arrays=[('DriverWakeReason', 7, 'b'), ('DriverWakeReason', 8, 'x'),
                          ('DriverWakeReason', 7, 'a')])
        con.close()
        database = mpl.PowerLogDatabase(path, path, immutable=True)
        self.addCleanup(database.close)
        self.assertEqual(database.side_values(POWER_STATE, 'DriverWakeReason'),
                         {7: ['b', 'a'], 8: ['x']})

    def test_offset_display(self):
        self.assertEqual(artifact._seconds(1 / 3), 0.333)  # pylint: disable=protected-access
        self.assertEqual(artifact._seconds(-5942080.88399999), -5942080.884)  # pylint: disable=protected-access
        self.assertEqual(artifact._seconds(None), '')  # pylint: disable=protected-access

    def test_hex_and_four_characters(self):
        # pylint: disable=protected-access
        self.assertEqual(artifact._hex(1452), '0x05AC')
        self.assertEqual(artifact._hex(1970170734), '0x756E6B6E')
        self.assertEqual(artifact._hex(0), '0x0000')
        self.assertEqual((artifact._hex(None), artifact._hex(-1)), ('', -1))
        self.assertEqual(artifact._four_characters(1651274862), 'bltn')
        self.assertEqual(artifact._four_characters(1970496032), 'usb ')
        self.assertEqual(artifact._four_characters(1768778083), 'imic')
        # A code whose bytes are not all printable, or a value that is not a 32-bit
        # integer, is shown as stored.
        self.assertEqual(artifact._four_characters(0x626C7400), 0x626C7400)
        self.assertEqual(artifact._four_characters(5), 5)
        self.assertEqual(artifact._four_characters(1 << 32), 1 << 32)
        self.assertEqual(artifact._four_characters(-1), -1)
        self.assertEqual(artifact._four_characters(None), '')
        self.assertEqual(artifact._four_characters('bltn'), 'bltn')

    def test_merge_sources(self):
        merged = mpl.merge_sources([
            (('a', 1), 'archive'), (('b', 2), 'archive'), (('a', 1), 'live'),
            (('b', 2), 'archive'), (('b', 2), 'live'), (('c', 3), 'live')])
        self.assertEqual(merged, [(('a', 1), ['archive', 'live']),
                                  (('b', 2), ['archive', 'live']),
                                  (('b', 2), ['archive', 'live']),
                                  (('c', 3), ['live'])])


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        # Keep the reader's temporary folder inside this test's own folder, so the test
        # never touches the system temporary directory and can see what is left behind.
        self.temp = os.path.join(self.root, 'temp')
        os.mkdir(self.temp)
        patcher = patch.object(tempfile, 'tempdir', self.temp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.folder = os.path.join(self.root, 'image', FOLDER)
        self.archive = os.path.join(self.folder, 'Archives', 'powerlog_2026-01-01_0A1B2C3D.PLSQL.gz')
        self.live = os.path.join(self.folder, 'CurrentPowerlog.PLSQL')

    def files(self):
        return walk(os.path.join(self.root, 'image'))

    def run_artifact(self, function):
        return function.__wrapped__(Context(os.path.join(self.root, 'image'), self.files()))

    def test_sleep_and_wake(self):
        offsets = [(MIDNIGHT, 2.0)]
        carried = (2, MIDNIGHT + 14400.5, MIDNIGHT + 14460.5, 2, 5, None, 31, 'U1', 1, 1, 1)
        write_archive(self.archive, offsets=offsets, states=[
            (1, MIDNIGHT + 4400, MIDNIGHT + 4400, 1, 1, 'Idle Sleep', None, 'U1', None, None, None),
            carried,
            (3, MIDNIGHT - 5600, MIDNIGHT - 5600, 5, 6, None, 25, 'U0', None, None, None)],
            arrays=[('WakeType', 2, 'HID Activity'), ('Reason', 2, 'smc.sysState.Wake lid'),
                    ('DriverWakeReason', 2, 'smc.sysState.Wake'), ('DriverWakeReason', 2, 'lid'),
                    ('WakeType', 99, 'Orphan')])
        write_live(self.live, offsets=offsets + [(MIDNIGHT + 74400, -5.5)], states=[
            (10,) + carried[1:],
            (11, MIDNIGHT + 84400.25, MIDNIGHT + 84400.25, 5, 6, None, 25, 'U2', None, None, None),
            (12, -0.000778, MIDNIGHT + 84401, -1, 4, None, None, 'U2', None, None, None)],
            arrays=[('WakeType', 10, 'HID Activity'), ('Reason', 10, 'smc.sysState.Wake lid'),
                    ('DriverWakeReason', 10, 'smc.sysState.Wake'), ('DriverWakeReason', 10, 'lid')])
        headers, rows, source = self.run_artifact(artifact.macosPowerLogSleepWake)
        archive = FOLDER + '/Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz'
        live = FOLDER + '/CurrentPowerlog.PLSQL'
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Logged Time (UTC)', 'State (as stored)', 'Event (as stored)',
                          'Wake Type', 'Wake Reason', 'Driver Wake Reason', 'Sleep Triggers',
                          'Capabilities (as stored)', 'UUID', 'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2025, 12, 31, 22, 26, 42, tzinfo=UTC), datetime(2025, 12, 31, 22, 26, 42, tzinfo=UTC),
             5, 6, '', '', '', '', 25, 'U0', 2.0, archive),
            (datetime(2026, 1, 1, 1, 13, 22, tzinfo=UTC), datetime(2026, 1, 1, 1, 13, 22, tzinfo=UTC),
             1, 1, '', '', '', 'Idle Sleep', '', 'U1', 2.0, archive),
            (datetime(2026, 1, 1, 4, 0, 2, 500000, tzinfo=UTC), datetime(2026, 1, 1, 4, 1, 2, 500000, tzinfo=UTC),
             2, 5, 'HID Activity', 'smc.sysState.Wake lid', 'smc.sysState.Wake, lid', '', 31, 'U1', 2.0,
             archive + '\n' + live),
            (datetime(2026, 1, 1, 23, 26, 34, 750000, tzinfo=UTC), datetime(2026, 1, 1, 23, 26, 34, 750000, tzinfo=UTC),
             5, 6, '', '', '', '', 25, 'U2', -5.5, live),
            ('', datetime(2026, 1, 1, 23, 26, 35, 500000, tzinfo=UTC),
             -1, 4, '', '', '', '', '', 'U2', '', live)])
        self.assertEqual(source.split('\n'), [os.path.join(self.root, 'image', archive),
                                              os.path.join(self.root, 'image', live)])
        self.assertEqual([m for m in self.logged if 'side table' in m],
                         [f'PowerLog (macOS): 1 side table entries in {archive} name a '
                          f'{POWER_STATE} row that database does not hold; not reported'])
        self.assertEqual(os.listdir(self.temp), [])

    def test_offsets_are_shared_within_a_folder_and_not_across_folders(self):
        # The archive has no offset entries of its own, so the live database's apply to it;
        # the firmlinked System/Volumes/Data copy of the folder is the same folder; a folder
        # elsewhere keeps its own entries.
        write_archive(self.archive, offsets=[], idle=[(MIDNIGHT + 60, 1)])
        write_live(self.live, offsets=[(MIDNIGHT, 2.0)], idle=[(MIDNIGHT + 60, 1), (MIDNIGHT + 120, 0)])
        firmlinked = os.path.join(self.root, 'image', 'System/Volumes/Data', FOLDER, 'CurrentPowerlog.PLSQL')
        write_live(firmlinked, offsets=[(MIDNIGHT, 2.0)], idle=[(MIDNIGHT + 120, 0)])
        elsewhere = os.path.join(self.root, 'image', 'Old Mac', FOLDER, 'CurrentPowerlog.PLSQL')
        write_live(elsewhere, offsets=[(MIDNIGHT, 7.0)], idle=[(MIDNIGHT + 60, 1)])
        _, rows, _ = self.run_artifact(artifact.macosPowerLogUserIdle)
        archive = FOLDER + '/Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz'
        live = FOLDER + '/CurrentPowerlog.PLSQL'
        self.assertEqual(rows, [
            (datetime(2026, 1, 1, 0, 1, 2, tzinfo=UTC), 1, 2.0, archive + '\n' + live),
            (datetime(2026, 1, 1, 0, 1, 7, tzinfo=UTC), 1, 7.0, 'Old Mac/' + live),
            (datetime(2026, 1, 1, 0, 2, 2, tzinfo=UTC), 0, 2.0, 'System/Volumes/Data/' + live + '\n' + live)])

    def test_folder_of_a_database(self):
        self.assertEqual(mpl.powerlog_folder('/x/System/Volumes/Data/private/var/db/powerlog/Library/'
                                             'BatteryLife/Archives/powerlog_a.PLSQL.gz'),
                         '/x/private/var/db/powerlog/Library/BatteryLife')
        self.assertEqual(mpl.powerlog_folder('C:\\case\\private\\var\\db\\powerlog\\Library\\BatteryLife\\'
                                             'Quarantine\\bad.PLSQL'),
                         'C:/case/private/var/db/powerlog/Library/BatteryLife')

    def test_disagreeing_offsets_are_logged(self):
        write_archive(self.archive, offsets=[(MIDNIGHT, 3.0)], idle=[(MIDNIGHT + 60, 1)])
        write_live(self.live, offsets=[(MIDNIGHT, 2.0)], idle=[])
        _, rows, _ = self.run_artifact(artifact.macosPowerLogUserIdle)
        # Both entries are kept, and the one sorting last at an equal time applies.
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 1, 3, tzinfo=UTC), 1, 3.0,
                                 FOLDER + '/Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz')])
        self.assertEqual([m for m in self.logged if 'different offsets' in m],
                         [f'PowerLog: the databases beside {FOLDER}/Archives/powerlog_2026-01-01_0A1B2C3D.PLSQL.gz '
                          'give different offsets for 1 entry times; all are kept'])

    def test_frontmost_app_and_time_zone(self):
        write_live(self.live, offsets=[(MIDNIGHT, -1.0)],
                   frontmost=[(MIDNIGHT + 30, 7, 1, 'com.example.editor'), (MIDNIGHT + 10, 9, 3, None)],
                   zones=[(MIDNIGHT + 5, 'US', 'en_US', -18000, 0, 'America/New_York', 'powerlog')])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogFrontmostApp)
        live = FOLDER + '/CurrentPowerlog.PLSQL'
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Bundle ID', 'Application Type (as stored)', 'ASN (as stored)',
                          'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 0, 9, tzinfo=UTC), '', 3, 9, -1.0, live),
                                (datetime(2026, 1, 1, 0, 0, 29, tzinfo=UTC), 'com.example.editor', 1, 7, -1.0, live)])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogTimeZone)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Time Zone Name', 'Seconds From GMT', 'Time Zone Is In DST (as stored)',
                          'Country Code', 'Locale ID', 'Trigger', 'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 0, 4, tzinfo=UTC), 'America/New_York', -18000, 0,
                                 'US', 'en_US', 'powerlog', -1.0, live)])

    def test_lid_peripherals_and_audio_devices(self):
        write_live(self.live, offsets=[(MIDNIGHT, 2.0)],
                   lids=[(MIDNIGHT + 20, 1), (MIDNIGHT + 10, 0)],
                   devices=[(MIDNIGHT + 30, 'Headset', 1, 1, 1, 1452, 1060, 4294968617, 2),
                            (MIDNIGHT + 40, None, 0, 0, 1, 0, 0, 4294968617, 0)],
                   audio=[(MIDNIGHT + 50, MIDNIGHT + 55, 93, 0, 0, 1769173099, 1651274862, 0.5),
                          (MIDNIGHT + 60, MIDNIGHT + 60, 100, 1, 1, 1768778083, 1651275109, 0.0)])
        live = FOLDER + '/CurrentPowerlog.PLSQL'
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogLid)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Closed (as stored)', 'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 0, 12, tzinfo=UTC), 0, 2.0, live),
                                (datetime(2026, 1, 1, 0, 0, 22, tzinfo=UTC), 1, 2.0, live)])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogPeripherals)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Device Name', 'Now Connected (as stored)', 'Is Builtin (as stored)',
                          'Device Type (as stored)', 'Vendor ID', 'Vendor ID (hex)', 'Product ID',
                          'Product ID (hex)', 'Register Entry ID', 'Bus Version Or Speed (as stored)',
                          'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2026, 1, 1, 0, 0, 32, tzinfo=UTC), 'Headset', 1, 1, 1, 1452, '0x05AC', 1060, '0x0424',
             4294968617, 2, 2.0, live),
            (datetime(2026, 1, 1, 0, 0, 42, tzinfo=UTC), '', 0, 0, 1, 0, '0x0000', 0, '0x0000',
             4294968617, 0, 2.0, live)])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogAudioDevices)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Logged Time (UTC)', 'Device ID (as stored)', 'Is Input (as stored)',
                          'Is Running (as stored)', 'Source ID', 'Transport Type', 'Volume',
                          'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [
            (datetime(2026, 1, 1, 0, 0, 52, tzinfo=UTC), datetime(2026, 1, 1, 0, 0, 57, tzinfo=UTC),
             93, 0, 0, 'ispk', 'bltn', 0.5, 2.0, live),
            (datetime(2026, 1, 1, 0, 1, 2, tzinfo=UTC), datetime(2026, 1, 1, 0, 1, 2, tzinfo=UTC),
             100, 1, 1, 'imic', 'blue', 0.0, 2.0, live)])

    def test_app_lifecycle_network_and_screen_on(self):
        write_live(self.live, offsets=[(MIDNIGHT, 2.0), (MIDNIGHT + 1000, -3.0)],
                   lifecycle=[(MIDNIGHT + 10, 'com.example.editor', 1, 501, 7001, 0),
                              (MIDNIGHT + 20, 'com.example.editor', 2, 501, 7001, 0)],
                   network=[(MIDNIGHT + 100, MIDNIGHT + 1900, 'com.example.mail', 'Mail', 1200, 300, 0, 0, 0, 0)],
                   screen=[(MIDNIGHT + 3600, 3600.0, 1800)])
        live = FOLDER + '/CurrentPowerlog.PLSQL'
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogAppLifecycle)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Bundle ID', 'Event (as stored)', 'PID', 'ASN (as stored)',
                          'Parent ASN (as stored)', 'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 0, 12, tzinfo=UTC), 'com.example.editor', 1, 501, 7001, 0, 2.0, live),
                                (datetime(2026, 1, 1, 0, 0, 22, tzinfo=UTC), 'com.example.editor', 2, 501, 7001, 0, 2.0, live)])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogProcessNetwork)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Start Time (UTC)', 'End Time (UTC)', 'Bundle Name', 'Process Name', 'Extension Name',
                          'Wifi In', 'Wifi Out', 'Wired In', 'Wired Out', 'Cell In', 'Cell Out', 'BT Companion In',
                          'BT Companion Out', 'Time Offset (seconds)', 'Source File'])
        # The end falls after the second offset entry, so it is corrected with that one.
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 1, 42, tzinfo=UTC), datetime(2026, 1, 1, 0, 31, 37, tzinfo=UTC),
                                 'com.example.mail', 'Mail', '', 1200, 300, 0, 0, 0, 0, '', '', 2.0, live)])
        headers, rows, _ = self.run_artifact(artifact.macosPowerLogScreenOn)
        self.assertEqual([h if isinstance(h, str) else h[0] for h in headers],
                         ['Time (UTC)', 'Time Interval (as stored)', 'Screen On (as stored)',
                          'Time Offset (seconds)', 'Source File'])
        self.assertEqual(rows, [(datetime(2026, 1, 1, 0, 59, 57, tzinfo=UTC), 3600.0, 1800, -3.0, live)])

    def test_unreadable_files_are_logged_and_the_rest_read(self):
        write_live(self.live, offsets=[], idle=[(MIDNIGHT, 1)])
        os.makedirs(os.path.join(self.folder, 'Archives'))
        pathlib.Path(self.folder, 'Archives', 'powerlog_2026-01-02_00000000.PLSQL.gz').write_bytes(
            b'\x1f\x8b not really gzip')
        pathlib.Path(self.folder, 'Quarantine').mkdir()
        pathlib.Path(self.folder, 'Quarantine', 'bad.PLSQL').write_bytes(b'not a database at all')
        _, rows, source = self.run_artifact(artifact.macosPowerLogUserIdle)
        self.assertEqual(rows, [(datetime(2026, 1, 1, tzinfo=UTC), 1, '', FOLDER + '/CurrentPowerlog.PLSQL')])
        self.assertEqual(source, self.live)
        self.assertEqual(sorted(m for m in self.logged if m.startswith('PowerLog:')), [
            f'PowerLog: could not read {FOLDER}/Archives/powerlog_2026-01-02_00000000.PLSQL.gz: BadGzipFile',
            f'PowerLog: {FOLDER}/Quarantine/bad.PLSQL is not a SQLite database'])
        self.assertEqual(os.listdir(self.temp), [])

    def test_every_connection_is_closed(self):
        # On Windows an open database keeps the temporary folder from being removed, so
        # every connection the reader opened must be closed when the artifact returns.
        write_archive(self.archive, offsets=[(MIDNIGHT, 2.0)], idle=[(MIDNIGHT + 60, 1)])
        write_live(self.live, offsets=[(MIDNIGHT, 2.0)], idle=[(MIDNIGHT + 120, 0)])
        opened = []
        real_connect = sqlite3.connect

        def recording_connect(*args, **kwargs):
            connection = real_connect(*args, **kwargs)
            opened.append(connection)
            return connection

        with patch.object(mpl.sqlite3, 'connect', recording_connect):
            _, rows, _ = self.run_artifact(artifact.macosPowerLogUserIdle)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(opened), 2)
        for connection in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute('SELECT 1')

    def test_declared_paths(self):
        for key, info in artifact.__artifacts_v2__.items():
            patterns = info['paths']
            for path in ('Macintosh HD - Data/private/var/db/powerlog/Library/BatteryLife/CurrentPowerlog.PLSQL',
                         'root/private/var/db/powerlog/Library/BatteryLife/Archives/powerlog_2021-02-15_36902C4F.PLSQL.gz'):
                self.assertTrue(any(fnmatch.fnmatch(path, p) for p in patterns), (key, path))
            self.assertEqual(key, getattr(artifact, key).__name__)


if __name__ == '__main__':
    unittest.main()
