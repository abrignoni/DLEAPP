import sqlite3

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               convert_cocoa_core_data_ts_to_utc, logfunc)
from scripts.macos_plists import fold_view_rows, unique_sources

# macOS keeps knowledgeC.db in two places: the per-user store at
# ~/Library/Application Support/Knowledge/knowledgeC.db and the system store at
# /private/var/db/CoreDuet/Knowledge/knowledgeC.db. The pattern
# '*/Knowledge/knowledgeC.db*' matches both. Each processor reads every store
# found, with its -wal, and tags each row with its Source File, so the two
# stores and a Mac with more than one user account stay apart.
#
# A row is a ZOBJECT row of the entity named Event in Z_PRIMARYKEY. Metadata
# columns are resolved from each store's live schema, because the columns differ
# between store versions, and a column a store lacks is left blank. Apple's code
# statements in the notes were read on macOS 27.2.1 (26B131) unless a note says
# otherwise. They are not extended to other macOS builds.

__artifacts_v2__ = {
    "knowledgeCInFocus": {
        "name": "KnowledgeC - App In Focus",
        "description": "/app/inFocus events from knowledgeC.db: the stored bundle identifier with the start "
                       "and end time of each event.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/app/inFocus as an app's transition to focal state. On macOS 27.2.1 (26B131) the "
                 "monitor sets a row's start when it builds the event and its end when it records the "
                 "next state. Older builds were not read. On the one macOS test image with this "
                 "stream, End Time does not always equal the next row's Start Time, and why is not "
                 "established. Start Time and End Time are stored as seconds since 2001-01-01 UTC and "
                 "shown in UTC. The store write was read in Apple's code on macOS 27.2.1 (26B131); "
                 "other macOS builds were not read. A row stored with Apple's open-ended end date "
                 "(NSDate distantFuture) shows a blank End Time and Duration (s); no row of this "
                 "stream in the three macOS test images holds that date. Stored On This Device is "
                 "ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied to this "
                 "store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) "
                 "the offset of the event's time zone when the row was written, which can differ from "
                 "its offset at the event across a daylight saving change. Source Device ID is "
                 "ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source device "
                 "ID to identify a peer device. The code that sets it on an event was not traced, so a"
                 " row that holds one should not be assumed to describe this Mac. A blank Source "
                 "Device ID means the row has no source record, or its ZDEVICEID is empty. On the "
                 "eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time and End Time are whole seconds and Stored On This "
                 "Device holds a fraction of a second, which the report cuts to the whole second. "
                 "Event Zone UTC Offset At Write held two values on dleapp_macos_bigsur. A copy of "
                 "knowledgeC.db under System/Volumes/Data that is byte-identical, -wal included, to "
                 "one already read is not read again. Copies of one file under System/Volumes/Data/ or"
                 " System/Volumes/Update/mnt1/ that differ are all read; a row identical in every "
                 "other column in more than one copy is reported as often as the copy holding it most "
                 "often holds it, normally once, and its Source File lists each file that held it, one"
                 " per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "eye",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 135 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
    "knowledgeCAppUsage": {
        "name": "KnowledgeC - App Usage",
        "description": "/app/usage events from knowledgeC.db: the stored bundle identifier with the start "
                       "and end time of each event.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/app/usage as usage of an application. On macOS 27.2.1 (26B131) the monitor takes "
                 "the start from its caller. The macOS 11.2.1 and 15.4 code was not read, so what "
                 "start and end mark on those versions is not established. The usageType and "
                 "isUsageTrusted metadata are not shown, because their meaning is not established. "
                 "Start Time and End Time are stored as seconds since 2001-01-01 UTC and shown in UTC."
                 " The store write was read in Apple's code on macOS 27.2.1 (26B131); other macOS "
                 "builds were not read. A row stored with Apple's open-ended end date (NSDate "
                 "distantFuture) shows a blank End Time and Duration (s); no row of this stream in the"
                 " three macOS test images holds that date. Stored On This Device is "
                 "ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied to this "
                 "store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) "
                 "the offset of the event's time zone when the row was written, which can differ from "
                 "its offset at the event across a daylight saving change. Source Device ID is "
                 "ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source device "
                 "ID to identify a peer device. The code that sets it on an event was not traced, so a"
                 " row that holds one should not be assumed to describe this Mac. A blank Source "
                 "Device ID means the row has no source record, or its ZDEVICEID is empty. On the "
                 "eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time and End Time are whole seconds and Stored On This "
                 "Device holds a fraction of a second, which the report cuts to the whole second. "
                 "Event Zone UTC Offset At Write held one value on every row of "
                 "magnet2021_macos_bigsur and mvs2026_macbookpro_macos15, and two values on "
                 "dleapp_macos_bigsur. Stored On This Device fell in the same whole second as End Time"
                 " on all 13 rows of magnet2021_macos_bigsur, so the two read the same in the report. "
                 "A copy of knowledgeC.db under System/Volumes/Data that is byte-identical, -wal "
                 "included, to one already read is not read again. Copies of one file under "
                 "System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are all read; a row "
                 "identical in every other column in more than one copy is reported as often as the "
                 "copy holding it most often holds it, normally once, and its Source File lists each "
                 "file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 220 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 13 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 202 rows",
        },
    },
    "knowledgeCWebUsage": {
        "name": "KnowledgeC - Web Usage",
        "description": "/app/webUsage events from knowledgeC.db: the stored bundle identifier, web domain "
                       "and webpage URL, with start and end times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/app/webUsage as granular web usage in an app. The code that writes this stream was "
                 "not located, so what Start Time and End Time mark is not established. Web Domain and"
                 " Webpage URL are the webDomain and webpageURL metadata attributes, shown as stored. "
                 "The usageType and isUsageTrusted metadata are not shown, because their meaning is "
                 "not established. Start Time and End Time are stored as seconds since 2001-01-01 UTC "
                 "and shown in UTC. The store write was read in Apple's code on macOS 27.2.1 (26B131);"
                 " other macOS builds were not read. A row stored with Apple's open-ended end date "
                 "(NSDate distantFuture) shows a blank End Time and Duration (s); no row of this "
                 "stream in the three macOS test images holds that date. Stored On This Device is "
                 "ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied to this "
                 "store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) "
                 "the offset of the event's time zone when the row was written, which can differ from "
                 "its offset at the event across a daylight saving change. Source Device ID is "
                 "ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source device "
                 "ID to identify a peer device. The code that sets it on an event was not traced, so a"
                 " row that holds one should not be assumed to describe this Mac. A blank Source "
                 "Device ID means the row has no source record, or its ZDEVICEID is empty. On the "
                 "eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time and End Time are whole seconds and Stored On This "
                 "Device holds a fraction of a second, which the report cuts to the whole second. "
                 "Event Zone UTC Offset At Write held one value on every row of dleapp_macos_bigsur "
                 "and mvs2026_macbookpro_macos15. Bundle ID held one value on every row of "
                 "dleapp_macos_bigsur and mvs2026_macbookpro_macos15. Stored On This Device fell in "
                 "the same whole second as End Time on all 21 rows of dleapp_macos_bigsur, so the two "
                 "read the same in the report. A copy of knowledgeC.db under System/Volumes/Data that "
                 "is byte-identical, -wal included, to one already read is not read again. Copies of "
                 "one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are "
                 "all read; a row identical in every other column in more than one copy is reported as"
                 " often as the copy holding it most often holds it, normally once, and its Source "
                 "File lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 21 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 74 rows",
        },
    },
    "knowledgeCSafariHistory": {
        "name": "KnowledgeC - Safari History",
        "description": "/safari/history events from knowledgeC.db: the stored URL and title, with the start "
                       "time of each event.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/safari/history as Safari browsing history. On macOS 27.2.1 (26B131) the row is "
                 "built from a donated searchable item and its start is the time of that conversion, "
                 "which may not be the page load. Older builds were not read. URL is the item's "
                 "contentURL and Title its title on that build. Start Time is stored as seconds since "
                 "2001-01-01 UTC and shown in UTC. The store write was read in Apple's code on macOS "
                 "27.2.1 (26B131); other macOS builds were not read. Stored On This Device is "
                 "ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied to this "
                 "store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) "
                 "the offset of the event's time zone when the row was written, which can differ from "
                 "its offset at the event across a daylight saving change. Source Device ID is "
                 "ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source device "
                 "ID to identify a peer device. The code that sets it on an event was not traced, so a"
                 " row that holds one should not be assumed to describe this Mac. A blank Source "
                 "Device ID means the row has no source record, or its ZDEVICEID is empty. On the "
                 "eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time is a whole second and Stored On This Device holds a "
                 "fraction of a second, which the report cuts to the whole second. Event Zone UTC "
                 "Offset At Write held one value on every row of dleapp_macos_bigsur. A copy of "
                 "knowledgeC.db under System/Volumes/Data that is byte-identical, -wal included, to "
                 "one already read is not read again. Copies of one file under System/Volumes/Data/ or"
                 " System/Volumes/Update/mnt1/ that differ are all read; a row identical in every "
                 "other column in more than one copy is reported as often as the copy holding it most "
                 "often holds it, normally once, and its Source File lists each file that held it, one"
                 " per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "compass",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 10 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
    "knowledgeCAppIntents": {
        "name": "KnowledgeC - App Intents",
        "description": "/app/intents events from knowledgeC.db: the stored intent domain, class, verb, "
                       "direction, handling status and source bundle identifier, with start and end times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/app/intents as active application intents. On macOS 27.2.1 (26B131) start and end "
                 "come from the interaction's date interval, and the time the event is built is used "
                 "when it has none. Older builds were not read. Direction and Handling Status use the "
                 "names in Apple's Intents headers. Intent Class and Intent Verb are the intentClass "
                 "and intentVerb metadata attributes, shown as stored. Derived Intent ID and Intent "
                 "Type are not interpreted: their meaning is not established, and they are shown as "
                 "stored. The serialized interaction is not decoded here. Start Time and End Time are "
                 "stored as seconds since 2001-01-01 UTC and shown in UTC. The store write was read in"
                 " Apple's code on macOS 27.2.1 (26B131); other macOS builds were not read. A row "
                 "stored with Apple's open-ended end date (NSDate distantFuture) shows a blank End "
                 "Time and Duration (s); no row of this stream in the three macOS test images holds "
                 "that date. Stored On This Device is ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the"
                 " time the row was copied to this store. Event Zone UTC Offset At Write is "
                 "ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) the offset of the event's time zone when "
                 "the row was written, which can differ from its offset at the event across a daylight"
                 " saving change. Source Device ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) "
                 "Apple's sync code uses a source device ID to identify a peer device. The code that "
                 "sets it on an event was not traced, so a row that holds one should not be assumed to"
                 " describe this Mac. A blank Source Device ID means the row has no source record, or "
                 "its ZDEVICEID is empty. On the eleven streams this module reads, every row with a "
                 "Source Device ID has a ZCREATIONDATE (not shown) that differs from "
                 "ZLOCALCREATIONDATE, and every row without one has the two equal. Rows with a Source "
                 "Device ID occur only on dleapp_macos_bigsur. The sync code of the macOS builds on "
                 "the test images was not read. A stored value outside the sourced labels is shown as "
                 "the value followed by (not established). The -wal sidecar is read alongside the "
                 "database. On every row of the three macOS test images, Start Time and End Time are "
                 "whole seconds and Stored On This Device holds a fraction of a second, which the "
                 "report cuts to the whole second. Event Zone UTC Offset At Write held one value on "
                 "every row of dleapp_macos_bigsur. A copy of knowledgeC.db under System/Volumes/Data "
                 "that is byte-identical, -wal included, to one already read is not read again. Copies"
                 " of one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ "
                 "are all read; a row identical in every other column in more than one copy is "
                 "reported as often as the copy holding it most often holds it, normally once, and its"
                 " Source File lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "zap",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 134 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
    "knowledgeCNotificationUsage": {
        "name": "KnowledgeC - Notification Usage",
        "description": "/notification/usage events from knowledgeC.db: the stored notification event name, "
                       "bundle identifier and notification identifier, with the event time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/notification/usage as lock screen, banner or history notification usage. "
                 "Notification Event is shown as stored. The strings are Apple's event type names, but"
                 " what each means for this stream is not established, and the code that writes the "
                 "stream was not located. Bundle ID is blank on rows where the metadata holds no "
                 "value. Notification ID is the identifier metadata attribute, shown as stored. Start "
                 "Time is stored as seconds since 2001-01-01 UTC and shown in UTC. The store write was"
                 " read in Apple's code on macOS 27.2.1 (26B131); other macOS builds were not read. "
                 "Stored On This Device is ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the "
                 "row was copied to this store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on "
                 "macOS 27.2.1 (26B131) the offset of the event's time zone when the row was written, "
                 "which can differ from its offset at the event across a daylight saving change. "
                 "Source Device ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code "
                 "uses a source device ID to identify a peer device. The code that sets it on an event"
                 " was not traced, so a row that holds one should not be assumed to describe this Mac."
                 " A blank Source Device ID means the row has no source record, or its ZDEVICEID is "
                 "empty. On the eleven streams this module reads, every row with a Source Device ID "
                 "has a ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time is a whole second and Stored On This Device holds a "
                 "fraction of a second, which the report cuts to the whole second. Event Zone UTC "
                 "Offset At Write held one value on every row of dleapp_macos_bigsur, "
                 "magnet2021_macos_bigsur and mvs2026_macbookpro_macos15. Notification Event held one "
                 "value on every row of magnet2021_macos_bigsur and mvs2026_macbookpro_macos15. Stored"
                 " On This Device fell in the same whole second as Start Time on all 4 rows of "
                 "magnet2021_macos_bigsur and all 13 rows of mvs2026_macbookpro_macos15, so the two "
                 "read the same in the report. A copy of knowledgeC.db under System/Volumes/Data that "
                 "is byte-identical, -wal included, to one already read is not read again. Copies of "
                 "one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are "
                 "all read; a row identical in every other column in more than one copy is reported as"
                 " often as the copy holding it most often holds it, normally once, and its Source "
                 "File lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "bell",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 323 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 4 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 13 rows",
        },
    },
    "knowledgeCAppMediaUsage": {
        "name": "KnowledgeC - App Media Usage",
        "description": "/app/mediaUsage events from knowledgeC.db: the stored bundle identifier, URL and "
                       "media URL, with start and end times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-25",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/app/mediaUsage as granular media (video) usage in an app. The code that writes this"
                 " stream was not located, so what Start Time and End Time mark and what media "
                 "activity a row records are not established. URL and Media URL are shown as stored "
                 "and are blank when the row or the store has no such value. The usageType and "
                 "isUsageTrusted metadata are not shown, because their meaning is not established. The"
                 " regression test uses a synthetic store. Start Time and End Time are stored as "
                 "seconds since 2001-01-01 UTC and shown in UTC. The store write was read in Apple's "
                 "code on macOS 27.2.1 (26B131); other macOS builds were not read. A row stored with "
                 "Apple's open-ended end date (NSDate distantFuture) shows a blank End Time and "
                 "Duration (s); no row of this stream in the three macOS test images holds that date. "
                 "Stored On This Device is ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the "
                 "row was copied to this store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on "
                 "macOS 27.2.1 (26B131) the offset of the event's time zone when the row was written, "
                 "which can differ from its offset at the event across a daylight saving change. "
                 "Source Device ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code "
                 "uses a source device ID to identify a peer device. The code that sets it on an event"
                 " was not traced, so a row that holds one should not be assumed to describe this Mac."
                 " A blank Source Device ID means the row has no source record, or its ZDEVICEID is "
                 "empty. On the eleven streams this module reads, every row with a Source Device ID "
                 "has a ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. The -wal sidecar is read alongside the database. On every row of the three "
                 "macOS test images, Start Time and End Time are whole seconds and Stored On This "
                 "Device holds a fraction of a second, which the report cuts to the whole second. "
                 "Event Zone UTC Offset At Write held one value on every row of "
                 "mvs2026_macbookpro_macos15. Stored On This Device fell in the same whole second as "
                 "End Time on all 7 rows of mvs2026_macbookpro_macos15, so the two read the same in "
                 "the report. A copy of knowledgeC.db under System/Volumes/Data that is "
                 "byte-identical, -wal included, to one already read is not read again. Copies of one "
                 "file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are all "
                 "read; a row identical in every other column in more than one copy is reported as "
                 "often as the copy holding it most often holds it, normally once, and its Source File"
                 " lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "player-play",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 0 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 7 rows",
        },
    },
    "knowledgeCMediaPlaying": {
        "name": "KnowledgeC - Media Playing",
        "description": "/media/nowPlaying events from knowledgeC.db: the playback state, stored bundle "
                       "identifier, and the title, artist, album and genre in the structured metadata.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/media/nowPlaying as the now playing state. Playback State uses the names Apple's "
                 "MediaRemote returns on macOS 27.2.1 (26B131) for 0 to 5: Unknown, Playing, Paused, "
                 "Stopped, Interrupted, Seeking. Media Type is shown as stored because its values are "
                 "not established. Title, Artist, Album and Genre are the metadata attributes of those"
                 " names, shown as stored. Media Duration is the duration attribute, shown as stored; "
                 "its unit was not sourced. On macOS 27.2.1 (26B131) the monitor sets a row's start "
                 "when it builds the event and its end when it records the next state. Older builds "
                 "were not read. Reference: Ian Whiffin, "
                 "https://www.doubleblak.com/blogPosts.php?id=29. Start Time and End Time are stored "
                 "as seconds since 2001-01-01 UTC and shown in UTC. The store write was read in "
                 "Apple's code on macOS 27.2.1 (26B131); other macOS builds were not read. A row "
                 "stored with Apple's open-ended end date (NSDate distantFuture) shows a blank End "
                 "Time and Duration (s); no row of this stream in the three macOS test images holds "
                 "that date. Stored On This Device is ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the"
                 " time the row was copied to this store. Event Zone UTC Offset At Write is "
                 "ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) the offset of the event's time zone when "
                 "the row was written, which can differ from its offset at the event across a daylight"
                 " saving change. Source Device ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) "
                 "Apple's sync code uses a source device ID to identify a peer device. The code that "
                 "sets it on an event was not traced, so a row that holds one should not be assumed to"
                 " describe this Mac. A blank Source Device ID means the row has no source record, or "
                 "its ZDEVICEID is empty. On the eleven streams this module reads, every row with a "
                 "Source Device ID has a ZCREATIONDATE (not shown) that differs from "
                 "ZLOCALCREATIONDATE, and every row without one has the two equal. Rows with a Source "
                 "Device ID occur only on dleapp_macos_bigsur. The sync code of the macOS builds on "
                 "the test images was not read. A stored value outside the sourced labels is shown as "
                 "the value followed by (not established). The -wal sidecar is read alongside the "
                 "database. On every row of the three macOS test images, Start Time and End Time are "
                 "whole seconds and Stored On This Device holds a fraction of a second, which the "
                 "report cuts to the whole second. Event Zone UTC Offset At Write held one value on "
                 "every row of dleapp_macos_bigsur. Bundle ID held one value on every row of "
                 "dleapp_macos_bigsur. Stored On This Device fell in the same whole second as End Time"
                 " on all 2 rows of dleapp_macos_bigsur, so the two read the same in the report. A "
                 "copy of knowledgeC.db under System/Volumes/Data that is byte-identical, -wal "
                 "included, to one already read is not read again. Copies of one file under "
                 "System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are all read; a row "
                 "identical in every other column in more than one copy is reported as often as the "
                 "copy holding it most often holds it, normally once, and its Source File lists each "
                 "file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "music",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 2 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
    "knowledgeCIsBacklit": {
        "name": "KnowledgeC - Display Backlit",
        "description": "/display/isBacklit events from knowledgeC.db: whether the stored backlight state was"
                       " Yes or No, with start and end times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/display/isBacklit as the backlight level. Backlit is ZVALUEINTEGER: on macOS 27.2.1"
                 " (26B131) the writer stores 1 for yes and 0 for no. On macOS 27.2.1 (26B131) the "
                 "monitor sets a row's start when it builds the event and its end when it records the "
                 "next state. Older builds were not read. On the three macOS test images, End Time "
                 "does not always equal the next row's Start Time, and why is not established. Start "
                 "Time and End Time are stored as seconds since 2001-01-01 UTC and shown in UTC. The "
                 "store write was read in Apple's code on macOS 27.2.1 (26B131); other macOS builds "
                 "were not read. A row stored with Apple's open-ended end date (NSDate distantFuture) "
                 "shows a blank End Time and Duration (s); no row of this stream in the three macOS "
                 "test images holds that date. Stored On This Device is ZLOCALCREATIONDATE, on macOS "
                 "27.2.1 (26B131) the time the row was copied to this store. Event Zone UTC Offset At "
                 "Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) the offset of the event's time "
                 "zone when the row was written, which can differ from its offset at the event across "
                 "a daylight saving change. Source Device ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 "
                 "(26B131) Apple's sync code uses a source device ID to identify a peer device. The "
                 "code that sets it on an event was not traced, so a row that holds one should not be "
                 "assumed to describe this Mac. A blank Source Device ID means the row has no source "
                 "record, or its ZDEVICEID is empty. On the eleven streams this module reads, every "
                 "row with a Source Device ID has a ZCREATIONDATE (not shown) that differs from "
                 "ZLOCALCREATIONDATE, and every row without one has the two equal. Rows with a Source "
                 "Device ID occur only on dleapp_macos_bigsur. The sync code of the macOS builds on "
                 "the test images was not read. A stored value outside the sourced labels is shown as "
                 "the value followed by (not established). The -wal sidecar is read alongside the "
                 "database. On every row of the three macOS test images, Start Time and End Time are "
                 "whole seconds and Stored On This Device holds a fraction of a second, which the "
                 "report cuts to the whole second. Event Zone UTC Offset At Write held one value on "
                 "every row of dleapp_macos_bigsur, magnet2021_macos_bigsur and "
                 "mvs2026_macbookpro_macos15. A copy of knowledgeC.db under System/Volumes/Data that "
                 "is byte-identical, -wal included, to one already read is not read again. Copies of "
                 "one file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are "
                 "all read; a row identical in every other column in more than one copy is reported as"
                 " often as the copy holding it most often holds it, normally once, and its Source "
                 "File lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "sun",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 225 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 13 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 67 rows",
        },
    },
    "knowledgeCIsLocked": {
        "name": "KnowledgeC - Device Locked",
        "description": "/device/isLocked events from knowledgeC.db: whether the stored screen lock state was"
                       " Yes or No, with start and end times and the stored source device identifier.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/device/isLocked as whether the screen is locked. Screen Locked is ZVALUEINTEGER: on"
                 " macOS 27.2.1 (26B131) the writer stores 1 for yes and 0 for no. On macOS 27.2.1 "
                 "(26B131) the monitor sets a row's start when it builds the event and its end when it"
                 " records the next state. Older builds were not read. On dleapp_macos_bigsur, End "
                 "Time does not always equal the next row's Start Time, and why is not established. On"
                 " dleapp_macos_bigsur all 37 rows hold a Source Device ID, so they should not be "
                 "assumed to describe this Mac's screen. Start Time and End Time are stored as seconds"
                 " since 2001-01-01 UTC and shown in UTC. The store write was read in Apple's code on "
                 "macOS 27.2.1 (26B131); other macOS builds were not read. A row stored with Apple's "
                 "open-ended end date (NSDate distantFuture) shows a blank End Time and Duration (s); "
                 "no row of this stream in the three macOS test images holds that date. Stored On This"
                 " Device is ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied "
                 "to this store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 "
                 "(26B131) the offset of the event's time zone when the row was written, which can "
                 "differ from its offset at the event across a daylight saving change. Source Device "
                 "ID is ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source "
                 "device ID to identify a peer device. The code that sets it on an event was not "
                 "traced, so a row that holds one should not be assumed to describe this Mac. A blank "
                 "Source Device ID means the row has no source record, or its ZDEVICEID is empty. On "
                 "the eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. A stored value outside the sourced labels is shown as the value followed by "
                 "(not established). The -wal sidecar is read alongside the database. On every row of "
                 "the three macOS test images, Start Time and End Time are whole seconds and Stored On"
                 " This Device holds a fraction of a second, which the report cuts to the whole "
                 "second. Event Zone UTC Offset At Write held one value on every row of "
                 "dleapp_macos_bigsur. A copy of knowledgeC.db under System/Volumes/Data that is "
                 "byte-identical, -wal included, to one already read is not read again. Copies of one "
                 "file under System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are all "
                 "read; a row identical in every other column in more than one copy is reported as "
                 "often as the copy holding it most often holds it, normally once, and its Source File"
                 " lists each file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "lock",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 37 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
    "knowledgeCIsPluggedIn": {
        "name": "KnowledgeC - Device Plugged In",
        "description": "/device/isPluggedIn events from knowledgeC.db: whether a charger was recorded as "
                       "plugged in (Yes or No), with start and end times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "KnowledgeC (macOS)",
        "platforms": ("macOS",),
        "notes": "The field meanings and method below were derived independently, using the store's "
                 "schema, measured data and Apple's code. Apple's stream definition describes "
                 "/device/isPluggedIn as whether a charger is plugged in. Plugged In is ZVALUEINTEGER:"
                 " on macOS 27.2.1 (26B131) the writer stores 1 for yes and 0 for no. On macOS 27.2.1 "
                 "(26B131) the monitor sets a row's start when it builds the event and its end when it"
                 " records the next state. Older builds were not read. On dleapp_macos_bigsur no row's"
                 " End Time equals the next row's Start Time and all 5 rows hold the same value. Why "
                 "is not established. Start Time and End Time are stored as seconds since 2001-01-01 "
                 "UTC and shown in UTC. The store write was read in Apple's code on macOS 27.2.1 "
                 "(26B131); other macOS builds were not read. A row stored with Apple's open-ended end"
                 " date (NSDate distantFuture) shows a blank End Time and Duration (s); no row of this"
                 " stream in the three macOS test images holds that date. Stored On This Device is "
                 "ZLOCALCREATIONDATE, on macOS 27.2.1 (26B131) the time the row was copied to this "
                 "store. Event Zone UTC Offset At Write is ZSECONDSFROMGMT, on macOS 27.2.1 (26B131) "
                 "the offset of the event's time zone when the row was written, which can differ from "
                 "its offset at the event across a daylight saving change. Source Device ID is "
                 "ZSOURCE.ZDEVICEID. On macOS 27.2.1 (26B131) Apple's sync code uses a source device "
                 "ID to identify a peer device. The code that sets it on an event was not traced, so a"
                 " row that holds one should not be assumed to describe this Mac. A blank Source "
                 "Device ID means the row has no source record, or its ZDEVICEID is empty. On the "
                 "eleven streams this module reads, every row with a Source Device ID has a "
                 "ZCREATIONDATE (not shown) that differs from ZLOCALCREATIONDATE, and every row "
                 "without one has the two equal. Rows with a Source Device ID occur only on "
                 "dleapp_macos_bigsur. The sync code of the macOS builds on the test images was not "
                 "read. A stored value outside the sourced labels is shown as the value followed by "
                 "(not established). The -wal sidecar is read alongside the database. On every row of "
                 "the three macOS test images, Start Time and End Time are whole seconds and Stored On"
                 " This Device holds a fraction of a second, which the report cuts to the whole "
                 "second. Event Zone UTC Offset At Write held one value on every row of "
                 "dleapp_macos_bigsur. Plugged In held one value on every row of dleapp_macos_bigsur. "
                 "A copy of knowledgeC.db under System/Volumes/Data that is byte-identical, -wal "
                 "included, to one already read is not read again. Copies of one file under "
                 "System/Volumes/Data/ or System/Volumes/Update/mnt1/ that differ are all read; a row "
                 "identical in every other column in more than one copy is reported as often as the "
                 "copy holding it most often holds it, normally once, and its Source File lists each "
                 "file that held it, one per line.",
        "paths": ('*/Knowledge/knowledgeC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "battery-charging",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 5 rows",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows",
        },
    },
}


