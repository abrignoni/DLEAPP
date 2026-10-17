"""The BSM audit trail macOS's auditd writes to /var/audit, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosBsmAudit": {
        "name": "Audit Trail (BSM)",
        "description": "The records in the BSM audit trail files auditd keeps in /var/audit, one row per record in file "
                       "order: the time in its header, the event, the result, the subject's audit, effective and real user "
                       "and group IDs, process and session IDs and terminal, the signing identity, and its text, path, "
                       "argument and other tokens, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Audit Trail (macOS)",
        "notes": "Reads the trail files in /var/audit (private/var/audit on a Mac). The audit daemon names a new trail"
                 " with a timestamp and .not_terminated "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/libauditd/auditd_lib.c#L823-L824),"
                 " replaces not_terminated with a second timestamp when it closes it "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/bin/auditd/auditd.c#L171-L174),"
                 " and at startup replaces not_terminated with crash_recovery in the name of the trail the current "
                 "link still points to, which its comment describes as audit not having been shut down properly "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/libauditd/auditd_lib.c#L1004-L1019);"
                 " every file there is read whatever its name, and one whose first byte is neither a header token nor "
                 "a file token is counted in the run log and not read. The format is OpenBSM's (BSD licence), read by "
                 "scripts/bsm_audit.py, a pure-Python reader written from libbsm's own reader, the one praudit uses: "
                 "the record framing in au_read_rec "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_io.c#L4714-L4816),"
                 " the token dispatch in au_fetch_tok "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_io.c#L4326-L4475)"
                 " and the token identifiers in audit_record.h "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/sys/bsm/audit_record.h#L44-L136);"
                 " the token layouts are also documented in Apple's audit.log(5) "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/man/audit.log.5)."
                 " Apple's identity token (0xed), which OpenBSM's reader does not read, follows its writer, "
                 "au_to_identity in xnu "
                 "(https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/security/audit/audit_bsm_token.c#L1380-L1443)."
                 " Reading a trail stops, as au_read_rec does, at the first record that runs past the end of the file "
                 "or starts with neither token, and the bytes left are counted in the run log. A token of a type the "
                 "reader does not know is skipped to where the trailer starts, as fetch_invalid_tok does "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_io.c#L4253-L4270),"
                 " so a token after it in the same record is skipped with it; a token that runs past its record ends "
                 "that record's tokens, as praudit does "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/bin/praudit/praudit.c#L103-L111);"
                 " both are counted in the run log and the record is still reported. Validation: every record of both "
                 "tested images was compared with the output of /usr/sbin/praudit on a macOS 27.0.1 system (26A434), "
                 "field by field, twice: with praudit -r -n (every token's numeric fields, one line per token, the "
                 "trailer included) and with praudit -x -r -n parsed as XML. On dleapp_macos_bigsur 5,253 of 5,253 "
                 "records and 36,216 of 36,216 tokens matched, and on magnet2021_macos_bigsur 4,327 of 4,327 records "
                 "and 29,773 of 29,773 tokens. The token types they hold are header (0x14), subject (0x24), expanded "
                 "subject (0x7a), text, path, 32 and 64-bit argument, return (0x27), identity and trailer. A trail "
                 "written for the unit tests, holding the file token, the 32-bit expanded and 64-bit headers, the "
                 "64-bit and IPv6 expanded subjects, the 64-bit return, exec arguments, an IP address and a token of "
                 "an unknown type, gave the same fields as praudit; no evidence image holds those, and every other "
                 "token type the reader reads (socket, attribute, process, IPC, opaque, data, sequence, exit, group, "
                 "exec environment, IP, IP port, expanded IP address, zone, privilege and UUID tokens, and the 64-bit "
                 "expanded header and subject) was not exercised against any data. Time (UTC) is the header's seconds "
                 "since 1970-01-01 UTC and milliseconds, which Apple's audit.log(5) describes as the time at which the"
                 " event occurred "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/man/audit.log.5#L89-L94);"
                 " OpenBSM's libbsm fills them from gettimeofday when it builds a record "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_token.c#L1668-L1674"
                 " and "
                 "https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_token.c#L1547-L1571),"
                 " and the kernel from the ar_endtime it passes to kau_close "
                 "(https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/security/audit/audit_bsm.c#L147-L153"
                 " and "
                 "https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/security/audit/audit_bsm.c#L2082)."
                 " Rows are in file order, which is not time order: on magnet2021_macos_bigsur 8 records carry a time "
                 "earlier than the record before them in the same file. Event is the description the audit_event file "
                 "gives the header's event number. It is taken from the extraction's own "
                 "private/etc/security/audit_event first, then from the copy under System/Library/Templates/Data, read"
                 " the way libbsm's getauevnum_r reads it, first matching line wins "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_event.c#L63-L102"
                 " and "
                 "https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/libbsm/bsm_event.c#L276-L298)."
                 " A number that file does not hold, or every number when the extraction holds no readable copy, is "
                 "named from the audit_event table of Apple's OpenBSM-21 "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/etc/audit_event),"
                 " bundled, and a number that table lacks by the constant xnu's audit_kevents.h or OpenBSM's "
                 "audit_uevents.h defines for it "
                 "(https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/bsm/audit_kevents.h"
                 " and "
                 "https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/bsm/audit_uevents.h);"
                 " Event Name From says which, per row. That table lacks the session events 44901 to 44904, which xnu "
                 "names AUE_SESSION_START, AUE_SESSION_UPDATE, AUE_SESSION_END and AUE_SESSION_CLOSE "
                 "(https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/bsm/audit_kevents.h#L624-L627)."
                 " On dleapp_macos_bigsur the extraction's audit_event copies are compressed in a way the image reader"
                 " does not decompress, so names came from the bundled tables: 4,103 rows from the OpenBSM table and "
                 "1,150 from the constants; praudit took its descriptions from the comparing system's "
                 "/etc/security/audit_event, which is byte-identical to magnet2021_macos_bigsur's, and with that table"
                 " the reader's 5,253 descriptions all equal praudit's. On magnet2021_macos_bigsur Event Name From "
                 "held one value on all rows, the extraction's own file, and every description equals praudit's. Event"
                 " ID is the number as stored. Result is success when the return token's error number is 0 and failure"
                 " otherwise. Error (BSM) is that number as stored, with the name OpenBSM's audit_errno.h gives it "
                 "where it gives one "
                 "(https://github.com/openbsm/openbsm/blob/6230904e8b0c8d73339682ebe9173dd853436047/sys/bsm/audit_errno.h);"
                 " Apple's audit.log(5) describes the field as the errno value "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/man/audit.log.5#L334-L351)."
                 " A number that file does not name, such as 255 on both tested images, is reported as the number "
                 "alone, and its meaning is not established here. Return Value is reported as an unsigned number, as "
                 "praudit prints it. Audit UID, Effective UID, Real UID, Effective GID, Real GID, PID, Session ID, "
                 "Terminal Port and Terminal Address are the first subject or expanded subject token's fields, as "
                 "audit.log(5) names them "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/man/audit.log.5#L352-L381),"
                 " the IDs printed as signed numbers as praudit prints them; an Audit UID of -1 is AU_DEFAUDITID, one "
                 "of the pre-defined audit IDs in xnu's audit.h "
                 "(https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/bsm/audit.h#L72-L75)."
                 " A second subject token, a process token (the target of an operation rather than its subject) and "
                 "any other token not shown in its own column go to Other Tokens with their fields. Audit User, "
                 "Effective User and Real User are the name in the local user record "
                 "(var/db/dslocal/nodes/Default/users/*.plist) in the extraction whose uid equals the ID, and are "
                 "blank when no such record is in the extraction; no name comes from the machine running the tool. On "
                 "magnet2021_macos_bigsur 1,122 rows carry an effective UID no user record in the extraction names. "
                 "Signing ID, Team ID and CDHash are the identity token's signing identifier, team identifier and code"
                 " directory hash as stored, with (truncated) added when the token's flag says the writer truncated "
                 "the value, which no tested row carried; Team ID held no value on any row of either tested image. "
                 "Text holds every text token, one per line, and a text token can itself hold line breaks (10 on "
                 "magnet2021_macos_bigsur, 46 on dleapp_macos_bigsur); Paths holds every path token; Arguments holds "
                 "each argument token as its number, its description and its value in hexadecimal; Exec Args holds the"
                 " exec argument token's strings, one per line. Exec Args and Other Tokens held no value on any row of"
                 " either tested image; the audit_control on magnet2021_macos_bigsur selects the lo and aa classes, "
                 "and the copy on dleapp_macos_bigsur is compressed in a way the image reader does not decompress. A "
                 "file token, which audit.log(5) describes as marking where a trail begins and ends "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/man/audit.log.5#L70-L76),"
                 " is a row of its own, with its time and, in Paths, the file name it holds; neither tested image "
                 "holds one. When a logical extraction holds the same trail under private/var, System/Volumes/Data and"
                 " System/Volumes/Update/mnt1, a byte-identical copy is read once, and a record two differing copies "
                 "both hold is reported once with both files in Source File; magnet2021_macos_bigsur holds three "
                 "byte-identical copies of each of its 9 trails, so its 12,981 records in all are 4,327 records. "
                 "Source File stays because the trail file is not otherwise identified. Not reported: the records of "
                 "/var/audit/current, a link to the open trail "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/bsm/auditd_lib.h#L54),"
                 " that the trail it names also holds, when an extraction holds the link as a copy of the file "
                 "(neither tested image does); and the configuration in /etc/security (audit_control, audit_class, "
                 "audit_user, audit_warn), which says what is to be audited and holds no record. Not covered: trails "
                 "from macOS versions other than 11.2.1, the only version whose trails were tested; the public macOS "
                 "15.4 extraction holds an empty private/var/audit, and the macOS 14.6.1 image no such folder.",
        "paths": ('*/var/audit/*', '*/etc/security/audit_event',
                  '*/var/db/dslocal/nodes/Default/users/*.plist'),
        "output_types": "standard",
        "artifact_icon": "shield",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 5253 rows",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no var/audit folder in the image)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 4327 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (private/var/audit present and empty)",
        },
    },
    "macosBsmAuditAccounts": {
        "name": "Audit Trail Logins and Account Changes (BSM)",
        "description": "The records of the Audit Trail (BSM) artifact whose event number is one of a fixed list of login and"
                       " logout, user, group and password change, authentication, sudo, shutdown and audit startup events, "
                       "with the same columns.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Audit Trail (macOS)",
        "notes": "Reads the same trails, the same way, as the Audit Trail (BSM) artifact, whose notes give the format,"
                 " the sources, the validation against praudit and the meaning of every column, and keeps only the "
                 "records whose event number is in a fixed list, named here as Apple's OpenBSM-21 audit_event names "
                 "them "
                 "(https://github.com/apple-oss-distributions/OpenBSM/blob/bb0681420e99d447f466ba70d38589213bb69fea/openbsm/etc/audit_event),"
                 " first matching line: logins and logouts, 6152 to 6155, 6158, 6159, 6162 to 6165, 6171 to 6173, "
                 "6212, 6213, 6600, 6601, 32800, 45021 and 45022 (local, telnet, rlogin, rsh, su, rexecd, passwd, "
                 "rexd, ftp, ftp logout, ssh, role, newgrp, admin, loginwindow and OpenSSH); user, group and password "
                 "changes, 6207 to 6211, 6501, 6511 to 6515 and 45014 to 45019; authentication, 6300, 45023, 45027 and"
                 " 45028 (sudo, user authentication, Calife); system halt, reboot and shutdown, 6160, 6161 and 6168; "
                 "and audit startup, shutdown and crash recovery, 45000, 45001 and 45029. The table holds two lines "
                 "for 6171 and 6172, and the first names them ftp logout and login - ssh. The list is chosen by event "
                 "number, not by what a record holds: authorization requests (SecSrvr AuthEngine and AuthMechanism, "
                 "45025 and 45030) and audit session records (44901 to 44904), which make up most of both tested "
                 "images, stay in the full artifact only. On dleapp_macos_bigsur 449 of 5,253 records were kept and on"
                 " magnet2021_macos_bigsur 452 of 4,327. On both images Event Name From held one value on all kept "
                 "rows (the bundled OpenBSM table on dleapp_macos_bigsur, the extraction's own audit_event on "
                 "magnet2021_macos_bigsur), and Team ID, Arguments, Exec Args and Other Tokens held no value on any "
                 "kept row.",
        "paths": ('*/var/audit/*', '*/etc/security/audit_event',
                  '*/var/db/dslocal/nodes/Default/users/*.plist'),
        "output_types": "standard",
        "artifact_icon": "log-in",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 449 rows",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no var/audit folder in the image)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 452 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (private/var/audit present and empty)",
        },
    },
}

import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts import bsm_audit
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import canonical_relative, fold_view_rows, load_plist, unique_sources

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_TEMPLATE = 'System/Library/Templates/Data/'
FROM_IMAGE = 'audit_event in the extraction'
FROM_TABLE = 'OpenBSM audit_event table (bundled)'
FROM_CONSTANT = 'xnu or OpenBSM header constant (bundled)'
FILE_TOKEN = 'file token (not an audit record)'
NOT_FOUND = 'not in any table'

# Event numbers the logins and account changes artifact keeps, as audit_event names them:
# login, logout, su, ssh, telnet, rlogin, rsh, rexec, ftp, passwd, newgrp, admin and
# loginwindow events; user, group and password changes; user authentication, sudo and
# Calife; system halt, reboot and shutdown; audit startup, shutdown and crash recovery.
ACCOUNT_EVENTS = frozenset((
    6152, 6153, 6154, 6155, 6158, 6159, 6160, 6161, 6162, 6163, 6164, 6165, 6168, 6171, 6172, 6173,
    6207, 6208, 6209, 6210, 6211, 6212, 6213, 6300, 6501, 6511, 6512, 6513, 6514, 6515, 6600, 6601,
    32800, 45000, 45001, 45014, 45015, 45016, 45017, 45018, 45019, 45021, 45022, 45023, 45027, 45028,
    45029))

HEADERS = (('Time (UTC)', 'datetime'), 'Event', 'Event ID', 'Event Name From', 'Result', 'Error (BSM)',
           'Return Value', 'Audit UID', 'Audit User', 'Effective UID', 'Effective User', 'Real UID',
           'Real User', 'Effective GID', 'Real GID', 'PID', 'Session ID', 'Terminal Port',
           'Terminal Address', 'Signing ID', 'Team ID', 'CDHash', 'Text', 'Paths', 'Arguments',
           'Exec Args', 'Other Tokens', 'Source File')

_SUBJECTS = (0x24, 0x75, 0x7a, 0x7c)
_RETURNS = (0x27, 0x72)
_ARGS = (0x2d, 0x71)


def _time(seconds, msec):
    try:
        return _EPOCH + timedelta(seconds=seconds, milliseconds=msec)
    except OverflowError:
        return ''


def _is_trail(path):
    try:
        with open(path, 'rb') as handle:
            first = handle.read(1)
    except OSError:
        return False
    return bool(first) and (first[0] in bsm_audit.HEADERS or first[0] == bsm_audit.AUT_OTHER_FILE32)


def _event_table(context, paths, problems):
    """(table, relative path) from the extraction's audit_event, the live copy before the
    template macOS keeps under System/Library/Templates/Data, or ({}, '')."""
    ranked = sorted(paths, key=lambda p: (_TEMPLATE in canonical_relative(context.get_relative_path(p)),
                                          len(p), p))
    for path in ranked:
        try:
            with open(path, 'rb') as handle:
                table = bsm_audit.parse_event_table(handle.read())
        except OSError:
            problems['audit_event files that could not be read'] += 1
            continue
        if table:
            return table, path
        problems['audit_event files with no event lines'] += 1
    return {}, ''


def _user_names(paths):
    """({uid: name}, {uid: [record files]}) from the local directory's user records in the extraction."""
    names = {}
    files = {}
    for path in paths:
        record = load_plist(path)
        if not isinstance(record, dict):
            continue
        uids, logins = record.get('uid'), record.get('name')
        if not (isinstance(uids, list) and uids and isinstance(logins, list) and logins):
            continue
        try:
            uid = int(str(uids[0]))
        except ValueError:
            continue
        names.setdefault(uid, set()).add(str(logins[0]))
        files.setdefault(uid, []).append(path)
    return {uid: ' / '.join(sorted(found)) for uid, found in names.items()}, files


