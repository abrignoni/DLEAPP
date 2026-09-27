__artifacts_v2__ = {
    "macosNotarizationTickets": {
        "name": "Notarization Tickets",
        "description": 'Code signing hashes listed in the notarization tickets Gatekeeper stores, one row per '
                       "hash, with the ticket's own timestamp and stored last_access value, and the bundle IDs "
                       'ExecPolicy records for the hash.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "System Policy (macOS)",
        "notes": (
            (
            (
            'Reads the tickets and hashes tables of the Tickets database in '
            "/var/db/SystemPolicyConfiguration, which Mother's Ruin Software describes as the "
            'cache in which macOS keeps the code signing digests (cdhashes) a notarization ticket '
            'lists: they are added when the signature of an app carrying a stapled ticket is '
            'first verified, when a disk image carrying one is opened, or when macOS requests a '
            "ticket from Apple, which it does at an app's first launch and at other times even "
            'when a ticket is stapled (References: '
            'https://www.mothersruin.com/software/Apparency/faq.html; '
            'https://www.mothersruin.com/software/Archaeology/reverse/tickets.html). A row is '
            'therefore not by itself evidence that the code it lists ran on this Mac. One row is '
            'reported per hash, with the fields of the ticket that lists it through '
            'hashes.ticket_id, the column syspolicyd joins on to look a hash up (Scott Knight, '
            "'syspolicyd internals', "
            'https://knight.sc/reverse%20engineering/2019/02/20/syspolicyd-internals.html); Hash '
            'and Ticket Hash are shown in lowercase hexadecimal. A ticket that lists no hash gets '
            'one row with Hash blank, and a hash whose ticket is missing keeps its row with the '
            'ticket columns blank; neither occurs on the public images. Ticket Timestamp is '
            'tickets.timestamp read as Unix seconds in UTC. It is the time the ticket itself '
            "records, which Mother's Ruin describes as corresponding, more or less, to when "
            'notarization was granted or the ticket issued, not a time this Mac stored or used '
            'the ticket: on the public MacBook Pro logical extraction (macOS 15.4 build 24E248, '
            'not a registered corpus key), 10 stored tickets list exactly the hashes of a ticket '
            'stapled into a Contents/CodeResources file on the same extraction, decoded with the '
            "layout Mother's Ruin gives, and 7 of them carry exactly that stapled ticket's "
            'timestamp; the other 3 are later, one of them a second stored ticket for '
            "Signal.app's 42 hashes 20 hours 51 minutes after the first. Last Access is "
            'tickets.last_access, a column the macOS 15.4 database has and the macOS 11.2.1 one '
            'on dleapp_macos_bigsur lacks, where it is blank; it is read as Unix seconds in UTC '
            'on this evidence: on the public MacBook Pro extraction it lies within 4 seconds of '
            "the latest Gatekeeper Scan Cache Timestamp (UTC) of a ticket's hashes on 6 of the 19 "
            'tickets whose hashes that cache holds. What it records is not established. Hash Type '
            "and Ticket Hash Type are stored integers; Mother's Ruin says a ticket's hash types "
            "are Apple's SecCSDigestAlgorithm values, which Apple defines as 1 SHA-1, 2 SHA-256, "
            '3 SHA-256 truncated to 20 bytes, 4 SHA-384 and 5 SHA-512 '
            '(https://github.com/apple-oss-distributions/Security/blob/97c3a4296c1ea06b0fe1877a7e616aa84450b5b2/OSX/libsecurity_codesigning/lib/CSCommon.h#L384-L390), '
            "and that an installer package's ticket usually carries a SHA-1 digest; only 1 and 2 "
            'occur on the public images, every hash there is 20 bytes, and on the 10 stored '
            'tickets that match a stapled ticket every hash has the type that ticket gives it. '
            'Ticket Hash is tickets.hash; on every ticket of both public images it is one of the '
            "ticket's own hashes, and what selects it is not established. Ticket Flags is "
            'tickets.flags as stored, 0 on every ticket and so on every row of both public '
            'images. Bundle IDs (ExecPolicy) lists the Bundle ID values that the ExecPolicy '
            'database in the same folder records for the same cdhash in the rows the Gatekeeper '
            'Scan Cache and Executable Measurements artifacts report, NOT_A_BUNDLE included as '
            'stored; it is filled on 81 of the 100 rows of dleapp_macos_bigsur and 42 of the 652 '
            'rows of the public MacBook Pro extraction, and a blank means only that no ExecPolicy '
            'database beside the Tickets file records a bundle ID for that cdhash. The '
            'legacy_policy table is empty on both public images, so what it holds is not '
            'established and it is not reported. A row that more than one copy of the database '
            'holds with the same values is reported once, and Source File lists every copy; on '
            'the public MacBook Pro extraction that joins the copies at private/var/db and '
            'System/Volumes/Data/private/var/db.'
        )
        )
        ),
        "paths": ('*/var/db/SystemPolicyConfiguration/Tickets*',
                  '*/var/db/SystemPolicyConfiguration/ExecPolicy*'),
        "output_types": ["standard"],
        "artifact_icon": "certificate",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 100 rows",
        },
    },
}

