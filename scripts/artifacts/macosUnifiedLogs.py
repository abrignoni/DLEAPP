"""Apple Unified Log entries (tracev3), imported into the LAVA database, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Ported from iLEAPP's logarchive import. The tracev3 data is read with Mandiant's
unifiedlog_iterator through scripts/unifiedlogs.py; a 'log show' JSON export is read
directly when one is supplied instead.
"""

__artifacts_v2__ = {
    "macosUnifiedLogs": {
        "name": "Unified Logs",
        "description": "Apple Unified Log entries from the tracev3 data under db/diagnostics with the "
                       "uuidtext format strings or in a .logarchive folder, or from a 'log show' JSON "
                       "export, imported "
                       "into the LAVA database: time, process, subsystem, category and message.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "Reading tracev3 data needs the unifiedlog_iterator binary from "
                        "Mandiant's macos-UnifiedLogs, found through the "
                        "DLEAPP_UNIFIEDLOG_ITERATOR environment variable, the bin folder beside "
                        "dleapp.py or inside a built DLEAPP executable, or PATH",
        "category": "Unified Logs (macOS)",
        "notes": "Imports the Apple Unified Log entries the parser returns into the LAVA database "
                 "only, one row per entry. The tracev3 files under db/diagnostics, with the "
                 "format strings under db/uuidtext, or, when no db/diagnostics folder holds "
                 "files, the contents of a .logarchive folder, are read by Mandiant's "
                 "unifiedlog_iterator "
                 "(https://github.com/mandiant/macos-UnifiedLogs), which DLEAPP runs with --mode "
                 "log-archive and --format jsonl and finds through the DLEAPP_UNIFIEDLOG_ITERATOR "
                 "environment variable, the bin folder beside dleapp.py or inside a built DLEAPP "
                 "executable, or PATH. admin/scripts/fetch_unifiedlog_iterator.py places the "
                 "binary in the bin folder beside dleapp.py, and a DLEAPP executable built with "
                 "packaging/build.py after that carries it. The run log records the version the "
                 "binary reports, unifiedlog_iterator 0.7.0 on the tested images. When no "
                 "binary is found the tracev3 data is not read and the run log says so. A log show "
                 "--style json export named logarchive*.json is read directly instead when one is "
                 "present; neither tested image carries one. Timestamp (UTC) is the time the parser "
                 "gives each entry, cut from nanoseconds to microseconds, or for a JSON export the "
                 "entry's timestamp with its stated offset converted to UTC. Row Number counts rows in"
                 " the order read. Process Image Path, Process ID, Subsystem, Category and Event "
                 "Message are the process, pid, subsystem, category and message values the parser "
                 "emits, or processImagePath, processID, subsystem, category and eventMessage from a "
                 "JSON export. Trace ID is traceID from a JSON export; the parser emits none, so Trace"
                 " ID has no value on any row read from tracev3 data, which is every row of both "
                 "tested images. A logical extraction of a Mac can hold both "
                 "private/var/db/diagnostics and System/Volumes/Data/private/var/db/diagnostics, and "
                 "the same for uuidtext; both copies are read together as one store, a file only "
                 "one copy holds from that copy and a file both hold from the copy whose bytes "
                 "begin with the other's, or, when neither does, from the copy read first, the "
                 "one with the most files beneath it, and the run log counts each case. On the "
                 "public MacBook Pro logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15"
                 ") private/var/db/diagnostics held 262 files and the System/Volumes/Data "
                 "copy 267: 19 tracev3 files only in "
                 "private/var/db/diagnostics, 24 files only in the other copy, 6 longer in the "
                 "System/Volumes/Data copy, each beginning with the other copy's bytes, and 237 "
                 "identical. Read alone, the System/Volumes/Data copy gives 22,102,026 entries; read "
                 "together the store gives 27,030,315, and the 19 files only "
                 "private/var/db/diagnostics holds give 4,928,289 when unifiedlog_iterator reads them "
                 "on their own. On dleapp_macos_bigsur the store gives 3,024,846 entries from "
                 "2021-02-15 15:25:46 to 2021-02-19 19:53:32 UTC, and on the MacBook Pro 27,030,315 "
                 "from 2025-11-26 15:51:30 to 2025-12-25 09:43:52 UTC. The first 20 lines the "
                 "parser writes to its error output are copied to the run log and any more are "
                 "counted: on dleapp_macos_bigsur one, that it failed to get a message "
                 "string from a UUIDText file, and on the MacBook Pro two, about an unsupported number"
                 " size of 16.",
        "sample_data": {
                     "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 3,024,846 rows",
                 },
        "paths": ('*/logarchive*.json', '*/db/diagnostics/*', '*/db/uuidtext/*', '*.logarchive/*'),
        "output_types": "lava_only",
        "artifact_icon": "database",
    },
    "macosUnifiedLogScreenUnlock": {
        "name": "Unified Logs - Screen Unlock",
        "description": "Unified log entries about locking and unlocking a Mac: keybag state transitions, the "
                       "kernel's volume lock and unlock notifications, Touch ID match results, loginwindow "
                       "password attempts and failed password verification entries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the LAVA "
                 "database in the same run, so it reports nothing when that artifact did not run; Row "
                 "Number is the entry's row number in that table and rows are in that order. Selects the "
                 "entries Tim Korver reports for a Mac unlock in 'Same unlock, three different stories' "
                 "(https://thesisfriday.com/thesis-friday-26-same-unlock-three-different-stories/, "
                 "measured there on macOS 26.6.2 on Apple silicon): the 'Transition:' entries of the "
                 "com.apple.chrono keybag category, of which that research reads 'locked -> inBioUnlock' "
                 "as following Touch ID and 'locked -> unlocked' as following a password; biometrickitd "
                 "'matchResult:timestamp:' with MATCH and a user ID, or NO-MATCH; coreauthd 'has "
                 "received no-match'; loginwindow 'loginPressed:' attempt numbers, 'password is CORRECT' "
                 "and 'Unlock succeeded, with password'; opendirectoryd 'ODRecordVerifyPassword failed'; "
                 "and authorizationhost 'pam_authenticate failed'. Every keybag transition is selected, "
                 "not only those leaving 'locked', and so is the kernel's 'Sending notification for "
                 "volume' entry, which carries the state as written (unlocked or locked on the tested "
                 "images). Tim Korver's 'Backward reasoning from a provable endpoint' "
                 "(https://thesisfriday.com/thesis-friday-27-backward-reasoning-from-a-provable-endpoint/, "
                 "measured on macOS 26.6.2) reports that a session unlocked with Touch ID stays in the "
                 "biometric state until it locks, that two processes writing the same transition are one "
                 "message relayed and not two observations, and that the kernel layer is the deepest "
                 "record of an unlock where it is present; it does not name the kernel strings, and the "
                 "volume notification is the entry his 'What a busy phone forgets' "
                 "(https://thesisfriday.com/thesis-friday-28-what-a-busy-phone-forgets/) counts with the "
                 "kernel lines of an unlock on iOS. Its relation to a screen unlock on macOS was not "
                 "tested here. A MATCH entry is not an unlock: 'Backward reasoning from a provable "
                 "endpoint' recorded successful matches with the machine already unlocked and no change "
                 "of state. The same research reports that most of these are written at the info and "
                 "debug levels, so a log collected without those levels carries few of them. An "
                 "ODRecordVerifyPassword or pam_authenticate failure is not established to be a person "
                 "typing a wrong password: 'Backward reasoning from a provable endpoint' found password "
                 "verification and authentication failure lines in a block where no password was typed, "
                 "without naming the strings, and whether these entries are of that kind was not tested "
                 "here. Read them beside the loginwindow entries around them. An absent entry is not "
                 "evidence that no unlock happened: 'The stop rule' "
                 "(https://thesisfriday.com/the-stop-rule/) sets out that an empty result counts only "
                 "when the log is shown to cover the period for that kind of entry. Tested on "
                 "dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and the "
                 "unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: 61 rows, 5 attempt entries, 5 'password is "
                 "CORRECT', 10 'Unlock succeeded' and 41 ODRecordVerifyPassword failures. macOS 14.6.1: "
                 "524 rows, 17 matchResult MATCH entries (user IDs 501 and 503), 1 'password is "
                 "CORRECT', 437 ODRecordVerifyPassword failures, 12 pam_authenticate failures, 37 keybag "
                 "transitions (18 'disabled -> unlocked', 8 'disabled -> unknown', 7 'unlocked -> "
                 "unknown', 2 'locking -> inBioUnlock', 2 'unlocked -> locking'; 'unknown' is reported "
                 "as stored) and 20 volume notifications (11 unlocked, 9 locked), with no attempt or "
                 "'Unlock succeeded' entry. macOS 15.4: 38 rows, 6 keybag transitions (2 'locked -> "
                 "unlocked', 2 'locking -> locked', 2 'unlocked -> locking', each written once by "
                 "chronod and once by NotificationCenter), 2 volume notifications (1 unlocked, 1 "
                 "locked), 1 attempt, 1 'password is CORRECT', 2 'Unlock succeeded' and 26 "
                 "ODRecordVerifyPassword failures. No keybag transition or volume notification appeared "
                 "on Big Sur. No transition leaving 'locked' appeared on 14.6.1, where the only form "
                 "naming inBioUnlock was 'locking -> inBioUnlock' (one entry each from chronod and "
                 "NotificationCenter). No 'locked -> inBioUnlock', NO-MATCH or coreauthd no-match "
                 "appeared on any tested image.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 61 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 524 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 38 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "unlock",
    },
    "macosUnifiedLogAuthorization": {
        "name": "Unified Logs - Authorization Rights",
        "description": "Unified log entries from authd recording authorization rights granted or refused "
                       "to a program, and the account whose credentials satisfied a right.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects authd 'Succeeded authorizing right', 'Failed to authorize right' "
                 "and 'authenticated as user ... for right' entries. Each names the right and the "
                 "program that asked for it; the 'authenticated as user' entry also names the "
                 "account whose credentials were accepted for the right. Right names are reported "
                 "as stored. The research cited by the Screen Unlock artifact reads "
                 "'system.login.screensaver' as the right needed to dismiss a locked screen "
                 "(https://thesisfriday.com/thesis-friday-26-same-unlock-three-different-stories/). "
                 "Many grants go to system daemons with no person involved: mdmclient's "
                 "com.apple.ServiceManagement.daemons.modify grants were 94 of the macOS 15.4 "
                 "rows. Tested on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 "
                 "(macOS 14.6.1) and the unified log store of a macOS 15.4 MacBook Pro logical "
                 "extraction (mvs2026_macbookpro_macos15). Big Sur: 157 rows (156 granted, 1 "
                 "authenticated) over 20 distinct rights. macOS 14.6.1: 471 rows (460 granted, 5 "
                 "refused, 6 authenticated) over 40 rights. macOS 15.4: 107 rows (106 granted, 1 "
                 "authenticated, for system.login.screensaver) over 6 rights. Process Image Path "
                 "(authd), Subsystem (com.apple.Authorization) and Category (authd) held one value "
                 "on every row of each tested image, and Process ID one value on the macOS 15.4 "
                 "rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 157 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 471 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 107 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "key",
    },
    "macosUnifiedLogTCCRequests": {
        "name": "Unified Logs - TCC Access Requests",
        "description": "Privacy (TCC) access requests reconstructed from tccd's AUTHREQ unified log "
                       "entries: service, subject, attributed process, preflight and the result values "
                       "tccd logged.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Groups the tccd entries of one request, matched on the message ID within "
                 "one tccd process ID (tccd PID and Message ID): AUTHREQ_CTX gives Function, "
                 "Service and Preflight, AUTHREQ_SUBJECT the Subject, AUTHREQ_ATTRIBUTION the "
                 "first process in the attribution with its role, identifier and path, and "
                 "AUTHREQ_RESULT authValue and authReason. One row per request, timed by its "
                 "AUTHREQ_RESULT entry, or by its first entry when it has none. Auth Value and "
                 "Auth Reason are reported as stored: their meaning is not established here. These "
                 "rows are the requests tccd logged; TCC.db holds the stored access entries, "
                 "reported by the TCC artifacts. Tested on dleapp_macos_bigsur (macOS 11.2.1), "
                 "evidencelocker_macos14 (macOS 14.6.1) and the unified log store of a macOS 15.4 "
                 "MacBook Pro logical extraction (mvs2026_macbookpro_macos15). Big Sur: 9,244 "
                 "requests from 10 tccd processes; Subject on 7,579; no AUTHREQ_ATTRIBUTION entry, "
                 "so the three Attribution columns held no value on any row; Auth Value 0 on 253, "
                 "1 on 7,282, 2 on 1,709. macOS 14.6.1: 39,067 requests from 16 processes, 2 "
                 "without a result; Subject on 28,941; Auth Value 0 on 13,349, 1 on 3,139, 2 on "
                 "22,575, 4 on 2. The subject com.yourcompany.RECON-IMAGER, named like an "
                 "acquisition tool, made 24,744 of them, 12,335 for "
                 "kTCCServiceSystemPolicyAppData. macOS 15.4: 10,891 requests from 2 processes, 1 "
                 "without a result; Subject on 378; Auth Value 0 on 72, 1 on 304, 2 on 10,514. "
                 "High volume, LAVA-only.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 9,244 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 39,067 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 10,891 rows",
        },
        "paths": None,
        "output_types": "lava_only",
        "artifact_icon": "shield",
    },
    "macosUnifiedLogGatekeeper": {
        "name": "Unified Logs - Gatekeeper Scans",
        "description": "Unified log entries from syspolicyd's Gatekeeper scans: what was scanned (team, "
                       "identifier, bundle identifier) and the scan result value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects syspolicyd 'GK performScan' and 'GK evaluateScanResult' entries. "
                 "Each names the scanned code by a volume and object ID or a path hash, its team "
                 "identifier, signing identifier and bundle identifier where present. The number "
                 "after 'evaluateScanResult:' and the values after the identifiers are reported as "
                 "stored; their meaning is not established here. Results seen: 2 on all 199 Big "
                 "Sur results, 2 and 3 on 14.6.1 (4 and 1) and on 15.4 (8 and 2). Tested on "
                 "dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and "
                 "the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: 233 rows (34 performScan, 199 "
                 "evaluateScanResult). macOS 14.6.1: 9 rows (4 and 5). macOS 15.4: 16 rows (6 and "
                 "10). Process Image Path (syspolicyd), Subsystem (com.apple.syspolicy.exec) and "
                 "Category (default) held one value on every row of each tested image, and Process "
                 "ID one value on the macOS 15.4 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 233 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 9 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 16 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "shield",
    },
    "macosUnifiedLogDiskArbitration": {
        "name": "Unified Logs - Disk Arbitration",
        "description": "Unified log entries from diskarbitrationd recording disks created, probed, "
                       "mounted, unmounted and removed, and mount or unmount approvals a process "
                       "dissented from.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects diskarbitrationd 'created disk', 'probed disk', 'mounted disk', "
                 "'unmounted disk' and 'removed disk' entries and its 'dispatched response ... "
                 "approval ... dissented' entries. The disk is named by its device node "
                 "(/dev/diskNsM), not by volume name; probed entries give the file system, and "
                 "mount, unmount and probe entries are written as 'ongoing' and again with a "
                 "completion status such as 'success'. Pair the device node with the volume and "
                 "device artifacts to name it. Tested on dleapp_macos_bigsur (macOS 11.2.1), "
                 "evidencelocker_macos14 (macOS 14.6.1) and the unified log store of a macOS 15.4 "
                 "MacBook Pro logical extraction (mvs2026_macbookpro_macos15). Big Sur: 6 rows, "
                 "all approval responses. macOS 14.6.1: 607 rows (137 created, 210 probed, 78 "
                 "mounted, 122 unmounted, 55 removed, 5 approval). macOS 15.4: 19 rows (3 created, "
                 "4 probed, 2 mounted, 4 unmounted, 6 approval). Process Image Path held one "
                 "value (diskarbitrationd) on every row of each tested image and Process ID one "
                 "value on the Big Sur and macOS 15.4 rows; Subsystem "
                 "(com.apple.DiskArbitration.diskarbitrationd) and Category (default) held one "
                 "value on the macOS 14.6.1 and 15.4 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 6 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 607 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 19 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "hard-drive",
    },
    "macosUnifiedLogMalwareScans": {
        "name": "Unified Logs - XProtect and MRT Scans",
        "description": "Unified log entries recording XProtect system, login and startup scans and MRT "
                       "'Finished MRT run' entries.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects XProtect 'Starting system scan', 'Finished system scan', "
                 "'Launching login scan' and 'Launching startup scan' entries and MRT 'Finished "
                 "MRT run'. They record that a scan ran, not what it found; no detection entry is "
                 "selected. Tested on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 "
                 "(macOS 14.6.1) and the unified log store of a macOS 15.4 MacBook Pro logical "
                 "extraction (mvs2026_macbookpro_macos15). Big Sur: 19 rows, all 'Finished MRT "
                 "run'. macOS 14.6.1: 56 rows (20 started and 18 finished system scans, 10 login "
                 "scans, 4 startup scans, 4 MRT runs). macOS 15.4: 36 rows (18 started, 18 "
                 "finished system scans). On Big Sur Subsystem and Category held no value and "
                 "Process Image Path and Event Message one value (MRT) on all 19 rows; on macOS "
                 "15.4 Process Image Path, Subsystem (com.apple.XProtectFramework) and Category "
                 "(Runner) held one value on all 36.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 19 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 56 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 36 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "shield",
    },
    "macosUnifiedLogShutdown": {
        "name": "Unified Logs - Shutdown and Reboot Requests",
        "description": "Unified log entries from shutdown and reboot recording a halt or reboot and the "
                       "account that requested it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects /sbin/shutdown 'halt by' and 'reboot by' entries and /sbin/reboot "
                 "'rebooted by' entries, which name the account that ran the command. A shutdown "
                 "or restart made another way, such as from the Apple menu, was not tested. Tested "
                 "on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) "
                 "and the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: 5 rows, all 'halt by root'. macOS 14.6.1: "
                 "5 rows (2 halt, 2 reboot by shutdown, 1 rebooted by reboot), one naming a user "
                 "account rather than root. macOS 15.4: none. Subsystem and Category held no value "
                 "on any row; on Big Sur Process Image Path (/sbin/shutdown) and Event Message "
                 "('halt by root: ') held one value on all 5 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 5 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 5 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "power",
    },
    "macosUnifiedLogSudo": {
        "name": "Unified Logs - sudo Commands",
        "description": "Unified log entries from sudo recording commands run with it, with the working "
                       "folder and target account.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects sudo entries containing 'COMMAND='. Each carries, as sudo wrote "
                 "it, the account that ran sudo, PWD (the working folder), USER (the account the "
                 "command ran as) and COMMAND. Installer package scripts run sudo too: 5 of the 7 "
                 "macOS 14.6.1 rows had a working folder under PKInstallSandbox. Tested on "
                 "dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and "
                 "the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: none. macOS 14.6.1: 7 rows. macOS 15.4: "
                 "none. Process Image Path held one value (/usr/bin/sudo) and Subsystem and "
                 "Category no value on all 7 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 7 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "terminal",
    },
    "macosUnifiedLogScreenCapture": {
        "name": "Unified Logs - Screen Capture Launches",
        "description": "Unified log entries from screencapture recording that it was started and the "
                       "mode it was started with.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects screencapture 'launched with' entries. The value after 'launched "
                 "with' is reported as stored; 'keyboard.screen' was the only one seen. An entry "
                 "records that screencapture started, not that an image was saved. Tested on "
                 "dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and "
                 "the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: none. macOS 14.6.1: 5 rows. macOS 15.4: "
                 "none. Process Image Path, Subsystem (com.apple.screencapture), Category "
                 "(default) and Event Message held one value on all 5 macOS 14.6.1 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 5 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "camera",
    },
    "macosUnifiedLogSleepWake": {
        "name": "Unified Logs - Sleep and Wake",
        "description": "Unified log entries recording system sleep and wake: the kernel's sleep and "
                       "power-on notices to loginwindow and the wake reasons the kernel and powerd "
                       "logged.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects the kernel's 'PMRD: kIOMessageSystemWillSleep' and 'PMRD: "
                 "kIOMessageSystemWillPowerOn' entries for the notice sent to loginwindow (the "
                 "kernel writes one such entry per notified client, and only the loginwindow one "
                 "is kept), kernel entries containing 'Wake reason: ', and powerd 'Wake reason:' "
                 "entries. Wake reasons are reported as stored; values seen were EC.LidOpen "
                 "(User), EC.KeyboardTouchpad (User), EC.RTC (Alarm), EC.USBC (Maintenance), "
                 "EC.SleepTimer (SleepTimer), EC.ACAttach (Maintenance) and Host followed by a "
                 "hexadecimal value. The macOS 15.4 store held 224 kernel wake reasons and only 2 "
                 "sleep and 2 power-on notices to loginwindow, so a wake reason does not always "
                 "have a loginwindow notice beside it. PowerLog's sleep and wake rows are reported "
                 "by the PowerLog artifacts. Tested on dleapp_macos_bigsur (macOS 11.2.1), "
                 "evidencelocker_macos14 (macOS 14.6.1) and the unified log store of a macOS 15.4 "
                 "MacBook Pro logical extraction (mvs2026_macbookpro_macos15). Big Sur: 43 rows "
                 "(19 sleep, 19 power-on, 5 powerd wake reasons whose values were <private>). "
                 "macOS 14.6.1: 61 rows (10 sleep, 10 power-on, 41 kernel wake reasons). macOS "
                 "15.4: 228 rows (2 sleep, 2 power-on, 224 kernel wake reasons). Subsystem and "
                 "Category held no value on the kernel rows, and Process Image Path (/kernel) and "
                 "Process ID (0) held one value on every macOS 14.6.1 and 15.4 row.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 43 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 61 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 228 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "moon",
    },
    "macosUnifiedLogUsbMassStorage": {
        "name": "Unified Logs - USB Mass Storage",
        "description": "Unified log entries in which the kernel logged a USB mass storage device's "
                       "identifier.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects kernel 'USBMSC Identifier (non-unique):' entries. The values "
                 "after the colon are reported as stored: an identifier string, three further "
                 "values and a number after a comma; their meaning is not established here. Tested "
                 "on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) "
                 "and the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: none. macOS 14.6.1: 10 rows carrying 3 "
                 "distinct identifier strings. macOS 15.4: none. Process Image Path (/kernel) and "
                 "Process ID (0) held one value and Subsystem and Category no value on all 10 "
                 "macOS 14.6.1 rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 10 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "hard-drive",
    },
    "macosUnifiedLogLoginSessions": {
        "name": "Unified Logs - Login Window Sessions",
        "description": "Unified log entries from loginwindow recording that it started, user logins with "
                       "the user ID, and logouts, restarts and shutdowns with their type.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects loginwindow 'Login Window Application Started', "
                 "'sendDistributedNotification: com.apple.sessionDidLogin, with userID:' and the "
                 "'startLogout' entry that carries 'logoutType:', which names the type (Logout, "
                 "Restart or Shutdown) and a subtype such as SoftwareUpdate, as loginwindow wrote "
                 "it. Tested on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS "
                 "14.6.1) and the unified log store of a macOS 15.4 MacBook Pro logical extraction "
                 "(mvs2026_macbookpro_macos15). Big Sur: 19 rows (7 starts, 6 logins for user ID "
                 "501, 5 Shutdown, 1 Restart with subtype SoftwareUpdate). macOS 14.6.1: 29 rows "
                 "(10 starts, 10 logins for user IDs 501 to 504, 7 Logout, 1 Restart, 1 Shutdown). "
                 "macOS 15.4: none. Process Image Path (loginwindow) and Subsystem "
                 "(com.apple.loginwindow.logging) held one value on the Big Sur and macOS 14.6.1 "
                 "rows.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 19 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 29 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "log-in",
    },
    "macosUnifiedLogIosDevices": {
        "name": "Unified Logs - iOS Device Connections",
        "description": "Unified log entries from usbmuxd and iTunes recording iOS devices connecting to "
                       "the Mac, and pairing attempts.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-03",
        "last_update_date": "2026-10-03",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": "Reads the macosunifiedlogs table that the Unified Logs artifact writes into the "
                 "LAVA database in the same run, so it reports nothing when that artifact did not "
                 "run; Row Number is the entry's row number in that table and rows are in that "
                 "order. Selects usbmuxd 'device connected' and 'device disconnected' entries, its "
                 "MobileDevice 'Successfully paired', 'Failed to pair' and 'Could not pair with "
                 "the device' entries, and 'Device attached over direct/cable' entries, which "
                 "iTunes wrote on macOS 14.6.1 with the device's UDID as stored. The connected "
                 "entry carries the device identifier as stored; pair it with the Paired iOS "
                 "Devices (lockdown) artifact. On macOS 14.6.1 one failed pairing gave "
                 "kAMDPasswordProtectedError, reported as stored. Tested on dleapp_macos_bigsur "
                 "(macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and the unified log store "
                 "of a macOS 15.4 MacBook Pro logical extraction (mvs2026_macbookpro_macos15). Big "
                 "Sur: none. macOS 14.6.1: 5 rows (1 usbmuxd connected, 1 iTunes attached, 2 "
                 "pairing failures, 1 successful pairing). macOS 15.4: none.",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 5 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "smartphone",
    },
    "macosUnifiedLogBatteryCenterSources": {
        "name": "Unified Logs - Battery Center Power Sources",
        "description": 'Unified log entries in which Battery Center listed a power source: an internal battery, a '
                       'wireless accessory or a UPS, with the name, type, transport, charge values and identifiers it '
                       'logged.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-09",
        "last_update_date": "2026-10-09",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": 'Reads the macosunifiedlogs table that the Unified Logs artifact writes into the LAVA database in '
                 "the same run, so it reports nothing when that artifact did not run; Row Number is the entry's "
                 'row number in that table and rows are in that order. Selects com.apple.BatteryCenter entries '
                 "containing 'Found power source: {', whose message is a dictionary of 'key = value;' lines. Each "
                 "column named for a key holds that key's value as logged, with the quotes and backslash escapes "
                 "of a quoted value removed; every other key goes to Other Values as 'key = value', with any line "
                 'that is not a key and value pair, and a message with no opening brace is kept whole there. A '
                 'value that is itself a dictionary or a list is kept as one value under its key, its lines as '
                 'logged and joined by spaces, so a key inside it is not taken for a key of the power source. The '
                 'closing brace is not required: an entry cut short is split up to the cut, and a line cut in '
                 "half goes to Other Values. Both shapes were measured on iOS images with iLEAPP's Battery Center "
                 'power source artifact (a nested dictionary in 3,929 entries on 5 images; 371 entries on 2 '
                 'images cut at 1,031 bytes) and neither is exercised on macOS: all 8 entries here are 667 to 669 '
                 'bytes long, end with the closing brace and hold no nested value. The meaning '
                 "and units of the values are not established here. Howard Oakley describes these entries in 'How "
                 "macOS keeps an eye on UPS and wireless devices' "
                 '(https://eclecticlight.co/2024/06/21/how-macos-keeps-an-eye-on-ups-and-wireless-devices/) and '
                 "'Check UPS, batteries and input devices using Unhidden' "
                 '(https://eclecticlight.co/2024/07/08/check-ups-batteries-and-input-devices-using-unhidden/): he '
                 'reports that they come from the BatteryCenter private framework added in macOS Sonoma, that they '
                 "list wireless keyboards, mice and trackpads, a UPS connected by USB and a notebook's internal "
                 'battery, and that they are written only once a Battery widget has been installed since the Mac '
                 'started. His examples show Accessory Identifier holding six hyphen-separated hexadecimal pairs '
                 'for a Bluetooth keyboard and an alphanumeric string for a USB UPS, with Vendor ID and Product ID '
                 'beside it and Accessory Category for the keyboard. No tested image holds an accessory or UPS '
                 'entry, so those four columns are taken from his published examples and were not exercised here: '
                 'Accessory Identifier, Accessory Category, Vendor ID and Product ID had no value on any of the 8 '
                 'rows. Tested on dleapp_macos_bigsur (macOS 11.2.1), evidencelocker_macos14 (macOS 14.6.1) and '
                 'mvs2026_macbookpro_macos15 (macOS 15.4). The Big Sur and macOS 15.4 stores held no '
                 'com.apple.BatteryCenter entry at all, so this artifact has no rows there; that is not evidence '
                 'that no accessory or UPS was connected. macOS 14.6.1: 80 com.apple.BatteryCenter entries, of '
                 'which 8 are selected here, 2 from each of 4 BatteriesAvocadoWidgetExtension processes; the 2 '
                 'entries of one process carried the same values. All 8 describe the internal battery: Name '
                 '(InternalBattery-0), Type (InternalBattery), Transport Type (Internal), Power Source State '
                 '(Battery Power), Max Capacity (100), Is Charging (0), Is Present (1), Hardware Serial Number and '
                 'Process Image Path held one value on all 8 rows; Current Capacity held 4 values and Power Source '
                 'ID 3. Other Values carried Battery Provides Time Remaining, BatteryHealth, '
                 'BatteryHealthCondition, Current, DesignCycleCount, LPM Active, Optimized Battery Charging '
                 'Engaged, Time to Empty and Time to Full Charge. The other 72 entries (notification '
                 "registrations, 'Fetch connected devices', source counts and the 'Found device' entries the "
                 'Battery Center Devices artifact reports) are not selected.',
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 8 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "battery",
    },
    "macosUnifiedLogBatteryCenterDevices": {
        "name": "Unified Logs - Battery Center Devices",
        "description": 'Unified log entries in which Battery Center listed a device with a battery: its name, vendor, '
                       'charge percentage, charging and connection values, transport and identifiers as logged.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-09",
        "last_update_date": "2026-10-09",
        "requirements": "The Unified Logs artifact (macosUnifiedLogs) must run in the same session",
        "category": "Unified Logs (macOS)",
        "notes": 'Reads the macosunifiedlogs table that the Unified Logs artifact writes into the LAVA database in '
                 "the same run, so it reports nothing when that artifact did not run; Row Number is the entry's "
                 'row number in that table and rows are in that order. Selects com.apple.BatteryCenter entries '
                 "containing 'Found device: <BCBatteryDevice:', whose message is a list of 'key = value' pairs "
                 "separated by '; '. The message is split where '; ' is followed by a word and '='. Columns hold "
                 "the values as logged, '(null)' included: Name (name), Group Name (groupName), Vendor (vendor), "
                 'Model Number (modelNumber), Percent Charge (percentCharge), Charging (charging), Connected '
                 '(connected), Internal (internal), Power Source State (the key is logged as poweredSoureState), '
                 'Transport Type (transportType), Accessory Identifier (accessoryIdentifier), Accessory Category '
                 '(accessoryCategory), Identifier (identifier) and Product Identifier (productIdentifier). Every '
                 'other pair goes to Other Values, and a message of another shape is kept whole there. The meaning '
                 "of the values is not established here. Howard Oakley describes these entries in 'How macOS keeps "
                 "an eye on UPS and wireless devices' "
                 '(https://eclecticlight.co/2024/06/21/how-macos-keeps-an-eye-on-ups-and-wireless-devices/) and '
                 "'Check UPS, batteries and input devices using Unhidden' "
                 '(https://eclecticlight.co/2024/07/08/check-ups-batteries-and-input-devices-using-unhidden/): he '
                 'reports that they come from the BatteryCenter private framework added in macOS Sonoma, that they '
                 "list wireless keyboards, mice and trackpads, a UPS connected by USB and a notebook's internal "
                 'battery, and that they are written only once a Battery widget has been installed since the Mac '
                 'started. His posts quote the power source dictionaries, reported by the Battery Center Power '
                 'Sources artifact, and not this entry. Tested on dleapp_macos_bigsur (macOS 11.2.1), '
                 'evidencelocker_macos14 (macOS 14.6.1) and mvs2026_macbookpro_macos15 (macOS 15.4). The Big Sur '
                 'and macOS 15.4 stores held no com.apple.BatteryCenter entry at all, so this artifact has no rows '
                 'there; that is not evidence that no accessory or UPS was connected. macOS 14.6.1: 8 rows, 2 from '
                 'each of 4 BatteriesAvocadoWidgetExtension processes, all for the internal battery; in each '
                 'process Identifier and Percent Charge equalled the Power Source ID and Current Capacity of that '
                 "process's power source entries. Name, Group Name (InternalBattery-0), Vendor (Apple), Model "
                 'Number ((null)), Charging (NO), Connected (YES), Internal (YES), Power Source State (Battery '
                 'Power), Transport Type (Internal), Accessory Identifier ((null)), Accessory Category (Unknown), '
                 'Product Identifier (0), Other Values (parts, matchIdentifier, lowBattery, lowPowerModeActive and '
                 'powerSource) and Process Image Path held one value on all 8 rows. No tested image holds an entry '
                 'for an accessory or a UPS, so how this entry describes one was not exercised here.',
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 8 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "battery",
    },
}

