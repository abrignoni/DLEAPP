"""Per-user COM class registrations in UsrClass.dat, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsUserComRegistrations": {
        "name": "Per-User COM Registrations",
        "description": "COM class keys in each user's UsrClass.dat under CLSID and Wow6432Node\\CLSID that have an "
                       "InprocServer32, LocalServer32 or TreatAs subkey, with the server paths, threading model, TreatAs "
                       "and ProgID as text, whether the SOFTWARE hive on the same volume holds a CLSID subkey of the "
                       "same name and whether a server path begins with a Users folder or a profile variable.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Microsoft says class registration information is stored under both HKEY_LOCAL_MACHINE\\Software\\Classes, "
                 "default settings that can apply to all users, and HKEY_CURRENT_USER\\Software\\Classes, settings that apply "
                 "only to the interactive user, that HKEY_CLASSES_ROOT merges the two, and that the user-specific settings "
                 "have priority over the default settings "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/hkey-classes-root-key.md#L13-L15)."
                 " In the merged view every subkey of the per-user tree is included, and for CLSID, a key found in both trees,"
                 " a subkey from HKEY_LOCAL_MACHINE is included only when the per-user tree has no subkey of that name "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/merged-view-of-hkey-classes-root.md#L15-L17"
                 " and "
                 "https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/merged-view-of-hkey-classes-root.md#L31-L38)."
                 " Microsoft also says that when an application runs with administrator rights and User Account Control is "
                 "disabled, COM ignores the per-user configuration "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/SysInfo/merged-view-of-hkey-classes-root.md#L19)."
                 " Microsoft says HKEY_USERS\\[SID]\\SOFTWARE\\Classes is a symbolic link to HKEY_USERS\\[SID]_Classes "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L104)."
                 " On the Windows 11 build 26200 lab virtual machine on 23 October 2026, the hivelist key named the profile's "
                 "AppData\\Local\\Microsoft\\Windows\\UsrClass.dat as the file of the user's _Classes hive, and "
                 "HKEY_CURRENT_USER\\Software\\Classes\\CLSID listed the same subkeys as that hive's CLSID key; that is the basis"
                 " for reading UsrClass.dat as the per-user Classes tree. Microsoft lists "
                 "HKEY_CURRENT_USER\\SOFTWARE\\Classes\\CLSID as redirected for applications of another processor architecture on"
                 " Windows 7 and newer, and names Wow6432Node as the redirected location for x86 processes on AMD64 Windows "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L25,"
                 " "
                 "https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L34"
                 " and "
                 "https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L98)."
                 " One row for each subkey of CLSID and of Wow6432Node\\CLSID in each UsrClass.dat that has an InprocServer32, "
                 "LocalServer32 or TreatAs subkey; a subkey with none of the three gives no row. View is CLSID or "
                 "Wow6432Node\\CLSID, CLSID is the subkey's name and Class Name its unnamed value. InprocServer32, "
                 "LocalServer32, TreatAs and ProgID are the unnamed values of those subkeys and ThreadingModel the "
                 "ThreadingModel value of InprocServer32, as stored, as text, with variables not expanded and quotes and "
                 "arguments kept; a multi-string value is joined with ' | ' and a binary value shown as hexadecimal. Key is "
                 "the subkey's path under the hive root. Microsoft documents InprocServer32 as registering an in-process "
                 "server, its unnamed value the path and ThreadingModel the threading model "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/inprocserver32.md#L13-L27),"
                 " LocalServer32 as giving the location of a local server application and optionally its command-line "
                 "arguments "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/localserver32.md#L13-L27),"
                 " TreatAs as the CLSID of a class that can emulate the current class "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/treatas.md#L13)"
                 " and ProgID as associating a ProgID with the CLSID "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/progid.md#L13)."
                 " It also says LocalServer32 is ignored when the CLSID key has a LocalService value "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/com/localserver32.md#L37);"
                 " that value is not read here. Also in SOFTWARE is Yes when the SOFTWARE hive on the same volume, the part of"
                 " the path before its Users or Windows folder, has a subkey of the same name, compared without case, under "
                 "Classes\\CLSID for the CLSID view or Classes\\Wow6432Node\\CLSID for the other, under the key Microsoft names "
                 "as the target of HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Classes "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/WinProg64/shared-registry-keys.md#L112);"
                 " it is No when that hive has none, and blank when no SOFTWARE hive, or more than one, was read for that "
                 "volume, which the run log names. Under the merge rules above, a Yes row is a per-user CLSID subkey with the "
                 "same name as one in the machine-wide tree; the machine-wide subkey's contents are not read. Server Under "
                 "Users Folder is Yes when the InprocServer32 or LocalServer32 value, leading spaces and quote removed and "
                 "compared without case, begins with \\Users\\ or \\Documents and Settings\\ and a folder name, with or without a "
                 "drive letter or %SystemDrive% before it, or with %USERPROFILE%, %APPDATA% or %LOCALAPPDATA%, forward slashes"
                 " read as backslashes, whose default paths Microsoft gives as %SystemDrive%\\Users\\%USERNAME% and folders in "
                 "it "
                 "(https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/shell/knownfolderid.md#L1701-L1702,"
                 " "
                 "https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/shell/knownfolderid.md#L2271-L2272"
                 " and "
                 "https://github.com/MicrosoftDocs/win32/blob/ca8274decead49403d70ceeed4af8d4ca74eaf11/desktop-src/shell/knownfolderid.md#L3269-L3270);"
                 " it is No otherwise and blank on a row with neither server subkey. Variables are not expanded, so a path in "
                 "a profile written through another variable reads No. Key Last Written (UTC) is the last-written time of the "
                 "CLSID subkey; it is not established as the time the class was registered. User is the folder name after "
                 "Users in the hive's path and Source File the hive. MITRE ATT&CK describes replacing COM references in the "
                 "registry as a way to run code for persistence (T1546.015, https://attack.mitre.org/techniques/T1546/015/); a"
                 " row, a Yes in either column or a server path under the Users folder is a registration to compare with the "
                 "software the user ran and is not a finding by itself. pc_mus_001_win11 gives 3,595 rows, 30 from CLSID and "
                 "3,565 from Wow6432Node\\CLSID, 3,542 with Also in SOFTWARE Yes, all in Wow6432Node\\CLSID, 50 with Server "
                 "Under Users Folder Yes, 3,544 No and 1 blank; hexordia_mvs2025_win11 gives 69 rows, 62 with Server Under "
                 "Users Folder Yes, 6 No and 1 blank; lonewolf_win10 42 rows, 2 with Also in SOFTWARE Yes, 36 with Server "
                 "Under Users Folder Yes and 6 No; af_case2_win10 44 rows, 42 Yes and 2 No; szechuan_win10 180 rows from four "
                 "UsrClass.dat hives of 45 rows each, 172 Yes and 8 No. The one row with Server Under Users Folder blank on "
                 "pc_mus_001_win11 and on hexordia_mvs2025_win11 is a CLSID subkey with a TreatAs subkey and no server; "
                 "TreatAs is blank on every other row and on all rows of af_case2_win10, lonewolf_win10 and szechuan_win10. "
                 "Also in SOFTWARE is No on all rows of af_case2_win10, hexordia_mvs2025_win11 and szechuan_win10. User holds "
                 "one value on all rows of each image with one UsrClass.dat. Source File is kept beside User because the "
                 "folder name alone does not separate two hives of the same user name on different volumes. Those counts, the "
                 "Also in SOFTWARE and Users-folder counts and the TreatAs rows were checked against a separate count over the"
                 " staged hives read with python-registry. The UsrClass.dat hives of alihadi_challenge3_win81, "
                 "alihadi_threatsim_server2019, cfreds_leakage_win7, ou_ransomware_server2022 and szechuan_dc01_server2012r2 "
                 "hold no CLSID or Wow6432Node\\CLSID key and give no rows. A run over a tree holding two volumes, each with "
                 "its own SOFTWARE hive, a third user with no SOFTWARE hive and copies of hives at paths the artifact does not"
                 " declare gave exactly the rows of the three declared hives, with Also in SOFTWARE matched to each user's own"
                 " volume and blank for the third. A path written through %USERPROFILE%, %APPDATA% or %LOCALAPPDATA%, a CLSID "
                 "with both servers and a multi-string value were tested with constructed input only; no tested image holds a "
                 "CLSID with both servers. Reading the hives requires the python-registry package. A dirty hive is read after "
                 "the entries of its .LOG1 and .LOG2 transaction logs that continue its sequence are applied; the run log "
                 "names each hive replayed and each dirty hive read as it is, with the reason.",
        "paths": ('*/AppData/Local/Microsoft/Windows/[Uu]sr[Cc]lass.[Dd]at',
                  '*/AppData/Local/Microsoft/Windows/[Uu][Ss][Rr][Cc][Ll][Aa][Ss][Ss].[Dd][Aa][Tt].[Ll][Oo][Gg][12]',
                  '*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "cpu",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 44 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (UsrClass.dat holds no CLSID key)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (UsrClass.dat holds no CLSID key)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (UsrClass.dat holds no CLSID key)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 69 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 42 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (UsrClass.dat holds no CLSID key)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3595 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (UsrClass.dat holds no CLSID key)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 180 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no UsrClass.dat in the extraction)",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 0 rows (no UsrClass.dat in the extraction)",
        },
    },
}

import re

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import found_hives, key_written_utc, open_hive, open_key, user_from_path

# (View, key path under the UsrClass.dat root, key path of the same view under the SOFTWARE hive root)
VIEWS = (
    ('CLSID', 'CLSID', r'Classes\CLSID'),
    (r'Wow6432Node\CLSID', r'Wow6432Node\CLSID', r'Classes\Wow6432Node\CLSID'),
)
_SERVERS = ('inprocserver32', 'localserver32')
# A drive letter or %SystemDrive% followed by a Users or Documents and Settings folder, or a variable for a profile
# folder.
_USER_PATH = re.compile(r'^(?:[a-z]:|%systemdrive%)?\\(?:users|documents and settings)\\[^\\]+'
                        r'|^%(?:userprofile|appdata|localappdata)%', re.I)


def _default(key):
    """A key's unnamed value as stored, as text, or ''."""
    if key is None:
        return ''
    for value in key.values():
        if value.name() in ('', '(default)'):
            data = value.value()
            if isinstance(data, list):
                return ' | '.join(str(item) for item in data if item != '')
            return data.hex() if isinstance(data, bytes) else str(data)
    return ''


