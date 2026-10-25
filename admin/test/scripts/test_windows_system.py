"""Tests for the Windows system artifacts migrated from WLEAPP."""

# pylint: disable=protected-access

import fnmatch
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsSystem  # pylint: disable=wrong-import-position


class _Context:
    def __init__(self, files):
        self._files = files

    def get_files_found(self):
        return self._files

    @staticmethod
    def get_relative_path(path):
        return str(path)


class TestWindowsSystem(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = pathlib.Path(self._tmp.name)

    def test_windows_timestamp_epochs(self):
        expected = datetime(1970, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(
            windowsSystem._utc_from_unix_seconds(1), expected.replace(second=1)
        )
        self.assertEqual(
            windowsSystem._utc_from_filetime(116444736010000000),
            expected.replace(second=1),
        )
        self.assertEqual(
            windowsSystem._utc_from_dotnet_ticks(621355968010000000),
            expected.replace(second=1),
        )
        self.assertEqual(windowsSystem._utc_from_filetime(0), "")

    def test_activities_cache_retains_non_json_payload(self):
        database_path = self.tmp_path / "ActivitiesCache.db"
        with sqlite3.connect(database_path) as database:
            database.execute(
                """
                CREATE TABLE Activity (
                    StartTime, EndTime, LastModifiedTime, ExpirationTime,
                    LastModifiedOnClient, AppActivityId, AppId, Payload,
                    ActivityType, ActivityStatus, Tag, "Group", IsLocalOnly, IsRead
                )
                """
            )
            database.execute(
                """
                INSERT INTO Activity VALUES (
                    1, 2, 3, 4, 5, 'activity-id',
                    '[{"application":"test.application"}]', 'Tk9OLUpTT04=',
                    11, 1, 'tag', 'group', 1, 0
                )
                """
            )
        database.close()

        _, rows, _ = windowsSystem.activitiesCache.__wrapped__(
            _Context([database_path])
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][5], "activity-id")
        self.assertEqual(rows[0][6], "test.application")
        self.assertEqual(rows[0][16], "Tk9OLUpTT04=")

    def _operations_database(self, with_operations=True):
        database_path = self.tmp_path / "ActivitiesCache.db"
        with sqlite3.connect(database_path) as database:
            database.execute("CREATE TABLE Activity (Id GUID, StartTime, AppId, Payload, ActivityType)")
            database.execute("INSERT INTO Activity VALUES (x'01', 10, '[]', '{}', 5)")
            if with_operations:
                database.execute(
                    "CREATE TABLE ActivityOperation (OperationOrder INTEGER, Id GUID, OperationType INT, "
                    "AppId TEXT, AppActivityId TEXT, ActivityType INT, LastModifiedTime, ExpirationTime, "
                    "Payload BLOB, CreatedTime, OperationExpirationTime, StartTime, EndTime, LastModifiedOnClient)"
                )
                database.execute(
                    "INSERT INTO ActivityOperation VALUES (7, x'02', 1, '[{\"application\":\"only.op\"}]', "
                    "'op-activity', 6, 30, 40, '{\"displayText\":\"Shown\"}', 20, 133000000000, 25, 35, 31)"
                )
                database.execute(
                    "INSERT INTO ActivityOperation VALUES (8, x'01', 3, '[]', '', 5, 12, 0, 'not json', 11, "
                    "NULL, 10, 0, 12)"
                )
        database.close()
        return database_path

    def test_operations_say_whether_the_id_is_in_the_activity_table(self):
        headers, rows, source = windowsSystem.activitiesCacheOperations.__wrapped__(
            _Context([self._operations_database()])
        )
        self.assertEqual(headers[0], ("Start Time (UTC)", "datetime"))
        index = {name if isinstance(name, str) else name[0]: i for i, name in enumerate(headers)}
        by_order = {row[index["Operation Order"]]: row for row in rows}
        only_here, also_in_activity = by_order[7], by_order[8]
        self.assertEqual(only_here[index["In Activity Table"]], "No")
        self.assertEqual(also_in_activity[index["In Activity Table"]], "Yes")
        self.assertEqual(only_here[index["Operation Type (as stored)"]], 1)
        self.assertEqual(only_here[index["Operation Expiration Time (as stored)"]], 133000000000)
        self.assertEqual(also_in_activity[index["Operation Expiration Time (as stored)"]], "")
        self.assertEqual(only_here[index["Created Time (UTC)"]], datetime(1970, 1, 1, 0, 0, 20, tzinfo=timezone.utc))
        self.assertEqual(only_here[index["Applications"]], "only.op")
        self.assertEqual(only_here[index["Display Text"]], "Shown")
        self.assertEqual(also_in_activity[index["End Time (UTC)"]], "")
        self.assertTrue(source.endswith("ActivitiesCache.db"))

    def test_a_file_without_the_operation_table_gives_no_rows_and_is_not_named(self):
        _, rows, source = windowsSystem.activitiesCacheOperations.__wrapped__(
            _Context([self._operations_database(with_operations=False)])
        )
        self.assertEqual((rows, source), ([], ""))

    def test_notifications_include_handler_and_payload_hash(self):
        database_path = self.tmp_path / "wpndatabase.db"
        with sqlite3.connect(database_path) as database:
            database.execute(
                """
                CREATE TABLE NotificationHandler (
                    RecordId INTEGER, PrimaryId TEXT, HandlerType TEXT,
                    CreatedTime TEXT, ModifiedTime TEXT
                )
                """
            )
            database.execute(
                """
                CREATE TABLE Notification (
                    ArrivalTime, ExpiryTime, BootId, Id, HandlerId, Type,
                    PayloadType, Payload, Tag, "Group", ExpiresOnReboot
                )
                """
            )
            database.execute(
                "INSERT INTO NotificationHandler VALUES "
                "(7, 'test.handler', 'app:test', 'created', 'modified')"
            )
            database.execute(
                """
                INSERT INTO Notification VALUES (
                    116444736010000000, 116444736020000000,
                    116444736000000000, 9, 7, 'toast', 'Xml',
                    '<toast><text>DLEAPP-NOTIFICATION-TEST-001</text></toast>',
                    'tag', 'group', 1
                )
                """
            )
        database.close()

        _, rows, _ = windowsSystem.windowsNotifications.__wrapped__(
            _Context([database_path])
        )
        self.assertEqual(len(rows), 1)
        # BootId is reported as stored, never decoded as a FILETIME timestamp
        self.assertEqual(rows[0][4], 116444736000000000)
        self.assertEqual(rows[0][7], "test.handler")
        self.assertEqual(rows[0][11], "DLEAPP-NOTIFICATION-TEST-001")
        self.assertEqual(len(rows[0][16]), 64)

    def test_sticky_notes_timestamp_first_and_markup_removed(self):
        database_path = self.tmp_path / "plum.sqlite"
        with sqlite3.connect(database_path) as database:
            database.execute(
                """
                CREATE TABLE Note (
                    UpdatedAt, CreatedAt, DeletedAt, Id, ParentId, Text,
                    IsOpen, IsAlwaysOnTop, Theme, WindowPosition
                )
                """
            )
            database.execute(
                """
                INSERT INTO Note VALUES (
                    621355968020000000, 621355968010000000, NULL,
                    'note-id', 'parent-id',
                    '\\id=01234567-89ab-cdef-0123-456789abcdef known text',
                    1, 0, 'Yellow', 'ManagedPosition='
                )
                """
            )
        database.close()

        headers, rows, _ = windowsSystem.windowsStickyNotes.__wrapped__(
            _Context([database_path])
        )
        self.assertEqual(
            headers[:3],
            (
                ("Updated Time (UTC)", "datetime"),
                ("Created Time (UTC)", "datetime"),
                ("Deleted Time (UTC)", "datetime"),
            ),
        )
        self.assertEqual(rows[0][5], "known text")

    def test_setupapi_sections_do_not_claim_first_connection(self):
        log_path = self.tmp_path / "setupapi.dev.log"
        log_path.write_text(
            """
>>>  [Device Install (Hardware initiated) - USB\\VID_1234&PID_5678\\ABC]
>>>  Section start 2026/07/29 10:00:00.100
     dvi: test
<<<  Section end 2026/07/29 10:00:01.600
<<<  [Exit status: SUCCESS]
""".lstrip(),
            encoding="utf-8",
        )
        headers, rows, _ = windowsSystem.setupapiSections.__wrapped__(
            _Context([log_path])
        )
        self.assertEqual(headers[0], "Start Time (device local)")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][3], r"USB\VID_1234&PID_5678\ABC")
        self.assertEqual(rows[0][4], "SUCCESS")
        self.assertEqual(rows[0][5], 1.5)
        self.assertEqual(rows[0][6], str(log_path))
        self.assertEqual(len(rows[0]), len(headers))

    def test_setupapi_paths_reach_every_spelling_of_the_folder_and_the_dated_copies(self):
        patterns = windowsSystem.__artifacts_v2__["setupapiSections"]["paths"]
        reached = (
            "root/lba0/Windows/INF/setupapi.dev.log",
            "root/C/WINDOWS/INF/setupapi.dev.log",
            "root/p2/Windows/inf/setupapi.dev.log",
            "root/lba0/Windows/Inf/setupapi.dev.log",
            "root/p2/Windows/INF/setupapi.dev.20231123_112100.log",
            "root/p2/Windows/inf/SetupAPI.dev.log",
        )
        missed = (
            "root/p2/Windows/INF/setupapi.setup.log",
            "root/p2/Windows/INF/setupapi.offline.20170929_064627.log",
            "root/p2/Windows/INF/setupapi.app.log",
            "root/p2/Windows/Recent/setupapi.dev.lnk",
        )
        for member in reached:
            self.assertEqual(sum(fnmatch.fnmatchcase(member, p) for p in patterns), 1, member)
        for member in missed:
            self.assertFalse(any(fnmatch.fnmatchcase(member, p) for p in patterns), member)

    def test_setupapi_reads_the_dated_copy_and_names_each_rows_file(self):
        section = """>>>  [Device Install (Hardware initiated) - USB\\VID_1234&PID_5678\\{serial}]
>>>  Section start 2026/07/2{day} 10:00:00.100
<<<  Section end 2026/07/2{day} 10:00:01.600
<<<  [Exit status: SUCCESS]
"""
        current = self.tmp_path / "setupapi.dev.log"
        older = self.tmp_path / "setupapi.dev.20260701_090000.log"
        other = self.tmp_path / "setupapi.setup.log"
        current.write_text(section.format(serial="B", day=9), encoding="utf-8")
        older.write_text(section.format(serial="A", day=1), encoding="utf-8")
        other.write_text(section.format(serial="C", day=2), encoding="utf-8")
        _headers, rows, source = windowsSystem.setupapiSections.__wrapped__(
            _Context([current, other, older])
        )
        self.assertEqual([(row[3], row[6]) for row in rows],
                         [(r"USB\VID_1234&PID_5678\A", str(older)),
                          (r"USB\VID_1234&PID_5678\B", str(current))])
        self.assertEqual(source, f"{older}\n{current}")


if __name__ == "__main__":
    unittest.main()
