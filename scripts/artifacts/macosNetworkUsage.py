__artifacts_v2__ = {
    "netusageAppData": {
        "name": "Network Usage - App Data",
        "description": "Per-process network byte counters from netusage.sqlite "
                       "(ZLIVEUSAGE joined to ZPROCESS): bundle name, process "
                       "name and Wifi, Mobile/WWAN and Wired bytes in and out.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-14",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "macOS - Network & Connectivity",
        "platforms": ("macOS",),
        "notes": "The field meanings and joins below were derived independently from the store's Core "
                 "Data model, measured data and Apple's code. On dleapp_macos_bigsur (macOS 11.2.1) "
                 "the store is at /private/var/networkd/db/. Only the first netusage.sqlite that holds"
                 " both tables is read. Rows join ZLIVEUSAGE to ZPROCESS through the hasProcess "
                 "relationship in the store's cached model. On dleapp_macos_bigsur all 103 rows are in"
                 " the write-ahead log. The timestamps are seconds from 2001-01-01 UTC. On iOS 18.7 "
                 "the writer sets Live Usage Timestamp when it creates the row, and a row is a running"
                 " total. No end time is stored for it on the measured images (ZBILLCYCLEEND is "
                 "empty), so it is not the time of a transfer. The writer was not read for macOS 11, "
                 "so this is not established for the tested image. What Process First Timestamp and "
                 "Process Timestamp mark on macOS is not established. ZKIND is reported as stored and "
                 "its meaning is not established. On iOS 18.7 the writer fills Process Name and Bundle"
                 " Name from the entity the traffic was attributed to, which need not be the program "
                 "that opened the connection. The macOS writer was not read. Byte column names follow "
                 "the stored columns (ZWIFIIN, ZWWANIN, ZWIREDIN and their OUT columns). What the "
                 "Wired and Mobile/WWAN columns hold on macOS is not established. On "
                 "dleapp_macos_bigsur the Wired columns are non-zero on 102 of 103 rows, Wifi In "
                 "(Bytes) and Wifi Out (Bytes) on none, and the Mobile/WWAN columns on 1.",
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
        ('Live Usage Timestamp', 'datetime'), ('Process First Timestamp', 'datetime'),
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
