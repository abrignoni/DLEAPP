"""Windows Task Scheduler cache (TaskCache) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

The SOFTWARE hive keeps a cache of registered scheduled tasks under
Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache: a Tasks subkey per task
GUID, holding the task's path, its actions and a DynamicInfo value with times and a
result code, and a Tree of keys mirroring each task's path, holding the task's GUID
as Id and its security descriptor as SD. This reads both, decodes the first action,
and notes whether the task's XML definition under Windows\\System32\\Tasks exists.
"""

import os
import struct
import uuid

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc

_TASKCACHE = 'Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache'
_TASKS_FOLDER = '/windows/system32/tasks/'
_ACTION_TYPES = {0x6666: 'Exec', 0x7777: 'COM handler'}

__artifacts_v2__ = {
    "windowsTaskCache": {
        "name": "Scheduled Task Cache (TaskCache)",
        "description": "Scheduled tasks in the SOFTWARE hive's TaskCache: last start and stop "
                       "times, registration time, last action result and first action, with "
                       "the Tree key's security descriptor and whether the task's XML "
                       "definition file exists, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads the TaskCache key of each SOFTWARE hive, Microsoft\\Windows "
                 "NT\\CurrentVersion\\Schedule\\TaskCache, one row per subkey of its Tasks key and one "
                 "per key of its Tree that holds an Id naming no Tasks subkey. The hive's .LOG1 and "
                 ".LOG2 transaction logs are not replayed. On af_case2_win10, lonewolf_win10, "
                 "pc_mus_001_win11 and the public DFIR Madness Szechuan Sauce desktop image (not a "
                 "registered corpus key), DynamicInfo was 36 bytes with a first 32-bit value of 3 on "
                 "all 755 tasks. winreg-kb documents that layout and leaves every field unknown, "
                 "naming the FILETIME at offset 4 last_registered_time and the one at 12 launch_time "
                 "(https://github.com/libyal/winreg-kb/blob/278fdb847dcd5a80195da588d0e0941638bc41e0/docs/sources/system-keys/Task-scheduler.md#L122-L131, "
                 "https://github.com/libyal/winreg-kb/blob/278fdb847dcd5a80195da588d0e0941638bc41e0/winregrc/task_cache.yaml#L37-L53), "
                 "and Eric Zimmerman's TaskCache plugin reads offset 4 as the time the task was "
                 "created, 0x0C as last start, 0x1C as last stop, 0x14 as task state and 0x18 as last "
                 "action result "
                 "(https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.TaskCache/TaskCache.cs#L87-L105). "
                 "Last Start (UTC), Last Stop (UTC) and Registered (UTC) are the FILETIMEs at 0x0C, "
                 "0x1C and 4, a zero shown blank. On the Szechuan image, whose Task Scheduler "
                 "Operational log covers 2020-09-18 21:42 to 2020-09-19 01:24 UTC, Last Start equalled "
                 "the time of the task's latest Event ID 100 record within two seconds on all 14 tasks "
                 "whose Last Start falls in that span, Last Stop equalled its latest Event ID 102 or "
                 "201 (Task action finished) record on all 13 such tasks, and Registered equalled the "
                 "task's Event ID 106 (Task registered) record on all 9 tasks with one, and an Event "
                 "ID 140 (Task registration updated) record on 9 of the 20 tasks with those, 6 of them "
                 "the latest. Last Action Result is the 32-bit value at 0x18 in hexadecimal, as "
                 "stored; it was 0x00000000 on 707 of the 755 tasks. The 32-bit value at 0x14 is not "
                 "reported; it was zero on all 755. Action Type, Command, Arguments, Working "
                 "Directory, Class ID, Data and Action Context come from the task's Actions value, "
                 "whose layout was read from the values themselves and checked against the tasks' XML "
                 "definitions: a 16-bit version (3 on every task), the action context, then for each "
                 "action a 16-bit type and the action's ID, and for an Exec action (type 0x6666, as "
                 "Zimmerman's plugin reads it, "
                 "https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.TaskCache/TaskCache.cs#L112-L147) "
                 "its command, arguments and working directory, or for a COM handler action (type "
                 "0x7777) a 16-byte class ID and its data, each string in UTF-16LE preceded by its "
                 "length in bytes. Only the first action is decoded. On the four images the first "
                 "action matched the Exec command, arguments and working directory, or the ComHandler "
                 "ClassId and Data, of the task's XML definition on all 755 tasks (338 Exec, 417 COM "
                 "handler), no XML definition held more than one action, and Action Context equalled "
                 "the Context of the XML Actions element on all 755. Zimmerman's plugin skips a fixed "
                 "four bytes where the action's ID is stored, which misreads the 6 tested Exec actions "
                 "whose ID is not empty. Task Path is the task's Path value and Task ID its GUID. Tree "
                 "SD Present is Yes when the task's Tree key carries an SD value, No when it does not, "
                 "and blank when the task has no Tree key; Microsoft describes deleting that value as "
                 "hiding a task from schtasks /query and Task Scheduler (Reference: Microsoft Threat "
                 "Intelligence, 'Tarrask malware uses scheduled tasks for defense evasion', "
                 "https://www.microsoft.com/en-us/security/blog/2022/04/12/tarrask-malware-uses-scheduled-tasks-for-defense-evasion/). "
                 "It was Yes on every row of the tested images, and each task's Tree key held the "
                 "task's GUID as Id. Definition File is Yes when a file at the task's path under "
                 "Windows/System32/Tasks on the same volume was found; it was Yes for all 755 tasks. "
                 "In Tasks Key is No on a row for a Tree key whose Id names no Tasks subkey; such a "
                 "row carries only the path, the Id, Tree SD Present and Definition File. There were "
                 "27, 22 and 31 of them on af_case2_win10, lonewolf_win10 and pc_mus_001_win11 and 27 "
                 "on the Szechuan image, none with a definition file. Values not reported include "
                 "Hash, Triggers, SecurityDescriptor, Author, Description, Source, URI, Version, "
                 "Schema and Date.",
        "paths": ('*/Windows/System32/config/SOFTWARE', '*/Windows/System32/Tasks/*'),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 197 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 196 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 245 rows",
        },
    },
}


