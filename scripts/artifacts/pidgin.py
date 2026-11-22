"""Pidgin chat logs, accounts, buddies, saved rooms and custom smileys for DLEAPP.

Author: @AlexisBrignoni, Claude.

Pidgin keeps its data in a .purple folder. The log layout and the XML elements read here come from the writers in the
Pidgin 2.14.14 source (libpurple/log.c, account.c, blist.c, smiley.c) and were checked on known data made with 2.14.14.
"""

import hashlib
import html
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

from scripts.ilapfuncs import artifact_processor, check_in_media, logfunc
from scripts.windows_registry import user_from_path

__artifacts_v2__ = {
    "pidginMessages": {
        "name": "Pidgin Messages",
        "description": "Entries of Pidgin's HTML and plain text logs for conversations, rooms and account system "
                       "logs, with the account, the conversation, the sender and the time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Pidgin",
        "platforms": ("Windows", "Linux"),
        "notes": "Read from the Pidgin 2.14.14 source and checked on known data (corpus key "
                 "windows11_arm_pidgin_known_20261121: Pidgin 2.14.14 on Windows 11 with one XMPP test account "
                 "against a test server on the same computer). The known data exercised Kind Message, Action "
                 "and System in IM and room logs of both formats. Kinds Auto-reply, Whisper, Error, Raw and "
                 "Unparsed, account system logs, a blank Message Time, the next-day and late-message steps and "
                 "messages of more than one line were read from the source only. Other protocols, other Pidgin "
                 "versions and Linux were not tested. User is the folder after Users in the path and is blank "
                 "when there is none. One row per logged entry. A message that spans several lines of the file "
                 "is one row. Time (as logged) is the text Pidgin wrote. By default it is a time of day, or a "
                 "date and time in a system log or when the message was logged more than 20 minutes after its "
                 "own time (log.c, log_get_timestamp). Both use the format of the locale Pidgin ran under "
                 "(util.c). Message Time is derived from it, using the date and UTC offset in the log's file "
                 "name. A time of day up to 20 minutes earlier than the line before it is read as a message "
                 "delivered late, which Pidgin logs with its own time and no date, and keeps its date. A time "
                 "earlier by more than that puts this line and the later lines on the next day, as in a log "
                 "that runs past midnight. A real gap of 23 hours 40 minutes or more between two lines can be "
                 "read as a late message, so compare with Time (as logged) and Log Started. It is blank when "
                 "the text does not parse or when its date could be read as either month-first or day-first. "
                 "The offset is the one in force when the log was opened, so a log that runs across a daylight "
                 "saving change is off by the change after it. Direction is set only for HTML logs, from the "
                 "colour log.c writes for a sent or received message. It is blank for /me actions, which use "
                 "one colour for both, and for all text logs. In a text log Sender is the text before the "
                 "first colon and space, when it has no space or matches an alias element in accounts.xml or "
                 "blist.xml. A system line starting with one word and a colon can read as a sender. A message "
                 "whose sender name has a space and matches no alias has Kind System and no Sender. A /me "
                 "action in a text log has a Sender only when it starts with such an alias. Otherwise its "
                 "whole text, sender included, is in Text. The known data has one account, one protocol and "
                 "one Windows user, so Account, Protocol and User each held one value on all rows there. In an "
                 "HTML log a line that matches no form the 2.14.14 writer produces is added to the Text of the "
                 "row before it when that row has no closing line break, and is otherwise kept with Kind "
                 "'Unparsed'. In a text log a line that does not start with a time in parentheses is added to "
                 "the Text of the row before it. A text-log line with a time and no recognised sender has Kind "
                 "'System', which includes whispers and errors. Protocol here is the short name in the log "
                 "header or folder. The other Pidgin artifacts show the protocol id from the XML. A row "
                 "records a line Pidgin logged, not that anyone read it.",
        "paths": ('*/.purple/logs/*/*/*/*.html', '*/.purple/logs/*/*/*/*.txt', '*/.purple/accounts.xml',
                  '*/.purple/blist.xml'),
        "output_types": ["standard"],
        "artifact_icon": "message-square",
        "sample_data": {
            "windows11_arm_pidgin_known_20261121": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 | 30 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no .purple files matched)",
        },
    },
    "pidginAccounts": {
        "name": "Pidgin Accounts",
        "description": "Accounts in Pidgin's accounts.xml, with the alias, the stored password and the connection "
                       "settings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Pidgin",
        "platforms": ("Windows", "Linux"),
        "notes": "Read from the Pidgin 2.14.14 source and checked on known data (corpus key "
                 "windows11_arm_pidgin_known_20261121: Pidgin 2.14.14 on Windows 11 with one XMPP test account "
                 "against a test server on the same computer). Other protocols, other Pidgin versions and "
                 "Linux were not tested. User is the folder after Users in the path and is blank when there is "
                 "none. One row per account element. Password is the password element as stored, which Pidgin "
                 "2.14.14 writes in clear text when the account is set to remember it (account.c). A password "
                 "element with a keyring_id attribute comes from libpurple 3. Its value is clear text when "
                 "keyring_id is keyring-internal and mode is empty or cleartext, and ciphertext otherwise "
                 "(account.c). The two attributes are in Other Settings as password_keyring_id and "
                 "password_mode. The known data has no such element. Other Settings holds the remaining "
                 "setting elements as name=value, with interface settings prefixed by the interface name. The "
                 "proxy element (type, host, port, user name, password), the statuses other than the active "
                 "one and current_error are not read. User Info was empty on the known data.",
        "paths": ('*/.purple/accounts.xml',),
        "output_types": ["standard"],
        "artifact_icon": "user",
        "sample_data": {
            "windows11_arm_pidgin_known_20261121": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no .purple files matched)",
        },
    },
    "pidginBuddies": {
        "name": "Pidgin Buddies",
        "description": "Buddies in Pidgin's blist.xml, with their group, alias, account and last seen time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Pidgin",
        "platforms": ("Windows", "Linux"),
        "notes": "Read from the Pidgin 2.14.14 source and checked on known data (corpus key "
                 "windows11_arm_pidgin_known_20261121: Pidgin 2.14.14 on Windows 11 with one XMPP test account "
                 "against a test server on the same computer). Other protocols, other Pidgin versions and "
                 "Linux were not tested. User is the folder after Users in the path and is blank when there is "
                 "none. One row per buddy element. Last Seen is the buddy's last_seen setting, Unix seconds, "
                 "shown in UTC and blank when absent. libpurple writes the computer's clock to it when an "
                 "online buddy goes offline, and for each buddy still online when the account disconnects "
                 "(blist.c, connection.c): on the known data both online buddies carry the time of the last "
                 "exit. It is not a time the buddy sent anything. The known data has one account, one protocol "
                 "and one Windows user, so Account, Protocol and User each held one value on all rows there. "
                 "Other Settings holds the remaining stored settings as name=value, and the contact's alias "
                 "when it has one. Other Settings had no value on any row of the known data. The privacy lists in "
                 "blist.xml are not read.",
        "paths": ('*/.purple/blist.xml',),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "windows11_arm_pidgin_known_20261121": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no .purple files matched)",
        },
    },
    "pidginSavedRooms": {
        "name": "Pidgin Saved Rooms",
        "description": "Rooms saved in Pidgin's buddy list, with their room, server, handle, account and auto-join "
                       "setting.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Pidgin",
        "platforms": ("Windows", "Linux"),
        "notes": "Read from the Pidgin 2.14.14 source and checked on known data (corpus key "
                 "windows11_arm_pidgin_known_20261121: Pidgin 2.14.14 on Windows 11 with one XMPP test account "
                 "against a test server on the same computer). Other protocols, other Pidgin versions and "
                 "Linux were not tested. User is the folder after Users in the path and is blank when there is "
                 "none. One row per chat element of blist.xml. Room, Server and Handle are the components of "
                 "that name, which are protocol specific, and any other component is in Other Settings. Auto "
                 "Join is the gtk-autojoin setting. On the known data the one saved room was placed in "
                 "blist.xml before Pidgin first started. Pidgin kept it and joined it.",
        "paths": ('*/.purple/blist.xml',),
        "output_types": ["standard"],
        "artifact_icon": "hash",
        "sample_data": {
            "windows11_arm_pidgin_known_20261121": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no .purple files matched)",
        },
    },
    "pidginCustomSmileys": {
        "name": "Pidgin Custom Smileys",
        "description": "Custom smileys in Pidgin's smileys.xml, with the shortcut text and the image.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Pidgin",
        "platforms": ("Windows", "Linux"),
        "notes": "Read from the Pidgin 2.14.14 source and checked on known data (corpus key "
                 "windows11_arm_pidgin_known_20261121: Pidgin 2.14.14 on Windows 11 with one XMPP test account "
                 "against a test server on the same computer). Other protocols, other Pidgin versions and "
                 "Linux were not tested. User is the folder after Users in the path and is blank when there is "
                 "none. One row per smiley element. Checksum is stored by Pidgin. SHA-1 Matches compares it "
                 "with the SHA-1 of the file in custom_smiley, and is blank when that file is not in the "
                 "extraction.",
        "paths": ('*/.purple/smileys.xml', '*/.purple/custom_smiley/*'),
        "output_types": ["standard"],
        "artifact_icon": "image",
        "sample_data": {
            "windows11_arm_pidgin_known_20261121": "Windows 11 build 26200 (ARM64), Pidgin 2.14.14 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no .purple files matched)",
        },
    },
}

