"""PowerShell transcript parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Start-Transcript, and the transcription policy, write a text file of a PowerShell
session named PowerShell_transcript.<computer name>.<random>.<yyyyMMddHHmmss>.txt.
Each session in the file opens with a header block between two lines of 22
asterisks and, when it is stopped, closes with a footer block. With the
invocation header option, every command is preceded by a three-line block that
holds the time the command started. The block layouts and their strings come
from PowerShell's own source and resource files; the citations are in the notes.
"""

import os
import re
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc

# The separator line PowerShell writes above and below each block.
_STARS = '*' * 22

# The second line of a session header or footer, in every language PowerShell
# ships resource strings for (TranscriptPrologue, MinimalTranscriptPrologue and
# TranscriptEpilogue in InternalHostUserInterfaceStrings.resx and its 13
# translations at the pinned commit), and the English "Windows PowerShell" form
# the strings had before PowerShell commit 3c597367b, which Windows PowerShell
# 5.1 writes. A title not listed here is read by the block's shape (see
# _block_kind).
_START_TITLES = frozenset((
    'PowerShell transcript start', 'Windows PowerShell transcript start',
    'Začátek přepisu PowerShellu', 'Beginn des PowerShell-Transkripts',
    'Inicio de transcripción de PowerShell', 'Début de la transcription PowerShell',
    'Avvio della trascrizione di PowerShell', 'PowerShell トランスクリプトの開始',
    'PowerShell 기록 시작', 'Początek transkrypcji programu PowerShell',
    'Начало расшифровки PowerShell', 'Windows PowerShell döküm başlangıcı',
    'PowerShell 记录开始', 'PowerShell 文字記錄開始',
))
_END_TITLES = frozenset((
    'PowerShell transcript end', 'Windows PowerShell transcript end',
    'Konec přepisu PowerShellu', 'Ende des PowerShell-Transkripts',
    'Fin de transcripción de PowerShell', 'Fin de la transcription PowerShell',
    'Fine della trascrizione di PowerShell', 'PowerShell トランスクリプトの終了',
    'PowerShell 기록 끝', 'Zakończenie transkrypcji programu PowerShell',
    'Завершение расшифровки PowerShell', 'Windows PowerShell döküm sonu',
    'PowerShell 记录结束', 'PowerShell 文字記錄結束',
))

# "<label>: <yyyyMMddHHmmss>", the start, end and command start time lines. The
# French strings put a no-break space before the colon.
_TIME_LINE = re.compile(r'^(.+?)\s*:\s*(\d{14})$')
# "<computer name> (<OS version>)"; the Traditional Chinese string has no space.
_MACHINE = re.compile(r'^(.*?) ?\((.*)\)$')
_LINE_BREAK = re.compile(r'\r?\n')

# Output kept per command, in characters.
OUTPUT_LIMIT = 10000

