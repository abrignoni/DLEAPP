"""Shared reading for the Outlook PST and OST artifacts in scripts/artifacts/outlookPst.py.

Files are read with the vendored pstprobe (scripts/vendor/pstprobe.py). Property IDs and
names are those of Microsoft [MS-OXPROPS] v20250520; what each property means, and the
values an enumerated one takes, are cited beside it from the Exchange protocol
documents ([MS-OXCMSG], [MS-OXOMSG], [MS-OXOCNTC], [MS-OXOTASK], [MS-OXONOTE],
[MS-OXOJRNL], release v20250520, and [MS-OXOCAL], release v20250819).
"""

import hashlib
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


def _index(pst, path, counts):
    """(folder path, item NID, class) for every item listed in a normal folder's contents
    table, walking the folder tree from the root. Search folders, whose results are items
    of other folders, and folder-associated contents are not listed. The class is read from
    the contents table row, else from the item."""
    stat = os.stat(path)
    key = (os.path.realpath(path), stat.st_size, stat.st_mtime_ns)
    if key in _INDEX:
        return _INDEX[key]
    items, seen = [], set()
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