import os
import re
from datetime import datetime, timezone

import ijson

from scripts import unifiedlogs
from scripts.ilapfuncs import artifact_processor, get_file_path, get_sqlite_db_records, \
    logfunc

DATA_HEADERS = (('Timestamp (UTC)', 'datetime'), 'Row Number', 'Process Image Path', 'Process ID',
                'Subsystem', 'Category', 'Event Message', 'Trace ID')


def _json_timestamp(timestamp):
    """A 'log show' timestamp such as '2021-02-19 19:48:25.533606-0500' as aware UTC, or ''."""
    text = (timestamp or '').strip()
    if len(text) > 5 and text[-5] in '+-' and text[-4:].isdigit():
        text = f'{text[:-2]}:{text[-2:]}'
    try:
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return ''


def _iterator_timestamp(timestamp):
    """The RFC 3339 time unifiedlog_iterator emits (nanoseconds, 'Z') as aware UTC, or ''."""
    if not timestamp:
        return ''
    normalized = timestamp[:-1] if timestamp.endswith('Z') else timestamp
    if '.' in normalized:
        whole, fraction = normalized.split('.', 1)
        normalized = f'{whole}.{fraction[:6]}'
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _rows_from_json(source_path):
    """Rows from a 'log show --style json' export, which is one JSON array of entries."""
    progress = unifiedlogs.ImportProgress(os.path.getsize(source_path))
    count = 0
    with open(source_path, 'rb') as handle:
        try:
            for record in ijson.items(handle, 'item', multiple_values=True):
                if not isinstance(record, dict):
                    continue
                count += 1
                progress.add_record()
                if count % unifiedlogs.ImportProgress.CHECK_EVERY == 0:
                    progress.set_bytes_done(handle.tell())
                yield (_json_timestamp(record.get('timestamp', '')), count,
                       record.get('processImagePath', ''), record.get('processID', ''),
                       record.get('subsystem', ''), record.get('category', ''),
                       str(record.get('eventMessage', '')), str(record.get('traceID', '')))
        except ijson.JSONError as exc:
            logfunc(f'Unified Logs: the JSON export stopped parsing after {count:,} entries '
                    f'({type(exc).__name__}); the entries before that point were imported')
    progress.finish()