__artifacts_v2__ = {
    "powershellTranscripts": {
        "name": "PowerShell Transcripts",
        "description": "Sessions recorded in PowerShell transcript files, one row per session, with the "
                       "start and end times, accounts, computer, host application, process ID and "
                       "PowerShell version the header stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from files named PowerShell_transcript.*.txt anywhere in the input. "
                 "PowerShell names a transcript PowerShell_transcript.<computer "
                 "name>.<random>.<yyyyMMddHHmmss>.txt "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L1143-L1184) "
                 "and puts it in the user's Documents folder, the home folder on macOS and Linux "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/CoreCLR/CorePsPlatform.cs#L406-L418, "
                 "https://github.com/MicrosoftDocs/PowerShell-Docs/blob/a3de8f22552170e70852470d46cd52cd9ca471ec/reference/7.5/Microsoft.PowerShell.Host/Start-Transcript.md#L44-L48), "
                 "unless Start-Transcript is given -OutputDirectory, or the $TRANSCRIPT variable is "
                 "set, which replaces the file name "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/Microsoft.PowerShell.ConsoleHost/host/msh/StartTranscriptCmdlet.cs#L158-L181). "
                 "When the Turn on PowerShell Transcription policy names an output directory, the "
                 "file sits in a yyyyMMdd folder below it "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L1111-L1131, "
                 "https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L1164-L1167). "
                 "A transcript saved under another name with Start-Transcript -Path is not found. "
                 "Each session in a file is one row: a file holds several when Start-Transcript "
                 "-Append added to it. A session header is a line of 22 asterisks, a title, Start "
                 "time, Username, RunAs User, Configuration Name, Machine, Host Application, "
                 "Process ID, the PSVersionTable entries one per line, and another line of "
                 "asterisks; a footer is asterisks, a title, End time and asterisks; a header made "
                 "with -UseMinimalHeader holds only the title and Start time "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/resources/InternalHostUserInterfaceStrings.resx#L195-L219, "
                 "https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L601-L657, "
                 "https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L682-L689). "
                 "-UseMinimalHeader was added in PowerShell commit "
                 "56fc426f8b309d2c1fe5a296afbbccb8049d09d8 "
                 "(https://github.com/PowerShell/PowerShell/commit/56fc426f8b309d2c1fe5a296afbbccb8049d09d8) "
                 "and is not in Windows PowerShell 5.1's Start-Transcript "
                 "(https://github.com/MicrosoftDocs/PowerShell-Docs/blob/a3de8f22552170e70852470d46cd52cd9ca471ec/reference/5.1/Microsoft.PowerShell.Host/Start-Transcript.md#L17-L36). "
                 "The cited code is PowerShell 7's; Windows PowerShell 5.1's code is not published, "
                 "and its transcripts in the known data and in plaso's test data have the same "
                 "layout. PowerShell's source holds the header strings in 13 other language "
                 "resource files, one of which (pt-BR) keeps the English text, so fields are read "
                 "by their position in the header, not by label. The Configuration Name line was "
                 "added in PowerShell commit 3f274aad9ce6d30f709cfc79dcebc7c943093316 "
                 "(https://github.com/PowerShell/PowerShell/commit/3f274aad9ce6d30f709cfc79dcebc7c943093316), "
                 "and a header with one line fewer before the PSVersionTable entries is read "
                 "without it. A block's title is matched against the titles in PowerShell's "
                 "resource strings in all 14 resource files and the older English Windows "
                 "PowerShell titles, which PowerShell commit "
                 "3c597367ba32c8b32851a9caf824c7dea202d95b replaced "
                 "(https://github.com/PowerShell/PowerShell/commit/3c597367ba32c8b32851a9caf824c7dea202d95b); "
                 "a block with any other title is a header when lines follow its time line or when "
                 "no session is open, and otherwise a footer. Start Time and End Time are the times "
                 "the header and footer store, which PowerShell takes from DateTime.Now and writes "
                 "as yyyyMMddHHmmss: the local time of the computer that wrote the file, with no "
                 "time zone or UTC offset recorded, so they are shown in that local time with "
                 "separators added, not converted to another zone. A time that is not a valid date "
                 "is shown as its digits. End Time is blank when the file holds no footer for the "
                 "session; the file does not say why. Username is the account PowerShell ran as, as "
                 "domain\\name, except that in a remoting session it is the connected user, and "
                 "RunAs User is the account the process ran as in both cases "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L615-L621). "
                 "Configuration Name is the remoting session configuration and is empty otherwise "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L638-L642). "
                 "Machine and OS Version are the two parts of the Machine line, the computer name "
                 "and the OS version string. Host Application is the process's command-line "
                 "arguments joined by spaces, which need not be a full path "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L654), "
                 "and Process ID its process ID. PS Version and PS Edition are the PSVersion and "
                 "PSEdition entries of the header. Header is full or minimal. Command Headers is "
                 "how many command start time blocks the session holds, reported one per row by the "
                 "PowerShell Transcript Commands artifact; it is 0 for a session started without "
                 "-IncludeInvocationHeader, whose commands are in the file but are not reported row "
                 "by row, because without the invocation header PowerShell writes only the prompt "
                 "text before each command, and a prompt can be any text. Start Line is the line of "
                 "the file where the header begins. Files are read as UTF-8, or as UTF-16 when they "
                 "begin with its byte order mark; bytes that are not UTF-8 are replaced and the run "
                 "log counts them. A file whose first line is not a line of 22 asterisks is not "
                 "read as a transcript and is named in the run log. On "
                 "windows11_arm_pstranscript_known_20261022 (Windows PowerShell 5.1.26100.9711, "
                 "files UTF-8 with a byte order mark) the 3 rows match the 3 sessions made, two in "
                 "one file, their start and end times and process IDs included. Username and RunAs "
                 "User held the same one account on every row, Configuration Name was empty on "
                 "every row, as no session was a remoting session, and Machine, OS Version, Host "
                 "Application, PS Version and PS Edition each held one value on every row, as the "
                 "three sessions ran on one computer from the same command; Header held full on "
                 "every row. plaso_testdata_f951fc6 keeps its two transcripts under repository "
                 "names, so it gives no rows; copied to transcript file names they read as one "
                 "session each, Windows PowerShell 5.1 in English and in German, the German one "
                 "with no footer and a title not in PowerShell's published strings, read as a "
                 "header by its shape, and Username and RunAs User were identical and Configuration "
                 "Name empty on both. The transcription policy is not read here: the Security "
                 "Settings artifact reports the machine policy's EnableTranscripting value, and "
                 "neither reads the policy's OutputDirectory or EnableInvocationHeader value or its "
                 "per-user copy. PowerShell 7, the minimal header and remoting sessions were not "
                 "exercised on real data and are covered by tests written from PowerShell's source; "
                 "the policy output folder was exercised only on a copy of the known-data file "
                 "placed in a yyyyMMdd folder.",
        "paths": ('*/PowerShell_transcript.*.txt',),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64), Windows PowerShell 5.1.26100.9711 | 3 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 0 rows (no file matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763.3046) | 0 rows (no file matches the "
                                            "declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not "
                                          "searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volume not unlocked, so not "
                                           "searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no file matches the declared paths)",
            "defender_evtx_attack_samples": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "defender_evtx_to_mitre": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dhparser_detectionhistory_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "discord_win_ptb": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dleapp_slack_known": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client_2023": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_ad": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_evtx": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win7_x86": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_mitre_attack_4688_cc0": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no file "
                                          "matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                         "file matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                        "file matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                   "file matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100.2033) | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education (build 16299, version 1709) | 0 rows (no file matches the "
                              "declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348.1850) | 0 rows (no file matches the "
                                        "declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 0 rows (no file matches the declared paths)",
            "plaso_testdata_f951fc6": "OS version not recorded | 0 rows (its two transcripts are kept at repository "
                                      "names, which the paths do not match)",
            "roblox_windows": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (no file matches "
                                          "the declared paths)",
            "szechuan_win10": "Windows 10 2004 (build 19041) | 0 rows (no file matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "wire_win": "OS version not recorded | 0 rows (no file matches the declared paths)",
        },
    },
    "powershellTranscriptCommands": {
        "name": "PowerShell Transcript Commands",
        "description": "Commands in PowerShell transcript files that carry a command start time, one row "
                       "per command, with the command line and up to 10,000 characters of its output.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the same files as the PowerShell Transcripts artifact, whose notes give "
                 "the file names, the folders and how sessions are found. When a transcript is "
                 "started with -IncludeInvocationHeader, or by the transcription policy with "
                 "invocation headers on, PowerShell writes, before the first line of each command, "
                 "a line of 22 asterisks, 'Command start time: ' (or its translation) and the time "
                 "as yyyyMMddHHmmss, and another line of asterisks, then the prompt text followed "
                 "by the command "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L440-L450, "
                 "https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/resources/InternalHostUserInterfaceStrings.resx#L192-L194). "
                 "One row is one such block. Command Start Time is the time the block stores, taken "
                 "from DateTime.Now: the local time of the computer that wrote the file, with no "
                 "time zone or UTC offset recorded, shown in that local time with separators added, "
                 "not converted to another zone. Command Line is the line after the block as "
                 "stored, without its line end. It begins with the prompt text: PS> when no prompt "
                 "was captured "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L1198), "
                 "otherwise the text the session's prompt function returned "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L754-L757), "
                 "which with PowerShell's default prompt is PS, the current location and >, as on "
                 "every known-data row; a custom prompt can return anything, so the prompt is not "
                 "split off. Output is every line after the command line up to the next block of "
                 "asterisks or the end of the file, without the blank lines at its end, kept as "
                 "stored with the lines joined by a line feed, including lines PowerShell writes "
                 "for further commands of the same input, which begin with >> "
                 "(https://github.com/PowerShell/PowerShell/blob/7962a6ae10d99655405c172bccc890b063c54c41/src/System.Management.Automation/engine/hostifaces/MshHostUserInterface.cs#L452-L455). "
                 "Output holds at most the first 10,000 characters; Output Lines is the number of "
                 "lines it had in full, whether or not it was cut, and the run log counts the "
                 "commands whose output was cut. Line Number is the line of the file holding the "
                 "command line. Session Start Time, Machine and Username are those of the session "
                 "header the command follows, and are blank for a block that follows no header. On "
                 "windows11_arm_pstranscript_known_20261022 the 6 rows match the 6 commands typed "
                 "in the session made with -IncludeInvocationHeader, start times and command lines "
                 "included, the last being Stop-Transcript (the output has no separate record in "
                 "the known data), and the two sessions made without it add none; Session Start "
                 "Time, Machine and Username held one value on every row, as all six commands come "
                 "from one session. plaso_testdata_f951fc6 gives no rows, as its files are kept "
                 "under repository names; copied to transcript file names, its German transcript "
                 "gives 2 rows and its English one none. A session without invocation headers adds "
                 "no rows here, however many commands it holds.",
        "paths": ('*/PowerShell_transcript.*.txt',),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64), Windows PowerShell 5.1.26100.9711 | 6 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 0 rows (no file matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763.3046) | 0 rows (no file matches the "
                                            "declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not "
                                          "searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volume not unlocked, so not "
                                           "searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no file matches the declared paths)",
            "defender_evtx_attack_samples": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "defender_evtx_to_mitre": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dhparser_detectionhistory_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "discord_win_ptb": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dleapp_slack_known": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_attack_samples_sysmon_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win10_client": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win11_client_2023": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_0_20348_azure": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_ad": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win2022_evtx": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_baseline_nextron_085_win7_x86": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_mitre_attack_4688_cc0": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evtx_mitre_sysmon_cc0": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no file "
                                          "matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                         "file matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                        "file matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no "
                                   "file matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100.2033) | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education (build 16299, version 1709) | 0 rows (no file matches the "
                              "declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348.1850) | 0 rows (no file matches the "
                                        "declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 0 rows (no file matches the declared paths)",
            "plaso_testdata_f951fc6": "OS version not recorded | 0 rows (its two transcripts are kept at repository "
                                      "names, which the paths do not match)",
            "roblox_windows": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (no file matches "
                                          "the declared paths)",
            "szechuan_win10": "Windows 10 2004 (build 19041) | 0 rows (no file matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "wire_win": "OS version not recorded | 0 rows (no file matches the declared paths)",
        },
    },
}


