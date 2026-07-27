__artifacts_v2__ = {
    "whatsappMedia": {
        "name": "WhatsApp Media",
        "description": "Media items recorded in ChatStorage.sqlite's ZWAMEDIAITEM "
                       "table, each joined to its message for the date and chat. "
                       "The stored file is embedded where it is present in the "
                       "extraction, and the recorded size, duration, coordinates, "
                       "title and contact-card name are reported alongside.",
        "author": "@AlexisBrignoni",
        "creation_date": "2026-07-27",
        "last_update_date": "2026-07-27",
        "requirements": "none",
        "category": "WhatsApp (Desktop)",
        "notes": "The media kind shown is derived from the stored file's extension, "
                 "so it reflects the file itself. Latitude and longitude are shown "
                 "only when the row holds a non-zero coordinate. A row can list a "
                 "media path whose file is no longer in the extraction, in which "
                 "case no file is embedded.",
        "paths": (
            '*/ChatStorage.sqlite*',
            '*/Message/Media/*',
        ),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "image",
        "sample_data": {"whatsapp_macos": "WhatsApp Desktop macOS | 43910 rows"},
    },
}

import os
from datetime import datetime, timezone

from scripts import whatsapp
from scripts.ilapfuncs import (artifact_processor, check_in_media,
                               logfunc, open_sqlite_db_readonly)

_EPOCH_MIN = datetime.min.replace(tzinfo=timezone.utc)


def _coordinate(value):
    """Return a coordinate only when it is a meaningful, non-zero fix."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return number if number else ""


@artifact_processor
def whatsappMedia(context):
    data_headers = (
        ("Message Date", "datetime"), "Chat", ("Media", "media"), "Media Kind",
        "Filename", "Size (bytes)", "Duration (s)", "Latitude", "Longitude",
        "Title", "Contact Card Name", "Local Path", "Chat JID", "Source File",
    )
    files_found = [str(f) for f in context.get_files_found()]
    source = next(iter(whatsapp.chat_storage_files(files_found)), "")
    if not source:
        return data_headers, [], ""
    database = open_sqlite_db_readonly(source)
    if database is None:
        return data_headers, [], source
    root = whatsapp.media_root(source, files_found)
    relative_source = context.get_relative_path(source)

    data_list = []
    embedded = 0
    query = """
        SELECT m.ZMESSAGEDATE, cs.ZPARTNERNAME, cs.ZCONTACTJID,
               mi.ZMEDIALOCALPATH, mi.ZFILESIZE, mi.ZMOVIEDURATION,
               mi.ZLATITUDE, mi.ZLONGITUDE, mi.ZTITLE, mi.ZVCARDNAME
        FROM ZWAMEDIAITEM mi
        LEFT JOIN ZWAMESSAGE m ON mi.ZMESSAGE = m.Z_PK
        LEFT JOIN ZWACHATSESSION cs ON m.ZCHATSESSION = cs.Z_PK
    """
    for (message_date, partner, jid, local_path, size, duration,
         latitude, longitude, title, vcard) in database.execute(query):
        media_ref = ""
        kind = ""
        filename = ""
        if local_path:
            filename = os.path.basename(local_path)
            extension = os.path.splitext(filename)[1].lstrip(".").lower()
            kind = extension
            if root:
                reference = check_in_media(local_path, name=filename)
                if reference:
                    media_ref = reference
                    embedded += 1

        data_list.append((
            whatsapp.cocoa_to_datetime(message_date),
            partner or jid or "",
            media_ref,
            kind,
            filename,
            size if size else "",
            int(duration) if duration else "",
            _coordinate(latitude),
            _coordinate(longitude),
            title or "",
            vcard or "",
            local_path or "",
            jid or "",
            relative_source,
        ))
    database.close()
    data_list.sort(key=lambda r: r[0] if isinstance(r[0], datetime) else _EPOCH_MIN)
    logfunc(f"WhatsApp Media: {len(data_list)} media item(s); {embedded} embedded.")
    return data_headers, data_list, source
