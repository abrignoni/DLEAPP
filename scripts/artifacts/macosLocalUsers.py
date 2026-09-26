"""macOS local user accounts parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each local account on a Mac is a property list in the local directory node,
private/var/db/dslocal/nodes/Default/users/<name>.plist, whose values are arrays. This
reads those records, the times and failed-login count in the account policy data each
may carry, the Apple ID a record may be linked to, and whether the admin group of the
same node lists the account.
"""

import os
import plistlib
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import as_utc, canonical_relative, load_plist, unique_sources

_USERS = '/var/db/dslocal/nodes/Default/users/'
_ADMIN = '/var/db/dslocal/nodes/Default/groups/admin.plist'
_TEMPLATE = '/System/Library/Templates/Data/'

__artifacts_v2__ = {
    "macosLocalUsers": {
        "name": "Local User Accounts",
        "description": "Local user account records from the Mac's local directory node: "
                       "name, real name, UID, home and shell, the account policy times and "
                       "failed-login count, the password hint, a linked Apple ID and admin "
                       "group membership, where the record stores them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": "Read from the account records under private/var/db/dslocal/nodes/Default/users, one "
                 "property list per account whose values are arrays, the location Velociraptor's "
                 "MacOS.System.Users artifact reads "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/MacOS/System/Users.yaml#L9), "
                 "and from the admin group record, groups/admin.plist, of the same node. A copy of the "
                 "node under the system volume's System/Library/Templates/Data is not read: on "
                 "dleapp_macos_bigsur it held 109 account records and an admin group record, among "
                 "them root and service accounts but not Guest or thisisdfir. Records whose shell ends "
                 "in /false are not reported; Velociraptor's artifact by default leaves out any record "
                 "whose shell contains false "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/MacOS/System/Users.yaml#L10-L12, "
                 "https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/MacOS/System/Users.yaml#L42); "
                 "that was 106 of the 111 records on dleapp_macos_bigsur, and the run log counts them. "
                 "When a logical extraction holds the node under private/var and under "
                 "System/Volumes/Data/private/var, a copy byte-identical to the first is not read "
                 "again, and is counted in the run log; a copy that differs is read and reported too. "
                 "On the public MacBook Pro logical extraction (macOS 15.4 build 24E248, not a "
                 "registered corpus key) all 132 files of the System/Volumes/Data copy were "
                 "byte-identical to the private/var copy, the template tree held 131 files, and 4 of "
                 "the node's 131 account records were reported: root, _uucp, _mbsetupuser and the "
                 "account with UID 501. Name, Real Name, UID, GID, Home, Shell, Password Hint and "
                 "Generated UID are the first element of the record's name, realname, uid, gid, home, "
                 "shell, hint and generateduid values as stored, the element Velociraptor's artifact "
                 "reads for all of them but hint "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/MacOS/System/Users.yaml#L18-L24), "
                 "and Authentication Authority lists the record's authentication_authority values, one "
                 "per line, as stored. Admin is Yes when the users value of the admin group record in "
                 "the same node lists the name, No when it does not, and blank when no admin group "
                 "record was found; on dleapp_macos_bigsur it listed root and thisisdfir, and on the "
                 "MacBook Pro extraction root, _mbsetupuser and the UID 501 account. Created (UTC), "
                 "Password Last Set (UTC), Last Failed Login (UTC) and Failed Login Count are "
                 "creationTime, passwordLastSetTime, failedLoginTimestamp and failedLoginCount in the "
                 "property list the record stores as data in accountPolicyData, the times read as "
                 "seconds since 1970-01-01 UTC as Velociraptor's artifact reads them "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/MacOS/System/Users.yaml#L28-L38), "
                 "and a zero failedLoginTimestamp is shown blank. On dleapp_macos_bigsur thisisdfir's "
                 "creationTime falls 5 minutes 55 seconds after the InstallHistory.plist entry for "
                 "macOS 11.0.1 and its passwordLastSetTime 2.4 seconds after that; root carries "
                 "creationTime only, and _mbsetupuser and _uucp carry no accountPolicyData; on the "
                 "MacBook Pro extraction root and _uucp carry none and _mbsetupuser carries "
                 "passwordLastSetTime but no creationTime. Last Failed Login (UTC) was blank on every "
                 "row of both, because failedLoginTimestamp was 0 on the two records that carry it on "
                 "each. Linked Apple ID lists the full name of each identity under appleid.apple.com "
                 "in the record's LinkedIdentity, a property list stored as text, and Linked Identity "
                 "Timestamp (UTC) is that identity's timestamp value, a property-list date, shown when "
                 "one identity is listed; what event it records was not established. Only thisisdfir's "
                 "record on dleapp_macos_bigsur carries LinkedIdentity, and only the UID 501 account's "
                 "on the MacBook Pro extraction. Values not reported include ShadowHashData, "
                 "KerberosKeys, HeimdalSRPKey, the picture and jpegphoto values, and the node's other "
                 "groups.",
        "paths": ('*/var/db/dslocal/nodes/Default/users/*.plist',
                  '*/var/db/dslocal/nodes/Default/groups/admin.plist'),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 5 rows",
        },
    },
}