# [[NSDate distantFuture] timeIntervalSinceReferenceDate], the end a monitor gives an open event.
_DISTANT_FUTURE = 63113904000.0
_NOT_ESTABLISHED = 'not established'
_YES_NO = {0: 'No', 1: 'Yes'}
# Intents.framework INInteraction.h
_DIRECTION = {0: 'Unspecified', 1: 'Outgoing', 2: 'Incoming'}
# Intents.framework INIntentHandlingStatus
_HANDLING = {0: 'Unspecified', 1: 'Ready', 2: 'InProgress', 3: 'Success', 4: 'Failure',
             5: 'DeferredToApplication', 6: 'UserConfirmationRequired'}
# MediaRemote MRMediaRemoteCopyPlaybackStateDescription on macOS 27.2.1 (26B131)
_PLAYBACK = {0: 'Unknown', 1: 'Playing', 2: 'Paused', 3: 'Stopped', 4: 'Interrupted', 5: 'Seeking'}

_INTENT = '_DKIntentMetadataKey'
_NOW = '_DKNowPlayingMetadataKey'
_HEALTH = '_DKDigitalHealthMetadataKey'
_MEDIA = '_DKAppMediaUsageMetadataKey'
_NOTE = '_DKNotificationUsageMetadataKey'
_SAFARI = '_DKSafariHistoryMetadataKey'


