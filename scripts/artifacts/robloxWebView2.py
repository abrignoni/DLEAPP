__artifacts_v2__ = {
    "robloxWindowsCookieVault": {
        "name": "Roblox Windows Cookie Vault",
        "description": "The Roblox Player CookiesData vault retained in "
                       "LocalStorage/RobloxCookies.dat, including the format version "
                       "and complete DPAPI-protected blob.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "CookiesData is encrypted with Windows DPAPI and cannot be decrypted "
                 "from AppData alone. The complete base64 value is retained for "
                 "decryption when matching Windows account material is available. "
                 "First 20 Bytes is the leading hex of the decoded value, reported "
                 "as stored; the parser does not verify it against the DPAPI "
                 "provider GUID. "
                 "Reference: Microsoft, 'Windows Data Protection (DPAPI)', "
                 "https://learn.microsoft.com/en-us/windows/win32/seccng/cng-dpapi",
        "paths": ("*/AppData/Local/Roblox/LocalStorage/RobloxCookies.dat",),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 1 row",
        },
    },
    "robloxWebView2Cookies": {
        "name": "Roblox WebView2 Cookies",
        "description": "Cookie metadata and complete encrypted values from Roblox's "
                       "Windows WebView2 profile.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Chromium v10 cookie values depend on the WebView2 Local State "
                 "os_crypt key and Windows DPAPI. Encrypted values are reported in "
                 "full as hexadecimal evidence; no decryption is attempted.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Network/Cookies",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 10 rows",
        },
    },
    "robloxWebView2History": {
        "name": "Roblox WebView2 History",
        "description": "Visits retained by Roblox's Windows WebView2 profile, "
                       "including UTC visit time, title, URL, transition, duration "
                       "and referring visit identifiers.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "URLs and query parameters are reported in full and may contain "
                 "challenge tokens or credential-like values. The parser does not "
                 "determine whether those values remain valid or reusable. History "
                 "is a retained partial record and can include repeated visits. "
                 "Transition names and the microsecond visit duration follow the "
                 "Chromium definitions. "
                 "Reference: Chromium, 'ui/base/page_transition_types.h and the "
                 "History database schema', "
                 "https://chromium.googlesource.com/chromium/src/+/main/ui/base/"
                 "page_transition_types.h",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/History",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 20 rows",
        },
    },
    "robloxWebView2LocalStorage": {
        "name": "Roblox WebView2 Local Storage",
        "description": "Live, superseded and deleted Local Storage record versions "
                       "recovered from Roblox's Windows WebView2 LevelDB.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "LevelDB table and log files preserve historical versions. Values "
                 "are reported in full; JSON is compacted and may contain tokens, "
                 "notifications and account state. The parser does not determine "
                 "whether token-like values remain valid or reusable.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Local Storage/leveldb/*",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 136 rows",
        },
    },
    "robloxWebView2SessionStorage": {
        "name": "Roblox WebView2 Session Storage",
        "description": "Live and deleted Session Storage record versions recovered "
                       "from Roblox's Windows WebView2 LevelDB stores, with namespace, "
                       "origin, map, key and sequence attribution.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Chromium Session Storage namespaces map origins to numbered maps. "
                 "LevelDB log records can preserve values after the namespace is "
                 "cleared; those tombstoned versions are labeled Deleted. UTF-16 "
                 "values are decoded and JSON is compacted without changing data.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Session Storage/*",
            "*/AppData/Local/Roblox/Versions/*/RobloxPlayerBeta.exe.WebView2/"
            "EBWebView/Default/Session Storage/*",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 8 rows",
        },
    },
    "robloxWebView2IndexedDB": {
        "name": "Roblox WebView2 IndexedDB",
        "description": "Database and object-store record versions recovered from "
                       "Roblox's Windows WebView2 IndexedDB LevelDB.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "The vendored Chromium IndexedDB reader returns decoded JavaScript "
                 "values where supported and explicit placeholders otherwise. "
                 "Historical versions can repeat. Output may contain tokens or "
                 "credential-like values whose validity and reusability are not "
                 "assessed.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "IndexedDB/https_www.roblox.com_0.indexeddb.leveldb/*",
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "database",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 171 rows",
        },
    },
    "robloxWebView2Cache": {
        "name": "Roblox WebView2 Network Cache",
        "description": "HTTP responses reconstructed from Roblox's Windows WebView2 "
                       "Chromium blockfile cache, including request, response, "
                       "creation and last-use times, URL, status, headers and body "
                       "storage details.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Parses Chromium v3 index, data_N blocks and f_XXXXXX streams using "
                 "the published blockfile format. URLs and headers are reported in "
                 "full. The cache is partial and can contain tokens or "
                 "credential-like query values; their validity and reusability are "
                 "not assessed.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "globe",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 534 rows",
        },
    },
    "robloxWebView2AccountData": {
        "name": "Roblox WebView2 Account Data",
        "description": "User-specific account, profile, contact, age-verification, "
                       "country, parental-control and privacy-setting values recovered "
                       "from cached Roblox API responses.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Only user-specific API endpoints are included; general feature "
                 "configuration metadata is excluded. Nested JSON is flattened to "
                 "field paths. Empty collections are retained as stored rather "
                 "than dropped. "
                 "Responses with no user ID in the URL are attributed from the "
                 "current appStorage account, so Subject User ID can be "
                 "misattributed where the profile was used by more than one "
                 "account or the signed-in account was switched. "
                 "Output can contain PII, contact details and privacy settings.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
            "*/AppData/Local/Roblox/LocalStorage/appStorage.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "user",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 103 rows",
        },
    },
    "robloxWebView2SocialData": {
        "name": "Roblox WebView2 Social & Group Data",
        "description": "Attributable friend relationships, online friends, group "
                       "memberships, roles and group-search actions recovered from "
                       "cached Roblox API responses.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "One row is emitted per relationship, membership or search action. "
                 "Group-search response listings are omitted because they are server "
                 "results rather than user activity. Searches with no user ID in the "
                 "URL are attributed from the current appStorage account.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
            "*/AppData/Local/Roblox/LocalStorage/appStorage.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 5 rows",
        },
    },
    "robloxWebView2Commerce": {
        "name": "Roblox WebView2 Commerce Activity",
        "description": "Attributable Robux balance, payment-session state and Robux "
                       "purchase-flow events retained in WebView2 cache and Local "
                       "Storage.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-08-01",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Purchase-flow telemetry documents page views, available products "
                 "and session state; it does not by itself prove a completed purchase. "
                 "Payment-card data was not present in the tested AppData corpus. "
                 "One row is emitted per balance, session or purchase-flow event. "
                 "Responses with no user ID in the URL are attributed from the "
                 "current appStorage account, so Subject User ID can be "
                 "misattributed where the profile was used by more than one "
                 "account or the signed-in account was switched. "
                 "Client-Reported Event Time is the lt parameter of a "
                 "client-generated telemetry URL, not a server timestamp.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Local Storage/leveldb/*",
            "*/AppData/Local/Roblox/LocalStorage/appStorage.json",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "currency-dollar",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 9 rows",
        },
    },
    "robloxWebView2UserContent": {
        "name": "Roblox WebView2 User Content Activity",
        "description": "Attributable avatar assets, favorites, badges, created "
                       "experiences and group wall posts recovered from cached "
                       "Roblox API responses.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Only records containing an actual user-linked item or wall post "
                 "are emitted. Empty lists, endpoint errors, category catalogs, "
                 "feature metadata and settings-option catalogs are excluded. "
                 "Identical retained response versions are deduplicated. The tested "
                 "Windows corpus produced zero rows, so the supported endpoint "
                 "schemas are parser capabilities rather than observed sample "
                 "evidence.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "star",
        "sample_data": {},
    },
    "robloxPrivateMessages": {
        "name": "Roblox Private Messages",
        "description": "Private-message records recovered from cached Roblox WebView2 "
                       "API responses, including sender, recipient, subject, full "
                       "HTML body, created and updated times, and read/system state.",
        "author": "@AlexisBrignoni, Codex",
        "creation_date": "2026-07-28",
        "last_update_date": "2026-07-29",
        "requirements": "none",
        "category": "Roblox (Windows)",
        "notes": "Recovered from retained privatemessages.roblox.com response bodies. "
                 "The cache is partial and can hold multiple versions; identical "
                 "message versions are deduplicated by message ID and update time. "
                 "Message bodies are reported in full as stored HTML.",
        "paths": (
            "*/AppData/Local/Roblox/UniversalApp/WebView2/EBWebView/Default/"
            "Cache/Cache_Data/*",
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "mail",
        "sample_data": {
            "roblox_windows": "Roblox 0.732.23.7321040 Windows | 1 row",
        },
    },
}