_FILE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})\.(\d{2})(\d{2})(\d{2})([+-])(\d{2})(\d{2}).*\.(?:html|txt)$', re.I)
_CLOCK = r'(\d{1,2}):(\d{2}):(\d{2})(?:\s*([AaPp])\.?[Mm]\.?)?'
_TIME_ONLY = re.compile(rf'^{_CLOCK}$')
_DATE_TIME = re.compile(rf'^(\d{{1,2}})/(\d{{1,2}})/(\d{{2,4}})\s+{_CLOCK}$')
_HEADER = re.compile(r'^(?:Conversation with (?P<conv>.+) at .+|System log for account (?P<sys>.+?) \((?P<sysp>[^()]+)\) '
                     r'connected at .+)$')
_HEADER_ON = re.compile(r' on (?P<acct>\S.*) \((?P<prot>[^()]+)\)$')
_TITLE = re.compile(r'<title>(.*?)</title>', re.S)
_HTML_LINE = re.compile(r'^(?:<span style="color: (#[0-9A-Fa-f]{6})">)?<span style="font-size: smaller">\((.*?)\)'
                        r'</span>(.*)$', re.S)
_HTML_NAME = re.compile(r'^\s*<b>\s*(.*?)</b></span>\s?(.*)$', re.S)
_SYSTEM = re.compile(r'^---- (.*) @ (.+?) ----(?:<br\s*/?>)?$', re.S)
_TXT_LINE = re.compile(r'^\(([^()]{4,40})\) (.*)$', re.S)
_LATE = timedelta(minutes=20)
_SENT, _RECEIVED, _ERROR = '#16569E', '#A82F2F', '#FF0000'


