"""The program paths in Windows 7's RecentFileCache.bcf, for DLEAPP.

Author: @AlexisBrignoni, Claude.

The file's layout is the one Eric Zimmerman's RecentFileCacheParser reads (RecentFileCache/RecentFileCacheFile.cs,
github.com/EricZimmerman/RecentFileCacheParser at commit cad0934d8c7910ad40c0839609453ee629bd9458): a four-byte
signature, then from offset 0x14 one entry after another, each a 32-bit count of characters, the path in UTF-16
and a two-byte terminator.
"""

__artifacts_v2__ = {
    "windowsRecentFileCache": {
        "name": "RecentFileCache.bcf",
        "description": "The program paths listed in Windows/AppCompat/Programs/RecentFileCache.bcf, a Windows 7 "
                       "file that Corey Harrell's research attributes to the Application Experience service, in "
                       "the order the file holds them, with the time the file was last written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-14",
        "last_update_date": "2026-10-29",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads Windows/AppCompat/Programs/RecentFileCache.bcf and reports one row per entry, in the order "
                 "the file holds them. The layout is the one Eric Zimmerman's RecentFileCacheParser reads "
                 "(Reference: RecentFileCacheParser, 'RecentFileCache/RecentFileCacheFile.cs', "
                 "https://github.com/EricZimmerman/RecentFileCacheParser/blob/cad0934d8c7910ad40c0839609453ee629bd9458/RecentFileCache/RecentFileCacheFile.cs): "
                 "a four-byte signature, FE FF EE FF, then from offset 0x14 one entry after another, each a 32-bit "
                 "count of characters, the path in UTF-16 and a two-byte terminator. Of the bytes between the signature and the first entry only the CRC-32 at offset 0x10 is read. File Checksum Matches is Yes when that value equals the CRC-32, as zlib computes it, of the file with those four bytes left out, the check RecentFileCacheParser makes since its 2026.10 release (https://github.com/EricZimmerman/RecentFileCacheParser/blob/f953a6028c09a57006be1fec365a69cda7c87acf/RecentFileCache/RecentFileCacheFile.cs#L62-L63, https://github.com/EricZimmerman/RecentFileCacheParser/blob/f953a6028c09a57006be1fec365a69cda7c87acf/RecentFileCache/Crc32.cs#L27-L45), and No when it does not; a mismatch is also named in the run log. A file shorter than 0x14 bytes yields no rows. It is the same on every row of a file. It was Yes on cfreds_leakage_win7, and the same computation gives the values RecentFileCacheParser's tests assert for its two sample files (0xF4637B64 and 0xE5918E10). No real file with a mismatch has been seen; No is exercised only with constructed input. Program Path is the path decoded from UTF-16, where "
                 "an invalid sequence would show as a replacement character, and Entry its position in the file. A "
                 "file that does not start with the signature, or an entry that runs past the end of the file or "
                 "is not followed by its terminator, is named in the run log, and the entries read before it are "
                 "reported. What the list holds comes from Corey Harrell's research, not from Microsoft "
                 "(Reference: \"Revealing the RecentFileCache.bcf File\", Journey Into Incident Response, 2 December "
                 "2013, https://journeyintoir.blogspot.com/2013/12/revealing-recentfilecachebcf-file.html): the "
                 "Application Experience service records an executable's full path in it; in the author's testing "
                 "it held references to programs that recently executed, mostly from executables newly created on "
                 "the system by copying, downloading or extracting, though he also reports seeing references to "
                 "executables that were present but never executed, which he could not reproduce; it is cleared "
                 "when the Application Experience ProgramDataUpdater task runs, which on his test system was "
                 "scheduled daily at 12:30 AM; and Windows 8 replaced it with the Amcache.hve hive. An entry holds "
                 "only its character count and path; neither source gives a time per entry. File Last Written is "
                 "the file's own last-written time as the seeker recorded it, so it is the same on every row of a "
                 "file. For a raw image or E01 that is the file's $STANDARD_INFORMATION last-written time. The "
                 "$MFT artifact cuts NTFS's 100-nanosecond ticks down to whole microseconds, while this column "
                 "passes through floating-point seconds and is rounded to the nearest microsecond, so the two can "
                 "differ by one microsecond for the same file. Validated on cfreds_leakage_win7, the NIST CFReDS "
                 "Data Leakage Case PC (Windows 7 Ultimate SP1): 21 rows, 21 distinct paths, all ending .exe and "
                 "written in lower case, 17 of them under c:\\windows. File Last Written held one value on all 21 "
                 "rows, 2015-03-25 15:15:52.256006 UTC, one microsecond later than the $MFT artifact's SI Modified "
                 "for the file, 2015-03-25 15:15:52.256005 UTC. The corpus's 16 other Windows disk images, among them pc_mus_001_win11, af_case2_win10, lonewolf_win10, szechuan_win10 and szechuan_dc01_server2012r2, hold no live file by that name, matching Windows and Programs exactly, AppCompat with either case on its two initials, and the file name with either case on its three initials. A row shows that a path was in the file when it was acquired; it "
                 "gives no time, and by itself does not show that the program ran. Not exercised on real data: a "
                 "damaged file, tested with constructed input, and an input other than a raw image or E01: for a "
                 "tar File Last Written is the member's recorded modified time, for a zip its NTFS or extended "
                 "timestamp field when present, and for a folder or single file the modified time of the examiner's copy.",
        "paths": ('*/Windows/[Aa]pp[Cc]ompat/Programs/[Rr]ecent[Ff]ile[Cc]ache.bcf',),
        "output_types": "standard",
        "artifact_icon": "list",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no RecentFileCache.bcf)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no RecentFileCache.bcf)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no RecentFileCache.bcf)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no RecentFileCache.bcf)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (no RecentFileCache.bcf)",
        },
    },
}

