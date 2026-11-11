"""Contacts in the macOS AddressBook stores, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosContacts": {
        "name": "Contacts",
        "description": "Contact cards in each user's AddressBook-v22.abcddb stores, the "
                       "main store and each store under Sources, with names, organization, "
                       "phone numbers, email, postal and web addresses, notes and the "
                       "stored creation and modification dates.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "none",
        "category": "Contacts (macOS)",
        "notes": "Reads each user's AddressBook-v22.abcddb under ~/Library/Application "
                 "Support/AddressBook and the one in each Sources folder beneath it, one "
                 "row per ZABCDRECORD row whose entity is ABCDContact in Z_PRIMARYKEY. "
                 "Store is Main for the top-level database and Sources/ with the folder name for "
                 "one under Sources. Store and User do not separate the Users/ and "
                 "System/Volumes/Data/Users/ copies of one database, which are both read when they differ; a contact identical in every other column in both is reported once, and Source File names each file that held it, one per line. Created (UTC) and "
                 "Modified (UTC) are "
                 "ZCREATIONDATE and ZMODIFICATIONDATE read as seconds since 00:00:00 UTC "
                 "on 1 January 2001, the reference date Apple documents for NSDate; read "
                 "that way the 4 contacts on dleapp_macos_bigsur were created between "
                 "December 2020 and February 2021, where the 1970 epoch would place the "
                 "earliest in 1989. Phone Numbers, Email Addresses, Postal Addresses and "
                 "URLs join the rows of ZABCDPHONENUMBER, ZABCDEMAILADDRESS, "
                 "ZABCDPOSTALADDRESS and ZABCDURLADDRESS that name the contact as ZOWNER, "
                 "in ZORDERINGINDEX order, each with its ZLABEL; a label stored in the "
                 "_$!<...>!$_ form is shown without that wrapper. Postal Addresses joins the "
                 "street, city, state, postal code and country fields with commas, except that "
                 "the state and postal code are separated by a space. "
                 "Note is the ZTEXT of the ZABCDNOTE row for the contact. The name, "
                 "organization, department, job title and unique ID columns are the "
                 "ZABCDRECORD fields of those names as stored. On dleapp_macos_bigsur the "
                 "top-level database and one Sources database each hold 2 contacts, 4 rows "
                 "in all, and Middle Name, Nickname, Department, Job Title and Note have "
                 "no value on any of them. On the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15) the top-level database and one "
                 "Sources database each hold 1 contact and a second Sources database holds "
                 "none; Postal Addresses and URLs have no value on any MacBook Pro row. "
                 "The Users/ and System/Volumes/Data/Users/ copies there hold byte-identical "
                 "database files but different -wal files, and both are read; each of the 2 contacts is in both and is reported once, with both files in Source File. All rows on each image come from one user, so User holds "
                 "one value there. When a logical extraction holds the same file under "
                 "Users/ and under System/Volumes/Data/Users/, a second copy whose database and "
                 "-wal file are both byte-identical to the first is not read again, and is "
                 "counted in the run log. Reference: Apple, "
                 "'NSDate', https://developer.apple.com/documentation/foundation/nsdate."
                 " Copies of one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ "
                 "are all read; a row identical in every other column in more than one copy is reported as "
                 "often as the copy holding it most often holds it, normally once, and its Source File "
                 "lists each file that held it, one per line.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 4 rows",
                           "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 3 rows",
                           "mvs2026_macbookpro_macos15": "macOS 15.4 | 2 rows",
                       },
        "paths": ('*/Library/Application Support/AddressBook/*AddressBook-v22.abcddb*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book",
    },
    "macosContactGroups": {
        "name": "Contact Groups",
        "description": "Groups in each user's AddressBook-v22.abcddb stores, with the stored dates and the "
                       "contacts each group lists as members.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Contacts (macOS)",
        "notes": (
            "Reads each user's AddressBook-v22.abcddb under ~/Library/Application Support/AddressBook and the "
            'one in each Sources folder beneath it, one row per ZABCDRECORD row whose entity is ABCDGroup in '
            'Z_PRIMARYKEY. Group Name and Unique ID are ZNAME and ZUNIQUEID as stored. Created (UTC) and '
            'Modified (UTC) are ZCREATIONDATE and ZMODIFICATIONDATE read as seconds since 00:00:00 UTC on 1 '
            'January 2001, the reference date Apple documents for NSDate '
            '(https://developer.apple.com/documentation/foundation/nsdate). Members lists the contacts that the'
            " store's contact-to-group join table links to the group. Each member is shown by its first, middle"
            ' and last name. When it has none, its organization is shown. When it has neither, or the linked '
            'record is not an ABCDContact row, it is shown as (record N), N being its Z_PK in that store; one '
            'member on the tested images was shown that way. Members are listed in the order the store returned'
            " them, joined with '; '. Member Count is the number of those links. Core Data names that table and"
            ' its columns with entity numbers that differ between stores, so it is found by shape: a table '
            'named Z_<number>PARENTGROUPS with one Z_<number>CONTACTS column and one Z_<number>PARENTGROUPS '
            'column, which ended in the digit 1 in every tested store. When no such table is found Member Count'
            ' and Members are blank and the run log says so; that did not happen on the tested images. The '
            'group-to-group table is not read, so a group inside a group is not shown; that table held no rows '
            'in any store on the five tested images. Rows of the ABCDSubscribedGroup entity are not read; no '
            'tested store held one. Who or what created a group is not established. On the five tested images '
            'each store that held a group held exactly one, and that group listed every contact in its store. '
            'The same group name recurred across unrelated images. No tested image held a group that listed '
            "only some of a store's contacts, so that case is unexercised. Store is Main for the top-level "
            'database and Sources/ with the folder name for one under Sources; every group on the five tested '
            'images came from a store under Sources, with 0 to 7 members. On the two logical images two volume '
            'views of a store (Users/ beside System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/) '
            'held the same group with different Modified values, so each group is reported twice there, once '
            'per file. User is the folder after Users in the path, root for a store under private/var/root, and'
            ' blank otherwise. User held one value on every row of each tested image. A copy of a store under '
            'System/Volumes/Data/ or System/Volumes/Update/mnt1/ whose database and -wal file are both '
            'byte-identical to one already read is not read again and the run log counts it; a row identical in'
            ' every other column in copies that differ is reported once, with each file in Source File, one per'
            ' line. No group on the tested images was folded this way.'
        ),
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 2 rows (1 group, reported from two volume views)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 1 row",
            "evidencelocker_macos14": "macOS 14.6.1 | 1 row",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 4 rows (2 groups, reported from two volume views)",
            "adams_macbookpro_macos26": "macOS 26.2 | 3 rows",
        },
        "paths": ('*/Library/Application Support/AddressBook/*AddressBook-v22.abcddb*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
    },
}

import re

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db, get_sqlite_db_records,
                               logfunc)
from scripts.macos_plists import (fold_view_rows, mac_absolute_utc, unique_sources,
                                  user_from_path)

_CONTACTS = '''
    SELECT r.Z_PK, r.ZCREATIONDATE, r.ZMODIFICATIONDATE, r.ZFIRSTNAME, r.ZMIDDLENAME, r.ZLASTNAME,
           r.ZNICKNAME, r.ZORGANIZATION, r.ZDEPARTMENT, r.ZJOBTITLE, r.ZUNIQUEID
    FROM ZABCDRECORD r JOIN Z_PRIMARYKEY e ON e.Z_ENT = r.Z_ENT
    WHERE e.Z_NAME = 'ABCDContact'
    ORDER BY r.ZCREATIONDATE
'''

_DETAILS = (
    ('ZABCDPHONENUMBER', 'ZOWNER', "ZFULLNUMBER"),
    ('ZABCDEMAILADDRESS', 'ZOWNER', "ZADDRESS"),
    ('ZABCDPOSTALADDRESS', 'ZOWNER',
     "trim(coalesce(ZSTREET, '') || ', ' || coalesce(ZCITY, '') || ', ' || coalesce(ZSTATE, '') "
     "|| ' ' || coalesce(ZZIPCODE, '') || ', ' || coalesce(ZCOUNTRYNAME, ''), ', ')"),
    ('ZABCDURLADDRESS', 'ZOWNER', "ZURL"),
)


def _label(label):
    """A stored label, with Apple's _$!<...>!$_ wrapper removed."""
    if not label:
        return ''
    match = re.fullmatch(r'_\$!<(.*)>!\$_', str(label))
    return match.group(1) if match else str(label)