def _other(tid, fields):
    name = bsm_audit.TOKEN_NAMES.get(tid, f'token 0x{tid:02x}')
    shown = ', '.join(f'{key}={", ".join(map(str, value)) if isinstance(value, list) else value}'
                      for key, value in fields.items())
    return f'{name}: {shown}'


def _row(record, events, users, relative):
    tokens = record['tokens']
    head_id, head = tokens[0]
    other = []
    if head_id == bsm_audit.AUT_OTHER_FILE32:
        return ((_time(head['seconds'], head['msec']), FILE_TOKEN, '', '') + ('',) * 18
                + ('', head['name'], '', '', '', relative))
    number = head['event']
    if number in events[0]:
        event, source = events[0][number], events[1]
    elif number in bsm_audit.BUNDLED_EVENTS:
        event, source = bsm_audit.BUNDLED_EVENTS[number], FROM_TABLE
    elif number in bsm_audit.EVENT_CONSTANTS:
        event, source = bsm_audit.EVENT_CONSTANTS[number], FROM_CONSTANT
    else:
        event, source = '', NOT_FOUND
    if head.get('modifier'):
        other.append(f'header: modifier={head["modifier"]}')
    if head.get('host'):
        other.append(f'header: host={head["host"]}')
    subject = ret = identity = None
    texts, paths, args, exec_args = [], [], [], []
    for tid, fields in tokens[1:]:
        if tid in _SUBJECTS and subject is None:
            subject = fields
        elif tid in _RETURNS and ret is None:
            ret = fields
        elif tid == bsm_audit.AUT_IDENTITY and identity is None:
            identity = fields
        elif tid == 0x28:
            texts.append(fields['text'])
        elif tid == 0x23:
            paths.append(fields['path'])
        elif tid in _ARGS:
            args.append(f'{fields["number"]} {fields["desc"]}=0x{fields["value"]:x}')
        elif tid == 0x3c:
            exec_args.extend(fields['strings'])
        elif tid == bsm_audit.AUT_TRAILER:
            continue
        else:
            other.append(_other(tid, fields))
    result = error = value = ''
    if ret is not None:
        result = 'success' if ret['status'] == 0 else 'failure'
        if ret['status']:
            name = bsm_audit.BSM_ERRNO.get(ret['status'])
            error = f'{ret["status"]} ({name})' if name else str(ret['status'])
        value = ret['value']
    who = ('',) * 12
    if subject is not None:
        who = (subject['auid'], users.get(subject['auid'], ''), subject['euid'], users.get(subject['euid'], ''),
               subject['ruid'], users.get(subject['ruid'], ''), subject['egid'], subject['rgid'],
               subject['pid'], subject['sid'], subject['port'], subject['addr'])
    signer = ('', '', '')
    if identity is not None:
        signer = (identity['signing_id'] + (' (truncated)' if identity['signing_id_truncated'] else ''),
                  identity['team_id'] + (' (truncated)' if identity['team_id_truncated'] else ''),
                  identity['cdhash'])
    return ((_time(head['seconds'], head['msec']), event, number, source, result, error, value) + who + signer
            + ('\n'.join(texts), '\n'.join(paths), '\n'.join(args), '\n'.join(exec_args), '\n'.join(other),
               relative))


