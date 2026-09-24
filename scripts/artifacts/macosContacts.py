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
                 "Store is Main for the top-level database and Sources/ with the folder "
                 "name for one under Sources. Created (UTC) and Modified (UTC) are "
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
                 "(macOS 15.4, not a registered corpus key) the top-level database and one "
                 "Sources database each hold 1 contact and a second Sources database holds "
                 "none; Postal Addresses and URLs have no value on any MacBook Pro row. "
                 "The Users/ and System/Volumes/Data/Users/ copies there hold byte-identical "
                 "database files but different -wal files, and both are read, so each contact "
                 "appears twice, identical in every column but "
                 "Source File. All rows on each image come from one user, so User holds "
                 "one value there. When a logical extraction holds the same file under "
                 "Users/ and under System/Volumes/Data/Users/, a second copy whose database and "
                 "-wal file are both byte-identical to the first is not read again, and is "
                 "counted in the run log. Reference: Apple, "
                 "'NSDate', https://developer.apple.com/documentation/foundation/nsdate.",
        "sample_data": {
                           "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 4 rows",
                       },
        "paths": ('*/Library/Application Support/AddressBook/*AddressBook-v22.abcddb*',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "address-book",
    },
}

import re

from scripts.ilapfuncs import (artifact_processor, does_table_exist_in_db, get_sqlite_db_records,
                               logfunc)
from scripts.macos_plists import mac_absolute_utc, unique_sources, user_from_path

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
    return data_headers, data_list, '\n'.join(read)