def decode_transcript(data):
    """Text of a transcript and how many replacement characters decoding added."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        text = data.decode('utf-16', errors='replace')
        return text, text.count('�') - data.decode('utf-16', errors='ignore').count('�')
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    text = data.decode('utf-8', errors='replace')
    return text, text.count('�') - data.count('�'.encode('utf-8'))


def show_time(digits):
    """yyyyMMddHHmmss as 'yyyy-MM-dd HH:mm:ss', or the digits when not a valid date."""
    try:
        return datetime.strptime(digits, '%Y%m%d%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return digits


def _field(line):
    """The value of a 'label: value' header line, or the line when it has no colon."""
    if ':' not in line:
        return line.strip()
    return line.split(':', 1)[1].strip()


def _block_kind(title, has_body, session_open):
    """'start' or 'end' for a header or footer block with this title."""
    if title in _START_TITLES:
        return 'start'
    if title in _END_TITLES:
        return 'end'
    return 'start' if has_body or not session_open else 'end'


def parse_header_body(body):
    """Fields of a full session header from the lines between its time line and the
    closing asterisks."""
    fields = {'username': '', 'runas': '', 'configuration': '', 'machine': '',
              'os_version': '', 'host_application': '', 'process_id': '',
              'ps_version': '', 'ps_edition': ''}
    table_at = len(body)
    for index, line in enumerate(body):
        if line.split(':', 1)[0].strip() == 'PSVersion':
            table_at = index
            break
    named = body[:table_at]
    if len(named) == 6:
        keys = ('username', 'runas', 'configuration', 'machine', 'host_application',
                'process_id')
    elif len(named) == 5:
        keys = ('username', 'runas', 'machine', 'host_application', 'process_id')
    else:
        keys = ()
    for key, line in zip(keys, named):
        fields[key] = _field(line)
    machine = _MACHINE.match(fields['machine'])
    if machine:
        fields['machine'], fields['os_version'] = machine.group(1), machine.group(2)
    for line in body[table_at:]:
        key, _, value = line.partition(':')
        if key.strip() == 'PSVersion':
            fields['ps_version'] = value.strip()
        elif key.strip() == 'PSEdition':
            fields['ps_edition'] = value.strip()
    fields['header_lines'] = len(named)
    return fields


def parse_transcript(text):
    """Sessions and commands in a transcript's text.

    Returns (sessions, commands). A session is a dict with its fields, 'start',
    'end', 'header', 'line' and 'commands' (the count of command blocks). A command
    is a dict with 'time', 'command', 'output', 'output_lines', 'line' and
    'session' (the index of its session, or None).
    """
    lines = _LINE_BREAK.split(text)
    if lines and lines[-1] == '':
        lines.pop()
    sessions = []
    commands = []
    open_session = None
    current = None
    index = 0
    count = len(lines)

    def close_output(end):
        if current is None:
            return
        output = lines[current['line']:end]
        while output and output[-1] == '':
            output.pop()
        joined = '\n'.join(output)
        current['output_lines'] = len(output)
        current['output'] = joined[:OUTPUT_LIMIT]
        current['cut'] = len(joined) > OUTPUT_LIMIT

    while index < count:
        if lines[index] != _STARS or index + 2 >= count:
            index += 1
            continue
        second = lines[index + 1]
        third = lines[index + 2]
        command_time = _TIME_LINE.match(second)
        if command_time and third == _STARS:
            close_output(index)
            command_line = index + 3
            current = {
                'time': show_time(command_time.group(2)),
                'command': lines[command_line] if command_line < count else '',
                'output': '', 'output_lines': 0, 'cut': False, 'line': command_line + 1,
                'session': open_session,
            }
            commands.append(current)
            if open_session is not None:
                sessions[open_session]['commands'] += 1
            index = command_line + 1
            continue
        block_time = _TIME_LINE.match(third)
        if not block_time:
            index += 1
            continue
        end = index + 3
        while end < count and lines[end] != _STARS:
            end += 1
        if end >= count:
            # No closing asterisks: not a block PowerShell wrote.
            index += 1
            continue
        close_output(index)
        current = None
        body = lines[index + 3:end]
        kind = _block_kind(second, bool(body), open_session is not None)
        if kind == 'end':
            if open_session is not None:
                sessions[open_session]['end'] = show_time(block_time.group(2))
                open_session = None
        else:
            session = parse_header_body(body)
            session.update({
                'start': show_time(block_time.group(2)), 'end': '',
                'header': 'full' if body else 'minimal', 'line': index + 1,
                'commands': 0,
            })
            sessions.append(session)
            open_session = len(sessions) - 1
        index = end + 1
    close_output(count)
    return sessions, commands


def _read_transcripts(context, label):
    """(relative path, sessions, commands) for each transcript found, and the files read."""
    results = []
    sources = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isdir(source):
            continue
        name = os.path.basename(source)
        if not (name.startswith('PowerShell_transcript.') and name.endswith('.txt')):
            continue
        relative = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                text, replaced = decode_transcript(handle.read())
        except OSError as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        first = _LINE_BREAK.split(text, 1)[0]
        if first != _STARS:
            logfunc(f'{label}: {relative} does not begin with a transcript header; not read')
            continue
        sources.append(source)
        sessions, commands = parse_transcript(text)
        if replaced:
            logfunc(f'{label}: {relative}: {replaced} bytes that are not UTF-8 replaced')
        unread = [s for s in sessions if s['header'] == 'full' and
                  s['header_lines'] not in (5, 6)]
        if unread:
            logfunc(f'{label}: {relative}: {len(unread)} headers with an unexpected '
                    f'number of lines; their fields are left blank')
        results.append((relative, sessions, commands))
    return results, sources


@artifact_processor
def powershellTranscripts(context):
    data_headers = ('Start Time (local, no zone recorded)', 'End Time (local, no zone recorded)',
                    'Username', 'RunAs User', 'Configuration Name', 'Machine', 'OS Version',
                    'Host Application', 'Process ID', 'PS Version', 'PS Edition', 'Header',
                    'Command Headers', 'Start Line', 'Source File')
    data_list = []
    results, sources = _read_transcripts(context, 'PowerShell Transcripts')
    for relative, sessions, _ in results:
        for s in sessions:
            data_list.append((s['start'], s['end'], s['username'], s['runas'],
                              s['configuration'], s['machine'], s['os_version'],
                              s['host_application'], s['process_id'], s['ps_version'],
                              s['ps_edition'], s['header'], s['commands'], s['line'],
                              relative))
        logfunc(f'PowerShell Transcripts: {len(sessions)} sessions read from {relative} '
                f'({sum(1 for s in sessions if not s["end"])} without a footer)')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def powershellTranscriptCommands(context):
    data_headers = ('Command Start Time (local, no zone recorded)',
                    'Session Start Time (local, no zone recorded)', 'Command Line', 'Output',
                    'Output Lines', 'Line Number', 'Machine', 'Username', 'Source File')
    data_list = []
    results, sources = _read_transcripts(context, 'PowerShell Transcript Commands')
    for relative, sessions, commands in results:
        for c in commands:
            session = sessions[c['session']] if c['session'] is not None else None
            data_list.append((c['time'],
                              session['start'] if session else '',
                              c['command'], c['output'], c['output_lines'], c['line'],
                              session['machine'] if session else '',
                              session['username'] if session else '',
                              relative))
        cut = sum(1 for c in commands if c['cut'])
        logfunc(f'PowerShell Transcript Commands: {len(commands)} commands read from '
                f'{relative} ({cut} with output cut at {OUTPUT_LIMIT} characters)')
    return data_headers, data_list, '\n'.join(sources)