def _rows_from_tracev3(binary, archive_dir):
    """Rows as unifiedlog_iterator decodes them; it emits no trace ID, so that stays blank."""
    count = 0
    for record in unifiedlogs.stream_records(binary, archive_dir):
        count += 1
        yield (_iterator_timestamp(record.get('timestamp', '')), count, record.get('process', ''),
               record.get('pid', ''), record.get('subsystem', ''), record.get('category', ''),
               str(record.get('message', '')), '')


def _log_merge(context, copies, summary):
    """Record in the run log which copies of the log store were read and how they compared."""
    relative = [context.get_relative_path(copy) for copy in copies]
    logfunc(f'Unified Logs: the log store is held in more than one copy ({", ".join(relative)}); '
            f'they were read together as one store')
    for copy, count in summary['only_in'].items():
        noun = 'file is' if count == 1 else 'files are'
        logfunc(f'Unified Logs: {count:,} {noun} only in {context.get_relative_path(copy)}')
    logfunc(f"Unified Logs: comparing the copies of each file the copies share, "
            f"{summary['identical']:,} were identical, {summary['extended']:,} were longer in one "
            f"copy that begins with the other's bytes (the longer was read), and "
            f"{summary['disagreed']:,} differed otherwise (the first copy's file was read)")


@artifact_processor
def macosUnifiedLogs(context):
    files_found = context.get_files_found()
    results = context.create_artifact_result(headers=DATA_HEADERS)

    source_path = get_file_path(files_found, 'logarchive*.json')
    if source_path:
        results.set_source_path(source_path)
        return results.extend(_rows_from_json(source_path))

    logarchive_dir, diagnostics_dir, uuidtext_dir = unifiedlogs.find_archive_roots(files_found)
    if not logarchive_dir and not diagnostics_dir:
        return results

    binary = unifiedlogs.find_iterator()
    if not binary:
        logfunc('Unified Logs: tracev3 data was found but the unifiedlog_iterator binary is not '
                'available, so it was not read. Install the binary (see the artifact '
                'requirements) or supply a logarchive*.json export.')
        return results

    if logarchive_dir:
        archive_dir = source_path = logarchive_dir
    else:
        if not uuidtext_dir:
            logfunc('Unified Logs: tracev3 data was found but no uuidtext directory, so the '
                    'messages cannot be resolved; nothing was imported.')
            return results
        workdir = os.path.join(context.get_data_folder(), '_logarchive_native')
        diagnostics_dirs = unifiedlogs.store_copies(files_found, diagnostics_dir)
        uuidtext_dirs = unifiedlogs.store_copies(files_found, uuidtext_dir)
        if len(diagnostics_dirs) == 1 and len(uuidtext_dirs) == 1:
            archive_dir = unifiedlogs.assemble_archive(diagnostics_dir, uuidtext_dir, workdir)
        else:
            archive_dir, summary = unifiedlogs.assemble_merged_archive(
                diagnostics_dirs, uuidtext_dirs, workdir)
            _log_merge(context, diagnostics_dirs + uuidtext_dirs, summary)
        source_path = '\n'.join(diagnostics_dirs + uuidtext_dirs)

    parser = unifiedlogs.iterator_version(binary) or os.path.basename(binary)
    logfunc(f'Unified Logs: reading tracev3 data with {parser}')
    results.set_source_path(source_path)
    return results.extend(_rows_from_tracev3(binary, archive_dir))


