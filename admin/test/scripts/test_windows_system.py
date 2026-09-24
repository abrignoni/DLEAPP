"""Tests for the Windows system artifacts migrated from WLEAPP."""

# pylint: disable=protected-access

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


if __name__ == "__main__":
    unittest.main()
