"""TeamViewer connection lists and application log for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads TeamViewer's connection lists, Connections_incoming.txt and Connections.txt,
and its application log, TeamViewer<version>_Logfile.log and its _OLD copy. The
list layout is read the way plaso's TeamViewer parser reads it; the log line types
reported are the ones TeamViewer's "Log file reading - Incoming connection" article
shows. The citations are in the notes.
"""

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc

_LINE_BREAK = re.compile(r'\r?\n')

# A connection list time, dd-mm-yyyy hh:mm:ss as plaso reads it.
_LIST_TIME = re.compile(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}$')
_DIGITS = re.compile(r'^\d+$')
# Fields of a list line that holds no tab: runs of two or more spaces.
_PADDING = re.compile(r' {2,}')

# The date and time that begins a log line.
_LOG_TIME = re.compile(r'^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})(?:\s|$)')
# The rest of a dated log line: two numbers, a short tag, then the message.
_LOG_FIELDS = re.compile(r'^\s+\d+\s+\d+\s+\S+(?:\s+(.*))?$')
# The Start and Version lines of the block the log writes when a process starts
# logging.
_HEADER_START = re.compile(r'^Start:\s+(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s*(?:\(([^)]*)\))?\s*$')
_HEADER_VERSION = re.compile(r'^Version:\s+(.*?)\s*$')

# Log line types named in TeamViewer's "Log file reading - Incoming connection"
# article, matched on the class, method and text the article shows.
_LOG_RULES = (
    ('Connection attempt', re.compile(r'::CreatePassiveSession\(\): incoming session')),
    ('Allowlist check refused',
     re.compile(r'\bCLoginServer::CheckIfConnectionIsAllowed: Partner .* not whitelisted')),
    ('Allowlist check refused', re.compile(r'\bCLoginServer::runServer: Connection is not allowed')),
    ('Easy Access check', re.compile(r'\bAuthenticationPublicKey_Passive::Verify:')),
    ('Easy Access check', re.compile(r'\bLookupPublicKeyV2: .*reject Authentication')),
    ('Password check',
     re.compile(r'\bAuthenticationPasswordLogin_Passive::RunAuthenticationMethod: authentication using ')),
    ('Participant added', re.compile(r'\bCPersistentParticipantManager::AddParticipant:')),
    ('Session terminate', re.compile(r'\bSessionManagerDesktop::SessionTerminate:')),
)

