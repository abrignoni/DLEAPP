"""Windows Installer (MsiInstaller) Application event log parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the MsiInstaller events in the Application log that record the outcome of
an installation, removal, configuration change or update of a Windows Installer
product. Event IDs and the meaning of their fields are sourced in the notes.
"""

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import classic_strings, read_event_records

_LOG = 'Application.evtx'

# Event IDs from Microsoft's Windows Installer event logging documentation; the
# 117xx IDs are Windows Installer error messages plus 10,000 (see notes).
_PRODUCT_EVENTS = {
    '1033': 'Installation completed',
    '1034': 'Removal completed',
    '1035': 'Configuration change completed',
}
_UPDATE_EVENTS = {
    '1036': 'Update installation completed',
    '1037': 'Update removal completed',
}
_MESSAGE_EVENTS = {
    '11707': 'Installation operation completed successfully',
    '11708': 'Installation operation failed',
    '11724': 'Removal completed successfully',
    '11725': 'Removal failed',
    '11728': 'Configuration completed successfully',
    '11729': 'Configuration failed',
}
_EVENTS = {**_PRODUCT_EVENTS, **_UPDATE_EVENTS, **_MESSAGE_EVENTS}

__artifacts_v2__ = {
    "msiInstallerEvents": {
        "name": "Windows Installer Product Events",
        "description": "Windows Installer (MsiInstaller) product installation, "
                       "removal, configuration and update outcome events from the "
                       "Application event log, with the product name, version, "
                       "manufacturer and status each record stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Application.evtx, named in the report's located-at line; only "
                 "records of the MsiInstaller provider with Event ID 1033 to 1037, 11707, "
                 "11708, 11724, 11725, 11728 or 11729 are read. Microsoft's Windows Installer "
                 "event logging documentation gives 1033 (installation), 1034 (removal) and "
                 "1035 (configuration change) the fields Product, Version, Language, "
                 "completion status and Manufacturer, and 1036 and 1037 (update installation "
                 "and removal) an Update field before the status "
                 "(https://github.com/MicrosoftDocs/win32/blob/"
                 "e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Msi/"
                 "event-logging.md#L181-L205); it states that errors are logged with a "
                 "message ID equal to the Windows Installer error number plus 10,000 "
                 "(#L21), so 11707, 11708, 11724, 11725, 11728 and 11729 are error messages "
                 "1707, 1708, 1724, 1725, 1728 and 1729: installation operation completed "
                 "successfully or failed, removal completed successfully or failed, and "
                 "configuration completed successfully or failed "
                 "(https://github.com/MicrosoftDocs/win32/blob/"
                 "e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/Msi/"
                 "windows-installer-error-messages.md#L92-L114). Product, Version, Language, "
                 "Status (as stored), Manufacturer and Update are the record's insertion "
                 "strings in that documented order, as stored; Message is the text of the "
                 "117xx events, which store the product name inside it. Update is filled "
                 "only by 1036 and 1037 and was empty on every row of pc_mus_001_win11 and "
                 "lonewolf_win10. User SID is the SID in the record's Security element and "
                 "held one value on every row of pc_mus_001_win11. Event Time (UTC) is the "
                 "record's TimeCreated SystemTime, which python-evtx renders from the "
                 "FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/"
                 "cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "Record ID is the record's EventRecordID. Computer is the machine name the "
                 "record stores: it held one value on every row of af_case2_win10 and "
                 "pc_mus_001_win11 and two values on lonewolf_win10. Not reported: the other "
                 "MsiInstaller events (1022, 1029, 1031, 1038, 1040 and 1042 on the registered "
                 "images), the records' binary data, and records of other providers in this "
                 "log that reuse these Event IDs. A record python-evtx cannot render, or whose "
                 "XML does not parse, is counted in the run log and not reported; every record "
                 "in this log rendered on the registered images. The absence of a product here "
                 "does not establish that it was never installed. Reading needs the "
                 "python-evtx package (pip install python-evtx).",
        "paths": ("*/Windows/System32/winevt/Logs/Application.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "list",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 39 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 8 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 18 rows",
        },
    },
}


def _value(strings, index):
    return strings[index].strip() if index < len(strings) else ''


@artifact_processor
def msiInstallerEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Product',
                    'Version', 'Language', 'Manufacturer', 'Update', 'Status (as stored)',
                    'Message', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(
        context, _LOG, 'Windows Installer Product Events', event_ids=set(_EVENTS),
        provider='MsiInstaller')
    data_list = []
    for record in records:
        strings = classic_strings(record.values)
        product = version = language = manufacturer = update = status = message = ''
        if record.event_id in _PRODUCT_EVENTS:
            product, version, language = _value(strings, 0), _value(strings, 1), _value(strings, 2)
            status, manufacturer = _value(strings, 3), _value(strings, 4)
        elif record.event_id in _UPDATE_EVENTS:
            product, version, language = _value(strings, 0), _value(strings, 1), _value(strings, 2)
            update, status, manufacturer = _value(strings, 3), _value(strings, 4), _value(strings, 5)
        else:
            message = _value(strings, 0)
        data_list.append((
            record.time, record.event_id, _EVENTS[record.event_id], product, version,
            language, manufacturer, update, status, message, record.user_sid,
            record.record_id, record.computer))
    return data_headers, data_list, '\n'.join(sources)
