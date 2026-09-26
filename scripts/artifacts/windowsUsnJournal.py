"""NTFS USN change journal ($Extend/$UsnJrnl:$J), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The record layout, reason flags and source flags follow Microsoft's
USN_RECORD_V2 and USN_RECORD_V3 documentation; see scripts/windows_ntfs.py for
the citations. Parent paths come from the $MFT of the same volume.
"""

__artifacts_v2__ = {
    "windowsUsnJournal": {
        "name": "USN Journal",
        "description": "Records of the NTFS change journal ($Extend/$UsnJrnl:$J): the time, file "
                       "name and reason flags of each, and the parent directory's path where the "
                       "same volume's $MFT resolves it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "File System (Windows)",
        "notes": "One row per USN_RECORD_V2 or USN_RECORD_V3 in each $Extend/$UsnJrnl:$J stream "
                 "a raw image or E01 holds, which the raw image seeker lists from its first "
                 "stored cluster, so the hole Windows leaves in front of the records is not "
                 "copied. The fields are read as Microsoft documents them (Reference: "
                 "https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winioctl/ns-winioctl-usn_record_v2.md#L60-L571"
                 " and ns-winioctl-usn_record_v3.md at the same commit): Timestamp is the "
                 "record's TimeStamp, a UTC FILETIME; Reasons and Source Info name each set bit "
                 "after its USN_REASON_ or USN_SOURCE_ constant and give any undocumented bit in "
                 "hex; File Attributes names each set bit after its FILE_ATTRIBUTE_ constant "
                 "(Reference: https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/FileIO/file-attribute-constants.md#L53-L74)."
                 " Source Info is blank when no bit is set. File Record and File Sequence, and "
                 "Parent Record and Parent Sequence, are the low 48 and top 16 bits of the "
                 "record's file references. Parent Path is the directory the parent reference "
                 "names, from the volume's root (/), resolved against the $MFT of the same volume as it was when the image "
                 "was taken: a directory renamed or moved since the record was written is shown "
                 "where it is now, and the path is blank when that $MFT was not found, when the "
                 "parent's record has since been reused (its sequence number no longer matches, "
                 "allowing for the one increment NTFS makes when it frees a record), or when the "
                 "chain does not reach the root. Version 4 records, which describe changed "
                 "ranges and carry no name or time, are counted in the run log, not reported, "
                 "as are bytes that do not form a record. SecurityId is not reported: it held 0 "
                 "on every record of every journal tested, 1,046,880 in all. A record is a change NTFS noted; it "
                 "does not record which user or program made it, and a journal's first record "
                 "is not evidence of when the journal began. Tested on a Windows-written NTFS "
                 "volume from the dissect.ntfs test data (tests/_data/ntfs-cloud.bin.gz at "
                 "fox-it/dissect.ntfs 7f021dd1182eb6f9b6a2dbd19cf2e29143ea654d, not a registered "
                 "corpus): 179 rows, all version 2, every USN, reason and name equal to "
                 "dissect.ntfs's reading, every parent path equal to its path. Every Timestamp is "
                 "the stored FILETIME cut to the microsecond. dissect.ntfs's time agrees on 91 "
                 "rows and is one or two microseconds away on the other 88, and on a row of each "
                 "size of difference, checked against the stored value, the difference is in "
                 "dissect.ntfs's reading. Record "
                 "Version held 2 on all 179 rows. Run on three Windows-written volumes read as E01 "
                 "images: 380,893 rows on pc_mus_001_win11, 312,959 on af_case2_win10 and "
                 "352,849 on lonewolf_win10. Each staged $J is byte-identical to The Sleuth "
                 "Kit's icat reading of the stream from its first stored cluster, and the hole "
                 "in front of it, 768 MiB, 56 MiB and 200 MiB, was not copied. On each image the "
                 "USNs and file names are equal, as a multiset, to dissect.ntfs 3.16's reading "
                 "of the same staged stream. A file name that is not valid UTF-16 is decoded "
                 "with each bad unit replaced by U+FFFD, which 8 rows of pc_mus_001_win11 carry;"
                 " dissect.ntfs 3.16 stops at such a name, so on that image its decode was set "
                 "to replace them the same way for the comparison. Record Version held 2 on all "
                 "1,046,701 of those rows. Source Info has a value on 60 rows of "
                 "pc_mus_001_win11 and on none of the other two. Parent Path is blank on "
                 "44,318, 89,164 and 73,804 rows. Version 3 records are read by the same code "
                 "with the wider references and have not been run against a journal holding "
                 "them.",
        "paths": ('*/$Extend/$UsnJrnl:$J', '*/$MFT'),
        "output_types": "standard",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 380893 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 312959 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 352849 rows",
        },
        "artifact_icon": "history",
    }
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import (FILE_ATTRIBUTES, USN_REASONS, USN_SOURCES, decode_flags,
                                  filetime, iter_usn, mft_index, split_reference)