# Artifacts that select entries from the imported table. Each reads the
# macosunifiedlogs table the import above writes into the LAVA database, so
# the import has to run in the same session.

LOG_HEADERS = (('Timestamp (UTC)', 'datetime'), 'Process Image Path', 'Process ID', 'Subsystem',
               'Category', 'Event Message', 'Row Number')


def _log_time(value):
    """The stored timestamp (Unix seconds as the import wrote them) as a UTC datetime."""
    if value in (None, ''):
        return ''
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return ''


def _imported_rows(context, where_clause):
    """Rows of the imported unified log table matching where_clause, oldest first."""
    source_path = get_file_path(context.get_files_found(), '_lava_artifacts.db')
    imported = get_sqlite_db_records(
        source_path, "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'macosunifiedlogs'")
    if not imported:
        logfunc('No imported unified log entries in this run (the Unified Logs artifact found no '
                'log store, or did not run), so there is nothing to select from.')
        return source_path, []
    query = ('SELECT timestamp_utc, process_image_path, process_id, subsystem, category, '
             'event_message, row_number FROM macosunifiedlogs WHERE ' + where_clause +
             ' ORDER BY CAST(row_number AS INTEGER)')
    return source_path, get_sqlite_db_records(source_path, query)


def _selected_entries(context, where_clause):
    source_path, records = _imported_rows(context, where_clause)
    data_list = [(_log_time(r[0]), r[1], r[2], r[3], r[4], r[5], r[6]) for r in records]
    return LOG_HEADERS, data_list, source_path


