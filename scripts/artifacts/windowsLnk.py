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

from scripts.windows_lnk import parse_lnk, target_path, text_mode_damaged, tracker_columns
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
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the .lnk shell links in a user's Recent folder "
                 "(AppData\\Roaming\\Microsoft\\Windows\\Recent, or Documents and Settings\\<user>\\Recent "
                 "on Windows XP), read from the files named "
                 "in Source File. Each row is one shell link. What wrote a given link "
                 "here, and when, is not established by this artifact; a row does not "
                 "record who was at the keyboard, and the target may since have been "
                 "moved or deleted. Target Path is the local path stored in the link "
                 "(LinkInfo), or for a target on a share the share name and the path below it, or a shell "
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
                 "Network Path is the UNC name of the share when the target is on a network share, "
                 "blank for a local target. Arguments is any command line stored in the "
                 "link, blank for a plain file shortcut. Machine ID is the "
                 "TrackerDataBlock's MachineID, which [MS-SHLLINK] gives as 'the NetBIOS"
                 " name of the machine where the link target was last known to reside' "
                 "(https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/df8e3748-fba5-4524-968a-f72be06d71fc);"
                 " it is blank when the link carries no such block or stores zeros there, and it was filled on"
                 " the same 58 of the 91 rows of the four Windows 10 and 11 images as the droid columns;"
                 " on cfreds_hacking_case_winxp it was filled on 2 of the 4 links with the block, and the"
                 " other 2, both with a network target, store zeros. Droid Volume "
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
                 "91 rows of the four Windows 10 and 11 images, and 4 of the 8 on cfreds_hacking_case_winxp, carry one. Checked with The Sleuth Kit 4.15.0 on the "
                 "four Windows 10 and 11 images: on each of the 49 rows whose Drive Serial is that "
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
                 "https://github.com/libyal/liblnk/blob/f80bdb225cb847916f6d163da9127919969c299d/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc"
                 " A file whose every LF byte follows a CR byte, whose extra data does not end with the terminal block"
                 " at the end of the file, and which does once the CR byte before each LF is removed (the change a "
                 "copy in text mode, such as an ASCII mode FTP transfer, makes to a binary file) is named in the run "
                 "log as such and not reported. Each of the 211 shell links these two artifacts read in the corpus "
                 "ends with the terminal block at the end of the file, and none was in that state; each of the 55 that"
                 " hold an LF byte, copied with a CR byte added before each LF for the test, was found by this check. "
                 "In the corpus none of the 211 has an ICON_LOCATION string or an IconEnvironmentDataBlock, so neither"
                 " is a column; Windows Jump Lists reports both.",
        "paths": ("*/Microsoft/Windows/[Rr]ecent/*.[Ll][Nn][Kk]", "*/Documents and Settings/*/[Rr]ecent/*.[Ll][Nn][Kk]"),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 20 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 14 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 38 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 19 rows",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 8 rows",
        },
    },
    "windowsLnkOfficeRecent": {
        "name": "Office Recent Shell Links (LNK)",
        "description": "Shell links (.lnk) in a user's Microsoft Office Recent folder, with each target's "
                       "path, recorded timestamps, size and volume, and the link's tracker block.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the .lnk shell links in a user's Microsoft Office Recent folder "
                 "(AppData\\Roaming\\Microsoft\\Office\\Recent in the tested profiles; the pattern matches a .lnk, "
                 "in any letter case, under any folder whose path ends Microsoft\\Office\\Recent or "
                 "Microsoft\\Office\\recent, subfolders included), read from the files named in Source File. Each row "
                 "is one shell link. What wrote a given link here, and when, is not established by this artifact; "
                 "a row does not record who was at the keyboard, and the target may since have been moved or "
                 "deleted. The columns are read from each link exactly as in Recent Shell Links (LNK), whose notes "
                 "source each one: Target Modified, Target Created and Target Accessed (UTC) are the times the link "
                 "records for its target, not when the link was made or used. The folder's index.dat, present on "
                 "all three images with rows, is not read; its format is not established here. A file named .lnk "
                 "that does not read as a shell link is counted in the run log and not reported. Tested on "
                 "cfreds_leakage_win7 (7 rows), lonewolf_win10 (8) and hexordia_mvs2025_win11 (1), one user "
                 "profile each, each .lnk the image listing holds in the folder giving a row. Arguments was blank "
                 "on all 16 rows. Drive Type and Drive Serial were filled on 14 of the 16 and blank on the 2 rows "
                 "of cfreds_leakage_win7 that carry a Network Path; Volume Label was filled on 3. The tracker block "
                 "columns (Droid Volume ID, Droid File ID, Droid File ID Time (UTC), Droid File ID Node, Birth "
                 "Droid Volume ID and Birth Droid File ID) were filled on 14 rows and blank on 2 rows of "
                 "cfreds_leakage_win7 whose links carry no tracker block. Machine ID was filled on 12 of the 14 "
                 "rows with a tracker block and blank on the 2 with a Network Path. Birth Droid Volume ID and "
                 "Birth Droid File ID equal Droid Volume ID and Droid File ID on all 14. On lonewolf_win10 Drive "
                 "Type, Drive Serial, Machine ID, Droid Volume ID and Birth Droid Volume ID each held one value on "
                 "all 8 rows, and Volume Label and Network Path were blank on all 8; on hexordia_mvs2025_win11 "
                 "Network Path was blank on its one row."
                 " A file whose every LF byte follows a CR byte, whose extra data does not end with the terminal block"
                 " at the end of the file, and which does once the CR byte before each LF is removed (the change a "
                 "copy in text mode, such as an ASCII mode FTP transfer, makes to a binary file) is named in the run "
                 "log as such and not reported. Each of the 211 shell links these two artifacts read in the corpus "
                 "ends with the terminal block at the end of the file, and none was in that state; each of the 55 that"
                 " hold an LF byte, copied with a CR byte added before each LF for the test, was found by this check. "
                 "In the corpus none of the 211 has an ICON_LOCATION string or an IconEnvironmentDataBlock, so neither"
                 " is a column; Windows Jump Lists reports both.",
        "paths": ("*/Microsoft/Office/[Rr]ecent/*.[Ll][Nn][Kk]",),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 7 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 8 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches "
                                        "the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 build 9600 | 0 rows (no member matches the "
                                          "declared paths)",
        },
    },
}


