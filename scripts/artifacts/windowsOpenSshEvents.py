"""Windows OpenSSH event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the OpenSSH Operational and Admin logs that Win32-OpenSSH (the OpenSSH
server and client shipped with Windows) writes each logged message to, and
splits the result, method, user and remote address out of the messages sshd
logs for an authentication attempt. Event IDs, field names and the message
formats are sourced in the notes.
"""

import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LOGS = ('OpenSSH%4Operational.evtx', 'OpenSSH%4Admin.evtx')
_PROVIDER = 'OpenSSH'

# Event ID -> level, from the Win32-OpenSSH event manifest (see notes).
_LEVELS = {'1': 'Critical', '2': 'Error', '3': 'Warning', '4': 'Informational'}

# sshd's authentication log line, auth.c auth_log():
# "%s %s%s%s for %s%.100s from %.200s port %d ssh2%s%s"
_AUTH = re.compile(r'^(Accepted|Failed|Postponed|Partial) (\S+) for (invalid user )?(.*)'
                   r' from (\S+) port (\d+) ssh2(?:: .*)?$', re.DOTALL)
# auth.c getpwnamallow(): "Invalid user %.100s from %.100s port %d"
_INVALID = re.compile(r'^Invalid user (.*) from (\S+) port (\d+)$', re.DOTALL)

__artifacts_v2__ = {
    "openSshEvents": {
        "name": "OpenSSH Events",
        "description": "Messages the Windows OpenSSH programs wrote to the OpenSSH "
                       "Operational and Admin event logs, with the result, method, user "
                       "and remote address of each authentication attempt sshd logged "
                       "split out.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from OpenSSH%4Operational.evtx and OpenSSH%4Admin.evtx, named in the report's "
                 "located-at line; only OpenSSH provider records with Event ID 1, 2, 3 or 4 are read. "
                 "Microsoft's OpenSSH for Windows is its fork of OpenSSH (Microsoft Learn, 'OpenSSH for "
                 "Windows overview', "
                 "https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh-overview, "
                 "naming https://github.com/PowerShell/openssh-portable), whose programs write a message "
                 "logged at critical level as event 1 and at error level as 2 in OpenSSH/Admin, at warning "
                 "level as 3 and informational level as 4 in OpenSSH/Operational, and at debug level as 6 "
                 "in OpenSSH/Debug, a channel its manifest leaves disabled, and write a message at any "
                 "other level to no event (tag v7.7.2.0: contrib/win32/win32compat/w32log.c, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/contrib/win32/win32compat/w32log.c#L51-L79, "
                 "and contrib/win32/openssh/openssh-events.man, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/contrib/win32/openssh/openssh-events.man#L7-L28). "
                 "Level is the manifest's name for that level: Critical, Error, Warning or Informational. "
                 "Program and Message are the event's process and payload fields as stored: the identity "
                 "the program opened its log with (log.c, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/log.c#L327) "
                 "and the message text. For a message in the form sshd logs for an authentication attempt, "
                 "'<result> <method> for [invalid user ]<user> from <address> port <port> ssh2' (auth.c at "
                 "v7.7.2.0, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/auth.c#L327-L348, "
                 "and the same at v10.0.0.0, "
                 "https://github.com/PowerShell/openssh-portable/blob/b8c08ef9da9450a94a9c5ef717d96a7bd83f3332/auth.c#L297-L318), "
                 "Login Result is the result (Accepted, Failed, Postponed or Partial), Method is the "
                 "method with any submethod after a slash, User is the user name, Invalid User is Yes when "
                 "the message carries 'invalid user', and Remote Address and Remote Port are the address "
                 "and port. For 'Invalid user <user> from <address> port <port>' (auth.c, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/auth.c#L621-L622 "
                 "and "
                 "https://github.com/PowerShell/openssh-portable/blob/b8c08ef9da9450a94a9c5ef717d96a7bd83f3332/auth.c#L530-L531), "
                 "User, Invalid User, Remote Address and Remote Port are filled the same way. Those "
                 "columns are blank for every other message. A program whose syslog facility is set to "
                 "LOCAL0 writes its messages to a log file instead of these events (w32log.c, "
                 "https://github.com/PowerShell/openssh-portable/blob/0f9808f1901f2783c78a45774844a3126e56a51e/contrib/win32/win32compat/w32log.c#L152-L170), "
                 "and that file is not read here. Process ID is the process ID in the record's Execution "
                 "element. Every record carried S-1-5-18 in its Security element, so no SID is reported. "
                 "Event Time (UTC) is the record's TimeCreated SystemTime, which python-evtx renders from "
                 "the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the record stores. "
                 "On af_case2_win10 OpenSSH/Operational held five informational messages from sshd, one of "
                 "them an accepted password login, and OpenSSH/Admin held none, so on its rows Event ID, "
                 "Level, Program and Computer each held one value on every row and Invalid User was empty "
                 "on every row; lonewolf_win10, pc_mus_001_win11 and szechuan_win10 carry neither log. The "
                 "Failed, Postponed, Partial and invalid user forms were checked with constructed records "
                 "only. A login row reports what sshd logged about the attempt, including the address it "
                 "recorded for the connection. A record python-evtx cannot render, or whose XML does not "
                 "parse, is counted in the run log and not reported; every record in this log rendered on "
                 "the tested images. Reading needs the python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/OpenSSH%4Operational.evtx",
                  "*/Windows/System32/winevt/Logs/OpenSSH%4Admin.evtx"),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 5 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no OpenSSH log on the image)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no OpenSSH log on the image)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no OpenSSH log on the image)",
        },
    },
}


def login_fields(message):
    """(result, method, user, invalid user, address, port) from an sshd login message."""
    match = _AUTH.match(message)
    if match:
        result, method, invalid, user, address, port = match.groups()
        return result, method, user, 'Yes' if invalid else '', address, port
    match = _INVALID.match(message)
    if match:
        user, address, port = match.groups()
        return '', '', user, 'Yes', address, port
    return ('',) * 6


def ssh_row(record):
    """One OpenSSH record as a report row."""
    message = record.get('payload')
    return (record.time, record.event_id, _LEVELS[record.event_id], record.get('process'),
            message, *login_fields(message), record.process_id, record.record_id,
            record.computer)


@artifact_processor
def openSshEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Level', 'Program', 'Message',
                    'Login Result', 'Method', 'User', 'Invalid User', 'Remote Address',
                    'Remote Port', 'Process ID', 'Record ID', 'Computer')
    data_list = []
    sources = []
    for log in _LOGS:
        records, read = read_event_records(
            context, log, 'OpenSSH Events', event_ids=set(_LEVELS), provider=_PROVIDER)
        data_list.extend(ssh_row(record) for record in records)
        sources.extend(read)
    return data_headers, data_list, '\n'.join(sources)
