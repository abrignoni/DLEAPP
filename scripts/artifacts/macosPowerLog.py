__artifacts_v2__ = {
    "macosPowerLogSleepWake": {
        "name": "PowerLog - Sleep and Wake",
        "description": "Rows of PowerLog's PLSleepWakeAgent_EventForward_PowerState table: "
                       "time, state and event codes, wake type, wake reason and sleep trigger.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLSleepWakeAgent_EventForward_PowerState from macOS PowerLog, in every .PLSQL '
            'database and .PLSQL.gz archive in /private/var/db/powerlog/Library/BatteryLife or '
            'below it: the live CurrentPowerlog.PLSQL, read with its -wal, and the archives in '
            'Archives, each decompressed to a temporary folder that is removed afterwards. A '
            'logical extraction can hold the folder under both private/var and '
            'System/Volumes/Data/private/var, and the two are read as one folder. Time is the '
            "row's timestamp, read as Unix seconds, corrected with PowerLog's "
            "PLStorageOperator_EventForward_TimeOffset table: the 'system' value of the latest "
            'entry at or before the time is added, or that of the oldest entry for a time older '
            "than every entry. That is the correction iLEAPP's PowerLog artifacts apply "
            '(https://github.com/abrignoni/iLEAPP/blob/bb6942ccbb27ada88c256ed5b91e283ba84ca9f7/scripts/artifacts/powerlog.py#L1437-L1452), '
            'except that the entries of every database in the folder are used together. Time '
            'Offset (seconds) is the value added, blank when the folder has no entries or Time is '
            "blank, and Logged Time is the row's timestampLogged corrected the same way. On the "
            'public MacBook Pro logical extraction (macOS 15.4 build 24E248, not a registered '
            'corpus key) the values added were 5,942,080.9 to 5,942,095.0 seconds, about 68.8 '
            "days, and 113 of the 167 Sleep, Wake and DarkWake records in that Mac's power "
            'management log (Power Management Log (ASL)) have a row here within one second of '
            'them, against none before the correction. On dleapp_macos_bigsur every value added '
            'was 0.001 seconds. A row that more than one database holds, with the same values and '
            'the same corrected times, is reported once, and Source File lists every database '
            'that held it (a row repeated within one database is kept each time): 2 of the 57 '
            'rows on dleapp_macos_bigsur, and all 283 on the public MacBook Pro extraction, whose '
            'two copies of the folder held the same rows. A stored timestamp of zero or less '
            'leaves Time blank: one row on dleapp_macos_bigsur stored -0.0008, while its '
            'timestampLogged and every other row fall in 2021, and it is reported with its Logged '
            'Time. Logged Time was later than Time on 142 of the 283 rows of the public MacBook '
            'Pro extraction, by up to 16,091 seconds, and on 2 rows of dleapp_macos_bigsur. State '
            'and Event are reported as stored; their meanings are not decoded here. On the public '
            'MacBook Pro extraction every row with State 1 and Event 6 (56) was within two '
            "seconds of a Sleep record in that Mac's power management log, every row with State 5 "
            'and Event 0 (55) within two seconds of a DarkWake record, 110 of the 111 with State '
            '5 and Event 6 within two seconds of a DarkWake record, and none of the 56 with Event '
            '4 within two seconds of any of those records; these are observations on one Mac, not '
            'a decoding. Wake Type, Wake Reason and Driver Wake Reason list, in stored order and '
            'separated by commas, the entries the side tables '
            'PLSleepWakeAgent_EventForward_PowerState_Array_WakeType, _Array_Reason and '
            "_Array_DriverWakeReason hold for the row, whose ID their FK_ID holds. The row's own "
            'WakeType, Reason and DriverWakeReason columns are not reported: on both public '
            'images they held 1 where the side table had entries for the row and 0 or nothing '
            'otherwise. On the public MacBook Pro extraction each of the 56 rows with a Wake '
            "Reason was within two seconds of a DarkWake or Wake record whose message reads 'due "
            "to' followed by the Wake Reason, a slash and the Wake Type, as in 'due to "
            "EC.RTC/Maintenance'. Driver Wake Reason was empty on both public images; on a "
            'private macOS 26 sample it held the words of the Wake Reason, in order. Side table '
            'entries whose FK_ID names no row of their database are not reported and are counted '
            "in the log: 2 in one archive, in each of the public MacBook Pro extraction's two "
            'copies of the folder. Sleep Triggers, Capabilities and UUID are reported as stored. '
            "On dleapp_macos_bigsur 10 of the 11 distinct UUIDs are also the uuid key of 'Display "
            "is turned on' or 'Display is turned off' records in that Mac's power management log, "
            "and the eleventh is on a row dated before that log's first record; on the public "
            'MacBook Pro extraction 282 of the 283 rows share one UUID. KernelSleepDate and the '
            'kernel wake time column (CurrentKernelWakeTime, or CurrentMachWakeTime) are not '
            'reported; what they record is not established here. The '
            'PLSleepWakeAgent_EventForward_PowerState_Dynamic side table is not read; it held no '
            'rows on either public image.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "power",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 57 rows",
        },
    },
    "macosPowerLogUserIdle": {
        "name": "PowerLog - User Idle",
        "description": "Rows of PowerLog's PLSleepWakeAgent_EventForward_UserIdle table: "
                       "time and the Idle value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLSleepWakeAgent_EventForward_UserIdle from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with Time corrected, and rows held by more '
            'than one database reported once, as its notes describe. Idle is reported as stored '
            'and held 0 or 1 on both public images (dleapp_macos_bigsur and the public MacBook '
            'Pro logical extraction (macOS 15.4 build 24E248, not a registered corpus key)); what '
            'each value records is not established here. On those images every row within five '
            "seconds of a 'Display is turned on' or 'Display is turned off' record in the Mac's "
            'power management log paired 0 with turned on (10 rows) and 1 with turned off (1 '
            'row); the other 39 rows had no such record within five seconds. Consecutive rows can '
            'hold the same value (9 of the 40 pairs on dleapp_macos_bigsur), and in each of the '
            'six databases of the public MacBook Pro extraction the earliest User Idle, Frontmost '
            'App and Time Zone rows fall within three seconds of one another, so a row does not '
            'always mark a change. Time Offset (seconds) held 0.001 on every row of '
            'dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "user",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 41 rows",
        },
    },
    "macosPowerLogFrontmostApp": {
        "name": "PowerLog - Frontmost App",
        "description": "Rows of PowerLog's PLApplicationAgent_EventForward_FrontmostApp "
                       "table: time and bundle ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLApplicationAgent_EventForward_FrontmostApp from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with Time corrected, and rows held by more '
            'than one database reported once, as its notes describe. Bundle ID, Application Type '
            'and ASN are reported as stored; what Application Type and ASN record is not '
            'established here. On both public images (dleapp_macos_bigsur and the public MacBook '
            'Pro logical extraction (macOS 15.4 build 24E248, not a registered corpus key)) '
            'Application Type was 3 on every row naming com.apple.ScreenSaver.Engine, '
            'com.apple.loginwindow, com.apple.SecurityAgent, com.apple.SystemProfiler or '
            'com.apple.UserNotificationCenter and 1 on every other row. Consecutive rows can name '
            'the same bundle (4 of the 112 pairs on dleapp_macos_bigsur and 6 of the 10 on the '
            'public MacBook Pro extraction), so a row does not always mark a change of app; see '
            'the PowerLog - User Idle notes. Time Offset (seconds) held 0.001 on every row of '
            'dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 113 rows",
        },
    },
    "macosPowerLogTimeZone": {
        "name": "PowerLog - Time Zone",
        "description": "Rows of PowerLog's PLLocaleAgent_EventForward_TimeZone table: time, "
                       "time zone name, offset from GMT, country code and locale.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLLocaleAgent_EventForward_TimeZone from the PowerLog databases the PowerLog - '
            'Sleep and Wake artifact reads, with Time corrected, and rows held by more than one '
            'database reported once, as its notes describe. Every column other than Time is '
            'reported as stored. On dleapp_macos_bigsur the rows name America/New_York (9) and '
            "US/Pacific (3), and Trigger held 'powerlog' on 10 and "
            "'kCFTimeZoneSystemTimeZoneDidChangeNotification' on 2. There Country Code held "
            "'Unavailable' on every row, Locale ID was empty on every row, and Time Zone Is In "
            'DST held 0 and Time Offset (seconds) 0.001 on every row. On the public MacBook Pro '
            'logical extraction (macOS 15.4 build 24E248, not a registered corpus key) Time Zone '
            'Name, Seconds From GMT, Time Zone Is In DST, Country Code, Locale ID and Trigger '
            'each held one value on all 7 rows: America/New_York, -18000, 0, US, en_US and '
            'powerlog. That extraction also carries a LocaleMetrics_TimeZone_1_2 table whose 7 '
            "rows repeat the time, name, Seconds From GMT and DST value of this table's 7, so it "
            'is not read separately.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 12 rows",
        },
    },
}