__artifacts_v2__ = {
    "teamViewerConnections": {
        "name": "TeamViewer Connection Lists",
        "description": "Connections listed in TeamViewer's Connections_incoming.txt and Connections.txt, one "
                       "row per line, with the start and end times, TeamViewer ID, display name, local "
                       "user, connection type and connection GUID as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "TeamViewer",
        "notes": "Read from Connections_incoming.txt and Connections.txt in a folder named TeamViewer anywhere in "
                 "the input, with the T and V of TeamViewer and the C of the file name in either case. "
                 "TeamViewer's knowledge base says successful connections are listed in Connections_incoming.txt "
                 "in the TeamViewer folder "
                 "(https://www.teamviewer.com/en/global/support/knowledge-base/teamviewer-remote/troubleshooting/log-file-reading-incoming-connection/,"
                 " last modified 8 March 2024); it does not describe Connections.txt or the fields of either file."
                 " The KAPE target collects connections*.txt from Program Files*\\TeamViewer "
                 "(https://github.com/EricZimmerman/KapeFiles/blob/9d3ec9ccba83e15c9f2d496226e69145049d0187/Targets/Apps/TeamViewerLogs.tkape#L7-L12)."
                 " The fields are read in the order plaso's parser reads them: TeamViewer ID, display name, start,"
                 " end, local account, activity type and connection identifier for Connections_incoming.txt "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L470-L479),"
                 " and the same without the display name for Connections.txt "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L317-L325)."
                 " plaso describes the Connections_incoming.txt ID as the TeamViewer identifier of the incoming "
                 "connection "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L44)"
                 " and stores the Connections.txt ID as the destination "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L361-L363);"
                 " Neither cited TeamViewer article documents the field, so the column is named TeamViewer ID. A "
                 "line is split on tabs, or on runs of two or more spaces when it holds no tab, and, after empty "
                 "fields at the end of the line are dropped, is read when it has 7 fields with times in the third "
                 "and fourth, or 6 fields with times in the second and third, and digits in the first. The layout "
                 "is decided by the line, not by the file name, and Display Name is blank on a 6-field line. Other"
                 " non-blank lines are not reported; the run log counts them per file. Start Time and End Time are"
                 " shown as stored, not converted. plaso reads them as day-month-year "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L540-L542)"
                 " in UTC "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L42-L45,"
                 " "
                 "https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L544-L546);"
                 " Neither cited TeamViewer article documents their zone. In plaso_testdata_f951fc6 the start and "
                 "end on the connections_incoming.txt row are within one second of 8 hours after the times of the "
                 "log's Connection attempt and Session terminate lines for the same session (see the TeamViewer "
                 "Log Events artifact), and the log's Start header gives UTC-8:00, which fits UTC in that one "
                 "sample only. Local User, Connection Type and Connection GUID are as stored; Neither cited "
                 "TeamViewer article documents their values. Line is the line of the file. On "
                 "plaso_testdata_f951fc6, which keeps the files at repository paths under test_data/teamviewer, "
                 "there are 2 rows, one per file: connections_incoming.txt is tab-separated with a tab at the end "
                 "of the line and Connections.txt is padded with spaces; the display name holds a redaction "
                 "placeholder, the value plaso's own test for the file expects. Local User and Connection Type "
                 "held one value on both rows, and Display Name is blank on the Connections.txt row. Not covered: "
                 "no known data from a TeamViewer install, which waits for a lab install with a TeamViewer "
                 "account; where TeamViewer keeps these lists on macOS and Linux is not established; a list in an "
                 "encoding other than UTF-8 or UTF-16 shows replacement characters, which the run log counts. The "
                 "KAPE target also collects files under AppData\\Roaming\\TeamViewer\\MRU\\RemoteSupport, an installer"
                 " log, a chat file cache database and a remote printing database "
                 "(https://github.com/EricZimmerman/KapeFiles/blob/9d3ec9ccba83e15c9f2d496226e69145049d0187/Targets/Apps/TeamViewerLogs.tkape#L26-L45);"
                 " none is read here.",
        "paths": ('*/[Tt]eam[Vv]iewer/[Cc]onnections_incoming.txt',
                  '*/[Tt]eam[Vv]iewer/[Cc]onnections.txt'),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "plaso_testdata_f951fc6": "OS not recorded, TeamViewer 15.50.5 per the log beside the lists | 2 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 0 rows (no file matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763.3046) | 0 rows (no file matches the declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no file matches the declared paths)",
            "chatgpt_computerhistory_synthetic": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "chatgpt_macos": "Darwin 25.5.0 | 0 rows (no file matches the declared paths)",
            "defender_evtx_attack_samples": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "defender_evtx_to_mitre": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dhparser_detectionhistory_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "discord_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "discord_win_ptb": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dissect_testdata_b43db37": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dleapp_imessage_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_keychains_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 (build 20D74) | 0 rows (no file matches the declared paths)",
            "dleapp_safari_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_slack_known": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 (build 23G93; SystemVersion.plist reads 10.16) | 0 rows (no file matches the declared paths)",
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
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server (aarch64) | 0 rows (no file matches the declared paths)",
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server (aarch64) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100.2033) | 0 rows (no file matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 (i386) | 0 rows (no file matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education (build 16299, version 1709) | 0 rows (no file matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 (build 20D74) | 0 rows (no file matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no file matches the declared paths)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 (per the publisher and the file name; not read from the image) | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348.1850) | 0 rows (no file matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon (usr/lib/os-release, etc/linuxmint/info) | 0 rows (no file matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 0 rows (no file matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "roblox_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "roblox_windows": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 (aarch64) | 0 rows (no file matches the declared paths)",
            "signal_macos": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "signal_macos_needed": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 (build 19041) | 0 rows (no file matches the declared paths)",
            "telegram_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_apport": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_apport_root": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_btmp": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_dconf": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_chooser": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_gui": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_monitors": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nautilusstars": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_a": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_b": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_etcwifi": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_screentime": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_tracker": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "vim_viminfo_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "whatsapp_macos": "macOS 26.5.2 | 0 rows (no file matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64), Windows PowerShell 5.1.26100.9711 | 0 rows (no file matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "wire_win": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "zsh_known_data_macos": "Darwin 25.6.0 | 0 rows (no file matches the declared paths)",
        },
    },
    "teamViewerLogEvents": {
        "name": "TeamViewer Log Events",
        "description": "Lines of the TeamViewer application log of the types TeamViewer's knowledge "
                       "base names for incoming connections (connection attempt, allowlist refusal, "
                       "Easy Access and password checks, participant added, session terminate), and "
                       "the log's own Start header lines, with the time and UTC offset as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-22",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "TeamViewer",
        "notes": "Read from files named TeamViewer*_Logfile*.log in any folder, with the T and V of TeamViewer and"
                 " the L of Logfile in either case. TeamViewer's knowledge base names TeamViewer15_Logfile.log, or"
                 " TeamViewerXX_Logfile.log for TeamViewer (Classic), and an _OLD copy when there is one, in "
                 "C:\\Program Files (x86)\\TeamViewer for the full version and Host, "
                 "C:\\Users\\<user>\\AppData\\Roaming\\TeamViewer for QuickSupport, and the user's "
                 "Library/Logs/TeamViewer on macOS "
                 "(https://www.teamviewer.com/en/global/support/knowledge-base/teamviewer-remote/contact-support/find-your-log-files/,"
                 " last modified 22 July 2026); the KAPE target looks in Program Files*\\TeamViewer and "
                 "AppData\\Roaming\\TeamViewer "
                 "(https://github.com/EricZimmerman/KapeFiles/blob/9d3ec9ccba83e15c9f2d496226e69145049d0187/Targets/Apps/TeamViewerLogs.tkape#L13-L24)."
                 " Each file is read on its own, so an _OLD file gives its own rows. A dated line begins "
                 "yyyy/mm/dd hh:mm:ss.mmm, then two numbers and a short tag, then the message, the layout plaso's "
                 "parser reads "
                 "(https://github.com/log2timeline/plaso/blob/f951fc6cdaf365948d91cd945ac405a2d1b5ff6c/plaso/parsers/text_plugins/teamviewer.py#L122-L135),"
                 " which takes the first number for a process identifier and gives the other two fields no stated "
                 "purpose; the numbers and the tag are not reported, and Line leads to them. A dated line is a row"
                 " when its message matches a line type shown in TeamViewer's article Log file reading - Incoming "
                 "connection "
                 "(https://www.teamviewer.com/en/global/support/knowledge-base/teamviewer-remote/troubleshooting/log-file-reading-incoming-connection/,"
                 " last modified 8 March 2024), with the article's stage heading in brackets: Connection attempt, "
                 "CreatePassiveSession(): incoming session (stage 1, establishing a connection attempt; the "
                 "article says no connection exists yet at that point); Allowlist check refused, "
                 "CheckIfConnectionIsAllowed: Partner ... not whitelisted or runServer: Connection is not allowed "
                 "(stage 2, block and allowlist check); Easy Access check, AuthenticationPublicKey_Passive::Verify"
                 " or LookupPublicKeyV2 ... reject Authentication, and Password check, "
                 "AuthenticationPasswordLogin_Passive::RunAuthenticationMethod: authentication using (stage 3, "
                 "easy access and password check); Participant added, "
                 "CPersistentParticipantManager::AddParticipant (stage 4, successful connection starts); Session "
                 "terminate, SessionManagerDesktop::SessionTerminate (stage 5, connection ends). Message is the "
                 "rest of the line after the tag and the spaces that follow it, as stored, without trailing "
                 "spaces, so whether a check succeeded or was denied, which password was used, the participant "
                 "entries, and whether a session was removed or logins aborted are read there. The article says "
                 "the IDs it shows for TVSessionID and ID are session IDs, not TeamViewer IDs, and that reading "
                 "the logs completely takes training TeamViewer gives some of its staff; a row is a line of a type"
                 " the article shows, not a finding that a session took place. Not reported: lines for outgoing "
                 "connections and file transfers, which neither cited TeamViewer article describes (the sample has"
                 " no Send file or Write file lines); the CheckIfConnectionIsAllowed() and AuthenticateServer() "
                 "lines the article shows for checks that pass; and every other line, including Connection "
                 "incoming, sessionID lines, which the article does not name. The run log counts each file's "
                 "lines, dated lines, lines without a date, Start header lines and rows by type. The file holds "
                 "blocks of lines without a date; a block's Start line gives a time and a UTC offset in brackets "
                 "and its Version line gives a version, and plaso_testdata_f951fc6 holds 2 such blocks; each Start"
                 " line is a row of type Log header Start, with its time in Time. Log Header UTC Offset (as "
                 "stored) and Log Header Version on each row are those of the last Start block above the row in "
                 "the same file, and are blank above the first block. In plaso_testdata_f951fc6 the dated lines "
                 "carry 9 distinct values in the field plaso reads as the process identifier, and nothing in the "
                 "file says which lines a block covers. Time is the line's time as stored, not converted; Neither "
                 "cited TeamViewer article documents its zone. In plaso_testdata_f951fc6 each Start time is within"
                 " 20 milliseconds of the dated lines on either side of its block, which fits the line times being"
                 " in the Start line's offset in that sample only. On plaso_testdata_f951fc6 there are 8 rows from"
                 " a log of 1,049 lines (1,013 dated, 36 without a date): 2 Log header Start, 1 Connection "
                 "attempt, 1 Password check, 3 Participant added and 1 Session terminate. Log Header UTC Offset "
                 "held UTC-8:00 and Log Header Version held 15.50.5 (64-bit) on all 8 rows, as both Start blocks "
                 "carry those values, and Source File held one path, as the sample holds one log. Allowlist check "
                 "refused and Easy Access check rows, a Session terminate that aborts logins, and logs from other "
                 "TeamViewer versions are covered only by tests written from the article's example lines. Not "
                 "covered: no known data from a TeamViewer install, which waits for a lab install with a "
                 "TeamViewer account; where TeamViewer writes its log on Linux is not established, as its article "
                 "gives only the teamviewer ziplog command.",
        "paths": ('*/[Tt]eam[Vv]iewer*_[Ll]ogfile*.log',),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "plaso_testdata_f951fc6": "OS not recorded, TeamViewer 15.50.5 per the log header | 8 rows",
            "af_case2_win10": "Windows 10 1809 (build 17763) | 0 rows (no file matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no file matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763.3046) | 0 rows (no file matches the declared paths)",
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 (ARM64) | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 0 rows (BitLocker volumes not unlocked, so not searched)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no file matches the declared paths)",
            "chatgpt_computerhistory_synthetic": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "chatgpt_macos": "Darwin 25.5.0 | 0 rows (no file matches the declared paths)",
            "defender_evtx_attack_samples": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "defender_evtx_to_mitre": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dhparser_detectionhistory_gpl": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "discord_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "discord_win_ptb": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dissect_testdata_b43db37": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "dleapp_imessage_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_keychains_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 (build 20D74) | 0 rows (no file matches the declared paths)",
            "dleapp_safari_bigsur": "macOS 11.2.1 | 0 rows (no file matches the declared paths)",
            "dleapp_slack_known": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 (build 23G93; SystemVersion.plist reads 10.16) | 0 rows (no file matches the declared paths)",
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
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server (aarch64) | 0 rows (no file matches the declared paths)",
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server (aarch64) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_64k_sha256": "ReFS 3.14 test volume (Windows Insider Server build 29574) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_snapshots": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_specials": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "forefst_refs314_usn": "ReFS 3.14 test volume (Windows 11 per its name; build not recorded) | 0 rows (no file matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 (build 26100.2033) | 0 rows (no file matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 (i386) | 0 rows (no file matches the declared paths)",
            "less_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education (build 16299, version 1709) | 0 rows (no file matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 (build 20D74) | 0 rows (no file matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no file matches the declared paths)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 (per the publisher and the file name; not read from the image) | 0 rows (no file matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348.1850) | 0 rows (no file matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon (usr/lib/os-release, etc/linuxmint/info) | 0 rows (no file matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 (build 22621) | 0 rows (no file matches the declared paths)",
            "python_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "roblox_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "roblox_windows": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 (aarch64) | 0 rows (no file matches the declared paths)",
            "signal_macos": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "signal_macos_needed": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "sqlite_history_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 (build 19041) | 0 rows (no file matches the declared paths)",
            "telegram_macos": "macOS 26.5.2 (build 25F84) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_apport": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_apport_root": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_btmp": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_dconf": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_chooser": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_gui": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_monitors": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nautilusstars": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_a": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_b": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_nm_etcwifi": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_screentime": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_tracker": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS (aarch64) | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS (aarch64), glibc 2.43 | 0 rows (no file matches the declared paths)",
            "vim_viminfo_known_macos": "macOS 27.0.1 (26A434) | 0 rows (no file matches the declared paths)",
            "whatsapp_macos": "macOS 26.5.2 | 0 rows (no file matches the declared paths)",
            "windows11_arm_4688_known": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_7zip_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_auditmap_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_cam_known_20261019": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_ntfs_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_parallels": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "windows11_arm_pstranscript_known_20261022": "Windows 11 build 26200 (ARM64), Windows PowerShell 5.1.26100.9711 | 0 rows (no file matches the declared paths)",
            "windows11_arm_smb_known_20261011": "Windows 11 25H2 (build 26200), ARM64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 (ARM64) | 0 rows (no file matches the declared paths)",
            "wire_win": "OS version not recorded | 0 rows (no file matches the declared paths)",
            "zsh_known_data_macos": "Darwin 25.6.0 | 0 rows (no file matches the declared paths)",
        },
    },
}


def decode_text(data):
    """Text of a file and how many replacement characters decoding added."""
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        text = data.decode('utf-16', errors='replace')
        return text, text.count('\ufffd') - data.decode('utf-16', errors='ignore').count('\ufffd')
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    text = data.decode('utf-8', errors='replace')
    return text, text.count('\ufffd') - data.count('\ufffd'.encode('utf-8'))


def split_list_line(line):
    """Fields of a connection list line: split on tabs, or on runs of spaces when the
    line holds no tab. Empty fields at the end of the line are dropped."""
    if '\t' in line:
        fields = line.split('\t')
    else:
        fields = _PADDING.split(line.strip())
    while fields and fields[-1].strip() == '':
        fields.pop()
    return fields


def parse_list_line(line):
    """A dict of the fields of one connection list line, or None when the line has
    neither layout plaso reads."""
    fields = split_list_line(line)
    if (len(fields) == 7 and _DIGITS.match(fields[0].strip())
            and _LIST_TIME.match(fields[2].strip()) and _LIST_TIME.match(fields[3].strip())):
        tv_id, name, start, end, user, kind, guid = fields
    elif (len(fields) == 6 and _DIGITS.match(fields[0].strip())
          and _LIST_TIME.match(fields[1].strip()) and _LIST_TIME.match(fields[2].strip())):
        tv_id, start, end, user, kind, guid = fields
        name = ''
    else:
        return None
    return {'id': tv_id.strip(), 'name': name, 'start': start.strip(), 'end': end.strip(),
            'user': user, 'type': kind, 'guid': guid}


def parse_connection_list(text):
    """(records, unread): one record per line with a list layout, each with its 1-based
    line number, and the number of non-blank lines without one."""
    records = []
    unread = 0
    for number, line in enumerate(_LINE_BREAK.split(text), 1):
        if not line.strip():
            continue
        record = parse_list_line(line)
        if record is None:
            unread += 1
            continue
        record['line'] = number
        records.append(record)
    return records, unread


def parse_log(text):
    """(events, counts) for a TeamViewer log's text.

    An event is a dict with 'time', 'offset', 'version', 'type', 'message' and 'line'.
    'offset' and 'version' are those of the last Start header block before the line,
    blank when there is none. counts holds 'lines', 'dated', 'undated', 'headers' and
    the number of events of each type.
    """
    lines = _LINE_BREAK.split(text)
    if lines and lines[-1] == '':
        lines.pop()
    events = []
    counts = {'lines': len(lines), 'dated': 0, 'undated': 0, 'headers': 0}
    offset = ''
    version = ''
    header_event = None
    for number, line in enumerate(lines, 1):
        dated = _LOG_TIME.match(line)
        if not dated:
            counts['undated'] += 1
            start = _HEADER_START.match(line)
            if start:
                counts['headers'] += 1
                offset = start.group(2) or ''
                version = ''
                header_event = {'time': start.group(1), 'offset': offset, 'version': '',
                                'type': 'Log header Start', 'message': line.rstrip(),
                                'line': number}
                events.append(header_event)
                counts['Log header Start'] = counts.get('Log header Start', 0) + 1
                continue
            stored = _HEADER_VERSION.match(line)
            if header_event is not None and stored:
                version = stored.group(1)
                header_event['version'] = version
            continue
        header_event = None
        counts['dated'] += 1
        fields = _LOG_FIELDS.match(line[dated.end(1):])
        message = (fields.group(1) or '').rstrip() if fields else ''
        if not message:
            continue
        for kind, rule in _LOG_RULES:
            if rule.search(message):
                events.append({'time': dated.group(1), 'offset': offset, 'version': version,
                               'type': kind, 'message': message, 'line': number})
                counts[kind] = counts.get(kind, 0) + 1
                break
    return events, counts


def _read_files(context, label, wanted):
    """(relative path, text, source) for each file found whose name passes wanted()."""
    results = []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isdir(source) or not wanted(os.path.basename(source)):
            continue
        relative = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                text, replaced = decode_text(handle.read())
        except OSError as exc:
            logfunc(f'{label}: could not read {relative}: {exc}')
            continue
        if replaced:
            logfunc(f'{label}: {relative}: {replaced} bytes that are not UTF-8 replaced')
        results.append((relative, text, source))
    return results


def _is_list(name):
    return name.lower() in ('connections_incoming.txt', 'connections.txt')


def _is_log(name):
    lowered = name.lower()
    return lowered.startswith('teamviewer') and '_logfile' in lowered and lowered.endswith('.log')


@artifact_processor
def teamViewerConnections(context):
    data_headers = ('Start Time (as stored)', 'End Time (as stored)', 'TeamViewer ID',
                    'Display Name', 'Local User', 'Connection Type', 'Connection GUID',
                    'Line', 'Source File')
    data_list = []
    sources = []
    for relative, text, source in _read_files(context, 'TeamViewer Connection Lists', _is_list):
        sources.append(source)
        records, unread = parse_connection_list(text)
        for r in records:
            data_list.append((r['start'], r['end'], r['id'], r['name'], r['user'], r['type'],
                              r['guid'], r['line'], relative))
        logfunc(f'TeamViewer Connection Lists: {len(records)} list lines read from {relative}, '
                f'{unread} non-blank lines not in a list layout')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def teamViewerLogEvents(context):
    data_headers = ('Time (as stored)', 'Log Header UTC Offset (as stored)', 'Line Type', 'Message',
                    'Log Header Version', 'Line', 'Source File')
    data_list = []
    sources = []
    for relative, text, source in _read_files(context, 'TeamViewer Log Events', _is_log):
        sources.append(source)
        events, counts = parse_log(text)
        for e in events:
            data_list.append((e['time'], e['offset'], e['type'], e['message'], e['version'],
                              e['line'], relative))
        order = dict.fromkeys(['Log header Start'] + [kind for kind, _ in _LOG_RULES])
        kinds = ', '.join(f'{kind} {counts[kind]}' for kind in order if counts.get(kind)) or 'none'
        logfunc(f'TeamViewer Log Events: {relative}: {counts["lines"]} lines, '
                f'{counts["dated"]} dated, {counts["undated"]} without a date '
                f'({counts["headers"]} Start header lines); {len(events)} reported ({kinds}); '
                f'{counts["lines"] - len(events)} lines not reported')
    return data_headers, data_list, '\n'.join(sources)
