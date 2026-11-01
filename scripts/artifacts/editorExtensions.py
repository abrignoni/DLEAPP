"""Extensions installed in Visual Studio Code and editors built on its code, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "editorExtensions": {
        "name": "Code Editor Extensions",
        "description": "Extensions listed in the extensions.json file of Visual Studio Code and of editors "
                       "built on its code, such as VSCodium, with the time each was last installed or updated, "
                       "its version, and whether it came from the extension gallery or a VSIX file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Code Editors",
        "notes": "Reads each extensions.json file in a folder named extensions, one row per entry in file order. "
                 "Visual Studio Code keeps the extensions installed for a user in the extensions folder of a "
                 "product-named folder in the home folder, unless the --extensions-dir option, the VSCODE_EXTENSIONS "
                 "variable or a portable install moves it "
                 "(https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/environment/common/environmentService.ts#L131-L147). "
                 "Each entry holds an identifier, a location, a relative location, a version and optional metadata "
                 "(https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/common/extensionsProfileScannerService.ts#L23-L29, "
                 "https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/common/extensionManagement.ts#L280-L291). "
                 "An entry is reported only when it passes the check the editor applies before using it "
                 "(https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/common/extensionsProfileScannerService.ts#L393-L401); "
                 "entries that fail it, and files whose top level is not a list, are counted in the run log. "
                 "Installed (UTC) is metadata.installedTimestamp, Unix time in milliseconds, which the install step "
                 "sets to the time of that install "
                 "(https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/node/extensionManagementService.ts#L1084-L1092). "
                 "On ubuntu2604_arm64_editorext_known_20261101 every Installed (UTC) value fell between the logged "
                 "start and end of the command that wrote it, and updating an extension replaced its value with the "
                 "time of the update, so the column is the latest install or update, not the first install. "
                 "Source is gallery or vsix as stored (vsix when the extension was installed from a file); on that "
                 "image the extension installed from a VSIX file read vsix and the others gallery. Pinned held true "
                 "on every row of that image: the editor records true when a given version is installed, the "
                 "VSIX install also recorded true, and the update kept it. In the step copies of the file, the "
                 "extension installed from the gallery without a version had no pinned key, and Pinned is blank "
                 "where the key is absent. Updated held true after the update. On rows installed from a VSIX file, "
                 "Updated, Pre-release Version, Publisher Display Name and Target Platform are blank, as those keys "
                 "were absent. Target Platform is as stored: Visual Studio Code wrote undefined and VSCodium "
                 "universal for the same extension. Extension ID is the identifier as stored, which on that image "
                 "was lowercase where the extension's own package.json spells it with capitals. The folder holding "
                 "the extensions folder names the editor in Source File: .vscode for Visual Studio Code 1.144.0 "
                 "and .vscode-oss for VSCodium 1.143.17232 on that image, which was made with each editor's "
                 "command line on Ubuntu 26.04. Other editors built on the same code, Windows and macOS "
                 "installs, and extensions installed from the editor window were not tested. An uninstalled or "
                 "replaced extension leaves this file; see Code Editor Extensions Marked for Removal. Not read: "
                 "extensions.json files in other folders, such as those of other profiles, and the editors' own "
                 "user data folders (for example ~/.config/Code), which the known data does not hold because no "
                 "editor window was opened. Source File names the file each row came from, since the path can "
                 "match more than one account or editor.",
        "paths": ('*/extensions/extensions.json',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "package",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no file matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no file matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_editorext_known_20261101": "Ubuntu 26.04 LTS aarch64, VS Code 1.144.0 and VSCodium 1.143.17232 | 4 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 | 0 rows (no file matches the declared paths)",
        },
    },
    "editorExtensionsObsolete": {
        "name": "Code Editor Extensions Marked for Removal",
        "description": "Extension folders named in the .obsolete file of Visual Studio Code and of editors built "
                       "on its code, which the editor writes when an extension is uninstalled or replaced by "
                       "another version, with the extension ID and version read from the folder's package.json "
                       "when the folder is in the extraction.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-01",
        "last_update_date": "2026-11-01",
        "requirements": "none",
        "category": "Code Editors",
        "notes": "Reads each .obsolete file in a folder named extensions, one row per folder name it lists. On "
                 "ubuntu2604_arm64_editorext_known_20261101, both uninstalling an extension and updating one to "
                 "another version removed its entry from extensions.json, left its folder on disk and added the "
                 "folder name to .obsolete with the value true, so a row does not say which of the two happened; "
                 "the same extension ID at another version in Code Editor Extensions fits an update. The file "
                 "holds no time. The editor's clean-up pass deletes the listed folders of extensions that carry "
                 "an install time "
                 "(https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/node/extensionManagementService.ts#L560-L565, "
                 "https://github.com/microsoft/vscode/blob/8fb60541db0e1a371ea40157e0f58951ae4a485d/src/vs/platform/extensionManagement/node/extensionManagementService.ts#L960-L997); "
                 "when that pass runs was not tested, as no editor window was opened. Extension ID (package.json) "
                 "is the publisher and name in the package.json of that folder, in the same extensions folder, "
                 "joined with a dot, and Version (package.json) its version; both are blank when that package.json "
                 "is not in the extraction, which is counted in the run log. On that image the uninstall was made "
                 "with each editor's command line, and all four listed folders were still present. Source File is "
                 "as in Code Editor Extensions.",
        "paths": ('*/extensions/.obsolete',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "trash-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no file matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no file matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no file matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no file matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no file matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no file matches the declared paths)",
            "ubuntu2604_arm64_editorext_known_20261101": "Ubuntu 26.04 LTS aarch64, VS Code 1.144.0 and VSCodium 1.143.17232 | 4 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no file matches the declared paths)",
            "windows11_arm_known_20261010": "Windows 11 25H2 build 26200 ARM64 | 0 rows (no file matches the declared paths)",
        },
    },
}

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _escape_fnmatch(value):
    """Escape evidence-controlled glob metacharacters for an exact search."""
    return value.replace('[', '[[]').replace('*', '[*]').replace('?', '[?]')


def _flag(value):
    """A JSON boolean as stored, blank when the key is absent."""
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return '' if value is None else str(value)


def _read_json(path, problems):
    try:
        with open(path, 'rb') as handle:
            return json.loads(handle.read().decode('utf-8'))
    except OSError:
        problems['files that could not be read'] += 1
    except (UnicodeDecodeError, ValueError):
        problems['files that are not JSON'] += 1
    return None


def _is_stored_extension(entry):
    """The shape check Visual Studio Code applies to each entry before it uses it."""
    if not isinstance(entry, dict):
        return False
    identifier = entry.get('identifier')
    location = entry.get('location')
    relative = entry.get('relativeLocation')
    version = entry.get('version')
    return (isinstance(identifier, dict) and isinstance(identifier.get('id'), str)
            and (isinstance(location, dict) or (isinstance(location, str) and bool(location)))
            and (relative is None or isinstance(relative, str))
            and isinstance(version, str) and bool(version))


def _installed_time(value, problems):
    if value is None:
        return ''
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems['install times that are not numbers, left blank'] += 1
        return ''
    try:
        return _EPOCH + timedelta(milliseconds=value)
    except OverflowError:
        problems['install times out of range, left blank'] += 1
        return ''


def _folder_name(entry):
    relative = entry.get('relativeLocation')
    if relative:
        return relative
    location = entry.get('location')
    location_path = location.get('path') if isinstance(location, dict) else location
    if isinstance(location_path, str):
        return location_path.replace('\\', '/').rstrip('/').rsplit('/', 1)[-1]
    return ''


def extension_rows(data, problems):
    if not isinstance(data, list):
        problems['files whose top level is not a list'] += 1
        return []
    rows = []
    for entry in data:
        if not _is_stored_extension(entry):
            problems['entries without an identifier, location and version'] += 1
            continue
        metadata = entry.get('metadata') if isinstance(entry.get('metadata'), dict) else {}
        rows.append((
            _installed_time(metadata.get('installedTimestamp'), problems),
            entry['identifier']['id'],
            entry['version'],
            _flag(metadata.get('source')),
            _flag(metadata.get('pinned')),
            _flag(metadata.get('updated')),
            _flag(metadata.get('isPreReleaseVersion')),
            _flag(metadata.get('publisherDisplayName')),
            _flag(metadata.get('targetPlatform')),
            _folder_name(entry),
        ))
    return rows


@artifact_processor
def editorExtensions(context):
    data_headers = (('Installed (UTC)', 'datetime'), 'Extension ID', 'Version', 'Source', 'Pinned', 'Updated',
                    'Pre-release Version', 'Publisher Display Name', 'Target Platform', 'Extension Folder',
                    'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        data = _read_json(path, problems)
        if data is None:
            continue
        rows = extension_rows(data, problems)
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Code Editor Extensions: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)


def _package(context, relative_obsolete, folder, problems):
    """The ID and version in <extensions folder>/<folder>/package.json, when it was extracted."""
    seeker = context.get_seeker()
    if seeker is None or not folder or '/' in folder or '\\' in folder or folder in ('.', '..'):
        return '', '', ''
    wanted = relative_obsolete.replace('\\', '/').rsplit('/', 1)[0] + '/' + folder + '/package.json'
    matches = [m for m in seeker.search('*/' + _escape_fnmatch(wanted))
               if context.get_relative_path(str(m)).replace('\\', '/') == wanted]
    if not matches:
        problems['folders whose package.json is not in the extraction'] += 1
        return '', '', ''
    manifest = _read_json(str(matches[0]), problems)
    if not isinstance(manifest, dict):
        return '', '', str(matches[0])
    publisher, name, version = manifest.get('publisher'), manifest.get('name'), manifest.get('version')
    ext_id = f'{publisher}.{name}' if isinstance(publisher, str) and isinstance(name, str) else ''
    return ext_id, version if isinstance(version, str) else '', str(matches[0])


@artifact_processor
def editorExtensionsObsolete(context):
    data_headers = ('Extension Folder', 'Extension ID (package.json)', 'Version (package.json)', 'Source File')
    data_list, read, problems = [], [], Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        data = _read_json(path, problems)
        if data is None:
            continue
        if not isinstance(data, dict):
            problems['files whose top level is not an object'] += 1
            continue
        relative = context.get_relative_path(path)
        if data:
            read.append(path)
        for folder in data:
            ext_id, version, manifest_path = _package(context, relative, folder, problems)
            data_list.append((folder, ext_id, version, relative))
            if manifest_path:
                read.append(manifest_path)
    if problems:
        logfunc('Code Editor Extensions Marked for Removal: '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(dict.fromkeys(read))
