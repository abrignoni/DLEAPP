"""Shared reading for the Outlook PST and OST artifacts in scripts/artifacts/outlookPst.py
and scripts/artifacts/outlookAutocomplete.py.

Files are read with the vendored pstprobe (scripts/vendor/pstprobe.py). Property IDs and
names are those of Microsoft [MS-OXPROPS] v20250520; what each property means, and the
values an enumerated one takes, are cited beside it from the Exchange protocol
documents ([MS-OXCMSG], [MS-OXOMSG], [MS-OXOCNTC], [MS-OXOTASK], [MS-OXONOTE],
[MS-OXOJRNL], [MS-OXCDATA], release v20250520, [MS-PST] v20250218 and [MS-OXOCAL] v20250819).
The autocomplete stream follows Microsoft Learn's "Autocomplete Stream" page.
"""

import datetime
import hashlib
import struct
import html.parser
import os
from collections import Counter

from scripts import ilapfuncs
from scripts.ilapfuncs import logfunc
from scripts.vendor import pstprobe as P

# Property sets ([MS-OXPROPS] 1.3.2)
PSETID_APPOINTMENT = '00062002-0000-0000-c000-000000000046'
PSETID_TASK = '00062003-0000-0000-c000-000000000046'
PSETID_ADDRESS = '00062004-0000-0000-c000-000000000046'
PSETID_LOG = '0006200a-0000-0000-c000-000000000046'
PSETID_NOTE = '0006200e-0000-0000-c000-000000000046'

# Tagged properties ([MS-OXPROPS] names)
TAG_MESSAGE_CLASS = 0x001A           # PidTagMessageClass
TAG_SUBJECT = 0x0037                 # PidTagSubject
TAG_TRANSPORT_HEADERS = 0x007D       # PidTagTransportMessageHeaders
TAG_CLIENT_SUBMIT_TIME = 0x0039      # PidTagClientSubmitTime
TAG_SENT_REPRESENTING_NAME = 0x0042  # PidTagSentRepresentingName
TAG_SENDER_NAME = 0x0C1A             # PidTagSenderName
TAG_SENDER_EMAIL = 0x0C1F            # PidTagSenderEmailAddress
TAG_RECIPIENT_TYPE = 0x0C15          # PidTagRecipientType
TAG_DELIVERY_TIME = 0x0E06           # PidTagMessageDeliveryTime
TAG_MESSAGE_FLAGS = 0x0E07           # PidTagMessageFlags
TAG_INTERNET_MESSAGE_ID = 0x1035     # PidTagInternetMessageId
TAG_DISPLAY_NAME = 0x3001            # PidTagDisplayName
TAG_EMAIL_ADDRESS = 0x3003           # PidTagEmailAddress
TAG_CREATION_TIME = 0x3007           # PidTagCreationTime
TAG_MODIFIED_TIME = 0x3008           # PidTagLastModificationTime
TAG_SMTP_ADDRESS = 0x39FE            # PidTagSmtpAddress
TAG_GIVEN_NAME = 0x3A06              # PidTagGivenName
TAG_BUSINESS_PHONE = 0x3A08          # PidTagBusinessTelephoneNumber
TAG_HOME_PHONE = 0x3A09              # PidTagHomeTelephoneNumber
TAG_SURNAME = 0x3A11                 # PidTagSurname
TAG_COMPANY = 0x3A16                 # PidTagCompanyName
TAG_TITLE = 0x3A17                   # PidTagTitle
TAG_MOBILE_PHONE = 0x3A1C            # PidTagMobileTelephoneNumber
TAG_BIRTHDAY = 0x3A42                # PidTagBirthday
TAG_SENDER_SMTP = 0x5D01             # PidTagSenderSmtpAddress
TAG_ATTACH_MIME = 0x370E             # PidTagAttachMimeTag

# [MS-OXCMSG] 2.2.1.6 PidTagMessageFlags
MF_READ = 0x00000001
MF_UNSENT = 0x00000008

# [MS-OXCMSG] 2.2.2.9 PidTagAttachMethod: afStorage keeps the attachment as an object in an
# application-specific format (PidTagAttachDataObject), not as an attached item
AF_STORAGE = 0x00000006

# [MS-OXOMSG] 2.2.3.1 PidTagRecipientType: the low values; 0x10000000 and 0x80000000 are
# resend flags that can be ORed in.
RECIPIENT_TYPES = {1: 'To', 2: 'Cc', 3: 'Bcc'}

