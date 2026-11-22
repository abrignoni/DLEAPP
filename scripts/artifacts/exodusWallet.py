"""Exodus desktop wallet files, presence only, for DLEAPP.

Author: @AlexisBrignoni, Claude.

Lists the files in an exodus.wallet folder with their sizes and the times the input holds. They are read through the
seeker's peek(), so they are not staged, and nothing from them is reported: no seed, key, passphrase, address, balance
or transaction.
"""

from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.search_files import PeekUnsupported

__artifacts_v2__ = {
    "exodusWalletFiles": {
        "name": "Exodus Wallet Files",
        "description": "Files in an Exodus desktop wallet folder (exodus.wallet): name, size and the modified and "
                       "created times the input holds for each file. The files are listed without being staged or "
                       "parsed, so no seed, key, passphrase, address, balance or transaction is reported.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Exodus",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per file under a folder named exodus.wallet inside a folder named Exodus. The files are "
                 "listed through the seeker's peek(), so no copy of them goes into the report's data folder. On the "
                 "known data (windows11_arm_exodus_known_20261122, Exodus 26.11.20 on Windows 11, no wallet action "
                 "taken) the program created passphrase.json, seed.seco, storage.seco and unsafe-storage.json by "
                 "itself at its first start. Files copied or restored into the folder would look the same to this "
                 "artifact. Their presence alone does not show that a person set up, funded or used a wallet. File is "
                 "the path below exodus.wallet as the input names it. The purpose of each file was not established. "
                 "Modified (UTC) and Created (UTC) are the UTC times the input holds for the file. They are blank "
                 "when the input holds none in UTC, for example a zip member with only a DOS time. Time Source names "
                 "where the input's times came from, and reads none when no time was read. On the known data, a tar, "
                 "Modified equalled the file's NTFS last-write second on all 4 rows. Created is blank on all 4 rows. "
                 "This tar holds no creation time record for them. The same pattern would match these folder names "
                 "on macOS or Linux. Where Exodus keeps its wallet on those systems was not sourced, and neither was "
                 "run. User is the folder name after Users or home in the file's path, and is empty when the path "
                 "has neither.",
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "credit-card",
        "sample_data": {
            "windows11_arm_exodus_known_20261122": "Windows 11 build 26200 (ARM64), Exodus 26.11.20 | 4 rows",
        },
    },
}


def _instant(value):
    if value is None:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError, TypeError):
        return ''


def _within_wallet(relative):
    """The path below the exodus.wallet folder, when that folder sits directly inside a folder named Exodus."""
    parts = relative.replace('\\', '/').split('/')
    for index in range(1, len(parts) - 1):
        if parts[index] == 'exodus.wallet' and parts[index - 1].lower() == 'exodus':
            return '/'.join(parts[index + 1:])
    return ''


def _profile_user(evidence_path):
    """The folder after the first Users or home folder of a path inside the evidence, as peek() names it."""
    parts = evidence_path.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'home'):
            return parts[index + 1]
    return ''


@artifact_processor
def exodusWalletFiles(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Created (UTC)', 'datetime'), 'File', ('Size (bytes)', 'number'),
                    'Time Source', 'User')
    data_list, sources = [], []
    seeker = context.get_seeker()
    if seeker is None or not hasattr(seeker, 'peek'):
        logfunc('Exodus Wallet Files: this input gives no way to list a file without staging it')
        return data_headers, data_list, ''
    try:
        peeked = seeker.peek('*/Exodus/exodus.wallet/*', 1)
    except PeekUnsupported as exc:
        logfunc(f'Exodus Wallet Files: {exc}')
        return data_headers, data_list, ''
    seen = set()
    for item in sorted(peeked, key=lambda entry: entry.path):
        name = _within_wallet(item.path)
        if not name or item.path in seen:
            continue
        seen.add(item.path)
        times = getattr(item.info, 'times', None)
        data_list.append((_instant(times.modified) if times else '', _instant(times.created) if times else '', name,
                          item.size, times.source if times else '', _profile_user(item.path)))
        sources.append(item.path)
    return data_headers, data_list, '\n'.join(sources)
