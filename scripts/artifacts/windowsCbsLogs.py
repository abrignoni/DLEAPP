"""Windows Component-Based Servicing (CBS) and DISM text log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Windows\\Logs\\CBS\\CBS.log, the older logs kept beside it as CbsPersist_*.log and
CbsPersist_*.cab, Windows\\Panther\\cbs.log and Windows\\Logs\\DISM\\dism.log. Each line begins
with a local time, a level and a component. The CBS logs also write the time in UTC at each
TiWorker start ("Universal Time is"), which is how the CBS rows get a UTC time; dism.log
writes no such line, so its times are reported as recorded.
"""

import datetime
import re
import struct
import zlib
from collections import Counter

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
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are "
                 "continuation lines and are not read. A cab is read when it holds one folder and one file compressed "
                 "with MSZIP: the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)) and each MSZIP block is a CK "
                 "signature and a deflate stream whose history carries over from the block before, per [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69). "
                 "Every block's recorded uncompressed size and the file's recorded size are checked, and a cab that fails "
                 "is named in the run log and not read. The six tested cabs were all MSZIP with one folder and one file, "
                 "and all of them passed; a cab of another kind is refused and was not seen. Times: each line's time is "
                 "local and carries no zone. The CBS logs also write a line 'Universal Time is: <time>' when TiWorker "
                 "starts, and the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- "
                 "Initializing Trusted Installer ---' line to the next, and each row takes the offset of the last UTC "
                 "line before it in its run, or of the run's first UTC line when none comes before it. A run with no UTC "
                 "line leaves the UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no "
                 "UTC line and no TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC "
                 "lines with two offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the "
                 "package state lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), "
                 "the CSI lines including the '[SR]' lines (150 on the tested images: 138 on hexordia_mvs2025_win11 and "
                 "12 on lonewolf_win10, every one in a run of one-component verify transactions after a 'Client requests "
                 "SFP repair object' line; no known data of an sfc run was available to say what they record), the DISM "
                 "lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and the ETL files in "
                 "Logs\\WindowsUpdate and Logs\\CBS. One row per 'TI: --- Initializing Trusted Installer ---' line, with "
                 "the first 'TI: Last boot time' and 'Loaded Servicing Stack' lines of its run. Last Boot Time is written "
                 "as a local time; it is moved to UTC with the run's offset. Checked against Kernel Boot Events on the "
                 "six tested images that have kernel boot events and an offset other than UTC+00:00 "
                 "(alihadi_threatsim_server2019 has no kernel boot event, so it was not checked): 142 of the 149 starts "
                 "with a boot time and an offset fell within 2 minutes of a kernel boot event once the offset was "
                 "applied, and none did when the time was read as UTC. Of the other 7, 6 name a boot earlier than the "
                 "first kernel boot event the image holds, and 1 on szechuan_win10 had no kernel boot event within 17 "
                 "minutes. On lonewolf_win10 one boot was named at UTC-07:00 and later at UTC-04:00, and both give the "
                 "same UTC time. Start Time (UTC) and UTC Offset (from the log) were blank on 11 of the 412 tested rows "
                 "(7 on lonewolf_win10, 3 on hexordia_mvs2025_win11, 1 on szechuan_win10), and on all 11 the run had no "
                 "Servicing Stack line either. UTC Offset (from the log) held one value on all rows of pc_mus_001_win11, "
                 "szechuan_dc01_server2012r2, ou_ransomware_server2022 and alihadi_threatsim_server2019, and two on "
                 "af_case2_win10, lonewolf_win10 and hexordia_mvs2025_win11. Servicing Stack Version held one value on "
                 "all rows of szechuan_dc01_server2012r2, ou_ransomware_server2022 and alihadi_threatsim_server2019.",
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
                 "Each line the artifact reads begins with a local time, a level and a component; other lines are "
                 "continuation lines and are not read. A cab is read when it holds one folder and one file compressed "
                 "with MSZIP: the cab layout follows the Microsoft Cabinet File Format "
                 "(https://learn.microsoft.com/en-us/previous-versions/bb417343(v=msdn.10)) and each MSZIP block is a CK "
                 "signature and a deflate stream whose history carries over from the block before, per [MS-MCI] "
                 "(https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-mci/3048c471-f739-4d30-bcb3-a962cfe84a69). "
                 "Every block's recorded uncompressed size and the file's recorded size are checked, and a cab that fails "
                 "is named in the run log and not read. The six tested cabs were all MSZIP with one folder and one file, "
                 "and all of them passed; a cab of another kind is refused and was not seen. Times: each line's time is "
                 "local and carries no zone. The CBS logs also write a line 'Universal Time is: <time>' when TiWorker "
                 "starts, and the UTC columns come from that line: a TrustedInstaller run is the lines from one 'TI: --- "
                 "Initializing Trusted Installer ---' line to the next, and each row takes the offset of the last UTC "
                 "line before it in its run, or of the run's first UTC line when none comes before it. A run with no UTC "
                 "line leaves the UTC columns blank, and cfreds_leakage_win7, the only Windows 7 image tested, writes no "
                 "UTC line and no TrustedInstaller start line at all. One run on alihadi_threatsim_server2019 held UTC "
                 "lines with two offsets; the run log counts such runs. Not read: the 'Appl:' applicability lines and the "
                 "package state lines (the Windows Servicing Events artifact reports package changes from Setup.evtx), "
                 "the CSI lines including the '[SR]' lines (150 on the tested images: 138 on hexordia_mvs2025_win11 and "
                 "12 on lonewolf_win10, every one in a run of one-component verify transactions after a 'Client requests "
                 "SFP repair object' line; no known data of an sfc run was available to say what they record), the DISM "
                 "lines Panther\\cbs.log also holds, Windows\\servicing\\Sessions\\*.xml, and the ETL files in "
                 "Logs\\WindowsUpdate and Logs\\CBS. One row per 'Session: <ID> initialized by client <client>' line of "
                 "the CBS component, with the client as the line names it (the text after it from ', external staging "
                 "directory' on, and a trailing period, are dropped). The Session ID is reported as stored; what its two "
                 "numbers are is not established here. 2,475 rows on the tested images, naming 19 clients, of which "
                 "WindowsUpdateAgent was the most common (1,605 rows). Session Start (UTC) and UTC Offset (from the log) "
                 "are empty on all 30 rows of cfreds_leakage_win7, whose logs write no UTC line. UTC Offset (from the "
                 "log) held one value on all rows of pc_mus_001_win11, szechuan_dc01_server2012r2 and "
                 "alihadi_threatsim_server2019. A session line records that the session was initialized, not what it "
                 "changed.",
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
                 "or for Dism.exe the first PID on a line of the session. Reboot Required (as stored) is the value of the "
                 "'Image session has been closed. Reboot required=' line, written only in Dism.exe sessions (13 yes and "
                 "17 no on the tested images). End Time is the session's ending line, blank when there is none: 12 rows "
                 "on the tested images, 3 each on pc_mus_001_win11, szechuan_dc01_server2012r2, ou_ransomware_server2022 "
                 "and alihadi_threatsim_server2019; the run log counts them. Times are local, as recorded: dism.log "
                 "writes no zone and no UTC line. The CBS artifacts give the offset the CBS logs recorded, which this "
                 "artifact does not apply. 3,301 rows on the tested images, 30 Dism.exe sessions (each with a Command "
                 "Line) and 3,271 DismApi.dll sessions (each with a Parent Process Command Line); 3,179 of the "
                 "DismApi.dll sessions were on ou_ransomware_server2022. Session Kind held one value on all rows of "
                 "pc_mus_001_win11, af_case2_win10, lonewolf_win10 and cfreds_leakage_win7, so Command Line and Reboot "
                 "Required (as stored) are empty on the first three and Parent Process Command Line on the last. Not "
                 "read: the other dism.log lines, and the DISM lines Windows\\Panther\\cbs.log holds.",
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
_PID = re.compile(r'PID=(\d+)')
_DISM_EXE_START = 'DISM.EXE: <----- Starting Dism.exe session ----->'
_DISM_EXE_END = 'DISM.EXE: <----- Ending Dism.exe session ----->'
_DISM_API_START = 'DismApi.dll: <----- Starting DismApi.dll session ----->'
_DISM_API_END = 'DismApi.dll: <----- Ending DismApi.dll session ----->'
_EXECUTING = re.compile(r'DISM\.EXE: Executing command line: (.*)')
_PARENT = re.compile(r'DismApi\.dll: Parent process command line: (.*?)(?: - DismInitializeInternal)?$')
_REBOOT = re.compile(r'Image session has been closed\. Reboot required=(\S+?)\.?$')