def _named(key, wanted):
    if key is None:
        return ''
    for value in key.values():
        if value.name().lower() == wanted:
            data = value.value()
            return data.hex() if isinstance(data, bytes) else str(data)
    return ''


def under_users_folder(path):
    """Whether a server path, leading spaces and quote removed, is in a Users or Documents and Settings folder or
    begins with a variable for a profile folder."""
    text = path.strip().lstrip('"').replace('/', '\\')
    return bool(_USER_PATH.match(text))


def volume_of(relative):
    """The part of a path within the extraction before its Users or Windows folder, compared without case."""
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts):
        if part.lower() in ('users', 'windows'):
            return '/'.join(parts[:index]).lower()
    return None


def machine_clsids(reg):
    """{View: the CLSID key names, in lower case, that the SOFTWARE hive holds for that view}."""
    held = {}
    for view, _user_path, machine_path in VIEWS:
        key = open_key(reg, machine_path)
        held[view] = {sub.name().lower() for sub in key.subkeys()} if key is not None else set()
    return held


def registration_rows(reg, machine):
    """(key last written, view, CLSID, name, InprocServer32, ThreadingModel, LocalServer32, TreatAs, ProgID,
    in SOFTWARE, under a user profile, key) for each CLSID key that names a server or a TreatAs class."""
    rows = []
    for view, user_path, _machine_path in VIEWS:
        clsids = open_key(reg, user_path)
        if clsids is None:
            continue
        for entry in clsids.subkeys():
            subs = {sub.name().lower(): sub for sub in entry.subkeys()}
            if not any(name in subs for name in _SERVERS + ('treatas',)):
                continue
            inproc, local = subs.get('inprocserver32'), subs.get('localserver32')
            servers = [_default(key) for key in (inproc, local) if key is not None]
            if machine is None:
                in_machine = ''
            else:
                in_machine = 'Yes' if entry.name().lower() in machine[view] else 'No'
            user = ('Yes' if any(under_users_folder(path) for path in servers) else 'No') if servers else ''
            rows.append((key_written_utc(entry), view, entry.name(), _default(entry), _default(inproc),
                         _named(inproc, 'threadingmodel'), _default(local), _default(subs.get('treatas')),
                         _default(subs.get('progid')), in_machine, user, f'{user_path}\\{entry.name()}'))
    return rows


