"""Shadow password entries Linux keeps in /etc/shadow, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxShadow": {
        "name": "Shadow Password Entries (shadow)",
        "description": "Account entries from Linux /etc/shadow files, with the password status and hash "
                       "algorithm read from the stored password field, the password field as stored, the "
                       "last-change and account-expiration dates, and the four password-aging periods.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Accounts (Linux)",
        "notes": "Reads each /etc/shadow the paths match, one row per entry line in file order. Each line is "
                 "split on colons and the first eight of the nine fields shadow(5) gives are read, "
                 "name:password:lastchange:min:max:warn:inactive:expire:reserved "
                 "(https://raw.githubusercontent.com/shadow-maint/shadow/4.17.4/man/shadow.5.xml); the ninth "
                 "(reserved) field and anything beyond it are ignored, and a line shorter than that leaves the "
                 "missing fields blank. An empty line is skipped; a line beginning with #, and a line with "
                 "fewer than two colon-separated fields or an empty name, is counted in the run log and not "
                 "reported. The backup file /etc/shadow- and the group shadow file /etc/gshadow are not read. "
                 "Account is the name field as stored, read as UTF-8 (a byte that is not valid UTF-8 shows as "
                 "the replacement character). "
                 "Password Field is the second field exactly as stored, kept whole. "
                 "Password Status uses this module's own labels for the field shapes shadow(5) describes: "
                 "'Set' when the field begins with $ (the hash itself is not checked for validity), 'Empty' "
                 "when it is the empty string (shadow(5) says no password is then required to authenticate, "
                 "and some applications may refuse access when the field is empty), 'Locked' when it begins "
                 "with ! (shadow(5): the password is locked and the rest of the field is the value before the "
                 "lock), and 'Other' for anything else. 'Other' covers a single * (shadow(5) gives * as a "
                 "string that is not a valid crypt(3) result, so the user cannot log in with a unix password "
                 "and may log in by other means) and the DES-family hashes descrypt, bsdicrypt and bigcrypt "
                 "that crypt(5) lists with no $ prefix; the raw field is always in the Password Field column. "
                 "Hash Algorithm names the crypt(3) scheme from the $id$ prefix of the hash, after any leading "
                 "! is removed and anything after a comma in the prefix is dropped (only the prefix decides "
                 "the name; the rest of the hash is not checked), from the table crypt(5) gives "
                 "(https://raw.githubusercontent.com/besser82/libxcrypt/v4.4.38/doc/crypt.5): $1$ md5crypt, "
                 "$2a$/$2b$/$2x$/$2y$ bcrypt, $3$ NT, $5$ sha256crypt, $6$ sha512crypt, $7$ scrypt, $sha1$ "
                 "sha1crypt, $y$ yescrypt, $gy$ gost-yescrypt, $md5$ SunMD5. It is blank when the field does "
                 "not begin with $ after any leading !, or when its prefix is not in this list; a blank does "
                 "not mean the field holds no hash, because the DES-family hashes have no $ prefix. "
                 "Last Password Change and Account Expiration are the third and eighth fields, each a count of "
                 "days since 1970-01-01, shown as that calendar date. An empty field, a value of 0 or less, a "
                 "value that is not a whole number of days, and a value past 9999-12-31, are shown blank in "
                 "both columns; shadow(5) says 0 in the last-change field means the user should change the "
                 "password at the next login and that 0 should not be used in the expiration field, and a "
                 "blank does not tell these apart. "
                 "Minimum Age, Maximum Age, Warning Period and Inactivity Period are the fourth to seventh "
                 "fields as stored, each a number of days (a duration, not a date), blank when empty. Source "
                 "File names the shadow file each row came from, because the paths can match more than one "
                 "shadow file in one image and no other column separates them. "
                 "Not exercised on the test file: the bcrypt, NT, scrypt, sha1crypt, yescrypt, gost-yescrypt "
                 "and SunMD5 prefixes, the DES-family hashes under 'Other', the ,rounds= form, a 0 date, a "
                 "date past 9999-12-31, an empty last-change field, a non-UTF-8 name, a skipped line, and more "
                 "than one shadow file; those paths follow the cited pages only. "
                 "On ubuntu2604_arm64_shadow_known_20261114 the constructed test file held 8 entries: two Set "
                 "(one sha512crypt, one sha256crypt), two Locked (one keeping an md5crypt hash after the !, "
                 "one a bare !), three Other (*) and one Empty. Hash Algorithm named sha512crypt, sha256crypt "
                 "and md5crypt on those three entries and was blank on the other five. Last Password Change "
                 "was filled on all 8 and Account Expiration on 1 (the sha256crypt entry). Minimum Age (days) "
                 "and Warning Period (days) each held one value on all 8 rows, 0 and 7. Maximum Age held 99999 "
                 "on 7 rows and 90 on 1, whose Inactivity Period held 14 while the other seven were blank. "
                 "Source File held etc/shadow on all 8, the one shadow file in the run.",
        "paths": ('*/etc/shadow',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "lock",
        "sample_data": {
            "ubuntu2604_arm64_shadow_known_20261114": "Ubuntu 26.04 LTS aarch64 | 8 rows (constructed test file)",
        },
    },
}

import datetime
import os
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc

_EPOCH = datetime.date(1970, 1, 1)

_ALGORITHMS = {
    '1': 'md5crypt',
    '2a': 'bcrypt',
    '2b': 'bcrypt',
    '2x': 'bcrypt',
    '2y': 'bcrypt',
    '3': 'NT',
    '5': 'sha256crypt',
    '6': 'sha512crypt',
    '7': 'scrypt',
    'sha1': 'sha1crypt',
    'y': 'yescrypt',
    'gy': 'gost-yescrypt',
    'md5': 'SunMD5',
}


def _lines(data):
    """The text lines of a file, without their line ends."""
    return [line.rstrip('\r') for line in data.decode('utf-8', errors='replace').split('\n')]


def shadow_records(data):
    """(records, counts): the colon-separated fields of each entry line of an /etc/shadow file, and a
    count of the lines left out, by reason."""
    records, counts = [], Counter()
    for line in _lines(data):
        if not line:
            continue
        if line[0] == '#':
            counts['shadow lines beginning with #, not reported'] += 1
            continue
        fields = line.split(':')
        if len(fields) < 2 or not fields[0]:
            counts['shadow lines with fewer than two fields or no name, not reported'] += 1
            continue
        records.append(fields)
    return records, counts


def password_status(field):
    """The login state the shadow password field encodes, per shadow(5)."""
    if field == '':
        return 'Empty'
    if field.startswith('$'):
        return 'Set'
    if field.startswith('!'):
        return 'Locked'
    return 'Other'


def hash_algorithm(field):
    """The crypt(3) scheme named by the $id$ prefix of a shadow hash, or '' when there is none."""
    hashed = field.lstrip('!')
    if not hashed.startswith('$'):
        return ''
    identifier = hashed.split('$')[1].split(',')[0]
    return _ALGORITHMS.get(identifier, '')


def _days_to_date(field):
    """Days since 1970-01-01 as a calendar date, or None when empty, 0 or less, non-numeric, or out
    of range."""
    if not (field.isascii() and field.isdigit()):
        return None
    days = int(field)
    if days <= 0:
        return None
    try:
        return _EPOCH + datetime.timedelta(days=days)
    except (OverflowError, ValueError):
        return None


def _field(fields, index):
    """The field at index as stored, or '' when the line is shorter than that."""
    return fields[index] if index < len(fields) else ''


def _read(path):
    with open(path, 'rb') as handle:
        return handle.read()


@artifact_processor
def linuxShadow(context):
    data_headers = (
        ('Last Password Change', 'date'),
        ('Account Expiration', 'date'),
        'Account',
        'Password Status',
        'Hash Algorithm',
        'Minimum Age (days)',
        'Maximum Age (days)',
        'Warning Period (days)',
        'Inactivity Period (days)',
        'Password Field',
        'Source File',
    )
    data_list = []
    read = []
    problems = Counter()
    files = [str(p) for p in context.get_files_found() if not os.path.isdir(p)]
    for path in sorted(p for p in files if os.path.basename(p) == 'shadow'):
        try:
            records, counts = shadow_records(_read(path))
        except OSError:
            problems['shadow files that could not be read'] += 1
            continue
        problems.update(counts)
        relative = context.get_relative_path(path)
        for fields in records:
            name = fields[0]
            password = fields[1]
            data_list.append((
                _days_to_date(_field(fields, 2)),
                _days_to_date(_field(fields, 7)),
                name,
                password_status(password),
                hash_algorithm(password),
                _field(fields, 3),
                _field(fields, 4),
                _field(fields, 5),
                _field(fields, 6),
                password,
                relative,
            ))
        if records:
            read.append(path)
    if problems:
        logfunc('Shadow Password Entries (shadow): '
                + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return data_headers, data_list, '\n'.join(read)