def _kc_sources(context):
    stores = [str(f) for f in context.get_files_found() if str(f).endswith('knowledgeC.db')]
    kept, _skipped = unique_sources(context, stores, sidecars=('-wal',), label='KnowledgeC')
    return kept


def _columns(database, table):
    return {row[1] for row in database.execute(f'PRAGMA table_info("{table}")')}


def _metadata_column(present, key, attribute):
    """The Core Data column of a metadata attribute in this store, or None."""
    name = f'Z{key}__{attribute}'.upper()
    if name in present:
        return name
    return name + '_V2' if name + '_V2' in present else None


def _stream_query(database, stream, value_column, metadata):
    """(sql, parameters) for one stream in this store, or (None, None) without an Event entity."""
    entity = database.execute("SELECT Z_ENT FROM Z_PRIMARYKEY WHERE Z_NAME = 'Event'").fetchone()
    if not entity:
        return None, None
    object_columns = _columns(database, 'ZOBJECT')
    source_columns = _columns(database, 'ZSOURCE')
    metadata_columns = _columns(database, 'ZSTRUCTUREDMETADATA')
    base = ('ZSTARTDATE', 'ZENDDATE', 'ZLOCALCREATIONDATE', 'ZSECONDSFROMGMT', value_column)
    selected = [f'o."{name}"' if name in object_columns else 'NULL' for name in base]
    selected += [f's."{name}"' if name in source_columns else 'NULL' for name in ('ZDEVICEID', 'ZBUNDLEID')]
    for _header, key, attribute, _labels in metadata:
        column = _metadata_column(metadata_columns, key, attribute)
        selected.append(f'm."{column}"' if column else 'NULL')
    joins = ''
    if source_columns and 'ZSOURCE' in object_columns:
        joins += ' LEFT JOIN ZSOURCE s ON o.ZSOURCE = s.Z_PK'
    else:
        selected = [item if not item.startswith('s.') else 'NULL' for item in selected]
    if metadata_columns and 'ZSTRUCTUREDMETADATA' in object_columns:
        joins += ' LEFT JOIN ZSTRUCTUREDMETADATA m ON o.ZSTRUCTUREDMETADATA = m.Z_PK'
    else:
        selected = [item if not item.startswith('m.') else 'NULL' for item in selected]
    sql = (f'SELECT {", ".join(selected)} FROM ZOBJECT o{joins} '
           'WHERE o.ZSTREAMNAME = ? AND o.Z_ENT = ? ORDER BY o.ZSTARTDATE, o.Z_PK')
    return sql, (stream, entity[0])


