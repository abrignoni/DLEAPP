"""Microsoft Defender Antivirus exclusions parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the Defender exclusion keys in the SOFTWARE hive: Microsoft\\Windows
Defender\\Exclusions and the Group Policy location Policies\\Microsoft\\Windows
Defender\\Exclusions, with their subkeys (Paths, Extensions, Processes,
IpAddresses, TemporaryPaths as present). Each value is one row, with the last
written time of the key that holds it, reported as stored. Sources are in the
notes.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import Registry, found_hives, key_written_utc, open_key

# (Location label, key path under the SOFTWARE hive root)
_EXCLUSION_KEYS = (
    ('Defender configuration', r"Microsoft\Windows Defender\Exclusions"),
    ('Group Policy', r"Policies\Microsoft\Windows Defender\Exclusions"),
)

__artifacts_v2__ = {
    "defenderExclusions": {
        "name": "Microsoft Defender Exclusions",
        "description": "Values under the Microsoft Defender Antivirus Exclusions keys "
                       "in the SOFTWARE hive, the Defender configuration key and the "
                       "Group Policy key, with the last written time of the key "
                       "holding each value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-09-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SOFTWARE hive, named in the report's located-at line, with "
                 "python-registry. Two keys are read: Microsoft\\Windows "
                 "Defender\\Exclusions, labelled Defender configuration in Location, and "
                 "Policies\\Microsoft\\Windows Defender\\Exclusions, labelled Group "
                 "Policy. Each value directly under either key and each value in one of "
                 "its subkeys is one row: Subkey is the subkey's name, blank for a value "
                 "directly under the key; Value Name and Value Data (as stored) are the "
                 "value's name and data as stored; Registry Key is the key's path under "
                 "the hive root. Key Last Written (UTC) is the last written time of the "
                 "key holding the value, as python-registry reads it; it belongs to the "
                 "key, so every value in one key shares it. Microsoft's Policy CSP page "
                 "maps the ExcludedExtensions, ExcludedPaths and ExcludedProcesses "
                 "policies to the Group Policy settings Exclusions_Extensions, "
                 "Exclusions_Paths and Exclusions_Processes, whose registry key it gives "
                 "as Software\\Policies\\Microsoft\\Windows Defender\\Exclusions ('Policy "
                 "CSP - Defender', snapshot "
                 "https://web.archive.org/web/20260915071729/https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-defender); "
                 "no Microsoft page describing the layout of the Defender configuration "
                 "key was found, so its subkeys and values are reported as stored. No "
                 "registered image carries the Group Policy key, so that branch is "
                 "unexercised. The Defender configuration key was present on the three "
                 "registered images, with Extensions, Paths, Processes and TemporaryPaths "
                 "subkeys and, on pc_mus_001_win11, an IpAddresses subkey; the one value "
                 "among them sat in Paths on af_case2_win10 and the others were empty, so "
                 "this artifact reports 1 row on af_case2_win10 and none on "
                 "pc_mus_001_win11 or lonewolf_win10. Microsoft documents a setting, "
                 "HideExclusionsFromLocalAdmins, under which exclusions are not visible in "
                 "Get-MpPreference or Registry Editor ('Configure custom exclusions for "
                 "Microsoft Defender Antivirus', snapshot "
                 "https://web.archive.org/web/20260610212440/https://learn.microsoft.com/en-us/defender-endpoint/configure-exclusions-microsoft-defender-antivirus); "
                 "whether exclusions hidden that way are present in an acquired hive was "
                 "not tested. A row records a value stored under an Exclusions key; it "
                 "does not by itself establish who added it or whether Defender applied it.",
        "paths": ("*/Windows/System32/config/SOFTWARE",),
        "output_types": ["standard"],
        "artifact_icon": "slash",
        "sample_data": {
                           "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the exclusion subkeys hold no values)",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the exclusion subkeys hold no values)",
                       },
    },
}


def _value_text(value):
    data = value.value()
    return data if isinstance(data, str) else str(data)


def _exclusion_rows(key, location, key_path):
    """Rows for the values directly under an Exclusions key and under each subkey."""
    for value in key.values():
        yield (key_written_utc(key), '', value.name(), _value_text(value), location, key_path)
    for subkey in key.subkeys():
        sub_path = f'{key_path}\\{subkey.name()}'
        for value in subkey.values():
            yield (key_written_utc(subkey), subkey.name(), value.name(),
                   _value_text(value), location, sub_path)


@artifact_processor
def defenderExclusions(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Subkey', 'Value Name',
                    'Value Data (as stored)', 'Location', 'Registry Key')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Microsoft Defender Exclusions: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in found_hives(context, 'SOFTWARE'):
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
            rows = []
            present = []
            for location, key_path in _EXCLUSION_KEYS:
                key = open_key(reg, key_path)
                if key is None:
                    continue
                present.append(location)
                rows.extend(_exclusion_rows(key, location, key_path))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Microsoft Defender Exclusions: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        logfunc(f'Microsoft Defender Exclusions: {len(rows)} value(s) under the exclusion '
                f'keys in {relative_source}; keys present: '
                f'{", ".join(present) if present else "none"}')
        data_list.extend(rows)

    return data_headers, data_list, '\n'.join(sources)