@artifact_processor
def macosUnifiedLogScreenUnlock(context):
    return _selected_entries(context, """
        (process_image_path LIKE '%/loginwindow'
            AND (event_message LIKE '%loginPressed:] |%Attempt #:%'
                 OR event_message LIKE '%password is CORRECT%'
                 OR event_message LIKE '%Unlock succeeded, with password%'))
        OR (subsystem = 'com.apple.chrono' AND category = 'keybag'
            AND event_message LIKE 'Transition:%')
        OR (process_image_path = '/kernel'
            AND event_message LIKE '%Sending notification for volume%')
        OR (process_image_path LIKE '%/biometrickitd' AND event_message LIKE 'matchResult:timestamp:%')
        OR (process_image_path LIKE '%/coreauthd' AND event_message LIKE '%has received no-match%')
        OR (process_image_path LIKE '%/opendirectoryd'
            AND event_message LIKE 'ODRecordVerifyPassword failed%')
        OR (process_image_path LIKE '%/authorizationhost'
            AND event_message LIKE 'pam_authenticate failed%')
    """)


@artifact_processor
def macosUnifiedLogAuthorization(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/authd'
        AND (event_message LIKE 'Succeeded authorizing right %'
             OR event_message LIKE 'Failed to authorize right %'
             OR event_message LIKE '% authenticated as user % for right %')
    """)


@artifact_processor
def macosUnifiedLogGatekeeper(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/syspolicyd'
        AND (event_message LIKE 'GK performScan:%' OR event_message LIKE 'GK evaluateScanResult:%')
    """)