_LABEL = 'USN Journal'
_V3_WIDE = 1 << 64


def _reference(value):
    """(record, sequence) for a 64-bit reference; a 128-bit one that does not
    fit in 64 bits is given whole in hex with no sequence."""
    if value >= _V3_WIDE:
        return f'0x{value:032X}', ''
    return split_reference(value)


def _member(context, infos, path):
    info = infos.get(path)
    return info.source_path if info else context.get_relative_path(path)


@artifact_processor
def windowsUsnJournal(context):
    data_headers = (('Timestamp', 'datetime'), 'File Name', 'Reasons', 'Parent Path',
                    'File Attributes', 'Source Info', 'USN', 'File Record', 'File Sequence',
                    'Parent Record', 'Parent Sequence', 'Reasons (Hex)', 'Record Version',
                    'Source File')
    results = context.create_artifact_result(headers=data_headers)
    seeker = context.get_seeker()
    infos = getattr(seeker, 'file_infos', {}) if seeker else {}
    journals, tables = [], {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path):
            continue
        member = _member(context, infos, path)
        if member.endswith('/$MFT') or member == '$MFT':
            tables[os.path.dirname(path)] = path
        elif member.endswith(':$J'):
            journals.append((path, member))
    sources = []
    for path, member in journals:
        # $J sits in $Extend at the volume's root, and $MFT at the root itself
        table = tables.get(os.path.dirname(os.path.dirname(path)))
        index = mft_index(table) if table else None
        if index is None:
            logfunc(f'{_LABEL}: no $MFT beside {member}, so parent paths are blank')
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {member}: {type(exc).__name__}')
            continue
        counts, rows = {}, 0
        relative = context.get_relative_path(path)
        for record in iter_usn(data, counts):
            file_record, file_sequence = _reference(record.file_reference)
            parent_record, parent_sequence = _reference(record.parent_reference)
            parent = ''
            if index is not None and parent_sequence != '':
                found = index.directory_path(record.parent_reference)
                parent = '' if found is None else '/' + found
            results.add_row((filetime(record.timestamp), record.name,
                             decode_flags(record.reason, USN_REASONS), parent,
                             decode_flags(record.attributes, FILE_ATTRIBUTES),
                             decode_flags(record.source_info, USN_SOURCES), record.usn,
                             file_record, file_sequence, parent_record, parent_sequence,
                             f'0x{record.reason:08X}', record.version, relative))
            rows += 1
        if counts.get('v4') or counts.get('unparsed'):
            logfunc(f"{_LABEL}: {member}: {counts['v4']:,} version 4 range records and "
                    f"{counts['unparsed']:,} bytes that are not a record were passed over")
        if rows:
            sources.append(path)
        else:
            logfunc(f'{_LABEL}: no records read from {member}')
    results.set_source_path('\n'.join(sources))
    return results
