# Firefox validation policy

Author: @AlexisBrignoni, Codex

The Firefox profile covers visits, downloads, bookmarks, cookies, form history, page
interactions, favicons, site local storage, IndexedDB records, session store tabs, and
saved login metadata. Public tests use independently authored synthetic SQLite records
and session files. Do not generate fixtures, baselines, fingerprints, or published
sample metadata from private corpus material. Keep source records and identifying or
aggregate corpus observations out of commits, PR descriptions, and messages.

Local end-to-end validation may use a read-only mount and temporary copies of
relevant stores with SQLite sidecars. Reports stay local. Publish only generic
pass/fail results and implementation details supported by vendor documentation.

The synthetic regression suite covers cookie schema timestamp changes, missing
optional fields, exact microseconds, orphaned visits, URL-scoped downloads,
malformed metadata, bookmark hierarchy cycles, form-source fan-out, interaction
units, profile paths, distinct profiles, firmlink deduplication, WAL-only records,
evidence integrity, continuation after a corrupt store, raw Snappy decompression, local
storage value conversion, structured-clone values, IndexedDB key encoding, LZ4 blocks,
the session store's open, closed and grouped tabs, and saved logins in logins.json and
both logins.db tables.

Source definitions are linked at pinned Mozilla revisions in artifact metadata.
Windows and Linux path tests do not establish real-image validation on those systems.

Profiles that Firefox's Refresh copied to the Desktop are read through a Desktop
pattern beside the profile-folder patterns; the artifact notes cite the Mozilla source
for the folder layout. The synthetic suite covers English and German folder names on
macOS and Windows paths.
