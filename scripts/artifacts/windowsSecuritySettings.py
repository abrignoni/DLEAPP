"""Security-relevant settings Windows keeps in the SOFTWARE and SYSTEM hives, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsSecuritySettings": {
        "name": "Security Settings",
        "description": "Registry settings that decide how exposed a Windows system was: Remote Desktop, User Account "
                       "Control, LSA protection and LAN Manager hashes, PowerShell and command-line logging, and "
                       "automatic logon. One row per setting, whether it is stored or not.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-10",
        "last_update_date": "2026-10-10",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "One row for each of 20 registry settings, whether the value is stored or not: Stored is Yes "
                 "or No, Data is the value as stored and empty when it is not stored, and Key Last Written "
                 "(UTC) is the last-written time of the key, which changes when any of its values is written "
                 "and is empty when the key does not exist. A value that is not stored leaves Windows on its "
                 "default, which this artifact does not state. Only values whose key and name a Microsoft page "
                 "gives are read; Data is not interpreted, and what the pages say is this. Remote Desktop: "
                 "fDenyTSConnections under Control\\Terminal Server of the current control set and under "
                 "Policies\\Microsoft\\Windows NT\\Terminal Services of SOFTWARE, 0 meaning RDP is enabled and 1 "
                 "disabled "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/rdp-error-general-troubleshooting), "
                 "and PortNumber of WinStations\\RDP-Tcp, the port Remote Desktop listens on "
                 "(https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/clients/change-listening-port). "
                 "User Account Control, under Microsoft\\Windows\\CurrentVersion\\Policies\\System: EnableLUA (run "
                 "all administrators in Admin Approval Mode, 0 disabled, 1 enabled), "
                 "ConsentPromptBehaviorAdmin (0 elevate without prompting to 5 prompt for consent for "
                 "non-Windows binaries), PromptOnSecureDesktop and FilterAdministratorToken "
                 "(https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/settings-and-configuration), "
                 "and LocalAccountTokenFilterPolicy, the UAC remote restriction for local accounts "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/windows-security/user-account-control-and-remote-restriction). "
                 "LSA, under Control\\Lsa: RunAsPPL, LSA protection, 1 with a UEFI variable and 2 without "
                 "(https://learn.microsoft.com/en-us/windows-server/security/credentials-protection-and-management/configuring-additional-lsa-protection), "
                 "LmCompatibilityLevel, the LAN Manager authentication level "
                 "(https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/network-security-lan-manager-authentication-level), "
                 "and NoLMHash, which prevents new LM hashes from being stored "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/windows-security/prevent-windows-store-lm-hash-password), "
                 "and UseLogonCredential under Control\\SecurityProviders\\WDigest, which when 0 keeps WDigest "
                 "from storing credentials in memory and when 1 has it store them "
                 "(https://support.microsoft.com/en-us/topic/microsoft-security-advisory-update-to-improve-credentials-protection-and-management-may-13-2014-93434251-04ac-b7f3-52aa-9f951c14b649). "
                 "Logging: ProcessCreationIncludeCmdLine_Enabled under Policies\\System\\Audit, the policy that "
                 "includes the command line in process creation events "
                 "(https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-admx-auditsettings), "
                 "and under Policies\\Microsoft\\Windows\\PowerShell the EnableScriptBlockLogging, "
                 "EnableModuleLogging and EnableTranscripting values of the ScriptBlockLogging, ModuleLogging "
                 "and Transcription keys "
                 "(https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-windowspowershell "
                 "and "
                 "https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-admx-powershellexecutionpolicy); "
                 "the per-user copies of those policies are not read. Automatic Logon, under Microsoft\\Windows "
                 "NT\\CurrentVersion\\Winlogon: AutoAdminLogon, DefaultUserName, DefaultDomainName and "
                 "DefaultPassword, the values that make Windows log a user on automatically, the password "
                 "being stored as plain text "
                 "(https://learn.microsoft.com/en-us/troubleshoot/windows-server/user-profiles-and-logon/turn-on-automatic-logon). "
                 "Value names are matched without case, Area groups the rows as above, Key is the key path "
                 "under the hive root and Source File is the hive; only the current control set of SYSTEM is "
                 "read. Every one of the six tested extractions gives 20 rows, 6 from SYSTEM and 14 from "
                 "SOFTWARE. On all six, PortNumber is 3389, EnableLUA is 1, ConsentPromptBehaviorAdmin is 5 "
                 "and NoLMHash is 1, and the Terminal Services policy value, FilterAdministratorToken, "
                 "LmCompatibilityLevel, UseLogonCredential and the three PowerShell logging values are not "
                 "stored, the three PowerShell keys being absent. fDenyTSConnections is 0 on szechuan_win10 "
                 "and 1 on the other five. LocalAccountTokenFilterPolicy is stored, as 1, on af_case2_win10 "
                 "only. PromptOnSecureDesktop is 1 on the four public images and 0 on "
                 "windows11_arm_known_20261001 and windows11_arm_known_20261010, which also hold RunAsPPL 2 "
                 "and ProcessCreationIncludeCmdLine_Enabled 1, neither stored on the public images. "
                 "AutoAdminLogon is 1 on af_case2_win10 and on the two build 26200 captures, and "
                 "DefaultPassword is stored on af_case2_win10 only. A setting stored in another form, a second "
                 "control set and a hive that cannot be read were tested with constructed input only. These "
                 "values are the configuration at the time of the hive: they do not show who changed a "
                 "setting, and whether Windows honoured each value on these systems was not tested. Reading "
                 "the hives requires the python-registry package; a dirty hive is read after its transaction "
                 "logs are applied, and the run log names each.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]',
                  '*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 20 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 20 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 20 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 20 rows",
            "windows11_arm_7zip_known_20261010": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 20 rows",
            "windows11_arm_known_20261010": "Windows 11 build 26200 | 20 rows",
        },
    },
}

import os

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import current_control_set, found_hives, key_written_utc, open_hive, open_key

_POLICIES = r'Microsoft\Windows\CurrentVersion\Policies\System'
_POWERSHELL = r'Policies\Microsoft\Windows\PowerShell'
# (Area for the row, key path under the hive root, value names): the settings looked for in each hive
_SOFTWARE_SETTINGS = (
    ('Remote Desktop', r'Policies\Microsoft\Windows NT\Terminal Services', ('fDenyTSConnections',)),
    ('User Account Control', _POLICIES, ('EnableLUA', 'ConsentPromptBehaviorAdmin', 'PromptOnSecureDesktop',
                                         'FilterAdministratorToken', 'LocalAccountTokenFilterPolicy')),
    ('Logging', _POLICIES + r'\Audit', ('ProcessCreationIncludeCmdLine_Enabled',)),
    ('Logging', _POWERSHELL + r'\ScriptBlockLogging', ('EnableScriptBlockLogging',)),
    ('Logging', _POWERSHELL + r'\ModuleLogging', ('EnableModuleLogging',)),
    ('Logging', _POWERSHELL + r'\Transcription', ('EnableTranscripting',)),
    ('Automatic Logon', r'Microsoft\Windows NT\CurrentVersion\Winlogon', ('AutoAdminLogon', 'DefaultUserName',
                                                                          'DefaultDomainName', 'DefaultPassword')),
)
# the same, under the control set the Select key names as current
_SYSTEM_SETTINGS = (
    ('Remote Desktop', r'Control\Terminal Server', ('fDenyTSConnections',)),
    ('Remote Desktop', r'Control\Terminal Server\WinStations\RDP-Tcp', ('PortNumber',)),
    ('LSA', r'Control\Lsa', ('RunAsPPL', 'LmCompatibilityLevel', 'NoLMHash')),
    ('LSA', r'Control\SecurityProviders\WDigest', ('UseLogonCredential',)),
)


def _data(value):
    """A value's data for the row: a string or a number as stored, the strings of a multi-string joined with
    ' | ', and bytes as hexadecimal."""
    data = value.value()
    if isinstance(data, list):
        return ' | '.join(str(item) for item in data)
    if isinstance(data, bytes):
        return data.hex()
    return data


def setting_rows(reg, settings, prefix=''):
    """The rows for the settings of one hive: (key last written, area, setting, data, stored, key path). A setting
    that is not stored gives a row too, with Stored 'No', and a key that does not exist gives its settings an
    empty time."""
    rows = []
    for area, path, names in settings:
        path = prefix + path
        key = open_key(reg, path)
        stored = {} if key is None else {value.name().lower(): value for value in key.values()}
        written = key_written_utc(key)
        for name in names:
            value = stored.get(name.lower())
            rows.append((written, area, name, '' if value is None else _data(value),
                         'No' if value is None else 'Yes', path))
    return rows


@artifact_processor
def windowsSecuritySettings(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Area', 'Setting', 'Data', 'Stored', 'Key',
                    'Source File')
    data_list, sources = [], []
    if Registry is None:
        logfunc('Security Settings: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in sorted(found_hives(context, 'SOFTWARE', 'SYSTEM')):
        relative = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            if os.path.basename(source).upper() == 'SYSTEM':
                rows = setting_rows(reg, _SYSTEM_SETTINGS, current_control_set(reg) + '\\')
            else:
                rows = setting_rows(reg, _SOFTWARE_SETTINGS)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Security Settings: could not read {relative}: {exc}')
            continue
        data_list.extend(row + (relative,) for row in rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
