"""Reader for the Chromium Local Storage LevelDB store.

Local Storage lives in ``Local Storage/leveldb`` and holds one record per
``window.localStorage`` key::

    META:<origin>                     metadata about the origin
    _<origin>\\x00<encoded key>        the stored value

Both the key remainder and the value start with an encoding marker byte:
``\\x00`` means UTF-16LE, anything else means one byte per character.

Records are read straight out of the LevelDB table and log files rather than
through a compacted view, so superseded and deleted versions of a key come
back too. That history is where drafts and selection state accumulate.
"""

from scripts.ccl import ccl_leveldb

_META_PREFIX = b"META:"


def _decode(data):
    """Decode a Local Storage key remainder or value using its marker byte."""
    if not data:
        return ""
    marker, payload = data[:1], data[1:]
    if marker == b"\x00":
        try:
            return payload.decode("utf-16-le")
        except UnicodeDecodeError:
            return payload.decode("utf-8", "replace")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload.decode("latin-1", "replace")


class StorageRecord:
    """One version of one Local Storage key."""

    __slots__ = ("origin", "key", "value", "sequence", "state", "source")

    def __init__(self, origin, key, value, sequence, state, source):
        self.origin = origin
        self.key = key
        self.value = value
        self.sequence = sequence
        self.state = state
        self.source = source

    @property
    def is_live(self):
        """True when this is not a deletion tombstone."""
        return self.state != "Deleted"


def leveldb_folders(files_found, folder_name="leveldb"):
    """Return the distinct LevelDB folders represented in a file list."""
    import os

    folders = {}
    for file_found in files_found:
        parent = os.path.dirname(str(file_found))
        if folder_name and os.path.basename(parent) != folder_name:
            continue
        try:
            real = os.path.realpath(parent)
        except OSError:
            real = parent
        folders.setdefault(real, parent)
    return list(folders.values())


def read_records(leveldb_folder):
    """Yield every :class:`StorageRecord` in a Local Storage LevelDB folder."""
    database = ccl_leveldb.RawLevelDb(leveldb_folder)
    for record in database.iterate_records_raw():
        raw_key = record.user_key
        if not raw_key or raw_key.startswith(_META_PREFIX):
            continue
        if not raw_key.startswith(b"_"):
            continue
        origin_bytes, separator, key_bytes = raw_key[1:].partition(b"\x00")
        if not separator:
            continue
        state = record.state.name if hasattr(record.state, "name") else str(record.state)
        yield StorageRecord(
            origin=origin_bytes.decode("utf-8", "replace"),
            key=_decode(key_bytes),
            value=_decode(record.value),
            sequence=record.seq,
            state=state,
            source=str(record.origin_file),
        )
