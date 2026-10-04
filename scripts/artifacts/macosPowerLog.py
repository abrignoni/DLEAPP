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
            'public MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15'
            ') the values added were 5,942,080.9 to 5,942,095.0 seconds, about 68.8 '
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
            'Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15)); what '
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
            'Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15)) '
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
            'logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15) Time Zone '
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
    "macosPowerLogLid": {
        "name": "PowerLog - Lid",
        "description": "Rows of PowerLog's PLPeripheralAgent_EventForward_ClamshellState table: "
                       "time and the closed value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLPeripheralAgent_EventForward_ClamshellState from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with Time corrected, and rows held by more '
            'than one database reported once, as its notes describe. Closed is reported as '
            'stored; what each value records is not established here. The table was empty on '
            'dleapp_macos_bigsur, whose PowerLog - Peripherals rows name VMware virtual devices. '
            'On the public MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus key '
            'mvs2026_macbookpro_macos15) Closed held 1 on 59 of the 64 rows and 0 on 5, and 61 of the '
            '63 pairs of consecutive rows repeat the value, so a row does not always mark a '
            "change. That Mac's power management log (Power Management Log (ASL)) has one "
            "'Clamshell Sleep' record in the period these rows cover, with rows holding 1 at 15.0 "
            'seconds before it and 1.6 seconds after it, and the earliest row holds 0 and comes '
            "16.8 seconds after a wake 'due to EC.LidOpen' in that log."
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "book",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
        },
    },
    "macosPowerLogPeripherals": {
        "name": "PowerLog - Peripherals",
        "description": "Rows of PowerLog's PLPeripheralAgent_EventForward_DeviceState table: "
                       "time, device name, connected and built-in values, vendor and product IDs.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLPeripheralAgent_EventForward_DeviceState from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with Time corrected, and rows held by more '
            'than one database reported once, as its notes describe. Device Name, Now Connected, '
            'Is Builtin, Device Type, Vendor ID, Product ID, Register Entry ID and Bus Version Or '
            'Speed are reported as stored, and what Now Connected, Is Builtin, Device Type and '
            'Bus Version Or Speed record is not established here; Vendor ID (hex) and Product ID '
            '(hex) are the same numbers in hexadecimal. On both public images '
            '(dleapp_macos_bigsur and the public MacBook Pro logical extraction (macOS 15.4 build '
            '24E248, corpus key mvs2026_macbookpro_macos15)) every row with Now Connected 0 has no Device '
            'Name and holds 0 in Is Builtin, Vendor ID, Product ID and Bus Version Or Speed, and '
            'every row with Now Connected 1 has a name. On the public MacBook Pro extraction '
            'every named row holds 1 in Is Builtin, so Now Connected and Is Builtin are identical '
            'on every row there; on dleapp_macos_bigsur Is Builtin was 1 only on the 16 rows '
            'naming the two USB root hub simulations and 0 on the other 60 named rows, which name '
            'the VMware virtual USB devices, the virtual Bluetooth adapter and AppleDisplay. A '
            'row without a name shares its Register Entry ID with an earlier named row on all 56 '
            'such rows of the public MacBook Pro extraction and on 3 of the 4 of '
            'dleapp_macos_bigsur, where 3 Register Entry IDs are each held by rows naming '
            'different devices, so an ID does not identify one device across an image. Device '
            'Type was 3 on the rows naming AppleDisplay (dleapp_macos_bigsur) and '
            'AppleBacklightDisplay (the public MacBook Pro extraction) and on 3 rows without a '
            'name, and 1 on every other row. ThunderboltRevisionID is not reported; it held 0 on '
            'every row of both public images. Time Offset (seconds) held 0.001 on every row of '
            'dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 80 rows",
        },
    },
    "macosPowerLogAudioDevices": {
        "name": "PowerLog - Audio Devices",
        "description": "Rows of PowerLog's PLAudioAgent_EventForward_AudioDevice table: time, "
                       "device ID, input and running values, source and transport codes, volume.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLAudioAgent_EventForward_AudioDevice from the PowerLog databases the PowerLog '
            '- Sleep and Wake artifact reads, with Time corrected, and rows held by more than one '
            "database reported once, as its notes describe. Logged Time is the row's "
            'timestampLogged corrected the same way. Device ID, Is Input, Is Running and Volume '
            'are reported as stored, and what Device ID and Is Running record is not established '
            'here. Source ID and Transport Type are stored as numbers and shown as their four '
            'characters, or as the stored number when its four bytes are not all printable. '
            "Apple's IOAudioTypes.h defines these four-character codes: 'bltn' as "
            "kIOAudioDeviceTransportTypeBuiltIn, 'usb ' as kIOAudioDeviceTransportTypeUSB and "
            "'blue' as kIOAudioDeviceTransportTypeBluetooth "
            '(https://github.com/apple-oss-distributions/IOAudioFamily/blob/6fdf514055a9868fe20e4dc3845b78dfa5e27110/IOAudioTypes.h#L468-L480), '
            "and 'ispk', 'hdpn' and 'imic' as the internal speaker, headphones and internal "
            "microphone port subtypes, with 'spdf' the S/PDIF output and input subtype "
            '(https://github.com/apple-oss-distributions/IOAudioFamily/blob/6fdf514055a9868fe20e4dc3845b78dfa5e27110/IOAudioTypes.h#L329-L339). '
            "Transport Type was 'bltn' on every row of both public images. On dleapp_macos_bigsur "
            "Source ID was 'hdpn' on 37 rows, all with Is Input 0, and 'spdf' on 24, all with Is "
            'Input 1, and Is Running held 1 on one row; on the public MacBook Pro logical '
            'extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15) Source ID was '
            "'ispk' on 7 rows, all with Is Input 0, and 'imic' on 6, all with Is Input 1, and Is "
            'Running held 0 on every row. Time Offset (seconds) held 0.001 on every row of '
            'dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "headphones",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 61 rows",
        },
    },
    "macosPowerLogAppLifecycle": {
        "name": "PowerLog - App Lifecycle",
        "description": "Rows of PowerLog's PLApplicationAgent_EventForward_AppLifecycle table: "
                       "time, bundle ID, event code, process ID and ASN values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLApplicationAgent_EventForward_AppLifecycle from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with times corrected, and rows held by '
            'more than one database reported once, as its notes describe. Bundle ID, Event, PID, '
            'ASN and Parent ASN are reported as stored; what Event, ASN and Parent ASN record is '
            'not established here. On dleapp_macos_bigsur Event held 1 on 3,464 rows, 2 on 3,351 '
            'and 0 on 61, and the rows of 2,194 of its 2,633 ASNs are one Event 1 followed by one '
            'Event 2; on the public MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus '
            'key mvs2026_macbookpro_macos15) Event held 0 on 505 of 596 rows, 2 on 49 and 1 on 42. Event '
            '1 and Event 2 are not established as a launch and an exit: 6 of '
            "dleapp_macos_bigsur's PowerLog - Frontmost App rows name an ASN whose latest Event 1 "
            'or 2 at or before them was 2. An ASN can appear with more than one PID (421 of the '
            "2,633 on dleapp_macos_bigsur), Parent ASN held 0 on 6,817 of that image's 6,876 "
            'rows, and com.apple.wifi.WiFiAgent accounts for 6,381 of them. The public MacBook '
            "Pro extraction's two copies of the live database differ: 26 of its rows are only in "
            'the copy under System/Volumes/Data. Time Offset (seconds) held 0.001 on every row of '
            'dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 6876 rows",
        },
    },
    "macosPowerLogProcessNetwork": {
        "name": "PowerLog - Process Network Usage",
        "description": "Rows of PowerLog's PLProcessNetworkAgent_EventInterval_UsageDiff table: "
                       "start and end times, bundle and process names, and the in and out values "
                       "for each interface as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLProcessNetworkAgent_EventInterval_UsageDiff from the PowerLog databases the '
            'PowerLog - Sleep and Wake artifact reads, with times corrected, and rows held by '
            "more than one database reported once, as its notes describe. Start Time is the row's "
            'timestamp and End Time its timestampEnd, each corrected; the rows span 1,767 to '
            '1,800 seconds on dleapp_macos_bigsur and 300 to 17,090 seconds on the public MacBook '
            'Pro logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15), 1,860 '
            'seconds on 5,561 of its 6,663 rows. Bundle Name, Process Name, Extension Name and '
            'the In and Out values for each interface are reported as stored, and the unit of the '
            'In and Out values is not established here. On dleapp_macos_bigsur Wifi In, Wifi Out, '
            'Cell In and Cell Out held 0 on every row, and Wired In or Wired Out was above 0 on '
            'every row; its tables have no ExtensionName, BTCompanionIn or BTCompanionOut column, '
            'so Extension Name, BT Companion In and BT Companion Out are empty there. On the '
            'public MacBook Pro extraction Cell In, Cell Out, BT Companion In and BT Companion '
            'Out held 0 on every row, and Extension Name has a value on 458 rows. Bundle Name '
            'equals Process Name on 258 of the 265 rows of dleapp_macos_bigsur and 5,381 of the '
            '6,663 of the public MacBook Pro extraction, whose two copies of the live database '
            'differ: 304 of its rows are only in the copy under System/Volumes/Data. Time Offset '
            '(seconds) held 0.001 on every row of dleapp_macos_bigsur.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 265 rows",
        },
    },
    "macosPowerLogScreenOn": {
        "name": "PowerLog - Screen On",
        "description": "Rows of PowerLog's PLDisplayAgent_Aggregate_ScreenOn table: time, time "
                       "interval and the ScreenOn value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLDisplayAgent_Aggregate_ScreenOn from the PowerLog databases the PowerLog - '
            'Sleep and Wake artifact reads, with times corrected, and rows held by more than one '
            'database reported once, as its notes describe. Time Interval and Screen On are '
            'reported as stored; what Screen On records is not established here, nor whether Time '
            'marks the start or the end of the interval. The table is absent from '
            "dleapp_macos_bigsur's databases. On the public MacBook Pro logical extraction (macOS "
            '15.4 build 24E248, corpus key mvs2026_macbookpro_macos15) Time Interval held 3600.0 on all 102 '
            'rows, Screen On ran from 122 to 3600 and was never above Time Interval, and 91 of '
            'the 101 gaps between consecutive rows are 3,600 seconds. One interval appears twice '
            'there, with Screen On 3300 in the copy of the live database under private/var and '
            '3600 in the copy under System/Volumes/Data, and that copy holds 10 more rows the '
            'other copy lacks.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "sun",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
        },
    },
    "macosPowerLogDeviceConfig": {
        "name": "PowerLog - Device Configuration",
        "description": "Rows of PowerLog's PLConfigAgent_EventNone_Config table: time, device boot time, build "
                       'and last build, last upgrade time, installed version, device, memory and disk sizes, and '
                       'remaining disk space as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLConfigAgent_EventNone_Config from the PowerLog databases the PowerLog - '
            'Sleep and Wake artifact reads, with Time corrected, and rows held by more than one '
            "database reported once, as its notes describe. Device Boot Time is the row's "
            "DeviceBootTime, read as Unix seconds and corrected with the value added to the row's "
            'own Time, or on its own for a row whose Time is blank. On the public MacBook Pro '
            'logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15), where the '
            'values added were 5,942,080.9 to 5,942,095.0 seconds, each of the 14 rows then gives '
            "a boot time 3.3 to 11.2 seconds after a BOOT_TIME record of that Mac's ASL Login and "
            'Boot Records; corrected on their own, the same values fall from 10.4 seconds before '
            'such a record to 11.2 seconds after one, and read uncorrected they fall about 68.8 '
            'days earlier. On dleapp_macos_bigsur, where the value added was 0.001 seconds, 7 of '
            'the 9 rows give a boot time within one second of such a record, and the other 2 give '
            "2021-02-15 15:25:46 UTC, a boot the ASL logs hold no record of; that Mac's "
            'install.log records softwareupdated starting 11 seconds later. Last Upgrade is '
            'LastUpgradeTimestamp read as Unix seconds with no correction. On the MacBook Pro '
            'Last Upgrade is 2025-09-04 00:23:07 UTC on all 14 rows, 28 seconds after the '
            'BOOT_TIME record of 00:22:39, and install.log records softwareupdated starting on '
            'build 15.4 (24E248) at 00:22:44 UTC; corrected, it would fall on 2025-11-11, a day '
            'no BOOT_TIME record falls on. On dleapp_macos_bigsur it is 2021-01-17 20:06:08 UTC '
            "on the first 3 rows, 51 seconds after install.log's first record of softwareupdated "
            'starting on build 11.1 (20C69), and 2021-02-15 15:59:21 UTC on the other 6, 60 '
            'seconds after the BOOT_TIME record of 15:58:21, the Device Boot Time of the first '
            'row whose Build is 20D74. Build and Last Build are Build and LastBuild as stored: on '
            'dleapp_macos_bigsur Build is 20C69 on the first 2 rows and 20D74 after them, and '
            'Last Build 20C69 on the first 3 and 20D74 after them; on the MacBook Pro Build holds '
            'one value, 24E248, on all 14 rows, and Last Build is empty on every row. Installed '
            'Version is InstalledSplat, which holds one value on all 14 rows of the MacBook Pro. '
            'Installed Version and Remaining Disk Space are empty on every row of '
            'dleapp_macos_bigsur, whose databases have no InstalledSplat or RemainingDiskSpace '
            'column. Device, Memory Size, Disk Size and Remaining Disk Space are Device, '
            'MemorySize, DeviceDiskSize and RemainingDiskSpace, reported as stored; their units '
            'are not established. Device, Memory Size and Disk Size each hold one value on each '
            'tested image, and Remaining Disk Space ranges from 906 to 939 on the MacBook Pro. '
            'Time Offset (seconds) holds one value, 0.001, on every row of dleapp_macos_bigsur. '
            'On dleapp_macos_bigsur Last Build separates the rows by Source File only by '
            'coincidence: the 3 rows whose Last Build is 20C69 are the ones an archive also '
            'holds. DeviceName and BootArgs are empty on every row of both public images, and '
            'DeviceSerialNumber on every row of the MacBook Pro, whose databases alone have that '
            'column; none of them is reported, nor is LastUpgradeSystemTimestamp, which also only '
            "the MacBook Pro's databases have and whose meaning is not established, nor are the "
            "table's other columns. ConfigMetrics_DeviceConfig_14_2, whose rows on the MacBook "
            'Pro have the same times and boot times as these, is not read: its BootReason and '
            'ShutdownReason columns are empty on every row there. Nor is '
            'PLSMCAgent_EventNone_ColdBoot, whose one column, VRTC, is empty on all 6 of the '
            "MacBook Pro's rows. Neither table is in dleapp_macos_bigsur's databases."
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 9 rows",
        },
    },
    "macosPowerLogBattery": {
        "name": "PowerLog - Battery",
        "description": "Rows of PowerLog's PLBatteryAgent_EventBackward_Battery table: time, battery level, and "
                       'the external connected, charging and fully charged values as stored.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "PowerLog (macOS)",
        "notes": (
            'Reads PLBatteryAgent_EventBackward_Battery from the PowerLog databases the PowerLog '
            '- Sleep and Wake artifact reads, with Time corrected, and rows held by more than one '
            'database reported once, as its notes describe. Level, External Connected, Is '
            'Charging and Fully Charged are Level, ExternalConnected, IsCharging and '
            'FullyCharged, reported as stored. ExternalConnected, IsCharging and FullyCharged are '
            "also the names of IOKit power source keys that Apple's IOPM.h lists, saying power "
            'source state is published to the IORegistry under those keys, with no further '
            'description; that PowerLog records those properties is not established (Reference: '
            'Apple, IOPM.h, the IOKit power management header of the macOS SDK, '
            'System/Library/Frameworks/IOKit.framework/Headers/pwr_mgt/IOPM.h in MacOSX26.5.sdk). '
            "The table is absent from dleapp_macos_bigsur's databases. On the public MacBook Pro "
            'logical extraction (macOS 15.4 build 24E248, corpus key mvs2026_macbookpro_macos15) the 7,103 '
            'rows run from 2025-12-18 05:01 to 2025-12-25 09:34 UTC, consecutive rows 60.0 '
            'seconds apart at the median; External Connected is 1 on 7,047 rows and 0 on 56, Is '
            'Charging is 1 on 137 and Fully Charged 1 on 603, and Level runs from 39 to 100. That '
            "Mac's power management log (Power Management Log (ASL)) holds 212 summaries reading "
            "'Using AC' or 'Using Batt' with a charge, and each of the 88 that fall within that "
            'span has a row no more than 26.1 seconds from it whose External Connected is 1 where '
            'the summary reads AC (3) and 0 where it reads Batt (85), and whose Level is within '
            'one of the charge on 83 of them and equal to it on 37. The copy of the live database '
            'under System/Volumes/Data holds 576 rows the copy under private/var does not, '
            'running to 2025-12-25 09:34 where the other copy stops at 2025-12-24 23:58. The '
            "table's other columns, among them CycleCount, Temperature, AdapterInfo and its "
            'capacity, voltage and current columns, are not reported, and neither is '
            'PLBatteryAgent_EventBackward_BatteryUI, whose only columns besides its ID and time '
            'are Level and IsCharging.'
        ),
        "paths": ('*/var/db/powerlog/Library/BatteryLife/*',),
        "output_types": ["standard"],
        "artifact_icon": "battery-charging",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
        },
    },
}

