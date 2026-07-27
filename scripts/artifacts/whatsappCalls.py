__artifacts_v2__ = {
    "whatsappCalls": {
        "name": "WhatsApp Calls",
        "description": "Call events from CallHistory.sqlite, with the date, "
                       "duration in seconds, the outcome code the database stores, "
                       "the group JID for a group call, and the participant JIDs "
                       "recorded against each call.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Apple)",
        "notes": "Outcome Code is the ZOUTCOME value the database holds and is "
                 "reported as the raw integer rather than a guessed label such as "
                 "missed or outgoing. A duration of zero is shown as stored and "
                 "does not by itself establish that a call did not connect.",
        "paths": ('*/CallHistory.sqlite*',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "phone",
        "sample_data": {"whatsapp_macos": "WhatsApp macOS | 212 rows"},
    },
}

from datetime import datetime, timezone

from scripts import whatsapp
from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


@artifact_processor
def whatsappCalls(context):
    data_headers = (
        ("Call Date", "datetime"), "Duration (s)", "Outcome Code", "Group JID",
        "Participants", "Bytes Sent", "Bytes Received", "Call ID", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.call_history_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    relative_source = context.get_relative_path(source)

    # Participant JIDs per call event, joined back by the event primary key.
    participants = {}
    try:
        for event_pk, jid in database.execute(
                "SELECT Z1PARTICIPANTS, ZJIDSTRING FROM ZWACDCALLEVENTPARTICIPANT "
                "WHERE ZJIDSTRING IS NOT NULL"):
            if event_pk is not None:
                participants.setdefault(event_pk, []).append(jid)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logfunc(f"WhatsApp Calls: participant table unavailable ({ex}).")

    data_list = []
    query = """SELECT Z_PK, ZDATE, ZDURATION, ZOUTCOME, ZGROUPJIDSTRING,
                      ZBYTESSENT, ZBYTESRECEIVED, ZCALLIDSTRING
               FROM ZWACDCALLEVENT"""
    for (pk, date, duration, outcome, group_jid, sent, received, call_id) in database.execute(query):
        data_list.append((
            whatsapp.cocoa_to_datetime(date),
            int(duration) if duration is not None else "",
            outcome if outcome is not None else "",
            group_jid or "",
            ", ".join(participants.get(pk, [])),
            sent if sent is not None else "",
            received if received is not None else "",
            call_id or "",
            relative_source,
        ))
    database.close()
    data_list.sort(key=lambda r: r[0] if isinstance(r[0], datetime) else _EPOCH_MIN, reverse=True)
    logfunc(f"WhatsApp Calls: {len(data_list)} call event(s).")
    return data_headers, data_list, source
