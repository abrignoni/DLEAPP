"""The records of an ESE table as ESE itself shows them.

The vendored reader's getNextRow returns every leaf node of a table, including a node
carrying ESE's deleted flag fNDDeleted (TAG_DEFUNCT in the reader). ESE's own code treats
such a node as not there unless its version store still holds an update to it, and a
database read from an image has no version store in use:
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248
https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079

TableRows walks a table the way getNextRow does, page by page and tag by tag, skips the
flagged nodes and counts them, and skips and counts a record the reader cannot convert,
so one bad record does not end the table. The vendored reader itself is left unchanged
(scripts/vendor/README.md).
"""

from scripts.vendor import impacket_ese


class TableRows:
    """Iterate the records of one table; `deleted` and `unreadable` count what was skipped.

    `cap` bounds the number of tags visited, so a corrupt page's forward pointer cannot
    loop forever. `errors` keeps the first few conversion errors for the run log.
    """

    def __init__(self, database, table_name, cap=5_000_000):
        self.database = database
        self.table_name = table_name
        self.cap = cap
        self.deleted = 0
        self.unreadable = 0
        self.errors = []
        self.capped = False
        self.found = None

    def __iter__(self):
        database = self.database
        cursor = database.openTable(self.table_name)
        self.found = cursor is not None
        if cursor is None:
            return
        to_record = database._ESENT_DB__tagToRecord  # pylint: disable=protected-access
        visited = 0
        while True:
            page = cursor['CurrentPageData']
            cursor['CurrentTag'] += 1
            if cursor['CurrentTag'] >= page.tagCount or not page.record['PageFlags'] & impacket_ese.FLAGS_LEAF:
                if page.record['NextPageNumber'] == 0:
                    return
                cursor['CurrentPageData'] = database.getPage(page.record['NextPageNumber'])
                cursor['CurrentTag'] = cursor['CurrentPageData'].firstDataTag - 1
                continue
            visited += 1
            if visited > self.cap:
                self.capped = True
                return
            flags, data = page.getTag(cursor['CurrentTag'])
            for special in (impacket_ese.FLAGS_SPACE_TREE, impacket_ese.FLAGS_INDEX,
                            impacket_ese.FLAGS_LONG_VALUE):
                if page.record['PageFlags'] & special:
                    raise ValueError(f'{self.table_name}: a table walk reached a page with flags '
                                     f'{page.record["PageFlags"]:#x}')
            if flags & impacket_ese.TAG_DEFUNCT:
                self.deleted += 1
                continue
            try:
                entry = impacket_ese.ESENT_LEAF_ENTRY(flags, data)
                record = to_record(cursor, entry['EntryData'])
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.unreadable += 1
                if len(self.errors) < 3:
                    self.errors.append(f'{type(exc).__name__}: {exc}')
                continue
            yield record

    def summary(self):
        """A run-log sentence for what was skipped, or '' when nothing was."""
        parts = []
        if self.deleted:
            parts.append(f'{self.deleted} record(s) ESE marks deleted (fNDDeleted) were not read')
        if self.unreadable:
            parts.append(f'{self.unreadable} record(s) the ESE reader could not convert were skipped'
                         + (f' ({"; ".join(self.errors)})' if self.errors else ''))
        if self.capped:
            parts.append(f'the walk stopped after {self.cap:,} records')
        return f'{self.table_name}: ' + '; '.join(parts) if parts else ''