import sqlite3
from datetime import datetime, timezone

from scripts import macos_powerlog
from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'PowerLog (macOS)'
_EARLIEST = datetime.min.replace(tzinfo=timezone.utc)


def _blank(value):
    return '' if value is None else value


def _seconds(offset):
    """The applied offset for display: three decimals, blank when none was applied."""
    return '' if offset is None else round(offset, 3)


def _collect(context, table, columns, build, arrays=()):
    """Rows built from table in every PowerLog database found.

    A record held by more than one database (the same stored values and the same
    corrected times) is one row, and Source File lists every database that held it; see
    macos_powerlog.merge_sources. build(database, row, side) returns the row's values
    without Source File."""
    records = []
    read = []
    with macos_powerlog.open_databases(context.get_files_found(), logfunc,
                                       context.get_relative_path) as databases:
        for database in databases:
            relative = context.get_relative_path(database.source)
            try:
                rows = database.rows(table, columns)
                side = {column: database.side_values(table, column) for column in arrays}
            except sqlite3.DatabaseError as exc:
                logfunc(f'{_LABEL}: could not read {table} in {relative}: {exc}')
                continue
            ids = {row['ID'] for row in rows}
            unclaimed = sum(len(values) for column in arrays
                            for parent, values in side[column].items() if parent not in ids)
            if unclaimed:
                logfunc(f'{_LABEL}: {unclaimed} side table entries in {relative} name a '
                        f'{table} row that database does not hold; not reported')
            if rows:
                read.append(database.source)
            for row in rows:
                records.append((build(database, row, side), relative))
    merged = macos_powerlog.merge_sources(records)
    merged.sort(key=lambda item: (item[0][0] == '', item[0][0] or _EARLIEST))
    data_list = [values + ('\n'.join(sources),) for values, sources in merged]
    return data_list, '\n'.join(read)