def dynamic_info(raw):
    """The fields of a DynamicInfo value, or None when it is shorter than 28 bytes."""
    if not isinstance(raw, (bytes, bytearray)) or len(raw) < 28:
        return None
    return {'registered': struct.unpack_from('<Q', raw, 4)[0],
            'last_start': struct.unpack_from('<Q', raw, 12)[0],
            'last_result': struct.unpack_from('<I', raw, 24)[0],
            'last_stop': struct.unpack_from('<Q', raw, 28)[0] if len(raw) >= 36 else 0}


def _string(raw, offset):
    """(text, next offset) of a UTF-16LE string preceded by its byte length as a 32-bit value."""
    if offset + 4 > len(raw):
        raise ValueError(f'no string length at offset {offset}')
    length = struct.unpack_from('<i', raw, offset)[0]
    if length < 0 or offset + 4 + length > len(raw):
        raise ValueError(f'a string length of {length} at offset {offset} runs past the value')
    return raw[offset + 4:offset + 4 + length].decode('utf-16-le', 'replace').rstrip('\x00'), \
        offset + 4 + length


def first_action(raw):
    """The context and first action of an Actions value; raises ValueError when it cannot."""
    if not isinstance(raw, (bytes, bytearray)) or len(raw) < 8:
        raise ValueError('shorter than a version and a context length')
    raw = bytes(raw)
    context, offset = _string(raw, 2)
    if offset + 2 > len(raw):
        raise ValueError('no action type after the context')
    magic = struct.unpack_from('<H', raw, offset)[0]
    action = {'context': context, 'type': _ACTION_TYPES.get(magic, f'0x{magic:04X} (not decoded)'),
              'command': '', 'arguments': '', 'working_directory': '', 'class_id': '', 'data': ''}
    if magic not in _ACTION_TYPES:
        return action
    _, offset = _string(raw, offset + 2)
    if magic == 0x6666:
        action['command'], offset = _string(raw, offset)
        action['arguments'], offset = _string(raw, offset)
        action['working_directory'], offset = _string(raw, offset)
    else:
        if offset + 16 > len(raw):
            raise ValueError('the class ID runs past the value')
        action['class_id'] = '{' + str(uuid.UUID(bytes_le=raw[offset:offset + 16])).upper() + '}'
        action['data'], offset = _string(raw, offset + 16)
    return action


