"""code_signing_info rows from a macOS containers.sqlite3 database, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosContainerCodeSigning": {
        "name": "Container Manager Code Signing",
        "description": "Rows of the code_signing_info table in containers.sqlite3 under a Library/ContainerManager "
                       "folder, one row per code_signing_info row: the code-signing identifier, the application "
                       "identifier and the entitlement keys stored with it, and whether the row is marked invalid or "
                       "a placeholder.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-12",
        "last_update_date": "2026-10-12",
        "requirements": "none",
        "category": "Containers (macOS)",
        "notes": "Reads containers.sqlite3 in a Library/ContainerManager folder and reports one row per "
                 "code_signing_info row, joined to code_signing_data on its cs_info_id column, which the schema "
                 "declares a foreign key to code_signing_info(id). Code Signing ID is the code_signing_id_text "
                 "column; on all 285 rows of dleapp_macos_bigsur it is a dotted string whose first label is com. "
                 "Invalid, Placeholder and Registered by Caller are the invalid, placeholder and registered_by_caller "
                 "columns, shown as Yes or No. Child Bundles is the child_code_signing_id_text of each child_bundles "
                 "row whose parent is this entry, joined with ' | '. Application Identifier, App Sandbox and "
                 "Entitlements come from the binary property list in code_signing_data, which stores a dictionary of "
                 "entitlement keys under the key 'com.apple.MobileContainerManager.Entitlements': Application "
                 "Identifier is that dictionary's com.apple.application-identifier value when it is a string, "
                 "otherwise blank; App Sandbox its com.apple.security.app-sandbox value as Yes or No, the value as "
                 "text when it is neither True nor False, or blank when the key is absent; and Entitlements the "
                 "dictionary's keys, sorted, joined with ' | '. A blob that is not that property list, or a missing "
                 "code_signing_data row, leaves the three blank. A row shows the entry is present in the database, "
                 "not that the app ran. On dleapp_macos_bigsur (macOS 11.2.1) the 285 rows come from three "
                 "databases: 274 from the user's Library/ContainerManager, 9 from private/var/root and 2 from "
                 "private/var/db/locationd. Across them 86 rows carry an Application Identifier, App Sandbox is Yes "
                 "on 269 rows and blank on 16, and 747 distinct entitlement keys appear. Child Bundles is empty on "
                 "all 285 rows, the artifact finding no child_bundles row for any entry, and Invalid is No, "
                 "Placeholder is No and Registered by Caller is Yes on all 285. evidencelocker_macos14 and "
                 "mvs2026_macbookpro_macos15 hold no file the declared paths match. magnet2021_macos_bigsur holds six "
                 "containers.sqlite3-wal files and no containers.sqlite3 beside them; the artifact reads only the "
                 "main database, so it reports nothing there. When an extraction holds the same database at its own "
                 "path and again under System/Volumes/Data or System/Volumes/Update/mnt1 with identical bytes it is "
                 "read once, and when the copies differ a row both hold is reported once with both files in Source "
                 "File. Not exercised on real data and covered only by the unit test with constructed input: a "
                 "child_bundles entry, a row marked invalid or placeholder, a non-string application identifier, a "
                 "non-boolean app-sandbox value, a code_signing_data blob that is not the entitlements property list, "
                 "and a database present under two differing volume views.",
        "paths": ("*/Library/ContainerManager/containers.sqlite3*",),
        "output_types": "standard",
        "artifact_icon": "box",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 | 285 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (the declared paths match only "
                                       "containers.sqlite3-wal files, no containers.sqlite3)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (no member matches the declared paths)",
        },
    },
}

import plistlib
import sqlite3
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import fold_view_rows, unique_sources

_LABEL = 'Container Manager Code Signing'
_ENTITLEMENTS = 'com.apple.MobileContainerManager.Entitlements'
_APP_ID = 'com.apple.application-identifier'
_SANDBOX = 'com.apple.security.app-sandbox'
_INFO = ('SELECT i.id, i.code_signing_id_text, i.invalid, i.placeholder, i.registered_by_caller, d.data '
         'FROM code_signing_info i LEFT JOIN code_signing_data d ON d.cs_info_id = i.id ORDER BY i.id')
_CHILDREN = 'SELECT parent_id, child_code_signing_id_text FROM child_bundles ORDER BY id'


def entitlements(blob):
    """The entitlements dict stored for a code-signing identity, read from the binary property list the container
    manager keeps under the MobileContainerManager.Entitlements key; {} when the blob is absent or not that plist."""
    if not isinstance(blob, (bytes, bytearray)):
        return {}
    try:
        loaded = plistlib.loads(bytes(blob))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError, RecursionError):
        return {}
    inner = loaded.get(_ENTITLEMENTS) if isinstance(loaded, dict) else None
    return inner if isinstance(inner, dict) else {}


def _flag(value):
    return 'Yes' if value else 'No' if value == 0 else ''


def _entitlement_flag(entitlements_dict, key):
    if key not in entitlements_dict:
        return ''
    value = entitlements_dict[key]
    return 'Yes' if value is True else 'No' if value is False else str(value)


def code_signing_rows(database):
    """The rows for one open containers.sqlite3."""
    children = {}
    try:
        for parent_id, child in database.execute(_CHILDREN):
            children.setdefault(parent_id, []).append(str(child))
    except sqlite3.OperationalError:
        pass
    rows = []
    for info_id, csid, invalid, placeholder, registered, blob in database.execute(_INFO):
        ent = entitlements(blob)
        application_id = ent.get(_APP_ID)
        rows.append((csid, application_id if isinstance(application_id, str) else '',
                     _entitlement_flag(ent, _SANDBOX), ' | '.join(sorted(str(k) for k in ent)),
                     _flag(invalid), _flag(placeholder), _flag(registered),
                     ' | '.join(children.get(info_id, []))))
    return rows


@artifact_processor
def macosContainerCodeSigning(context):
    data_headers = ('Code Signing ID', 'Application Identifier', 'App Sandbox', 'Entitlements', 'Invalid',
                    'Placeholder', 'Registered by Caller', 'Child Bundles', 'Source File')
    found = [str(p) for p in context.get_files_found()
             if str(p).replace('\\', '/').endswith('/containers.sqlite3')]
    data_list, read, counts = [], [], Counter()
    for path in sorted(unique_sources(context, found, sidecars=('-wal', '-shm'), label=_LABEL)[0]):
        database = open_sqlite_db_readonly(path)
        if database is None:
            counts['databases that could not be opened'] += 1
            continue
        try:
            rows = code_signing_rows(database)
        except sqlite3.Error as error:
            counts[f'databases with no code-signing table ({type(error).__name__})'] += 1
            continue
        finally:
            database.close()
        relative = context.get_relative_path(path)
        data_list.extend(row + (relative,) for row in rows)
        if rows:
            read.append(path)
    if counts:
        logfunc(_LABEL + ': ' + ', '.join(f'{count} {kind}' for kind, count in sorted(counts.items())))
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
