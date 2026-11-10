"""Outlook autocomplete entries, from the IPM.Configuration.Autocomplete item of PST and OST
files and from the RoamCache Stream_Autocomplete files, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "outlookAutocomplete": {
        "name": "Outlook Autocomplete",
        "description": "Rows of the Outlook autocomplete stream, with nickname, display name, "
                       "email address and weight, from PST and OST files and from Outlook's "
                       "RoamCache folder.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads the autocomplete stream with the layout Microsoft Learn gives in Autocomplete Stream "
            "(Outlook MAPI reference, learn.microsoft.com/office/client-developer/outlook/mapi/"
            "autocomplete-stream, updated 2024-04-12) from the two places its Nickname cache page "
            "(nickname-cache) names for Outlook 2010 and 2013: PR_ROAMING_BINARYSTREAM "
            "(PidTagRoamingBinary on Learn) of the folder-associated item of class "
            "IPM.Configuration.Autocomplete, read in every file named .pst or .ost, in any case, "
            "read-only, with the vendored pstprobe 0.1.0, and the Stream_Autocomplete .dat files of a "
            "RoamCache folder, which that page calls a cache that is not written back. A stream whose major version is not 12, "
            "which the page says is not to be read, whose property types are not ones the page gives a "
            "layout for, or whose rows, extra information and 8 trailing metadata bytes do not end "
            "exactly at the end of the stream is not read and is logged; on the inputs in sample_data "
            "every stream was read. The page names PT_UNICODE but shows no layout for it; it is read "
            "like PT_STRING8, a byte count then UTF-16 text, and every stream read that way here ended "
            "exactly at its end. The .NK2 file of Outlook 2003 and 2007 is not read; no input here "
            "holds one. A byte-identical second copy of a file is read once. One row per entry of the "
            "stream. Item Modified and Item Created are PidTagLastModificationTime and "
            "PidTagCreationTime of the item that holds the stream, not times of any one entry, and are "
            "blank on rows from a RoamCache file; Item Modified was blank on the 5 rows from OST files, "
            "whose autocomplete items do not store it, and in "
            "windows11_arm_outlook_pst_more_known_20261110 it is 2026-11-10 16:36:27.229 UTC, 2 s "
            "after the kit's log starts the script that calls Application.Quit() and before the line "
            "that records Outlook as exited; the Nickname cache page says Outlook saves the stream on "
            "shutdown. Folder names the folder "
            "that holds the item. Rank is the entry's position in the stream, which the page says is "
            "sorted by weight, highest first. Nickname, Display Name, Email Address, Address Type, SMTP "
            "Address, Dropdown Display and Weight are PR_NICK_NAME_W, PR_DISPLAY_NAME_W, "
            "PR_EMAIL_ADDRESS_W, PR_ADDRTYPE_W, PR_SMTP_ADDRESS_W, PR_DROPDOWN_DISPLAY_NAME_W and "
            "PR_NICK_NAME_WEIGHT of the entry, blank when the entry does not store them as text or a "
            "number; the page says the weight goes up by 0x2000 (8192) when Outlook 2007 sends to or "
            "resolves a recipient and goes down over time. Store says which of the two stores the row "
            "came from. On the inputs in sample_data, 13 rows: Address Type was SMTP on 8, MAPIPDL on 3 "
            "and EX on 2; Dropdown Display equalled Display Name on 11; SMTP Address was blank on 4 and "
            "Email Address on 3. The two rows of cfreds_leakage_win7, one from the OST and one from the "
            "RoamCache file, hold the same values. In windows11_arm_outlook_pst_known_20261109 the two "
            "entries are the two contacts its fill log leaves in Contacts; the contact it moved to "
            "Deleted Items, the contact saved in its second PST and the four addresses its fill script "
            "put on unsent drafts have none. In windows11_arm_outlook_pst_more_known_20261110 the three "
            "entries are the contact its fill log resolved as a recipient and the two distribution "
            "lists it saved, each at weight 8192; the one-off addresses the same script resolved have "
            "no entry. The Nickname cache page lists resolving a name, picking a recipient from the "
            "address book and sending mail as what adds an entry; which actions added these entries "
            "was not established."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_more_known_20261110": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 3 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 4 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST and RoamCache | 2 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]', '*/RoamCache/Stream_Autocomplete*.dat'),
        "output_types": "standard",
        "artifact_icon": "at-sign",
    },
}

from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts import outlook_pst as O

# Microsoft Learn, "Autocomplete Stream": significant properties of a row
_NICKNAME = 0x6001001F           # PR_NICK_NAME_W
_DISPLAY_NAME = 0x3001001F       # PR_DISPLAY_NAME_W
_ADDRESS_TYPE = 0x3002001F       # PR_ADDRTYPE_W
_EMAIL_ADDRESS = 0x3003001F      # PR_EMAIL_ADDRESS_W
_SMTP_ADDRESS = 0x39FE001F       # PR_SMTP_ADDRESS_W
_DROPDOWN = 0x6003001F           # PR_DROPDOWN_DISPLAY_NAME_W
_WEIGHT = 0x60040003             # PR_NICK_NAME_WEIGHT


def _rows(data, item_times, folder, store, relative, counts):
    try:
        _minor, entries = O.parse_autocomplete(data)
    except O.AutocompleteError as exc:
        counts['autocomplete streams that do not follow the documented layout, not read'] += 1
        logfunc(f'Outlook Autocomplete: the stream in {relative} ({store}) was not read: {exc}')
        return []
    out = []
    for rank, entry in enumerate(entries, 1):
        def text(tag, entry=entry):
            value = entry.get(tag)
            return value if isinstance(value, str) else ''
        weight = entry.get(_WEIGHT)
        out.append(item_times + (folder, rank, text(_NICKNAME), text(_DISPLAY_NAME), text(_EMAIL_ADDRESS),
                    text(_ADDRESS_TYPE), text(_SMTP_ADDRESS), text(_DROPDOWN),
                    weight if isinstance(weight, int) else '', store, relative))
    return out


@artifact_processor
def outlookAutocomplete(context):
    data_headers = (('Item Modified', 'datetime'), ('Item Created', 'datetime'), 'Folder', ('Rank', 'number'), 'Nickname', 'Display Name',
                    'Email Address', 'Address Type', 'SMTP Address', 'Dropdown Display', ('Weight', 'number'),
                    'Store', 'Source File')
    rows, read, counts = [], [], Counter()
    reader = O.Reader(counts)
    for path in O.unique_files(context.get_files_found(), context.get_relative_path, counts):
        relative = context.get_relative_path(path)
        read.append(path)
        if not O.is_pst_name(path):
            try:
                with open(path, 'rb') as handle:
                    data = handle.read()
            except OSError as exc:
                counts['RoamCache files that could not be read'] += 1
                logfunc(f'Outlook Autocomplete: {relative} was not read: {exc}')
                continue
            rows.extend(_rows(data, ('', ''), '', 'RoamCache file', relative, counts))
            continue
        try:
            pst = O.P.open_pst(path)
        except (OSError,) + O.P.DAMAGE_ERRORS as exc:
            counts['files that could not be opened as PST or OST'] += 1
            logfunc(f'Outlook Autocomplete: {relative} was not read: {exc}')
            continue
        with pst:
            for folder, item in O.associated_items(pst, O.AUTOCOMPLETE_CLASS, counts):
                data = reader.get(item.pc, O.TAG_ROAMING_BINARY)
                if not isinstance(data, (bytes, bytearray)):
                    counts['autocomplete items with no stream'] += 1
                    continue
                times = (reader.time(reader.get(item.pc, O.TAG_MODIFIED_TIME)),
                         reader.time(reader.get(item.pc, O.TAG_CREATION_TIME)))
                rows.extend(_rows(bytes(data), times, folder,
                                  'PidTagRoamingBinary of ' + O.AUTOCOMPLETE_CLASS, relative, counts))
    if counts:
        logfunc('Outlook Autocomplete: ' + ', '.join(f'{n} {what}' for what, n in sorted(counts.items())))
    return data_headers, rows, '\n'.join(read)
