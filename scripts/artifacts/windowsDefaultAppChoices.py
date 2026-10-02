"""Windows default app user choice parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the UserChoice and UserChoiceLatest keys of each user's NTUSER.DAT: for a file extension (under
Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts) or a URL scheme (under
Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations), the program ID and hash the key stores and the
time the key was last written.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive, open_key,
                                      user_from_path)

_LABEL = 'Default App User Choices'
_PARENTS = (r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts',
            r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations')
_CHOICES = ('userchoice', 'userchoicelatest')


__artifacts_v2__ = {
    "defaultAppUserChoices": {
        "name": "Default App User Choices",
        "description": "UserChoice and UserChoiceLatest keys of each NTUSER.DAT: the program ID and hash stored for "
                       "a file extension or URL scheme, with the time the key was last written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Reads each NTUSER.DAT the paths match with python-registry and reports one row per key named "
                 "UserChoice or UserChoiceLatest (names compared without case) below each subkey of "
                 "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts and of "
                 "Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations. Association is the name of that "
                 "subkey: on every tested row a file extension with its period under FileExts and a name without "
                 "one, such as http or mailto, under UrlAssociations. Program ID is the key's ProgId value and Hash "
                 "its Hash value, value names compared without case, each reported as stored when it is text and "
                 "left blank otherwise; no tested key held one that was not text. A key with no ProgId value that is "
                 "text has the ProgId value of its subkey named ProgId read instead, which is where the 158 "
                 "UserChoiceLatest keys of the tested capture keep it. Microsoft's Programmatic Identifiers page "
                 "says 'The Shell uses a programmatic identifier (ProgID) registry subkey to associate a file type "
                 "with an application' "
                 "(https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/shell/fa-progids.md?plain=1#L11). "
                 "Key Last Written (UTC) is the last written time of the UserChoice or UserChoiceLatest key itself. "
                 "Registry Key is that key's path in the hive: the parent path as written above, then the subkey and "
                 "key names as the hive stores them (the 5 szechuan_win10 hives spell the first part SOFTWARE). User "
                 "is the folder after Users in the hive's path. Eric Zimmerman's FileExts registry plugin says it "
                 "processes the subkeys of FileExts and 'displays associated executables, program IDs and user "
                 "choice for each extension found', and takes the ProgId value of UserChoice as that choice "
                 "(https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.FileExts/FileExts.cs#L40-L41, "
                 "https://github.com/EricZimmerman/RegistryPlugins/blob/c16219db698f7ee66fbd97de7ec5d17fc10bdf8e/RegistryPlugin.FileExts/FileExts.cs#L115-L120), "
                 "and RECmd's DFIR batch file lists the key as 'File Extensions', 'Tracks programs associated with "
                 "file extensions' (Andrew Rathbun, 'DFIR RECmd Batch File', "
                 "https://github.com/EricZimmerman/RECmd/blob/bcd0ac33ed98de61ea6de551eef96052bddbbd49/BatchExamples/DFIRBatch.reb#L4052-L4065). "
                 "No Microsoft documentation of these keys was found. Mozilla's Firefox source generates and checks "
                 "the UserChoice hash: its check joins the association, the user's SID, the program ID, the "
                 "UserChoice key's last write time with its seconds and milliseconds set to zero and a fixed text, "
                 "puts the result in lower case, and encodes a 64-bit value derived from it as base64; its comment "
                 "says the format was 'used at least since 1803' "
                 "(https://github.com/mozilla-firefox/firefox/blob/4578f07ce13c6db83454d7bd2b7583fe3d132bc0/browser/components/shell/WindowsUserChoice.cpp#L74-L129, "
                 "https://github.com/mozilla-firefox/firefox/blob/4578f07ce13c6db83454d7bd2b7583fe3d132bc0/browser/components/shell/WindowsUserChoice.cpp#L195-L264, "
                 "https://github.com/mozilla-firefox/firefox/blob/4578f07ce13c6db83454d7bd2b7583fe3d132bc0/browser/components/shell/WindowsUserChoice.cpp#L331-L350). "
                 "Computed that way from each row's Association, the user's SID (through the User Profile List "
                 "artifact), Program ID and Key Last Written (UTC), the result equals Hash on all 919 tested "
                 "UserChoice rows that have one, and a time one minute later gives another hash on all 919. It "
                 "equals Hash on none of the 158 UserChoiceLatest rows; how their hash is made is not sourced. This "
                 "artifact does not compute the hash. The Microsoft-Windows-Shell-Core manifest of Windows 11 build "
                 "26100.1742 has an event, 62440, whose message begins 'Hash mismatch detected for: %1. ProgId: %2. "
                 "UserSid: %3. HashInRegistry: %4. ComputedHash: %5.' "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-Shell-Core.xml#L37447-L37470). "
                 "Tested on four public images (af_case2_win10, build 17763; lonewolf_win10, build 16299; "
                 "pc_mus_001_win11, build 22621; szechuan_win10, build 19041), which gave 93, 93, 133 and 444 rows "
                 "in that order, and on one capture of a Windows 11 build 26200 machine "
                 "(windows11_arm_known_20261001), which gave 315; the other capture holds no NTUSER.DAT. Each public "
                 "image also holds one hive with no such key, in the Users folder named Default. User held one value "
                 "on af_case2_win10, lonewolf_win10, pc_mus_001_win11 and the capture, each with one hive that has "
                 "rows; szechuan_win10 has rows for 4 users. On the 1,078 rows Program ID is AppX followed by lower "
                 "case letters and digits on 915 and another name on 163; Hash is 12 characters of base64 that "
                 "decode to 8 bytes on 1,077 and blank on 1, a lonewolf_win10 key whose only value is named Progid. "
                 "Only the capture has UserChoiceLatest keys: 158, beside 157 UserChoice keys. Each of the 157 "
                 "associations with both keys has the same Program ID in both and a different Hash, and its "
                 "UserChoiceLatest key was written later, never in the same minute; 1 association has "
                 "UserChoiceLatest only. What sets the two keys apart is not established. The public images' rows "
                 "agree with Default App Events. Of their 763 rows, 684 have a SetDefault-Info row there for the "
                 "same account and association, and on every one the last such row names the same program ID, its H "
                 "equals Hash and its T is the minute of Key Last Written (UTC). Of the 79 without one, 77 are "
                 "pc_mus_001_win11 keys written before that image's first Default App Events record, 1 is a "
                 "pc_mus_001_win11 key written after it and 1 is the lonewolf_win10 key with no Hash. A key does not "
                 "record what made the choice: 1,066 of the 1,078 rows were written in a minute in which the same "
                 "user's hive had 20 or more of these keys written. Rows follow the hives in the order the tool "
                 "found them, FileExts before UrlAssociations within a hive, in the order the hive lists the keys. A "
                 "hive that cannot be read is named in the run log and skipped; every tested hive was read. Reading "
                 "the hive needs the python-registry package. A dirty hive, one whose base block's two sequence "
                 "numbers differ, is read after the entries in its .LOG1 and .LOG2 transaction logs that continue "
                 "its sequence are applied, following Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason. 3 tested hives were replayed, one each on "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10. Not read: the OpenWithList and "
                 "OpenWithProgids subkeys the same FileExts keys hold (1,253 and 972 in the tested hives), "
                 "UsrClass.dat, and the SOFTWARE hive. The tested hives hold no key whose name begins UserChoice "
                 "anywhere else.",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 93 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 93 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 133 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 444 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 315 rows",
        },
        "paths": ('*/Users/*/NTUSER.DAT',
                  '*/Users/*/[Nn][Tt][Uu][Ss][Ee][Rr].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "settings",
    },
}


def _texts(key):
    """A key's text values, by value name in lower case."""
    found = {}
    for value in key.values():
        data = value.value()
        if isinstance(data, str):
            found[value.name().lower()] = data
    return found


def choice_rows(parent, parent_path, user):
    """One row per UserChoice or UserChoiceLatest key under the subkeys of a FileExts or UrlAssociations key.

    The program ID is the key's ProgId value, or the ProgId value of its ProgId subkey when the key has none.
    """
    rows = []
    for association in parent.subkeys():
        for choice in association.subkeys():
            if choice.name().lower() not in _CHOICES:
                continue
            stored = _texts(choice)
            program = stored.get('progid')
            if program is None:
                for sub in choice.subkeys():
                    if sub.name().lower() == 'progid':
                        program = _texts(sub).get('progid')
            rows.append((key_written_utc(choice), user, association.name(), program or '', stored.get('hash', ''),
                         f'{parent_path}\\{association.name()}\\{choice.name()}'))
    return rows


@artifact_processor
def defaultAppUserChoices(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Association', 'Program ID', 'Hash',
                    'Registry Key')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''
    for source in found_hives(context, 'NTUSER.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            rows = []
            for parent_path in _PARENTS:
                parent = open_key(reg, parent_path)
                if parent is not None:
                    rows.extend(choice_rows(parent, parent_path, user_from_path(relative_source)))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        data_list.extend(rows)
    return data_headers, data_list, '\n'.join(sources)
