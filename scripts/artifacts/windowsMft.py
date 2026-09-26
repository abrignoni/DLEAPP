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
        "last_update_date": "2026-09-26",
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
                 "Run on three Windows-written volumes read as E01 images: 510,672 rows on "
                 "pc_mus_001_win11 (510,638 and 34 from its two NTFS volumes), 122,289 on "
                 "af_case2_win10 and 142,987 on lonewolf_win10 (142,956 and 31). A separate walk "
                 "of each staged $MFT, applying the update sequence fixups and folding extension "
                 "records, found the same named base records on every volume, and resolving "
                 "paths by the rule above left the same records blank. In Use is No on 234,658, "
                 "15 and 3,074 rows. Path is blank on 197,743, 3 and 2,522 rows, every one of "
                 "them a record not in use. Other Links has a value on 29,216, 26,611 and "
                 "30,945 rows. Owner SID was compared with dissect.ntfs 3.16's owner for the "
                 "same Security Id on 5,000 randomly chosen rows of each large volume and every "
                 "row of the two small ones, 15,065 rows, and was equal on all of them. It is "
                 "blank on 3, 2 and 6 rows, each with a Security Id of 0, which the $Secure:$SDS "
                 "beside it does not hold.",
        "paths": ('*/$MFT', '*/$Secure:$SDS'),
        "output_types": "standard",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 510672 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 122289 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 142987 rows",
        },
        "artifact_icon": "files",
    }
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
