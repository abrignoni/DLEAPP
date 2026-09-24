"""Remote Desktop Connection client server history, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "rdpClientServers": {
        "name": "Remote Desktop Client Servers",
        "description": "Remote Desktop Connection client history from the Terminal Server "
                       "Client Default MRU list and Servers key in each NTUSER.DAT, with the "
                       "UsernameHint value stored for each server.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-24",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads Software\\Microsoft\\Terminal Server Client in each NTUSER.DAT: the MRU values "
                 "under Default and the subkeys under Servers. Microsoft documents that each new "
                 "Remote Desktop Connection is given MRU0 and the other values move down, so MRU "
                 "Position 0 is the most recent entry in that list. A Servers subkey is reported with "
                 "its UsernameHint value as stored and whether it has a CertHash value; an MRU entry "
                 "with no Servers subkey is reported with its position only. The time is the Servers "
                 "subkey's last-written time, which is not established as a connection time. On "
                 "pc_mus_001_win11 the user's two Servers subkeys both appear in the MRU list, both "
                 "carry a UsernameHint, and one a CertHash. Reference: Microsoft, 'Remove entries from"
                 " Remote Desktop Connection Computer', "
                 "https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/remove-entries-from-remote-desktop-connection-computer.",
        "paths": ('*/Users/*/NTUSER.DAT',),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "log-in",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no Terminal Server Client key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no Terminal Server Client key)",
        },
    },
}

import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_key,
                                      user_from_path, value_of)

_TSC = r'Software\Microsoft\Terminal Server Client'
_MRU = re.compile(r'^MRU(\d+)$')


@artifact_processor
def rdpClientServers(context):
    data_headers = (('Servers Key Last Written (UTC)', 'datetime'), 'Server', 'MRU Position',
                    'Username Hint', 'Certificate Hash Stored', 'User', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Remote Desktop Client Servers: the python-registry package is not installed')
        return data_headers, data_list, ''
    for path in found_hives(context, 'NTUSER.DAT'):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        try:
            reg = Registry.Registry(path)
            mru = {}
            default = open_key(reg, _TSC + r'\Default')
            for value in (default.values() if default else []):
                match = _MRU.match(value.name())
                if match and isinstance(value.value(), str) and value.value():
                    mru.setdefault(value.value(), int(match.group(1)))
            servers = open_key(reg, _TSC + r'\Servers')
            seen = set()
            for server in (servers.subkeys() if servers else []):
                seen.add(server.name())
                cert = value_of(server, 'CertHash')
                data_list.append((key_written_utc(server), server.name(),
                                  mru.get(server.name(), ''),
                                  value_of(server, 'UsernameHint') or '',
                                  'Yes' if cert else '', user, relative))
            for name, position in sorted(mru.items(), key=lambda item: item[1]):
                if name not in seen:
                    data_list.append(('', name, position, '', '', user, relative))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Remote Desktop Client Servers: could not read {relative}: {exc}')
            continue
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