def _time(value):
    if value is None or value >= _DISTANT_FUTURE - 1:
        return ''
    return convert_cocoa_core_data_ts_to_utc(value)


def _duration(start, end):
    if start is None or end is None or end >= _DISTANT_FUTURE - 1:
        return ''
    return round(end - start, 3)


def _offset(seconds):
    if seconds is None:
        return ''
    whole = int(seconds)
    sign = '+' if whole >= 0 else '-'
    whole = abs(whole)
    return f'{sign}{whole // 3600:02d}:{(whole % 3600) // 60:02d}'


def _shown(value, labels):
    if value is None:
        return ''
    if labels is None:
        return value
    return labels.get(value, f'{value} ({_NOT_ESTABLISHED})')


def _event_artifact(context, stream, value_header, value_column='ZVALUESTRING', value_labels=None,
                    metadata=(), has_end=True, source_bundle=False):
    """Headers, rows and sources for one stream, read from every store found."""
    headers = [('Start Time', 'datetime')]
    if has_end:
        headers.append(('End Time', 'datetime'))
    headers += [('Stored On This Device', 'datetime'), value_header]
    headers += [item[0] for item in metadata]
    if has_end:
        headers.append('Duration (s)')
    if source_bundle:
        headers.append('Source Bundle ID')
    headers += ['Event Zone UTC Offset At Write', 'Source Device ID', 'Source File']

    data_list = []
    read_sources = []
    for source in _kc_sources(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        try:
            sql, parameters = _stream_query(database, stream, value_column, metadata)
            if sql is None:
                logfunc(f'knowledgeC {relative_source}: no Event entity in Z_PRIMARYKEY, store not read')
                continue
            rows = database.execute(sql, parameters).fetchall()
        except sqlite3.Error as exc:
            logfunc(f'knowledgeC {relative_source}: {exc}')
            continue
        finally:
            database.close()
        for row in rows:
            start, end, stored, offset, value, device, bundle = row[:7]
            built = [_time(start)]
            if has_end:
                built.append(_time(end))
            built += [_time(stored), _shown(value, value_labels)]
            built += [_shown(item, spec[3]) for item, spec in zip(row[7:], metadata)]
            if has_end:
                built.append(_duration(start, end))
            if source_bundle:
                built.append(bundle or '')
            built += [_offset(offset), device or '', relative_source]
            data_list.append(tuple(built))
        if rows:
            read_sources.append(relative_source)
    return tuple(headers), fold_view_rows(data_list), '\n'.join(read_sources)


@artifact_processor
def knowledgeCInFocus(context):
    return _event_artifact(context, '/app/inFocus', 'Bundle ID')


@artifact_processor
def knowledgeCAppUsage(context):
    return _event_artifact(context, '/app/usage', 'Bundle ID')


@artifact_processor
def knowledgeCWebUsage(context):
    return _event_artifact(context, '/app/webUsage', 'Bundle ID', metadata=(
        ('Web Domain', _HEALTH, 'webDomain', None),
        ('Webpage URL', _HEALTH, 'webpageURL', None)))


@artifact_processor
def knowledgeCSafariHistory(context):
    return _event_artifact(context, '/safari/history', 'URL', has_end=False, metadata=(
        ('Title', _SAFARI, 'title', None),))


@artifact_processor
def knowledgeCAppIntents(context):
    return _event_artifact(context, '/app/intents', 'Intent Domain', source_bundle=True, metadata=(
        ('Intent Class', _INTENT, 'intentClass', None),
        ('Intent Verb', _INTENT, 'intentVerb', None),
        ('Direction', _INTENT, 'direction', _DIRECTION),
        ('Handling Status', _INTENT, 'intentHandlingStatus', _HANDLING),
        ('Intent Type (as stored)', _INTENT, 'intentType', None),
        ('Derived Intent ID (as stored)', _INTENT, 'derivedIntentIdentifier', None)))


@artifact_processor
def knowledgeCNotificationUsage(context):
    return _event_artifact(context, '/notification/usage', 'Notification Event (as stored)',
                           has_end=False, metadata=(
                               ('Bundle ID', _NOTE, 'bundleID', None),
                               ('Notification ID', _NOTE, 'identifier', None)))


@artifact_processor
def knowledgeCAppMediaUsage(context):
    return _event_artifact(context, '/app/mediaUsage', 'Bundle ID', metadata=(
        ('URL', _MEDIA, 'URL', None),
        ('Media URL', _MEDIA, 'mediaURL', None)))


@artifact_processor
def knowledgeCMediaPlaying(context):
    return _event_artifact(context, '/media/nowPlaying', 'Bundle ID', metadata=(
        ('Playback State', _NOW, 'playing', _PLAYBACK),
        ('Title', _NOW, 'title', None),
        ('Artist', _NOW, 'artist', None),
        ('Album', _NOW, 'album', None),
        ('Genre', _NOW, 'genre', None),
        ('Media Duration (as stored)', _NOW, 'duration', None),
        ('Media Type (as stored)', _NOW, 'mediaType', None)))


@artifact_processor
def knowledgeCIsBacklit(context):
    return _event_artifact(context, '/display/isBacklit', 'Backlit', 'ZVALUEINTEGER', _YES_NO)


@artifact_processor
def knowledgeCIsLocked(context):
    return _event_artifact(context, '/device/isLocked', 'Screen Locked', 'ZVALUEINTEGER', _YES_NO)


@artifact_processor
def knowledgeCIsPluggedIn(context):
    return _event_artifact(context, '/device/isPluggedIn', 'Plugged In', 'ZVALUEINTEGER', _YES_NO)
