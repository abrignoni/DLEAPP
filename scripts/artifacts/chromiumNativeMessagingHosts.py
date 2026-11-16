"""Chromium native messaging host registrations and manifests, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "chromiumNativeMessagingRegistry": {
        "name": "Chromium Native Messaging Host Registry Keys",
        "description": "Native messaging host registrations in the SOFTWARE and NTUSER.DAT registry hives: one row "
                       "per host key under the Google Chrome and Chromium NativeMessagingHosts keys, with the "
                       "key's last-written time and the path of the manifest file its default value names.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none (vendored regfprobe)",
        "category": "Chromium",
        "notes": "Reads, in the SOFTWARE hive, Google\\Chrome\\NativeMessagingHosts and "
                 "Chromium\\NativeMessagingHosts at the hive root and under WOW6432Node, and in each NTUSER.DAT the "
                 "same two keys under Software and under Software\\Wow6432Node. No source read for this artifact "
                 "shows Chromium reading Software\\Wow6432Node in NTUSER.DAT; that key is read in case it holds "
                 "registrations. The Chromium source reads the default value of the host's subkey and uses it as "
                 "the manifest path, which must be absolute. It reads SOFTWARE\\Google\\Chrome\\NativeMessagingHosts "
                 "in every build, and a Chromium-branded build tries SOFTWARE\\Chromium\\NativeMessagingHosts first. "
                 "It looks in HKEY_CURRENT_USER first, when user-level hosts are allowed, then in "
                 "HKEY_LOCAL_MACHINE, and in each tries the 32-bit view, then the 64-bit view "
                 "(chrome/browser/extensions/api/messaging/launch_context_win.cc, lines 44 to 92 and 183 to 211, "
                 "chromium/chromium at 623ed6937e8e32110f32bacb043495bfc1e99be5). The Chrome documentation "
                 "(https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging, read on 15 "
                 "November 2026) names the Google\\Chrome key under HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER, the "
                 "default value, and the 32-bit then 64-bit order; it does not name the Chromium key. Key Last "
                 "Written is the last-written time of the host's key, UTC. The hive stores no time for a value: "
                 "the time is the last write to the host's key, which a change to its values or subkeys also "
                 "updates, and it is not an install time. Manifest File is the default value's text, up to its "
                 "terminating NUL; environment variables in a REG_EXPAND_SZ value are not expanded here, while "
                 "Chromium expands them, and a value of a binary type is shown as hexadecimal. Only REG_SZ values "
                 "were in the test hives. The manifest is read by Chromium Native Messaging Host Manifests only "
                 "when it sits in a folder it matches, so a manifest at the registered path is not opened here. "
                 "Key is the path of the NativeMessagingHosts key inside the hive, and Source File names the hive. "
                 "Scope is Machine for the SOFTWARE hive and User for NTUSER.DAT. User is the folder name after "
                 "Users in the hive's path. Keys of other browsers, such as Microsoft Edge and Firefox, are not "
                 "read; the test SOFTWARE hive held an Edge key and a Mozilla key named NativeMessagingHosts, each "
                 "with one host, and neither is in the output. A row shows a registration, not that a host ran or "
                 "that its manifest or binary exists. Rows are not filtered by who registered them: on the test "
                 "VM, 3 of the 7 rows were keys already present, with host names starting com.microsoft. The hives "
                 "are read with the vendored regfprobe and a dirty hive is replayed from its .LOG1 and .LOG2 files "
                 "as Run and RunOnce Keys describes; both test hives were clean and had no logs, so the replay did "
                 "not run for this artifact. Evidence tier: data-proven on the SOFTWARE and NTUSER.DAT hives of a "
                 "Windows 11 ARM64 lab VM (build 26200), saved with reg save after four keys were added with reg "
                 "add for this artifact (one each under HKLM, HKLM WOW6432Node, HKCU Google Chrome and HKCU "
                 "Chromium) and removed again; these hives are not corpus images and have no corpus key. 4 added "
                 "keys and 3 keys already on the VM were read, 7 rows. Rows came from four of the eight locations: "
                 "SOFTWARE Google\\Chrome, SOFTWARE WOW6432Node\\Google\\Chrome, NTUSER Software\\Google\\Chrome and "
                 "NTUSER Software\\Chromium. The Chromium key in SOFTWARE, under the root and under WOW6432Node, "
                 "and both Wow6432Node keys in NTUSER.DAT were absent; those paths are code-present and "
                 "unexercised. No manifest written by an installer was read by this artifact. Source File stays "
                 "because Scope separates the files only when the extraction holds one SOFTWARE hive and one "
                 "NTUSER.DAT per user; a second copy (a Windows.old folder) is told apart only by it.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "link",
    },
    "chromiumNativeMessagingManifests": {
        "name": "Chromium Native Messaging Host Manifests",
        "description": "Native messaging host manifest files in NativeMessagingHosts and native-messaging-hosts folders: "
                 "one row per .json file that holds a JSON object, with its name, description, path, type and "
                 "allowed_origins fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none",
        "category": "Chromium",
        "notes": "Reads every .json file in a folder named NativeMessagingHosts or native-messaging-hosts. The "
                 "Chromium source and the Chrome documentation give these folders for Chrome and Chromium: on "
                 "macOS the user folder NativeMessagingHosts under the browser's user data folder, and "
                 "/Library/Google/Chrome/NativeMessagingHosts and /Library/Application "
                 "Support/Chromium/NativeMessagingHosts system-wide; on Linux the user folder NativeMessagingHosts "
                 "under the user data folder, and /etc/opt/chrome/native-messaging-hosts and "
                 "/etc/chromium/native-messaging-hosts system-wide (chrome/common/chrome_paths.cc, lines 459 to "
                 "495, chromium/chromium at 623ed6937e8e32110f32bacb043495bfc1e99be5). The same source gives "
                 "Chrome for Testing folders, and its Linux branch is also built for ChromeOS and Android. Windows "
                 "has no such folder in that source: its manifests are found through the registry keys in Chromium "
                 "Native Messaging Host Registry Keys and can sit anywhere, so a Windows manifest is read here "
                 "only if it happens to lie in a folder with one of these names. Columns come from the manifest "
                 "fields the documentation lists: name, description, path, type and allowed_origins (Host Name, "
                 "Description, Binary Path, Type, Allowed Origins, one per line). Folders with these names can "
                 "also hold manifests of other browsers, which use other fields; those fields are not read and "
                 "such a manifest can show a blank Allowed Origins. The artifact does not decide which browser a "
                 "manifest belongs to, and Source File shows the folder. On macOS and Linux the documentation says "
                 "a manifest is named after its host; Host Name and Source File are both shown and the artifact "
                 "does not compare them. A row shows a .json file in such a folder, not that a browser uses it, "
                 "that the binary exists or that any extension connected. The file's own times are not read. "
                 "Evidence tier: source-verified. Exercised only on manifest files written for the test from the "
                 "documented fields, and on no corpus image; no manifest written by an installer has been read.",
        "paths": ("*/NativeMessagingHosts/*.json", "*/native-messaging-hosts/*.json"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "link",
    },
}

import json
import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import fold_view_rows, unique_sources
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive, open_key,
                                      user_from_path)

_BROWSER_KEYS = (r'Google\Chrome\NativeMessagingHosts', r'Chromium\NativeMessagingHosts')
_SOFTWARE_ROOTS = ('', 'WOW6432Node\\')
_NTUSER_ROOTS = ('Software\\', 'Software\\Wow6432Node\\')


def _text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _lines(value):
    return '\n'.join(str(v) for v in value) if isinstance(value, list) else _text(value)


def _registry_rows(reg, roots, scope, user, relative):
    rows = []
    for root in roots:
        for browser_key in _BROWSER_KEYS:
            key_path = root + browser_key
            key = open_key(reg, key_path)
            if key is None:
                continue
            for host in key.subkeys():
                manifest = ''
                for value in host.values():
                    if value.name() in ('(default)', ''):
                        manifest = _text(value.value())
                rows.append((key_written_utc(host), host.name(), manifest, key_path, scope, user, relative))
    return rows


@artifact_processor
def chromiumNativeMessagingRegistry(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Host Name', 'Manifest File', 'Key', 'Scope', 'User',
                    'Source File')
    data_list, sources = [], []
    for source in found_hives(context, 'SOFTWARE', 'NTUSER.DAT'):
        relative = context.get_relative_path(source)
        is_software = os.path.basename(source).upper() == 'SOFTWARE'
        try:
            reg = open_hive(source, context)
            rows = _registry_rows(reg, _SOFTWARE_ROOTS if is_software else _NTUSER_ROOTS,
                                  'Machine' if is_software else 'User',
                                  '' if is_software else user_from_path(relative), relative)
        except (OSError, ValueError, Registry.RegistryException) as error:
            logfunc(f'Chromium Native Messaging Host Registry Keys: could not read {relative}: {error}')
            continue
        data_list.extend(rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def chromiumNativeMessagingManifests(context):
    data_headers = ('Host Name', 'Description', 'Binary Path', 'Type', 'Allowed Origins', 'Source File')
    label = 'Chromium Native Messaging Host Manifests'
    wanted = [p for p in context.get_files_found() if str(p).lower().endswith('.json')
              and os.path.basename(os.path.dirname(str(p))) in ('NativeMessagingHosts', 'native-messaging-hosts')]
    paths, _skipped = unique_sources(context, wanted, label=label)
    data_list, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = json.loads(handle.read().decode('utf-8-sig'))
        except (OSError, ValueError) as error:
            logfunc(f'{label}: {relative} could not be read as JSON ({type(error).__name__})')
            continue
        if not isinstance(data, dict):
            logfunc(f'{label}: {relative} holds JSON that is not an object')
            continue
        read.append(path)
        data_list.append((_text(data.get('name')), _text(data.get('description')), _text(data.get('path')),
                          _text(data.get('type')), _lines(data.get('allowed_origins')), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
