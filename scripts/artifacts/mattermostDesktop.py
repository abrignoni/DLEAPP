"""Mattermost Desktop (Electron) data, for DLEAPP: cached API responses, drafts and configured servers.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "mattermostPosts": {
        "name": "Mattermost Posts",
        "description": (
            'Posts in the Mattermost Desktop HTTP cache: created, updated, edited and deleted '
            'times, channel and user IDs with names resolved from cached channel and user '
            'objects, message text, post type and attached file IDs.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Mattermost (Desktop)",
        "notes": (
            'Reads the Mattermost Desktop (Electron) Chromium HTTP cache in '
            'Mattermost/Cache/Cache_Data, and the same folder under Mattermost/Partitions/*, in '
            "both of Chromium's formats. The sample's cache is a blockfile cache and has no "
            'Partitions folder; the simple cache and the Partitions path are exercised only by '
            'cached files built in the unit tests. Every cached response from a URL under '
            '/api/v4/ with a status below 400 and a JSON content type is decoded (gzip removed; '
            'one JSON document, or one per line with a line that does not parse skipped) and '
            'searched, to 12 levels of nesting, for objects that carry a fixed set of the field '
            "names of the server's Post, User or Channel struct (the deepest value in the "
            'sample is 10 levels down). An object is reported wherever it sits in a response; a '
            'non-post object that carries the same field names would be reported as a post, '
            'though a scheduled post is kept out by the post fields a draft lacks. Object '
            "fields follow the server's own structs: Post, User and Channel in "
            'server/public/model/post.go, user.go and channel.go of mattermost/mattermost at '
            'v12.0.1 (commit 987e57120dca630dadbcd2638064ab66a02bb81e), the version the '
            'X-Version-Id header of the cached responses in the sample begins with. The cached '
            'JSON is what the server sent that client when the response was cached; Chromium '
            'can evict a cache entry, so a post, user or channel that was fetched may be '
            'missing here. When the same object (same server, ID and update_at) is cached more '
            'than once, the fields reported are those of the newest response, and Cached (UTC) '
            "is that response's time as Chromium recorded it. Server is the scheme and host of "
            'the cached URL (for drafts, the origin the IndexedDB folder is named for).One row '
            'per distinct (server, post ID, update_at). A post cached with two different '
            'update_at values has two rows; the sample has none, and this is exercised only in '
            'the unit tests. Created (UTC), Updated (UTC), Edited (UTC) and Deleted (UTC) are '
            'create_at, update_at, edit_at and delete_at, which the server writes as Unix '
            'milliseconds (GetMillis is UnixMilli, utils.go lines 453 to 460; post.go line 798 '
            "sets create_at from it); each is blank when 0. In the sample every post's "
            'create_at precedes the response time Chromium recorded for the response that held '
            'it, by more than 1.4 seconds, and none follows it. Edited (UTC), Deleted (UTC), '
            'File IDs and Pinned are empty on all 16 rows. A cached response can hold a post '
            'the server has since deleted; that was not tested here. Channel and User are the '
            'display name (or, for a direct channel, the two user names of its userId1__userId2 '
            'name, GetDMNameFromIds in channel.go lines 621 to 626) and the username found in '
            'the cached channel and user objects of the same server, and are blank when the '
            'cache holds none; a direct-channel member with no cached user object is shown by '
            'ID, and a channel with an empty display name by its name. All 16 posts of the '
            'sample resolve. Channel ID, User ID, Root ID and Post ID are as stored. Message is '
            'as stored and is non-empty on all 16 rows (13 distinct texts). Type is as stored: '
            'empty for an ordinary post (PostTypeDefault, post.go line 32), which 6 of the 16 '
            'rows are, and a system_ value for the other 10 (system_join_channel 5, '
            'system_join_team 2, system_displayname_change, system_header_change and '
            'system_purpose_change 1 each). Server held one value on all 16 rows. Not reported, '
            'among other struct fields: props, metadata, hashtags, original_id, message_source, '
            'pending_post_id, has_reactions, remote_id, reply counts and participants. Rows: 16 '
            'on the sample, from 109 cached API responses of which 0 did not parse. Stores of '
            'the Mattermost Desktop folder that none of these artifacts report: Local Storage '
            '(navigation keys such as the previous channel per user and team, login flags), '
            "Network/Cookies (values not read), logs/main.log (the desktop app's own log), "
            'Session Storage, downloads.json (0 bytes in the sample) and the cached responses '
            'under /api/v4 that are not JSON (16 image responses in the sample). Other files in '
            'the folder were not surveyed. Windows is the only layout exercised: the macOS '
            '(Library/Application Support/Mattermost) and Linux (.config/Mattermost) folders '
            'are reached by the same `*/Mattermost/...` paths and were not tested. Sample: the '
            'public lab folder of Mattermost Desktop 6.3.1 from '
            '0ri0ri/selfhosted-chat-forensics (MIT, commit 0bbb8b1; corpus keys '
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1 and the same name ending '
            '_users_layout, README beside them), against a server whose responses carry an '
            'X-Version-Id beginning 12.0.1; its row counts are in sample_data. It is the only '
            'Mattermost client sample run. No record of what was typed or sent accompanies it, '
            'so the rows were not compared with known data.'
        ),
        "paths": ('*/Mattermost/Cache/Cache_Data/*', '*/Mattermost/Partitions/*/Cache/Cache_Data/*',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Mattermost Desktop 6.3.1, Windows | 16 rows',
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1': 'Mattermost Desktop 6.3.1, Windows | 16 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
    "mattermostUsers": {
        "name": "Mattermost Users",
        "description": (
            'Users in the Mattermost Desktop HTTP cache: username, name, email, roles and the '
            'account times, as the server returned them.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Mattermost (Desktop)",
        "notes": (
            'Reads the Mattermost Desktop (Electron) Chromium HTTP cache in '
            'Mattermost/Cache/Cache_Data, and the same folder under Mattermost/Partitions/*, in '
            "both of Chromium's formats. The sample's cache is a blockfile cache and has no "
            'Partitions folder; the simple cache and the Partitions path are exercised only by '
            'cached files built in the unit tests. Every cached response from a URL under '
            '/api/v4/ with a status below 400 and a JSON content type is decoded (gzip removed; '
            'one JSON document, or one per line with a line that does not parse skipped) and '
            'searched, to 12 levels of nesting, for objects that carry a fixed set of the field '
            "names of the server's Post, User or Channel struct (the deepest value in the "
            'sample is 10 levels down). An object is reported wherever it sits in a response; a '
            'non-post object that carries the same field names would be reported as a post, '
            'though a scheduled post is kept out by the post fields a draft lacks. Object '
            "fields follow the server's own structs: Post, User and Channel in "
            'server/public/model/post.go, user.go and channel.go of mattermost/mattermost at '
            'v12.0.1 (commit 987e57120dca630dadbcd2638064ab66a02bb81e), the version the '
            'X-Version-Id header of the cached responses in the sample begins with. The cached '
            'JSON is what the server sent that client when the response was cached; Chromium '
            'can evict a cache entry, so a post, user or channel that was fetched may be '
            'missing here. When the same object (same server, ID and update_at) is cached more '
            'than once, the fields reported are those of the newest response, and Cached (UTC) '
            "is that response's time as Chromium recorded it. Server is the scheme and host of "
            'the cached URL (for drafts, the origin the IndexedDB folder is named for).One row '
            'per distinct (server, user ID, update_at). A user object counts only with a '
            'non-empty username and one of email, roles or first_name; an object with an id and '
            'an empty username is left out. Created (UTC), Updated (UTC) and Deleted (UTC) are '
            'create_at, update_at and delete_at in Unix milliseconds, blank when 0. Username, '
            'First Name, Last Name, Nickname, Email, Position, Roles and Auth Service are as '
            'stored; Bot is yes when is_bot is true. Which of these fields the server includes '
            "for another user may depend on the server's settings; that was not tested. In the "
            'sample, 4 users: Bot is yes on 2; Last Name, Nickname, Position and Auth Service '
            'are empty on all 4 rows, Deleted (UTC) is empty on all 4, Server held one value, '
            'and Cached (UTC) held one value, the newest response holding each of the four '
            'having the same response time. A user the cache never returned is absent, so the '
            'table is not a user list of the server. Not reported, among other struct fields: '
            'notify_props, timezone, locale, the picture and password times, last_activity_at, '
            'last_login, mfa_active, email_verified, bot description, props and the terms of '
            'service fields. Stores of the Mattermost Desktop folder that none of these '
            'artifacts report: Local Storage (navigation keys such as the previous channel per '
            'user and team, login flags), Network/Cookies (values not read), logs/main.log (the '
            "desktop app's own log), Session Storage, downloads.json (0 bytes in the sample) "
            'and the cached responses under /api/v4 that are not JSON (16 image responses in '
            'the sample). Other files in the folder were not surveyed. Windows is the only '
            'layout exercised: the macOS (Library/Application Support/Mattermost) and Linux '
            '(.config/Mattermost) folders are reached by the same `*/Mattermost/...` paths and '
            'were not tested. Sample: the public lab folder of Mattermost Desktop 6.3.1 from '
            '0ri0ri/selfhosted-chat-forensics (MIT, commit 0bbb8b1; corpus keys '
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1 and the same name ending '
            '_users_layout, README beside them), against a server whose responses carry an '
            'X-Version-Id beginning 12.0.1; its row counts are in sample_data. It is the only '
            'Mattermost client sample run. No record of what was typed or sent accompanies it, '
            'so the rows were not compared with known data.'
        ),
        "paths": ('*/Mattermost/Cache/Cache_Data/*', '*/Mattermost/Partitions/*/Cache/Cache_Data/*',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Mattermost Desktop 6.3.1, Windows | 4 rows',
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1': 'Mattermost Desktop 6.3.1, Windows | 4 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
    "mattermostChannels": {
        "name": "Mattermost Channels",
        "description": (
            'Channels in the Mattermost Desktop HTTP cache: type, names, header, purpose and '
            'the channel times, as the server returned them.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Mattermost (Desktop)",
        "notes": (
            'Reads the Mattermost Desktop (Electron) Chromium HTTP cache in '
            'Mattermost/Cache/Cache_Data, and the same folder under Mattermost/Partitions/*, in '
            "both of Chromium's formats. The sample's cache is a blockfile cache and has no "
            'Partitions folder; the simple cache and the Partitions path are exercised only by '
            'cached files built in the unit tests. Every cached response from a URL under '
            '/api/v4/ with a status below 400 and a JSON content type is decoded (gzip removed; '
            'one JSON document, or one per line with a line that does not parse skipped) and '
            'searched, to 12 levels of nesting, for objects that carry a fixed set of the field '
            "names of the server's Post, User or Channel struct (the deepest value in the "
            'sample is 10 levels down). An object is reported wherever it sits in a response; a '
            'non-post object that carries the same field names would be reported as a post, '
            'though a scheduled post is kept out by the post fields a draft lacks. Object '
            "fields follow the server's own structs: Post, User and Channel in "
            'server/public/model/post.go, user.go and channel.go of mattermost/mattermost at '
            'v12.0.1 (commit 987e57120dca630dadbcd2638064ab66a02bb81e), the version the '
            'X-Version-Id header of the cached responses in the sample begins with. The cached '
            'JSON is what the server sent that client when the response was cached; Chromium '
            'can evict a cache entry, so a post, user or channel that was fetched may be '
            'missing here. When the same object (same server, ID and update_at) is cached more '
            'than once, the fields reported are those of the newest response, and Cached (UTC) '
            "is that response's time as Chromium recorded it. Server is the scheme and host of "
            'the cached URL (for drafts, the origin the IndexedDB folder is named for).One row '
            'per distinct (server, channel ID, update_at), taken from the newest cached '
            'response that held it. Created (UTC), Updated (UTC), Last Post (UTC) and Deleted '
            '(UTC) are create_at, update_at, last_post_at and delete_at in Unix milliseconds, '
            "blank when 0. Type is the stored letter with the name of the server's constant: O "
            'open, P private, D direct, G group (ChannelType, channel.go lines 28 to 31); any '
            'other value is shown as stored. Display Name and Name are as stored; a direct '
            'channel has an empty display name (2 of 7 rows in the sample) and its name is the '
            'two user IDs joined by two underscores (GetDMNameFromIds, channel.go lines 621 to '
            '626). Header, Purpose, Team ID and Creator ID are as stored; Message Count is '
            'total_msg_count. Last Post and Message Count change without update_at changing, so '
            'they are the values in the newest cached response. In the sample 4 channels are '
            'open, 1 private and 2 direct; Deleted (UTC) is empty on all 7 rows and Server held '
            'one value. A channel the cache never returned is absent. Not reported, among other '
            'struct fields: props, scheme and policy fields, extra_update_at, '
            'group_constrained, shared, total_msg_count_root, last_root_post_at, banner_info '
            'and autotranslation. Stores of the Mattermost Desktop folder that none of these '
            'artifacts report: Local Storage (navigation keys such as the previous channel per '
            'user and team, login flags), Network/Cookies (values not read), logs/main.log (the '
            "desktop app's own log), Session Storage, downloads.json (0 bytes in the sample) "
            'and the cached responses under /api/v4 that are not JSON (16 image responses in '
            'the sample). Other files in the folder were not surveyed. Windows is the only '
            'layout exercised: the macOS (Library/Application Support/Mattermost) and Linux '
            '(.config/Mattermost) folders are reached by the same `*/Mattermost/...` paths and '
            'were not tested. Sample: the public lab folder of Mattermost Desktop 6.3.1 from '
            '0ri0ri/selfhosted-chat-forensics (MIT, commit 0bbb8b1; corpus keys '
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1 and the same name ending '
            '_users_layout, README beside them), against a server whose responses carry an '
            'X-Version-Id beginning 12.0.1; its row counts are in sample_data. It is the only '
            'Mattermost client sample run. No record of what was typed or sent accompanies it, '
            'so the rows were not compared with known data.'
        ),
        "paths": ('*/Mattermost/Cache/Cache_Data/*', '*/Mattermost/Partitions/*/Cache/Cache_Data/*',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Mattermost Desktop 6.3.1, Windows | 7 rows',
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1': 'Mattermost Desktop 6.3.1, Windows | 7 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
    "mattermostDrafts": {
        "name": "Mattermost Drafts",
        "description": (
            "Message drafts the Mattermost web app kept in the desktop app's IndexedDB: the "
            'versions still present of its channel, reply and edit drafts, each with the time '
            'the app stored and a mark on the newest.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Mattermost (Desktop)",
        "notes": (
            'Reads the IndexedDB database named localforage, object store keyvaluepairs, key '
            'persist:storage in each Mattermost/IndexedDB/<origin>.indexeddb.leveldb folder. '
            "Its value is JSON text of the web app's persisted state: a _persist entry and one "
            'entry per draft whose key is draft_, comment_draft_ or edit_draft_ followed by a '
            '26-character ID (the key prefixes are StoragePrefixes in '
            'webapp/channels/src/utils/constants.tsx at mattermost/mattermost v12.0.1, commit '
            '987e57120dca630dadbcd2638064ab66a02bb81e, lines 831 to 833). Each draft entry '
            'holds timestamp, an ISO 8601 UTC string, and value, which holds message on every '
            'entry of the sample; the other fields of value vary between entries (fileInfos, '
            'uploadsInProgress and metadata on most, channelId, rootId, createAt and updateAt '
            'on some). In the sample every IndexedDB record is one saved state of all drafts '
            'and all 108 are still in the LevelDB log, so earlier texts are present; LevelDB '
            'can discard older records when it compacts. This reads every record that is a '
            'persist:storage value (a record with no value is skipped) and keeps one row per '
            'distinct (draft key, timestamp, message). Latest is yes on the version in the '
            'newest persist:storage record that holds that draft key, and is empty for a draft '
            'key that record no longer holds; in the sample all 9 keys are in the newest record '
            'and all 9 Latest rows have an empty Message. Kind follows the prefix: channel '
            'draft, reply draft and edit draft; Target ID is the ID after the prefix. In the '
            'sample 9 draft keys with 106 versions in 108 records (51 versions for the key with '
            'the most): 96 rows are channel drafts, 7 reply drafts and 3 edit drafts, and '
            'Message is empty on 55 rows, a state in which the draft held no text; why it was '
            'empty was not tested. Channel is the name of the channel found in the cached '
            'channel objects (for a reply or edit draft, the channel of the cached post named '
            'by Target ID), which resolves on all 106 rows; this needs the cache files of the '
            'same server in the same extraction, and is blank otherwise. Files lists the file '
            'names in fileInfos, on 5 rows. Draft Time (UTC) is the timestamp the web app '
            'stored; what it marks (typing, saving or syncing a draft) was not tested. The '
            'record order uses the LevelDB sequence number of each record. Server is the origin '
            'the IndexedDB folder is named for, shown without a port when the folder name ends '
            "_0, which Chromium writes for a scheme's default port. Server held one value on "
            'all 106 rows. A record that cannot be deserialised is counted in the run log. '
            'IndexedDB is read through the vendored CCL reader; the unit tests stand in a small '
            'fake for it, and the real reading is exercised on the sample only. Not reported: '
            'uploadsInProgress, metadata and the other value fields. Stores of the Mattermost '
            'Desktop folder that none of these artifacts report: Local Storage (navigation keys '
            'such as the previous channel per user and team, login flags), Network/Cookies '
            "(values not read), logs/main.log (the desktop app's own log), Session Storage, "
            'downloads.json (0 bytes in the sample) and the cached responses under /api/v4 that '
            'are not JSON (16 image responses in the sample). Other files in the folder were '
            'not surveyed. Windows is the only layout exercised: the macOS (Library/Application '
            'Support/Mattermost) and Linux (.config/Mattermost) folders are reached by the same '
            '`*/Mattermost/...` paths and were not tested. Sample: the public lab folder of '
            'Mattermost Desktop 6.3.1 from 0ri0ri/selfhosted-chat-forensics (MIT, commit '
            '0bbb8b1; corpus keys mattermost_desktop_selfhosted_chat_forensics_0bbb8b1 and the '
            'same name ending _users_layout, README beside them), against a server whose '
            'responses carry an X-Version-Id beginning 12.0.1; its row counts are in '
            'sample_data. It is the only Mattermost client sample run. No record of what was '
            'typed or sent accompanies it, so the rows were not compared with known data.'
        ),
        "paths": ('*/Mattermost/IndexedDB/*.indexeddb.leveldb/*', '*/Mattermost/Cache/Cache_Data/*', '*/Mattermost/Partitions/*/Cache/Cache_Data/*',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Mattermost Desktop 6.3.1, Windows | 106 rows',
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1': 'Mattermost Desktop 6.3.1, Windows | 106 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
    "mattermostServers": {
        "name": "Mattermost Servers",
        "description": (
            "The servers configured in Mattermost Desktop's config.json, with the one marked "
            'last active and the desktop version recorded in app-state.json.'
        ),
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-14",
        "last_update_date": "2026-11-14",
        "requirements": "none",
        "category": "Mattermost (Desktop)",
        "notes": (
            "Reads Mattermost/config.json (the desktop app's configuration, whose servers list "
            'holds name, url, order and an optional isPredefined, and whose optional '
            'lastActiveServer is a number: ConfigServer and CurrentConfig in '
            'src/types/config.ts at mattermost/desktop v6.3.1, commit '
            '45944fb07a70f08587b25719c8c88c71f16ff920) and the lastAppVersion of the '
            'app-state.json beside it. Order and URL are as stored. Last Active is yes on the '
            'server whose rank by order equals lastActiveServer: the app sorts its servers by '
            'order (src/common/servers/serverManager.ts line 329 at the same commit), indexes '
            'them with lastActiveServer (line 342) and writes that index from the ordered list '
            '(line 369). Predefined servers, which an installation can add ahead of the list, '
            'were not tested, and the sample has one server. Predefined is empty on the one row '
            'of the sample. Desktop Version (app-state.json) is lastAppVersion as stored, blank '
            'when no app-state.json sits beside the config. Rows: 1 on the sample. Not '
            'reported: the other settings of config.json (tray, spell checker, notifications '
            'and so on). Stores of the Mattermost Desktop folder that none of these artifacts '
            'report: Local Storage (navigation keys such as the previous channel per user and '
            'team, login flags), Network/Cookies (values not read), logs/main.log (the desktop '
            "app's own log), Session Storage, downloads.json (0 bytes in the sample) and the "
            'cached responses under /api/v4 that are not JSON (16 image responses in the '
            'sample). Other files in the folder were not surveyed. Windows is the only layout '
            'exercised: the macOS (Library/Application Support/Mattermost) and Linux '
            '(.config/Mattermost) folders are reached by the same `*/Mattermost/...` paths and '
            'were not tested. Sample: the public lab folder of Mattermost Desktop 6.3.1 from '
            '0ri0ri/selfhosted-chat-forensics (MIT, commit 0bbb8b1; corpus keys '
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1 and the same name ending '
            '_users_layout, README beside them), against a server whose responses carry an '
            'X-Version-Id beginning 12.0.1; its row counts are in sample_data. It is the only '
            'Mattermost client sample run. No record of what was typed or sent accompanies it, '
            'so the rows were not compared with known data.'
        ),
        "paths": ('*/Mattermost/config.json', '*/Mattermost/app-state.json',),
        "output_types": "standard",
        "artifact_icon": "message-square",
        "sample_data": {
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1_users_layout': 'Mattermost Desktop 6.3.1, Windows | 1 rows',
            'mattermost_desktop_selfhosted_chat_forensics_0bbb8b1': 'Mattermost Desktop 6.3.1, Windows | 1 rows',
            'windows11_arm_claude_code_history_known_20261108': 'Windows 11 build 26200 (ARM64) | 0 rows',
        },
    },
}

import json
import os
import re
from datetime import datetime, timezone

from scripts.chromium.mattermost_api import CHANNEL_TYPES, ms_to_datetime, scan_cache
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor.ccl import ccl_chromium_indexeddb as indexeddb

_LABEL = 'Mattermost'
# The prefixes the web app puts on the keys of its persisted drafts, StoragePrefixes in
# webapp/channels/src/utils/constants.tsx at mattermost/mattermost v12.0.1 (987e57120dca630dadbcd2638064ab66a02bb81e, lines 831 to 833).
_DRAFT_KEY = re.compile(r'^(draft|comment_draft|edit_draft)_([a-z0-9]{26})$')
_DRAFT_KINDS = {'draft': 'channel draft', 'comment_draft': 'reply draft', 'edit_draft': 'edit draft'}


def _latest(table):
    """{(server, id): the object with the highest update_at} from a scan table."""
    out = {}
    for (server, ident, update_at), row in table.items():
        best = out.get((server, ident))
        if best is None or (update_at or 0) > (best[0] or 0):
            out[(server, ident)] = (update_at, row['object'])
    return {key: value[1] for key, value in out.items()}


def _user_name(users, server, user_id):
    user = users.get((server, user_id))
    return user.get('username', '') if user else ''


def _channel_name(channels, users, server, channel_id):
    channel = channels.get((server, channel_id))
    if not channel:
        return ''
    if channel.get('type') == 'D' and '__' in (channel.get('name') or ''):
        # A direct channel is named userId1__userId2 (GetDMNameFromIds, channel.go lines 621 to 626).
        return ' and '.join(_user_name(users, server, part) or part for part in channel['name'].split('__'))
    return channel.get('display_name') or channel.get('name') or ''


def _log_scan(scan):
    logfunc(f'{_LABEL}: {scan.entry_count} cached API responses with JSON read, {scan.json_failures} did not parse')
    if scan.too_deep:
        logfunc(f'{_LABEL}: {scan.too_deep} nested value(s) below the nesting limit were not searched')


def _source(scan):
    return '\n'.join(sorted(scan.sources))


@artifact_processor
def mattermostPosts(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Updated (UTC)', 'datetime'), ('Edited (UTC)', 'datetime'),
                    ('Deleted (UTC)', 'datetime'), ('Cached (UTC)', 'datetime'), 'Server', 'Channel', 'Channel ID',
                    'User', 'User ID', 'Message', 'Type', 'Root ID', 'File IDs', 'Pinned', 'Post ID')
    scan = scan_cache(context.get_files_found())
    if not scan.entry_count:
        return data_headers, [], ''
    _log_scan(scan)
    users, channels = _latest(scan.users), _latest(scan.channels)
    rows = []
    for (server, post_id, _update), item in scan.posts.items():
        post = item['object']
        rows.append((ms_to_datetime(post.get('create_at')), ms_to_datetime(post.get('update_at')),
                     ms_to_datetime(post.get('edit_at')), ms_to_datetime(post.get('delete_at')), item['cached'], server,
                     _channel_name(channels, users, server, post.get('channel_id')), post.get('channel_id', ''),
                     _user_name(users, server, post.get('user_id')), post.get('user_id', ''),
                     post.get('message', ''), post.get('type', ''), post.get('root_id', ''),
                     '\n'.join(post.get('file_ids') or []), 'yes' if post.get('is_pinned') else '', post_id))
    rows.sort(key=lambda r: (str(r[0]), r[15], str(r[1])))
    return data_headers, rows, _source(scan)


@artifact_processor
def mattermostUsers(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Updated (UTC)', 'datetime'), ('Deleted (UTC)', 'datetime'),
                    ('Cached (UTC)', 'datetime'), 'Server', 'Username', 'First Name', 'Last Name', 'Nickname', 'Email',
                    'Position', 'Roles', 'Auth Service', 'Bot', 'User ID')
    scan = scan_cache(context.get_files_found())
    if not scan.entry_count:
        return data_headers, [], ''
    rows = []
    for (server, user_id, _update), item in scan.users.items():
        user = item['object']
        rows.append((ms_to_datetime(user.get('create_at')), ms_to_datetime(user.get('update_at')),
                     ms_to_datetime(user.get('delete_at')), item['cached'], server, user.get('username', ''),
                     user.get('first_name', ''), user.get('last_name', ''), user.get('nickname', ''),
                     user.get('email', ''), user.get('position', ''), user.get('roles', ''),
                     user.get('auth_service', ''), 'yes' if user.get('is_bot') else '', user_id))
    rows.sort(key=lambda r: (str(r[0]), r[14], str(r[1])))
    return data_headers, rows, _source(scan)


@artifact_processor
def mattermostChannels(context):
    data_headers = (('Created (UTC)', 'datetime'), ('Updated (UTC)', 'datetime'), ('Last Post (UTC)', 'datetime'),
                    ('Deleted (UTC)', 'datetime'), ('Cached (UTC)', 'datetime'), 'Server', 'Type', 'Display Name',
                    'Name', 'Header', 'Purpose', 'Team ID', 'Creator ID', 'Message Count', 'Channel ID')
    scan = scan_cache(context.get_files_found())
    if not scan.entry_count:
        return data_headers, [], ''
    rows = []
    for (server, channel_id, _update), item in scan.channels.items():
        channel = item['object']
        kind = channel.get('type', '')
        rows.append((ms_to_datetime(channel.get('create_at')), ms_to_datetime(channel.get('update_at')),
                     ms_to_datetime(channel.get('last_post_at')), ms_to_datetime(channel.get('delete_at')),
                     item['cached'], server, f"{CHANNEL_TYPES[kind]} ({kind})" if kind in CHANNEL_TYPES else kind,
                     channel.get('display_name', ''), channel.get('name', ''), channel.get('header', ''),
                     channel.get('purpose', ''), channel.get('team_id', ''), channel.get('creator_id', ''),
                     channel.get('total_msg_count', ''), channel_id))
    rows.sort(key=lambda r: (str(r[0]), r[14], str(r[1])))
    return data_headers, rows, _source(scan)


def _origin(folder_name):
    """The server origin an IndexedDB folder is named for: scheme_host_port.indexeddb.leveldb. Chromium writes the
    default port of a scheme as 0 (database_identifier.cc), so port 0 is shown as no port."""
    stem = folder_name.split('.indexeddb')[0]
    scheme, _, rest = stem.partition('_')
    host, _, port = rest.rpartition('_')
    if port.isdigit():
        return f'{scheme}://{host}' if int(port) == 0 else f'{scheme}://{host}:{port}'
    return f'{scheme}://{rest}'


def _iso_to_datetime(value):
    if not isinstance(value, str):
        return ''
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except ValueError:
        return ''


def _collector(sink):
    """A handler for records the IndexedDB reader cannot deserialise: it remembers their keys."""
    return lambda key, _data: sink.append(key)


def _draft_states(record):
    """{draft key: (timestamp, message, draft)} of one persist:storage record, {} when it is not one."""
    if str(record.key.value) != 'persist:storage' or not isinstance(record.value, str):
        return {}
    try:
        state = json.loads(record.value)
    except ValueError:
        return {}
    out = {}
    for key, raw in (state.items() if isinstance(state, dict) else ()):
        if not _DRAFT_KEY.match(key):
            continue
        try:
            draft = json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            continue
        if isinstance(draft, dict) and isinstance(draft.get('value'), dict):
            out[key] = (draft.get('timestamp'), draft['value'].get('message', ''), draft)
    return out


@artifact_processor
def mattermostDrafts(context):
    data_headers = (('Draft Time (UTC)', 'datetime'), 'Server', 'Kind', 'Channel', 'Message', 'Files', 'Target ID',
                    'Latest')
    found = sorted(str(p) for p in context.get_files_found() if os.path.isfile(str(p)))
    folders = sorted({os.path.dirname(p) for p in found if p.endswith(('.log', '.ldb')) and
                      os.path.dirname(p).endswith('.indexeddb.leveldb')})
    if not folders:
        return data_headers, [], ''
    scan = scan_cache(found)
    users, channels = _latest(scan.users), _latest(scan.channels)
    posts = {key[:2]: row['object'] for key, row in scan.posts.items()}
    rows, sources = [], []
    for folder in folders:
        server = _origin(os.path.basename(folder))
        sources.extend(p for p in found if os.path.dirname(p) == folder and p.endswith(('.log', '.ldb')))
        try:
            wrapped = indexeddb.WrappedIndexDB(folder, None)
            databases = list(wrapped.database_ids)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: {context.get_relative_path(folder)} could not be opened as IndexedDB: {exc}')
            continue
        bad = []
        versions = {}   # draft key -> {(timestamp, message): draft}
        newest_seq, newest_state = -1, {}
        for database in databases:
            if database.name != 'localforage':
                continue
            store = wrapped[database.dbid_no]
            if 'keyvaluepairs' not in store.object_store_names:
                continue
            for record in store['keyvaluepairs'].iterate_records(
                    bad_deserializer_data_handler=_collector(bad)):
                states = _draft_states(record)
                if record.ldb_seq_no >= newest_seq and str(record.key.value) == 'persist:storage':
                    newest_seq, newest_state = record.ldb_seq_no, {k: (v[0], v[1]) for k, v in states.items()}
                for key, (stamp, message, draft) in states.items():
                    versions.setdefault(key, {}).setdefault((stamp, message), draft)
        if bad:
            logfunc(f'{_LABEL}: {context.get_relative_path(folder)}: {len(bad)} IndexedDB record(s) could not be deserialised')
        for key, found_versions in versions.items():
            kind_key, target = _DRAFT_KEY.match(key).groups()
            for (stamp, message), draft in found_versions.items():
                channel_id = target if kind_key == 'draft' else (posts.get((server, target)) or {}).get('channel_id', '')
                files = draft['value'].get('fileInfos') or []
                names = '\n'.join(str(f.get('name', '')) if isinstance(f, dict) else str(f) for f in files)
                rows.append((_iso_to_datetime(stamp), server, _DRAFT_KINDS[kind_key],
                             _channel_name(channels, users, server, channel_id), message, names, target,
                             'yes' if newest_state.get(key) == (stamp, message) else ''))
    rows.sort(key=lambda r: (r[2], r[6], str(r[0])))
    return data_headers, rows, '\n'.join(sources)


@artifact_processor
def mattermostServers(context):
    data_headers = ('Name', 'URL', 'Order', 'Predefined', 'Last Active', 'Desktop Version (app-state.json)')
    found = sorted(str(p) for p in context.get_files_found() if os.path.isfile(str(p)))
    configs = [p for p in found if os.path.basename(p) == 'config.json']
    rows, sources = [], []
    for path in configs:
        sources.append(path)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                config = json.load(handle)
        except (OSError, ValueError) as exc:
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} did not read as JSON: {exc}')
            continue
        state_path = os.path.join(os.path.dirname(path), 'app-state.json')
        version = ''
        if os.path.isfile(state_path):
            sources.append(state_path)
            try:
                with open(state_path, 'r', encoding='utf-8') as handle:
                    version = (json.load(handle) or {}).get('lastAppVersion', '')
            except (OSError, ValueError):
                pass
        servers = config.get('servers') if isinstance(config, dict) else None
        if not isinstance(servers, list):
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} holds no servers list')
            continue
        # The app indexes its servers sorted by their order value (serverManager.ts at desktop v6.3.1), so
        # lastActiveServer is compared with the rank by order, not with the position in the file.
        ranked = sorted((s for s in servers if isinstance(s, dict)),
                        key=lambda s: s.get('order') if isinstance(s.get('order'), int) else 0)
        rank = {id(server): number for number, server in enumerate(ranked)}
        active = config.get('lastActiveServer')
        for server in servers:
            if not isinstance(server, dict):
                continue
            rows.append((server.get('name', ''), server.get('url', ''), server.get('order', ''),
                         'yes' if server.get('isPredefined') else '',
                         'yes' if isinstance(active, int) and rank.get(id(server)) == active else '', version))
    return data_headers, rows, '\n'.join(sources)