@artifact_processor
def windowsUserComRegistrations(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'View', 'CLSID', 'Class Name', 'InprocServer32',
                    'ThreadingModel', 'LocalServer32', 'TreatAs', 'ProgID', 'Also in SOFTWARE',
                    'Server Under Users Folder', 'Key', 'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Per-User COM Registrations: the python-registry package is not installed')
        return data_headers, data_list, ''
    machines = {}
    for source in sorted(found_hives(context, 'SOFTWARE')):
        relative = context.get_relative_path(source)
        try:
            held = machine_clsids(open_hive(source, context))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Per-User COM Registrations: could not read {relative}: {exc}')
            continue
        volume = volume_of(relative)
        if volume in machines:
            logfunc(f'Per-User COM Registrations: more than one SOFTWARE hive for {volume or "the extraction root"}; '
                    f'Also in SOFTWARE is left blank for its users')
            machines[volume] = None
        else:
            machines[volume] = held
    for source in sorted(found_hives(context, 'USRCLASS.DAT')):
        relative = context.get_relative_path(source)
        machine = machines.get(volume_of(relative))
        if machine is None:
            logfunc(f'Per-User COM Registrations: no single SOFTWARE hive beside {relative}; '
                    f'Also in SOFTWARE is left blank for it')
        try:
            rows = registration_rows(open_hive(source, context), machine)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Per-User COM Registrations: could not read {relative}: {exc}')
            continue
        user = user_from_path(relative)
        data_list.extend((row[0], user) + row[1:] + (relative,) for row in rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)