_MSZIP = 1


class CabError(ValueError):
    """A cab this reader does not read: not a cab, more than one folder or file, or not MSZIP."""


def mszip_cab_member(data):
    """The name and bytes of the one file in a cabinet whose one folder is MSZIP compressed.

    Layout per [MS-CAB] (CFHEADER, CFFOLDER, CFFILE, CFDATA) and MSZIP per [MS-MCI]: each CFDATA
    block is "CK" and a deflate stream whose history is the previous 32 KiB of output. Every block's
    recorded uncompressed size and the file's recorded size are checked; a mismatch raises.
    """
    if data[:4] != b'MSCF':
        raise CabError('not a cabinet (no MSCF signature)')
    coff_files, = struct.unpack_from('<I', data, 16)
    folders, files, flags = struct.unpack_from('<HHH', data, 26)
    if folders != 1 or files != 1:
        raise CabError(f'{folders} folders and {files} files, where one of each is read')
    offset, per_data = 36, 0
    if flags & 4:
        reserve_header, _, per_data = struct.unpack_from('<HBB', data, 36)
        offset += 4 + reserve_header
    first_data, blocks, compression = struct.unpack_from('<IHH', data, offset)
    if compression & 0xf != _MSZIP:
        raise CabError(f'compression type {compression & 0xf}, where only MSZIP (1) is read')
    size, _, _, _, _, _ = struct.unpack_from('<IIHHHH', data, coff_files)
    name_at = coff_files + 16
    name = data[name_at:data.index(b'\0', name_at)].decode('latin-1')
    out, position = bytearray(), first_data
    for _ in range(blocks):
        _, packed, unpacked = struct.unpack_from('<IHH', data, position)
        position += 8 + per_data
        block = data[position:position + packed]
        position += packed
        if block[:2] != b'CK':
            raise CabError('an MSZIP block without its CK signature')
        history = bytes(out[-32768:])
        inflater = zlib.decompressobj(-15, zdict=history) if history else zlib.decompressobj(-15)
        chunk = inflater.decompress(block[2:]) + inflater.flush()
        if len(chunk) != unpacked:
            raise CabError(f'a block gave {len(chunk)} bytes where the cab records {unpacked}')
        out += chunk
    if len(out) != size:
        raise CabError(f'{len(out)} bytes where the cab records {size} for {name}')
    return name, bytes(out)


