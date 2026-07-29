"""Tests for modern Windows Photos and Clock artifacts."""

# pylint: disable=protected-access

import sqlite3
from datetime import datetime, timezone

from scripts.artifacts import windowsApps


class _Context:
    def __init__(self, files, seeker=None):
        self._files = files
        self._seeker = seeker

    def get_files_found(self):
        return self._files

    def set_files_found(self, files):
        self._files = files

    def get_seeker(self):
        return self._seeker or _Seeker({})

    @staticmethod
    def get_relative_path(path):
        return str(path)


class _Seeker:
    def __init__(self, matches):
        self._matches = matches
        self.patterns = []

    def search(self, pattern):
        self.patterns.append(pattern)
        return self._matches.get(pattern, [])


def _create_photos_database(path):
    with sqlite3.connect(path) as database:
        database.executescript(
            """
            CREATE TABLE mediaFolder (
                FolderId, Path, ParentFolderId, IsLibraryFolder, ProviderKey,
                FolderAttributes, DateCreated, DateModified, SumAllFileDates,
                SumMediaFileDates, ScannedMediaFileCount, DateScanned
            );
            CREATE TABLE mediaItemFile (
                FolderId, FileName, MediaItemKey, FileAttributes, ProviderKey,
                DateCreated, DateModified, DateIngested, FileSize, IsImage,
                AlternateDateTaken
            );
            CREATE TABLE mediaItemProps (
                MediaItemKey, PropVersion, PropScanDate, DateModified,
                DateTaken, Width, Height, Media_Duration, Rating, UserTags,
                Latitude, Longitude, LatitudeBucket, LongitudeBucket
            );
            CREATE TABLE mediaItemAddresses (
                LatitudeBucket, LongitudeBucket, DatePreviouslyFailed, Version,
                Locale, Country, Region, Town, NormalizedAddress
            );
            CREATE TABLE mediaItemCategory (
                MediaItemKey, Category, RelevanceScore
            );
            CREATE TABLE mediaItemDates (
                MediaItemKey, Locale, DateFormatterType, Date, FormattedDate
            );
            INSERT INTO mediaFolder VALUES (
                1, 'C:\\Evidence\\Pictures', 0, 1, 2, 17,
                116444736010000000, 116444736020000000, 0, 0, 1,
                30000000
            );
            INSERT INTO mediaItemFile VALUES (
                1, 'DLEAPP-PHOTO-TEST-001.png', 42, 128, 2,
                116444736010000000, 116444736020000000,
                116444736030000000, 1234, 1, 116444736010000000
            );
            INSERT INTO mediaItemProps VALUES (
                42, 1, 116444736040000000, 116444736020000000,
                116444736015000000, 1024, 768, NULL, 5, 'known-tag',
                10.5, -20.25, 10.5, -20.25
            );
            INSERT INTO mediaItemAddresses VALUES (
                10.5, -20.25, NULL, 1, 'en-US', 'Country', 'Region',
                'Town', 'Known Address'
            );
            INSERT INTO mediaItemCategory VALUES (42, 'document', 0.75);
            INSERT INTO mediaItemDates VALUES (
                42, 'en-US', 7, 116444736015000000, 'January 1, 1970'
            );
            """
        )


