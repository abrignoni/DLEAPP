"""mIRC chat logs and connection settings for DLEAPP.

Author: @AlexisBrignoni, Claude.

mIRC writes one text log per window (channel, private query, status) into its logs folder, and keeps its settings in
mirc.ini. The log layout and the mirc.ini keys used here were measured on known data made with mIRC 7.86 and checked
against the mIRC 6.12-era files of cfreds_hacking_case_winxp; see the notes.
"""

import configparser
import os
import re
from collections import OrderedDict
from datetime import datetime

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import user_from_path

_SESSION_FORMAT = '%a %b %d %H:%M:%S %Y'
_COLOUR_PREFIX = re.compile(r'^\x03\d{1,2}(?:,\d{1,2})?')
_TIME = re.compile(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\] ?(.*)$')
_NICK = re.compile(r'^<([^<> ]+)> ?(.*)$')
_CONTROL = re.compile(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|[\x02\x0f\x16\x1d\x1e\x1f]')
_SETTINGS = (('Name', 'mirc', 'user'), ('Email', 'mirc', 'email'), ('Nickname', 'mirc', 'nick'),
             ('Alternative Nickname', 'mirc', 'anick'), ('Server (as stored)', 'mirc', 'host'),
             ('Ident User ID (as stored)', 'ident', 'userid'), ('Logs Folder (as stored)', 'dirs', 'logdir'),
             ('Version (as stored)', 'about', 'version'))

__artifacts_v2__ = {
    "mircLogLines": {
        "name": "mIRC Log Lines",
        "description": "Lines of mIRC's chat logs, one per channel, private or status window, with the session they "
                       "belong to, the time mIRC wrote before each line, and the nickname for message lines.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "mIRC",
        "notes": "One row per line of a log other than the Session Start, Session Ident and Session Close lines, blank lines, and lines holding only '-', which mIRC 7.86 wrote between server replies in the status window (mirc.ini [text] linesep was '-' on the known data). Read from the .log files in a logs folder under a folder named mIRC, and in one folder below it (mIRC's help, Logging topic, https://www.mirc.com/help/html/logging.html, fetched 2026-11-04 and the same as the mirc.chm shipped with 7.86: the Include network option puts the network name in the log file name, and its make folder option makes a logs folder per network). mIRC can be set to keep its logs elsewhere ([dirs] logdir in mirc.ini, shown by mIRC Settings); logs kept elsewhere are not read. On the known data (corpus key windows11_arm_mirc_known_20261104, mIRC 7.86 with its default logging options, connected to a test IRC server on the same computer, network KDNet) mIRC wrote one file per window: #kdtest.KDNet.log for a channel, kdpeer.KDNet.log for a private query and status.KDNet.log for the status window. Each session in a file opens with a Session Start line and a Session Ident line naming the window, and ends with a Session Close line. Session times are as mIRC wrote them, local time with no time zone recorded, reformatted as YYYY-MM-DD HH:MM:SS (kept as stored if they do not parse): on the known data, made on a computer set to UTC-5, the channel's Session Start was five hours behind the UTC time the test server logged for the join, to the second. Text is decoded as UTF-8, or as Windows-1252 when it is not UTF-8. Session Start (local) and Window are those of the session the line is in. Time (as logged) is the timestamp mIRC wrote at the start of the line, as stored: hours and minutes ([HH:nn]) on both tested installs, so it is not combined with the session date, as a session can run past midnight. Nickname is set when the rest of the line begins with <nickname>, the form mIRC wrote for channel and private messages: on the known data the test client's own messages were written under the nickname set in its Options dialog and the other users' under theirs. Other lines (joins, parts, quits, topics, server replies) have no Nickname, and so do CTCP ACTION lines, which mIRC wrote as '* nickname text' like those. Text is the rest of the line with IRC formatting codes (bold, colour, reverse, italic, strikethrough, underline and reset) removed; on the known data mIRC 7.86 wrote a colour code before the time of the event lines and of the test client's own messages (the help's Line colors option), which is removed too. Log File is the file's name and Line its line number. On cfreds_hacking_case_winxp (mIRC 6.12) the 12 logs gave 258 lines, 124 with a Nickname, in 12 sessions; on the known data 3 logs gave 17 lines, 4 with a Nickname. A row records a line mIRC logged, not that anyone read it.",
        "paths": ('*/mIRC/logs/*.log', '*/mIRC/logs/*/*.log'),
        "output_types": ["standard"],
        "artifact_icon": "message-square",
        "sample_data": {
            "windows11_arm_mirc_known_20261104": "Windows 11 build 26200 (ARM64), mIRC 7.86 | 17 rows",
            "cfreds_hacking_case_winxp": "Windows XP, mIRC 6.12 | 258 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no mIRC)",
        },
    },
    "mircLogSessions": {
        "name": "mIRC Log Sessions",
        "description": "Each logging session in mIRC's chat logs: the window it logged and when the session started "
                       "and closed, as mIRC wrote them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "mIRC",
        "notes": "One row per Session Start line in a log. Read from the .log files in a logs folder under a folder named mIRC, and in one folder below it (mIRC's help, Logging topic, https://www.mirc.com/help/html/logging.html, fetched 2026-11-04 and the same as the mirc.chm shipped with 7.86: the Include network option puts the network name in the log file name, and its make folder option makes a logs folder per network). mIRC can be set to keep its logs elsewhere ([dirs] logdir in mirc.ini, shown by mIRC Settings); logs kept elsewhere are not read. On the known data (corpus key windows11_arm_mirc_known_20261104, mIRC 7.86 with its default logging options, connected to a test IRC server on the same computer, network KDNet) mIRC wrote one file per window: #kdtest.KDNet.log for a channel, kdpeer.KDNet.log for a private query and status.KDNet.log for the status window. Each session in a file opens with a Session Start line and a Session Ident line naming the window, and ends with a Session Close line. Session times are as mIRC wrote them, local time with no time zone recorded, reformatted as YYYY-MM-DD HH:MM:SS (kept as stored if they do not parse): on the known data, made on a computer set to UTC-5, the channel's Session Start was five hours behind the UTC time the test server logged for the join, to the second. Text is decoded as UTF-8, or as Windows-1252 when it is not UTF-8. Session Close (local) is the Session Close line that ends the session, blank if the file has none for it. Lines is the number of mIRC Log Lines rows the session holds. Window is the Session Ident line that follows Session Start: a channel name, a nickname for a private query, or Status Window. On cfreds_hacking_case_winxp each of the 12 logs held one session; on the known data the 3 logs held one each. A session records when mIRC had that window's log open, not when anyone was reading it.",
        "paths": ('*/mIRC/logs/*.log', '*/mIRC/logs/*/*.log'),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "windows11_arm_mirc_known_20261104": "Windows 11 build 26200 (ARM64), mIRC 7.86 | 3 rows",
            "cfreds_hacking_case_winxp": "Windows XP, mIRC 6.12 | 12 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no mIRC)",
        },
    },
    "mircSettings": {
        "name": "mIRC Settings",
        "description": "The name, email, nicknames and server mIRC keeps in mirc.ini, with its logs folder and version "
                       "as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "mIRC",
        "notes": "One row per mirc.ini, the file mIRC keeps its settings in (mIRC's help, Command Line topic, https://www.mirc.com/help/html/command_line.html: -r sets the folder where mIRC saves mirc.ini). Read with Python's configparser, as text decoded as UTF-8 or Windows-1252. Name, Email, Nickname and Alternative Nickname are the [mirc] values user, email, nick and anick: on the known data (corpus key windows11_arm_mirc_known_20261104) the Name, Email, Nickname and Alternative fields of mIRC 7.86's Options dialog were set to test values and saved under exactly those keys, and when mIRC connected it sent that nickname and that name to the test server. Server (as stored) is [mirc] host as stored; on the known data it named the address and port of the server mIRC had last connected to, given on its command line, and what else it can hold was not established. Ident User ID (as stored) is [ident] userid as stored (empty on the known data); its meaning was not established. Logs Folder (as stored) is [dirs] logdir, logs\\ on both tested installs, where the logs were found beside mirc.ini. Version (as stored) is [about] version: 7.86 on the known data, the installed version, and 6.12 on cfreds_hacking_case_winxp. Folder is the folder of the mirc.ini read: Program Files\\mIRC on the Windows XP image and the user's AppData\\Roaming\\mIRC on the known data. Not read: urls.ini, servers.ini and channels.ini, which on the known data held the lists the installer wrote. A setting records what mIRC was set to when it last saved the file, not when it was set.",
        "paths": ('*/mIRC/mirc.ini',),
        "output_types": ["standard"],
        "artifact_icon": "settings",
        "sample_data": {
            "windows11_arm_mirc_known_20261104": "Windows 11 build 26200 (ARM64), mIRC 7.86 | 1 row",
            "cfreds_hacking_case_winxp": "Windows XP, mIRC 6.12 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no mIRC)",
        },
    },
}


