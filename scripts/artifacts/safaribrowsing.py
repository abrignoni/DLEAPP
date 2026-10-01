__artifacts_v2__ = {
    "safariHistory": {
        "name": "Safari History",
        "description": "Each row in History.db's history_visits table, "
                       "joined back to history_items for the URL, domain "
                       "and lifetime visit count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every History.db found is parsed, so a Mac with more than "
                 "one user account reports each account, tagged by Source "
                 "File. visit_time is Mac Absolute Time in seconds since "
                 "2001-01-01, confirmed against the validation image. "
                 "Tags and Tag Identifiers list the title and identifier of "
                 "each history_tags row that a history_items_to_tags row "
                 "links to the visit's history item, ordered by the link's "
                 "timestamp and separated by a semicolon and a space. The "
                 "link is to the history item, so each visit of that item shows the same tags. Tags "
                 "and Tag Identifiers are blank when the item has no link or "
                 "the database lacks either table; they were blank on every "
                 "row of dleapp_safari_bigsur, whose two tag tables are "
                 "empty. Safari History Tags reports the tags themselves. "
                 "A logical extraction can hold one user's History.db under "
                 "Users/ and again under System/Volumes/Data/Users/. The two "
                 "are read as one store: a visit both copies hold with the "
                 "same values and tags is reported once, with the Source File "
                 "of the copy under Users/, and a visit only one copy holds, "
                 "or that differs between them, is reported from the copy "
                 "that holds it. On the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key) History.db was "
                 "byte-identical under the two paths, its -wal differed, and "
                 "each copy held the same 139 visits, which are reported "
                 "once; 11 of them show a tag. The differing-copies case was "
                 "exercised with constructed databases only.",
        "paths": (
            "*/Library/Safari/History.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), History.db | 22 history items, 27 visits",
        },
    },
    "safariHistoryTags": {
        "name": "Safari History Tags",
        "description": "Tags stored in Safari's History.db and the history "
                       "items each tag is linked to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "One row per history_items_to_tags row, which links a "
                 "history_tags row to a history_items row, and one row for "
                 "each history_tags row that no link names. Tag Modified is "
                 "history_tags.modification_timestamp and Item Tagged is "
                 "history_items_to_tags.timestamp, both read as Mac Absolute "
                 "Time (seconds since 2001-01-01) and shown in UTC. Tag is "
                 "the title "
                 "column, Identifier the identifier column and URL the linked "
                 "item's url. Item Count is history_tags.item_count as "
                 "stored, Linked Items is the number of links that name the "
                 "tag in the same database, counted by this artifact, and "
                 "Type and Level are the stored integers. On the row of a tag "
                 "with no link, Item Tagged and URL are blank and Linked "
                 "Items is 0. A link that names a tag id history_tags lacks "
                 "would not be reported, and a link that names a missing "
                 "history item would show a blank URL. No tested database "
                 "held either. "
                 "The CREATE statements stored in the database allow one link "
                 "per item and tag (UNIQUE(history_item, tag_id) ON CONFLICT "
                 "REPLACE) and define two triggers that add 1 to item_count "
                 "after a link is inserted and subtract 1 before a link is "
                 "deleted. "
                 "Measured on the public MacBook Pro logical extraction "
                 "(macOS 15.4, not a registered corpus key), which holds 4 "
                 "tags and 5 links: every tag had a link, Item Count was "
                 "higher than Linked Items on 1 of the 4 tags and lower on "
                 "none, Tag Modified equalled the tag's latest Item Tagged "
                 "value on all 4, and Item Tagged was within 60 seconds of a "
                 "visit to the linked item on 4 of the 5 links. What event "
                 "either time records is not established. Type held one "
                 "value, 1, and Level held one value, 200, on all 4 tags, "
                 "and what they mean is not established. Each Identifier was the letter Q followed by "
                 "digits, the form of a Wikidata item identifier. How Safari "
                 "chooses a tag for a page is not established. "
                 "dleapp_safari_bigsur (macOS 11.2.1) holds both tables with "
                 "no rows. A tag with no link, and a History.db without the "
                 "two tables, were exercised with constructed databases "
                 "only. "
                 "A logical extraction can hold one user's History.db under "
                 "Users/ and again under System/Volumes/Data/Users/. The two "
                 "are read as one store: a row both copies hold with the same "
                 "values is reported once, with the Source File of the copy "
                 "under Users/, and a row only one copy holds, or that "
                 "differs between them, is reported from the copy that holds "
                 "it. The MacBook Pro's 5 rows were held by both copies and "
                 "are reported once. "
                 "The two tables and the Wikidata form of the identifier are "
                 "described in the reference. Reference: Yogesh Khatri, 'Tags "
                 "in Safari History db', "
                 "https://www.swiftforensics.com/2026/10/tags-in-safari-history-db.html",
        "paths": (
            "*/Library/Safari/History.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "tag",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (both "
                "tag tables are empty)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (both "
                "tag tables are empty)",
        },
    },
    "safariBookmarks": {
        "name": "Safari Bookmarks",
        "description": "Each leaf bookmark in Bookmarks.plist (Bookmarks "
                       "Bar, Bookmarks Menu and Reading List) with its "
                       "folder path, title and URL.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every Bookmarks.plist found is parsed, tagged by Source "
                 "File. Leaf title is read from URIDictionary.title, not the "
                 "top-level Title key (that key only exists on folder nodes), "
                 "confirmed against real bookmarks-bar entries.",
        "paths": (
            "*/Library/Safari/Bookmarks.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "bookmark",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), Bookmarks.plist | 7 bookmarks-bar "
                "entries (Bookmarks Menu and Reading List empty on this "
                "image)",
        },
    },
    "safariTopSites": {
        "name": "Safari Top Sites",
        "description": "Each entry in TopSites.plist's TopSites list, "
                       "flagging which are Apple's shipped built-in "
                       "defaults versus frecency-derived from real "
                       "browsing.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every TopSites.plist found is parsed, tagged by Source "
                 "File. On the validation image all entries were built-in "
                 "defaults (TopSiteIsBuiltIn true); that column is included "
                 "so an analyst can distinguish earned top sites from "
                 "defaults on other data.",
        "paths": (
            "*/Library/Safari/TopSites.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "star",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), TopSites.plist | 12 entries, all "
                "TopSiteIsBuiltIn true on this image",
        },
    },
    "safariRecentlyClosedTabs": {
        "name": "Safari Recently Closed Tabs",
        "description": "Each tab in RecentlyClosedTabs.plist's "
                       "ClosedTabOrWindowPersistentStates: window and "
                       "tab UUIDs, close time, title and URL.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every RecentlyClosedTabs.plist found is parsed, tagged by "
                 "Source File. Each tab also carries a large SessionState "
                 "NSKeyedArchiver-style binary blob (per-tab back/forward "
                 "navigation history); it is not decoded, only its size is "
                 "reported.",
        "paths": (
            "*/Library/Safari/RecentlyClosedTabs.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "x-circle",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), RecentlyClosedTabs.plist | 2 closed "
                "windows, 1 tab each",
        },
    },
    "safariCloudTabs": {
        "name": "Safari iCloud Tabs (CloudTabs.db)",
        "description": "Tabs synced to this Mac from other Apple devices "
                       "via iCloud Tabs/Handoff, joined to the "
                       "originating device's name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every CloudTabs.db found is parsed, tagged by Source File. "
                 "system_fields and position are opaque NSKeyedArchiver/zlib "
                 "CloudKit-metadata blobs and are not decoded. "
                 "cloud_tab_close_requests exists in the schema but is not "
                 "read.",
        "paths": (
            "*/Library/Safari/CloudTabs.db*",
        ),
        "output_types": ["standard"],
        "artifact_icon": "cloud",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), CloudTabs.db | 2 synced tabs from 1 "
                "device",
        },
    },
    "safariLastSession": {
        "name": "Safari Last Session (Open Tabs)",
        "description": "Windows and tabs that were open the last time "
                       "Safari quit, from LastSession.plist: title, "
                       "URL, last-visit time and whether the window was "
                       "private.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-01",
        "last_update_date": "2026-09-01",
        "requirements": "none",
        "category": "Safari (macOS)",
        "notes": "Every LastSession.plist found is parsed, tagged by Source "
                 "File. Same tab shape as RecentlyClosedTabs, including the "
                 "undecoded SessionState blob. LastVisitTime is Mac Absolute "
                 "Time in seconds, the same unit as History.db.",
        "paths": (
            "*/Library/Safari/LastSession.plist",
        ),
        "output_types": ["standard"],
        "artifact_icon": "layout",
        "sample_data": {
            "dleapp_safari_bigsur": "macOS Big Sur (Josh Hickman public test "
                "image, thisisdfir), LastSession.plist | 1 open window, 2 "
                "tabs",
        },
    },
}

