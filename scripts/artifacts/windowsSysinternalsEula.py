"""Sysinternals EULA acceptance parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Sysinternals tools keep a Software\\Sysinternals\\<tool> key in the registry hive of
the account that ran them, holding an EulaAccepted value. This reads that key in each
user's NTUSER.DAT, in the service profiles' NTUSER.DAT files and in the DEFAULT hive,
one row per tool key, with the key's last written time.
"""

import os

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import key_written_utc

_KEY = 'Software\\Sysinternals'

__artifacts_v2__ = {
    "windowsSysinternalsEula": {
        "name": "Sysinternals EULA Acceptance",
        "description": "Sysinternals tool keys in each account's registry hive, with the "
                       "EulaAccepted value and the key's last written time, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-26",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads Software\\Sysinternals in each user's NTUSER.DAT, in the NTUSER.DAT of each "
                 "folder under Windows/ServiceProfiles and in Windows/System32/config/DEFAULT, one row "
                 "per subkey. Velociraptor's Windows.Registry.Sysinternals.Eulacheck artifact reads "
                 "the same key in every loaded user hive, describes a tool writing an EulaAccepted "
                 "value there when its EULA is accepted on first run, and reports the key's last "
                 "written time as the time accepted "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Registry/Sysinternals/Eulacheck.yaml#L2-L7, "
                 "https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Registry/Sysinternals/Eulacheck.yaml#L31-L38). "
                 "Tool is the subkey's name, EulaAccepted its EulaAccepted value as stored, blank when "
                 "absent, Key Last Written (UTC) the subkey's last written time, and Profile the "
                 "folder holding the NTUSER.DAT, or DEFAULT for that hive. Microsoft describes a key's "
                 "last write time as the last time the key or any of its values was modified "
                 "(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winreg/nf-winreg-regqueryinfokeyw.md#L140-L141), "
                 "so it can reflect a later change than the acceptance. Of the tested images only "
                 "af_case2_win10 carried the key, in the IEUser hive, with BGInfo and SDelete, each "
                 "EulaAccepted 1. Its SDelete key was last written 78 milliseconds before the only run "
                 "time in the SDELETE.EXE Prefetch file, and its BGInfo key 0.4 seconds after the "
                 "earliest of the 8 run times in the BGINFO.EXE Prefetch file, the later runs leaving "
                 "it unchanged. No service profile NTUSER.DAT or DEFAULT hive on the tested images "
                 "held the key, so reading those hives is unexercised. Values under a tool key other "
                 "than EulaAccepted are not reported.",
        "paths": ('*/Users/*/NTUSER.DAT', '*/Windows/ServiceProfiles/*/NTUSER.DAT',
                  '*/Windows/System32/config/DEFAULT'),
        "output_types": ["standard"],
        "artifact_icon": "tool",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 2 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no hive holds a Software\\Sysinternals key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no hive holds a Software\\Sysinternals key)",
        },
    },
}


def profile_of(relative):
    """The profile a hive belongs to: the folder holding NTUSER.DAT, or DEFAULT."""
    parts = relative.replace('\\', '/').rstrip('/').split('/')
    if parts[-1].upper() == 'DEFAULT':
        return 'DEFAULT'
    return parts[-2] if len(parts) >= 2 else ''


@artifact_processor
def windowsSysinternalsEula(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Tool', 'EulaAccepted', 'Profile')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Sysinternals EULA: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted({str(f) for f in context.get_files_found()}):
        name = os.path.basename(source).upper()
        if not os.path.isfile(source) or name not in ('NTUSER.DAT', 'DEFAULT'):
            continue
        relative = context.get_relative_path(source)
        try:
            root = Registry.Registry(source).open(_KEY)
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Sysinternals EULA: could not read {relative}: {exc}')
            continue
        for tool in root.subkeys():
            values = {value.name(): value.value() for value in tool.values()}
            accepted = values.get('EulaAccepted', '')
            data_list.append((key_written_utc(tool), tool.name(),
                              accepted if isinstance(accepted, int) else '', profile_of(relative)))
        sources.append(source)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0])))
    return data_headers, data_list, '\n'.join(sources)