import os
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db,
                               get_sqlite_db_records, logfunc)
from scripts.macos_powerlog import merge_sources

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _databases(context, name):
    """Staged copies of one database by file name (not its sidecars or directories)."""
    return sorted({str(path) for path in context.get_files_found()
                   if os.path.basename(str(path)) == name and not os.path.isdir(str(path))})


def _blank(value):
    return '' if value is None else value


def _unix_time(value):
    """Unix seconds as a UTC datetime; blank for no value and for 0; the stored value when it
    is not a number."""
    if value is None or value == 0:
        return ''
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    try:
        return _UNIX_EPOCH + timedelta(seconds=value)
    except OverflowError:
        return value


def _hex(value):
    """A stored hash as lowercase hexadecimal; a value that is not bytes as stored."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    return _blank(value)


def _columns(path, table):
    return {row['name'] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')}


def _bundle_ids(path):
    """cdhash (lowercase hexadecimal) -> bundle IDs the ExecPolicy database at path records for
    it, from the Gatekeeper scan cache and the executable measurements."""
    names = {}
    for table, column in (('policy_scan_cache', 'bundle_id'),
                          ('executable_measurements_v2', 'bundle_identifier')):
        if not does_table_exist_in_db(path, table) or not {'cdhash', column} <= _columns(path, table):
            continue
        for row in get_sqlite_db_records(path, f'SELECT cdhash, {column} AS bundle FROM {table} '
                                               'WHERE cdhash IS NOT NULL'):
            if row['bundle']:
                names.setdefault(str(row['cdhash']).strip().lower(), set()).add(row['bundle'])
    return names


@artifact_processor
def macosNotarizationTickets(context):
    data_headers = (('Ticket Timestamp (UTC)', 'datetime'), ('Last Access (UTC)', 'datetime'),
                    'Ticket ID', 'Hash', 'Hash Type (as stored)', 'Ticket Hash',
                    'Ticket Hash Type (as stored)', 'Ticket Flags (as stored)',
                    'Bundle IDs (ExecPolicy)', 'Source File')
    records, read = [], []
    for path in _databases(context, 'Tickets'):
        relative = context.get_relative_path(path)
        if not (does_table_exist_in_db(path, 'tickets') and does_table_exist_in_db(path, 'hashes')):
            logfunc(f'Notarization Tickets: no tickets and hashes tables in {relative}')
            continue
        last = 't.last_access' if 'last_access' in _columns(path, 'tickets') else 'NULL'
        ticket = (f't.id AS ticket_id, t.hash AS ticket_hash, t.hash_type AS ticket_hash_type, '
                  f't.timestamp AS timestamp, t.flags AS flags, {last} AS last_access')
        rows = get_sqlite_db_records(
            path, f'SELECT {ticket}, h.hash AS hash, h.hash_type AS hash_type FROM tickets t '
                  'LEFT JOIN hashes h ON h.ticket_id = t.id ORDER BY t.timestamp, t.id, h.id')
        # A hash whose ticket is gone is kept, with the ticket columns blank.
        rows = list(rows) + list(get_sqlite_db_records(
            path, 'SELECT h.ticket_id AS ticket_id, NULL AS ticket_hash, NULL AS ticket_hash_type, '
                  'NULL AS timestamp, NULL AS flags, NULL AS last_access, h.hash AS hash, '
                  'h.hash_type AS hash_type FROM hashes h WHERE h.ticket_id IS NULL OR h.ticket_id '
                  'NOT IN (SELECT id FROM tickets) ORDER BY h.id'))
        execpolicy = os.path.join(os.path.dirname(path), 'ExecPolicy')
        names = {}
        if os.path.isfile(execpolicy):
            names = _bundle_ids(execpolicy)
            if names:
                read.append(execpolicy)
        if rows:
            read.append(path)
        for row in rows:
            digest = _hex(row['hash'])
            bundles = names.get(digest, set()) if isinstance(digest, str) else set()
            records.append(((_unix_time(row['timestamp']), _unix_time(row['last_access']),
                             _blank(row['ticket_id']), digest, _blank(row['hash_type']),
                             _hex(row['ticket_hash']), _blank(row['ticket_hash_type']),
                             _blank(row['flags']), '\n'.join(sorted(bundles))), relative))
    data_list = [values + ('\n'.join(sources),) for values, sources in merge_sources(records)]
    return data_headers, data_list, '\n'.join(read)
