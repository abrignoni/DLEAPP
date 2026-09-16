"""Windows Recent shell links (.lnk) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Lnk artifact. The shell
link binary format is parsed by scripts/windows_lnk.py, which follows Microsoft's
[MS-SHLLINK] specification and libyal liblnk.

Windows writes a shell link into the per-user Recent folder when the user opens a
file, so each .lnk there is a recorded access to its target. The shortcut carries
the target's path, the target file's own recorded timestamps and size, the volume
it lived on, and the machine the shortcut was created on.
"""

from scripts.windows_lnk import parse_lnk, target_path
from scripts.ilapfuncs import artifact_processor, logfunc

_LNK = ".lnk"

__artifacts_v2__ = {
    "windowsLnkRecent": {
        "name": "Recent Shell Links (LNK)",
        "description": "Files recorded as recently opened, from the .lnk shell links "
                       "in the Recent folder, with each target's path, recorded "
                       "timestamps, size, volume and the machine the link was made on.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the .lnk shell links in a user's Recent folder "
                 "(AppData\\Roaming\\Microsoft\\Windows\\Recent), read from the files "
                 "named in Source File. Each row is one shell link. Windows writes a "
                 "link here when a file is opened, so a row records that the target "
                 "was opened on this machine; it does not record who was at the "
                 "keyboard, and the target may since have been moved or deleted. "
                 "Target Path is the local path stored in the link (LinkInfo), or the "
                 "network path for a target on a share, or a shell path rebuilt from "
                 "the link's target id list when the link stores no file path (a "
                 "known shell-folder name where the GUID is documented, otherwise the "
                 "raw {GUID}); a link to a URI or app shows its root shell-folder "
                 "GUID here and the URI is carried in the link's own file name in "
                 "Source File. Target Created, Target Modified and Target Accessed "
                 "(UTC) are the target file's own timestamps as recorded inside the "
                 "link (Windows FILETIMEs), captured when the link was last written; "
                 "they describe the target file, not when the user opened it, and are "
                 "blank when the link stores none (for example a virtual or URI "
                 "target). Target Size (bytes) is the target size the link recorded "
                 "(0 when none is stored). Drive Type, Drive Serial and Volume Label "
                 "are the volume the target lived on, from the link's VolumeID; Drive "
                 "Type is named from the Windows GetDriveType constants and Drive "
                 "Serial and Volume Label are as stored; all three are blank for a "
                 "network or virtual target. Network Path is the UNC path when the "
                 "target is on a network share, blank for a local target. Arguments "
                 "is any command line stored in the link, blank for a plain file "
                 "shortcut. Machine ID is the NetBIOS name of the computer where the "
                 "link was created, from the link's TrackerDataBlock, blank when the "
                 "link carries no such block. Format: Microsoft [MS-SHLLINK], "
                 "https://learn.microsoft.com/openspecs/windows_protocols/ms-shllink/"
                 "16cb4ca1-9339-4d0c-a68d-bf1d6cc0f943 ; and libyal liblnk, Windows "
                 "Shortcut File format, https://github.com/libyal/liblnk/blob/main/"
                 "documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc",
        "paths": ("*/Microsoft/Windows/[Rr]ecent/*.[Ll][Nn][Kk]",),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 20 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 14 rows",
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
                    'Machine ID', 'Source File')
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
            relative_source,
        ))
        sources.append(source)
    return data_headers, data_list, "\n".join(sources)