class _Text(HTMLParser):
    """Visible text of a logged message. A line break becomes a newline and an image keeps its reference."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.parts.append('\n')
        elif tag == 'img':
            values = dict(attrs)
            self.parts.append(f"[image: {values.get('src') or values.get('id') or ''}]")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.parts.append(data)


def _strip(markup):
    parser = _Text()
    parser.feed(markup)
    parser.close()
    return ''.join(parser.parts).strip()


def _decode(raw):
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('cp1252', 'replace')


def _read(path):
    with open(path, 'rb') as handle:
        return _decode(handle.read())


def _hour(hour, marker):
    if marker:
        hour = hour % 12 + (12 if marker.lower() == 'p' else 0)
    return hour


class _Clock:
    """Turns a logged time into UTC, from the date and offset in the log's file name."""

    def __init__(self, name):
        found = _FILE.match(name)
        self.start = self.offset = self.previous = None
        if found:
            year, month, day, hour, minute, second = (int(found.group(i)) for i in range(1, 7))
            sign = -1 if found.group(7) == '-' else 1
            self.offset = timedelta(minutes=sign * (int(found.group(8)) * 60 + int(found.group(9))))
            try:
                self.previous = datetime(year, month, day, hour, minute, second)
            except ValueError:
                self.offset = None
                return
            self.start = self._utc(self.previous)

    def _utc(self, local):
        return (local - self.offset).replace(tzinfo=timezone.utc)

    def convert(self, text):
        if self.offset is None:
            return ''
        text = text.strip()
        only = _TIME_ONLY.match(text)
        try:
            if only:
                local = self.previous.replace(hour=_hour(int(only.group(1)), only.group(4)),
                                              minute=int(only.group(2)), second=int(only.group(3)))
                for late in (local, local - timedelta(days=1)):
                    if self.previous - _LATE <= late < self.previous:
                        return self._utc(late)
                while local < self.previous:
                    local += timedelta(days=1)
                self.previous = local
                return self._utc(local)
            full = _DATE_TIME.match(text)
            if not full:
                return ''
            first, second, year = int(full.group(1)), int(full.group(2)), int(full.group(3))
            if first > 12 >= second:
                day, month = first, second
            elif second > 12 >= first:
                month, day = first, second
            elif first == second:
                month = day = first
            else:
                return ''
            year += 2000 if year < 100 else 0
            return self._utc(datetime(year, month, day, _hour(int(full.group(4)), full.group(7)),
                                      int(full.group(5)), int(full.group(6))))
        except ValueError:
            return ''