# The item classes each artifact reports. [MS-OXCMSG] 2.2.1.3: matching against
# PidTagMessageClass is case-insensitive, and the value is read in groups separated by
# periods, so a class belongs to a prefix when it equals it or continues it after a period.
KIND_PREFIXES = (
    ('contact', ('IPM.Contact', 'IPM.DistList')),
    ('appointment', ('IPM.Appointment',)),
    ('task', ('IPM.Task',)),
    ('note', ('IPM.StickyNote',)),
    ('journal', ('IPM.Activity',)),
)
# Classes no artifact reports, named in the notes.
EXCLUDED_PREFIXES = ('IPM.Microsoft.ScheduleData.FreeBusy', 'IPM.AbchPerson', 'IPM.Network')

PST_PATHS = ('*.[pP][sS][tT]', '*.[oO][sS][tT]')


def has_prefix(message_class, prefix):
    value, prefix = message_class.lower(), prefix.lower()
    return value == prefix or value.startswith(prefix + '.')


def kind_is_list(message_class):
    return isinstance(message_class, str) and has_prefix(message_class, 'IPM.DistList')


def kind_of(message_class):
    """The artifact an item class belongs to: contact, appointment, task, note or journal
    by prefix, None for an excluded class, and email for every other class, so that a class
    nobody listed is reported under Emails with its class rather than dropped."""
    if not isinstance(message_class, str) or not message_class:
        return 'email'
    for kind, prefixes in KIND_PREFIXES:
        if any(has_prefix(message_class, p) for p in prefixes):
            return kind
    if any(has_prefix(message_class, p) for p in EXCLUDED_PREFIXES):
        return None
    return 'email'