@artifact_processor
def macosUnifiedLogDiskArbitration(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/diskarbitrationd'
        AND (event_message LIKE 'created disk, id = %'
             OR event_message LIKE 'probed disk, id = %'
             OR event_message LIKE 'mounted disk, id = %'
             OR event_message LIKE 'unmounted disk, id = %'
             OR event_message LIKE 'removed disk, id = %'
             OR event_message LIKE '%dispatched response, id = %approval, disk = %')
    """)


@artifact_processor
def macosUnifiedLogMalwareScans(context):
    return _selected_entries(context, """
        (process_image_path LIKE '%/XProtect'
            AND (event_message LIKE 'Starting system scan%'
                 OR event_message LIKE 'Finished system scan%'
                 OR event_message LIKE 'Launching login scan%'
                 OR event_message LIKE 'Launching startup scan%'))
        OR (process_image_path LIKE '%/MRT' AND event_message LIKE 'Finished MRT run%')
    """)


@artifact_processor
def macosUnifiedLogShutdown(context):
    return _selected_entries(context, """
        (process_image_path LIKE '%/shutdown'
            AND (event_message LIKE 'halt by %' OR event_message LIKE 'reboot by %'))
        OR (process_image_path LIKE '%/reboot' AND event_message LIKE 'rebooted by %')
    """)


@artifact_processor
def macosUnifiedLogSudo(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/sudo' AND event_message LIKE '%COMMAND=%'
    """)


