"""Microsoft Office alert events (OAlerts.evtx) for DLEAPP.

Author: @AlexisBrignoni, Claude.

On every tested record of the OAlerts event log the Event ID was 300 and the record carried one event data value,
a string array of 2 to 6 strings. No published description of those strings was found, so they are shown as read,
one per line, and are not named.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import classic_strings, read_event_records

_LOG = 'OAlerts.evtx'
_LABEL = 'Office Alerts'

__artifacts_v2__ = {
    "officeAlerts": {
        "name": "Office Alerts",
        "description": "Records of the OAlerts event log, written by a provider whose stored name is Microsoft "
                       "Office, a number, then Alerts: the time, the provider name, and the alert's event data "
                       "strings.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from OAlerts.evtx in Windows\\System32\\winevt\\Logs, named in the report's located-at line: "
                 "every record of it that renders and parses as XML, read the way scripts/windows_evtx.py describes; "
                 "the run log counts any that do not. Event Time is the record's TimeCreated, converted to UTC and "
                 "cut to whole microseconds. Event ID, Record ID and Computer are the text of those System elements, "
                 "and Provider is the Provider element's Name attribute; on every tested record the Event ID was 300 "
                 "and the provider was Microsoft Office 15 Alerts (cfreds_leakage_win7) or Microsoft Office 16 Alerts "
                 "(hexordia_mvs2025_win11, lonewolf_win10). Alert Text is the record's event data, which on every "
                 "tested record was one value, a string array of 2 to 6 strings; its strings are shown one per line "
                 "in stored order, and some of them hold line breaks of their own. No published description of those "
                 "strings was found, so they are not named. A record shows that an alert was written to this log "
                 "under that provider name, not that anyone saw or answered it.",
        "paths": ('*/Windows/System32/winevt/Logs/OAlerts.evtx',),
        "output_types": ["standard"],
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 6 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 2 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no OAlerts.evtx)",
        },
    },
}


@artifact_processor
def officeAlerts(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Provider', 'Alert Text', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL)
    data_list = []
    for record in records:
        text = '\n'.join(classic_strings(record.values))
        data_list.append((record.time, record.event_id, record.provider, text, record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
