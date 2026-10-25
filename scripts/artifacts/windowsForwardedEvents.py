"""Windows forwarded event records for DLEAPP.

Author: @AlexisBrignoni, Claude.

A Windows Event Collector subscription stores the events it receives in the local
log it names; wecutil's quick-config enables the ForwardedEvents channel for it.
Each record holds a System and an EventData element and, for a subscription
delivering RenderedText, a RenderingInfo element holding the
event's message and names as rendered for delivery (scripts/windows_evtx.py,
EventRecord.rendering).
"""

import os

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import EventRecordStream

_LABEL = 'Forwarded Events'

__artifacts_v2__ = {
    "forwardedEvents": {
        "name": "Forwarded Events",
        "description": "Records stored in the ForwardedEvents event log and its archives: the time, the computer, "
                       "channel, provider and event ID each record names, the message and names it carries as "
                       "rendered text, and its event data.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-25",
        "last_update_date": "2026-10-25",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from ForwardedEvents.evtx and the files named Archive-ForwardedEvents-*.evtx in the same "
                 "folder, named in the report's located-at line: every record of each that renders and parses as XML; the run "
                 "log counts any that do not. wecutil's /lf option names the local event log that stores the events "
                 "a subscription receives, and its quick-config enables the ForwardedEvents channel so a subscription "
                 "can be created; a subscription that names another log with /lf is not read here (Microsoft, 'wecutil', "
                 "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/wecutil). "
                 "Microsoft gives an archived log's file name as Archive-LOG_FILE_NAME-YYYY-MM-DD-hh-mm-ss-nnn.evtx and gives the time in "
                 "that event as UTC (Microsoft, '1105(S): Event log automatic backup.', "
                 "https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-1105). "
                 "Rows are in time order, and a record whose time does not parse is listed last. Event Time is the record's TimeCreated, converted to UTC and "
                 "cut to whole microseconds. Computer, Channel, Event ID and Event Record ID are the text of those "
                 "System elements; Provider is the Provider element's Name attribute, User SID the Security element's "
                 "UserID attribute and Process ID the Execution element's ProcessID attribute; Microsoft's event schema describes Computer as the name of the computer "
                 "on which the event occurred and Channel as the channel the event was logged to "
                 "(SystemPropertiesType, "
                 "https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-systempropertiestype-complextype). "
                 "Message, Level, Task, Opcode and Keywords (Rendered) and Rendering Culture come from the record's "
                 "RenderingInfo element, which the schema gives as the rendered message strings of the event and "
                 "of its level, task, opcode and keywords, in the culture named, carried only by events collected "
                 "by the Windows Event Collector service (RenderingInfoType, "
                 "https://learn.microsoft.com/en-us/windows/win32/wes/eventschema-renderingtype-complextype). "
                 "wecutil gives a subscription's content format as RenderedText, which attaches the localized "
                 "strings, or Events. A record with no RenderingInfo leaves those columns blank; no such record "
                 "has been read here. Event Data lists the record's EventData values in order, each as Name: value "
                 "where the value has a name. Log File is the name of the file the row was read from. The records "
                 "of this log hold their elements without a template, which python-evtx 0.8.1 does not render; "
                 "they are read the way scripts/windows_evtx.py describes. On evtx_forwarded_events_rust_evtx, the "
                 "Archive-ForwardedEvents-test.evtx sample of the evtx crate (omerbenamram/evtx at commit "
                 "da613729880438bed1aabc8ba32858f3cc39bb62, MIT or Apache-2.0), all 653 records were read and "
                 "rendered, the number the crate's own test of that file expects "
                 "(https://github.com/omerbenamram/evtx/blob/da613729880438bed1aabc8ba32858f3cc39bb62/tests/test_full_samples.rs#L208). "
                 "Every one carries RenderingInfo, with Culture en-US and a non-empty Message. The rendered "
                 "Channel was blank on 2 records and otherwise equal to the System Channel; the rendered Provider "
                 "was blank on 2 records, the rendered Opcode on 2, the rendered Task on 3 and the rendered Keywords "
                 "on 1. That sample is "
                 "an archive file only: no live ForwardedEvents.evtx, no record delivered as Events, and no culture "
                 "other than en-US has been tested. The 38 zipped Windows corpus keys hold no file named for a ForwardedEvents log, live or "
                 "archived. Of the 17 raw Windows corpus images, 15 were searched for a live ForwardedEvents.evtx and "
                 "none holds one; the two BitLocker volumes were not searched, and archived ForwardedEvents files on the "
                 "raw images were not searched for. A row shows that the collector stored that record; the Computer field is what the "
                 "record names. User SID, when present, is the record's Security UserID, which the schema calls the "
                 "user that logged the event; it does not by itself show who was using the computer. Reading the logs needs the python-evtx package.",
        "paths": ("*/Windows/System32/winevt/Logs/ForwardedEvents.evtx",
                  "*/Windows/System32/winevt/Logs/Archive-ForwardedEvents-*.evtx"),
        "output_types": ["standard"],
        "artifact_icon": "share-2",
        "sample_data": {
            "evtx_forwarded_events_rust_evtx": "Public sample log, Windows build not recorded | 653 rows",
        },
    },
}


def event_data_text(record):
    """The record's EventData values in order, one per line, as Name: value where a name is stored."""
    return '\n'.join(f'{name}: {text}' if name else text for name, text in record.data_pairs)


def forwarded_row(record):
    rendering = record.rendering
    return (record.time, record.computer, record.channel, record.provider, record.event_id,
            rendering.get('Message', ''), rendering.get('Level', ''), rendering.get('Task', ''),
            rendering.get('Opcode', ''), rendering.get('Keywords', ''), rendering.get('Culture', ''),
            event_data_text(record), record.user_sid, record.process_id, record.record_id,
            os.path.basename(record.source))


def _in_time_order(records):
    """Oldest first; a record whose time did not parse goes last, in the order read."""
    dated = [r for r in records if r.time != '']
    undated = [r for r in records if r.time == '']
    return sorted(dated, key=lambda r: r.time) + undated


@artifact_processor
def forwardedEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Computer', 'Channel', 'Provider', 'Event ID',
                    'Message (Rendered)', 'Level (Rendered)', 'Task (Rendered)', 'Opcode (Rendered)',
                    'Keywords (Rendered)', 'Rendering Culture', 'Event Data', 'User SID', 'Process ID',
                    'Event Record ID', 'Log File')
    records = list(EventRecordStream(context, '.evtx', _LABEL))
    data_list = []
    sources = []
    for record in _in_time_order(records):
        data_list.append(forwarded_row(record))
        if record.source not in sources:
            sources.append(record.source)
    return data_headers, data_list, '\n'.join(sources)
