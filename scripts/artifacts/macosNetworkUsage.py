__artifacts_v2__ = {
    "netusageAppData": {
        "name": "Network Usage - App Data",
        "description": "Per-process network byte counters from netusage.sqlite "
                       "(ZLIVEUSAGE joined to ZPROCESS): bundle name, process "
                       "name and Wifi, Mobile/WWAN and Wired bytes in and out.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-09-14",
        "requirements": "none",
        "category": "Network Usage (macOS)",
        "notes": "macOS keeps netusage.sqlite at /private/var/networkd/db/. "
                 "Every netusage.sqlite found is parsed, tagged by Source File. "
                 "The timestamps are Mac Absolute Time (Core Data), seconds "
                 "since 2001-01-01 UTC. ZKIND is reported as stored; its values "
                 "are not documented. The Wifi, Mobile/WWAN and Wired byte "
                 "columns hold whatever the interface recorded, so a column is "
                 "zero when no traffic was attributed to that interface: "
                 "Wifi In (Bytes) and Wifi Out (Bytes) are zero on a Mac whose "
                 "traffic is attributed to the wired or WWAN interface. Live "
                 "Usage Timestamp and Process First Usage Timestamp coincide "
                 "when a process has a single live-usage row. The netusage.sqlite "
                 "forensic value is documented by Sarah Edwards, 'Network and "
                 "Application Usage', https://www.mac4n6.com/blog/2019/1/6/network-and-application-usage-using-netusagesqlite-amp-datausagesqlite-ios-databases",
        "paths": ('*/netusage.sqlite*',),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS Big Sur (Josh Hickman public test image, thisisdfir) | 103 rows",
        },
    },
}

from scripts.ilapfuncs import (artifact_processor, get_sqlite_db_records,
                               does_table_exist_in_db, convert_cocoa_core_data_ts_to_utc,
                               logfunc)


def _find_netusage_db(context, required_tables):
    '''Returns the first netusage.sqlite that holds all the required tables.
    An extraction can carry more than one netusage.sqlite (for example an empty
    stub); the one missing a table must not be picked over the populated one.'''
    for file_found in context.get_files_found():
        file_found = str(file_found)
        if not file_found.endswith('netusage.sqlite'):
            continue
        if all(does_table_exist_in_db(file_found, table) for table in required_tables):
            return file_found
        logfunc(f'Skipping {file_found}: missing one of the tables {", ".join(required_tables)}')
    return ''


@artifact_processor
def netusageAppData(context):
    data_headers = (
        ('Live Usage Timestamp', 'datetime'), ('Process First Usage Timestamp', 'datetime'),
        ('Process Timestamp', 'datetime'), 'Bundle Name', 'Process Name', 'ZKIND (as stored)',
        'Wifi In (Bytes)', 'Wifi Out (Bytes)', 'Mobile/WWAN In (Bytes)', 'Mobile/WWAN Out (Bytes)',
        'Wired In (Bytes)', 'Wired Out (Bytes)')
    data_list = []

    data_source = _find_netusage_db(context, ('ZLIVEUSAGE', 'ZPROCESS'))
    if data_source:
        all_rows = get_sqlite_db_records(data_source, '''
            SELECT
                ZLIVEUSAGE.ZTIMESTAMP,
                ZPROCESS.ZFIRSTTIMESTAMP,
                ZPROCESS.ZTIMESTAMP,
                ZPROCESS.ZBUNDLENAME,
                ZPROCESS.ZPROCNAME,
                ZLIVEUSAGE.ZKIND,
                ZLIVEUSAGE.ZWIFIIN,
                ZLIVEUSAGE.ZWIFIOUT,
                ZLIVEUSAGE.ZWWANIN,
                ZLIVEUSAGE.ZWWANOUT,
                ZLIVEUSAGE.ZWIREDIN,
                ZLIVEUSAGE.ZWIREDOUT
            FROM ZLIVEUSAGE
            LEFT JOIN ZPROCESS ON ZPROCESS.Z_PK = ZLIVEUSAGE.ZHASPROCESS
        ''')

        for row in all_rows:
            live_ts = convert_cocoa_core_data_ts_to_utc(row[0])
            first_used = convert_cocoa_core_data_ts_to_utc(row[1])
            proc_ts = convert_cocoa_core_data_ts_to_utc(row[2])
            data_list.append((live_ts, first_used, proc_ts, row[3], row[4], row[5],
                              row[6], row[7], row[8], row[9], row[10], row[11]))

    return data_headers, data_list, data_source