def _office_recent(relative_source):
    """True for a link in a Microsoft\\Office\\Recent folder, which Office Recent Shell Links reads.
    The XP Recent pattern's wildcard also crosses into that folder."""
    return '/microsoft/office/' in '/' + relative_source.replace('\\', '/').lower()


def _link_rows(context, label, skip=None):
    """One row per shell link in files_found, and the staged paths read. skip, given the
    evidence-relative path, leaves a link to another artifact."""
    data_list = []
    sources = []
    not_links = 0
    damaged = 0
    for source in sorted(str(f) for f in context.get_files_found()
                         if str(f).lower().endswith(_LNK)):
        relative_source = context.get_relative_path(source)
        if skip and skip(relative_source):
            continue
        try:
            with open(source, 'rb') as handle:
                data = handle.read()
            parsed = parse_lnk(data)
        except OSError as exc:
            logfunc(f'{label}: could not read {relative_source}: {exc}')
            continue
        if text_mode_damaged(data):
            damaged += 1
            logfunc(f'{label}: {relative_source} reads as a whole shell link only with the CR byte before each LF '
                    'removed, as a copy in text mode leaves a binary file, and was not reported')
            continue
        if parsed.get('error'):
            not_links += 1
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
    if not_links:
        logfunc(f'{label}: {not_links} file(s) named .lnk did not read as a shell link and were not reported')
    if damaged:
        logfunc(f'{label}: {damaged} file(s) named .lnk read as a whole shell link only with the CR byte before '
                'each LF removed, the state a copy in text mode leaves, and were not reported')
    return data_list, sources


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
    data_list, sources = _link_rows(context, 'Recent Shell Links', skip=_office_recent)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def windowsLnkOfficeRecent(context):
    data_headers = (('Target Modified (UTC)', 'datetime'),
                    ('Target Created (UTC)', 'datetime'),
                    ('Target Accessed (UTC)', 'datetime'),
                    'Target Path', 'Target Size (bytes)', 'Drive Type',
                    'Drive Serial', 'Volume Label', 'Network Path', 'Arguments',
                    'Machine ID', 'Droid Volume ID', 'Droid File ID',
                    ('Droid File ID Time (UTC)', 'datetime'), 'Droid File ID Node',
                    'Birth Droid Volume ID', 'Birth Droid File ID', 'Source File')
    data_list, sources = _link_rows(context, 'Office Recent Shell Links')
    return data_headers, data_list, "\n".join(sources)
