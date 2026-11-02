"""Windows Component-Based Servicing (CBS) and DISM text log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it as CbsPersist_*.log and
CbsPersist_*.cab, Windows\\Panther\\cbs.log and Windows\\Logs\\DISM\\dism.log. Each line begins
with a local time, a level and a component. The CBS logs also write a "Universal Time is" line
in the lines that follow a TrustedInstaller start, which is how the CBS rows get a UTC time;
dism.log writes no such line, so its times are reported as recorded.
"""

import datetime
import re
import struct
import zlib
from collections import Counter

from scripts.cabinet import cab_member
from scripts.ilapfuncs import artifact_processor, logfunc

__artifacts_v2__ = {
    "windowsCbsTrustedInstallerStarts": {
        "name": "CBS TrustedInstaller Starts",
        "description": "Each TrustedInstaller start the CBS logs record, with the last boot time the log writes at that start "
                       "and the UTC offset the log's own UTC line gives.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it (CbsPersist_<date>.log and "
                 "CbsPersist_<date>.cab, the names seen on the tested images) and Windows\\Panther\\cbs.log. Microsoft "
                 "names %windir%\\Logs\\CBS\\CBS.log as the log DISM writes "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/installing-updates-features-roles/fix-windows-update-errors). "
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are not "
                 "read: continuation lines, CSIPERF lines, and lines that carry a time and a level but no component. A "
                 "cab is read by scripts/cabinet.py when it holds one folder and one file, compressed with MSZIP or LZX: "
                 "the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)), MSZIP follows [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69), "
                 "and LZX follows the LZX section of the cabinet document except at three points where Windows' own "
                 "makecab.exe writes differently, which that module names and its tests pin against makecab output. The "
                 "recorded sizes are checked, and a cab that fails is named in the run log and not read. The six cabs on "
                 "the corpus images were MSZIP and the one on windows11_arm_cbs_known_20261101 (Windows 11 build 26200) "
                 "was LZX with a 2 MiB window; all seven were read, and the LZX one decoded to the same bytes as bsdtar "
                 "3.5.3 (libarchive 3.7.4) gave. Times: each line's time is local and carries no zone. The CBS logs also "
                 "write a line 'Universal Time is: <time>' in the lines after a TrustedInstaller start (on the tested "
                 "images 12 to 29 timed lines after it, most often 18, and 9 times before the first start of a file), and "
                 "the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- Initializing "
                 "Trusted Installer ---' line to the next, and each row takes the offset of the last UTC line before it "
                 "in its run, or of the run's first UTC line when none comes before it. A run with no UTC line leaves the "
                 "UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no UTC line and no "
                 "TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC lines with three "
                 "offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the package state "
                 "lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), the CSI lines "
                 "other than the '[SR]' lines (which CBS SFP Verify and Repair Runs reads), the lines of a store scan "
                 "report other than its Summary values (which CBS Store Corruption Scans reads), the 'Session ... "
                 "finalized' lines, the DISM lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and "
                 "the ETL files in Logs\\WindowsUpdate and Logs\\CBS. One row per 'TI: --- Initializing Trusted Installer "
                 "---' line, with the first 'TI: Last boot time' and 'Loaded Servicing Stack' lines of its run. Last Boot "
                 "Time is written as a local time; it is moved to UTC with the run's offset. Checked against Kernel Boot "
                 "Events on the six tested images that have kernel boot events and an offset other than UTC+00:00 "
                 "(alihadi_threatsim_server2019 has no kernel boot event, so it was not checked): 142 of the 149 starts "
                 "with a boot time and an offset fell within 2 minutes of a kernel boot event once the offset was "
                 "applied, and none did when the time was read as UTC. Of the other 7, 6 name a boot earlier than the "
                 "first kernel boot event the image holds, and 1 on szechuan_win10 had no kernel boot event within 17 "
                 "minutes. On lonewolf_win10 one boot was named at UTC-07:00 and later at UTC-04:00, and both give the "
                 "same UTC time. Start Time (UTC) and UTC Offset (from the log) were blank on 12 of the 443 tested rows "
                 "(7 on lonewolf_win10, 3 on hexordia_mvs2025_win11, 1 on szechuan_win10 and 1 on "
                 "windows11_arm_cbs_known_20261101), and on all 12 the run had no Servicing Stack line either. UTC Offset "
                 "(from the log) held one value on all rows of pc_mus_001_win11, szechuan_dc01_server2012r2, "
                 "ou_ransomware_server2022 and alihadi_threatsim_server2019, and two values besides blank on "
                 "af_case2_win10, lonewolf_win10, hexordia_mvs2025_win11 and windows11_arm_cbs_known_20261101. Servicing "
                 "Stack Version held one value on all rows of szechuan_dc01_server2012r2, ou_ransomware_server2022 and "
                 "alihadi_threatsim_server2019.",
        "paths": ('*/Windows/Logs/CBS/CBS.log', '*/Windows/Logs/CBS/CbsPersist_*.log',
                  '*/Windows/Logs/CBS/CbsPersist_*.cab', '*/Windows/Panther/cbs.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "power",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 35 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 23 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 39 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 6 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 6 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (its CBS logs write no TrustedInstaller start line)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 51 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (only Windows\\Panther\\cbs.log, which holds no TrustedInstaller start line)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 246 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 6 rows",
            "windows11_arm_cbs_known_20261101": "Windows 11 build 26200 (ARM64) | 31 rows",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no CBS or DISM log)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
        },
    },
    "windowsCbsSessions": {
        "name": "CBS Servicing Sessions",
        "description": "Each servicing session the CBS logs record as initialized, with the session ID and the client named on "
                       "the line.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it (CbsPersist_<date>.log and "
                 "CbsPersist_<date>.cab, the names seen on the tested images) and Windows\\Panther\\cbs.log. Microsoft "
                 "names %windir%\\Logs\\CBS\\CBS.log as the log DISM writes "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/installing-updates-features-roles/fix-windows-update-errors). "
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are not "
                 "read: continuation lines, CSIPERF lines, and lines that carry a time and a level but no component. A "
                 "cab is read by scripts/cabinet.py when it holds one folder and one file, compressed with MSZIP or LZX: "
                 "the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)), MSZIP follows [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69), "
                 "and LZX follows the LZX section of the cabinet document except at three points where Windows' own "
                 "makecab.exe writes differently, which that module names and its tests pin against makecab output. The "
                 "recorded sizes are checked, and a cab that fails is named in the run log and not read. The six cabs on "
                 "the corpus images were MSZIP and the one on windows11_arm_cbs_known_20261101 (Windows 11 build 26200) "
                 "was LZX with a 2 MiB window; all seven were read, and the LZX one decoded to the same bytes as bsdtar "
                 "3.5.3 (libarchive 3.7.4) gave. Times: each line's time is local and carries no zone. The CBS logs also "
                 "write a line 'Universal Time is: <time>' in the lines after a TrustedInstaller start (on the tested "
                 "images 12 to 29 timed lines after it, most often 18, and 9 times before the first start of a file), and "
                 "the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- Initializing "
                 "Trusted Installer ---' line to the next, and each row takes the offset of the last UTC line before it "
                 "in its run, or of the run's first UTC line when none comes before it. A run with no UTC line leaves the "
                 "UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no UTC line and no "
                 "TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC lines with three "
                 "offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the package state "
                 "lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), the CSI lines "
                 "other than the '[SR]' lines (which CBS SFP Verify and Repair Runs reads), the lines of a store scan "
                 "report other than its Summary values (which CBS Store Corruption Scans reads), the 'Session ... "
                 "finalized' lines, the DISM lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and "
                 "the ETL files in Logs\\WindowsUpdate and Logs\\CBS. One row per 'Session: <ID> initialized by client "
                 "<client>' line of the CBS component, with the client as the line names it (the text after it from ', "
                 "external staging directory' on, and a trailing period, are dropped). The Session ID is reported as "
                 "stored; what its two numbers are is not established here. 2,688 rows on the tested images, naming 19 "
                 "clients, of which WindowsUpdateAgent was the most common (1,605 rows). Session Start (UTC) and UTC "
                 "Offset (from the log) are empty on all 30 rows of cfreds_leakage_win7, whose logs write no UTC line. "
                 "UTC Offset (from the log) held one value on all rows of pc_mus_001_win11 and "
                 "szechuan_dc01_server2012r2, and four on alihadi_threatsim_server2019. A session line records that the "
                 "session was initialized, not what it changed.",
        "paths": ('*/Windows/Logs/CBS/CBS.log', '*/Windows/Logs/CBS/CbsPersist_*.log',
                  '*/Windows/Logs/CBS/CbsPersist_*.cab', '*/Windows/Panther/cbs.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "layers",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 165 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 130 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1167 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 20 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 19 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 30 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 210 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (only Windows\\Panther\\cbs.log, which holds no session line)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 707 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 27 rows",
            "windows11_arm_cbs_known_20261101": "Windows 11 build 26200 (ARM64) | 213 rows",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no CBS or DISM log)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
        },
    },
    "windowsCbsSfpRuns": {
        "name": "CBS SFP Verify and Repair Runs",
        "description": "Each run of SFP verify and repair transactions the CBS logs record after a request for the SFP repair "
                       "object, with the counts of transactions and components and the files the log names as corrupt or "
                       "repaired.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it (CbsPersist_<date>.log and "
                 "CbsPersist_<date>.cab, the names seen on the tested images) and Windows\\Panther\\cbs.log. Microsoft "
                 "names %windir%\\Logs\\CBS\\CBS.log as the log DISM writes "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/installing-updates-features-roles/fix-windows-update-errors). "
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are not "
                 "read: continuation lines, CSIPERF lines, and lines that carry a time and a level but no component. A "
                 "cab is read by scripts/cabinet.py when it holds one folder and one file, compressed with MSZIP or LZX: "
                 "the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)), MSZIP follows [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69), "
                 "and LZX follows the LZX section of the cabinet document except at three points where Windows' own "
                 "makecab.exe writes differently, which that module names and its tests pin against makecab output. The "
                 "recorded sizes are checked, and a cab that fails is named in the run log and not read. The six cabs on "
                 "the corpus images were MSZIP and the one on windows11_arm_cbs_known_20261101 (Windows 11 build 26200) "
                 "was LZX with a 2 MiB window; all seven were read, and the LZX one decoded to the same bytes as bsdtar "
                 "3.5.3 (libarchive 3.7.4) gave. Times: each line's time is local and carries no zone. The CBS logs also "
                 "write a line 'Universal Time is: <time>' in the lines after a TrustedInstaller start (on the tested "
                 "images 12 to 29 timed lines after it, most often 18, and 9 times before the first start of a file), and "
                 "the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- Initializing "
                 "Trusted Installer ---' line to the next, and each row takes the offset of the last UTC line before it "
                 "in its run, or of the run's first UTC line when none comes before it. A run with no UTC line leaves the "
                 "UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no UTC line and no "
                 "TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC lines with three "
                 "offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the package state "
                 "lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), the CSI lines "
                 "other than the '[SR]' lines (which CBS SFP Verify and Repair Runs reads), the lines of a store scan "
                 "report other than its Summary values (which CBS Store Corruption Scans reads), the 'Session ... "
                 "finalized' lines, the DISM lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and "
                 "the ETL files in Logs\\WindowsUpdate and Logs\\CBS. One row per 'TiWorker: Client requests SFP repair "
                 "object.' line of the CBS component, with the CSI '[SR]' lines and the DEPLOY '[Pnp] Corrupt file' and "
                 "'[Pnp] Repaired file' lines after it, up to the next such request or TrustedInstaller start. [SR] or "
                 "[Pnp] lines with no request before them in their run get a row of their own that starts at the first of "
                 "them, and the run log counts such rows; none was seen. Verify Transactions counts the '[SR] Beginning "
                 "Verify and Repair transaction' lines, Components Verified sums the N of the '[SR] Verifying N "
                 "components' lines, Repair Passes counts the '[SR] Repairing N components' lines and Components Repaired "
                 "sums their N; Files Reported Corrupt and Files Reported Repaired are the paths of the [Pnp] lines, one "
                 "per line. Last Line Time is the time of the last of these lines. Known data, "
                 "windows11_arm_cbs_known_20261101: sfc /verifyonly and then sfc /scannow, run on the VM with their start "
                 "and end stamped in UTC, gave one row each, and each row's Start Time (UTC) falls in the same second as "
                 "the stamped start of its command and its Last Line Time (UTC) before the stamped end (the log writes "
                 "whole seconds). The /verifyonly row has 173 transactions, 17,214 components verified and no repair "
                 "pass; the /scannow row has 174 transactions, 17,214 components verified and one repair pass. Both name "
                 "one file as corrupt and only the /scannow row names it as repaired; sfc printed that it found integrity "
                 "violations and that it found corrupt files and repaired them. On that row the '[SR] Repairing' line "
                 "names 0 components while a '[Pnp] Repaired file' line names the file, so Components Repaired held 0 and "
                 "Files Reported Repaired held one path. The lines do not name the command that started a run; on the "
                 "known data only /scannow wrote a repair pass. A run that finds a file it cannot repair was not "
                 "produced. The CbsPersist cab of windows11_arm_cbs_known_20261101 gave a third row on that key, with 46 "
                 "transactions, from before the sfc runs. Corpus images: hexordia_mvs2025_win11 gave 3 rows, one with 46 "
                 "transactions and two from its CbsPersist cab with no [SR] line after the request (Verify Transactions "
                 "0), and lonewolf_win10 gave 1 row with 4 transactions. On those 4 rows and on the cab row of "
                 "windows11_arm_cbs_known_20261101 each transaction verified one component, so Verify Transactions and "
                 "Components Verified are identical, Repair Passes held 0 on all 5 rows, Components Repaired held 0 on "
                 "all 5 rows, and Files Reported Corrupt and Files Reported Repaired were empty on all 5. What started "
                 "those runs is not established.",
        "paths": ('*/Windows/Logs/CBS/CBS.log', '*/Windows/Logs/CBS/CbsPersist_*.log',
                  '*/Windows/Logs/CBS/CbsPersist_*.cab', '*/Windows/Panther/cbs.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 3 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (only Windows\\Panther\\cbs.log, which holds no SFP repair object request)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows",
            "windows11_arm_cbs_known_20261101": "Windows 11 build 26200 (ARM64) | 3 rows",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no CBS or DISM log)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
        },
    },
    "windowsCbsStoreScans": {
        "name": "CBS Store Corruption Scans",
        "description": "Each component store corruption report the CBS logs hold, with the operation, its result and the totals "
                       "of corruption detected and repaired, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it (CbsPersist_<date>.log and "
                 "CbsPersist_<date>.cab, the names seen on the tested images) and Windows\\Panther\\cbs.log. Microsoft "
                 "names %windir%\\Logs\\CBS\\CBS.log as the log DISM writes "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/installing-updates-features-roles/fix-windows-update-errors). "
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are not "
                 "read: continuation lines, CSIPERF lines, and lines that carry a time and a level but no component. A "
                 "cab is read by scripts/cabinet.py when it holds one folder and one file, compressed with MSZIP or LZX: "
                 "the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)), MSZIP follows [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69), "
                 "and LZX follows the LZX section of the cabinet document except at three points where Windows' own "
                 "makecab.exe writes differently, which that module names and its tests pin against makecab output. The "
                 "recorded sizes are checked, and a cab that fails is named in the run log and not read. The six cabs on "
                 "the corpus images were MSZIP and the one on windows11_arm_cbs_known_20261101 (Windows 11 build 26200) "
                 "was LZX with a 2 MiB window; all seven were read, and the LZX one decoded to the same bytes as bsdtar "
                 "3.5.3 (libarchive 3.7.4) gave. Times: each line's time is local and carries no zone. The CBS logs also "
                 "write a line 'Universal Time is: <time>' in the lines after a TrustedInstaller start (on the tested "
                 "images 12 to 29 timed lines after it, most often 18, and 9 times before the first start of a file), and "
                 "the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- Initializing "
                 "Trusted Installer ---' line to the next, and each row takes the offset of the last UTC line before it "
                 "in its run, or of the run's first UTC line when none comes before it. A run with no UTC line leaves the "
                 "UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no UTC line and no "
                 "TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC lines with three "
                 "offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the package state "
                 "lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), the CSI lines "
                 "other than the '[SR]' lines (which CBS SFP Verify and Repair Runs reads), the lines of a store scan "
                 "report other than its Summary values (which CBS Store Corruption Scans reads), the 'Session ... "
                 "finalized' lines, the DISM lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and "
                 "the ETL files in Logs\\WindowsUpdate and Logs\\CBS. One row per 'Checking System Update Readiness.' "
                 "line of the CBS component, with the first 'Operation', 'Operation result', 'Total Detected Corruption', "
                 "'Total Repaired Corruption' and 'Total Operation Time' lines after it in its run, as stored. Session ID "
                 "and Session Start come from the last 'Session(... Store Corruption Detect/Repair): <ID>' line before it "
                 "in its run, blank when there is none. Microsoft's page cited above shows this Summary block as an "
                 "example of the log after the DISM commands it describes, with 'Operation: Detect and Repair'. Known "
                 "data, windows11_arm_cbs_known_20261101: DISM /Online /Cleanup-Image /ScanHealth gave one row, Operation "
                 "'Detect only', result 0x0, 816 detected, 0 repaired and 112 seconds, with Session Start (UTC) in the "
                 "same second as the stamped start of the command and Summary Time (UTC) before its stamped end (the log "
                 "writes whole seconds); DISM printed that the component store is repairable. DISM /CheckHealth, run just "
                 "before, wrote no such block, only a session line (reported by CBS Servicing Sessions). RestoreHealth "
                 "was not run, so a 'Detect and Repair' row is untested. The per-item lines of the report (816 '(p) CSI "
                 "Payload Corrupt' lines on the known data) are not read. None of the 13 corpus images holds the block.",
        "paths": ('*/Windows/Logs/CBS/CBS.log', '*/Windows/Logs/CBS/CbsPersist_*.log',
                  '*/Windows/Logs/CBS/CbsPersist_*.cab', '*/Windows/Panther/cbs.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (only Windows\\Panther\\cbs.log, which holds no store scan report)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows",
            "windows11_arm_cbs_known_20261101": "Windows 11 build 26200 (ARM64) | 1 row",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no CBS or DISM log)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
        },
    },
    "windowsDismSessions": {
        "name": "DISM Sessions",
        "description": "Each Dism.exe and DismApi.dll session dism.log records, with the command line Dism.exe logs as executed "
                       "or the parent process command line DismApi.dll logs.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows\\Logs\\DISM\\dism.log. One row per '<----- Starting Dism.exe session ----->' or '<----- "
                 "Starting DismApi.dll session ----->' line. Command Line is the first 'DISM.EXE: Executing command line' "
                 "line of a Dism.exe session and is written only in those sessions; Parent Process Command Line is the "
                 "first 'DismApi.dll: Parent process command line' line of a DismApi.dll session, matched to its session "
                 "by the PID on the line, and is written only in those. Process ID is the PID of the DismApi.dll lines, "
                 "or for Dism.exe the first 'PID=' on a line of the session other than the 'Parent process PID=' of the "
                 "'Instance information' line that Windows 11 writes (on hexordia_mvs2025_win11 and "
                 "windows11_arm_cbs_known_20261101, all 18 Dism.exe sessions); which process that PID names is not "
                 "established here, and the Instance information line is not read. Reboot Required (as stored) is the "
                 "value of the 'Image session has been closed. Reboot required=' line, written only in Dism.exe sessions "
                 "(14 yes and 19 no on the tested images, and blank on one Dism.exe session on "
                 "windows11_arm_cbs_known_20261101). The Dism.exe start and end lines carry no PID, so one Dism.exe "
                 "session is kept open at a time: when a second starts before the first has ended, as once on "
                 "windows11_arm_cbs_known_20261101 (starts 2 seconds apart), the first is reported with no end time and "
                 "no reboot value, the second takes the next ending line, and the run log counts it. End Time is the "
                 "session's ending line, blank when there is none or when it could not be paired: 16 rows on the tested "
                 "images, 3 each on pc_mus_001_win11, szechuan_dc01_server2012r2, ou_ransomware_server2022 and "
                 "alihadi_threatsim_server2019 and 4 on windows11_arm_cbs_known_20261101 (3 DismApi.dll sessions with no "
                 "ending line and the overlapped Dism.exe session above); the run log counts them. Times are local, as "
                 "recorded: dism.log writes no zone and no UTC line. The CBS artifacts give the offset the CBS logs "
                 "recorded, which this artifact does not apply. 3,385 rows on the tested images, 34 Dism.exe sessions "
                 "(each with a Command Line) and 3,351 DismApi.dll sessions (each with a Parent Process Command Line); "
                 "3,179 of the DismApi.dll sessions were on ou_ransomware_server2022. Session Kind held one value on all "
                 "rows of pc_mus_001_win11, af_case2_win10, lonewolf_win10, szechuan_win10 and cfreds_leakage_win7, so "
                 "Command Line and Reboot Required (as stored) are empty on the first four and Parent Process Command "
                 "Line on the last. Not read: the other dism.log lines, and the DISM lines Windows\\Panther\\cbs.log "
                 "holds.",
        "paths": ('*/Windows/Logs/DISM/dism.log',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "terminal",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 12 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 9 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 38 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 12 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 31 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no dism.log)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 3180 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 13 rows",
            "windows11_arm_cbs_known_20261101": "Windows 11 build 26200 (ARM64) | 84 rows",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no CBS or DISM log)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 (ARM64) | 0 rows (the extraction holds no CBS or DISM log)",
        },
    },
}

