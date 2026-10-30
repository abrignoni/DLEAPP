"""Forensically useful Windows app artifacts modernized from WLEAPP.

Authors: @AlexisBrignoni, Codex
Predecessor: abrignoni/WLEAPP windowsAlarms.py and windowsPhotos.py.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import (
    artifact_processor,
    check_in_media,
    logfunc,
    open_sqlite_db_readonly,
)
from scripts.windows_app_settings import open_settings, settings


__artifacts_v2__ = {
    "windowsPhotos": {
        "name": "Photos",
        "description": "Media indexed by modern Microsoft Photos, including "
                       "ingestion and media times, original path, filename, "
                       "dimensions, tags, rating, and location metadata. The "
                       "original media is previewed when it remains present "
                       "at the database-recorded path in the acquisition.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Validated with Photos 2026.11020.20001.0. The modern "
                 "database is LocalState/shared.sqlite. Numeric timestamps "
                 "are converted from Windows FILETIME; their original "
                 "application-level timezone semantics may vary. Alternate "
                 "Date Taken is a separate app-recorded date whose "
                 "derivation is not documented; it must not be "
                 "treated as proof of capture time. Zero coordinates are "
                 "retained as stored and do not by themselves prove a "
                 "location. A blank preview accompanied by 'Original file "
                 "not present in acquisition' means the database row remains "
                 "but the referenced file was not supplied to DLEAPP; it does "
                 "not prove deletion. ImageEmbeddings data is not treated as "
                 "image content.",
        "paths": (
            "*/AppData/Local/Packages/Microsoft.Windows.Photos_*/"
            "LocalState/shared.sqlite*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "image",
        "sample_data": {
            "windows11_arm_parallels": (
                "Photos 2026.11020.20001.0 | 3 controlled rows"
            ),
        },
    },
    "windowsPhotosFolders": {
        "name": "Photos Folders",
        "description": "Folders indexed by modern Microsoft Photos, with "
                       "scan, modified, and created times and indexed media "
                       "counts.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Windows Apps",
        "notes": "Validated by adding a controlled local folder in Photos "
                 "2026.11020.20001.0. DateScanned uses 100-nanosecond units "
                 "from the Unix epoch; folder dates use Windows FILETIME.",
        "paths": (
            "*/AppData/Local/Packages/Microsoft.Windows.Photos_*/"
            "LocalState/shared.sqlite*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "folder",
        "sample_data": {
            "windows11_arm_parallels": (
                "Photos 2026.11020.20001.0 | 6 folders"
            ),
        },
    },
    "windowsAlarms": {
        "name": "Alarms",
        "description": "Windows Clock alarms from the modern packaged-app "
                       "settings hive or the older Alarms.json format, "
                       "including scheduled, created, and updated times and "
                       "the time each alarm's settings value was written.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-29",
        "last_update_date": "2026-10-22",
        "requirements": "python-registry",
        "category": "Windows Apps",
        "notes": "Modernized from WLEAPP and validated on "
                 "windows11_arm_parallels with Clock "
                 "11.2605.10.0. Scheduled fields are device-local; created "
                 "and updated values are converted from Windows FILETIME. "
                 "Days of Week is reported as stored, undecoded. When the "
                 "source carries no IsRecurring value, Recurring is derived "
                 "from a nonzero Days of Week value. The settings.dat hive "
                 "is read offline, without loading it into the examiner "
                 "system registry, and the alarm values of its "
                 "LocalState\\Alarms key are decoded by DLEAPP's own "
                 "scripts/windows_app_settings.py, from the type numbers and "
                 "composite layout of python-registry's SettingsParse.py "
                 "(Yogesh Khatri, MIT; "
                 "https://github.com/williballenthin/python-registry/blob/4edb5d1b72597faf257878060aa68baa9c5b28df/Registry/SettingsParse.py#L38-L165). "
                 "Value Written (UTC) is the FILETIME stored at the end of "
                 "the alarm's value, which ogmini's Notepad-State-Library "
                 "(MIT) describes as the time of the setting's change "
                 "(https://github.com/ogmini/Notepad-State-Library/blob/ce53f9d66de4551fa78f3cb19df90d7820f08d94/README.md#L298-L307): "
                 "when the value was written, not when the alarm is due; "
                 "it is blank for Alarms.json rows. Until 2026-10-22 the "
                 "values were decoded by python-registry, which drops that "
                 "time; on windows11_arm_parallels both alarm rows are "
                 "unchanged in every other column by the move, and on each "
                 "the stored FILETIME of Value Written (UTC) equals those "
                 "of its __Created and __Updated members; the report can "
                 "show Value Written (UTC) one microsecond earlier, because "
                 "the columns are converted by two routines. Created Time (UTC) and Updated "
                 "Time (UTC) were identical on both rows of that image. A "
                 "hive with no alarm values gives no rows; its path appears "
                 "in the located-at list only when another file in the run "
                 "gave rows. The Clock hives of hexordia_mvs2025_win11, "
                 "alihadi_challenge3_win81 (2) and two of szechuan_win10's "
                 "three have no LocalState\\Alarms key; those of "
                 "af_case2_win10, lonewolf_win10, pc_mus_001_win11 and the "
                 "third szechuan_win10 hive have the key with no values, and the "
                 "Alarms.json of lonewolf_win10 holds an empty Alarms list."
                 " A dirty hive, one whose base block's two sequence numbers "
                 "differ, is read after the entries in its .LOG1 and .LOG2 "
                 "transaction logs that continue its sequence are applied, "
                 "following Maxim Suhanov's 'Windows registry file format "
                 "specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "When no log in the format Windows 8.1 and later write applies, a log in the older format used before Windows 8.1 is applied instead: the first of .LOG1 and .LOG2 whose base block is valid and holds the hive's last-written time has the pages its dirty vector marks written where the vector places them (https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L620-L677, https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L742). On the 16 hives of cfreds_leakage_win7 that carry such a log as .LOG1, each copied, made dirty and given overwritten bytes in every page its log marks for the test, this rebuilt each hive byte for byte, as rla 2026.10.1 did; none of the 54 dirty hives in the 17 corpus images surveyed carries one. A lone .LOG beside a hive is not read. A replay that would give a key an earlier last-written time than the hive already holds is not applied, a "
                 "check added here beyond the specification; the run log "
                 "names each hive replayed, with the sequence numbers "
                 "applied, and each dirty hive read as it is, with the "
                 "reason.",
        "paths": ('*/AppData/Local/Packages/Microsoft.WindowsAlarms_*/LocalState/Alarms/Alarms.json',
                  '*/AppData/Local/Packages/Microsoft.WindowsAlarms_*/Settings/settings.dat',
                  '*/AppData/Local/Packages/Microsoft.WindowsAlarms_*/Settings/[Ss][Ee][Tt][Tt][Ii][Nn][Gg][Ss].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "windows11_arm_parallels": (
                "Clock 11.2605.10.0 | 2 rows"
            ),
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (LocalState\\Alarms key holds no values)",
            "lonewolf_win10": "Windows 10 1709 build 16299 | 0 rows (LocalState\\Alarms key holds no values; Alarms.json holds an empty Alarms list)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (LocalState\\Alarms key holds no values)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (two hives have no LocalState\\Alarms key, the third's key holds no values)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no LocalState\\Alarms key)",
            "alihadi_challenge3_win81": "Windows 8.1 build 9600 | 0 rows (no LocalState\\Alarms key)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 build 17763 | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no file matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 SP1 build 7601 | 0 rows (no file matches the declared paths)",
        },
    },
}


_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WINDOWS_FILETIME_EPOCH_TICKS = 116444736000000000
_TICKS_PER_SECOND = 10_000_000


def _utc_from_filetime(value):
    if value in (None, "", 0):
        return ""
    try:
        seconds = (int(value) - _WINDOWS_FILETIME_EPOCH_TICKS) / _TICKS_PER_SECOND
        return _UNIX_EPOCH + timedelta(seconds=seconds)
    except (OverflowError, TypeError, ValueError):
        return ""


def _utc_from_unix_100ns(value):
    if value in (None, "", 0):
        return ""
    try:
        return _UNIX_EPOCH + timedelta(seconds=int(value) / _TICKS_PER_SECOND)
    except (OverflowError, TypeError, ValueError):
        return ""


def _yes_no(value):
    if value is True or value == 1:
        return "Yes"
    if value is False or value == 0:
        return "No"
    return "Unknown" if value is not None else ""


def _clean_text(value):
    return value.rstrip("\x00") if isinstance(value, str) else value or ""


def _recorded_media_path(folder, filename):
    """Build a normalized Windows path suitable for evidence-file matching."""
    if not folder or not filename:
        return ""
    normalized_folder = str(folder).replace("\\", "/").rstrip("/")
    normalized_name = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
    return f"{normalized_folder}/{normalized_name}"


def _escape_fnmatch(value):
    """Escape evidence-controlled glob metacharacters for an exact search."""
    return value.replace("[", "[[]").replace("*", "[*]").replace("?", "[?]")


def _media_search_pattern(recorded_path):
    """Return a suffix glob for a drive-letter, UNC, or relative Windows path."""
    normalized = recorded_path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")
    return f"*/{_escape_fnmatch(normalized)}"


def _extract_referenced_media(context, recorded_paths):
    """Extract only media files explicitly referenced by a Photos database."""
    seeker = context.get_seeker()
    original_files = list(context.get_files_found())
    extracted_files = []
    present_paths = set()

    for recorded_path in dict.fromkeys(path for path in recorded_paths if path):
        matches = seeker.search(_media_search_pattern(recorded_path))
        if matches:
            present_paths.add(recorded_path)
            extracted_files.extend(matches)

    if extracted_files:
        context.set_files_found(list(dict.fromkeys(original_files + extracted_files)))
    return present_paths


def _photos_records(database):
    return database.execute(
        """
        SELECT f.DateIngested, p.DateTaken, f.AlternateDateTaken,
               f.DateModified, f.DateCreated, p.PropScanDate, f.MediaItemKey,
               d.Path, f.FileName, f.FileSize, f.IsImage, p.Width, p.Height,
               p.Media_Duration, p.Rating, p.UserTags, p.Latitude,
               p.Longitude, a.Country, a.Region, a.Town, a.NormalizedAddress,
               (
                   SELECT group_concat(
                       c.Category || ' [' || c.RelevanceScore || ']', ' | '
                   )
                     FROM mediaItemCategory AS c
                    WHERE c.MediaItemKey = f.MediaItemKey
               ) AS Categories,
               (
                   SELECT group_concat(
                       md.DateFormatterType || ': ' || md.FormattedDate, ' | '
                   )
                     FROM mediaItemDates AS md
                    WHERE md.MediaItemKey = f.MediaItemKey
               ) AS FormattedDates
          FROM mediaItemFile AS f
          JOIN mediaFolder AS d ON d.FolderId = f.FolderId
          LEFT JOIN mediaItemProps AS p ON p.MediaItemKey = f.MediaItemKey
          LEFT JOIN mediaItemAddresses AS a
            ON a.LatitudeBucket = p.LatitudeBucket
           AND a.LongitudeBucket = p.LongitudeBucket
         ORDER BY f.DateIngested DESC
        """
    ).fetchall()


@artifact_processor
def windowsPhotos(context):
    data_headers = (
        ("Date Ingested (UTC)", "datetime"),
        ("Date Taken (UTC)", "datetime"),
        ("Alternate Date Taken (UTC)", "datetime"),
        ("Date Modified (UTC)", "datetime"),
        ("Date Created (UTC)", "datetime"),
        ("Property Scan Time (UTC)", "datetime"),
        ("Media Preview", "media"),
        "Original File Status",
        "Media Item Key",
        "Folder",
        "Filename",
        "File Size (bytes)",
        "Image",
        "Width",
        "Height",
        "Media Duration (database value)",
        "Rating",
        "User Tags",
        "Latitude",
        "Longitude",
        "Country",
        "Region",
        "Town",
        "Normalized Address",
        "Categories [relevance]",
        "Formatted Dates [formatter type]",
        "Source File",
    )
    rows = []
    sources = []
    database_records = []
    recorded_paths = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "shared.sqlite":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            records = _photos_records(database)
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"Photos: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        source = context.get_relative_path(file_found)
        database_records.append((records, source))
        for record in records:
            recorded_paths.append(_recorded_media_path(record[7], record[8]))

    present_paths = _extract_referenced_media(context, recorded_paths)
    for records, source in database_records:
        for record in records:
            recorded_path = _recorded_media_path(record[7], record[8])
            media_reference = ""
            if recorded_path in present_paths:
                media_reference = check_in_media(
                    recorded_path, name=record[8] or ""
                ) or ""
                if media_reference:
                    original_status = "Present in acquisition; copied to report"
                else:
                    original_status = (
                        "Present in acquisition; report preview unavailable"
                    )
            else:
                original_status = "Original file not present in acquisition"
            rows.append((
                _utc_from_filetime(record[0]),
                _utc_from_filetime(record[1]),
                _utc_from_filetime(record[2]),
                _utc_from_filetime(record[3]),
                _utc_from_filetime(record[4]),
                _utc_from_filetime(record[5]),
                media_reference,
                original_status,
                record[6],
                record[7] or "",
                record[8] or "",
                record[9],
                _yes_no(record[10]),
                record[11] or "",
                record[12] or "",
                record[13] or "",
                record[14] or "",
                record[15] or "",
                record[16] if record[16] is not None else "",
                record[17] if record[17] is not None else "",
                record[18] or "",
                record[19] or "",
                record[20] or "",
                record[21] or "",
                record[22] or "",
                record[23] or "",
                source,
            ))
    return data_headers, rows, "\n".join(sources)


@artifact_processor
def windowsPhotosFolders(context):
    data_headers = (
        ("Date Scanned (UTC)", "datetime"),
        ("Date Modified (UTC)", "datetime"),
        ("Date Created (UTC)", "datetime"),
        "Folder ID",
        "Parent Folder ID",
        "Path",
        "Library Folder",
        "Scanned Media File Count",
        "Provider Key",
        "Folder Attributes",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        if os.path.basename(file_found).lower() != "shared.sqlite":
            continue
        database = open_sqlite_db_readonly(file_found)
        if database is None:
            continue
        try:
            records = database.execute(
                """
                SELECT DateScanned, DateModified, DateCreated, FolderId,
                       ParentFolderId, Path, IsLibraryFolder,
                       ScannedMediaFileCount, ProviderKey, FolderAttributes
                  FROM mediaFolder
                 ORDER BY DateScanned DESC, Path
                """
            ).fetchall()
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"Photos Folders: could not read '{file_found}': {exception}")
            database.close()
            continue
        database.close()
        sources.append(file_found)
        source = context.get_relative_path(file_found)
        for record in records:
            rows.append((
                _utc_from_unix_100ns(record[0]),
                _utc_from_filetime(record[1]),
                _utc_from_filetime(record[2]),
                record[3],
                record[4],
                record[5] or "",
                _yes_no(record[6]),
                record[7],
                record[8],
                record[9],
                source,
            ))
    return data_headers, rows, "\n".join(sources)


def _scheduled_local(alarm):
    fields = (
        alarm.get("ScheduledYear"),
        alarm.get("ScheduledMonth"),
        alarm.get("ScheduledDay"),
        alarm.get("ScheduledHour"),
        alarm.get("ScheduledMinute"),
    )
    if any(value is None for value in fields):
        return ""
    try:
        return datetime(*(int(value) for value in fields))
    except (TypeError, ValueError):
        return ""


def _alarm_row(alarm, record_id, source_format, source, written=""):
    days = alarm.get("DaysOfWeek")
    recurring = alarm.get("IsRecurring")
    if recurring is None and days is not None:
        try:
            recurring = int(days) != 0
        except (TypeError, ValueError):
            recurring = None
    try:
        alarm_time = (
            f"{int(alarm.get('Hour')):02d}:{int(alarm.get('Minute')):02d}"
        )
    except (TypeError, ValueError):
        alarm_time = ""
    return (
        _scheduled_local(alarm),
        _utc_from_filetime(alarm.get("__Created")),
        _utc_from_filetime(alarm.get("__Updated")),
        written,
        _clean_text(alarm.get("Name")),
        alarm_time,
        _yes_no(alarm.get("IsEnabled")),
        _yes_no(recurring),
        days if days is not None else "",
        alarm.get("SnoozeInterval", ""),
        _clean_text(alarm.get("ChimeName")),
        _clean_text(alarm.get("ChimePath")),
        record_id,
        source_format,
        source,
    )


def _json_alarms(file_found):
    with open(file_found, "r", encoding="utf-8-sig") as source:
        document = json.load(source)
    values = document.get("Alarms", []) if isinstance(document, dict) else []
    return [
        (value, str(index), "")
        for index, value in enumerate(values)
        if isinstance(value, dict)
    ]


def _registry_alarms(file_found):
    if Registry is None:
        raise RuntimeError(
            "python-registry is required to read Windows Clock settings.dat"
        )
    hive = open_settings(file_found)
    try:
        key = hive.open(r"LocalState\Alarms")
    except Registry.RegistryKeyNotFoundException:
        return []
    alarms = []
    for name, setting in settings(key).items():
        if setting.type_name != "Composite":
            continue
        if not isinstance(setting.value, dict):
            logfunc(f"Alarms: alarm {name} not decoded: {setting.error}")
            continue
        members = {member: item[1] for member, item in setting.value.items()}
        alarms.append((members, name, setting.written))
    return alarms


@artifact_processor
def windowsAlarms(context):
    data_headers = (
        ("Next Scheduled Time (device local)", "datetime"),
        ("Created Time (UTC)", "datetime"),
        ("Updated Time (UTC)", "datetime"),
        ("Value Written (UTC)", "datetime"),
        "Name",
        "Alarm Time (device local)",
        "Enabled",
        "Recurring",
        "Days of Week (database value)",
        "Snooze Interval (minutes)",
        "Chime Name / Resource",
        "Chime Path",
        "Record ID",
        "Source Format",
        "Source File",
    )
    rows = []
    sources = []
    for file_found in map(str, context.get_files_found()):
        basename = os.path.basename(file_found).lower()
        try:
            if basename == "alarms.json":
                alarms = _json_alarms(file_found)
                source_format = "Alarms.json"
            elif basename == "settings.dat":
                alarms = _registry_alarms(file_found)
                source_format = "Packaged-app settings hive"
            else:
                continue
        except Exception as exception:  # pylint: disable=broad-exception-caught
            logfunc(f"Alarms: could not read '{file_found}': {exception}")
            continue
        sources.append(file_found)
        source = context.get_relative_path(file_found)
        for alarm, record_id, written in alarms:
            rows.append(_alarm_row(alarm, record_id, source_format, source, written))
    return data_headers, rows, "\n".join(sources)
