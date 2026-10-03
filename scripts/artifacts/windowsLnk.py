"""Windows Recent shell links (.lnk) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Lnk artifact. The shell
link binary format is parsed by scripts/windows_lnk.py, which follows Microsoft's
[MS-SHLLINK] specification and libyal liblnk.

A shell link carries the target's path, the target file's own recorded timestamps
and size, the volume it lived on, and its tracker block: the machine where the
target was last known to reside and the NTFS object identifiers of the target
and its volume.
"""

from scripts.windows_lnk import parse_lnk, target_path, tracker_columns
from scripts.ilapfuncs import artifact_processor, logfunc

_LNK = ".lnk"

__artifacts_v2__ = {
    "windowsLnkRecent": {
        "name": "Recent Shell Links (LNK)",
        "description": "Shell links (.lnk) in the Recent folder, with each target's path, "
                       "recorded timestamps, size and volume, and the link's tracker block: "
                       "the machine where the target was last known to reside and the NTFS "
                       "object IDs of the target and its volume.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-10-03",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the .lnk shell links in a user's Recent folder "
                 "(AppData\\Roaming\\Microsoft\\Windows\\Recent), read from the files named "
                 "in Source File. Each row is one shell link. What wrote a given link "
                 "here, and when, is not established by this artifact; a row does not "
                 "record who was at the keyboard, and the target may since have been "
                 "moved or deleted. Target Path is the local path stored in the link "
                 "(LinkInfo), or the network path for a target on a share, or a shell "
                 "path rebuilt from the link's target id list when the link stores no "
                 "file path (a known shell-folder name where the GUID is documented, "
                 "otherwise the raw {GUID}); a link to a URI or app shows its root "
                 "shell-folder GUID here and the URI is carried in the link's own file "
                 "name in Source File. Target Created, Target Modified and Target "
                 "Accessed (UTC) are the link header's CreationTime, WriteTime and "
                 "AccessTime, which [MS-SHLLINK] gives as the creation, write and access"
                 " times of the link target in UTC "
                 "(https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/c3376b21-0931-45e4-b2fc-a48ac0e60d15),"
                 " FILETIMEs converted with integer arithmetic and cut to whole "
                 "microseconds; they describe the target file, not when the user opened "
                 "it, and are blank when the link stores 0 (for example a virtual or URI"
                 " target). On lonewolf_win10 Target Modified (UTC) is filled on 16 of "
                 "the 38 rows: the other 22 links store 0 for all three target times, 8 "
                 "of them for a shell-folder target with no file path. Target Size "
                 "(bytes) is the target size the link recorded (0 when none is stored). "
                 "Drive Type, Drive Serial and Volume Label are the volume the target "
                 "lived on, from the link's VolumeID; Drive Type is named from the "
                 "Windows GetDriveType constants and Drive Serial and Volume Label are "
                 "as stored; all three are blank for a network or virtual target. "
                 "Network Path is the UNC path when the target is on a network share, "
                 "blank for a local target. Arguments is any command line stored in the "
                 "link, blank for a plain file shortcut. Machine ID is the "
                 "TrackerDataBlock's MachineID, which [MS-SHLLINK] gives as 'the NetBIOS"
                 " name of the machine where the link target was last known to reside' "
                 "(https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/df8e3748-fba5-4524-968a-f72be06d71fc);"
                 " it is blank when the link carries no such block, and it was filled on"
                 " the same 58 of the 91 tested rows as the droid columns. Droid Volume "
                 "ID, Droid File ID, Birth Droid Volume ID and Birth Droid File ID are "
                 "the TrackerDataBlock's Droid and DroidBirth values, two GUIDs each, "
                 "which [MS-SHLLINK] says are 'used to find the link target with the "
                 "Link Tracking service' "
                 "(https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/df8e3748-fba5-4524-968a-f72be06d71fc);"
                 " libyal's liblnk document names them the droid and birth droid volume "
                 "and file identifiers and says each contains an NTFS object identifier,"
                 " the volume one found in the $OBJECT_ID attribute of the $Volume "
                 "metadata file and the file one in that of the file "
                 "(https://github.com/libyal/liblnk/blob/f80bdb225cb847916f6d163da9127919969c299d/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc#L656-L674)."
                 " They are blank when the link carries no TrackerDataBlock; 58 of the "
                 "91 tested rows carry one. Checked with The Sleuth Kit 4.15.0 on the "
                 "four public images: on each of the 49 rows whose Drive Serial is that "
                 "of an NTFS volume in the image, Droid Volume ID and Birth Droid Volume"
                 " ID equal that volume's $Volume object ID, and on each of the 44 of "
                 "those whose Target Path The Sleuth Kit found by name in that volume, "
                 "Droid File ID equals the object ID of the file at that path; 5 were "
                 "not found by name. The other 9 rows with the block are on volumes the "
                 "images do not hold, and their Droid Volume ID is all zeros. Birth "
                 "Droid Volume ID and Birth Droid File ID equal Droid Volume ID and "
                 "Droid File ID on every tested row. Every tested Droid File ID is a "
                 "version 1 UUID, and Droid File ID Time (UTC) and Droid File ID Node "
                 "are its timestamp and node fields: RFC 9562 gives the timestamp as 'a "
                 "count of 100-nanosecond intervals since 00:00:00.00, 15 October 1582' "
                 "in UTC, cut here to whole microseconds, and the node as 'an IEEE 802 "
                 "MAC address, usually the host address or a randomly derived value' "
                 "(https://www.rfc-editor.org/rfc/rfc9562#section-5.1). RFC 9562 also "
                 "says a node generated as a random number has its multicast bit set and"
                 " an address from a network card never has "
                 "(https://www.rfc-editor.org/rfc/rfc9562#section-6.10); the bit was "
                 "clear on every tested row. What event the time marks, and which "
                 "machine's address the node is, is not established here. Format: "
                 "Microsoft [MS-SHLLINK], "
                 "https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943"
                 " ; and libyal liblnk, Windows Shortcut File format, "
                 "https://github.com/libyal/liblnk/blob/f80bdb225cb847916f6d163da9127919969c299d/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc",
        "paths": ("*/Microsoft/Windows/[Rr]ecent/*.[Ll][Nn][Kk]",),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 20 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 14 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 38 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 19 rows",
        },
    },
}