@artifact_processor
def macosUnifiedLogScreenCapture(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/screencapture' AND event_message LIKE 'launched with %'
    """)


@artifact_processor
def macosUnifiedLogIosDevices(context):
    return _selected_entries(context, """
        (process_image_path LIKE '%/usbmuxd'
         AND (event_message LIKE '%device connected:%'
             OR event_message LIKE '%device disconnected:%'
             OR event_message LIKE 'Successfully paired%'
             OR event_message LIKE 'Failed to pair%'
             OR event_message LIKE 'Could not pair with the device%'))
        OR event_message LIKE '%Device attached over direct/cable:%'
    """)


@artifact_processor
def macosUnifiedLogSleepWake(context):
    return _selected_entries(context, """
        (process_image_path = '/kernel'
            AND (event_message LIKE 'PMRD: kIOMessageSystemWillSleep[%] to pid %, loginwindow%'
                 OR event_message LIKE 'PMRD: kIOMessageSystemWillPowerOn to pid %, loginwindow%'
                 OR event_message LIKE '%Wake reason: %'))
        OR (process_image_path LIKE '%/powerd' AND event_message LIKE 'Wake reason:%')
    """)


@artifact_processor
def macosUnifiedLogUsbMassStorage(context):
    return _selected_entries(context, """
        process_image_path = '/kernel' AND event_message LIKE 'USBMSC Identifier%'
    """)


@artifact_processor
def macosUnifiedLogLoginSessions(context):
    return _selected_entries(context, """
        process_image_path LIKE '%/loginwindow'
        AND (event_message LIKE '%Login Window Application Started%'
             OR event_message LIKE '%sendDistributedNotification: com.apple.sessionDidLogin%'
             OR event_message LIKE '%startLogout%logoutType:%')
    """)


# Battery Center writes each power source as an NSDictionary description ('key = value;' lines
# between braces) and each device as '<BCBatteryDevice: 0x...; key = value; ...>'.

_BC_PAIR = re.compile(r'^\s*("(?:[^"\\]|\\.)*"|[^\s=;"]+)\s*=\s*("(?:[^"\\]|\\.)*"|[^;"]*);\s*$')
_BC_OPEN = re.compile(r'^("(?:[^"\\]|\\.)*"|[^\s=;"]+)\s*=\s*([{(])$')
_BC_ESCAPE = re.compile(r'\\(U[0-9a-fA-F]{4}|.)', re.DOTALL)
_BC_ESCAPED = {'n': '\n', 't': '\t', 'r': '\r'}
_BC_DEVICE = re.compile(r'Found device: <BCBatteryDevice: 0x[0-9a-fA-F]+; (.*?);?\s*>\s*$', re.DOTALL)
_BC_DEVICE_SPLIT = re.compile(r'; (?=\w+ ?=)')
_BC_DEVICE_PAIR = re.compile(r'^(\w+) ?= ?(.*)$', re.DOTALL)

_BC_SOURCE_KEYS = ('Name', 'Type', 'Transport Type', 'Power Source State', 'Current Capacity',
                   'Max Capacity', 'Is Charging', 'Is Present', 'Accessory Identifier',
                   'Accessory Category', 'Hardware Serial Number', 'Vendor ID', 'Product ID',
                   'Power Source ID')
_BC_DEVICE_KEYS = ('name', 'groupName', 'vendor', 'modelNumber', 'percentCharge', 'charging',
                   'connected', 'internal', 'poweredSoureState', 'transportType',
                   'accessoryIdentifier', 'accessoryCategory', 'identifier', 'productIdentifier')


def _bc_unquote(text):
    """A value or key of an NSDictionary description without its quotes and escapes."""
    text = text.strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return text

    def unescape(match):
        token = match.group(1)
        if token[0] == 'U' and len(token) == 5:
            return chr(int(token[1:], 16))
        return _BC_ESCAPED.get(token, token)
    return _BC_ESCAPE.sub(unescape, text[1:-1])


def _bc_source_pairs(message):
    """(pairs, leftover) of a 'Found power source: {...}' entry; leftover is what did not parse.

    A value that is itself a dictionary or a list spans several lines. It is kept as one
    value, its lines as logged, so a key inside it is never read as a key of the power
    source. The log cuts a long entry short, so the closing brace is not required: what was
    logged before the cut is still split, and a line cut in half goes to leftover.
    """
    start = message.find('{')
    if start < 0:
        return [], message.strip()
    pairs = []
    leftover = []
    key = None      # the key of the nested value being read, if any
    opener = ''
    depth = 0
    lines = []
    for line in message[start + 1:].splitlines():
        text = line.strip()
        if not text:
            continue
        if key is not None:
            if text[-1] in '{(':
                depth += 1
            elif text.rstrip(';') in ('}', ')'):
                if depth == 0:
                    pairs.append((key, opener + ' '.join(lines) + text.rstrip(';')))
                    key = None
                    continue
                depth -= 1
            lines.append(text)
            continue
        if text == '}':
            break
        match = _BC_OPEN.match(text)
        if match:
            key, opener, depth, lines = _bc_unquote(match.group(1)), match.group(2), 0, []
            continue
        match = _BC_PAIR.match(line)
        if match:
            pairs.append((_bc_unquote(match.group(1)), _bc_unquote(match.group(2))))
        else:
            leftover.append(text)
    if key is not None:
        pairs.append((key, opener + ' '.join(lines)))
    return pairs, ' '.join(leftover)


def _bc_device_pairs(message):
    """(pairs, leftover) of a 'Found device: <BCBatteryDevice: ...>' entry."""
    match = _BC_DEVICE.search(message)
    if not match:
        return [], message.strip()
    pairs = []
    leftover = []
    for piece in _BC_DEVICE_SPLIT.split(match.group(1)):
        pair = _BC_DEVICE_PAIR.match(piece)
        if pair:
            pairs.append((pair.group(1), pair.group(2).strip()))
        else:
            leftover.append(piece.strip())
    return pairs, '; '.join(leftover)


def _bc_row(pairs, leftover, shown_keys):
    """The shown keys' values in order, then every pair not shown and anything unparsed."""
    shown = {}
    other = []
    for key, value in pairs:
        if key in shown_keys and key not in shown:
            shown[key] = value
        else:
            other.append(f'{key} = {value}')
    if leftover:
        other.append(leftover)
    return tuple(shown.get(key, '') for key in shown_keys) + ('; '.join(other),)


def _bc_entries(context, where_clause, pairs_of, shown_keys):
    source_path, records = _imported_rows(context, where_clause)
    data_list = []
    for record in records:
        pairs, leftover = pairs_of(record[5] or '')
        data_list.append((_log_time(record[0]),) + _bc_row(pairs, leftover, shown_keys)
                         + (record[1], record[2], record[6]))
    return data_list, source_path


@artifact_processor
def macosUnifiedLogBatteryCenterSources(context):
    data_list, source_path = _bc_entries(context, """
        subsystem = 'com.apple.BatteryCenter' AND event_message LIKE '%Found power source: {%'
    """, _bc_source_pairs, _BC_SOURCE_KEYS)
    data_headers = (('Timestamp (UTC)', 'datetime'),) + _BC_SOURCE_KEYS + (
        'Other Values', 'Process Image Path', 'Process ID', 'Row Number')
    return data_headers, data_list, source_path


@artifact_processor
def macosUnifiedLogBatteryCenterDevices(context):
    data_list, source_path = _bc_entries(context, """
        subsystem = 'com.apple.BatteryCenter'
        AND event_message LIKE '%Found device: <BCBatteryDevice:%'
    """, _bc_device_pairs, _BC_DEVICE_KEYS)
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Name', 'Group Name', 'Vendor', 'Model Number',
                    'Percent Charge', 'Charging', 'Connected', 'Internal', 'Power Source State',
                    'Transport Type', 'Accessory Identifier', 'Accessory Category', 'Identifier',
                    'Product Identifier', 'Other Values', 'Process Image Path', 'Process ID',
                    'Row Number')
    return data_headers, data_list, source_path


