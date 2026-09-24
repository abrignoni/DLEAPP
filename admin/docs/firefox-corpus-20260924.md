# Firefox artifacts from the Fuji corpus

Author: @AlexisBrignoni, Codex

Six artifacts add Firefox coverage absent from DLEAPP before this change. They read
allocated rows in `places.sqlite`, `cookies.sqlite`, and `formhistory.sqlite`, including
committed WAL content. The focused profile is `firefox.dlprofile`. No extra dependency
is required. Outputs are HTML, TSV, timeline, and LAVA.

## Real-image validation

Corpus key: `brunofischer_macos27_fuji_20260924`. The Fuji acquisition log describes a
macOS 27.0 (26A428) user-folder acquisition. Its image SHA-256 is
`3d99a3500a3f4670e09a7649ec747458cc869f722c278f65bffd38cae22f61f2`.
Firefox `compatibility.ini` records `156.0_20260909172920/20260909172920`.
One profile has the browser databases; two other profile directories contain only
`times.json` or `.parentlock`. The image root is the acquired home directory, so the
report deliberately leaves User blank: the source path itself does not name an account.

| Artifact | Source records | Rows |
|---|---|---:|
| Firefox Visits | `moz_historyvisits`, joined to `moz_places` and referring visit | 267 |
| Firefox Downloads | Per-place destination and metadata annotations | 8 |
| Firefox Bookmarks | `moz_bookmarks`, type 1 | 4 |
| Firefox Cookies | `moz_cookies`, schema 17 | 317 |
| Firefox Form History | `moz_formhistory`, with source relationships | 7 |
| Firefox Page Interactions | `moz_places_metadata` | 50 |
| Total | | 653 |

The four bookmarks are Mozilla product/support links in the Mozilla Firefox folder,
with identical added/modified timestamps. They must not be described as user-created
bookmarks; that behavior is tested only with synthetic records. Metadata notes explicitly
identify these and other uniform sample columns. Cookie update timestamps can be assigned
by a schema migration, rather than a server replacing a cookie.

The image was mounted read-only with `hdiutil attach -readonly -nobrowse -noautoopen`.
Schema inspection used temporary copies with available SQLite sidecars. Final validation
runs the actual DLEAPP entry point with the focused profile against that read-only mount:

```sh
python3 dleapp.py -t fs \
  -i /Volumes/2026_09_24_YKW0K0V4JY_Acquisition \
  -o "$HOME/Desktop" -m firefox.dlprofile \
  --custom_output_folder 'DLEAPP Fuji Firefox 2026-09-24 Verified'
```

The DMG is mounted for this run; direct `-t raw` DMG compatibility is not established by
this validation. Do not substitute a direct raw-image run when reproducing these results.

## Survey and scope

A filesystem inventory examined 35,795 regular, non-symlink files, including databases,
plists, JSON, text logs, and extensionless files. Existing DLEAPP macOS system, Safari,
Signal, and other application coverage was checked before selecting Firefox as a coherent
new family. The inventory also identified Threema Desktop, Potato Desktop, Garmin caches,
a MobileSync backup, and Zalo browser storage. Their presence is not a claim of decoded
contents or new parser coverage; they are outside this Firefox implementation.

All tables in the three selected databases were enumerated with schema and row counts.
The following tables are not separate report artifacts:

- `moz_places` (230) and `moz_origins` (54) are URL/origin metadata used for joins; their
  mere presence is not a visit. No additional URL list inflates the event report.
- `moz_bookmarks` has seven folder rows, used for hierarchy, and four URL rows. Folders
  and separators do not get separate output rows.
- `moz_anno_attributes` has two definitions and `moz_annos` has sixteen annotation rows,
  combined into eight downloads. Download annotation creation is not a download start
  time; metadata is URL-scoped and can be replaced by later downloads.
- `moz_newtab_shortcuts_interaction` has twelve rows. Its separate event types have not
  been validated here and are not silently labeled as visits.
- `moz_meta` (2), `sqlite_stat1` (24), and `sqlite_sequence` (0) are bookkeeping, not
  examiner-facing activities.
- Empty Places tables: `moz_places_extra`, `moz_historyvisits_extra`, `moz_inputhistory`,
  `moz_bookmarks_deleted`, `moz_keywords`, `moz_items_annos`,
  `moz_places_metadata_search_queries`, `moz_previews_tombstones`,
  `moz_newtab_story_click`, and `moz_newtab_story_impression`. Deletion tombstones,
  adaptive input history, keywords, and interaction search-query joins are not implemented;
  their empty state in this image does not establish non-use.