def _log_parts(relative):
    parts = relative.replace('\\', '/').split('/')
    lower = [part.lower() for part in parts]
    for index in range(len(parts) - 1, 0, -1):
        if lower[index] == 'logs' and lower[index - 1] == '.purple' and len(parts) >= index + 5:
            return parts[index + 1], parts[index + 2], parts[index + 3]
    return '', '', ''


def _html_rows(text):
    rows, last_open = [], False
    for number, raw in enumerate(text.split('\n'), 1):
        line = raw.rstrip('\r')
        if number == 1 or not line or line in ('</p>', '</body>', '</html>'):
            continue
        system = _SYSTEM.match(line)
        if system:
            rows.append([number, system.group(2), '', '', 'System', _strip(system.group(1))])
            last_open = False
            continue
        found = _HTML_LINE.match(line)
        if not found:
            if last_open and rows:
                rows[-1][5] = f"{rows[-1][5]}\n{_strip(line)}".strip()
                last_open = not line.endswith('<br>')
            else:
                rows.append([number, '', '', '', 'Unparsed', _strip(line)])
            continue
        colour, when, rest = found.groups()
        last_open = not line.endswith('<br>')
        rest = re.sub(r'<br>$', '', rest)
        if colour is None:
            if rest.startswith('<b>'):
                rows.append([number, when, '', '', 'System', _strip(rest)])
            else:
                rows.append([number, when, '', '', 'Raw', _strip(rest)])
            continue
        name = _HTML_NAME.match(rest)
        if not name:
            rows.append([number, when, '', '', 'Unparsed', _strip(rest)])
            continue
        who, body = name.groups()
        if colour.upper() == _ERROR:
            rows.append([number, when, '', '', 'Error', _strip(who)])
            continue
        direction = {_SENT: 'Sent', _RECEIVED: 'Received'}.get(colour.upper(), '')
        who = html.unescape(who)
        if who.startswith('***'):
            rows.append([number, when, who[3:], '', 'Action', _strip(body)])
        elif who.endswith(' <AUTO-REPLY>:'):
            rows.append([number, when, who[:-14], direction, 'Auto-reply', _strip(body)])
        elif colour.upper() == '#6C2585':
            rows.append([number, when, who.rstrip(':'), '', 'Whisper', _strip(body)])
        else:
            rows.append([number, when, who.rstrip(':'), direction, 'Message', _strip(body)])
    return rows


def _txt_rows(text, aliases):
    rows = []
    for number, raw in enumerate(text.split('\n'), 1):
        line = raw.rstrip('\r')
        if number == 1 or not line:
            continue
        system = _SYSTEM.match(line)
        if system:
            rows.append([number, system.group(2), '', '', 'System', system.group(1)])
            continue
        found = _TXT_LINE.match(line)
        if not found or not re.search(r'\d:\d{2}', found.group(1)):
            if rows:
                rows[-1][5] = f'{rows[-1][5]}\n{line}'
            else:
                rows.append([number, '', '', '', 'Unparsed', line])
            continue
        when, rest = found.groups()
        if rest.startswith('***'):
            action = rest[3:]
            who = next((name for name in sorted(aliases, key=len, reverse=True) if action.startswith(name + ' ')), '')
            if not who and ' ' in action:
                rows.append([number, when, '', '', 'Action', action])
            else:
                rows.append([number, when, who or action, '', 'Action', action[len(who) + 1:] if who else ''])
            continue
        auto = rest.find(' <AUTO-REPLY>: ')
        if auto > 0:
            rows.append([number, when, rest[:auto], '', 'Auto-reply', rest[auto + 15:]])
            continue
        who, separator, body = rest.partition(': ')
        if separator and (' ' not in who or who in aliases):
            rows.append([number, when, who, '', 'Message', body])
        else:
            rows.append([number, when, '', '', 'System', rest])
    return rows