_LINE = re.compile(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d), (\w+)\s+(\S+)\s+(.*)')
_UTC = re.compile(r'Universal Time is: (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)')
_TI_START = 'TI: --- Initializing Trusted Installer ---'
_LAST_BOOT = re.compile(r'TI: Last boot time: (.*)')
_STACK = re.compile(r'Loaded Servicing Stack (v\S+)')
_SESSION = re.compile(r'Session: (\S+) initialized by client (.*?)(?:, external staging directory:.*)?$')
_SFP_REQUEST = 'TiWorker: Client requests SFP repair object.'
_SR = re.compile(r'\[SR\] ((Verifying|Repairing) (\d+) components|Beginning Verify and Repair transaction|Verify complete|'
                 r'Repair complete)')
_PNP_FILE = re.compile(r'\[Pnp\] (Corrupt|Repaired) file: (.*)')
_STORE_CHECK = 'Checking System Update Readiness.'
_STORE_SESSION = re.compile(r'Session\(.*Store Corruption Detect/Repair\): (\S+)')
_SUMMARY = (('operation', re.compile(r'Operation:\s+(.*)')), ('result', re.compile(r'Operation result:\s+(.*)')),
            ('detected', re.compile(r'Total Detected Corruption:\s+(\d+)')),
            ('repaired', re.compile(r'Total Repaired Corruption:\s+(\d+)')),
            ('seconds', re.compile(r'Total Operation Time:\s+(\d+) seconds')))
