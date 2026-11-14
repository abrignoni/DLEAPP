"""Notifications websites showed through their service worker, from the Platform Notifications
database of Chromium-based browser profiles, for DLEAPP.

Ported from ALEAPP's chromiumNotifications.py; the fields are read against Chromium's
notification_database_data.proto with scripts/chromium/web_storage.proto_items rather than a
schema-less decoder, and browser, profile and user come from scripts/chromium/browser_profiles.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "chromiumWebNotifications": {
        "name": "Chromium Web Notifications",
        "description": "Notifications stored for websites' service workers in the Platform Notifications database of Chromium-based browser profiles: site, title, body, tag, when each was created, clicked and closed, and whether its record is live or deleted.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the Platform Notifications database of each Chromium-based browser profile that scripts/chromium/browser_profiles locates (Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi, Opera, Opera GX, 360 Safe Browser and webOS webbrowser) on Windows, macOS and Linux, where Chromium stores the notifications a site's service worker asks it to show (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/blink_notification_service_impl.cc#L296-L352). The same message has flags for a notification shown by the browser and for a scheduled notification not yet displayed (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L87-L93); those two flags are not reported. Format and meanings come from Chromium at commit 77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784. The folder is read with the vendored ccl_leveldb, and State comes from the newest version of each key: LevelDB orders the versions of a key by sequence number (https://github.com/google/leveldb/blob/bb74ef739973a70ca9f0d90788a1da89b788c0ad/db/dbformat.cc#L47-L63). A folder that cannot be read is skipped and named in the run log, and a record that does not decode keeps its State, Browser, Profile, User and Source File with the other columns blank, and the log names its folder. Each notification is a key DATA:, the site's origin identifier, a zero byte and the notification id (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L33, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L45, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L81-L87), holding a NotificationDatabaseDataProto (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L15). Its fields are read by their numbers in that message (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L23-L36, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L41-L52, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L59-L85) with scripts/chromium/web_storage, not with a schema-less decoder. Site is the stored origin; Title, Body, Tag, Icon URL and Image URL are the notification's own fields, decoded as UTF-8, and Action Buttons the stored titles of its actions (a button or a text input), joined with ; . The icon and image are reported as URLs: the cached image files are not looked up. Created is when the notification was first requested to be shown (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/public/browser/notification_database_data.h#L81-L82), stored as microseconds since 1601-01-01 UTC although the field is named creation_time_millis (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_conversions.cc#L62-L63); in the known data below it fell inside the mint window, and read as milliseconds since 1970 the value is past the year 9999. Site Timestamp is the notification's timestamp field, in the same unit (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_conversions.cc#L131-L132); the test page set none. Clicks and Action Button Clicks are the stored counts. First Click, Last Click and Closed are Created plus the stored delays, measured from Created when the click or close is recorded (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L142-L145, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L247-L251) and written in milliseconds (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_conversions.cc#L284-L295). Closed Reason is the stored ClosedReason with its name, USER, DEVELOPER or UNKNOWN (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L16-L20, https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database_data.proto#L36); a stored number outside those three is shown as unknown with the number. It defaults to UNKNOWN (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/public/browser/notification_database_data.h#L95-L96) and Chromium writes USER when it records a close (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L247-L251); what sets off that record in a desktop browser was not traced, so USER is not by itself evidence that a person closed the notification. State is Live when the newest version of the key is not a deletion. Deleted, value kept: the newest version is a deletion and an earlier version is still in the files; the columns come from the last version stored before it. Deleted, key only: no earlier version is left; the notification's own columns are blank and State, Browser, Profile, User and Source File are filled. Chromium deletes a notification's key in DeleteNotificationData (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L343-L360) and in a deletion over several keys (https://github.com/chromium/chromium/blob/77a2fd4e2e4c2937b5fc24e5f5e88f9e2f999784/content/browser/notifications/notification_database.cc#L533-L534); which actions in a desktop browser reach those calls was not traced, so a Deleted row is not evidence of a click, a close or a person's action. A row records that the browser stored the notification for that site; it does not show that a person saw it. Browser, Profile and User come from the path, as in the other Chromium artifacts, and Source File names the folder each row came from. On a Mac logical extraction a profile can sit under Users/ and under System/Volumes/Data/Users/; a folder whose copy under the second path holds the same files with the same bytes is read once, as it was on mvs2026_macbookpro_macos15. Ported from ALEAPP's Chromium Web Notifications; its Android known data and its cached-image lookup were not repeated here. Known data (windows11_arm_chrome_fs_notifications_known_20261114, Chrome 157.0.8103.51 on Windows 11 ARM64, a fresh profile and one local test page at http://localhost:8765 that showed two persistent notifications through its service worker, with permission from the NotificationsAllowedForUrls policy; minted 2026-11-14 07:52:26 to 07:53:12 UTC, Chrome then force-closed; README beside the image): both notifications were read with the title, body and tag written, State Live, Created at 07:52:35 UTC and Site Timestamp within 10 milliseconds of Created. First Click, Last Click, Closed, Icon URL, Image URL and Action Buttons held no value on any of the 2 rows, as the page clicked and closed nothing and set no icon, image or button. Site, Clicks, Action Button Clicks, Closed Reason, State, Browser, Profile and User held one value on all 2 rows: the test site, 0, 0, UNKNOWN (2), Live, Google Chrome, Default and kd. On the corpus images the Platform Notifications databases of hexordia_mvs2025_win11 (Microsoft Edge), mvs2026_macbookpro_macos15 (Google Chrome) and ou_ransomware_server2022 (two Microsoft Edge profiles) held no record at all: their log files were 0 bytes and they had no table file. Not exercised by the tested images: a Deleted row, a key with more than one version, a table file (the known data was read from one log file), a click or a close, action buttons, an icon or image URL, a timestamp set by the site, a record that does not decode, a folder that cannot be read, a macOS or Linux profile holding records, and records from browsers other than Google Chrome.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/Google/Chrome/*/Platform Notifications/*',
            '*/.config/google-chrome/*/Platform Notifications/*',
            '*/AppData/Local/Chromium/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/Chromium/*/Platform Notifications/*',
            '*/.config/chromium/*/Platform Notifications/*',
            '*/snap/chromium/common/chromium/*/Platform Notifications/*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Platform Notifications/*',
            '*/webbrowser/chrome/*/Platform Notifications/*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/Microsoft Edge/*/Platform Notifications/*',
            '*/.config/microsoft-edge/*/Platform Notifications/*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Platform Notifications/*',
            '*/.config/BraveSoftware/Brave-Browser/*/Platform Notifications/*',
            '*/AppData/Local/Vivaldi/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/Vivaldi/*/Platform Notifications/*',
            '*/.config/vivaldi/*/Platform Notifications/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Platform Notifications/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/*/Platform Notifications/*',
            '*/AppData/Roaming/360se6/User Data/*/Platform Notifications/*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Platform Notifications/*',
            '*/.config/opera/*/Platform Notifications/*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Platform Notifications/*',
            '*/AppData/Roaming/Opera Software/Opera GX Stable/Platform Notifications/*',
            '*/AppData/Roaming/360se6/User Data/Platform Notifications/*',
            '*/Library/Application Support/com.operasoftware.Opera/Platform Notifications/*',
            '*/.config/opera/Platform Notifications/*',
        ),
        "output_types": "standard",
        "artifact_icon": "bell",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (its Platform Notifications database held no record)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (its Platform Notifications database held no record)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (its Platform Notifications databases held no record)",
            "windows11_arm_chrome_fs_notifications_known_20261114": "Windows 11 build 26200 ARM64 | 2 rows (known data)",
        },
    },
}

import datetime

from scripts.chromium.browser_profiles import enum_label, row_tail, webkit_time
from scripts.chromium.web_storage import ProtoError, is_deleted, newest_versions, profile_folders, proto_items
from scripts.ilapfuncs import artifact_processor, logfunc

_STORE = 'Platform Notifications'
_DATA = b'DATA:'
# NotificationDatabaseDataProto.ClosedReason (see the notes).
_CLOSED = {0: 'USER', 1: 'DEVELOPER', 2: 'UNKNOWN'}
_LIVE, _DELETED_VALUE, _DELETED_KEY = 'Live', 'Deleted, value kept', 'Deleted, key only'
_READ_ERRORS = (OSError, ValueError, KeyError, IndexError, EOFError)


def _fields(data):
    """{field number: [values]} of one encoded message, every value of a repeated field kept.

    A field expected to hold a message can arrive as a varint in a damaged or unexpected record;
    that is refused here as a ProtoError so the row degrades instead of the artifact failing.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise ProtoError(f'expected an embedded message, found {type(data).__name__}')
    out = {}
    for number, value in proto_items(data):
        out.setdefault(number, []).append(value)
    return out