def _text(raw):
    """mIRC log and ini bytes as text: UTF-8, else Windows-1252."""
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', 'replace')


def _session_time(value):
    """A Session Start or Session Close time as 'YYYY-MM-DD HH:MM:SS', or the text as stored if it does not parse."""
    try:
        return datetime.strptime(value.strip(), _SESSION_FORMAT).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return value.strip()


def parse_log(text):
    """(sessions, lines) of one mIRC log.

    sessions: dicts with start, close, window, lines. lines: (session start, time, window, nick, text, line number).
    """
    sessions, lines = [], []
    current = None
    for number, raw in enumerate(text.split('\n'), 1):
        line = raw.rstrip('\r')
        if not line.strip():
            continue
        if line.startswith('Session Start: '):
            current = {'start': _session_time(line[15:]), 'close': '', 'window': '', 'lines': 0}
            sessions.append(current)
            continue
        if line.startswith('Session Ident: ') and current is not None and not current['window']:
            current['window'] = line[15:].strip()
            continue
        if line.startswith('Session Close: '):
            if current is not None:
                current['close'] = _session_time(line[15:])
            current = None
            continue
        body = _COLOUR_PREFIX.sub('', line, count=1)
        if body == '-':
            continue
        when = ''
        matched = _TIME.match(body)
        if matched:
            when, body = matched.group(1), matched.group(2)
        nick = ''
        said = _NICK.match(body)
        if said:
            nick, body = said.group(1), said.group(2)
        if current is not None:
            current['lines'] += 1
        lines.append((current['start'] if current else '', when, current['window'] if current else '', nick,
                      _CONTROL.sub('', body), number))
    return sessions, lines


