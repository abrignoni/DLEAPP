""".NET CLR usage log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the files the .NET Framework CLR writes in a profile's
AppData\\Local\\Microsoft\\CLR_v<version>\\UsageLogs folder (and the same folder
under a packaged app's LocalCache\\Local), one per program, named after the
program with .log appended. Each row names the program, the profile and CLR
folder the file sits in, the file's created and modified times when the input is
a disk image, and the file's text as stored. Sources are in the notes.
"""

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import user_from_path

_LABEL = 'CLR Usage Logs'
_SUFFIX = '.log'

__artifacts_v2__ = {
    "clrUsageLogs": {
        "name": "CLR Usage Logs",
        "description": "Programs named by the usage log files the .NET Framework CLR writes "
                       "per profile, with the profile and CLR folder each file sits in, the "
                       "file's created and modified times from a disk image, and the file's "
                       "text as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the files in a profile's AppData\\Local\\Microsoft\\CLR_v<version>\\UsageLogs "
                 "folder, and in the same folder under a packaged app's LocalCache\\Local, each named in "
                 "the report's located-at line; one row per file. bohops describes these as usage logs the "
                 ".NET CLR writes, named after the executing process, when a program finishes executing "
                 "for the first time in a user's context: the file is written just before a graceful exit "
                 "and not written when the process is forced to terminate ('Investigating .NET CLR Usage "
                 "Log Tampering Techniques For EDR Evasion', 16 March 2021, "
                 "https://bohops.com/2021/03/16/investigating-net-clr-usage-log-tampering-techniques-for-edr-evasion/). "
                 "His part 2 adds that the CLR writes the file if one does not already exist, and lists "
                 "CLR_v4.0 for 64-bit and CLR_v4.0_32 for 32-bit .NET 4.0, at user level under "
                 "AppData\\Local\\Microsoft and at system level under config\\systemprofile (22 August 2022, "
                 "https://bohops.com/2022/08/22/investigating-net-clr-usage-log-tampering-techniques-for-edr-evasion-part-2/). "
                 "Program is the file name without its .log ending, as the file carries it, which can be a "
                 "short 8.3 name (SYNCRE~1.EXE on lonewolf_win10). Profile is the folder under Users, "
                 "systemprofile for a file under config\\systemprofile, or the folder under "
                 "ServiceProfiles. CLR Folder is the CLR_v folder the file sits in: CLR_v4.0 or "
                 "CLR_v4.0_32 on the tested images. Package is the packaged app folder when the file sits "
                 "under Packages\\<package>\\LocalCache: Microsoft.MicrosoftOfficeHub_8wekyb3d8bbwe on one "
                 "pc_mus_001_win11 file and three szechuan_win10 files, and empty on every row of "
                 "af_case2_win10 and lonewolf_win10. Log Text is the file's text as stored, read as UTF-8 "
                 "with its line breaks kept; every file on the tested images decoded without a replacement "
                 "character and began with the line 1,\"fusion\",\"GAC\",0. What the numbered records mean is "
                 "not established here, so they are not decoded. Created (UTC) and Modified (UTC) are the "
                 "file's $STANDARD_INFORMATION created and modified times as the raw image reader reports "
                 "them, in seconds, so they can differ by a microsecond from the stored FILETIME (checked "
                 "against The Sleuth Kit's istat on one pc_mus_001_win11 file); they are blank for a "
                 "folder or archive input, whose copy's times are not the evidence's. Modified was later "
                 "than Created on 7 of 9 files of af_case2_win10 (by up to 1,434 days), 13 of 19 of "
                 "lonewolf_win10 and 16 of 25 of pc_mus_001_win11, and equal to it on the rest, including "
                 "all 7 of szechuan_win10, so a file is written again after it is created and Modified is "
                 "not the time of its first write. A row names a program the CLR logged for that profile; "
                 "a program whose process was forced to terminate before a graceful exit leaves no file, "
                 "per bohops.",
        "paths": ("*/AppData/Local/Microsoft/CLR_v*/UsageLogs/*",
                  "*/LocalCache/Local/Microsoft/CLR_v*/UsageLogs/*"),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 9 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 19 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 25 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 7 rows",
        },
    },
}


def _instant(value):
    """A FileInfo time (seconds since 1970, UTC) as an aware datetime, or ''."""
    if not value:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def location(relative):
    """(profile, CLR folder, package) for a usage log's path within the extraction."""
    parts = relative.replace('\\', '/').split('/')
    lower = [part.lower() for part in parts]
    profile = user_from_path(relative)
    if not profile:
        if 'systemprofile' in lower:
            profile = 'systemprofile'
        elif 'serviceprofiles' in lower:
            index = lower.index('serviceprofiles')
            profile = parts[index + 1] if index + 1 < len(parts) else ''
    clr = next((part for part in parts if part.lower().startswith('clr_v')), '')
    package = ''
    if 'packages' in lower:
        index = lower.index('packages')
        if index + 2 < len(parts) and lower[index + 2] == 'localcache':
            package = parts[index + 1]
    return profile, clr, package


def log_text(raw):
    """The file's bytes as text: UTF-8, with anything that does not decode replaced."""
    return raw.decode('utf-8', 'replace').replace('\r\n', '\n').strip('\n')


@artifact_processor
def clrUsageLogs(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'Program',
                    'Profile', 'CLR Folder', 'Package', 'Log Text')
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    # Only a disk image gives the evidence's own times; a folder or archive
    # gives the times of the copy.
    from_image = hasattr(seeker, 'stream_list')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        name = os.path.basename(path)
        if os.path.isdir(path) or not name.lower().endswith(_SUFFIX):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                raw = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        info = infos.get(path)
        created = modified = ''
        if from_image and info:
            created, modified = _instant(info.creation_date), _instant(info.modification_date)
        data_list.append((created, modified, name[:-len(_SUFFIX)], *location(relative),
                          log_text(raw)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