import os
import plistlib
import re
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

# Seconds between the Unix epoch (1970-01-01) and the Mac/Cocoa epoch
# (2001-01-01). History.db visit_time and LastSession/RecentlyClosedTabs
# LastVisitTime are both Mac Absolute Time in seconds, confirmed against the
# validation image.
_MAC_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _mac_abs_s_to_utc(value):
    """Mac/Cocoa Absolute Time in SECONDS since 2001-01-01."""
    if not value:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    try:
        return _MAC_EPOCH + timedelta(seconds=value)
    except (OverflowError, OSError, ValueError):
        return None


def _files_named(files_found, basename):
    """Every file whose basename matches, one per user account."""
    return [p for p in files_found if os.path.basename(p) == basename]


def _load_plist(path):
    try:
        with open(path, "rb") as handle:
            return plistlib.load(handle)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"Safari: could not parse plist '{path}': {ex}")
        return None


# A logical extraction can hold the Data volume at its root and again under
# System/Volumes/Data/. Removing that prefix gives both copies of a store one key.
_DATA_VOLUME = re.compile(r"(^|/)System/Volumes/Data/")


def _history_stores(context):
    """(staged path, evidence path, store key) per History.db, with a copy
    under System/Volumes/Data/ after the copy at the root."""
    stores = []
    for source in _files_named([str(f) for f in context.get_files_found()],
                               "History.db"):
        relative_source = context.get_relative_path(source)
        normal = relative_source.replace("\\", "/")
        store = _DATA_VOLUME.sub(r"\1", normal, count=1)
        stores.append((store, store != normal, source, relative_source))
    stores.sort()
    return [(source, relative_source, store)
            for store, _second, source, relative_source in stores]