class Reader:
    """Reads values of one item and counts what could not be read."""

    def __init__(self, counts):
        self.counts = counts

    def get(self, pc, pid):
        try:
            return pc.get(pid)
        except P.DAMAGE_ERRORS:
            self.counts['values that could not be read, left blank'] += 1
            return None

    def named(self, message, guid, lid):
        pid = message.pst.named_property_id(guid, lid)
        return None if pid is None else self.get(message.pc, pid)

    def text(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value.rstrip('\x00')
        if isinstance(value, (bytes, bytearray)):
            # a string property that did not decode is shown as its stored bytes
            self.counts['string values shown as hexadecimal because they did not decode'] += 1
            return bytes(value).hex()
        if isinstance(value, (list, tuple)):
            return '; '.join(self.text(v) for v in value)
        return str(value)

    def time(self, value, no_date_sentinel=False):
        """A PtypTime value as decoded, or ''. With no_date_sentinel, 4501-01-01, the value
        0x5AE980E0 minutes that [MS-OXOTASK] 2.2.2.2.4 and 2.2.2.2.5 give for "no date",
        is blank too."""
        if value is None or not hasattr(value, 'year'):
            return ''
        if no_date_sentinel and value.year == 4501:
            self.counts['task dates holding the no-date value, left blank'] += 1
            return ''
        return value

    @staticmethod
    def flag(value):
        if value is None:
            return ''
        return 'Yes' if value else 'No'


class _Visible(html.parser.HTMLParser):
    HIDDEN = ('head', 'style', 'script', 'title')

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self.hidden += 1
        elif tag in ('br', 'p', 'div', 'tr', 'li'):
            self.out.append('\n')

    def handle_endtag(self, tag):
        if tag in self.HIDDEN and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.out.append(data)


def visible_text(markup):
    parser = _Visible()
    parser.feed(markup)
    parser.close()
    lines = [line.strip() for line in ''.join(parser.out).splitlines()]
    return '\n'.join(line for line in lines if line)


TAG_INTERNET_CODEPAGE = 0x3FDE      # PidTagInternetCodepage


def decode_html(message, data, reader):
    """PidTagBodyHtml stored as bytes, decoded with PidTagInternetCodepage, the code page of
    the body ([MS-OXPROPS] 2.747), when it names one Python has and the bytes decode in it;
    else as UTF-8; else in that code page (or UTF-8) with undecodable bytes replaced."""
    data = data.split(b'\x00', 1)[0]
    codepage = reader.get(message.pc, TAG_INTERNET_CODEPAGE)
    codec = P.codepage_codec(codepage) if isinstance(codepage, int) and codepage > 0 else None
    for name in (codec, 'utf-8'):
        if name:
            try:
                return data.decode(name)
            except (UnicodeDecodeError, LookupError):
                continue
    reader.counts['HTML bodies with bytes their code page does not decode, replaced'] += 1
    return data.decode(codec or 'utf-8', 'replace')


def body_text(message, reader):
    """(text, source): PidTagBody when stored; else the text the compressed RTF body
    (PidTagRtfCompressed) holds or encapsulates; else the visible text of PidTagBodyHtml."""
    try:
        body = message.body()
    except P.DAMAGE_ERRORS:
        reader.counts['bodies that could not be read'] += 1
        body = None
    if isinstance(body, str) and body.strip('\x00').strip():
        return body.rstrip('\x00'), 'PidTagBody'
    try:
        kind, text = message.rtf_text()
    except P.DAMAGE_ERRORS:
        reader.counts['compressed RTF bodies that could not be read'] += 1
        kind, text = None, None
    if kind == 'html' and text:
        return visible_text(text), 'PidTagRtfCompressed (HTML)'
    if kind and text and text.strip():
        return text, 'PidTagRtfCompressed'
    try:
        markup = message.html_body()
    except P.DAMAGE_ERRORS:
        reader.counts['HTML bodies that could not be read'] += 1
        markup = None
    if isinstance(markup, (bytes, bytearray)):
        markup = decode_html(message, bytes(markup), reader)
    if isinstance(markup, str) and markup.strip():
        return visible_text(markup), 'PidTagBodyHtml'
    return '', ''


def file_attachments(message, reader, chain=None, depth=0):
    """(within, attachment) for every file attachment of the item and of the items attached
    to it, to depth 8; within names the attached item for a nested one."""
    try:
        attachments = message.attachments()
    except P.DAMAGE_ERRORS:
        reader.counts['attachment tables that could not be read'] += 1
        return
    for a in attachments:
        try:
            method = a.method
            if a.is_embedded_message and method != AF_STORAGE:
                inner = a.embedded_message()
                if inner is not None and depth < 8:
                    name = reader.text(inner.subject) or '(attached item)'
                    yield from file_attachments(inner, reader, (chain + ' > ' if chain else '') + name, depth + 1)
                continue
        except P.DAMAGE_ERRORS:
            reader.counts['attached items that could not be read'] += 1
            continue
        if method == AF_STORAGE:
            reader.counts['attachments in an application-specific format (afStorage), listed without data'] += 1
        yield chain or '', a


def attachment_names(message, reader):
    """Every attachment's stored name, attached items by their subject."""
    names = []
    try:
        attachments = message.attachments()
    except P.DAMAGE_ERRORS:
        return ''
    for a in attachments:
        try:
            if a.is_embedded_message and a.method != AF_STORAGE:
                inner = a.embedded_message()
                subject = reader.text(inner.subject) if inner is not None else ''
                names.append('[attached item] ' + subject)
            else:
                names.append(reader.text(a.filename))
        except P.DAMAGE_ERRORS:
            names.append('[could not be read]')
    return '\n'.join(names)


def check_in_attachment(source, attachment, reader):
    """The media reference of a file attachment's data, or '' when it holds none."""
    try:
        data = attachment.data()
    except P.DAMAGE_ERRORS:
        reader.counts['attachment data that could not be read'] += 1
        return ''
    if not data:
        return ''
    try:
        # called through the module so a test harness that replaces it is used here too
        ref = ilapfuncs.check_in_embedded_media(source, data, reader.text(attachment.filename))
    except P.DAMAGE_ERRORS as exc:
        # a failure of the report's media store, not damage in the file: let it stop the artifact
        raise MediaCheckInError(f'could not check in an attachment: {exc}') from exc
    return ref or ''


class MediaCheckInError(Exception):
    """The report could not store an attachment. Not one of pstprobe's damage errors, so the
    per-item handling in read_items does not count it as an unreadable item."""


def attachment_media(source, message, reader):
    refs = [check_in_attachment(source, a, reader) for _within, a in file_attachments(message, reader)]
    return [r for r in refs if r] or ''


def recipients(message, reader):
    """{'To': [...], 'Cc': [...], 'Bcc': [...]} as "name <address>" strings, in table order.
    The address is PidTagSmtpAddress when stored, else PidTagEmailAddress."""
    out = {'To': [], 'Cc': [], 'Bcc': []}
    try:
        rows = message.recipients()
    except P.DAMAGE_ERRORS:
        reader.counts['recipient tables that could not be read'] += 1
        return out
    for row in rows:
        kind = row.get(TAG_RECIPIENT_TYPE)
        label = RECIPIENT_TYPES.get(kind & 0x0FFFFFFF) if isinstance(kind, int) else None
        if label is None:
            reader.counts['recipients of another type, not reported'] += 1
            continue
        values = [row.get(p) for p in (TAG_DISPLAY_NAME, TAG_SMTP_ADDRESS, TAG_EMAIL_ADDRESS)]
        name, smtp, address = ('' if isinstance(v, Exception) else reader.text(v) for v in values)
        address = smtp or address
        out[label].append(f'{name} <{address}>' if name and address and name != address else (name or address))
    return out


def _same_file_key(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


_FIRMLINK = 'System/Volumes/Data/'


def unique_files(files_found, relative, counts):
    """The PST and OST files found, with a byte-identical second copy of a file (the same
    store reached by two paths in one extraction) left out and counted. Files are taken in
    order of their path in the extraction, a copy under System/Volumes/Data/ after the one
    under Users/, so the Users/ copy is the one kept. Only files of equal size are hashed."""
    paths = sorted({str(p) for p in files_found if os.path.isfile(str(p))},
                   key=lambda p: (_FIRMLINK in relative(p).replace('\\', '/'), relative(p)))
    by_size, digests = {}, {}
    for path in paths:
        by_size.setdefault(os.path.getsize(path), []).append(path)
    keep = []
    for path in paths:
        group = by_size[os.path.getsize(path)]
        if len(group) > 1:
            for p in group:
                if p not in digests:
                    digests[p] = _same_file_key(p)
            if any(digests[p] == digests[path] for p in group[:group.index(path)]):
                counts['byte-identical copies of a file already read, not read again'] += 1
                continue
        keep.append(path)
    return keep


_INDEX = {}


def _folders(pst, counts):
    """Every folder of the file, walking the folder tree from the root, each once."""
    seen = set()
    pending = [(P.NID_ROOT_FOLDER, '')]
    while pending:
        nid, parent = pending.pop(0)
        if nid in seen:
            counts['folders listed again by another folder, read once'] += 1
            continue
        seen.add(nid)
        try:
            folder = pst.folder(nid, parent)
        except P.DAMAGE_ERRORS:
            counts['folders that could not be read'] += 1
            continue
        if folder is None:
            continue
        try:
            pending.extend((sub, folder.path) for sub in folder.subfolder_nids())
        except P.DAMAGE_ERRORS:
            counts['folder hierarchy tables that could not be read'] += 1
        yield folder


def associated_items(pst, message_class, counts):
    """(folder path, item) for every folder-associated item whose PidTagMessageClass is
    message_class, compared without regard to case, in every folder that is not a search
    folder."""
    for folder in _folders(pst, counts):
        if folder.is_search_folder:
            continue
        try:
            nids = folder.assoc_message_nids()
        except P.DAMAGE_ERRORS:
            counts['folder-associated contents tables that could not be read'] += 1
            continue
        for nid in nids:
            try:
                item = pst.message(nid)
            except P.DAMAGE_ERRORS:
                counts['folder-associated items that could not be read'] += 1
                continue
            if item is None:
                counts['folder-associated items listed with no item node'] += 1
                continue
            value = item.message_class
            if isinstance(value, str) and value.lower() == message_class.lower():
                yield folder.path, item


def is_pst_name(path):
    return os.path.splitext(str(path))[1].lower() in ('.pst', '.ost')


def _index(pst, path, counts):
    """(folder path, item NID, class) for every item listed in a normal folder's contents
    table, walking the folder tree from the root. Search folders, whose results are items
    of other folders, and folder-associated contents are not listed. The class is read from
    the contents table row, else from the item."""
    stat = os.stat(path)
    key = (os.path.realpath(path), stat.st_size, stat.st_mtime_ns)
    if key in _INDEX:
        return _INDEX[key]
    items = []
    for folder in _folders(pst, counts):
        if folder.is_search_folder:
            continue
        try:
            table = folder.contents_table()
            rows = table.row_index if table is not None else []
        except P.DAMAGE_ERRORS:
            counts['contents tables that could not be read'] += 1
            continue
        for row_id, n in rows:
            message_class = None
            try:
                message_class = table.row(row_id, n).get(TAG_MESSAGE_CLASS)
            except P.DAMAGE_ERRORS:
                pass
            if not isinstance(message_class, str):
                try:
                    item = pst.message(row_id)
                    message_class = item.message_class if item is not None else None
                except P.DAMAGE_ERRORS:
                    message_class = None
            items.append((folder.path, row_id, message_class))
    _INDEX[key] = items
    return items


def read_items(context, kinds, label, build_row):
    """Rows for one artifact: build_row(message, folder path, message class, source, relative
    source, reader) for every item whose class belongs to one of kinds, over every PST and OST
    file found."""
    rows, read, counts = [], [], Counter()
    reader = Reader(counts)
    for path in unique_files(context.get_files_found(), context.get_relative_path, counts):
        relative = context.get_relative_path(path)
        try:
            pst = P.open_pst(path)
        except (OSError,) + P.DAMAGE_ERRORS as exc:
            counts['files that could not be opened as PST or OST'] += 1
            logfunc(f'{label}: {relative} was not read: {exc}')
            read.append(path)
            continue
        with pst:
            if pst.file_size < pst.file_eof:
                counts['files shorter than their header records'] += 1
                logfunc(f'{label}: {relative} is {pst.file_size} bytes and its header records '
                        f'{pst.file_eof}; the rest is missing, not empty, and items stored there '
                        'cannot be read')
            for folder_path, nid, message_class in _index(pst, path, counts):
                if kind_of(message_class) not in kinds:
                    continue
                try:
                    message = pst.message(nid)
                    if message is None:
                        counts['items listed by a folder with no item node'] += 1
                        continue
                    rows.append(build_row(message, folder_path, reader.text(message_class), path, relative, reader))
                except P.DAMAGE_ERRORS as exc:
                    counts['items that could not be read'] += 1
                    if counts['items that could not be read'] <= 3:
                        logfunc(f'{label}: item 0x{nid:x} in {relative} could not be read: {exc}')
        read.append(path)
    if counts:
        logfunc(f'{label}: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return rows, '\n'.join(read)


# Autocomplete stream: Microsoft Learn, "Autocomplete Stream" (Outlook MAPI reference,
# https://learn.microsoft.com/en-us/office/client-developer/outlook/mapi/autocomplete-stream).
# It is held in PidTagRoamingBinary (0x7C09) of the folder-associated item of class
# IPM.Configuration.Autocomplete, and Outlook keeps a local copy in RoamCache as
# Stream_Autocomplete_*.dat; the layout below is the same in both.
TAG_ROAMING_BINARY = 0x7C09
AUTOCOMPLETE_CLASS = 'IPM.Configuration.Autocomplete'
AUTOCOMPLETE_MAJOR = 12          # "if the major version is different than 12, then this stream should not be read"
# property types whose value is the 8-byte union alone
_AC_STATIC = {0x0002, 0x0003, 0x0004, 0x0005, 0x000A, 0x000B, 0x0014, 0x0040}


class AutocompleteError(ValueError):
    """The stream does not follow the documented layout."""


def _filetime(raw):
    ticks = int.from_bytes(raw, 'little')
    if ticks == 0:
        return None
    try:
        return P.filetime_to_datetime(ticks)
    except (OverflowError, ValueError, AttributeError):
        return None


def parse_autocomplete(data):
    """(minor version, rows) of an autocomplete stream; each row is {property tag: value}.
    Raises AutocompleteError when the major version is not 12, a property type has no
    documented layout, or the rows, the extra information and the 8 trailing metadata bytes
    do not end exactly at the end of the stream."""

    end = len(data)
    if end < 16:
        raise AutocompleteError(f'{end} bytes, shorter than the 16-byte header')
    _meta, major, minor, count = struct.unpack_from('<4I', data, 0)
    if major != AUTOCOMPLETE_MAJOR:
        raise AutocompleteError(f'major version {major}, not {AUTOCOMPLETE_MAJOR}')
    pos = 16

    def take(n):
        nonlocal pos
        if n < 0 or pos + n > end:
            raise AutocompleteError(f'a field of {n} bytes at offset {pos} runs past the end ({end})')
        chunk = data[pos:pos + n]
        pos += n
        return chunk

    def u32():
        return struct.unpack('<I', take(4))[0]

    def counted():
        return take(u32())

    rows = []
    for _ in range(count):
        row = {}
        for _ in range(u32()):
            tag = u32()
            take(4)                      # reserved
            union = take(8)
            ptype = tag & 0xFFFF
            if ptype in _AC_STATIC:
                if ptype == 0x0002:
                    value = struct.unpack_from('<h', union)[0]
                elif ptype in (0x0003, 0x000A):
                    value = struct.unpack_from('<i', union)[0]
                elif ptype == 0x0004:
                    value = struct.unpack_from('<f', union)[0]
                elif ptype == 0x0005:
                    value = struct.unpack_from('<d', union)[0]
                elif ptype == 0x000B:
                    value = bool(struct.unpack_from('<h', union)[0])
                elif ptype == 0x0014:
                    value = struct.unpack_from('<q', union)[0]
                else:
                    value = _filetime(union)
            elif ptype == 0x001E:
                value = counted().split(b'\x00', 1)[0].decode('cp1252', 'replace')
            elif ptype == 0x001F:
                value = counted().decode('utf-16-le', 'replace').split('\x00', 1)[0]
            elif ptype == 0x0048:
                value = take(16)
            elif ptype == 0x0102:
                value = counted()
            elif ptype in (0x1102, 0x101E, 0x101F):
                items = [counted() for _ in range(u32())]
                if ptype == 0x101E:
                    value = [i.split(b'\x00', 1)[0].decode('cp1252', 'replace') for i in items]
                elif ptype == 0x101F:
                    value = [i.decode('utf-16-le', 'replace').split('\x00', 1)[0] for i in items]
                else:
                    value = items
            else:
                raise AutocompleteError(f'property 0x{tag:08x} has a type with no documented layout')
            row[tag] = value
        rows.append(row)
    extra = u32()
    take(extra)
    take(8)
    if pos != end:
        raise AutocompleteError(f'{end - pos} bytes after the trailing metadata')
    return minor, rows


# Distribution list members ([MS-OXOCNTC] 2.2.2.2) and the EntryIDs they hold ([MS-OXCDATA]
# 2.2.5.1 One-Off EntryID; [MS-OXOCNTC] 2.2.2.2.4.1.1 WrappedEntryId; [MS-PST] 2.4.3.2 the
# EntryID of an object in a PST)
LID_DL_ONE_OFF_MEMBERS = 0x8054      # PidLidDistributionListOneOffMembers
LID_DL_MEMBERS = 0x8055              # PidLidDistributionListMembers
LID_DL_STREAM = 0x8064               # PidLidDistributionListStream
ONE_OFF_UID = bytes.fromhex('812b1fa4bea310199d6e00dd010f5402')
WRAPPED_UID = bytes.fromhex('c091add3519dcf11a4a900aa0047faa4')
TAG_RECORD_KEY = 0x0FF9              # PidTagRecordKey
# [MS-OXOCNTC] 2.2.2.2.4.1.1: bits 0x70 of the Type of a wrapped contact name the address
_WRAPPED_CONTACT_ADDRESS = {4: 0x8083, 5: 0x8093, 6: 0x80A3}   # Email1..Email3 (PidLidEmailNEmailAddress)


def parse_one_off(data):
    """(display name, address type, email address) of a One-Off EntryID, or None when the
    bytes are not one. The 2-byte flags word after Version is read most significant byte
    first, as its bit diagram is drawn; U (0x0080) selects UTF-16 strings."""
    if len(data) < 24 or data[4:20] != ONE_OFF_UID:
        return None
    flags = int.from_bytes(data[22:24], 'big')
    unicode_ = bool(flags & 0x0080)
    pos, out = 24, []
    for _ in range(3):
        if unicode_:
            end = pos
            while end + 1 < len(data) and data[end:end + 2] != b'\x00\x00':
                end += 2
            if end + 1 >= len(data):
                return None
            out.append(data[pos:end].decode('utf-16-le', 'replace'))
            pos = end + 2
        else:
            end = data.find(b'\x00', pos)
            if end < 0:
                return None
            out.append(data[pos:end].decode('cp1252', 'replace'))
            pos = end + 1
    if pos != len(data):
        return None
    return tuple(out)


def _person(name, addrtype, address):
    shown = address if not addrtype or addrtype.upper() == 'SMTP' else f'{addrtype}:{address}'
    if name and shown and name != address:
        return f'{name} <{shown}>'
    return name or shown


def store_record_key(pst, reader):
    try:
        store = pst.message_store()
    except P.DAMAGE_ERRORS:
        return None
    value = reader.get(store, TAG_RECORD_KEY) if store is not None else None
    return bytes(value) if isinstance(value, (bytes, bytearray)) else None


def _member_entry(entry, pst, record_key, reader):
    """(text, NID of the item it names in this file or None, what to count when the text is
    used) for one PidLidDistributionListMembers entry."""
    entry = bytes(entry)
    one_off = parse_one_off(entry)
    if one_off:
        return _person(*one_off), None, None
    if len(entry) < 21 or entry[4:20] != WRAPPED_UID:
        return f'[entry {entry.hex()}]', None, 'distribution list member entries of another kind, shown as stored'
    kind, embedded = entry[20], entry[21:]
    one_off = parse_one_off(embedded)
    if one_off:
        # Outlook 16 writes Type 0xB5 here, which [MS-OXOCNTC] gives to a GAL mail user
        # (an Address Book EntryID); the embedded bytes carry the One-Off provider UID
        return _person(*one_off), None, None
    if len(embedded) == 24 and record_key and embedded[4:20] == record_key:
        nid = int.from_bytes(embedded[20:24], 'little')
        try:
            item = pst.message(nid)
        except P.DAMAGE_ERRORS:
            item = None
        if item is None:
            return f'[item 0x{nid:x} not found]', None, 'distribution list members naming an item not in the file'
        name = reader.text(reader.get(item.pc, TAG_DISPLAY_NAME))
        lid = _WRAPPED_CONTACT_ADDRESS.get((kind >> 4) & 0x7) if kind & 0x0F == 3 else None
        address = reader.text(reader.named(item, PSETID_ADDRESS, lid)) if lid else ''
        return _person(name, 'SMTP', address), nid, None
    return f'[entry {entry.hex()}]', None, 'distribution list members whose entry is not of this file, shown as stored'


def dl_members(message, pst, record_key, reader):
    """One line per member of a distribution list: the one-off entry at the member's position
    in PidLidDistributionListOneOffMembers when there is one, else the member's own entry
    from PidLidDistributionListMembers; a member that names an item of this file is followed
    by that item's ID. '' when neither property is stored."""
    if reader.named(message, PSETID_ADDRESS, LID_DL_STREAM) is not None:
        reader.counts['distribution lists with PidLidDistributionListStream, not decoded'] += 1
    members = reader.named(message, PSETID_ADDRESS, LID_DL_MEMBERS)
    one_offs = reader.named(message, PSETID_ADDRESS, LID_DL_ONE_OFF_MEMBERS)
    members = members if isinstance(members, list) else []
    one_offs = one_offs if isinstance(one_offs, list) else []
    if one_offs and members and len(one_offs) != len(members):
        reader.counts['distribution lists whose two member arrays differ in length'] += 1
    lines = []
    for i in range(max(len(members), len(one_offs))):
        text, nid, note = (_member_entry(members[i], pst, record_key, reader) if i < len(members)
                           else ('', None, None))
        one_off = parse_one_off(bytes(one_offs[i])) if i < len(one_offs) else None
        if one_off:
            text = _person(*one_off)
        elif note:
            reader.counts[note] += 1
        lines.append(text + (f' [item 0x{nid:x}]' if nid is not None else ''))
    return '\n'.join(lines)


# Recurrence of a calendar item ([MS-OXOCAL] 2.2.1.44)
LID_APPOINTMENT_RECUR = 0x8216       # PidLidAppointmentRecur
_FREQUENCY = {0x200A: 'Daily', 0x200B: 'Weekly', 0x200C: 'Monthly', 0x200D: 'Yearly'}
_PATTERN = {0x0: 'Day', 0x1: 'Week', 0x2: 'Month', 0x3: 'MonthNth', 0x4: 'MonthEnd',
            0xA: 'HjMonth', 0xB: 'HjMonthNth', 0xC: 'HjMonthEnd'}
_DAYS = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')
_NTH = {1: 'First', 2: 'Second', 3: 'Third', 4: 'Fourth', 5: 'Last'}
_END_TYPE = {0x2021: 'End by date', 0x2022: 'End after occurrences', 0x2023: 'No end', 0xFFFFFFFF: 'No end'}
NO_END_DATE = 0x5AE980DF
_ARO_SUBJECT, _ARO_MEETINGTYPE, _ARO_REMINDERDELTA, _ARO_REMINDER = 0x1, 0x2, 0x4, 0x8
_ARO_LOCATION, _ARO_BUSYSTATUS, _ARO_ATTACHMENT, _ARO_SUBTYPE, _ARO_APPTCOLOR = 0x10, 0x20, 0x40, 0x80, 0x100


class RecurrenceError(ValueError):
    """The blob does not follow the documented layout."""


def minutes_to_local(minutes):
    """A count of minutes since 1601-01-01 00:00 as a naive datetime: the blob stores these
    in the series' own time zone, not UTC."""
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(minutes=minutes)


def parse_recurrence(data):
    """The AppointmentRecurrencePattern of a PidLidAppointmentRecur value as a dict. Raises
    RecurrenceError on a version the document does not give, a field past the end, or bytes
    left after ReservedBlock2."""
    end, pos = len(data), 0

    def take(fmt):
        nonlocal pos
        size = struct.calcsize(fmt)
        if pos + size > end:
            raise RecurrenceError(f'a {size}-byte field at offset {pos} runs past the end ({end})')
        value = struct.unpack_from(fmt, data, pos)
        pos += size
        return value if len(value) > 1 else value[0]

    def skip(n):
        nonlocal pos
        if n < 0 or pos + n > end:
            raise RecurrenceError(f'{n} bytes at offset {pos} run past the end ({end})')
        pos += n

    reader_v, writer_v, frequency, pattern, calendar = take('<5H')
    if (reader_v, writer_v) != (0x3004, 0x3004):
        raise RecurrenceError(f'versions 0x{reader_v:x}/0x{writer_v:x}, not 0x3004')
    first, period, _sliding = take('<3I')
    out = {'frequency': frequency, 'pattern': pattern, 'calendar': calendar, 'period': period,
           'days': None, 'day': None, 'nth': None}
    if pattern in (0x1,):
        out['days'] = take('<I')
    elif pattern in (0x2, 0x4, 0xA, 0xC):
        out['day'] = take('<I')
    elif pattern in (0x3, 0xB):
        out['days'], out['nth'] = take('<2I')
    elif pattern != 0x0:
        raise RecurrenceError(f'PatternType 0x{pattern:x} is not one the document gives')
    out['end_type'], out['occurrences'], out['first_dow'] = take('<3I')
    out['deleted'] = [take('<I') for _ in range(take('<I'))]
    out['modified'] = [take('<I') for _ in range(take('<I'))]
    out['start_date'], out['end_date'] = take('<2I')
    reader2, writer2, out['start_offset'], out['end_offset'] = take('<4I')
    if reader2 != 0x3006:
        raise RecurrenceError(f'ReaderVersion2 0x{reader2:x}, not 0x3006')
    exceptions = []
    for _ in range(take('<H')):
        start, finish, original, flags = take('<3IH')
        e = {'start': start, 'end': finish, 'original': original, 'flags': flags,
             'subject': None, 'location': None}
        if flags & _ARO_SUBJECT:
            _length, length2 = take('<2H')
            e['subject'] = data[pos:pos + length2].decode('cp1252', 'replace')
            skip(length2)
        for flag in (_ARO_MEETINGTYPE, _ARO_REMINDERDELTA, _ARO_REMINDER):
            if flags & flag:
                skip(4)
        if flags & _ARO_LOCATION:
            _length, length2 = take('<2H')
            e['location'] = data[pos:pos + length2].decode('cp1252', 'replace')
            skip(length2)
        for flag in (_ARO_BUSYSTATUS, _ARO_ATTACHMENT, _ARO_SUBTYPE, _ARO_APPTCOLOR):
            if flags & flag:
                skip(4)
        exceptions.append(e)
    skip(take('<I'))                                  # ReservedBlock1
    for e in exceptions:
        if writer2 >= 0x3009:
            skip(take('<I'))                          # ChangeHighlight
        skip(take('<I'))                              # ReservedBlockEE1
        if e['flags'] & (_ARO_SUBJECT | _ARO_LOCATION):
            skip(12)                                  # StartDateTime, EndDateTime, OriginalStartDate
            if e['flags'] & _ARO_SUBJECT:
                n = take('<H')
                e['subject'] = data[pos:pos + 2 * n].decode('utf-16-le', 'replace')
                skip(2 * n)
            if e['flags'] & _ARO_LOCATION:
                n = take('<H')
                e['location'] = data[pos:pos + 2 * n].decode('utf-16-le', 'replace')
                skip(2 * n)
            skip(take('<I'))                          # ReservedBlockEE2
    skip(take('<I'))                                  # ReservedBlock2
    if pos != end:
        raise RecurrenceError(f'{end - pos} bytes after ReservedBlock2')
    out['exceptions'] = exceptions
    out['first_date_time'] = first
    return out


def describe_pattern(r):
    """The stored pattern fields in words: frequency, PatternType and its fields, period."""
    words = [_FREQUENCY.get(r['frequency'], 'RecurFrequency 0x%x' % r['frequency']),
             _PATTERN.get(r['pattern'], 'PatternType 0x%x' % r['pattern'])]
    if r['days'] is not None:
        words.append(','.join(d for i, d in enumerate(_DAYS) if r['days'] & (1 << i)) or 'no days')
    if r['nth'] is not None:
        words.append(_NTH.get(r['nth'], 'N %d' % r['nth']))
    if r['day'] is not None:
        words.append('day %d' % r['day'])
    # Period is minutes for a daily pattern, weeks for a weekly one and months for monthly
    # and yearly ones (2.2.1.44.1); any other combination is shown as stored
    period = r['period']
    if r['frequency'] == 0x200A and r['pattern'] == 0x0 and period % 1440 == 0:
        words.append(f'every {period // 1440} day(s)')
    elif r['frequency'] == 0x200B and r['pattern'] == 0x1:
        words.append('every %d week(s)' % period)
    elif r['frequency'] in (0x200C, 0x200D):
        words.append('every %d month(s)' % period)
    else:
        words.append('Period %d' % period)
    return ', '.join(words)


def _local(minutes, with_time=True):
    value = minutes_to_local(minutes)
    return value.strftime('%Y-%m-%d %H:%M') if with_time else value.date().isoformat()


def recurrence_columns(message, reader):
    """(Recurrence, Series End, Deleted Occurrences, Modified Occurrences) from
    PidLidAppointmentRecur, or four blanks when it is not stored or does not decode."""
    blob = reader.named(message, PSETID_APPOINTMENT, LID_APPOINTMENT_RECUR)
    if not isinstance(blob, (bytes, bytearray)):
        return '', '', '', ''
    try:
        r = parse_recurrence(bytes(blob))
    except RecurrenceError:
        reader.counts['recurrence values that do not follow the documented layout, left blank'] += 1
        return '', '', '', ''
    end_type = _END_TYPE.get(r['end_type'], 'EndType 0x%x' % r['end_type'])
    if r['end_type'] == 0x2022:
        end_type = 'end after %d occurrences' % r['occurrences']
    text = describe_pattern(r) + '; ' + end_type[0].lower() + end_type[1:]
    series_end = '' if r['end_date'] == NO_END_DATE else _local(r['end_date'], False)
    # an exception's original date is in DeletedInstanceDates too; a date left after taking
    # those out is an occurrence removed from the series
    originals = {e['original'] - e['original'] % 1440 for e in r['exceptions']}
    deleted = '\n'.join(_local(d, False) for d in r['deleted'] if d not in originals)
    lines = []
    for e in r['exceptions']:
        line = _local(e['original']) + ' moved to ' + _local(e['start']) + ' to ' + _local(e['end'])
        if e['subject'] is not None:
            line += ' | Subject: ' + e['subject']
        if e['location'] is not None:
            line += ' | Location: ' + e['location']
        lines.append(line)
    return text, series_end, deleted, '\n'.join(lines)