_PID = re.compile(r'(?<!Parent process )\bPID=(\d+)')
_DISM_EXE_START = 'DISM.EXE: <----- Starting Dism.exe session ----->'
_DISM_EXE_END = 'DISM.EXE: <----- Ending Dism.exe session ----->'
_DISM_API_START = 'DismApi.dll: <----- Starting DismApi.dll session ----->'
_DISM_API_END = 'DismApi.dll: <----- Ending DismApi.dll session ----->'
_EXECUTING = re.compile(r'DISM\.EXE: Executing command line: (.*)')
_PARENT = re.compile(r'DismApi\.dll: Parent process command line: (.*?)(?: - DismInitializeInternal)?$')
_REBOOT = re.compile(r'Image session has been closed\. Reboot required=(\S+?)\.?$')

def log_text(path):
    """The text of a log, or of the log a CbsPersist cab holds, and what was replaced on decoding."""
    with open(path, 'rb') as handle:
        data = handle.read()
    if path.lower().endswith('.cab'):
        _, data = cab_member(data)
    text = data.decode('utf-8-sig', errors='replace')
    return text, text.count('\ufffd')


def log_lines(text):
    """(local time text, component, message) for every line that begins with a time."""
    for line in text.splitlines():
        match = _LINE.match(line.lstrip('﻿'))
        if match:
            yield match.group(1), match.group(3), match.group(4).rstrip()