def _has_tag_tables(database):
    names = {row[0] for row in database.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    return {"history_tags", "history_items_to_tags"} <= names


def _item_tags(database):
    """history_items.id -> (tag titles, tag identifiers), ordered by link
    timestamp."""
    if not _has_tag_tables(database):
        return {}
    tags = {}
    for item, title, identifier in database.execute("""
            SELECT l.history_item, t.title, t.identifier
            FROM history_items_to_tags l
            JOIN history_tags t ON t.id = l.tag_id
            ORDER BY l.history_item, l.timestamp, t.id"""):
        titles, identifiers = tags.setdefault(item, ([], []))
        titles.append(title)
        identifiers.append(identifier)
    return {item: ("; ".join(titles), "; ".join(identifiers))
            for item, (titles, identifiers) in tags.items()}


_HISTORY_QUERY = """
    SELECT
        hv.visit_time, hi.url, hi.domain_expansion, hv.title,
        hi.visit_count, hv.load_successful, hv.http_non_get,
        hv.synthesized, hv.origin, hv.id, hi.id
    FROM history_visits hv
    JOIN history_items hi ON hi.id = hv.history_item
    ORDER BY hv.visit_time DESC
"""

# One row per link between a tag and a history item, and one row for a tag no
# link names.
_TAGS_QUERY = """
    SELECT
        t.modification_timestamp, l.timestamp, t.title, t.identifier, hi.url,
        t.item_count,
        (SELECT COUNT(*) FROM history_items_to_tags c WHERE c.tag_id = t.id),
        t.type, t.level, t.id, l.history_item
    FROM history_tags t
    LEFT JOIN history_items_to_tags l ON l.tag_id = t.id
    LEFT JOIN history_items hi ON hi.id = l.history_item
    ORDER BY t.modification_timestamp DESC, t.id, l.timestamp DESC
"""


@artifact_processor
def safariHistory(context):
    data_headers = (
        ("Visit Time", "datetime"), "URL", "Domain", "Visit Title",
        "Item Visit Count (lifetime)", "Load Successful", "HTTP Non-GET",
        "Synthesized", "Origin (raw)", "Tags", "Tag Identifiers",
        "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    for source, relative_source, store in _history_stores(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        item_tags = _item_tags(database)
        for row in database.execute(_HISTORY_QUERY):
            (visit_time, url, domain, title, visit_count, load_successful,
             http_non_get, synthesized, origin, _visit_id, item_id) = row
            tags, tag_identifiers = item_tags.get(item_id, ("", ""))
            record = (store, tuple(row), tags, tag_identifiers)
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                _mac_abs_s_to_utc(visit_time), url or "", domain or "",
                title or "", visit_count if visit_count is not None else "",
                "Yes" if load_successful else "No",
                "Yes" if http_non_get else "",
                "Yes" if synthesized else "",
                origin if origin is not None else "", tags, tag_identifiers,
                relative_source,
            ))
        database.close()

    logfunc(f"Safari History: {len(data_list)} visit(s) across "
            f"{len(read_sources)} History.db file(s); {repeated} visit(s) "
            f"held by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariHistoryTags(context):
    data_headers = (
        ("Tag Modified", "datetime"), ("Item Tagged", "datetime"), "Tag",
        "Identifier", "URL", "Item Count", "Linked Items", "Type", "Level",
        "Source File",
    )
    data_list = []
    read_sources = []
    seen = set()
    repeated = 0
    for source, relative_source, store in _history_stores(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        read_sources.append(relative_source)
        if not _has_tag_tables(database):
            database.close()
            continue
        for row in database.execute(_TAGS_QUERY):
            (modified, tagged, title, identifier, url, item_count, linked,
             tag_type, level, _tag_id, _item_id) = row
            record = (store, tuple(row))
            if record in seen:
                repeated += 1
                continue
            seen.add(record)
            data_list.append((
                _mac_abs_s_to_utc(modified), _mac_abs_s_to_utc(tagged),
                title, identifier, url or "", item_count, linked, tag_type,
                level, relative_source,
            ))
        database.close()

    logfunc(f"Safari History Tags: {len(data_list)} row(s) across "
            f"{len(read_sources)} History.db file(s); {repeated} row(s) held "
            f"by a second copy of a store were not reported again.")
    return data_headers, data_list, "\n".join(read_sources)


def _walk_bookmarks(node, folder_path, rows):
    if not isinstance(node, dict):
        return
    node_type = node.get("WebBookmarkType")

    if node_type == "WebBookmarkTypeLeaf":
        title = (node.get("URIDictionary") or {}).get("title", "")
        rows.append((
            folder_path, title, node.get("URLString", ""),
            node.get("WebBookmarkUUID", ""),
        ))
        return

    # Folder/list node (WebBookmarkTypeList) or the unlabeled root dict: both
    # use 'Children'; proxy nodes (e.g. the History shortcut) have no useful
    # children and simply fall through with nothing appended.
    name = node.get("Title", "")
    child_path = f"{folder_path}/{name}" if folder_path and name else (name or folder_path)
    for child in node.get("Children", []) or []:
        _walk_bookmarks(child, child_path, rows)


@artifact_processor
def safariBookmarks(context):
    data_headers = ("Folder Path", "Title", "URL", "Bookmark UUID", "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    data_list = []
    read_sources = []
    for source in _files_named(files_found, "Bookmarks.plist"):
        plist = _load_plist(source)
        if plist is None:
            continue
        relative_source = context.get_relative_path(source)
        rows = []
        _walk_bookmarks(plist, "", rows)
        for row in rows:
            data_list.append(row + (relative_source,))
        if rows:
            read_sources.append(relative_source)

    logfunc(f"Safari Bookmarks: {len(data_list)} bookmark(s) across "
            f"{len(read_sources)} Bookmarks.plist file(s).")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariTopSites(context):
    data_headers = ("Title", "URL", "Built-in Default", "Source File")
    files_found = [str(f) for f in context.get_files_found()]
    data_list = []
    read_sources = []
    for source in _files_named(files_found, "TopSites.plist"):
        plist = _load_plist(source)
        if plist is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        for site in plist.get("TopSites", []) or []:
            data_list.append((
                site.get("TopSiteTitle", ""), site.get("TopSiteURLString", ""),
                "Yes" if site.get("TopSiteIsBuiltIn") else "No", relative_source,
            ))
            rows_here += 1
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Safari Top Sites: {len(data_list)} entr(ies) across "
            f"{len(read_sources)} TopSites.plist file(s).")
    return data_headers, data_list, "\n".join(read_sources)


def _tab_rows(window):
    window_uuid = window.get("WindowUUID", "")
    window_closed = window.get("DateClosed")
    is_private = "Yes" if window.get("IsPrivateWindow") else "No"
    rows = []
    for tab in window.get("TabStates", []) or []:
        session_state = tab.get("SessionState")
        state_size = len(session_state) if isinstance(session_state, (bytes, bytearray)) else ""
        rows.append((
            tab.get("TabTitle", ""), tab.get("TabURL", ""),
            tab.get("DateClosed") or window_closed,
            tab.get("LastVisitTime"),
            window_uuid, tab.get("TabUUID", ""),
            tab.get("TabIndex", ""), is_private, state_size,
        ))
    return rows


@artifact_processor
def safariRecentlyClosedTabs(context):
    data_headers = (
        "Tab Title", "URL", ("Closed", "datetime"), ("Last Visit Time", "datetime"),
        "Window UUID", "Tab UUID", "Tab Index", "Private Window",
        "Session State Size (bytes)", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    data_list = []
    read_sources = []
    for source in _files_named(files_found, "RecentlyClosedTabs.plist"):
        plist = _load_plist(source)
        if plist is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        for entry in plist.get("ClosedTabOrWindowPersistentStates", []) or []:
            window = entry.get("PersistentState", {}) or {}
            for title, url, closed, last_visit, w_uuid, t_uuid, idx, priv, state_size in _tab_rows(window):
                data_list.append((
                    title, url, closed, _mac_abs_s_to_utc(last_visit),
                    w_uuid, t_uuid, idx, priv, state_size, relative_source,
                ))
                rows_here += 1
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Safari Recently Closed Tabs: {len(data_list)} tab(s) across "
            f"{len(read_sources)} file(s).")
    return data_headers, data_list, "\n".join(read_sources)


@artifact_processor
def safariLastSession(context):
    data_headers = (
        "Tab Title", "URL", ("Window Closed", "datetime"),
        ("Last Visit Time", "datetime"), "Window UUID", "Tab UUID",
        "Tab Index", "Private Window", "Session State Size (bytes)",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    data_list = []
    read_sources = []
    for source in _files_named(files_found, "LastSession.plist"):
        plist = _load_plist(source)
        if plist is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        for window in plist.get("SessionWindows", []) or []:
            for title, url, closed, last_visit, w_uuid, t_uuid, idx, priv, state_size in _tab_rows(window):
                data_list.append((
                    title, url, closed, _mac_abs_s_to_utc(last_visit),
                    w_uuid, t_uuid, idx, priv, state_size, relative_source,
                ))
                rows_here += 1
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Safari Last Session: {len(data_list)} tab(s) across "
            f"{len(read_sources)} file(s).")
    return data_headers, data_list, "\n".join(read_sources)


_CLOUDTABS_QUERY = """
    SELECT
        ct.tab_uuid, ct.title, ct.url, ct.is_pinned, ct.is_showing_reader,
        ct.reader_scroll_position_page_index, ctd.device_name,
        ctd.device_uuid, ctd.last_modified, ctd.is_ephemeral_device
    FROM cloud_tabs ct
    LEFT JOIN cloud_tab_devices ctd ON ctd.device_uuid = ct.device_uuid
    ORDER BY ctd.last_modified DESC, ct.rowid, ctd.rowid
"""


@artifact_processor
def safariCloudTabs(context):
    data_headers = (
        "Tab Title", "URL", "Device Name", "Device UUID",
        ("Device Last Modified", "datetime"), "Ephemeral Device",
        "Pinned", "Showing Reader", "Reader Scroll Page", "Tab UUID",
        "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    data_list = []
    read_sources = []
    for source in _files_named(files_found, "CloudTabs.db"):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        for row in database.execute(_CLOUDTABS_QUERY):
            (tab_uuid, title, url, is_pinned, is_reader, reader_page,
             device_name, device_uuid, last_modified, is_ephemeral) = row
            data_list.append((
                title or "", url or "", device_name or "", device_uuid or "",
                _mac_abs_s_to_utc(last_modified),
                "Yes" if is_ephemeral else "",
                "Yes" if is_pinned else "", "Yes" if is_reader else "",
                reader_page if reader_page is not None else "",
                tab_uuid or "", relative_source,
            ))
            rows_here += 1
        database.close()
        if rows_here:
            read_sources.append(relative_source)

    logfunc(f"Safari iCloud Tabs: {len(data_list)} synced tab(s) across "
            f"{len(read_sources)} CloudTabs.db file(s).")
    return data_headers, data_list, "\n".join(read_sources)
