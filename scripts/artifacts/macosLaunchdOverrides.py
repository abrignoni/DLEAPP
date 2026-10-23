"""launchd disabled overrides in /private/var/db/com.apple.xpc.launchd, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosLaunchdDisabledOverrides": {
        "name": "launchd Disabled Overrides",
        "description": "Entries of the disabled.plist and disabled.<uid>.plist files in "
                       "/private/var/db/com.apple.xpc.launchd: the label, the value stored for "
                       "it, the domain the file name names, and the launch plists whose Label "
                       "key is that label.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "none",
        "category": "Persistence (macOS)",
        "notes": (
            'Reads every file whose name starts with disabled in '
            '/private/var/db/com.apple.xpc.launchd, one row per key of each that reads as a '
            'property list dictionary; a file that does not, such as the 0-byte '
            'disabled.migrated both public images hold, is logged with its size and not '
            'reported, and what that file records is not established here. The copy under '
            '/System/Library/Templates is not read. Label is the key. Value is its value: true '
            'or false for a Boolean, the number or text otherwise; a dictionary or list value '
            'would be written as JSON, which is not the file\'s own spelling. The launchctl(1) '
            "manual page (macOS 27.0.1, dated 1 October 2014), under 'enable | disable', says "
            'that once a service is disabled it cannot be loaded in the specified domain until '
            'it is enabled again and that this state persists across boots, and under the '
            "legacy 'load | unload' -w option that the state of the Disabled key is now stored "
            'elsewhere on disk, in a location that may not be directly manipulated by any '
            'process other than launchd; the launchd.plist(5) page (dated 30 July 2019) says '
            "of the Disabled key that it may be overridden through launchctl's enable "
            'subcommand and that this state is kept externally. Neither page names these '
            'files. Domain (from file name) is system '
            'for disabled.plist and user/<uid> for disabled.<uid>.plist, and blank for any '
            'other name; User ID is that uid. On a private macOS 27.0.1 system, launchctl '
            'print-disabled system listed every label of that system\'s disabled.plist and '
            'print-disabled user/<uid> every label of its disabled.<uid>.plist, printing '
            'disabled for each entry stored true and enabled for each stored false; counts and '
            'values from that system are not published. Launch Plists With This Label lists, '
            'one per line, each Library/LaunchAgents or Library/LaunchDaemons property list in '
            'the extraction, /System/Library included, whose Label key equals the entry\'s '
            'label, which launchd.plist(5) describes as the key that uniquely identifies the '
            'job to launchd; it is blank when no such file was found, which does not mean the '
            'service has no definition elsewhere. On dleapp_macos_bigsur (macOS 11.2.1) '
            'disabled.plist held 3 entries and disabled.501.plist 5, Value held true '
            'on all 8 rows, and 7 rows name one launch plist each, all under /System/Library, '
            'which the Launch Agents and Daemons artifact does not report. On the public '
            'MacBook Pro logical extraction (macOS 15.4, corpus key '
            'mvs2026_macbookpro_macos15) disabled.plist held 4 entries and disabled.501.plist '
            '5, each file with one entry stored false, and 8 rows name one launch plist each, '
            'all under /System/Library. File Modified (UTC) is the modification time the input '
            'records for the file: the volume\'s time on a raw image, a zip member\'s NTFS '
            "(0x000a) or extended timestamp (0x5455) field, or a tar member's time; it is blank "
            "otherwise, and for a folder input, whose times are those of the copy. The public "
            'MacBook Pro zip records its times in an NTFS extra field, and File Modified (UTC) '
            'has a value on all 9 of its rows (run of 2026-10-23). That extraction holds the folder under private/var and again under '
            'System/Volumes/Data/private/var with byte-identical files, so the second copies '
            'are not read again and are counted in the run log; when two copies differ, both '
            'are read, and an entry both hold with the same value and the same File Modified '
            '(UTC) is reported once with both files in Source File, and otherwise once per file. '
            'Source File stays beside Domain (from file name), which separates the two files '
            'on both public images, because the domain does not say which copy, folder view or '
            'volume held the file, and a file of another name has no domain. On '
            'magnet2021_macos_bigsur (macOS 11.2.1) the folder is present only '
            'under /System/Library/Templates, and on evidencelocker_macos14 (macOS 14.6.1) '
            'private/var/db holds no com.apple.xpc.launchd folder, so neither yields a row.'
        ),
        "paths": ('*/var/db/com.apple.xpc.launchd/disabled*',
                  '*/Library/LaunchAgents/*.plist', '*/Library/LaunchDaemons/*.plist'),
        "output_types": "standard",
        "artifact_icon": "toggle-left",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 8 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 9 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows",
        },
    },
}

import json
import os
import posixpath
import re
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative, fold_view_rows, load_plist, unique_sources

_LABEL = 'launchd Disabled Overrides'
_FOLDER = '/var/db/com.apple.xpc.launchd/'
_TEMPLATES = '/System/Library/Templates/'
_USER_FILE = re.compile(r'disabled\.(\d+)\.plist')
# Seekers whose recorded modification time is the evidence's own: a raw image's volume
# times, and the times a zip or tar recorded for its member. A folder input records the
# times of the copy on the examiner's disk.
_EVIDENCE_TIMES = ('FileSeekerRaw', 'FileSeekerZip', 'FileSeekerTar')


def _relative(context, path):
    return '/' + context.get_relative_path(str(path)).replace('\\', '/').lstrip('/')


def _domain(name):
    """(domain, user ID) from an overrides file name, ('', '') for any other name."""
    if name == 'disabled.plist':
        return 'system', ''
    match = _USER_FILE.fullmatch(name)
    if match:
        return f'user/{match.group(1)}', match.group(1)
    return '', ''


def _as_stored(value):
    """A plist value written the way the file spells it: true or false for a Boolean."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    return '' if value is None else str(value)


