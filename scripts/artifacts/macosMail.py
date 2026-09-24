"""Messages indexed in the macOS Mail Envelope Index, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosMailMessages": {
        "name": "Mail Messages",
        "description": "Messages listed in each user's Mail Envelope Index: received and sent "
                       "times, sender, recipients with their stored type, subject, the stored "
                       "summary text, mailbox, attachment names and the stored read, flagged "
                       "and deleted values.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "none",
        "category": "Mail (macOS)",
        "notes": "Reads each user's Envelope Index under ~/Library/Mail/V<n>/MailData, one "
                 "row per message in its messages table. Date Received (UTC) and Date Sent "
                 "(UTC) are date_received and date_sent read as Unix seconds; read that "
                 "way the 98 messages on the public MacBook Pro logical extraction (macOS "
                 "15.4, not a registered corpus key) were received between 4 November and "
                 "25 December 2025, where the 2001 epoch would place them in 2056. Sender "
                 "and Sender Name are the address and comment of the addresses row the "
                 "message names as its sender. Recipients (type as stored) lists the "
                 "recipients rows for the message, in type and position order, each as its "
                 "address with the stored type; what the type means is not established "
                 "here, and on the MacBook Pro the recipients rows of the 98 messages "
                 "stored type 0 on 98 and type 1 on 2. The recipients table there also "
                 "holds 9 rows naming 9 message row IDs that the messages table does not "
                 "hold, and those rows are not reported. Subject is subject_prefix "
                 "followed by the subjects row the message names. Summary is the text of "
                 "the summaries row the message names; 73 of the 98 messages name one. "
                 "Mailbox is the url of the mailboxes row. Attachments lists the names in "
                 "the attachments table for the message; 3 of the 98 messages have one or "
                 "more. Read, Flagged, Deleted, Size, Conversation ID and Message Row ID "
                 "are read, flagged, deleted, size, conversation_id and ROWID as stored; "
                 "Read was 1 on 18 of the 98 messages, and Flagged and Deleted each held "
                 "one value on all 98. On dleapp_macos_bigsur there are Mail folders and "
                 "no Envelope Index, so this artifact reports no rows there. On the "
                 "MacBook Pro the Users/ and System/Volumes/Data/Users/ copies of the "
                 "Envelope Index differ and both are read, so each message appears twice, "
                 "identical in every column but Source File, and all rows come from one "
                 "user, so User holds one value. When a logical extraction holds the same "
                 "file under Users/ and under System/Volumes/Data/Users/, a byte-identical "
                 "second copy is read once and counted in the run log. The message files "
                 "(.emlx) are not read.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows (Mail folders with no Envelope Index)",
                       },
        "paths": ('*/Library/Mail/V*/MailData/Envelope Index*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "mail",
    }
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import (artifact_processor, does_column_exist_in_db, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_plists import unique_sources, user_from_path

_LABEL = 'Mail Messages'
_INDEX = 'Envelope Index'
_MESSAGE_COLUMNS = ('ROWID', 'date_received', 'date_sent', 'sender', 'subject_prefix', 'subject',
                    'summary', 'mailbox', 'read', 'flagged', 'deleted', 'size', 'conversation_id')


def _text(value):
    return '' if value is None else str(value)


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime, or '' when not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _columns(path, table, names):
    """The named columns, with NULL standing in for any the table lacks; ROWID is always kept."""
    return ', '.join(name if name == 'ROWID' or does_column_exist_in_db(path, table, name)
                     else f'NULL AS {name}' for name in names)


def _lookup(path, table, columns):
    """ROWID -> the other named columns, for a small lookup table; {} when it is absent."""
    if not does_table_exist_in_db(path, table):
        return {}
    return {row[0]: row[1:] for row in get_sqlite_db_records(
        path, f"SELECT {_columns(path, table, ('ROWID',) + columns)} FROM {table}") or []}


def _grouped(path, table, key, columns, order):
    """key -> list of rows of the other named columns, for a one-to-many table."""
    if not does_table_exist_in_db(path, table):
        return {}
    groups = {}
    for row in get_sqlite_db_records(
            path, f"SELECT {_columns(path, table, (key,) + columns)} FROM {table} ORDER BY {order}") or []:
        groups.setdefault(row[0], []).append(row[1:])
    return groups


def _address(addresses, rowid):
    address, name = addresses.get(rowid, (None, None))
    return _text(address), _text(name)


def _rows(path):
    addresses = _lookup(path, 'addresses', ('address', 'comment'))
    subjects = _lookup(path, 'subjects', ('subject',))
    summaries = _lookup(path, 'summaries', ('summary',))
    mailboxes = _lookup(path, 'mailboxes', ('url',))
    recipients = _grouped(path, 'recipients', 'message', ('address', 'type'), 'message, type, position')
    attachments = _grouped(path, 'attachments', 'message', ('name',), 'message, ROWID')
    records = get_sqlite_db_records(
        path, f"SELECT {_columns(path, 'messages', _MESSAGE_COLUMNS)} FROM messages "
              "ORDER BY date_received") or []
    for row in records:
        (rowid, received, sent, sender, prefix, subject, summary, mailbox, read, flagged, deleted,
         size, conversation) = row
        sender_address, sender_name = _address(addresses, sender)
        recipient_text = '; '.join(
            f'{_address(addresses, address)[0]} (type {_text(kind)})'
            for address, kind in recipients.get(rowid, []))
        subject_text = _text(prefix) + _text(subjects.get(subject, ('',))[0])
        yield (_unix_utc(received), _unix_utc(sent), sender_address, sender_name, recipient_text,
               subject_text, _text(summaries.get(summary, ('',))[0]),
               _text(mailboxes.get(mailbox, ('',))[0]),
               '; '.join(_text(name) for (name,) in attachments.get(rowid, [])),
               _text(read), _text(flagged), _text(deleted), _text(size), _text(conversation),
               _text(rowid))


@artifact_processor
def macosMailMessages(context):
    data_headers = (('Date Received (UTC)', 'datetime'), ('Date Sent (UTC)', 'datetime'),
                    'Sender', 'Sender Name', 'Recipients (type as stored)', 'Subject', 'Summary',
                    'Mailbox', 'Attachments', 'Read (as stored)', 'Flagged (as stored)',
                    'Deleted (as stored)', 'Size (as stored)', 'Conversation ID', 'Message Row ID',
                    'User', 'Source File')
    data_list = []
    read = []
    indexes = [p for p in context.get_files_found() if os.path.basename(str(p)) == _INDEX]
    paths, _skipped = unique_sources(context, indexes, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'messages'):
            logfunc(f'{_LABEL}: no messages table read from {relative}')
            continue
        read.append(path)
        found = [row + (user_from_path(relative), relative) for row in _rows(path)]
        if not found:
            logfunc(f'{_LABEL}: no messages in {relative}')
        data_list.extend(found)
    return data_headers, data_list, '\n'.join(read)
