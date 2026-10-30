"""Shares the Server service holds in the SYSTEM hive, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsLanmanServerShares": {
        "name": "LanmanServer Shares",
        "description": "One row for each named value of Services\\LanmanServer\\Shares in each control set of the SYSTEM "
                       "hive, with the fields of the value split by name and reported as stored, the Shares key's "
                       "last-written time, whether the control set is the current one and whether Shares\\Security "
                       "holds a value of the same name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Microsoft says shares and their assigned share permissions are stored in "
                 "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Shares, and that the key can serve as a "
                 "reference of the share names and the location of the shared folders "
                 "(https://github.com/MicrosoftDocs/SupportArticles-docs/blob/13b2d50440e0b880deadd46afe076b6b3625235f/support/windows-server/networking/recovery-process-of-dfs-namespace.md#L380-L386)."
                 " Each named value of the key in each ControlSet00N key of the SYSTEM hive gives one row, so a share held in "
                 "two control sets gives two rows. Control Set is that key's name, and Current Control Set is Yes for the "
                 "control set the Select key's Current value names and No for the others; it is blank when the hive has no "
                 "Select\\Current value or that value is not a number. Value Name is the name of the value. Every tested value "
                 "is a REG_MULTI_SZ whose strings take the form Field=Value, and each string is split at its first =. "
                 "ShareName, Path, Remark, Type, Permissions, MaxUses, CSCFlags and CATimeout are those fields as stored, text"
                 " unchanged and blank when the value holds no such field. Other Fields holds, joined with ' | ', every other "
                 "non-empty string of the value as stored: a field with another name, a second field of a name already shown, "
                 "or a string without =. A value of another type is reported with its type and data in Other Fields. The "
                 "Microsoft article cited above does not document these fields, so no meaning is given here for Type, "
                 "Permissions, MaxUses, CSCFlags or CATimeout, and their numbers are reported as stored. Security Value is Yes"
                 " when the Security subkey of the same Shares key holds a value whose name equals Value Name, compared "
                 "without case, and No otherwise. The Security value is not decoded: the article cited above does not document"
                 " its format. Key Last Written (UTC) is the last-written time of the Shares key, one time for the key and not"
                 " for any one value, so it is not established as the time any one share was created or changed; Key is the "
                 "key path under the hive root and Source File the hive. On alihadi_threatsim_server2019 the 2 values are held"
                 " in ControlSet001 and ControlSet002, giving 4 rows. On ou_ransomware_server2022 ControlSet001 holds 3 values"
                 " and ControlSet002 a Shares key with none, giving 3 rows, so Control Set, Current Control Set and Key hold "
                 "one value on all 3 rows there. On szechuan_dc01_server2012r2 ControlSet001 and ControlSet002 hold 3 values "
                 "each, giving 6 rows. On each of the three images Key Last Written (UTC) holds one value on every row, "
                 "because the two Shares keys carry the same last-written time where both hold values. On those 13 rows "
                 "ShareName equals Value Name, every value holds the eight fields once each, and python-registry returns two "
                 "empty strings for its terminating nulls, Type is 0, MaxUses is 4294967295 and CATimeout is 0 on every row, "
                 "Other Fields is blank and Security Value is Yes on every row. The nine client images tested hold a Shares "
                 "key with no values and give no rows. Those counts were checked against a separate count of the values in "
                 "each staged SYSTEM hive read with python-registry. A run over a tree holding the SYSTEM hives of "
                 "alihadi_threatsim_server2019 and szechuan_dc01_server2012r2 on two volumes, and a copy of a third SYSTEM "
                 "hive in a folder the artifact does not declare, gave exactly their 10 rows, each with its own hive in Source"
                 " File. A value of another type, a string without =, a repeated field and a hive without a Select key were "
                 "tested with constructed input only. A row is a share definition the hive holds; it does not establish that "
                 "the share was reachable or used. Reading the hive requires the python-registry package. A dirty hive is read"
                 " with the entries of its .LOG1 and .LOG2 transaction logs applied when they continue its sequence and pass "
                 "the checks in scripts/registry_recovery.py, and otherwise as it is; the run log names each hive replayed and"
                 " each dirty hive read as it is, with the reason.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "share-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the Shares key holds no values)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (the Shares key holds no values)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 4 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (the Shares key holds no values)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (the Shares key holds no values)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the Shares key holds no values)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the Shares key holds no values)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 6 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the Shares key holds no values)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (the Shares key holds no values)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (the Shares key holds no values)",
            "cfreds_hacking_case_winxp": "Windows XP build 2600 | 2 rows",
        },
    },
}

from collections import Counter

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key, value_of

_SHARES = r'Services\LanmanServer\Shares'
FIELDS = ('ShareName', 'Path', 'Remark', 'Type', 'Permissions', 'MaxUses', 'CSCFlags', 'CATimeout')


def split_fields(data, counts):
    """(the eight named fields as stored, Other Fields) for the data of one Shares value."""
    shown = dict.fromkeys(FIELDS, '')
    seen, other = set(), []
    for item in data:
        text = str(item)
        if not text:
            continue
        name, equals, rest = text.partition('=')
        if equals and name in shown and name not in seen:
            shown[name] = rest
            seen.add(name)
        else:
            other.append(text)
    if other:
        counts['strings reported in Other Fields'] += len(other)
    return tuple(shown.values()), ' | '.join(other)


def share_rows(reg, counts):
    """(key last written, control set, current, value name, eight fields, other, security, key) per Shares value."""
    current = value_of(open_key(reg, 'Select'), 'Current')
    current_name = f'controlset{current:03d}' if isinstance(current, int) else None
    rows = []
    sets = sorted((key for key in reg.root().subkeys() if key.name().lower().startswith('controlset')),
                  key=lambda key: key.name().lower())
    for control_set in sets:
        path = f'{control_set.name()}\\{_SHARES}'
        shares = open_key(reg, path)
        if shares is None:
            continue
        security = open_key(reg, path + '\\Security')
        secured = {value.name().lower() for value in security.values()} if security is not None else set()
        is_current = '' if current_name is None else ('Yes' if control_set.name().lower() == current_name else 'No')
        for value in shares.values():
            if value.name() in ('', '(default)'):
                continue
            data = value.value()
            if not isinstance(data, list):
                counts['values that are not a multi-string, reported in Other Fields'] += 1
                data = [f'{value.value_type_str()}: ' + (data.hex() if isinstance(data, bytes) else str(data))]
            fields, other = split_fields(data, counts)
            rows.append((key_written_utc(shares), control_set.name(), is_current, value.name()) + fields
                        + (other, 'Yes' if value.name().lower() in secured else 'No', path))
    return rows


@artifact_processor
def windowsLanmanServerShares(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Control Set', 'Current Control Set', 'Value Name') \
        + FIELDS + ('Other Fields', 'Security Value', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('LanmanServer Shares: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SYSTEM')):
        relative = context.get_relative_path(source)
        counts = Counter()
        try:
            rows = share_rows(open_hive(source, context), counts)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'LanmanServer Shares: could not read {relative}: {exc}')
            continue
        if counts:
            logfunc(f'LanmanServer Shares: {relative}: ' + ', '.join(f'{n} {k}' for k, n in sorted(counts.items())))
        data_list.extend(row + (relative,) for row in rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)

