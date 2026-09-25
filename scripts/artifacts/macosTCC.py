import sqlite3

from scripts.ilapfuncs import (artifact_processor, open_sqlite_db_readonly,
                               convert_unix_ts_to_utc, logfunc)

# macOS keeps a system TCC.db at /Library/Application Support/com.apple.TCC/ and
# a per-user one at ~/Library/Application Support/com.apple.TCC/. The pattern
# matches both; each is read and tagged by Source File. TCC records which app
# was granted or denied a protected capability (camera, microphone, location,
# screen recording, full-disk access, Accessibility, Apple Events, and so on).

__artifacts_v2__ = {
    "tccAccess": {
        "name": "TCC - App Permissions",
        "description": "Access decisions from the TCC.db access table: the "
                       "service (capability), the client app, whether it was "
                       "allowed or denied, and when the decision was last "
                       "modified.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none",
        "category": "App Permissions (macOS)",
        "notes": "Every TCC.db found is parsed (the system store under "
                 "/Library/Application Support/com.apple.TCC/ and each user's "
                 "under ~/Library/Application Support/com.apple.TCC/), tagged by "
                 "Source File. Service is shown without its kTCCService prefix. "
                 "Client Type is decoded (0 Bundle ID, 1 Absolute path) and the "
                 "Client is a bundle identifier or an on-disk path accordingly. "
                 "Access is decoded from auth_value on modern schemas (0 Not "
                 "allowed, 2 Allowed, 3 Limited) or from allowed on older ones "
                 "(0/1); unrecognized values are reported as stored. Auth Reason "
                 "is reported as stored; its codes follow community-established "
                 "TCC research and are not decoded here. Indirect Object is the "
                 "target the client controls (for Apple Events / PostEvent), "
                 "blank when TCC stored UNUSED. Last Modified is Unix epoch "
                 "seconds in UTC. The -wal sidecar is read alongside the "
                 "database.",
        "paths": ('*/com.apple.TCC/TCC.db*',),
        "output_types": ["standard"],
        "artifact_icon": "key",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 19 rows (13 user store + 6 system store)",
        },
    },
}


def _tcc_sources(context):
    return [str(f) for f in context.get_files_found() if str(f).endswith('TCC.db')]


@artifact_processor
def tccAccess(context):
    data_headers = (('Last Modified', 'datetime'), 'Service', 'Client', 'Client Type',
                    'Access', 'Auth Reason (as stored)', 'Indirect Object', 'Source File')
    data_list = []
    read_sources = []

    for source in _tcc_sources(context):
        database = open_sqlite_db_readonly(source)
        if database is None:
            continue
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            cols = {r[1] for r in database.execute("PRAGMA table_info(access)")}
            if not cols:
                database.close()
                continue
            if 'auth_value' in cols:
                access_sql = ("CASE auth_value WHEN 0 THEN 'Not allowed' WHEN 2 THEN 'Allowed' "
                              "WHEN 3 THEN 'Limited' ELSE auth_value END")
            else:
                access_sql = "CASE allowed WHEN 0 THEN 'Not allowed' WHEN 1 THEN 'Allowed' ELSE allowed END"
            last_mod = 'last_modified' if 'last_modified' in cols else 'NULL'
            client_type = ("CASE client_type WHEN 0 THEN 'Bundle ID' WHEN 1 THEN 'Absolute path' "
                           "ELSE client_type END") if 'client_type' in cols else "''"
            auth_reason = 'auth_reason' if 'auth_reason' in cols else 'NULL'
            iobj = ("CASE WHEN indirect_object_identifier = 'UNUSED' THEN '' "
                    "ELSE indirect_object_identifier END") if 'indirect_object_identifier' in cols else "''"
            query = (f"SELECT {last_mod}, REPLACE(service, 'kTCCService', ''), client, "
                     f"{client_type}, {access_sql}, {auth_reason}, {iobj} "
                     f"FROM access ORDER BY {last_mod if last_mod != 'NULL' else 'client'}, access.rowid")
            for row in database.execute(query):
                last_modified = convert_unix_ts_to_utc(row[0]) if row[0] else ''
                data_list.append((last_modified, row[1], row[2], row[3], row[4],
                                  '' if row[5] is None else row[5], row[6] or '', relative_source))
                rows_here += 1
        except sqlite3.Error as exc:
            logfunc(f'TCC {relative_source}: {exc}')
        finally:
            database.close()
        if rows_here:
            read_sources.append(relative_source)

    return data_headers, data_list, "\n".join(read_sources)