def _values(key):
    return {value.name(): value.value() for value in key.values()}


def tree_entries(taskcache):
    """{lowercased task path: (path as stored, Id, SD present)} for Tree keys holding an Id."""
    entries = {}
    stack = [(taskcache.subkey('Tree'), '')]
    while stack:
        key, path = stack.pop()
        values = _values(key)
        if 'Id' in values:
            entries[path.lower()] = (path, str(values['Id']), 'SD' in values)
        for child in key.subkeys():
            stack.append((child, path + '\\' + child.name()))
    return entries


def definition_files(context, volume_prefix):
    """Lowercased task paths of the XML files under this volume's Windows/System32/Tasks."""
    found = set()
    for item in context.get_files_found():
        path = str(item)
        if not os.path.isfile(path):
            continue
        relative = '/' + context.get_relative_path(path).replace('\\', '/').lstrip('/')
        lowered = relative.lower()
        at = lowered.find(_TASKS_FOLDER)
        if at >= 0 and lowered[:at] == volume_prefix:
            found.add('\\' + relative[at + len(_TASKS_FOLDER):].replace('/', '\\').lower())
    return found


def _row(info, action, path, task_id, tree, definitions, in_tasks):
    tree_sd = '' if tree is None else ('Yes' if tree[2] else 'No')
    return (filetime_utc(info['last_start']) if info else '',
            filetime_utc(info['last_stop']) if info else '',
            filetime_utc(info['registered']) if info else '',
            path, f"0x{info['last_result']:08X}" if info else '',
            action.get('type', ''), action.get('command', ''), action.get('arguments', ''),
            action.get('working_directory', ''), action.get('class_id', ''), action.get('data', ''),
            action.get('context', ''), task_id, tree_sd,
            'Yes' if path.lower() in definitions else 'No', in_tasks)


@artifact_processor
def windowsTaskCache(context):
    data_headers = (('Last Start (UTC)', 'datetime'), ('Last Stop (UTC)', 'datetime'),
                    ('Registered (UTC)', 'datetime'), 'Task Path', 'Last Action Result',
                    'Action Type', 'Command', 'Arguments', 'Working Directory', 'Class ID',
                    'Data', 'Action Context', 'Task ID', 'Tree SD Present', 'Definition File',
                    'In Tasks Key')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('TaskCache: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted({str(f) for f in context.get_files_found()}):
        relative = '/' + context.get_relative_path(source).replace('\\', '/').lstrip('/')
        if not os.path.isfile(source) or not relative.lower().endswith('/windows/system32/config/software'):
            continue
        volume_prefix = relative.lower()[:-len('/windows/system32/config/software')]
        try:
            taskcache = Registry.Registry(source).open(_TASKCACHE)
        except Registry.RegistryKeyNotFoundException:
            logfunc(f'TaskCache: no TaskCache key in {relative.lstrip("/")}')
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'TaskCache: could not read {relative.lstrip("/")}: {exc}')
            continue
        tree = tree_entries(taskcache)
        definitions = definition_files(context, volume_prefix)
        seen_ids = set()
        undecoded = 0
        for task_key in taskcache.subkey('Tasks').subkeys():
            values = _values(task_key)
            path = str(values.get('Path', ''))
            task_id = task_key.name()
            seen_ids.add(task_id.upper())
            try:
                action = first_action(values.get('Actions'))
            except ValueError:
                undecoded += 1
                action = {}
            data_list.append(_row(dynamic_info(values.get('DynamicInfo')), action, path, task_id,
                                  tree.get(path.lower()), definitions, 'Yes'))
        tree_only = [entry for entry in tree.values() if entry[1].upper() not in seen_ids]
        for path, task_id, has_sd in tree_only:
            data_list.append(_row(None, {}, path, task_id, (path, task_id, has_sd), definitions, 'No'))
        if undecoded:
            logfunc(f'TaskCache: {undecoded} Actions values in {relative.lstrip("/")} could not be decoded')
        if tree_only:
            logfunc(f'TaskCache: {len(tree_only)} Tree keys in {relative.lstrip("/")} name a task '
                    f'with no Tasks entry')
        sources.append(source)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0])), reverse=False)
    return data_headers, data_list, '\n'.join(sources)