def test_photos_timestamp_order_preview_and_metadata(tmp_path, monkeypatch):
    database_path = tmp_path / "shared.sqlite"
    _create_photos_database(database_path)
    media_path = tmp_path / "C" / "Evidence" / "Pictures" / (
        "DLEAPP-PHOTO-TEST-001.png"
    )
    media_path.parent.mkdir(parents=True)
    media_path.write_bytes(b"known image")
    seeker = _Seeker({
        "*/Evidence/Pictures/DLEAPP-PHOTO-TEST-001.png": [media_path],
    })
    checked_in = []

    def _check_in_media(path, name=""):
        checked_in.append((path, name))
        return "known-media-reference"

    monkeypatch.setattr(windowsApps, "check_in_media", _check_in_media)

    headers, rows, _ = windowsApps.windowsPhotos.__wrapped__(
        _Context([database_path], seeker)
    )

    assert [header[0] for header in headers[:6]] == [
        "Date Ingested (UTC)",
        "Date Taken (UTC)",
        "Alternate Date Taken (UTC)",
        "Date Modified (UTC)",
        "Date Created (UTC)",
        "Property Scan Time (UTC)",
    ]
    assert headers[6:8] == (
        ("Media Preview", "media"),
        "Original File Status",
    )
    assert len(rows) == 1
    assert rows[0][0] == datetime(1970, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
    assert rows[0][6] == "known-media-reference"
    assert rows[0][7] == "Present in acquisition; copied to report"
    assert rows[0][10] == "DLEAPP-PHOTO-TEST-001.png"
    assert rows[0][17] == "known-tag"
    assert rows[0][23] == "Known Address"
    assert rows[0][24] == "document [0.75]"
    assert checked_in == [(
        "C:/Evidence/Pictures/DLEAPP-PHOTO-TEST-001.png",
        "DLEAPP-PHOTO-TEST-001.png",
    )]


def test_photos_reports_missing_original_without_inferring_deletion(tmp_path):
    database_path = tmp_path / "shared.sqlite"
    _create_photos_database(database_path)

    _, rows, _ = windowsApps.windowsPhotos.__wrapped__(
        _Context([database_path], _Seeker({}))
    )

    assert rows[0][6] == ""
    assert rows[0][7] == "Original file not present in acquisition"


def test_photos_folders_unix_100ns_scan_time(tmp_path):
    database_path = tmp_path / "shared.sqlite"
    _create_photos_database(database_path)

    headers, rows, _ = windowsApps.windowsPhotosFolders.__wrapped__(
        _Context([database_path])
    )

    assert headers[:3] == (
        ("Date Scanned (UTC)", "datetime"),
        ("Date Modified (UTC)", "datetime"),
        ("Date Created (UTC)", "datetime"),
    )
    assert rows[0][0] == datetime(1970, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
    assert rows[0][5] == r"C:\Evidence\Pictures"


def test_alarm_composite_timestamp_order_and_fields():
    alarm = {
        "Name": "DLEAPP-ALARM-TEST-001\x00",
        "Hour": 2,
        "Minute": 5,
        "IsEnabled": True,
        "DaysOfWeek": 0,
        "SnoozeInterval": 10,
        "ScheduledYear": 2026,
        "ScheduledMonth": 7,
        "ScheduledDay": 30,
        "ScheduledHour": 2,
        "ScheduledMinute": 5,
        "ChimeName": "Alarm1/SoundName\x00",
        "ChimePath": "ms-winsoundevent:Notification.Looping.Alarm\x00",
        "__Created": 116444736010000000,
        "__Updated": 116444736020000000,
    }

    row = windowsApps._alarm_row(
        alarm, "{KNOWN-RECORD}", "Packaged-app settings hive", "settings.dat"
    )

    assert row[:3] == (
        datetime(2026, 7, 30, 2, 5),
        datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
        datetime(1970, 1, 1, 0, 0, 2, tzinfo=timezone.utc),
    )
    assert row[3:9] == (
        "DLEAPP-ALARM-TEST-001",
        "02:05",
        "Yes",
        "No",
        0,
        10,
    )


def test_alarm_json_retains_every_alarm(tmp_path):
    alarms_path = tmp_path / "Alarms.json"
    alarms_path.write_text(
        """
        {
          "Alarms": [
            {"Name": "one", "Hour": 1, "Minute": 2, "IsEnabled": true},
            {"Name": "two", "Hour": 3, "Minute": 4, "IsEnabled": false}
          ]
        }
        """,
        encoding="utf-8",
    )

    headers, rows, _ = windowsApps.windowsAlarms.__wrapped__(
        _Context([alarms_path])
    )

    assert headers[:3] == (
        ("Next Scheduled Time (device local)", "datetime"),
        ("Created Time (UTC)", "datetime"),
        ("Updated Time (UTC)", "datetime"),
    )
    assert [row[3] for row in rows] == ["one", "two"]