def _listed(side, column, row_id):
    return ', '.join(str(value) for value in side[column].get(row_id, []))


@artifact_processor
def macosPowerLogSleepWake(context):
    data_headers = (('Time (UTC)', 'datetime'), ('Logged Time (UTC)', 'datetime'),
                    'State (as stored)', 'Event (as stored)', 'Wake Type', 'Wake Reason',
                    'Driver Wake Reason', 'Sleep Triggers', 'Capabilities (as stored)', 'UUID',
                    'Time Offset (seconds)', 'Source File')
    columns = ('ID', 'timestamp', 'timestampLogged', 'State', 'Event', 'SleepTriggers',
               'Capabilities', 'UUID')

    def build(database, row, side):
        time, offset = database.corrected(row['timestamp'])
        logged, _ = database.corrected(row['timestampLogged'])
        return (_blank(time), _blank(logged), _blank(row['State']), _blank(row['Event']),
                _listed(side, 'WakeType', row['ID']), _listed(side, 'Reason', row['ID']),
                _listed(side, 'DriverWakeReason', row['ID']), _blank(row['SleepTriggers']),
                _blank(row['Capabilities']), _blank(row['UUID']), _seconds(offset))

    data_list, source = _collect(context, 'PLSleepWakeAgent_EventForward_PowerState', columns,
                                 build, arrays=('WakeType', 'Reason', 'DriverWakeReason'))
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogUserIdle(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Idle (as stored)', 'Time Offset (seconds)',
                    'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['Idle']), _seconds(offset))

    data_list, source = _collect(context, 'PLSleepWakeAgent_EventForward_UserIdle',
                                 ('ID', 'timestamp', 'Idle'), build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogFrontmostApp(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Bundle ID', 'Application Type (as stored)',
                    'ASN (as stored)', 'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['BundleID']), _blank(row['ApplicationType']),
                _blank(row['ASN']), _seconds(offset))

    data_list, source = _collect(context, 'PLApplicationAgent_EventForward_FrontmostApp',
                                 ('ID', 'timestamp', 'BundleID', 'ApplicationType', 'ASN'),
                                 build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogTimeZone(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time Zone Name', 'Seconds From GMT',
                    'Time Zone Is In DST (as stored)', 'Country Code', 'Locale ID', 'Trigger',
                    'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['TimeZoneName']), _blank(row['SecondsFromGMT']),
                _blank(row['TimeZoneIsInDST']), _blank(row['CountryCode']),
                _blank(row['LocaleId']), _blank(row['Trigger']), _seconds(offset))

    data_list, source = _collect(context, 'PLLocaleAgent_EventForward_TimeZone',
                                 ('ID', 'timestamp', 'TimeZoneName', 'SecondsFromGMT',
                                  'TimeZoneIsInDST', 'CountryCode', 'LocaleId', 'Trigger'),
                                 build)
    return data_headers, data_list, source