def _one(fields, number):
    values = fields.get(number)
    return values[-1] if values else None


def _text(value):
    return value.decode('utf-8', 'replace') if isinstance(value, bytes) else ''


def _after(created, milliseconds):
    """Created plus a stored delay in milliseconds, blank when either is missing."""
    if not created or not isinstance(milliseconds, int):
        return ''
    try:
        return created + datetime.timedelta(milliseconds=milliseconds)
    except OverflowError:
        return ''


def _records(store, label):
    """{key: (state, value or None)} for the DATA keys of one store: the newest version's state and
    the newest value put, which a later deletion leaves in the files until they are compacted."""
    try:
        newest, puts, _records_read = newest_versions(store.path)
    except _READ_ERRORS as ex:
        logfunc(f'{label}: could not read {store.relative}: {ex}')
        return None
    out = {}
    for key, (_seq, state, value) in newest.items():
        if not key.startswith(_DATA):
            continue
        if not is_deleted(state):
            out[key] = (_LIVE, value)
            continue
        earlier = max(puts.get(key, []), default=None)
        out[key] = (_DELETED_VALUE, earlier[1]) if earlier else (_DELETED_KEY, None)
    return out


def _row(state, value, store, label):
    """One notification's columns, from its newest stored version when one is readable."""
    if value is None:
        return ('',) * 15 + (state,) + row_tail(store)
    try:
        top = _fields(value)
        payload = _fields(_one(top, 4) or b'')
        actions = [_fields(action) for action in payload.get(10, [])]
    except ProtoError as ex:
        logfunc(f'{label}: a notification in {store.relative} did not decode: {ex}')
        return ('',) * 15 + (state,) + row_tail(store)
    created = webkit_time(_one(top, 9))
    buttons = '; '.join(_text(_one(action, 2)) for action in actions if _one(action, 2))
    clicks, button_clicks = _one(top, 7), _one(top, 8)
    return (created, _after(created, _one(top, 10)), _after(created, _one(top, 11)), _after(created, _one(top, 12)),
            webkit_time(_one(payload, 12)), _text(_one(top, 2)), _text(_one(payload, 1)), _text(_one(payload, 4)),
            _text(_one(payload, 5)), '' if clicks is None else clicks, '' if button_clicks is None else button_clicks,
            enum_label(_CLOSED, _one(top, 13)), _text(_one(payload, 6)), _text(_one(payload, 15)), buttons,
            state) + row_tail(store)


@artifact_processor
def chromiumWebNotifications(context):
    label = 'Chromium Web Notifications'
    data_headers = (('Created', 'datetime'), ('First Click', 'datetime'), ('Last Click', 'datetime'),
                    ('Closed', 'datetime'), ('Site Timestamp', 'datetime'), 'Site', 'Title', 'Body', 'Tag', 'Clicks',
                    'Action Button Clicks', 'Closed Reason', 'Icon URL', 'Image URL', 'Action Buttons', 'State',
                    'Browser', 'Profile', 'User', 'Source File')
    data_list, sources = [], []
    for store in profile_folders(context, _STORE, label):
        records = _records(store, label)
        if not records:
            continue
        sources.append(store.path)
        for key in sorted(records):
            state, value = records[key]
            data_list.append(_row(state, value, store, label))
    return data_headers, data_list, '\n'.join(sources)