def _offset_text(minutes):
    sign = '+' if minutes >= 0 else '-'
    hours, mins = divmod(abs(minutes), 60)
    return f'UTC{sign}{hours:02d}:{mins:02d}'


def _utc(local, minutes):
    """A local time as the log writes it ("2023-02-20 15:30:47", with or without ".500"), moved to UTC by the
    offset in minutes; blank when there is no offset or the text is not such a time."""
    if minutes is None or not local:
        return ''
    try:
        when = datetime.datetime.strptime(local, '%Y-%m-%d %H:%M:%S.%f' if '.' in local else '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return ''
    return (when - datetime.timedelta(minutes=minutes)).replace(tzinfo=datetime.timezone.utc)


def placed_lines(text, problems):
    """(local, component, message, offset in minutes or None) for every timed line of a CBS log.

    A run is the lines from one "Initializing Trusted Installer" line to the next (the lines before
    the first are a run of their own). A line takes the offset of the last UTC line before it in its
    run, or the run's first UTC line when none comes before it; a run with none gives None. The UTC
    lines themselves are left out.
    """
    runs = [[]]
    for local, component, message in log_lines(text):
        if component == 'CBS' and message == _TI_START:
            runs.append([])
        runs[-1].append((local, component, message))
    placed = []
    for run in runs:
        offsets = []
        for local, _, message in run:
            match = _UTC.search(message)
            if match:
                delta = datetime.datetime.strptime(local, '%Y-%m-%d %H:%M:%S') - \
                    datetime.datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                offsets.append(round(delta.total_seconds() / 60))
        if len(set(offsets)) > 1:
            problems['TrustedInstaller runs whose UTC lines give more than one offset'] += 1
        current = offsets[0] if offsets else None
        seen = 0
        for local, component, message in run:
            if _UTC.search(message):
                current = offsets[seen]
                seen += 1
                continue
            placed.append((local, component, message, current))
    return placed


def cbs_events(text, problems):
    """The TrustedInstaller starts and the sessions of one CBS log, each with its UTC offset."""
    starts, sessions = [], []
    start = {}
    for local, component, message, current in placed_lines(text, problems):
        if component != 'CBS':
            continue
        boot = _LAST_BOOT.match(message)
        stack = _STACK.match(message)
        session = _SESSION.match(message)
        if message == _TI_START:
            start = {'local': local, 'offset': current, 'boot': '', 'stack': ''}
            starts.append(start)
        elif boot and start and not start['boot']:
            start['boot'] = boot.group(1)
        elif stack and start and not start['stack']:
            start['stack'] = stack.group(1)
        elif session:
            sessions.append((local, current, session.group(1), session.group(2).rstrip('.')))
    unplaced = sum(1 for start in starts if start['offset'] is None)
    if unplaced:
        problems['TrustedInstaller starts with no UTC line in their run, UTC left blank'] += unplaced
    return starts, sessions


def cbs_checks(text, problems):
    """The SFP verify and repair runs and the store corruption scans of one CBS log.

    An SFP run starts at a "Client requests SFP repair object" line and takes the [SR] lines and the
    [Pnp] corrupt and repaired file lines after it, up to the next such request or TrustedInstaller
    start. A store scan starts at a "Checking System Update Readiness." line and takes the Summary
    values after it; its session is the last "Store Corruption Detect/Repair" session started before it.
    """
    runs, scans = [], []
    run = scan = None
    store_session = ('', '')
    for local, component, message, current in placed_lines(text, problems):
        if component == 'CBS' and message == _TI_START:
            run = scan = None
            store_session = ('', '')
            continue
        if component == 'CBS' and message == _SFP_REQUEST:
            run = {'local': local, 'offset': current, 'last': local, 'transactions': 0, 'verified': 0,
                   'repairs': 0, 'repaired': 0, 'corrupt_files': [], 'repaired_files': []}
            runs.append(run)
            continue
        sr = _SR.search(message) if component == 'CSI' else None
        pnp = _PNP_FILE.match(message) if component == 'DEPLOY' else None
        if sr or pnp:
            if run is None:
                problems['runs of [SR] or [Pnp] lines with no SFP repair object request before them'] += 1
                run = {'local': local, 'offset': current, 'last': local, 'transactions': 0, 'verified': 0,
                       'repairs': 0, 'repaired': 0, 'corrupt_files': [], 'repaired_files': [],
                       'unanchored': True}
                runs.append(run)
            run['last'] = local
            if sr and sr.group(1) == 'Beginning Verify and Repair transaction':
                run['transactions'] += 1
            elif sr and sr.group(2) == 'Verifying':
                run['verified'] += int(sr.group(3))
            elif sr and sr.group(2) == 'Repairing':
                run['repairs'] += 1
                run['repaired'] += int(sr.group(3))
            elif pnp:
                run['corrupt_files' if pnp.group(1) == 'Corrupt' else 'repaired_files'].append(pnp.group(2))
            continue
        if component != 'CBS':
            continue
        started = _STORE_SESSION.search(message)
        if started:
            store_session = (local, started.group(1))
        elif message == _STORE_CHECK:
            scan = {'local': local, 'offset': current, 'started': store_session[0], 'session': store_session[1],
                    'operation': '', 'result': '', 'detected': '', 'repaired': '', 'seconds': ''}
            scans.append(scan)
        elif scan is not None:
            for key, pattern in _SUMMARY:
                value = pattern.match(message)
                if value and not scan[key]:
                    scan[key] = value.group(1).strip()
    return runs, scans


def dism_sessions(text, problems):
    """One dict per Dism.exe or DismApi.dll session of a dism.log, in the order they start."""
    sessions, open_exe, open_api = [], None, {}
    for local, _, message in log_lines(text):
        pid = _PID.search(message)
        pid = pid.group(1) if pid else ''
        if _DISM_EXE_START in message:
            if open_exe is not None:
                problems['Dism.exe sessions that started before the one before them ended, the earlier reported '
                         'with no end time'] += 1
            open_exe = {'start': local, 'end': '', 'kind': 'Dism.exe', 'command': '', 'parent': '',
                        'pid': '', 'reboot': ''}
            sessions.append(open_exe)
        elif _DISM_API_START in message:
            if pid in open_api:
                problems['DismApi.dll sessions that started again before ending'] += 1
            open_api[pid] = {'start': local, 'end': '', 'kind': 'DismApi.dll', 'command': '', 'parent': '',
                             'pid': pid, 'reboot': ''}
            sessions.append(open_api[pid])
        elif _DISM_EXE_END in message:
            if open_exe is not None:
                open_exe['end'] = local
            open_exe = None
        elif _DISM_API_END in message:
            session = open_api.pop(pid, None)
            if session is not None:
                session['end'] = local
        elif message.startswith('API:') and pid in open_api:
            parent = _PARENT.search(message)
            if parent and not open_api[pid]['parent']:
                open_api[pid]['parent'] = parent.group(1)
        elif open_exe is not None:
            executing = _EXECUTING.search(message)
            reboot = _REBOOT.search(message)
            if executing and not open_exe['command']:
                open_exe['command'] = executing.group(1)
            elif reboot:
                open_exe['reboot'] = reboot.group(1)
            elif pid and not open_exe['pid']:
                open_exe['pid'] = pid
    unended = sum(1 for session in sessions if not session['end'])
    if unended:
        problems['sessions with no ending line, reported with a blank end time'] += unended
    return sessions


def _read_logs(context, label, parse):
    """parse(text, problems) for every file found, in path order, with the relative path."""
    for source in sorted({str(found) for found in context.get_files_found()}):
        relative = context.get_relative_path(source)
        problems = Counter()
        try:
            text, replaced = log_text(source)
        except (OSError, ValueError, zlib.error, struct.error) as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        if replaced:
            problems['characters that are not UTF-8, replaced'] += replaced
        result = parse(text, problems)
        for problem, count in sorted(problems.items()):
            logfunc(f'{label}: {relative}: {count} {problem}')
        yield source, relative, result


@artifact_processor
def windowsCbsTrustedInstallerStarts(context):
    data_headers = (('Start Time (UTC)', 'datetime'), ('Last Boot Time (UTC)', 'datetime'),
                    'Start Time (local, as recorded)', 'UTC Offset (from the log)',
                    'Last Boot Time (local, as recorded)', 'Servicing Stack Version', 'Source File')
    data_list, sources = [], []
    for source, relative, (starts, _) in _read_logs(context, 'CBS TrustedInstaller Starts', cbs_events):
        sources.append(source)
        for start in starts:
            offset = start['offset']
            data_list.append((_utc(start['local'], offset), _utc(start['boot'], offset), start['local'],
                              '' if offset is None else _offset_text(offset), start['boot'], start['stack'],
                              relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsCbsSessions(context):
    data_headers = (('Session Start (UTC)', 'datetime'), 'Session Start (local, as recorded)',
                    'UTC Offset (from the log)', 'Client', 'Session ID', 'Source File')
    data_list, sources = [], []
    for source, relative, (_, sessions) in _read_logs(context, 'CBS Servicing Sessions', cbs_events):
        sources.append(source)
        for local, offset, session_id, client in sessions:
            data_list.append((_utc(local, offset), local, '' if offset is None else _offset_text(offset),
                              client, session_id, relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsDismSessions(context):
    data_headers = ('Start Time (local, no zone recorded)', 'End Time (local, no zone recorded)', 'Session Kind',
                    'Command Line', 'Parent Process Command Line', 'Process ID', 'Reboot Required (as stored)')
    data_list, sources = [], []
    for source, _, sessions in _read_logs(context, 'DISM Sessions', dism_sessions):
        sources.append(source)
        for session in sessions:
            data_list.append((session['start'], session['end'], session['kind'], session['command'],
                              session['parent'], session['pid'], session['reboot']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsCbsSfpRuns(context):
    data_headers = (('Start Time (UTC)', 'datetime'), ('Last Line Time (UTC)', 'datetime'),
                    'Start Time (local, as recorded)', 'UTC Offset (from the log)', 'Verify Transactions',
                    'Components Verified', 'Repair Passes', 'Components Repaired', 'Files Reported Corrupt',
                    'Files Reported Repaired', 'Source File')
    data_list, sources = [], []
    for source, relative, (runs, _) in _read_logs(context, 'CBS SFP Verify and Repair Runs', cbs_checks):
        sources.append(source)
        for run in runs:
            offset = run['offset']
            data_list.append((_utc(run['local'], offset), _utc(run['last'], offset), run['local'],
                              '' if offset is None else _offset_text(offset), run['transactions'], run['verified'],
                              run['repairs'], run['repaired'], '\n'.join(run['corrupt_files']),
                              '\n'.join(run['repaired_files']), relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsCbsStoreScans(context):
    data_headers = (('Summary Time (UTC)', 'datetime'), ('Session Start (UTC)', 'datetime'),
                    'Summary Time (local, as recorded)', 'UTC Offset (from the log)', 'Operation (as stored)',
                    'Operation Result (as stored)', 'Total Detected Corruption', 'Total Repaired Corruption',
                    'Total Operation Time (seconds)', 'Session ID', 'Source File')
    data_list, sources = [], []
    for source, relative, (_, scans) in _read_logs(context, 'CBS Store Corruption Scans', cbs_checks):
        sources.append(source)
        for scan in scans:
            offset = scan['offset']
            data_list.append((_utc(scan['local'], offset), _utc(scan['started'], offset), scan['local'],
                              '' if offset is None else _offset_text(offset), scan['operation'], scan['result'],
                              scan['detected'], scan['repaired'], scan['seconds'], scan['session'], relative))
    return data_headers, data_list, '\n'.join(sources)