import os
import struct
import zlib

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_time, seeker_of

_LABEL = 'RecentFileCache.bcf'
_SIGNATURE = b'\xfe\xff\xee\xff'                # 0xFFEEFFFE read little-endian
_FIRST_ENTRY = 0x14
_CHECKSUM = 0x10


def checksum_matches(data):
    """'Yes' when the CRC-32 stored at 0x10 equals the CRC-32 (zlib's) of the file with those 4 bytes left
    out, 'No' when it does not, '' for a file too short to hold it."""
    if len(data) < _FIRST_ENTRY:
        return ''
    stored, = struct.unpack_from('<I', data, _CHECKSUM)
    return 'Yes' if stored == zlib.crc32(data[:_CHECKSUM] + data[_CHECKSUM + 4:]) & 0xFFFFFFFF else 'No'


def entries(data):
    """(paths, problem) for a RecentFileCache.bcf's bytes: the paths in file order, and '' when every entry
    was read to the end of the file, or what stopped the reading."""
    if data[:4] != _SIGNATURE:
        return [], 'does not start with the RecentFileCache signature'
    paths, position = [], _FIRST_ENTRY
    while position < len(data):
        if position + 4 > len(data):
            return paths, f'ends inside the length of an entry at offset {position}'
        characters, = struct.unpack_from('<i', data, position)
        start = position + 4
        end = start + 2 * characters
        if characters < 0 or end + 2 > len(data):
            return paths, f'has an entry at offset {position} that runs past the end of the file'
        if data[end:end + 2] != b'\0\0':
            return paths, f'has an entry at offset {position} that is not followed by its terminator'
        paths.append(data[start:end].decode('utf-16-le', 'replace'))
        position = end + 2
    return paths, ''


@artifact_processor
def windowsRecentFileCache(context):
    data_headers = (('File Last Written', 'datetime'), 'Program Path', 'Entry', 'File Checksum Matches')
    data_list, read = [], []
    seeker = seeker_of(context)
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path).lower() != 'recentfilecache.bcf':
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}')
            continue
        paths, problem = entries(data)
        if problem:
            logfunc(f'{_LABEL}: {relative} {problem}; {len(paths):,} entries read before it')
        written = recorded_time(seeker, path, None) if seeker is not None else ''
        matches = checksum_matches(data)
        if matches == 'No':
            logfunc(f'{_LABEL}: {relative} holds a CRC-32 at 0x10 that does not match its contents')
        data_list.extend((written, program, number, matches) for number, program in enumerate(paths, 1))
        if paths:
            read.append(path)
    return data_headers, data_list, '\n'.join(read)
