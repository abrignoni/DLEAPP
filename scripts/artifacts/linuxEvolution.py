"""Contacts, calendar events and tasks in the local stores of Evolution Data Server (GNOME), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxEvolutionContacts": {
        "name": "Evolution Contacts",
        "description": "Contacts in a user's local Evolution Data Server address books (contacts.db), each with the "
                       "details its vCard holds and the revision time the vCard records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the address books Evolution Data Server keeps for a user, contacts.db in each folder under "
                 ".local/share/evolution/addressbook, the folder for the built-in Personal address book being named "
                 "system (Reference: evolution-data-server 3.56.2, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/libedataserver/e-data-server-util.c#L124-130, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L440-477, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L2341), "
                 "one row per row of its folder_id table, in table order. Each row holds the contact's vCard "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/libedata-book/e-book-sqlite.c#L2538), "
                 "and every column but Address Book and Source File is read from that vCard: Name is FN; Nickname, "
                 "Organization, Title, Birthday, Note and Categories are the vCard values as stored; Email "
                 "Addresses, Phone Numbers, Addresses and Web Pages list each value on its own line with its TYPE "
                 "labels in parentheses; Contact List is Yes for a vCard marked X-EVOLUTION-LIST; UID is the vCard "
                 "UID, or the row's uid when the vCard has none; Address Book is the folder name. Last Changed is "
                 "the vCard REV in UTC. Evolution Data Server sets REV from the clock when it stores a contact whose "
                 "vCard has none and whenever it stores a change "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L855-878, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L957-964, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L1033-1035, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L1553-1554), "
                 "so a contact created with a REV of its own keeps that value; when an address book's revision "
                 "guards are on, the time of day in REV encodes a counter instead "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L866-874). "
                 "An embedded photo is written to the book's photos folder and the vCard then names that file by a "
                 "file URI "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L681-704); "
                 "Photo shows the file of that name in the same book's photos folder, and an embedded photo still in "
                 "a vCard is shown from the vCard (tested with constructed input only). Removing a contact deletes "
                 "its row "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/addressbook/backends/file/e-book-backend-file.c#L1726-1730). "
                 "The revision guards were read in the source and not exercised; the address book caches Evolution "
                 "Data Server keeps for online accounts under .cache/evolution are not read. A REV not in UTC is "
                 "left blank and a photo file named by a contact but not in the extraction is counted in the run "
                 "log. Validated on ubuntu2604_arm64_eds, captured from a VM running evolution-data-server 3.56.2-8 "
                 "after known steps made by calling Evolution Data Server's own D-Bus methods, with the stores "
                 "copied after each step; the VM's clock was about 5,158 s ahead of real time, and the times below "
                 "are by that clock. The 4 rows are the 4 contacts the steps left: Known Alpha and Known List, "
                 "created at 02:22:50 UTC on 1 October, Known Bravo, modified at 02:23:02, and Known Delta, created "
                 "at 02:26:04, and each Last Changed is that step's second. Known Charlie, removed, has no row, and "
                 "neither its name nor its UID is anywhere in the file. Known List still gives Known Bravo's address "
                 "from before the change: the list holds the addresses written into it. None of the stored vCards "
                 "holds a creation time. Known Delta was sent with its photo embedded; Evolution Data Server wrote "
                 "it to the photos folder as dleapp_known_delta_photo-file0.image-2FJPEG, byte for byte the photo "
                 "sent, and the vCard names it by its absolute path in the user's home. Address Book held system on "
                 "all 4 rows, the only address book the steps used. No member of the other four tested images "
                 "matches the declared paths.",
        "paths": ("*/.local/share/evolution/addressbook/*/contacts.db",
                  "*/.local/share/evolution/addressbook/*/photos/*"),
        "output_types": "standard",
        "artifact_icon": "users",
        "sample_data": {
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS aarch64, evolution-data-server 3.56.2 | 4 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxEvolutionEvents": {
        "name": "Evolution Calendar Events",
        "description": "Events in a user's local Evolution Data Server calendars (calendar.ics), each with its start, "
                       "end, summary and the creation and change times stored with it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the calendars Evolution Data Server keeps for a user, calendar.ics in each folder under "
                 ".local/share/evolution/calendar, the folder for the built-in Personal calendar being named system "
                 "(Reference: evolution-data-server 3.56.2, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/libedataserver/e-data-server-util.c#L124-130, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L3848-3893, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file-events.c#L39), "
                 "one row per VEVENT in file order. The file is iCalendar "
                 "(https://www.rfc-editor.org/rfc/rfc5545). Start and End are DTSTART and DTEND as stored, "
                 "reformatted and not converted: a date alone for a date value, a time with UTC for a UTC value, and "
                 "otherwise the time as stored, with the zone it names, if any, in Time Zone "
                 "(https://www.rfc-editor.org/rfc/rfc5545#section-3.3.5); a zone beginning "
                 "/freeassociation.sourceforge.net/ is one built into libical "
                 "(https://github.com/libical/libical/blob/57ce34025066935f356fd539e6deb7a7a9952618/src/libical/icaltimezone.c#L64). "
                 "Summary, Location and Description are as stored; Repeats is the RRULE as stored, and the dates it "
                 "gives are not listed. Created and Last Modified are CREATED and LAST-MODIFIED in UTC. Evolution "
                 "Data Server sets both from the clock when it stores a new event that has no CREATED, and "
                 "LAST-MODIFIED alone when it stores a change "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L2395-2405, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L2583-2585); "
                 "it does not keep a CREATED the client leaves out of a change. A CREATED or LAST-MODIFIED not in "
                 "UTC is left blank and counted in the run log. Removing an event deletes it from the file. Calendar "
                 "caches for online accounts under .cache/evolution, and memos, are not read. Validated on "
                 "ubuntu2604_arm64_eds, captured from a VM running evolution-data-server 3.56.2-8 after known steps "
                 "made by calling Evolution Data Server's own D-Bus methods, with the stores copied after each step; "
                 "the VM's clock was about 5,158 s ahead of real time, and the times below are by that clock. The 3 "
                 "rows are the 3 events the steps left. The all-day and weekly events show the second they were "
                 "created, 02:22:56 UTC on 1 October, as Created and Last Modified. The UTC event was then changed "
                 "by a client that sent no CREATED: its row has no Created, and its Last Modified, 02:23:02, is the "
                 "change. The weekly event, sent with the time zone "
                 "/freeassociation.sourceforge.net/America/New_York, was stored with that zone and no VTIMEZONE. The "
                 "event removed in the steps is not in the file. Calendar held system on all 3 rows, the only "
                 "calendar the steps used. No member of the other four tested images matches the declared paths.",
        "paths": ("*/.local/share/evolution/calendar/*/calendar.ics",),
        "output_types": "standard",
        "artifact_icon": "calendar",
        "sample_data": {
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS aarch64, evolution-data-server 3.56.2 | 3 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
    "linuxEvolutionTasks": {
        "name": "Evolution Tasks",
        "description": "Tasks in a user's local Evolution Data Server task lists (tasks.ics), each with its due date, "
                       "status and the creation, completion and change times stored with it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the task lists Evolution Data Server keeps for a user, tasks.ics in each folder under "
                 ".local/share/evolution/tasks, the folder for the built-in Personal task list being named system "
                 "(Reference: evolution-data-server 3.56.2, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/libedataserver/e-data-server-util.c#L124-130, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L3848-3893, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file-todos.c#L39), "
                 "one row per VTODO in file order. The file is iCalendar "
                 "(https://www.rfc-editor.org/rfc/rfc5545). Due is DUE as stored, reformatted and not converted, "
                 "with the zone it names, if any, in Time Zone; Summary, Description, Status, Priority and Percent "
                 "Complete are as stored. Completed, Created and Last Modified are COMPLETED, CREATED and "
                 "LAST-MODIFIED in UTC; Evolution Data Server sets CREATED and LAST-MODIFIED as it does for events "
                 "(https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L2395-2405, "
                 "https://gitlab.gnome.org/GNOME/evolution-data-server/-/blob/9330886fe4c5685bd18d1979bd5c60cb9c3fcc6d/src/calendar/backends/file/e-cal-backend-file.c#L2583-2585), "
                 "and a value not in UTC is left blank and counted in the run log. Validated on "
                 "ubuntu2604_arm64_eds, captured from a VM running evolution-data-server 3.56.2-8 after known steps "
                 "made by calling Evolution Data Server's own D-Bus methods, with the stores copied after each step; "
                 "the VM's clock was about 5,158 s ahead of real time, and the times below are by that clock. The 2 "
                 "rows are the 2 tasks created at 02:22:56 UTC on 1 October. The completed task's Completed, "
                 "12:00:00 UTC on 30 September, is the value the step sent, more than 14 hours before the task was "
                 "stored, so on this store Completed was the client's value. Time Zone and Description were blank on "
                 "both rows: the tasks were sent with neither a zone on DUE nor a DESCRIPTION. Task List held system "
                 "on both rows. No member of the other four tested images matches the declared paths.",
        "paths": ("*/.local/share/evolution/tasks/*/tasks.ics",),
        "output_types": "standard",
        "artifact_icon": "check-square",
        "sample_data": {
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS aarch64, evolution-data-server 3.56.2 | 2 rows",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import base64
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

from scripts.ilapfuncs import (artifact_processor, check_in_embedded_media, check_in_media, logfunc,
                               open_sqlite_db_readonly)

_ESCAPES = {'n': '\n', 'N': '\n', ',': ',', ';': ';', '\\': '\\', ':': ':'}


def unfold(text):
    """Logical lines of a vCard or iCalendar text: a line break followed by a space or tab continues the line."""
    return re.sub(r'\r?\n[ \t]', '', text.replace('\r\n', '\n')).split('\n')


def parse_line(line):
    """(NAME, {PARAM: [values]}, raw value) for a content line, or None when it has no unquoted colon."""
    i, quoted = 0, False
    while i < len(line):
        ch = line[i]
        if ch == '"':
            quoted = not quoted
        elif ch == ':' and not quoted:
            break
        i += 1
    if i >= len(line):
        return None
    head, value = line[:i], line[i + 1:]
    parts, buf, quoted = [], '', False
    for ch in head:
        if ch == '"':
            quoted = not quoted
            buf += ch
        elif ch == ';' and not quoted:
            parts.append(buf)
            buf = ''
        else:
            buf += ch
    parts.append(buf)
    name = parts[0].split('.')[-1].upper()
    params = {}
    for part in parts[1:]:
        key, _, val = part.partition('=')
        if not _:
            params.setdefault('TYPE', []).append(key)
            continue
        params.setdefault(key.upper(), []).extend(v.strip('"') for v in re.findall(r'"[^"]*"|[^,]+', val))
    return name, params, value


def unescape(value):
    """A TEXT value with its backslash escapes resolved."""
    return re.sub(r'\\(.)', lambda m: _ESCAPES.get(m.group(1), m.group(0)), value)


def split_unescaped(value, sep):
    """Components of a structured value split on separators that are not escaped, each unescaped."""
    parts, buf, i = [], '', 0
    while i < len(value):
        if value[i] == '\\' and i + 1 < len(value):
            buf += value[i:i + 2]
            i += 2
            continue
        if value[i] == sep:
            parts.append(unescape(buf))
            buf = ''
        else:
            buf += value[i]
        i += 1
    parts.append(unescape(buf))
    return parts


def properties(lines):
    """Parsed content lines, skipping lines that are not content lines."""
    out = []
    for line in lines:
        parsed = parse_line(line) if line else None
        if parsed:
            out.append(parsed)
    return out


def _typed(value, params):
    kinds = [t.lower() for t in params.get('TYPE', [])]
    return f"{value} ({', '.join(kinds)})" if kinds else value


def contact_fields(vcard):
    """A dict of the reported fields of one vCard."""
    props = properties(unfold(vcard))
    f = {'emails': [], 'phones': [], 'addresses': [], 'urls': [], 'photo_uri': '', 'photo_data': None, 'list': False}
    for name, params, value in props:
        if name == 'FN':
            f['name'] = unescape(value)
        elif name == 'NICKNAME':
            f['nickname'] = ', '.join(p for p in split_unescaped(value, ',') if p)
        elif name == 'ORG':
            f['org'] = ', '.join(p for p in split_unescaped(value, ';') if p)
        elif name == 'TITLE':
            f['title'] = unescape(value)
        elif name == 'EMAIL':
            f['emails'].append(_typed(unescape(value), params))
        elif name == 'TEL':
            f['phones'].append(_typed(unescape(value), params))
        elif name == 'ADR':
            f['addresses'].append(_typed(', '.join(p for p in split_unescaped(value, ';') if p), params))
        elif name == 'BDAY':
            f['birthday'] = value
        elif name == 'URL':
            f['urls'].append(unescape(value))
        elif name == 'NOTE':
            f['note'] = unescape(value)
        elif name == 'CATEGORIES':
            f['categories'] = ', '.join(p for p in split_unescaped(value, ',') if p)
        elif name == 'REV':
            f['rev'] = value
        elif name == 'UID':
            f['uid'] = value
        elif name == 'X-EVOLUTION-LIST':
            f['list'] = value.strip().upper() == 'TRUE'
        elif name == 'PHOTO':
            if 'URI' in [v.upper() for v in params.get('VALUE', [])] or value.startswith('file:'):
                f['photo_uri'] = value
            elif [v.upper() for v in params.get('ENCODING', [])] in (['B'], ['BASE64']):
                try:
                    f['photo_data'] = base64.b64decode(value, validate=False)
                except ValueError:
                    f['photo_data'] = None
    return f


def utc_stamp(value):
    """A UTC datetime for a REV, CREATED, LAST-MODIFIED or COMPLETED value in UTC (ending Z), else None."""
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y%m%dT%H%M%SZ', '%Y-%m-%dT%H:%M:%S.%fZ'):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def ical_time(value, params):
    """(text, time zone) for a DATE or DATE-TIME value as stored: a date, a UTC time, a time in the TZID it names, or
    a floating time with no zone. The text is the value reformatted, never converted."""
    m = re.fullmatch(r'(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})(Z?))?', value.strip())
    if not m:
        return value, params.get('TZID', [''])[0]
    y, mo, d, h, mi, s, z = m.groups()
    if h is None:
        return f'{y}-{mo}-{d}', ''
    text = f'{y}-{mo}-{d} {h}:{mi}:{s}'
    if z:
        return text + ' UTC', ''
    return text, params.get('TZID', [''])[0]


def components(text, kind):
    """Lists of parsed properties, one per top-level component of the given kind (VEVENT, VTODO) in a VCALENDAR,
    leaving out nested components such as VALARM."""
    out, stack, current = [], [], None
    for name, params, value in properties(unfold(text)):
        if name == 'BEGIN':
            stack.append(value.upper())
            if value.upper() == kind and len(stack) == 2:
                current = []
            continue
        if name == 'END':
            if stack and stack[-1] == value.upper():
                stack.pop()
                if value.upper() == kind and len(stack) == 1 and current is not None:
                    out.append(current)
                    current = None
            continue
        if current is not None and len(stack) == 2:
            current.append((name, params, value))
    return out


def _first(props, name):
    for prop in props:
        if prop[0] == name:
            return prop
    return None


def prop_text(props, name):
    prop = _first(props, name)
    return unescape(prop[2]) if prop else ''


def _stamp(props, name, counts):
    prop = _first(props, name)
    if not prop:
        return ''
    when = utc_stamp(prop[2])
    if when is None:
        counts[f'{name} values not in UTC, left blank'] += 1
    return when or ''


def _ics_files(context, filename):
    for path in sorted({str(p) for p in context.get_files_found()}):
        if os.path.basename(path) == filename and os.path.isfile(path):
            yield path


def _read_text(path, counts):
    try:
        with open(path, 'rb') as handle:
            return handle.read().decode('utf-8', 'replace')
    except OSError:
        counts['files that could not be read'] += 1
        return None


@artifact_processor
def linuxEvolutionContacts(context):
    data_headers = (('Last Changed', 'datetime'), 'Name', 'Nickname', 'Organization', 'Title', 'Email Addresses',
                    'Phone Numbers', 'Addresses', 'Birthday', 'Web Pages', 'Note', 'Categories', 'Contact List',
                    ('Photo', 'media'), 'UID', 'Address Book', 'Source File')
    data_list, read, counts = [], [], Counter()
    found = sorted({str(p) for p in context.get_files_found()})
    for path in found:
        if os.path.basename(path) != 'contacts.db' or not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        folder = os.path.dirname(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            counts['files that could not be opened as SQLite'] += 1
            continue
        try:
            try:
                tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
                if 'folder_id' not in tables:
                    counts['files with no folder_id table, not reported'] += 1
                    continue
                cards = db.execute('SELECT uid, vcard FROM folder_id ORDER BY rowid').fetchall()
            finally:
                db.close()
        except sqlite3.Error as exc:
            logfunc(f'Evolution Contacts: could not read {relative}: {exc}')
            continue
        for uid, vcard in cards:
            if not vcard:
                counts['rows with no vCard, not reported'] += 1
                continue
            f = contact_fields(vcard)
            when = utc_stamp(f.get('rev', '')) if f.get('rev') else None
            if f.get('rev') and when is None:
                counts['REV values not in UTC, left blank'] += 1
            photo = ''
            if f['photo_uri']:
                name = os.path.basename(unquote(urlparse(f['photo_uri']).path))
                local = os.path.join(folder, 'photos', name)
                if name and local in found:
                    photo = check_in_media(local, name) or ''
                else:
                    counts['photo files named by a contact and not in the extraction'] += 1
            elif f['photo_data']:
                photo = check_in_embedded_media(path, f['photo_data'], f'{uid} photo') or ''
            data_list.append((when or '', f.get('name', ''), f.get('nickname', ''), f.get('org', ''),
                              f.get('title', ''), '\n'.join(f['emails']), '\n'.join(f['phones']),
                              '\n'.join(f['addresses']), f.get('birthday', ''), '\n'.join(f['urls']),
                              f.get('note', ''), f.get('categories', ''), 'Yes' if f['list'] else '', photo,
                              f.get('uid') or uid, os.path.basename(folder), relative))
        read.append(path)
    if counts:
        logfunc('Evolution Contacts: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxEvolutionEvents(context):
    data_headers = ('Start', 'End', 'Time Zone', 'Summary', 'Location', 'Description', 'Repeats',
                    ('Created', 'datetime'), ('Last Modified', 'datetime'), 'UID', 'Calendar', 'Source File')
    data_list, read, counts = [], [], Counter()
    for path in _ics_files(context, 'calendar.ics'):
        text = _read_text(path, counts)
        if text is None:
            continue
        relative = context.get_relative_path(path)
        events = components(text, 'VEVENT')
        for props in events:
            start = _first(props, 'DTSTART')
            end = _first(props, 'DTEND')
            start_text, start_zone = ical_time(start[2], start[1]) if start else ('', '')
            end_text, end_zone = ical_time(end[2], end[1]) if end else ('', '')
            zones = [z for z in dict.fromkeys((start_zone, end_zone)) if z]
            rrule = _first(props, 'RRULE')
            data_list.append((start_text, end_text, '\n'.join(zones), prop_text(props, 'SUMMARY'),
                              prop_text(props, 'LOCATION'), prop_text(props, 'DESCRIPTION'), rrule[2] if rrule else '',
                              _stamp(props, 'CREATED', counts), _stamp(props, 'LAST-MODIFIED', counts),
                              prop_text(props, 'UID'), os.path.basename(os.path.dirname(path)), relative))
        if events:
            read.append(path)
    if counts:
        logfunc('Evolution Calendar Events: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def linuxEvolutionTasks(context):
    data_headers = ('Due', 'Time Zone', 'Summary', 'Description', 'Status', 'Priority', 'Percent Complete',
                    ('Completed', 'datetime'), ('Created', 'datetime'), ('Last Modified', 'datetime'), 'UID',
                    'Task List', 'Source File')
    data_list, read, counts = [], [], Counter()
    for path in _ics_files(context, 'tasks.ics'):
        text = _read_text(path, counts)
        if text is None:
            continue
        relative = context.get_relative_path(path)
        tasks = components(text, 'VTODO')
        for props in tasks:
            due = _first(props, 'DUE')
            due_text, due_zone = ical_time(due[2], due[1]) if due else ('', '')
            data_list.append((due_text, due_zone, prop_text(props, 'SUMMARY'), prop_text(props, 'DESCRIPTION'),
                              prop_text(props, 'STATUS'), prop_text(props, 'PRIORITY'), prop_text(props, 'PERCENT-COMPLETE'),
                              _stamp(props, 'COMPLETED', counts), _stamp(props, 'CREATED', counts),
                              _stamp(props, 'LAST-MODIFIED', counts), prop_text(props, 'UID'),
                              os.path.basename(os.path.dirname(path)), relative))
        if tasks:
            read.append(path)
    if counts:
        logfunc('Evolution Tasks: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
