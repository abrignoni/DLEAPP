"""Windows Scheduled Tasks parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange artifact that reads the Task Scheduler
store; this reads the task definition XML files directly, following Microsoft's
Task Scheduler Schema, and is not ported from that artifact.
"""

import os
import xml.etree.ElementTree as ET

from scripts.ilapfuncs import artifact_processor, logfunc

# Each scheduled task is stored as an XML definition under
# Windows\System32\Tasks (in a tree that mirrors the task's path). The XML
# records what the task runs (an executable or a COM handler), the account it
# runs as, its triggers, and registration metadata. This reads those XML files;
# it does not read the SOFTWARE hive TaskCache, so the last-run and next-run
# times kept there are not included.

__artifacts_v2__ = {
    "scheduledTasks": {
        "name": "Scheduled Tasks",
        "description": "Windows scheduled tasks from their Task Scheduler XML "
                       "definitions: what each task runs, the account it runs "
                       "as, its run level, whether it is enabled, its triggers "
                       "and registration metadata.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "none",
        "category": "Windows",
        "notes": "Rows from the Task Scheduler XML definitions under "
                 "Windows\\System32\\Tasks, one row per task, each named in "
                 "Source File. Task Name is the task's URI (its path in the Task "
                 "Scheduler tree) when the definition records one, otherwise the "
                 "file's path under the Tasks folder. Action Command and "
                 "Arguments are the executable and arguments of an Exec action as "
                 "stored; for a task that instead invokes a COM object the "
                 "command is shown as ComHandler with the COM ClassId, and a task "
                 "with neither action is left blank. Run As User is the task "
                 "principal's UserId or GroupId as stored, the account the task "
                 "is configured to run under (a name or a SID; the well-known SID "
                 "S-1-5-18 and the name System are the LocalSystem account). Run "
                 "Level is the principal's RunLevel as stored (HighestAvailable "
                 "runs the task elevated when the account allows it, "
                 "LeastPrivilege does not), blank when the definition records "
                 "none. Enabled is the task's Settings Enabled value as stored, "
                 "blank when the definition records none, which is not evidence "
                 "the task was disabled; an individual trigger can also be "
                 "enabled or disabled on its own, which is not reflected in this "
                 "column. Author, Description and Registration Date come from the "
                 "definition's RegistrationInfo and are blank when it records "
                 "none, which is common for tasks Windows ships. Registration "
                 "Date is the recorded Date as stored, a local time that may or "
                 "may not carry a UTC offset, and is reported as text rather than "
                 "converted. Triggers lists the trigger types present (for "
                 "example LogonTrigger, BootTrigger, CalendarTrigger, "
                 "TimeTrigger, EventTrigger) with each trigger's StartBoundary as "
                 "stored where present, blank when the definition records no "
                 "trigger such as for an on-demand task; the full schedule is not "
                 "expanded. A "
                 "scheduled task is a persistence and execution mechanism; its "
                 "presence does not establish that it ran. Format: Microsoft Task "
                 "Scheduler Schema, https://learn.microsoft.com/en-us/windows/"
                 "win32/taskschd/task-scheduler-schema ; element names confirmed "
                 "against the tested images.",
        "paths": ('*/Windows/System32/Tasks/*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 214 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 170 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 174 rows",
        },
    },
}


def _text(element, default=''):
    return element.text.strip() if element is not None and element.text else default


def _task_name(root, source):
    reg_info = root.find('{*}RegistrationInfo')
    uri = _text(reg_info.find('{*}URI')) if reg_info is not None else ''
    if uri:
        return uri
    normalized = source.replace('\\', '/')
    marker = '/Tasks/'
    idx = normalized.find(marker)
    if idx >= 0:
        return '\\' + normalized[idx + len(marker):].replace('/', '\\')
    return os.path.basename(source)


def _action(root):
    actions = root.find('{*}Actions')
    if actions is None:
        return '', ''
    exec_action = actions.find('{*}Exec')
    if exec_action is not None:
        return _text(exec_action.find('{*}Command')), _text(exec_action.find('{*}Arguments'))
    com_action = actions.find('{*}ComHandler')
    if com_action is not None:
        class_id = _text(com_action.find('{*}ClassId'))
        return (f'ComHandler ClassId={class_id}' if class_id else 'ComHandler'), ''
    return '', ''


def _triggers(root):
    triggers = root.find('{*}Triggers')
    if triggers is None:
        return ''
    summary = []
    for trigger in triggers:
        kind = trigger.tag.split('}')[-1]
        start = _text(trigger.find('{*}StartBoundary'))
        summary.append(f'{kind}@{start}' if start else kind)
    return '; '.join(summary)


@artifact_processor
def scheduledTasks(context):
    data_headers = ('Task Name', 'Action Command', 'Arguments', 'Run As User',
                    'Run Level', 'Enabled', 'Author', 'Registration Date',
                    'Triggers', 'Description', 'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()]:
        if os.path.isdir(source):
            continue
        relative_source = context.get_relative_path(source)
        try:
            with open(source, 'rb') as handle:
                root = ET.fromstring(handle.read())
        except (OSError, ET.ParseError):
            continue
        if root.tag.split('}')[-1] != 'Task':
            continue
        reg_info = root.find('{*}RegistrationInfo')
        principal = root.find('{*}Principals/{*}Principal')
        settings = root.find('{*}Settings')
        command, arguments = _action(root)
        data_list.append((
            _task_name(root, source), command, arguments,
            (_text(principal.find('{*}UserId')) or _text(principal.find('{*}GroupId')))
            if principal is not None else '',
            _text(principal.find('{*}RunLevel')) if principal is not None else '',
            _text(settings.find('{*}Enabled')) if settings is not None else '',
            _text(reg_info.find('{*}Author')) if reg_info is not None else '',
            _text(reg_info.find('{*}Date')) if reg_info is not None else '',
            _triggers(root),
            _text(reg_info.find('{*}Description')) if reg_info is not None else '',
            relative_source))
        sources.append(source)

    if not data_list:
        logfunc('Scheduled Tasks: no task definitions parsed')
    return data_headers, data_list, "\n".join(sources)