import sqlite3
from datetime import datetime, timedelta, timezone

from scripts import macos_powerlog
from scripts.ilapfuncs import artifact_processor, logfunc

_LABEL = 'PowerLog (macOS)'
_EARLIEST = datetime.min.replace(tzinfo=timezone.utc)


def _blank(value):
    return '' if value is None else value


def _plus(raw, offset):
    """A stored Unix time plus offset seconds (None adds nothing) as a UTC datetime; blank for
    a value that is not a clock reading (missing, zero or less) or too large for a date."""
    try:
        raw = float(raw)
    except (TypeError, ValueError):
        return ''
    if raw <= 0:
        return ''
    try:
        return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=raw + (offset or 0))
    except OverflowError:
        return ''


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


def _hex(value):
    """A stored integer written in hexadecimal, at least four digits."""
    return f'0x{value:04X}' if isinstance(value, int) and value >= 0 else _blank(value)


def _four_characters(value):
    """A stored four-character code as its four characters, or the stored value when it
    is not an integer whose four bytes are printable ASCII."""
    if isinstance(value, int) and 0 <= value < 1 << 32:
        text = value.to_bytes(4, 'big').decode('latin-1')
        if all(32 <= ord(character) < 127 for character in text):
            return text
    return _blank(value)


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


@artifact_processor
def macosPowerLogLid(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Closed (as stored)', 'Time Offset (seconds)',
                    'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['closed']), _seconds(offset))

    data_list, source = _collect(context, 'PLPeripheralAgent_EventForward_ClamshellState',
                                 ('ID', 'timestamp', 'closed'), build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogPeripherals(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Device Name', 'Now Connected (as stored)',
                    'Is Builtin (as stored)', 'Device Type (as stored)', 'Vendor ID',
                    'Vendor ID (hex)', 'Product ID', 'Product ID (hex)', 'Register Entry ID',
                    'Bus Version Or Speed (as stored)', 'Time Offset (seconds)', 'Source File')
    columns = ('ID', 'timestamp', 'DeviceName', 'NowConnected', 'IsBuiltin', 'DeviceType',
               'VendorID', 'ProductID', 'RegisterEntryID', 'BusVersionOrSpeed')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['DeviceName']), _blank(row['NowConnected']),
                _blank(row['IsBuiltin']), _blank(row['DeviceType']), _blank(row['VendorID']),
                _hex(row['VendorID']), _blank(row['ProductID']), _hex(row['ProductID']),
                _blank(row['RegisterEntryID']), _blank(row['BusVersionOrSpeed']),
                _seconds(offset))

    data_list, source = _collect(context, 'PLPeripheralAgent_EventForward_DeviceState', columns,
                                 build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogAudioDevices(context):
    data_headers = (('Time (UTC)', 'datetime'), ('Logged Time (UTC)', 'datetime'),
                    'Device ID (as stored)', 'Is Input (as stored)', 'Is Running (as stored)',
                    'Source ID', 'Transport Type', 'Volume', 'Time Offset (seconds)', 'Source File')
    columns = ('ID', 'timestamp', 'timestampLogged', 'DeviceID', 'IsInput', 'IsRunning',
               'SourceID', 'TransType', 'Volume')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        logged, _ = database.corrected(row['timestampLogged'])
        return (_blank(time), _blank(logged), _blank(row['DeviceID']), _blank(row['IsInput']),
                _blank(row['IsRunning']), _four_characters(row['SourceID']),
                _four_characters(row['TransType']), _blank(row['Volume']), _seconds(offset))

    data_list, source = _collect(context, 'PLAudioAgent_EventForward_AudioDevice', columns,
                                 build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogAppLifecycle(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Bundle ID', 'Event (as stored)', 'PID',
                    'ASN (as stored)', 'Parent ASN (as stored)', 'Time Offset (seconds)',
                    'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['BundleID']), _blank(row['Event']), _blank(row['PID']),
                _blank(row['ASN']), _blank(row['ParentASN']), _seconds(offset))

    data_list, source = _collect(context, 'PLApplicationAgent_EventForward_AppLifecycle',
                                 ('ID', 'timestamp', 'BundleID', 'Event', 'PID', 'ASN',
                                  'ParentASN'), build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogProcessNetwork(context):
    counters = ('WifiIn', 'WifiOut', 'WiredIn', 'WiredOut', 'CellIn', 'CellOut',
                'BTCompanionIn', 'BTCompanionOut')
    data_headers = (('Start Time (UTC)', 'datetime'), ('End Time (UTC)', 'datetime'),
                    'Bundle Name', 'Process Name', 'Extension Name', 'Wifi In', 'Wifi Out',
                    'Wired In', 'Wired Out', 'Cell In', 'Cell Out', 'BT Companion In',
                    'BT Companion Out', 'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        start, offset = database.corrected(row['timestamp'])
        end, _ = database.corrected(row['timestampEnd'])
        return ((_blank(start), _blank(end), _blank(row['BundleName']),
                 _blank(row['ProcessName']), _blank(row['ExtensionName']))
                + tuple(_blank(row[name]) for name in counters) + (_seconds(offset),))

    data_list, source = _collect(context, 'PLProcessNetworkAgent_EventInterval_UsageDiff',
                                 ('ID', 'timestamp', 'timestampEnd', 'BundleName', 'ProcessName',
                                  'ExtensionName') + counters, build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogScreenOn(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time Interval (as stored)',
                    'Screen On (as stored)', 'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['timeInterval']), _blank(row['ScreenOn']),
                _seconds(offset))

    data_list, source = _collect(context, 'PLDisplayAgent_Aggregate_ScreenOn',
                                 ('ID', 'timestamp', 'timeInterval', 'ScreenOn'), build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogDeviceConfig(context):
    data_headers = (('Time (UTC)', 'datetime'), ('Device Boot Time (UTC)', 'datetime'), 'Build',
                    'Last Build', ('Last Upgrade (UTC)', 'datetime'), 'Installed Version',
                    'Device (as stored)', 'Memory Size (as stored)', 'Disk Size (as stored)',
                    'Remaining Disk Space (as stored)', 'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        if time is None:
            # No row offset to apply: correct the boot time as a time of its own.
            boot = _blank(database.corrected(row['DeviceBootTime'])[0])
        else:
            # The boot time is in the clock of the row's own time, so it takes the row's offset.
            boot = _plus(row['DeviceBootTime'], offset)
        return (_blank(time), boot, _blank(row['Build']), _blank(row['LastBuild']),
                _plus(row['LastUpgradeTimestamp'], None), _blank(row['InstalledSplat']),
                _blank(row['Device']), _blank(row['MemorySize']), _blank(row['DeviceDiskSize']),
                _blank(row['RemainingDiskSpace']), _seconds(offset))

    data_list, source = _collect(context, 'PLConfigAgent_EventNone_Config',
                                 ('ID', 'timestamp', 'DeviceBootTime', 'Build', 'LastBuild',
                                  'LastUpgradeTimestamp', 'InstalledSplat', 'Device', 'MemorySize',
                                  'DeviceDiskSize', 'RemainingDiskSpace'), build)
    return data_headers, data_list, source


@artifact_processor
def macosPowerLogBattery(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Level (as stored)',
                    'External Connected (as stored)', 'Is Charging (as stored)',
                    'Fully Charged (as stored)', 'Time Offset (seconds)', 'Source File')

    def build(database, row, _side):
        time, offset = database.corrected(row['timestamp'])
        return (_blank(time), _blank(row['Level']), _blank(row['ExternalConnected']),
                _blank(row['IsCharging']), _blank(row['FullyCharged']), _seconds(offset))

    data_list, source = _collect(context, 'PLBatteryAgent_EventBackward_Battery',
                                 ('ID', 'timestamp', 'Level', 'ExternalConnected', 'IsCharging',
                                  'FullyCharged'), build)
    return data_headers, data_list, source
