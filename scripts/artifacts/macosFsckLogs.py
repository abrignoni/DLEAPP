"""File system check runs recorded in the fsck logs macOS keeps in private/var/log, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosFsckLogs": {
        "name": "fsck Logs",
        "description": "Runs of fsck_apfs, fsck_hfs and other fsck programs recorded in the fsck "
                       "logs: start and completion time as written, device, program and the lines "
                       "the run wrote.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "File System (macOS)",
        "notes": "Reads each fsck log in a folder ending var/log (private/var/log on a Mac), such as "
                 "fsck_apfs.log and fsck_hfs.log, and in a Library/Logs folder, one row per run in the "
                 "file's order; a log whose name ends in _error.log, such as fsck_apfs_error.log, whose "
                 "lines are in another form, is not read. A run begins with a line '<device>: <program> "
                 "started at <time>' and ends with '<device>: <program> completed at <time>', and Messages "
                 "holds the non-empty lines between them as stored. Apple's source for fsck_hfs writes "
                 "those two lines with ctime, and without the device when it had to hold the log in memory "
                 "while checking "
                 "(https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L453 "
                 "and "
                 "https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L288, "
                 "and "
                 "https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L476 "
                 "and "
                 "https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L286); "
                 "it appends to /var/log/fsck_hfs.log "
                 "(https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L83 "
                 "and "
                 "https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L249-L264) "
                 "and, when not run as root, writes Library/Logs/fsck_hfs.log in the user's home folder "
                 "instead "
                 "(https://github.com/apple-oss-distributions/hfs/blob/d1bac2f062e6e9c0dfcce302d9aacb10173d0eea/fsck_hfs/utilities.c#L358-L369). "
                 "No tested image held a copy under Library/Logs. Program told the MacBook Pro's two logs "
                 "apart, but it does not separate every file a row can come from, since "
                 "/var/log/fsck_hfs.log and each user's Library/Logs/fsck_hfs.log all hold fsck_hfs runs, "
                 "so Source File stays. Apple's ctime manual gives the local date and time with no offset "
                 "(https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/stdtime/FreeBSD/ctime.3#L135-L143), "
                 "so Started (as written) and Completed (as written) are text as stored. A GitHub code "
                 "search of apple-oss-distributions found no source that writes the fsck_apfs lines; on "
                 "both tested images they have the same form. A run with no completion line keeps a blank "
                 "Completed (as written), a completion line with no open run of the same program and "
                 "device is a row of its own, a non-empty line outside any run is a row with only "
                 "Messages, and a file with no run is logged and not read. On dleapp_macos_bigsur "
                 "fsck_apfs.log held 40 runs, dated 2021-02-15 to 2021-02-19 as written, on seven devices "
                 "under /dev/rdisk1, so Program held one value, fsck_apfs, on all 40 rows. On the public "
                 "MacBook Pro logical extraction (macOS 15.4, not a registered corpus key) fsck_apfs.log "
                 "held 75 runs, dated 2025-09-03 to 2025-12-12, on seven devices under /dev/rdisk1 and on "
                 "/dev/rdisk3s1, and fsck_hfs.log held 11 runs, dated 2025-09-12 to 2025-12-24, on "
                 "/dev/rdisk2, /dev/rdisk2s1, /dev/rdisk2s2 and /dev/rdisk4s2. The 9 runs on /dev/rdisk3s1 "
                 "were full checks whose Messages name the volume in a line 'The volume <name> was "
                 "formatted by ...', and they named three different volumes, so a device node alone does "
                 "not identify a volume; none of the other 117 runs on the two images named one. Started "
                 "(as written) and Completed (as written) were identical on all 40 and all 86 rows, every "
                 "tested run ending within the second it began; they are read from separate lines, and the "
                 "module's tests give them different times. The same log held at the root and under "
                 "System/Volumes/Data is one log captured twice: a run is reported as many times as the "
                 "copy holding it most often does, from the copy with more runs, or the one at the root "
                 "when both hold the same number. The MacBook Pro's two copies of each log were "
                 "byte-identical. Bytes that are not valid UTF-8 are shown as the Unicode replacement "
                 "character; there were none in the tested files.",
        "paths": ('*/var/log/fsck_*.log', '*/Library/Logs/fsck_*.log'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 40 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

_CTIME = r'[A-Z][a-z]{2} [A-Z][a-z]{2} [ \d]\d \d{2}:\d{2}:\d{2} \d{4}'
# "<device>: <program> started at <ctime>", the device left out when the program could not name it.
_STARTED = re.compile(rf'^(?:(\S+): )?(fsck_\w+) started at ({_CTIME})$')
_COMPLETED = re.compile(rf'^(?:(\S+): )?(fsck_\w+) completed at ({_CTIME})$')
_FIRMLINK = re.compile(r'(^|/)System/Volumes/Data/')


def _runs(text):
    """(started, completed, device, program, messages) per run in the file's order. A run with no
    completion line keeps a blank Completed, a completion line with no start becomes a run of its
    own, and a non-empty line outside any run becomes a row with only messages."""
    runs = []
    current = None
    for line in text.split('\n'):
        match = _STARTED.match(line)
        if match:
            device, program, started = match.groups()
            current = [started, '', device or '', program, []]
            runs.append(current)
            continue
        match = _COMPLETED.match(line)
        if match:
            device, program, completed = match.groups()
            if current is not None and current[3] == program and current[2] == (device or ''):
                current[1] = completed
            else:
                runs.append(['', completed, device or '', program, []])
            current = None
            continue
        if not line.strip():
            continue
        if current is None:
            current = ['', '', '', '', []]
            runs.append(current)
        current[4].append(line)
    return [(started, completed, device, program, '\n'.join(messages))
            for started, completed, device, program, messages in runs]


def _read(path):
    try:
        with open(path, 'rb') as handle:
            return handle.read().decode('utf-8', errors='replace')
    except OSError:
        return None


@artifact_processor
def macosFsckLogs(context):
    data_headers = ('Started (as written)', 'Completed (as written)', 'Device', 'Program', 'Messages',
                    'Source File')
    data_list = []
    sources = []
    stores = {}
    for path in context.get_files_found():
        name = os.path.basename(path)
        if os.path.isdir(path) or not re.fullmatch(r'fsck_\w+\.log', name) or name.endswith('_error.log'):
            continue
        relative = context.get_relative_path(path).replace('\\', '/')
        key = _FIRMLINK.sub(r'\1', relative, count=1)
        stores.setdefault(key, {})[relative] = path
    repeated = 0
    for views in stores.values():
        read = []
        for relative in sorted(views):
            path = views[relative]
            text = _read(path)
            if text is None:
                logfunc(f'fsck Logs: could not read {relative}')
                continue
            runs = _runs(text)
            if not any(run[3] for run in runs):
                logfunc(f'fsck Logs: no fsck run in {relative}')
                continue
            read.append((relative, [(run, path) for run in runs]))
        # The same log reached at the root and under System/Volumes/Data is one log captured twice:
        # each run is reported as many times as the copy holding it most often does.
        wanted = Counter()
        for _relative, rows in read:
            wanted |= Counter(run for run, _path in rows)
        done = Counter()
        # The copy with more runs goes first, and of two equal copies the one at the root.
        read.sort(key=lambda view: (-len(view[1]), bool(_FIRMLINK.search(view[0])), view[0]))
        for _relative, rows in read:
            for run, path in rows:
                if done[run] < wanted[run]:
                    done[run] += 1
                    data_list.append(run + (context.get_relative_path(path),))
                    if path not in sources:
                        sources.append(path)
                else:
                    repeated += 1
    if repeated:
        logfunc(f'fsck Logs: {repeated} runs the other view of the same log also holds not reported again')
    logfunc(f'fsck Logs: {len(data_list)} runs from {len(sources)} file(s).')
    return data_headers, data_list, '\n'.join(sources)
