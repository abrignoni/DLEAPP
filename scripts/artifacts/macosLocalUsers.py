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
        "last_update_date": "2026-11-12",
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
                 "On the public MacBook Pro logical extraction (macOS 15.4 build 24E248, corpus key "
                 "mvs2026_macbookpro_macos15) all 132 files of the System/Volumes/Data copy were "
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
                 "on the MacBook Pro extraction. The record's ShadowHashData fields and its picture and "
                 "jpegphoto values are reported by the Local User Password Hashes and Local User "
                 "Pictures artifacts. Values not reported include KerberosKeys, HeimdalSRPKey and the "
                 "node's other groups.",
        "paths": ('*/var/db/dslocal/nodes/Default/users/*.plist',
                  '*/var/db/dslocal/nodes/Default/groups/admin.plist'),
        "output_types": ["standard"],
        "artifact_icon": "users",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 5 rows",
        },
    },
    "macosLocalUserPictures": {
        "name": "Local User Pictures",
        "description": "The picture path and the embedded image stored in the macOS local account "
                       "records that Local User Accounts reports, where a record carries them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-12",
        "last_update_date": "2026-11-12",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": (
            'One row per macOS local account that stores a picture path or an embedded image: a record under '
            "private/var/db/dslocal/nodes/Default/users, not the system volume's template copy, whose shell "
            'does not end in /false, the same records Local User Accounts reports. A byte-identical copy of a '
            'record under another volume view is read once; a copy that differs is read too and gives its own '
            "row, which no tested image held. Name, Real Name and UID are the first element of the record's "
            "name, realname and uid values as stored. Picture Path is the first element of the record's picture"
            ' value as stored; on the tested images it was a path under /Library/User Pictures or '
            '/System/Library/CoreServices, the artifact does not read the file at that path, and whether it '
            'shows the same picture as the embedded image was not established. Account Picture is the first '
            "element of the record's jpegphoto value when it holds bytes, saved to the report's media folder; "
            "Embedded Picture Format is the MIME type read from those bytes' leading bytes and Embedded Picture"
            ' Size (bytes) is their length. Despite the jpegphoto key name, the stored bytes were TIFF on '
            "dleapp_macos_bigsur and PNG on mvs2026_macbookpro_macos15, one record each, and the path's own "
            'extension differed from them. JPEG, PNG, TIFF, GIF and HEIC signatures are checked; only TIFF and '
            'PNG occurred on the tested images, and the other three are untested. Bytes with none of those '
            'signatures are still saved, with a .bin extension and a blank Embedded Picture Format, which no '
            'tested image held. A TIFF picture may not display in the HTML report or in LAVA; the file is in '
            "the report's media folder either way. Account Picture, Embedded Picture Format and Embedded "
            'Picture Size are blank when the record holds no jpegphoto bytes, as for the Guest record on '
            'dleapp_macos_bigsur, which has no jpegphoto key, and the one account on adams_macbookpro_macos26, '
            'whose jpegphoto value is an empty string; both carried a picture path only. On the three images '
            'with rows no record left out for a shell ending in /false carried a picture or jpegphoto value. On'
            ' magnet2021_macos_bigsur the pattern matched only the 218 template copies, which are not read; on '
            'evidencelocker_macos14 it matched no file; neither gave a row.'
        ),
        "paths": ('*/var/db/dslocal/nodes/Default/users/*.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (only template copies matched, 218 files, not read)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 2 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no file matched the pattern)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 1 row",
            "adams_macbookpro_macos26": "macOS 26.2 | 1 row",
        },
    },
    "macosLocalUserPasswordHashes": {
        "name": "Local User Password Hashes",
        "description": "The fields the reported macOS local account records store in ShadowHashData: "
                       "scheme name, iterations, salt and the entropy or verifier bytes, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-12",
        "last_update_date": "2026-11-12",
        "requirements": "none",
        "category": "Accounts (macOS)",
        "notes": (
            'One row per scheme key a macOS local account stores in ShadowHashData: a record under '
            "private/var/db/dslocal/nodes/Default/users, not the system volume's template copy, whose shell "
            'does not end in /false, the same records Local User Accounts reports. A byte-identical copy of a '
            'record under another volume view is read once; a copy that differs is read too and gives its own '
            "row, which no tested image held. Name, Real Name and UID are the first element of the record's "
            "name, realname and uid values as stored. The artifact name follows the record's ShadowHashData "
            "key. ShadowHashData is the first element of the record's ShadowHashData value, a property list "
            '(binary on the tested images) whose keys are scheme names; each key whose value is a dictionary '
            'gives a row, and a key holding any other kind of value gives none, which no tested image held. '
            "Scheme is the key name as stored. Iterations is the scheme's iterations value as stored and Salt "
            '(hex) its salt value as hex. Value Field is the name of the field the scheme holds as bytes, '
            'entropy or verifier, whichever is present, and entropy when both are, and Value (hex) is that '
            "field's bytes as hex; other fields a scheme may hold are not reported, and on the tested images "
            'each scheme held only iterations, salt and one of those two. The scheme and field names in the '
            "rows are the record's own and values are shown as stored or as hex; nothing here is interpreted, "
            'and what a field is used for beyond its name is not described here. A row shows that the record '
            'stores these fields; it does not establish that a password is set or in use for the account, and '
            'the Guest record on dleapp_macos_bigsur carried both scheme keys. On dleapp_macos_bigsur, '
            'mvs2026_macbookpro_macos15 and adams_macbookpro_macos26, 5 of the 13 reported accounts carried '
            'ShadowHashData, 2, 2 and 1; each held two keys, SALTED-SHA512-PBKDF2 with an entropy field of 128 '
            'bytes (256 hex characters) and SRP-RFC5054-4096-SHA512-PBKDF2 with a verifier field of 512 bytes '
            '(1,024 hex characters), each with a 32-byte salt (64 hex characters) and an integer iterations '
            'value. The other 8 accounts carried no ShadowHashData and gave no row. On magnet2021_macos_bigsur '
            'the pattern matched only the 218 template copies, which are not read; on evidencelocker_macos14 it'
            ' matched no file; neither gave a row.'
        ),
        "paths": ('*/var/db/dslocal/nodes/Default/users/*.plist',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "magnet2021_macos_bigsur": "macOS 11.2.1 | 0 rows (only template copies matched, 218 files, not read)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 4 rows",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no file matched the pattern)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 4 rows",
            "adams_macbookpro_macos26": "macOS 26.2 | 2 rows",
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


from scripts.ilapfuncs import check_in_embedded_media  # noqa: E402

_IMAGE_MAGIC = (
    (b'\xff\xd8\xff', 'image/jpeg', 'jpg'),
    (b'\x89PNG\r\n\x1a\n', 'image/png', 'png'),
    (b'MM\x00*', 'image/tiff', 'tiff'),
    (b'II*\x00', 'image/tiff', 'tiff'),
    (b'GIF87a', 'image/gif', 'gif'),
    (b'GIF89a', 'image/gif', 'gif'),
)
_SHADOW_VERIFIER_FIELDS = ('entropy', 'verifier')


def _image_kind(data):
    """(mime type, extension) from an image's leading bytes, or ('', '') when unrecognised.

    An ISO base media file (HEIC among them) carries 'ftyp' at offset 4 and its brand after it.
    """
    if not isinstance(data, (bytes, bytearray)) or len(data) < 12:
        return '', ''
    data = bytes(data)
    for magic, mime, extension in _IMAGE_MAGIC:
        if data.startswith(magic):
            return mime, extension
    if data[4:8] == b'ftyp':
        brand = data[8:12]
        if brand in (b'heic', b'heix', b'mif1', b'heis', b'hevc', b'heim', b'heis'):
            return 'image/heic', 'heic'
    return '', ''


def _account_records(context, label):
    """(path, relative path, record) for each account the Local User Accounts artifact reports: a
    record under the users folder, not the system template copy, whose shell does not end in /false,
    one per byte-identical copy across volume views."""
    found = [str(handle) for handle in context.get_files_found()]
    live = [handle for handle in found
            if handle.endswith('.plist')
            and _USERS in anchored(context.get_relative_path(handle))
            and _TEMPLATE not in anchored(context.get_relative_path(handle))]
    kept, _skipped = unique_sources(context, live, label=label)
    for path in kept:
        record = load_plist(path)
        if not isinstance(record, dict):
            continue
        if str(first(record, 'shell')).endswith('/false'):
            continue
        yield path, anchored(context.get_relative_path(path)), record


@artifact_processor
def macosLocalUserPictures(context):
    data_headers = (('Account Picture', 'media'), 'Name', 'Real Name', 'UID', 'Picture Path',
                    'Embedded Picture Format', 'Embedded Picture Size (bytes)')
    data_list, sources = [], []
    for path, _relative, record in _account_records(context, 'Local User Pictures'):
        name = str(first(record, 'name'))
        picture_path = str(first(record, 'picture'))
        photo = first(record, 'jpegphoto')
        if not isinstance(photo, (bytes, bytearray)) or not photo:
            photo = b''
        if not picture_path and not photo:
            continue
        mime, extension = _image_kind(photo)
        media = ''
        if photo:
            media = check_in_embedded_media(path, bytes(photo), name=f'{name} account picture',
                                            force_type=mime or None,
                                            force_extension=extension or 'bin') or ''
        data_list.append((media, name, str(first(record, 'realname')), str(first(record, 'uid')),
                          picture_path, mime, len(photo) if photo else ''))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def macosLocalUserPasswordHashes(context):
    data_headers = ('Name', 'Real Name', 'UID', 'Scheme (as stored)', 'Iterations (as stored)',
                    'Salt (hex)', 'Value Field (as stored)', 'Value (hex)')
    data_list, sources = [], []
    for path, _relative, record in _account_records(context, 'Local User Password Hashes'):
        shadow = nested_plist(record, 'ShadowHashData')
        if not shadow:
            continue
        name = str(first(record, 'name'))
        real = str(first(record, 'realname'))
        uid = str(first(record, 'uid'))
        added = False
        for scheme in sorted(shadow):
            fields = shadow.get(scheme)
            if not isinstance(fields, dict):
                continue
            field = next((candidate for candidate in _SHADOW_VERIFIER_FIELDS
                          if isinstance(fields.get(candidate), (bytes, bytearray))), '')
            salt = fields.get('salt')
            data_list.append((
                name, real, uid, str(scheme), str(fields.get('iterations', '')),
                bytes(salt).hex() if isinstance(salt, (bytes, bytearray)) else '',
                field, bytes(fields[field]).hex() if field else ''))
            added = True
        if added:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