@artifact_processor
def windowsLnkRecent(context):
    data_headers = (('Target Modified (UTC)', 'datetime'),
                    ('Target Created (UTC)', 'datetime'),
                    ('Target Accessed (UTC)', 'datetime'),
                    'Target Path', 'Target Size (bytes)', 'Drive Type',
                    'Drive Serial', 'Volume Label', 'Network Path', 'Arguments',
                    'Machine ID', 'Droid Volume ID', 'Droid File ID',
                    ('Droid File ID Time (UTC)', 'datetime'), 'Droid File ID Node',
                    'Birth Droid Volume ID', 'Birth Droid File ID', 'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(_LNK)]:
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                parsed = parse_lnk(handle.read())
        except OSError as exc:
            logfunc(f'Recent Shell Links: could not read {relative_source}: {exc}')
            continue
        if parsed.get('error'):
            continue
        data_list.append((
            parsed.get('target_modified', ''),
            parsed.get('target_created', ''),
            parsed.get('target_accessed', ''),
            target_path(parsed),
            parsed.get('target_size', ''),
            parsed.get('drive_type', ''),
            parsed.get('drive_serial', ''),
            parsed.get('volume_label', ''),
            parsed.get('network_path', ''),
            parsed.get('arguments', ''),
            parsed.get('machine_id', ''),
        ) + tracker_columns(parsed) + (relative_source,))
        sources.append(source)
    return data_headers, data_list, "\n".join(sources)