def _xml_root(path):
    try:
        return ET.fromstring(_read(path).lstrip('\ufeff'))
    except (OSError, ET.ParseError) as exc:
        logfunc(f'Pidgin: could not read {os.path.basename(path)}: {type(exc).__name__}')
        return None


def _found(context, name):
    return sorted(str(p) for p in context.get_files_found() if os.path.isfile(str(p)) and
                  os.path.basename(str(p)).lower() == name)


def _purple_key(path):
    return os.path.dirname(path)


def _settings(node):
    return {child.get('name', ''): (child.text or '') for child in node.findall('setting')}


def _other(values):
    return '; '.join(f'{key}={value}' for key, value in sorted(values.items()))


def _aliases(context):
    """Alias text per .purple folder, from accounts.xml and blist.xml."""
    result = {}
    for name, tag in (('accounts.xml', 'alias'), ('blist.xml', 'alias')):
        for path in _found(context, name):
            root = _xml_root(path)
            if root is None:
                continue
            bucket = result.setdefault(_purple_key(path), set())
            bucket.update(node.text for node in root.iter(tag) if node.text)
    return result


@artifact_processor
def pidginMessages(context):
    data_headers = (('Message Time', 'datetime'), ('Log Started', 'datetime'), 'Time (as logged)', 'Account', 'Protocol',
                    'Conversation', 'Conversation Type', 'Sender', 'Direction', 'Kind', 'Text', 'Log File', 'Line',
                    'User')
    data_list, sources = [], []
    aliases = _aliases(context)
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or not path.lower().endswith(('.html', '.txt')):
            continue
        relative = context.get_relative_path(path)
        protocol, account, target = _log_parts(relative)
        if not target:
            continue
        try:
            text = _read(path)
        except OSError as exc:
            logfunc(f'Pidgin: could not read a log: {type(exc).__name__}')
            continue
        name = os.path.basename(relative.replace('\\', '/'))
        purple = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(path)))))
        is_html = name.lower().endswith('.html')
        first = text.split('\n', 1)[0].rstrip('\r')
        header = first
        if is_html:
            title = _TITLE.search(first)
            header = html.unescape(title.group(1)) if title else ''
        on = _HEADER_ON.search(header)
        if on:
            account, protocol = on.group('acct'), on.group('prot')
        elif _HEADER.match(header) and _HEADER.match(header).group('sys'):
            account, protocol = _HEADER.match(header).group('sys'), _HEADER.match(header).group('sysp')
        if target == '.system':
            kind, conversation = 'System', ''
        elif target.endswith('.chat'):
            kind, conversation = 'Room', target[:-5]
        else:
            kind, conversation = 'IM', target
        rows = _html_rows(text) if is_html else _txt_rows(text, aliases.get(purple, set()))
        clock = _Clock(name)
        for number, when, sender, direction, line_kind, body in rows:
            data_list.append((clock.convert(when) if when else '', clock.start or '', when, account, protocol,
                              conversation, kind, sender, direction, line_kind, body, name, number,
                              user_from_path(relative)))
        if rows:
            sources.append(path)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[11], row[12]))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pidginAccounts(context):
    data_headers = ('Account', 'Protocol', 'Alias', 'Password', 'Connect Server', 'Port', 'Connection Security',
                    'Auto Login', 'Active Status', 'User Info', 'Other Settings', 'User')
    data_list, sources = [], []
    for path in _found(context, 'accounts.xml'):
        root = _xml_root(path)
        if root is None:
            continue
        relative = context.get_relative_path(path)
        for account in root.findall('account'):
            settings, auto = {}, ''
            for block in account.findall('settings'):
                values = _settings(block)
                if block.get('ui'):
                    auto = values.pop('auto-login', auto)
                    settings.update({f"{block.get('ui')}:{key}": value for key, value in values.items()})
                else:
                    settings.update(values)
            server, port, security = (settings.pop(key, '') for key in ('connect_server', 'port',
                                                                        'connection_security'))
            password = account.find('password')
            if password is not None:
                for attr in ('keyring_id', 'mode'):
                    if password.get(attr):
                        settings[f'password_{attr}'] = password.get(attr)
            active = next((status.get('type', '') for status in account.findall('statuses/status')
                           if status.get('active') == 'true'), '')
            data_list.append((account.findtext('name', ''), account.findtext('protocol', ''),
                              account.findtext('alias', ''), password.text or '' if password is not None else '',
                              server, port, security, {'1': 'Yes', '0': 'No'}.get(auto, auto), active,
                              account.findtext('userinfo', ''), _other(settings), user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pidginBuddies(context):
    data_headers = (('Last Seen', 'datetime'), 'Group', 'Buddy', 'Alias', 'Account', 'Protocol', 'Other Settings',
                    'User')
    data_list, sources = [], []
    for path in _found(context, 'blist.xml'):
        root = _xml_root(path)
        if root is None:
            continue
        relative = context.get_relative_path(path)
        for group in root.findall('blist/group'):
            for contact in group.findall('contact'):
                for buddy in contact.findall('buddy'):
                    settings = _settings(buddy)
                    seen = settings.pop('last_seen', '')
                    when = ''
                    if seen.isdigit() and int(seen) > 0:
                        try:
                            when = datetime.fromtimestamp(int(seen), timezone.utc)
                        except (OverflowError, OSError, ValueError):
                            settings['last_seen'] = seen
                    if contact.get('alias'):
                        settings['contact_alias'] = contact.get('alias')
                    data_list.append((when, group.get('name', ''), buddy.findtext('name', ''),
                                      buddy.findtext('alias', ''), buddy.get('account', ''), buddy.get('proto', ''),
                                      _other(settings), user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pidginSavedRooms(context):
    data_headers = ('Group', 'Alias', 'Room', 'Server', 'Handle', 'Auto Join', 'Account', 'Protocol', 'Other Settings',
                    'User')
    data_list, sources = [], []
    for path in _found(context, 'blist.xml'):
        root = _xml_root(path)
        if root is None:
            continue
        relative = context.get_relative_path(path)
        for group in root.findall('blist/group'):
            for chat in group.findall('chat'):
                components = {node.get('name', ''): (node.text or '') for node in chat.findall('component')}
                settings = _settings(chat)
                auto = settings.pop('gtk-autojoin', '')
                room, server, handle = (components.pop(key, '') for key in ('room', 'server', 'handle'))
                settings.update({f'component:{key}': value for key, value in components.items()})
                data_list.append((group.get('name', ''), chat.findtext('alias', ''), room, server, handle,
                                  {'1': 'Yes', '0': 'No'}.get(auto, auto), chat.get('account', ''),
                                  chat.get('proto', ''), _other(settings), user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def pidginCustomSmileys(context):
    data_headers = (('Image', 'media'), 'Shortcut', 'Checksum', 'SHA-1 Matches', 'File Name', 'User')
    data_list, sources = [], []
    files = {}
    for found in context.get_files_found():
        found = str(found)
        if os.path.isfile(found) and os.path.basename(os.path.dirname(found)).lower() == 'custom_smiley':
            files[(os.path.dirname(os.path.dirname(found)), os.path.basename(found))] = found
    for path in _found(context, 'smileys.xml'):
        root = _xml_root(path)
        if root is None:
            continue
        relative = context.get_relative_path(path)
        for smiley in root.iter('smiley'):
            filename = os.path.basename(smiley.get('filename', '').replace('\\', '/'))
            checksum = smiley.get('checksum', '')
            image = files.get((os.path.dirname(path), filename))
            media, matches = '', ''
            if image:
                media = check_in_media(image, filename)
                with open(image, 'rb') as handle:
                    matches = 'Yes' if hashlib.sha1(handle.read()).hexdigest() == checksum.lower() else 'No'
            data_list.append((media, smiley.get('shortcut', ''), checksum, matches, filename,
                              user_from_path(relative)))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