import base64
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from scripts.ccl.indexeddb_to_json import load_indexeddb
from scripts.ccl import ccl_leveldb
from scripts.chromium.blockfile_cache import iter_entries
from scripts.chromium.local_storage import leveldb_folders, read_records
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.roblox import (
    chromium_datetime,
    compact_value,
    iso_datetime,
    read_json,
)

_TRANSITIONS = {
    0: "Link",
    1: "Typed",
    2: "Auto Bookmark",
    3: "Auto Subframe",
    4: "Manual Subframe",
    5: "Generated",
    6: "Start Page",
    7: "Form Submit",
    8: "Reload",
    9: "Keyword",
    10: "Keyword Generated",
}
_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)
_USER_ID_RE = re.compile(r"/users/(\d+)(?:/|$)")

_ACCOUNT_ENDPOINTS = {
    ("users.roblox.com", "/v1/birthdate"): "Birthdate",
    ("users.roblox.com", "/v1/gender"): "Gender",
    ("users.roblox.com", "/v1/description"): "Profile Description",
    ("accountinformation.roblox.com", "/v1/phone"): "Phone",
    ("accountinformation.roblox.com", "/v1/promotion-channels"):
        "Promotion Channels",
    ("accountsettings.roblox.com", "/v1/account/settings/account-country"):
        "Account Country",
    ("accountsettings.roblox.com", "/v1/emails"): "Email",
    ("apis.roblox.com",
     "/age-verification-service/v1/age-verification/verified-age"):
        "Verified Age",
    ("apis.roblox.com", "/user-settings-api/v1/account-insights/age-group"):
        "Age Group",
    ("apis.roblox.com", "/user-settings-api/v1/user-settings"):
        "User Settings",
    ("apis.roblox.com",
     "/parental-controls-api/v1/parental-controls/get-linked-parents"):
        "Linked Parents",
    ("apis.roblox.com",
     "/account-management-api/graphql/AccountSettingsQuery/"
     "pI4yH8pYRe-ns_3r0y_FIA"):
        "Account Settings",
}


