"""Files and other resources in the recently used list GTK keeps (recently-used.xbel), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxRecentFiles": {
        "name": "Recently Used Files (GTK)",
        "description": "Files and other items in the recently used list GTK keeps (recently-used.xbel), one row for "
                       "each application listed with an item, with when it last registered the item and when the "
                       "item entered the list.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-28",
        "last_update_date": "2026-09-28",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads each recently used list GTK keeps, a recently-used.xbel file, in both places GTK has kept "
                 "it. Of the GTK releases checked, 2.10.0, 2.12.0, 2.14.0, 2.16.0, 2.18.0, 2.20.0, 2.21.0 to 2.21.2, "
                 "2.22.0 and 2.23.0 keep it as .recently-used.xbel in the home folder (2.22.0, "
                 "https://github.com/GNOME/gtk/blob/6c95f0475f1e120e748e903089fe202c1a509334/gtk/gtkrecentmanager.c#L45 "
                 "and "
                 "https://github.com/GNOME/gtk/blob/6c95f0475f1e120e748e903089fe202c1a509334/gtk/gtkrecentmanager.c#L511-L513), "
                 "and 2.23.2, 2.23.3, 2.24.0, 2.24.33, 3.0.0, 3.2.0, 3.4.0, 3.24.52 and 4.22.4 as recently-used.xbel "
                 "in the user's data folder (2.23.2, "
                 "https://github.com/GNOME/gtk/blob/e01ae1ee12e429f6df2d13f8415d22156786bfda/gtk/gtkrecentmanager.c#L485-L490; "
                 "3.24.52, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L579-L581; "
                 "4.22.4, "
                 "https://github.com/GNOME/gtk/blob/7f99ab1a26408b6499a18f353f081e3c0598ea5c/gtk/gtkrecentmanager.c#L567-L569), "
                 "which is .local/share in the home folder when $XDG_DATA_HOME is not set or is empty (Base "
                 "Directory specification, "
                 "https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L136-139). "
                 "GTK 2.24.33 moves an older file it finds to the newer place, or merges it into a list already "
                 "there and deletes it "
                 "(https://github.com/GNOME/gtk/blob/68631945733158f164427db84f01301d7e875763/gtk/gtkrecentmanager.c#L509-L628); "
                 "in a merge the newer list's copy of an item both lists hold is kept, and an item copied over is "
                 "created anew, with the time of the merge as its Added and Modified, while its applications keep "
                 "their counts and times "
                 "(https://github.com/GNOME/gtk/blob/68631945733158f164427db84f01301d7e875763/gtk/gtkrecentmanager.c#L562-L608). "
                 "A list kept in another data folder is not read. It gives one row per application entry of each "
                 "bookmark, in file order, and one row with blank application fields for a bookmark with none; "
                 "Source File is the list a row comes from, and the report's located-at line names the lists that "
                 "held a row. GTK 3.24.52 and 4.22.4 read and write the list through GLib (3.24.52, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L682 "
                 "and "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L504; "
                 "4.22.4, "
                 "https://github.com/GNOME/gtk/blob/7f99ab1a26408b6499a18f353f081e3c0598ea5c/gtk/gtkrecentmanager.c#L670 "
                 "and "
                 "https://github.com/GNOME/gtk/blob/7f99ab1a26408b6499a18f353f081e3c0598ea5c/gtk/gtkrecentmanager.c#L485), "
                 "and GLib 2.88.0 writes the bookmarks in the order they were first added (glib/gbookmarkfile.c, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L2125 "
                 "and "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L1641-L1656), "
                 "each bookmark's applications in the order they first registered it "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L3604 "
                 "and "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L461-L476), "
                 "and no bookmark without an application "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L609-L616). "
                 "Each bookmark element directly in the xbel element is read: its href, added and modified "
                 "attributes, its title and desc elements, and, in its metadata element whose owner is "
                 "http://freedesktop.org, the mime-type, groups, private and application elements, as GLib names "
                 "them "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L56-L111). "
                 "GLib refuses a whole file holding an element it does not expect "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L1211-L1409); "
                 "this artifact passes over any other element, and counts in the run log, without reporting, a "
                 "bookmark element that is not directly in the xbel element, a file that is not XML with an xbel "
                 "root element and a file that cannot be read. Last Registered (UTC), Added (UTC) and Modified (UTC) "
                 "are converted to UTC with the Z or UTC offset each time carries; GLib 2.88.0 writes a time in ISO "
                 "8601 with Z for UTC and with microseconds when it is not a whole second (glib/gdatetime.c, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gdatetime.c#L3843-L3878), "
                 "and GLib 2.64.0 wrote whole seconds "
                 "(https://github.com/GNOME/glib/blob/369626e3105d688afaa316d89d34e8927a8a0171/glib/gbookmarkfile.c#L1606-L1613). "
                 "A time in another form, a time with no zone among them, is left blank and counted in the run log. "
                 "When an application element has no modified attribute, Last Registered is read from its older "
                 "timestamp attribute as seconds since 1970, as GLib reads it "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L955-L969). "
                 "Where a time is missing, GLib's reader puts in the current time "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L2131-L2138, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L965-L968), "
                 "so a program reading the list through GLib can show a time the file does not hold; this artifact "
                 "leaves it blank. Added is set when GLib creates the item, in every GLib release checked (2.20.0, "
                 "2.26.0, 2.40.0, each even-numbered release from 2.42.0 to 2.64.0, 2.64.6, 2.66.0, 2.68.0, 2.72.0, "
                 "2.76.0, 2.80.0, 2.84.0, 2.86.0 and 2.88.0), and no GTK release checked calls GLib to set Added or "
                 "Modified itself. It does not report the bookmark's visited attribute, which neither a GTK nor a "
                 "GLib release checked sets to the time of a use: the GLib releases from 2.66.0 to 2.88.0 set it "
                 "when they create the item "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L2131-L2138), "
                 "and it matched Added to within a microsecond on all 6 bookmarks of ubuntu2604_arm64_recent; the "
                 "ones from 2.62.0 to 2.64.6 left it unset and wrote an unset time as 1969-12-31T23:59:59Z (2.64.0, "
                 "https://github.com/GNOME/glib/blob/369626e3105d688afaa316d89d34e8927a8a0171/glib/gbookmarkfile.c#L516, "
                 "https://github.com/GNOME/glib/blob/369626e3105d688afaa316d89d34e8927a8a0171/glib/gbookmarkfile.c#L560 "
                 "and "
                 "https://github.com/GNOME/glib/blob/369626e3105d688afaa316d89d34e8927a8a0171/glib/gbookmarkfile.c#L1606-L1613); "
                 "and the ones from 2.20.0 to 2.60.0 left it unset and wrote it as the time of each write of the "
                 "list (2.40.0, "
                 "https://github.com/GNOME/glib/blob/3f8f040349ae821854bccb2c3535a58b0ee66803/glib/gbookmarkfile.c#L515, "
                 "https://github.com/GNOME/glib/blob/3f8f040349ae821854bccb2c3535a58b0ee66803/glib/gbookmarkfile.c#L559 "
                 "and "
                 "https://github.com/GNOME/glib/blob/3f8f040349ae821854bccb2c3535a58b0ee66803/glib/gbookmarkfile.c#L1537-L1550). "
                 "Modified is set to the current time whenever GLib changes the item's title, description, MIME "
                 "type, groups, private mark or applications (bookmark_item_touch_modified, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L597-L601, "
                 "which each of those setters calls), the last change of a GTK registration being the private mark "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L1006-L1007; "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L2541-L2542). "
                 "Last Registered is the time of the application's last registration of the item and Registrations "
                 "its count attribute, the number of its registrations, as GLib describes them "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L3510-L3511); "
                 "GLib stamps the time and adds one to the count at each registration "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L3330-L3342, "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L3619-L3625). "
                 "Application is the name it registered under and Command the command it gave, as stored, which GLib "
                 "writes shell-quoted "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L3627-L3631); "
                 "for a registration by URI alone GTK gives the application name and the program name followed by %u "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L808-L809). "
                 "GTK sets MIME Type at every registration, from the content type GIO gives the file for a "
                 "registration by URI alone "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L784-L811) "
                 "or as the application gives it "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L988), "
                 "so it is the last registration's. Title and Description are written only when an application gives "
                 "them and Groups gains any group an application gives "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L982-L996); "
                 "the groups are joined here with a comma and a space. Private is yes when the item carries GLib's "
                 "private mark "
                 "(https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L509-L514), "
                 "which GTK sets from each registration "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L1006-L1007) "
                 "and clears at a registration by URI alone "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L811). "
                 "File is the path a file URI with no host or the host localhost names, with its escapes decoded as "
                 "UTF-8 and a sequence that is not UTF-8 shown as the replacement character, blank for any other "
                 "URI; URI is the href as stored. The list names items, not their state: an item can name a file "
                 "that no longer exists. GTK 3.24.52 keeps at most 1,000 items and, past that, removes the items "
                 "first added, whatever their later use "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L117, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L467-L499, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L1470-L1496; "
                 "https://github.com/GNOME/glib/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gbookmarkfile.c#L2230-L2238), "
                 "a limit GTK 4.22.4 shares "
                 "(https://github.com/GNOME/gtk/blob/7f99ab1a26408b6499a18f353f081e3c0598ea5c/gtk/gtkrecentmanager.c#L109); "
                 "with its gtk-recent-files-max-age setting above 0 it also removes items whose Modified is more "
                 "days old than that setting "
                 "(https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtkrecentmanager.c#L1439-L1468), "
                 "whose own default is 30 (gtk/gtksettings.c, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gtk/gtksettings.c#L1127-L1133). "
                 "On a GNOME Wayland session GTK takes that setting from GNOME's recent-files-max-age (GTK 3.24.52, "
                 "gdk/wayland/gdkscreen-wayland.c, "
                 "https://github.com/GNOME/gtk/blob/6a0b360d473f7c546314738c0c8dd9829eb9d3c2/gdk/wayland/gdkscreen-wayland.c#L546-L547; "
                 "GTK 4.22.4, gdk/wayland/gdksettings-wayland.c, "
                 "https://github.com/GNOME/gtk/blob/7f99ab1a26408b6499a18f353f081e3c0598ea5c/gdk/wayland/gdksettings-wayland.c#L287-L288), "
                 "whose default, -1, keeps items indefinitely (gsettings-desktop-schemas 50.0, "
                 "https://github.com/GNOME/gsettings-desktop-schemas/blob/0b3ea8e1a25ecfc33e9f6af1b1db93c4032b84e6/schemas/org.gnome.desktop.privacy.gschema.xml.in#L39-L45). "
                 "The removal of the first-added item was measured on the lab VM with a scratch list: at its 1,001st "
                 "item GTK 3.24.52 removed the first item, although that item had just been registered again. On "
                 "ubuntu2604_arm64_recent, captured from a VM running GTK 3.24.52 and 4.22.4 and GLib 2.88.0 with "
                 "GNOME's recent-files-max-age at its default, the 8 rows are the 8 application entries of the 6 "
                 "bookmarks that three test applications registered there through GTK, and each row equals GLib "
                 "2.88.0's own reading of the same file, field by field and in order, with the command expanded as "
                 "GLib expands it and File as GLib's own conversion of the URI. The bookmarks are in the order the "
                 "steps first registered them and each bookmark's rows in the order its applications first "
                 "registered it; each Last Registered fell inside the logged time of the step that made it; and "
                 "Modified was 1 microsecond after the latest Last Registered on every bookmark. alpha notes.txt has "
                 "a row for each of the two applications that registered it, the one that did so twice with "
                 "Registrations 2 and its second registration's time; delta-deleted.txt is still listed although it "
                 "was removed after its registration and before five later writes of the list; the web address has a "
                 "blank File; and epsilon.txt kept the title and group an application gave it but lost its private "
                 "mark when a second application registered it by URI alone, while gamma.png kept its. "
                 "ubuntu2604_arm64_triage, a capture of the same VM before those tests, holds the list with no "
                 "bookmark.",
        "paths": ('*/.local/share/recently-used.xbel', '*/.recently-used.xbel'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 8 rows",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (its list holds no bookmark)",
        },
    },
}

import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

from scripts.ilapfuncs import artifact_processor, logfunc

_BOOKMARK = '{http://www.freedesktop.org/standards/desktop-bookmarks}'
_MIME = '{http://www.freedesktop.org/standards/shared-mime-info}'
_OWNER = 'http://freedesktop.org'
_TIME = re.compile(r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}(?::?\d{2})?)')
_SECONDS = re.compile(r'-?\d+')


def xbel_time(value):
    """The UTC time for an ISO 8601 time as GLib writes one: a date, T, a time with an optional fraction of a
    second, then Z or a UTC offset. None for anything else, a time with no zone among them."""
    match = _TIME.fullmatch(value or '')
    if not match:
        return None
    year, month, day, hour, minute, second, fraction, zone = match.groups()
    try:
        when = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second),
                        int((fraction or '0')[:6].ljust(6, '0')), tzinfo=timezone.utc)
        if zone != 'Z':
            digits = zone[1:].replace(':', '')
            offset = timedelta(hours=int(digits[:2]), minutes=int(digits[2:] or 0))
            when = when - offset if zone[0] == '+' else when + offset
    except (ValueError, OverflowError):
        return None
    return when


def seconds_time(value):
    """The UTC time for a count of seconds since 1970, the older timestamp attribute, or None."""
    if not _SECONDS.fullmatch(value or ''):
        return None
    try:
        return datetime.fromtimestamp(int(value), timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None


def local_path(uri):
    """The path a file URI names, with its escapes decoded as UTF-8, for a URI with no host or the host localhost;
    '' for any other URI."""
    if uri[:5].lower() != 'file:':
        return ''
    rest = uri[5:]
    if rest.startswith('//'):
        host, slash, path = rest[2:].partition('/')
        if not slash or host.lower() not in ('', 'localhost'):
            return ''
        rest = '/' + path
    elif not rest.startswith('/'):
        return ''
    return unquote(rest, errors='replace')


def recent_rows(data, counts):
    """Rows (last registered, added, modified, file, URI, title, description, MIME type, application, command,
    registrations, groups, private) for the text of a recently-used.xbel file: one per application entry of each bookmark
    element of the xbel element, in file order, and one with blank application fields for a bookmark with none.
    None when the text is not XML with an xbel root element."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return None
    if root.tag != 'xbel':
        return None
    bookmarks = root.findall('bookmark')
    nested = len(root.findall('.//bookmark')) - len(bookmarks)
    if nested:
        counts['bookmark elements not directly in the xbel element, not reported'] += nested
    rows = []
    for bookmark in bookmarks:
        times = []
        for key in ('added', 'modified'):
            stored = bookmark.get(key)
            when = xbel_time(stored)
            if stored is not None and when is None:
                counts[f'bookmark {key} times in another form, left blank'] += 1
            times.append(when or '')
        uri = bookmark.get('href', '')
        titles = bookmark.findall('title')
        descriptions = bookmark.findall('desc')
        title = (titles[-1].text or '') if titles else ''
        description = (descriptions[-1].text or '') if descriptions else ''
        mime_type, groups, applications, private = '', [], [], False
        for metadata in bookmark.findall('info/metadata'):
            if metadata.get('owner') != _OWNER:
                continue
            for mime in metadata.findall(_MIME + 'mime-type'):
                mime_type = mime.get('type', '')
            groups.extend(group.text or '' for group in metadata.findall(f'{_BOOKMARK}groups/{_BOOKMARK}group'))
            applications.extend(metadata.findall(f'{_BOOKMARK}applications/{_BOOKMARK}application'))
            private = private or metadata.find(_BOOKMARK + 'private') is not None
        shared = (local_path(uri), uri, title, description, mime_type)
        tail = (', '.join(groups), 'yes' if private else 'no')
        if not applications:
            rows.append(('', *times, *shared, '', '', '', *tail))
            continue
        for application in applications:
            stored, legacy = application.get('modified'), application.get('timestamp')
            registered = xbel_time(stored) if stored is not None else seconds_time(legacy)
            if (stored is not None or legacy is not None) and registered is None:
                counts['application times in another form, left blank'] += 1
            rows.append((registered or '', *times, *shared, application.get('name', ''), application.get('exec', ''),
                         application.get('count', ''), *tail))
    return rows


@artifact_processor
def linuxRecentFiles(context):
    data_headers = (('Last Registered (UTC)', 'datetime'), ('Added (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'),
                    'File', 'URI', 'Title', 'Description', 'MIME Type', 'Application', 'Command', 'Registrations',
                    'Groups', 'Private', 'Source File')
    data_list = []
    read = []
    problems = Counter()
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        rows = recent_rows(data, problems)
        if rows is None:
            problems['files that are not XML with an xbel root element, not reported'] += 1
            continue
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if problems:
        logfunc('Recently Used Files (GTK): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