def log_text(path):
    """The text of a log, or of the log a CbsPersist cab holds, and what was replaced on decoding."""
    with open(path, 'rb') as handle:
        data = handle.read()
    if path.lower().endswith('.cab'):
        _, data = mszip_cab_member(data)
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


def cbs_events(text, problems):
    """The TrustedInstaller starts and the sessions of one CBS log, each with its UTC offset.

    A run is the lines from one "Initializing Trusted Installer" line to the next (the lines before
    the first are a run of their own). A row takes the offset of the last UTC line before it in its
    run, or the run's first UTC line when none comes before it; a run with none leaves UTC blank.
    """
    runs = [[]]
    for local, component, message in log_lines(text):
        if component == 'CBS' and message == _TI_START:
            runs.append([])
        runs[-1].append((local, component, message))
    starts, sessions = [], []
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
        start = {}
        for local, component, message in run:
            if _UTC.search(message):
                current = offsets[seen]
                seen += 1
                continue
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


def dism_sessions(text, problems):
    """One dict per Dism.exe or DismApi.dll session of a dism.log, in the order they start."""
    sessions, open_exe, open_api = [], None, {}
    for local, _, message in log_lines(text):
        pid = _PID.search(message)
        pid = pid.group(1) if pid else ''
        if _DISM_EXE_START in message:
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
        except (OSError, CabError, zlib.error, struct.error) as exc:
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