def _yes(value):
    return "Yes" if value else ""


def _format_value(value):
    if isinstance(value, bytes):
        return value.hex()
    return compact_value(value)


def _json_fields(value, prefix=""):
    if isinstance(value, dict):
        if not value:
            yield prefix or "$", "{}"
        for key, nested in value.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            yield from _json_fields(nested, field)
    elif isinstance(value, list):
        if not value:
            yield prefix or "$", "[]"
        for index, nested in enumerate(value):
            field = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _json_fields(nested, field)
    else:
        yield prefix or "$", _format_value(value)


def _subject_user_id(url):
    parsed = urlsplit(url)
    match = _USER_ID_RE.search(parsed.path)
    if match:
        return match.group(1)
    query = parse_qs(parsed.query)
    child_user_id = query.get("childUserId", [])
    if child_user_id:
        return child_user_id[0]
    variables = query.get("variables", [])
    if variables:
        try:
            return str(json.loads(variables[0]).get("userId", ""))
        except (TypeError, ValueError):
            pass
    return ""


def _current_user_id(files_found):
    for file_found in map(str, files_found):
        if os.path.basename(file_found) != "appStorage.json":
            continue
        payload = read_json(file_found)
        if isinstance(payload, dict) and payload.get("UserId"):
            return str(payload["UserId"])
    return ""


def _account_evidence_type(url):
    parsed = urlsplit(url)
    direct = _ACCOUNT_ENDPOINTS.get((parsed.netloc, parsed.path))
    if direct:
        return direct
    if parsed.netloc == "users.roblox.com" and re.fullmatch(
            r"/v1/users/\d+", parsed.path):
        return "User Profile"
    if parsed.netloc == "accountinformation.roblox.com" and re.fullmatch(
            r"/v1/users/\d+/promotion-channels", parsed.path):
        return "Promotion Channels"
    if (parsed.netloc == "apis.roblox.com"
            and parsed.path == "/parental-controls-api/v1/parental-controls/consents"):
        return "Parental Control Consents"
    return ""


def _social_evidence_type(url):
    parsed = urlsplit(url)
    path = parsed.path
    if parsed.netloc == "friends.roblox.com":
        if path == "/v1/my/new-friend-requests/count":
            return "Friend Request Count"
        if re.fullmatch(r"/v1/users/\d+/friends/find", path):
            return "Friend Relationship"
        if re.fullmatch(r"/v1/users/\d+/friends/online", path):
            return "Online Friends"
    if parsed.netloc == "groups.roblox.com":
        if path == "/v1/groups/search":
            return "Group Search"
        if re.fullmatch(r"/v1/users/\d+/groups/roles", path):
            return "Group Membership & Role"
        if re.fullmatch(r"/v1/users/\d+/friends/groups/roles", path):
            return "Friends' Group Memberships"
    return ""


