"""NTFS master file table ($MFT), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The record and attribute layouts follow the Linux-NTFS project's NTFS
documentation; see scripts/windows_ntfs.py for the citations. The $MFT is read
twice: once for the directory tree and the extension records, and once more to
report each record, so a volume of any size is never held whole.
"""

__artifacts_v2__ = {
    "windowsMft": {
        "name": "MFT",
        "description": "Named records of an NTFS master file table, in use or not: the four "
                       "$STANDARD_INFORMATION and four $FILE_NAME times, the path where it resolves, size, "
                       "named streams and, where the volume's $Secure:$SDS was read, the "
                       "owner SID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per base record of each $MFT that holds at least one $FILE_NAME, "
                 "whether or not the record is in use; extension records are folded into the "
                 "record they extend. The layout follows the Linux-NTFS documentation "
                 "(Reference: https://github.com/flatcap/ntfs-docs/blob/641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29/concepts/file_record.html#L68-L231,"
                 " attributes/standard_information.html#L53-L134 and "
                 "attributes/file_name.html#L47-L114 at the same commit). The SI times are "
                 "$STANDARD_INFORMATION's C, A, M and R times, which that documentation names "
                 "File Creation, File Altered, MFT Changed and File Read, reported as SI "
                 "Created, SI Modified, SI Record Changed and SI Accessed; the FN times are the "
                 "same four from the $FILE_NAME that names the row. The documentation notes that "
                 "$FILE_NAME's times are updated only when the name changes "
                 "(attributes/file_name.html#L218-L222), so the two sets can differ without "
                 "anything having altered either. Name and Path come from a "
                 "long name in preference to its DOS 8.3 alias; Path runs from the volume's "
                 "root (/) through each parent reference, and is blank when a parent's record "
                 "has since been reused (its sequence number no longer matches, allowing for "
                 "the one increment NTFS makes when it frees a record) or the chain does not "
                 "reach the root. Other Links lists the paths of the record's further names, "
                 "one per hard link. In Use is the record's in-use flag: No means the record "
                 "is free and still names a file. Size (bytes) is the unnamed $DATA's real "
                 "size and is blank for a directory, or when the record holds no first extent "
                 "of it. Named Streams lists each named $DATA with its recorded size. Owner SID is the "
                 "owner in the security descriptor that $STANDARD_INFORMATION's Security Id "
                 "names in the same volume's $Secure:$SDS (Reference: files/secure.html#L108-L159"
                 " and attributes/security_descriptor.html#L138-L181 at the same commit); it is "
                 "blank when no $Secure:$SDS was read beside the $MFT, when the record's "
                 "$STANDARD_INFORMATION is the 48-byte form that carries no Security Id, or when "
                 "the id is not in the stream. Only a raw image or E01 lists $Secure:$SDS. "
                 "The root directory's row has the Path /. "
                 "Tested on a public Windows XP $MFT (samples/MFT at omerbenamram/mft "
                 "dc36db7d3b83d68c0eecb75225c9955cfd7b2f2d, not a registered corpus) read as a "
                 "folder: 13,060 rows, 1,227 of them records not in use. On the 13,060 records "
                 "both parsers name, the sequence number, in-use flag, the four SI times and "
                 "every path the mft crate resolves are equal to its reading, and it reports "
                 "351 of them under [Unknown] where this artifact leaves the same 351 paths "
                 "blank. Owner SID has no value on any row of that run, since a folder input "
                 "lists no $Secure:$SDS. Other Links has no value on any row of that run, since "
                 "no record there holds a second long name. "
                 "Tested on two Windows-written NTFS volumes from the dissect.ntfs test data "
                 "(tests/_data/ntfs.bin.gz and ntfs-cloud.bin.gz at fox-it/dissect.ntfs "
                 "7f021dd1182eb6f9b6a2dbd19cf2e29143ea654d, not registered corpora) read as raw "
                 "images: 2,292 and 45 rows, and every Owner SID is equal to dissect.ntfs's owner "
                 "for the same Security Id. Other Links has no value on any row of either. On "
                 "ntfs.bin, FN Created, FN Modified, FN Record Changed and FN Accessed are "
                 "identical to one another and to SI Created on all 2,292 rows. On ntfs.bin, SI "
                 "Modified is identical to SI Record Changed on all 2,292 rows. "
                 "Tested on the NTFS fixture written by mkntfs and ntfs-3g that the raw image "
                 "seeker tests read (admin/test/data/raw_images/ntfs-streams.img.gz): 996 rows, "
                 "965 of them records not in use, and 964 of those are files whose path "
                 "resolves through their deleted parent directory, /holes, the 965th. On that fixture, SI Created is identical to SI Accessed on "
                 "all 996 rows. On that fixture, FN Created, FN Modified, FN Record Changed and "
                 "FN Accessed are identical to one another on all 996 rows. "
                 "Run on the Windows-written volumes of four E01 images: 510,672 rows on pc_mus_001_win11 (510,638 and 34 from its two NTFS "
                 "volumes), 122,289 on af_case2_win10, 142,987 on lonewolf_win10 (142,956 and 31) and 102,293 on szechuan_win10 (102,262 and 31). "
                 "A separate walk "
                 "of each staged $MFT of af_case2_win10, lonewolf_win10 and pc_mus_001_win11, applying the update sequence fixups and folding "
                 "extension "
                 "records, found the same named base records on every volume, and resolving "
                 "paths by the rule above left the same records blank. In Use is No on 234,658, "
                 "15, 3,074 and 7 rows. Path is blank on 197,743, 3, 2,522 and 0 rows, every one of "
                 "them a record not in use. Other Links has a value on 29,216, 26,611, 30,945 and 24,099 rows. Owner SID was compared with "
                 "dissect.ntfs 3.16's owner for the "
                 "same Security Id on 5,000 randomly chosen rows of each large volume of af_case2_win10, lonewolf_win10 and pc_mus_001_win11 and "
                 "every "
                 "row of the two small ones, 15,065 rows, and was equal on all of them. It is "
                 "blank on 3, 2, 6 and 3 rows; on 13 of them the record's $STANDARD_INFORMATION carries no Security Id, and the other, on "
                 "lonewolf_win10, has a Security Id of 0, which the $Secure:$SDS "
                 "beside it does not hold.",
        "paths": ('*/$MFT', '*/$Secure:$SDS'),
        "output_types": "standard",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 510672 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 122289 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 142987 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 102,293 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 12179 rows",
        },
        "artifact_icon": "files",
    },
    "windowsMftSiBeforeFn": {
        "name": "MFT SI Created Earlier Than FN Created",
        "description": "Records of an NTFS master file table whose $STANDARD_INFORMATION creation time is earlier "
                       "than the creation time in their $FILE_NAME, with the gap, the SI record-changed time and "
                       "the folders the record's names are in.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per named base record of each $MFT, in use or not, whose $STANDARD_INFORMATION (SI) "
                 "creation time is earlier than the creation time in the $FILE_NAME (FN) the MFT artifact shows for "
                 "it, the long name before its DOS 8.3 alias; the two are compared as stored, in 100-nanosecond "
                 "ticks. Record layout and the four times of each attribute are as in the MFT artifact, whose notes "
                 "cite the Linux-NTFS documentation; that documentation notes that $FILE_NAME's times are updated "
                 "only when the name changes (https://github.com/flatcap/ntfs-docs/blob/641edd36dc5f6b62c2aae6658c5a60a4d6d3fe29/attributes/file_name.html#L218-L222). The row names a "
                 "condition, not what caused it. Known data (corpus key windows11_arm_ntfs_si_fn_known_20261104, a "
                 "64 MB NTFS volume made on Windows 11 build 26200 with one file per action and each action's time "
                 "logged) produced the condition from setting a file's times back with the Windows API (PowerShell "
                 "CreationTime, which calls SetFileTime), from robocopy /COPY:DAT, which carried the source's "
                 "creation time, and from extracting a zip through the Explorer shell, which wrote the archived time; "
                 "it did not come from Copy-Item, from moving a file within or across volumes, from Expand-Archive, "
                 "or from deleting a file and creating one of the same name 2 seconds later. A file whose times were "
                 "set back and that was then renamed gave no row: the rename wrote the set-back time into FN Created. "
                 "So a row can come from ordinary copying or extraction, and a record without a row can still have "
                 "had its times set. Installers, Windows servicing, profile creation and other tools were not "
                 "tested. Gap (seconds) is FN Created minus SI Created. SI Record Changed is SI's MFT changed time: "
                 "on the known data it was the moment of the set-back on the set-back files and the moment of the "
                 "extraction on the Explorer extract, but on the files copied with Copy-Item and robocopy it was the "
                 "source file's value, copied across. SI Created Whole Second is Yes when SI Created has no "
                 "fraction of a second; the whole-second set-back and the Explorer extract gave Yes, and on the corpus "
                 "images most Yes rows are under Program Files, so it describes the value and does not separate a "
                 "cause. Folders names the folder of every name the record has, from the path's leading folders: "
                 "Windows\\WinSxS, Windows (other), Program Files (and Program Files (x86)), ProgramData, Users (and "
                 "Documents and Settings) or Other; it is blank when no name resolves to a path. A record is listed "
                 "once, under the name in Path, and its other names are in Other Links: on the tested Windows 10 and "
                 "11 images about 14,700 to 20,300 rows per image have names both under WinSxS and elsewhere in "
                 "Windows, so no folder is left out. On the tested images the condition held on 79,683 of 122,289 "
                 "records on af_case2_win10, 81,865 of 142,987 on lonewolf_win10 and 73,226 of 102,293 on "
                 "szechuan_win10 (65, 57 and 72 percent), on 121,388 of 510,672 on pc_mus_001_win11 "
                 "(42,027 of them free records with no resolvable path) and on 350 of 12,179 on "
                 "cfreds_hacking_case_winxp. Almost all were under Windows and Program Files. On the four Windows 10 "
                 "and 11 images 109 to 767 rows had their only names under Users, and 62 to 72 rows per image had "
                 "a name in the Default profile itself; 4 rows on cfreds_hacking_case_winxp had their names under "
                 "Documents and Settings. Path, Name, "
                 "In Use, Directory, Other Links and Record are as in the MFT artifact.",
        "paths": ('*/$MFT',),
        "output_types": "standard",
        "sample_data": {
            "windows11_arm_ntfs_si_fn_known_20261104": "Windows 11 build 26200 (ARM64), test volume; run -t raw on kd_ts.vhd | 4 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 121388 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 79683 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 81865 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 73226 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 350 rows",
        },
        "artifact_icon": "clock",
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import (ROOT_RECORD, filetime, iter_mft, mft_index, sds_owners,
                                  split_reference)

_LABEL = 'MFT'
_REFERENCE_MASK = 0xFFFFFFFFFFFF


def _member(context, infos, path):
    info = infos.get(path)
    return info.source_path if info else context.get_relative_path(path)


def _rooted(path):
    return '' if path is None else '/' + path


def mft_rows(handle, index, owners):
    """One row per named base record, as the artifact reports it, without the
    Source File column."""
    for _number, record in iter_mft(handle):
        if record is None or record.base & _REFERENCE_MASK:
            continue
        index.fold(record)
        chosen = record.best_name()
        if chosen is None:
            continue
        std = record.std_times or (0, 0, 0, 0)
        parent_record, parent_sequence = split_reference(chosen[0])
        others = [_rooted(index.path_of_name(name)) or name[2]
                  for name in record.link_names() if name is not chosen]
        size = '' if record.is_dir or record.data_size is None else record.data_size
        streams = '; '.join(f'{name} ({length:,} bytes)' for name, length in record.streams)
        owner = owners.get(record.security_id, '') if record.security_id else ''
        path = '/' if record.number == ROOT_RECORD else _rooted(index.path_of_name(chosen))
        yield (tuple(filetime(v) for v in std) + tuple(filetime(v) for v in chosen[3])
               + (path, chosen[2],
                  'Yes' if record.in_use else 'No', 'Yes' if record.is_dir else 'No',
                  size, streams, owner, record.number, record.sequence,
                  parent_record, parent_sequence, '; '.join(others)))


@artifact_processor
def windowsMft(context):
    data_headers = (('SI Created', 'datetime'), ('SI Modified', 'datetime'),
                    ('SI Record Changed', 'datetime'), ('SI Accessed', 'datetime'),
                    ('FN Created', 'datetime'), ('FN Modified', 'datetime'),
                    ('FN Record Changed', 'datetime'), ('FN Accessed', 'datetime'),
                    'Path', 'Name', 'In Use', 'Directory', 'Size (bytes)', 'Named Streams',
                    'Owner SID', 'Record', 'Sequence', 'Parent Record', 'Parent Sequence',
                    'Other Links', 'Source File')
    results = context.create_artifact_result(headers=data_headers)
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    tables, descriptors = [], {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        member = _member(context, infos, path)
        if member.endswith('/$MFT') or member == '$MFT':
            tables.append((path, member))
        elif member.endswith('$Secure:$SDS'):
            descriptors[os.path.dirname(path)] = path
    sources = []
    for path, member in tables:
        owners = {}
        stream = descriptors.get(os.path.dirname(path))
        if stream:
            try:
                with open(stream, 'rb') as handle:
                    owners = sds_owners(handle.read())
            except OSError as exc:
                logfunc(f'{_LABEL}: could not read the $Secure:$SDS beside {member}: '
                        f'{type(exc).__name__}')
        try:
            index = mft_index(path)
            relative = context.get_relative_path(path)
            rows = 0
            with open(path, 'rb') as handle:
                for row in mft_rows(handle, index, owners):
                    results.add_row(row + (relative,))
                    rows += 1
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {member}: {type(exc).__name__}')
            continue
        if rows:
            sources.append(path)
            if stream:
                sources.append(stream)
        else:
            logfunc(f'{_LABEL}: no named records read from {member}')
    results.set_source_path('\n'.join(sources))
    return results



_TICKS_PER_SECOND = 10_000_000


def folder_class(path):
    """The folder a rooted path is in, by its literal leading folders, or '' for no path."""
    if not path:
        return ''
    parts = [part.lower() for part in path.strip('/').split('/')]
    if parts[0] == 'windows':
        return 'Windows\\WinSxS' if len(parts) > 1 and parts[1] == 'winsxs' else 'Windows (other)'
    if parts[0] in ('program files', 'program files (x86)'):
        return 'Program Files'
    if parts[0] == 'programdata':
        return 'ProgramData'
    if parts[0] in ('users', 'documents and settings'):
        return 'Users'
    return 'Other'


def si_before_fn_rows(handle, index):
    """One row per named base record whose SI creation FILETIME is below its chosen $FILE_NAME's, compared
    as stored (100 ns ticks), without the Source File column."""
    for _number, record in iter_mft(handle):
        if record is None or record.base & _REFERENCE_MASK:
            continue
        index.fold(record)
        chosen = record.best_name()
        if chosen is None or not record.std_times:
            continue
        si_created, _si_modified, si_changed, _si_read = record.std_times
        fn_created = chosen[3][0]
        if not si_created or not fn_created or si_created >= fn_created:
            continue
        path = '/' if record.number == ROOT_RECORD else _rooted(index.path_of_name(chosen))
        names = [path] + [_rooted(index.path_of_name(name)) for name in record.link_names() if name is not chosen]
        folders = '; '.join(sorted({folder_class(name) for name in names if name}))
        others = [_rooted(index.path_of_name(name)) or name[2]
                  for name in record.link_names() if name is not chosen]
        yield (filetime(si_created), filetime(fn_created), round((fn_created - si_created) / _TICKS_PER_SECOND, 7),
               filetime(si_changed), 'Yes' if si_created % _TICKS_PER_SECOND == 0 else 'No', folders, path,
               chosen[2], 'Yes' if record.in_use else 'No', 'Yes' if record.is_dir else 'No', '; '.join(others),
               record.number)


@artifact_processor
def windowsMftSiBeforeFn(context):
    data_headers = (('SI Created', 'datetime'), ('FN Created', 'datetime'), 'Gap (seconds)',
                    ('SI Record Changed', 'datetime'), 'SI Created Whole Second', 'Folders', 'Path', 'Name',
                    'In Use', 'Directory', 'Other Links', 'Record', 'Source File')
    label = 'MFT SI Created Earlier Than FN Created'
    results = context.create_artifact_result(headers=data_headers)
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    sources = []
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        member = _member(context, infos, path)
        if not (member.endswith('/$MFT') or member == '$MFT'):
            continue
        try:
            index = mft_index(path)
            relative = context.get_relative_path(path)
            rows = 0
            with open(path, 'rb') as handle:
                for row in si_before_fn_rows(handle, index):
                    results.add_row(row + (relative,))
                    rows += 1
        except OSError as exc:
            logfunc(f'{label}: could not read {member}: {type(exc).__name__}')
            continue
        if rows:
            sources.append(path)
    results.set_source_path('\n'.join(sources))
    return results