- `moz_sources` has one row and `moz_history_to_sources` six rows. These enrich form
  history without multiplying entries. `moz_deleted_formhistory` is empty and omitted.
- `moz_cookies` is the only cookies database table. Stored cookie values and partition
  attributes are retained; cookie access is not labeled a top-level visit.

Other Firefox stores found but excluded: `favicons.sqlite` (icons), `permissions.sqlite`
and `content-prefs.sqlite` (site settings), `protections.sqlite` and
`bounce-tracking-protection.sqlite` (privacy subsystem records), `suggest.sqlite` and
`domain_to_categories.sqlite` (suggestion/classification stores), `storage-sync-v2.sqlite`
and `webappsstore.sqlite` (other storage), `tabnotes.sqlite`, `logins.db`, `breach-alerts.db`,
`storage.sqlite`, and origin-specific IndexedDB/local-storage databases. No schema/content
claims are made for these excluded stores. In particular, Zalo IndexedDB decoding needs
its own format research and is not part of generic browser history parsing.

Non-SQLite Firefox files include `sessionstore.jsonlz4`, `search.json.mozlz4`,
`logins.json`, `logins-backup.json`, `key4.db`, `cert9.db`, `prefs.js`, `extensions.json`,
`addons.json`, `containers.json`, `handlers.json`, and startup/experiment/state files.
Session restoration, credential recovery, extensions, cache/media export, and settings
parsers remain outside this implementation. No application was launched and no stored
credential was used. Private corpus records were not added to repository fixtures.

## Field references

Pinned Mozilla source revision: `3682546ac2c02610537306ca16849de2c24aea45`.
These exact revision files were retrieved and inspected, not just search summaries.

- [Places PRTime units and visit types](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L595-L596)
- [Transition constants](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/places/nsINavHistoryService.idl#L918-L977)
- [Download annotation/state definitions](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L27-L36)
- [Download metadata construction](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadHistory.sys.mjs#L125-L151)
- [Download endTime milliseconds](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/downloads/DownloadCore.sys.mjs#L1282-L1287)
- [Cookie expiry migration and initialization of updateTime](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/CookiePersistentStorage.cpp#L1593-L1614)
- [Cookie microsecond times](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/netwerk/cookie/nsICookie.idl#L118-L138)
- [Form-history microseconds](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/toolkit/components/satchel/FormHistory.sys.mjs#L390-L430)
- [Interaction timestamp and measurement units](https://github.com/mozilla-firefox/firefox/blob/3682546ac2c02610537306ca16849de2c24aea45/browser/components/places/Interactions.sys.mjs#L88-L113)

## Regression boundaries

Synthetic tests cover schemas 15/16/17 cookie expiry units, optional fields, exact
microseconds, redirects and missing visit joins, repeated download visits, malformed or
missing metadata, bookmark hierarchy cycles, form-source fan-out, millisecond interaction
dates, macOS/Windows/Linux path matching, independent profiles, firmlink duplicates,
WAL-only records, evidence hashes, and continuation after a corrupt profile. Windows and
Linux have path tests only; their real-browser images remain unvalidated.

## Completed checks

- 44 focused/framework regression tests ran: 41 passed, three pre-existing
  platform-dependent tests skipped; all 13 new Firefox tests passed.
- Pylint on the reader, artifact module, and tests: 10.00/10.
- Artifact descriptions, claim language, source paths, source-file columns, HTML safety,
  report-local paths, conversation column order, and sample registry checks passed.
  Registry validation reported zero errors and existing warnings in unrelated modules.
- The final focused report produced 653 rows in TSV, LAVA, and timeline outputs, with six
  HTML artifact pages and matching LAVA manifest counts. No parser errors occurred.
- Independent SQL queries matched every emitted record's identifiers and selected payload
  fields, plus every exported timestamp in all six artifacts, without calling the reader.
- All five preserved source database/WAL files matched the mounted evidence by SHA-256.
- The strict output-column checker passed after the notes documented observed uniform
  columns and the sample's other limitations.

Final manual-inspection output: `~/Desktop/DLEAPP Fuji Firefox 2026-09-24 Verified/index.html`.