_TCC_PATTERNS = {
    'ctx': re.compile(r'^AUTHREQ_CTX: msgID=([\d.]+), function=([^,]*), service=([^,]*), '
                      r'preflight=([^,]*)'),
    'subject': re.compile(r'^AUTHREQ_SUBJECT: msgID=([\d.]+), subject=(.*?),?\s*$'),
    'attribution': re.compile(r'^AUTHREQ_ATTRIBUTION: msgID=([\d.]+), attribution=\{(\w+)=\{'
                              r'TCCDProcess: identifier=([^,]*),.*?'
                              r'(?:binary_path|responsible_path)=([^}]*)\}'),
    'result': re.compile(r'^AUTHREQ_RESULT: msgID=([\d.]+), authValue=(\d+), authReason=(\d+)'),
}


@artifact_processor
def macosUnifiedLogTCCRequests(context):
    source_path, records = _imported_rows(context, """
        process_image_path LIKE '%/tccd' AND event_message LIKE 'AUTHREQ_%'
    """)
    requests = {}
    order = []
    for record in records:
        message = record[5] or ''
        for kind, pattern in _TCC_PATTERNS.items():
            match = pattern.match(message)
            if not match:
                continue
            key = (record[2], match.group(1))
            if key not in requests:
                requests[key] = {'first': record}
                order.append(key)
            entry = requests[key]
            entry.setdefault(kind, match.groups()[1:])
            if kind == 'result':
                entry.setdefault('result_record', record)
            break
    data_list = []
    for key in order:
        entry = requests[key]
        timed = entry.get('result_record', entry['first'])
        ctx = entry.get('ctx', ('', '', ''))
        attribution = entry.get('attribution', ('', '', ''))
        result = entry.get('result', ('', ''))
        data_list.append((_log_time(timed[0]), ctx[1], entry.get('subject', ('',))[0],
                          attribution[0], attribution[1], attribution[2].strip(), ctx[2],
                          result[0], result[1], ctx[0], key[0], key[1], timed[6]))
    data_headers = (('Timestamp (UTC)', 'datetime'), 'Service', 'Subject', 'Attribution Role',
                    'Attribution Identifier', 'Attribution Path', 'Preflight',
                    'Auth Value (as stored)', 'Auth Reason (as stored)', 'Function', 'tccd PID',
                    'Message ID', 'Row Number')
    return data_headers, data_list, source_path