def audit_rows(context):
    """(rows, files read) for every record in the trails among the files found."""
    problems = Counter()
    trails, tables, user_files = [], [], []
    for path in context.get_files_found():
        if os.path.isdir(path) or not os.path.isfile(path):
            continue
        relative = canonical_relative(context.get_relative_path(path))
        if relative.endswith('etc/security/audit_event'):
            tables.append(path)
        elif '/var/db/dslocal/nodes/Default/users/' in '/' + relative:
            user_files.append(path)
        elif _is_trail(path):
            trails.append(path)
        else:
            problems['files under var/audit that do not start with a header or file token, not read'] += 1
    table, table_path = _event_table(context, tables, problems)
    events = (table, FROM_IMAGE)
    users, user_sources = _user_names(user_files)
    trails, _skipped = unique_sources(context, trails, label='Audit Trail (BSM)')
    rows, read = [], []
    # /var/audit/current is a link to the open trail; a copy of it read as a file holds
    # records the trail it names also holds, so it is read last and those are dropped
    held = {}
    for path in sorted(trails, key=lambda p: os.path.basename(p) == 'current'):
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['trail files that could not be read'] += 1
            continue
        folder = held.setdefault(os.path.dirname(canonical_relative(relative)), set())
        is_link = os.path.basename(path) == 'current'
        kept = 0
        for record in bsm_audit.read_trail(data, problems):
            raw = data[record['offset']:record['offset'] + record['size']]
            if is_link and raw in folder:
                problems['records in a copy of the current link that a named trail also holds, not reported again'] += 1
                continue
            folder.add(raw)
            rows.append(_row(record, events, users, relative))
            kept += 1
        if kept or not is_link:
            read.append(path)
    folded = fold_view_rows(rows)
    if len(folded) != len(rows):
        problems['records another capture of the same trail also holds, reported once'] += len(rows) - len(folded)
    if problems:
        logfunc('Audit Trail (BSM): ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    logfunc(f'Audit Trail (BSM): {len(folded)} record(s) from {len(read)} trail file(s); event names from '
            + (context.get_relative_path(table_path) if table_path else 'the bundled tables')
            + f'; {len(users)} user ID(s) named from the extraction.')
    named = {row[index] for row in folded for index in (7, 9, 11) if row[index] in users}
    sources = read + ([table_path] if table_path and read else [])
    sources += sorted(path for uid in named for path in user_sources[uid])
    return folded, sources


@artifact_processor
def macosBsmAudit(context):
    rows, sources = audit_rows(context)
    return HEADERS, rows, '\n'.join(sources)


@artifact_processor
def macosBsmAuditAccounts(context):
    rows, sources = audit_rows(context)
    kept = [row for row in rows if row[2] in ACCOUNT_EVENTS]
    logfunc(f'Audit Trail Logins and Account Changes (BSM): {len(kept)} of {len(rows)} record(s).')
    return HEADERS, kept, '\n'.join(sources)
