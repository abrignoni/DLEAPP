__artifacts_v2__ = {
    "windowsUpdateOrchestratorHistory": {
        "name": "Windows Update Orchestrator Update History",
        "description": "The update history table of the Update Orchestrator store "
                       "(ProgramData\\USOPrivate\\UpdateStore\\store.db and store.bak): the time recorded for "
                       "each update, its title, history category, update ID, provider and whether a reboot was required.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads the COMPLETEDUPDATES table of ProgramData\\USOPrivate\\UpdateStore\\store.db and of store.bak in the same folder, one row per provider, update ID and time; a row store.bak shares with store.db is shown once, from store.db, and Source File names the file each row came from. On pc_mus_001_win11 store.bak held one update with an earlier time than store.db, shown as its own row. No Microsoft documentation of this store is cited here; the meanings below are measured, not sourced. Time is the TIME text read as milliseconds since 1970-01-01 UTC. Data check: every one of the 55 rows of the WuProvider provider on the tested images (pc_mus_001_win11, hexordia_mvs2025_win11, szechuan_win10) has a Microsoft-Windows-WindowsUpdateClient event 19, Installation Successful, in the System event log (as read by windowsUpdateClientEvents.py) for the same update GUID and revision; read this way Time was within 1 second of the nearest such event on 41 rows, within 5 seconds on 47 and within 2 minutes on 53. On 2 rows, both of category Driver, it was 3.5 hours and about 18 days after the event, so Time is not always the installation time. Rows of the other providers seen (LegacyUOProvider 22 rows, SignalUpdater 2, WSXProvider 1) carry Update IDs that are not a GUID and revision and matched no event 19 record on those images, so their Time is read the same way without that check. Title, Description, More Info URL, History Category, Update ID and Provider are TITLE, DESCRIPTION, MOREINFOURL, HISTORYCATEGORY, UPDATEID and PROVIDERID as stored; a WuProvider Update ID is the update GUID and its revision number joined by a colon, matching the event's update GUID (which the event stores in braces) and revision. History Category held Other, Definition, Driver and Quality on the tested rows. Reboot Required and For OS are WASREBOOTREQUIRED and FOROS shown as Yes or No; of the tested stores only the one with user_version 10 (hexordia_mvs2025_win11) has those columns, so Reboot Required and For OS held no value on any row of pc_mus_001_win11 (user_version 7) and szechuan_win10 (user_version 3). A row does not establish who or what started the update. Not read: UNINSTALL (0 on every tested row) and METADATA (JSON text, present only in the user_version 10 store, holding an UpdateInternalMetadata object of mostly boolean values; meaning not established here); the UPDATES, UPDATESPROP, VARIABLES, PROVIDERSPROP, ACTIONRECORDS, APPROVEDUPDATES, SIGNALUPDATES, WSXPACKUPDATES, DOWNTIMEHISTORY and ACTIONRECORDSPROP tables, whose meaning is not established here; and the updatestore<GUID>.xml and UpdateCspStore.xml files found in the same folder on the older builds tested (af_case2_win10, alihadi_threatsim_server2019, lonewolf_win10), whose session variables hold times in a unit not established here. ou_ransomware_server2022 holds a store.db whose COMPLETEDUPDATES table is empty.",
        "paths": ('*/ProgramData/USOPrivate/UpdateStore/store.db*',
                  '*/ProgramData/USOPrivate/UpdateStore/store.bak*'),
        "output_types": "standard",
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 40 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 38 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (COMPLETEDUPDATES is empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no store.db; the folder holds the older XML files)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no store.db; the folder holds the older XML files)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no store.db; the folder holds the older XML files)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
        },
    },
}

import datetime
import os
import sqlite3

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

_STORES = ('store.db', 'store.bak')
_COLUMNS = ('TIME', 'TITLE', 'HISTORYCATEGORY', 'WASREBOOTREQUIRED', 'FOROS', 'UPDATEID', 'PROVIDERID',
            'DESCRIPTION', 'MOREINFOURL')


def _unix_ms(value):
    """A TIME string of milliseconds since 1970-01-01 UTC as a datetime; '' when it is not one."""
    try:
        milliseconds = int(str(value).strip())
    except (TypeError, ValueError):
        return ''
    if milliseconds <= 0:
        return ''
    try:
        return datetime.datetime.fromtimestamp(milliseconds / 1000, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _yes_no(value):
    if value is None or value == '':
        return ''
    return 'Yes' if value else 'No'


@artifact_processor
def windowsUpdateOrchestratorHistory(context):
    label = 'Windows Update Orchestrator Update History'
    data_list = []
    sources = []
    seen = set()
    paths = sorted(str(p) for p in context.get_files_found()
                   if os.path.basename(str(p)) in _STORES and os.path.isfile(str(p)))
    # store.db before store.bak in each folder, so a row both hold is reported from store.db
    paths.sort(key=lambda p: (os.path.dirname(p), _STORES.index(os.path.basename(p))))
    for path in paths:
        relative = context.get_relative_path(path)
        db = open_sqlite_db_readonly(path)
        if db is None:
            continue
        try:
            present = {row[1] for row in db.execute('PRAGMA table_info("COMPLETEDUPDATES")')}
            if not present:
                logfunc(f'{label}: {relative} has no COMPLETEDUPDATES table')
                sources.append(path)
                continue
            select = ', '.join(f'"{c}"' if c in present else 'NULL' for c in _COLUMNS)
            rows = db.execute(f'SELECT {select} FROM COMPLETEDUPDATES ORDER BY TIME').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(path)
        folder = os.path.dirname(relative)
        repeated = 0
        for time, title, category, reboot, for_os, update_id, provider, description, url in rows:
            key = (folder, provider, update_id, time)
            if key in seen:
                repeated += 1
                continue
            seen.add(key)
            data_list.append((_unix_ms(time), title, category, _yes_no(reboot), _yes_no(for_os), update_id,
                              provider, description, url, relative))
        if repeated:
            logfunc(f'{label}: {repeated} row(s) of {relative} already read from store.db in the same folder')
    data_headers = (('Time', 'datetime'), 'Title', 'History Category', 'Reboot Required', 'For OS',
                    'Update ID', 'Provider', 'Description', 'More Info URL', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