def first(record, key):
    """The first element of a record's array value, or '' when absent."""
    value = record.get(key)
    if isinstance(value, list):
        return value[0] if value else ''
    return value if value is not None else ''


def nested_plist(record, key):
    """The property list stored, as data or as text, in the first element of a value."""
    data = first(record, key)
    if isinstance(data, str):
        data = data.encode('utf-8')
    if not isinstance(data, (bytes, bytearray)) or not data:
        return {}
    try:
        parsed = plistlib.loads(bytes(data))
    except (plistlib.InvalidFileException, ValueError, TypeError, OverflowError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def unix_utc(value):
    """Seconds since 1970-01-01 UTC as an aware datetime; '' for zero or not a number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return ''
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def linked_apple_ids(record):
    """(names, timestamps) of the Apple ID identities the record's LinkedIdentity lists."""
    apple = nested_plist(record, 'LinkedIdentity').get('appleid.apple.com')
    identities = apple.get('linked identities') if isinstance(apple, dict) else None
    names, times = [], []
    for identity in identities if isinstance(identities, list) else []:
        if isinstance(identity, dict):
            names.append(str(identity.get('full name', '')))
            times.append(as_utc(identity.get('timestamp')))
    return names, times


def anchored(relative_path):
    """A relative path with forward slashes and one leading slash, so segment tests match at the root."""
    return '/' + relative_path.replace('\\', '/').lstrip('/')


def node_of(relative_path):
    """The path of the local node a users or groups plist belongs to."""
    path = anchored(canonical_relative(relative_path))
    at = path.find('/var/db/dslocal/nodes/Default/')
    return path[:at] if at >= 0 else os.path.dirname(path)


@artifact_processor
def macosLocalUsers(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Password Last Set (UTC)', 'datetime'),
                    ('Last Failed Login (UTC)', 'datetime'), 'Failed Login Count', 'Name',
                    'Real Name', 'UID', 'GID', 'Admin', 'Home', 'Shell', 'Password Hint',
                    'Linked Apple ID', ('Linked Identity Timestamp (UTC)', 'datetime'),
                    'Authentication Authority', 'Generated UID')
    found = [str(f) for f in context.get_files_found()]
    live = [f for f in found if _TEMPLATE not in anchored(context.get_relative_path(f))]
    skipped_template = len([f for f in found if os.path.isfile(f)]) - len(
        [f for f in live if os.path.isfile(f)])
    kept, _ = unique_sources(context, live, label='Local User Accounts')
    admins = {}
    admin_files = {}
    for path in kept:
        if anchored(context.get_relative_path(path)).endswith(_ADMIN):
            group = load_plist(path) or {}
            node = node_of(context.get_relative_path(path))
            admins[node] = {str(name) for name in group.get('users', []) or []}
            admin_files[node] = path
    data_list = []
    sources = []
    no_shell_false = 0
    for path in kept:
        relative = anchored(context.get_relative_path(path))
        if _USERS not in relative or not path.endswith('.plist'):
            continue
        record = load_plist(path)
        if not isinstance(record, dict):
            logfunc(f'Local User Accounts: could not read {relative} as a property list')
            continue
        shell = str(first(record, 'shell'))
        if shell.endswith('/false'):
            no_shell_false += 1
            continue
        sources.append(path)
        if node_of(relative) in admin_files and admin_files[node_of(relative)] not in sources:
            sources.append(admin_files[node_of(relative)])
        name = str(first(record, 'name'))
        policy = nested_plist(record, 'accountPolicyData')
        names, times = linked_apple_ids(record)
        admin_users = admins.get(node_of(relative))
        admin = '' if admin_users is None else ('Yes' if name in admin_users else 'No')
        data_list.append((
            unix_utc(policy.get('creationTime')), unix_utc(policy.get('passwordLastSetTime')),
            unix_utc(policy.get('failedLoginTimestamp')), policy.get('failedLoginCount', ''),
            name, str(first(record, 'realname')), str(first(record, 'uid')),
            str(first(record, 'gid')), admin, str(first(record, 'home')), shell,
            str(first(record, 'hint')), '\n'.join(names), times[0] if len(times) == 1 else '',
            '\n'.join(str(a) for a in record.get('authentication_authority', []) or []),
            str(first(record, 'generateduid'))))
    logfunc(f'Local User Accounts: {len(data_list)} accounts reported; {no_shell_false} records '
            f'whose shell ends in /false not reported; {skipped_template} files under '
            f'System/Library/Templates not read')
    data_list.sort(key=lambda row: (int(row[6]) if row[6].lstrip('-').isdigit() else 0, row[4]))
    return data_headers, data_list, '\n'.join(sources)