def _modified(context, path):
    """The modification time the seeker recorded for a staged file, as a UTC datetime, when
    that time is the evidence's; '' otherwise."""
    seeker = context.get_seeker() if hasattr(context, 'get_seeker') else None
    if type(seeker).__name__ not in _EVIDENCE_TIMES:
        return ''
    info = getattr(seeker, 'file_infos', {}).get(path)
    value = getattr(info, 'modification_date', None)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return ''
    return datetime.fromtimestamp(value, timezone.utc)


def _launch_plists(context, found):
    """{label: [launch plist paths in the extraction]} from the Label key of every
    LaunchAgents and LaunchDaemons plist, one path per file across folder views."""
    labels = {}
    for path in found:
        relative = _relative(context, path)
        if '/Library/LaunchAgents/' not in relative and '/Library/LaunchDaemons/' not in relative:
            continue
        item = load_plist(path)
        label = item.get('Label') if isinstance(item, dict) else None
        if isinstance(label, str):
            canonical = canonical_relative(relative)
            paths = labels.setdefault(label, [])
            if canonical not in paths:
                paths.append(canonical)
    return {label: sorted(paths) for label, paths in labels.items()}


@artifact_processor
def macosLaunchdDisabledOverrides(context):
    data_headers = (('File Modified (UTC)', 'datetime'), 'Label', 'Value',
                    'Domain (from file name)', 'User ID', 'Launch Plists With This Label',
                    'Source File')
    found = sorted(str(path) for path in context.get_files_found() if os.path.isfile(str(path)))
    overrides = [path for path in found
                 if _FOLDER in _relative(context, path)
                 and _TEMPLATES not in _relative(context, path)]
    if not overrides:
        return data_headers, [], ''
    plists = _launch_plists(context, found)
    paths, _skipped = unique_sources(context, overrides, label=_LABEL)
    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        name = posixpath.basename(relative.replace('\\', '/'))
        item = load_plist(path)
        if not isinstance(item, dict):
            logfunc(f'{_LABEL}: {relative} ({os.path.getsize(path)} bytes) did not read as a '
                    'property list dictionary; not reported')
            continue
        read.append(path)
        if not item:
            logfunc(f'{_LABEL}: no entries in {relative}')
        domain, uid = _domain(name)
        modified = _modified(context, path)
        for label in sorted(item, key=str):
            data_list.append((modified, str(label), _as_stored(item[label]), domain, uid,
                              '\n'.join(plists.get(label, [])), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