def _logs(context):
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or not path.lower().endswith('.log'):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                text = _text(handle.read())
        except OSError as exc:
            logfunc(f'mIRC: could not read {relative}: {type(exc).__name__}')
            continue
        yield path, relative, text


@artifact_processor
def mircLogLines(context):
    data_headers = ('Session Start (local)', 'Time (as logged)', 'Window', 'Nickname', 'Text', 'Log File', 'Line',
                    'User')
    data_list, sources = [], []
    for path, relative, text in _logs(context):
        _sessions, lines = parse_log(text)
        name = os.path.basename(relative.replace('\\', '/'))
        for start, when, window, nick, said, number in lines:
            data_list.append((start, when, window, nick, said, name, number,
                              user_from_path(context.get_relative_path(path))))
        if lines:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def mircLogSessions(context):
    data_headers = ('Session Start (local)', 'Session Close (local)', 'Window', 'Lines', 'Log File', 'User')
    data_list, sources = [], []
    for path, relative, text in _logs(context):
        sessions, _lines = parse_log(text)
        name = os.path.basename(relative.replace('\\', '/'))
        for session in sessions:
            data_list.append((session['start'], session['close'], session['window'], session['lines'], name,
                              user_from_path(context.get_relative_path(path))))
        if sessions:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def mircSettings(context):
    data_headers = tuple(label for label, _section, _key in _SETTINGS) + ('Folder', 'User')
    data_list, sources = [], []
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or os.path.basename(path).lower() != 'mirc.ini':
            continue
        relative = context.get_relative_path(path)
        parser = configparser.RawConfigParser(strict=False, interpolation=None, dict_type=OrderedDict)
        parser.optionxform = str
        try:
            with open(path, 'rb') as handle:
                parser.read_string(_text(handle.read()))
        except (OSError, configparser.Error) as exc:
            logfunc(f'mIRC Settings: could not read {relative}: {type(exc).__name__}')
            continue
        values = tuple(parser.get(section, key, fallback='') for _label, section, key in _SETTINGS)
        data_list.append(values + (os.path.dirname(relative.replace('\\', '/')),
                                   user_from_path(context.get_relative_path(path))))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