def _details(path, table, owner, value):
    """{owner pk: 'label: value; ...'} for one detail table, in stored order."""
    if not does_table_exist_in_db(path, table):
        return {}
    rows = get_sqlite_db_records(
        path, f'SELECT {owner}, ZLABEL, {value} FROM {table} ORDER BY {owner}, ZORDERINGINDEX')
    joined = {}
    for row in rows:
        if row[2]:
            label = _label(row[1])
            joined.setdefault(row[0], []).append(f'{label}: {row[2]}' if label else str(row[2]))
    return {key: '; '.join(values) for key, values in joined.items()}


def _store(relative):
    match = re.search(r'/Sources/([^/]+)/', '/' + relative.replace('\\', '/'))
    return f'Sources/{match.group(1)}' if match else 'Main'


@artifact_processor
def macosContacts(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'First Name',
                    'Middle Name', 'Last Name', 'Nickname', 'Organization', 'Department',
                    'Job Title', 'Phone Numbers', 'Email Addresses', 'Postal Addresses', 'URLs',
                    'Note', 'Unique ID', 'Store', 'User', 'Source File')
    data_list = []
    read = []
    stores = [p for p in context.get_files_found() if str(p).endswith('.abcddb')]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label='Contacts')
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ZABCDRECORD'):
            logfunc(f'Contacts: no ZABCDRECORD table read from {relative}')
            continue
        read.append(path)
        details = [_details(path, *spec) for spec in _DETAILS]
        notes = {}
        if does_table_exist_in_db(path, 'ZABCDNOTE'):
            notes = {row[0]: row[1] for row in get_sqlite_db_records(
                path, 'SELECT ZCONTACT, ZTEXT FROM ZABCDNOTE WHERE ZTEXT IS NOT NULL')}
        for row in get_sqlite_db_records(path, _CONTACTS):
            pk = row[0]
            data_list.append((mac_absolute_utc(row[1]), mac_absolute_utc(row[2]),
                              *(row[i] or '' for i in range(3, 10)),
                              *(detail.get(pk, '') for detail in details), notes.get(pk, ''),
                              row[10] or '', _store(relative), user_from_path(relative), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


_GROUPS = '''
    SELECT r.Z_PK, r.ZCREATIONDATE, r.ZMODIFICATIONDATE, r.ZNAME, r.ZUNIQUEID
    FROM ZABCDRECORD r JOIN Z_PRIMARYKEY e ON e.Z_ENT = r.Z_ENT
    WHERE e.Z_NAME = 'ABCDGroup'
    ORDER BY r.ZCREATIONDATE
'''


def _member_links(path):
    """[(contact pk, group pk)] from the contact-to-group join table, or None when none is found.

    Core Data names the table and its columns with entity numbers that differ between
    stores (Z_21PARENTGROUPS with Z_21CONTACTS and Z_18PARENTGROUPS1 in one, Z_22PARENTGROUPS
    with Z_22CONTACTS and Z_19PARENTGROUPS1 in another), so they are found by shape.
    """
    tables = get_sqlite_db_records(
        path, "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'Z\\_%PARENTGROUPS' ESCAPE '\\'")
    for (table,) in tables:
        if not re.fullmatch(r'Z_\d+PARENTGROUPS', table):
            continue
        columns = [row[1] for row in get_sqlite_db_records(path, f'PRAGMA table_info("{table}")')]
        contact = [c for c in columns if re.fullmatch(r'Z_\d+CONTACTS', c)]
        group = [c for c in columns if re.fullmatch(r'Z_\d+PARENTGROUPS\d*', c)]
        if len(contact) == 1 and len(group) == 1:
            return [(row[0], row[1]) for row in get_sqlite_db_records(
                path, f'SELECT "{contact[0]}", "{group[0]}" FROM "{table}"')]
    return None


def _contact_names(path):
    """{contact pk: display text} from the name and organization fields, as stored."""
    names = {}
    for row in get_sqlite_db_records(path, _CONTACTS):
        person = ' '.join(str(part) for part in (row[3], row[4], row[5]) if part)
        names[row[0]] = person or str(row[7] or '')
    return names


@artifact_processor
def macosContactGroups(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Modified (UTC)', 'datetime'), 'Group Name', 'Member Count',
                    'Members', 'Unique ID', 'Store', 'User', 'Source File')
    data_list = []
    read = []
    stores = [p for p in context.get_files_found() if str(p).endswith('.abcddb')]
    paths, _skipped = unique_sources(context, stores, sidecars=('-wal',), label='Contact Groups')
    for path in paths:
        relative = context.get_relative_path(path)
        if not does_table_exist_in_db(path, 'ZABCDRECORD'):
            logfunc(f'Contact Groups: no ZABCDRECORD table read from {relative}')
            continue
        read.append(path)
        groups = get_sqlite_db_records(path, _GROUPS)
        if not groups:
            continue
        links = _member_links(path)
        if links is None:
            logfunc(f'Contact Groups: no contact-to-group table found in {relative}; members not listed')
        names = _contact_names(path)
        for row in groups:
            members = [contact for contact, group in (links or []) if group == row[0]]
            listed = '; '.join(names.get(contact, f'(record {contact})') or f'(record {contact})'
                               for contact in members)
            data_list.append((mac_absolute_utc(row[1]), mac_absolute_utc(row[2]), row[3] or '',
                              '' if links is None else len(members), listed, row[4] or '',
                              _store(relative), user_from_path(relative), relative))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