def _cache_json(entry):
    try:
        return json.loads(entry.decoded_body())
    except (TypeError, ValueError, UnicodeDecodeError):
        return None


@artifact_processor
def robloxWindowsCookieVault(context):
    data_headers = (
        "Format Version", "DPAPI Blob (base64)", "Decoded Blob Size (bytes)",
        "First 20 Bytes (hex)", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        payload = read_json(file_found)
        if not isinstance(payload, dict):
            continue
        encoded = payload.get("CookiesData", "")
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            decoded = b""
        data_list.append((
            payload.get("CookiesVersion", ""),
            encoded,
            len(decoded),
            decoded[:20].hex().upper(),
            context.get_relative_path(file_found),
        ))
        source_paths.append(file_found)
    logfunc(f"Roblox Windows Cookie Vault: {len(data_list)} vault(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxWebView2Cookies(context):
    data_headers = (
        ("Last Access", "datetime"), ("Created", "datetime"),
        ("Last Updated", "datetime"), ("Expires", "datetime"), "Domain", "Name",
        "Path", "Secure", "HttpOnly", "SameSite", "Encrypted Value (hex)",
        "Encrypted Value Size (bytes)", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        connection = open_sqlite_db_readonly(file_found)
        if not connection:
            continue
        try:
            rows = connection.execute(
                "SELECT last_access_utc, creation_utc, last_update_utc, "
                "expires_utc, host_key, name, path, is_secure, is_httponly, "
                "samesite, hex(encrypted_value), length(encrypted_value) "
                "FROM cookies ORDER BY last_access_utc").fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox WebView2 cookies: could not read '{file_found}': {ex}")
            connection.close()
            continue
        connection.close()
        if rows:
            source_paths.append(file_found)
        for row in rows:
            data_list.append((
                chromium_datetime(row[0]), chromium_datetime(row[1]),
                chromium_datetime(row[2]), chromium_datetime(row[3]),
                row[4], row[5], row[6], _yes(row[7]), _yes(row[8]), row[9],
                row[10], row[11], context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox WebView2 Cookies: {len(data_list)} cookie(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxWebView2History(context):
    data_headers = (
        ("Visited", "datetime"), "Title", "Host", "URL", "Visit ID",
        "From Visit ID", "Opener Visit ID", "Transition", "Transition Value",
        "Visit Duration (seconds)", "External Referrer", "Source File",
    )
    data_list = []
    source_paths = []
    for file_found in map(str, context.get_files_found()):
        connection = open_sqlite_db_readonly(file_found)
        if not connection:
            continue
        try:
            rows = connection.execute(
                "SELECT v.visit_time, u.title, u.url, v.id, v.from_visit, "
                "v.opener_visit, v.transition, v.visit_duration, "
                "v.external_referrer_url FROM visits v "
                "JOIN urls u ON u.id = v.url ORDER BY v.visit_time").fetchall()
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox WebView2 history: could not read '{file_found}': {ex}")
            connection.close()
            continue
        connection.close()
        if rows:
            source_paths.append(file_found)
        for visited, title, url, visit_id, from_visit, opener, transition, duration, referrer in rows:
            try:
                host = urlsplit(url).hostname or ""
            except ValueError:
                host = ""
            data_list.append((
                chromium_datetime(visited), title, host, url, visit_id,
                from_visit, opener, _TRANSITIONS.get(transition & 0xFF, "Other"),
                transition, duration / 1_000_000, referrer,
                context.get_relative_path(file_found),
            ))
    logfunc(f"Roblox WebView2 History: {len(data_list)} visit(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxWebView2LocalStorage(context):
    data_headers = (
        "Origin", "Key", "Value", "Value Length", "State", "Sequence",
        "Source LevelDB File",
    )
    data_list = []
    source_paths = []
    for folder in leveldb_folders(context.get_files_found()):
        try:
            records = list(read_records(folder))
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox WebView2 Local Storage: could not read '{folder}': {ex}")
            continue
        if records:
            source_paths.append(folder)
        for record in records:
            try:
                value = compact_value(json.loads(record.value))
            except (TypeError, ValueError):
                value = record.value
            data_list.append((
                record.origin, record.key, value, len(record.value),
                record.state, record.sequence,
                context.get_relative_path(record.source),
            ))
    data_list.sort(key=lambda row: row[5])
    logfunc(f"Roblox WebView2 Local Storage: {len(data_list)} record version(s).")
    return data_headers, data_list, "\n".join(source_paths)


def _session_storage_value(raw):
    if not raw:
        return ""
    if len(raw) % 2 == 0 and b"\x00" in raw:
        try:
            value = raw.decode("utf-16-le")
        except UnicodeDecodeError:
            value = raw.decode("utf-8", "replace")
    else:
        value = raw.decode("utf-8", "replace")
    try:
        return compact_value(json.loads(value))
    except (TypeError, ValueError):
        return value


@artifact_processor
def robloxWebView2SessionStorage(context):
    data_headers = (
        "Origin", "Namespace ID", "Map ID", "Key", "Value",
        "Value Size (bytes)", "State", "Sequence", "Source LevelDB File",
    )
    data_list = []
    source_paths = []
    for folder in leveldb_folders(
            context.get_files_found(), folder_name="Session Storage"):
        try:
            database = ccl_leveldb.RawLevelDb(folder)
            records = list(database.iterate_records_raw())
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(
                f"Roblox WebView2 Session Storage: could not read '{folder}': {ex}")
            continue
        namespaces = {}
        for record in records:
            key = record.user_key.decode("utf-8", "replace")
            if not key.startswith("namespace-") or not record.value:
                continue
            namespace_origin = key.removeprefix("namespace-")
            namespace_id, separator, origin = namespace_origin.partition("-")
            if separator:
                namespaces[record.value.decode("ascii", "replace")] = (
                    namespace_id, origin)
        for record in records:
            key = record.user_key.decode("utf-8", "replace")
            if not key.startswith("map-"):
                continue
            map_key = key.removeprefix("map-")
            map_id, separator, item_key = map_key.partition("-")
            if not separator:
                continue
            namespace_id, origin = namespaces.get(map_id, ("", ""))
            state = (
                record.state.name if hasattr(record.state, "name")
                else str(record.state)
            )
            data_list.append((
                origin,
                namespace_id,
                map_id,
                item_key,
                _session_storage_value(record.value),
                len(record.value),
                state,
                record.seq,
                context.get_relative_path(str(record.origin_file)),
            ))
            source_paths.append(str(record.origin_file))
    data_list.sort(key=lambda row: row[7])
    logfunc(
        f"Roblox WebView2 Session Storage: {len(data_list)} record version(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))


@artifact_processor
def robloxWebView2IndexedDB(context):
    data_headers = (
        "Origin", "Database", "Object Store", "Database Number", "Key",
        "Value", "Value Length", "Source LevelDB",
    )
    data_list = []
    source_paths = []
    folders = {}
    for file_found in map(str, context.get_files_found()):
        folder = os.path.dirname(file_found)
        if os.path.basename(folder).endswith(".indexeddb.leveldb"):
            folders.setdefault(os.path.realpath(folder), folder)
    for folder in folders.values():
        try:
            stores = load_indexeddb(folder, log=None)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox WebView2 IndexedDB: could not read '{folder}': {ex}")
            continue
        source_paths.append(folder)
        for store, records in stores.items():
            for record in records:
                value = _format_value(record.get("value", ""))
                data_list.append((
                    record.get("origin", ""),
                    record.get("db_name", ""),
                    store,
                    record.get("db_number", ""),
                    _format_value(record.get("key", "")),
                    value,
                    len(value),
                    context.get_relative_path(folder),
                ))
    logfunc(f"Roblox WebView2 IndexedDB: {len(data_list)} record version(s).")
    return data_headers, data_list, "\n".join(source_paths)


@artifact_processor
def robloxWebView2Cache(context):
    data_headers = (
        ("Requested", "datetime"), ("Response Received", "datetime"),
        ("Last Used", "datetime"), ("Created", "datetime"), "Host", "URL",
        "HTTP Status", "Content Type", "Content Encoding", "ETag",
        "Body Size (bytes)", "Entry Address", "Entry Block File",
        "Body Storage File",
    )
    data_list = []
    source_paths = []
    for entry in iter_entries(context.get_files_found()):
        try:
            host = urlsplit(entry.url).hostname or ""
        except ValueError:
            host = ""
        data_list.append((
            entry.request_time, entry.response_time, entry.last_used, entry.created,
            host, entry.url, entry.status_code, entry.content_type,
            entry.content_encoding, entry.etag, entry.body_size,
            f"0x{entry.address:08X}",
            context.get_relative_path(entry.source),
            context.get_relative_path(entry.body_source) if entry.body_source else "",
        ))
        source_paths.extend((entry.source, entry.body_source))
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox WebView2 Network Cache: {len(data_list)} response(s).")
    return data_headers, data_list, "\n".join(
        sorted({path for path in source_paths if path})[:50])


@artifact_processor
def robloxWebView2AccountData(context):
    data_headers = (
        ("Response Received", "datetime"), "Evidence Type", "Subject User ID",
        "Field", "Value", "Source URL", "Source Cache File",
    )
    data_list = []
    source_paths = []
    files_found = list(context.get_files_found())
    current_user_id = _current_user_id(files_found)
    for entry in iter_entries(files_found):
        evidence_type = _account_evidence_type(entry.url)
        if not evidence_type:
            continue
        payload = _cache_json(entry)
        if payload is None:
            continue
        source = entry.body_source or entry.source
        source_paths.append(source)
        for field, value in _json_fields(payload):
            data_list.append((
                entry.response_time,
                evidence_type,
                _subject_user_id(entry.url) or current_user_id,
                field,
                value,
                entry.url,
                context.get_relative_path(source),
            ))
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox WebView2 Account Data: {len(data_list)} field value(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))


@artifact_processor
def robloxWebView2SocialData(context):
    data_headers = (
        ("Response Received", "datetime"), "Activity Type", "Subject User ID",
        "Related User ID", "Username", "Display Name", "Group ID",
        "Group Name", "Role", "Search Query", "Result Count", "Source URL",
        "Source Cache File",
    )
    data_list = []
    source_paths = []
    files_found = list(context.get_files_found())
    current_user_id = _current_user_id(files_found)
    for entry in iter_entries(files_found):
        evidence_type = _social_evidence_type(entry.url)
        if not evidence_type:
            continue
        payload = _cache_json(entry)
        if payload is None:
            continue
        source = entry.body_source or entry.source
        source_paths.append(source)
        subject_user_id = _subject_user_id(entry.url) or current_user_id
        source_file = context.get_relative_path(source)
        if evidence_type == "Group Search":
            query = parse_qs(urlsplit(entry.url).query)
            data_list.append((
                entry.response_time,
                "Group Search",
                subject_user_id,
                "", "", "", "", "", "",
                query.get("keyword", [""])[0],
                payload.get("totalResults", ""),
                entry.url,
                source_file,
            ))
            continue
        if evidence_type == "Friend Request Count":
            count = payload.get("count", 0)
            if count:
                data_list.append((
                    entry.response_time, evidence_type, subject_user_id,
                    "", "", "", "", "", "", "", count, entry.url, source_file,
                ))
            continue
        if evidence_type in ("Friend Relationship", "Online Friends"):
            items = payload.get("PageItems") or payload.get("data") or []
            for item in items:
                data_list.append((
                    entry.response_time, evidence_type, subject_user_id,
                    item.get("id") or item.get("userId", ""),
                    item.get("name") or item.get("username", ""),
                    item.get("displayName", ""),
                    "", "", "", "", "", entry.url, source_file,
                ))
            continue
        if evidence_type == "Group Membership & Role":
            for item in payload.get("data") or []:
                group = item.get("group") or {}
                role = item.get("role") or {}
                data_list.append((
                    entry.response_time, evidence_type, subject_user_id,
                    "", "", "", group.get("id", ""), group.get("name", ""),
                    role.get("name", ""), "", "", entry.url, source_file,
                ))
            continue
        if evidence_type == "Friends' Group Memberships":
            for item in payload.get("data") or []:
                user = item.get("user") or {}
                for membership in item.get("groups") or []:
                    group = membership.get("group") or {}
                    role = membership.get("role") or {}
                    data_list.append((
                        entry.response_time, evidence_type, subject_user_id,
                        user.get("userId", ""), user.get("username", ""),
                        user.get("displayName", ""), group.get("id", ""),
                        group.get("name", ""), role.get("name", ""), "", "",
                        entry.url, source_file,
                    ))
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox WebView2 Social & Group Data: {len(data_list)} activity(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))


def _commerce_cache_type(url):
    parsed = urlsplit(url)
    if (parsed.netloc == "economy.roblox.com"
            and re.fullmatch(r"/v1/users/\d+/currency", parsed.path)):
        return "Robux Balance"
    if parsed.netloc == "ecsv2.roblox.com":
        query = parse_qs(parsed.query)
        if (query.get("evt", [""])[0] == "UserPurchaseFlow"
                or query.get("ctx", [""])[0] == "WebRobuxPurchase"):
            return "Purchase Flow Telemetry"
    return ""


@artifact_processor
def robloxWebView2Commerce(context):
    data_headers = (
        ("Client-Reported Event Time (lt)", "datetime"), "Activity Type",
        "Subject User ID",
        "Payment Session ID", "Purchase Flow UUID", "View Name", "Event Type",
        "Message", "Status", "Current View", "Robux Balance",
        "Robux Package IDs", "Subscription Product IDs", "Application Type",
        "Entry Point", "Storage State", "Storage Sequence",
        "Source URL or Key", "Source File",
    )
    data_list = []
    source_paths = []
    files_found = list(context.get_files_found())
    current_user_id = _current_user_id(files_found)
    for entry in iter_entries(files_found):
        evidence_type = _commerce_cache_type(entry.url)
        if not evidence_type:
            continue
        source = entry.body_source or entry.source
        source_paths.append(source)
        if evidence_type == "Purchase Flow Telemetry":
            query = parse_qs(urlsplit(entry.url).query, keep_blank_values=True)
            metadata = {}
            try:
                metadata = json.loads(query.get("event_metadata", ["{}"])[0])
            except (TypeError, ValueError):
                pass
            event_time = iso_datetime(query.get("lt", [""])[0])
            user_id = query.get("uid", [""])[0] or current_user_id
            session_id = metadata.get("paymentSessionId", "")
            data_list.append((
                event_time,
                evidence_type,
                user_id,
                session_id,
                query.get("purchase_flow_uuid", [""])[0],
                query.get("view_name", [""])[0],
                query.get("purchase_event_type", [""])[0],
                query.get("view_message", [""])[0],
                query.get("status", [""])[0],
                query.get("current_view_path", [""])[0],
                metadata.get("robuxBalance", ""),
                metadata.get("robuxPackageIds", ""),
                metadata.get("subscriptionProductIds", ""),
                "", "", "", "",
                entry.url,
                context.get_relative_path(source),
            ))
        else:
            payload = _cache_json(entry)
            if payload is None:
                continue
            data_list.append((
                entry.response_time,
                evidence_type,
                _subject_user_id(entry.url) or current_user_id,
                "", "", "", "", "", "", "",
                payload.get("robux", "") if isinstance(payload, dict) else "",
                "", "", "", "", "", "",
                entry.url,
                context.get_relative_path(source),
            ))

    for folder in leveldb_folders(files_found):
        try:
            records = read_records(folder)
            for record in records:
                if not record.key.startswith("paymentSession-"):
                    continue
                try:
                    payload = json.loads(record.value)
                except (TypeError, ValueError):
                    payload = {"value": record.value}
                source_paths.append(record.source)
                user_id = record.key.removeprefix("paymentSession-")
                data_list.append((
                    "", "Payment Session", user_id, payload.get("id", ""),
                    "", "", "", "", "", "", "", "", "",
                    payload.get("applicationType", ""),
                    payload.get("entryPoint", ""),
                    record.state,
                    record.sequence,
                    record.key,
                    context.get_relative_path(record.source),
                ))
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f"Roblox WebView2 commerce: could not read '{folder}': {ex}")
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox WebView2 Commerce Activity: {len(data_list)} activity record(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))


def _user_content_endpoint(url):
    parsed = urlsplit(url)
    endpoint_patterns = (
        ("Avatar Asset", "avatar.roblox.com",
         r"/v1/users/(\d+)/currently-wearing"),
        ("Favorite Asset", "catalog.roblox.com",
         r"/v1/favorites/users/(\d+)/favorites/\d+/assets"),
        ("Badge", "badges.roblox.com", r"/v1/users/(\d+)/badges"),
        ("Roblox Badge", "accountinformation.roblox.com",
         r"/v1/users/(\d+)/roblox-badges"),
        ("Created Experience", "games.roblox.com", r"/v2/users/(\d+)/games"),
    )
    for activity_type, host, pattern in endpoint_patterns:
        if parsed.netloc != host:
            continue
        match = re.fullmatch(pattern, parsed.path)
        if match:
            return activity_type, match.group(1), ""
    if parsed.netloc == "groups.roblox.com":
        match = re.fullmatch(r"/v2/groups/(\d+)/wall/posts", parsed.path)
        if match:
            return "Group Wall Post", "", match.group(1)
    return "", "", ""


def _content_items(activity_type, payload):
    if activity_type == "Avatar Asset":
        if not isinstance(payload, dict):
            return []
        return [
            {"id": asset_id, "itemType": "Avatar Asset"}
            for asset_id in payload.get("assetIds") or []
            if asset_id not in (None, "")
        ]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    return [
        item for item in (
            payload.get("data")
            or payload.get("collection")
            or payload.get("games")
            or []
        )
        if isinstance(item, dict)
    ]


@artifact_processor
def robloxWebView2UserContent(context):
    data_headers = (
        ("Response Received", "datetime"), "Activity Type", "Subject User ID",
        "Item ID", "Item Type", "Item Name", "Description or Message",
        "Related User ID", "Related Username", "Group ID",
        ("Created", "datetime"), ("Updated", "datetime"), "Source URL",
        "Source Cache File",
    )
    data_list = []
    source_paths = []
    seen = set()
    for entry in iter_entries(context.get_files_found()):
        activity_type, subject_user_id, group_id = _user_content_endpoint(entry.url)
        if not activity_type:
            continue
        payload = _cache_json(entry)
        if payload is None:
            continue
        for item in _content_items(activity_type, payload):
            related = item.get("creator") or item.get("poster") or {}
            if not isinstance(related, dict):
                related = {}
            role = related.get("role") or {}
            if not isinstance(role, dict):
                role = {}
            item_id = (
                item.get("id")
                or item.get("assetId")
                or item.get("placeId")
                or item.get("rootPlaceId")
            )
            if item_id in (None, ""):
                continue
            item_type = (
                item.get("itemType")
                or item.get("assetType")
                or item.get("type")
                or activity_type
            )
            description = item.get("description") or item.get("body") or ""
            related_user_id = (
                related.get("id")
                or related.get("userId")
                or related.get("creatorTargetId")
            )
            related_username = (
                related.get("name")
                or related.get("username")
                or related.get("displayName")
            )
            created = iso_datetime(item.get("created"))
            updated = iso_datetime(item.get("updated"))
            identity = (
                activity_type, subject_user_id, group_id, str(item_id),
                str(item_type), str(description), str(related_user_id),
                str(created), str(updated),
            )
            if identity in seen:
                continue
            seen.add(identity)
            source = entry.body_source or entry.source
            source_paths.append(source)
            data_list.append((
                entry.response_time,
                activity_type,
                subject_user_id,
                item_id,
                item_type,
                item.get("name") or role.get("name", ""),
                description,
                related_user_id or "",
                related_username or "",
                group_id,
                created,
                updated,
                entry.url,
                context.get_relative_path(source),
            ))
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox WebView2 User Content Activity: {len(data_list)} item(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))


@artifact_processor
def robloxPrivateMessages(context):
    data_headers = (
        ("Created", "datetime"), ("Updated", "datetime"), "Message ID",
        "Sender User ID", "Sender Username", "Sender Display Name",
        "Recipient User ID", "Recipient Username", "Recipient Display Name",
        "Subject", "Body (HTML)", "Read", "System Message",
        ("Cache Response Received", "datetime"), "Source URL", "Source Cache File",
    )
    data_list = []
    source_paths = []
    seen = set()
    for entry in iter_entries(context.get_files_found()):
        if "privatemessages.roblox.com/v1/messages?" not in entry.url:
            continue
        try:
            payload = json.loads(entry.decoded_body())
        except (TypeError, ValueError, UnicodeDecodeError):
            continue
        for message in payload.get("collection") or []:
            sender = message.get("sender") or {}
            recipient = message.get("recipient") or {}
            identity = (message.get("id"), message.get("updated"))
            if identity in seen:
                continue
            seen.add(identity)
            data_list.append((
                iso_datetime(message.get("created")),
                iso_datetime(message.get("updated")),
                message.get("id", ""),
                sender.get("id", ""),
                sender.get("name", ""),
                sender.get("displayName", ""),
                recipient.get("id", ""),
                recipient.get("name", ""),
                recipient.get("displayName", ""),
                message.get("subject", ""),
                message.get("body", ""),
                _yes(message.get("isRead")),
                _yes(message.get("isSystemMessage")),
                entry.response_time,
                entry.url,
                context.get_relative_path(entry.body_source or entry.source),
            ))
            source_paths.append(entry.body_source or entry.source)
    data_list.sort(
        key=lambda row: row[0] if isinstance(row[0], datetime) else _EPOCH_MIN)
    logfunc(f"Roblox Private Messages: {len(data_list)} message(s).")
    return data_headers, data_list, "\n".join(sorted(set(source_paths)))
