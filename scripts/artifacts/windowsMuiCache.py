"""Windows MUICache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the MuiCache key of each user's UsrClass.dat, Local Settings\\Software\\
Microsoft\\Windows\\Shell\\MuiCache. Its values are named for a file path
followed by .FriendlyAppName or .ApplicationCompany and hold that file's
friendly name and company as text. Each path is one row: the user, the path,
the two texts and the key's last written time. Sources and measurements are in
the notes.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, found_hives, key_written_utc, open_hive,
                                      open_key, user_from_path)

_LABEL = 'MUICache'
_MUICACHE = r"Local Settings\Software\Microsoft\Windows\Shell\MuiCache"
# value name suffix -> position of its text in the row's (friendly name, company) pair
_SUFFIXES = (('.friendlyappname', 0), ('.applicationcompany', 1))

__artifacts_v2__ = {
    "muiCache": {
        "name": "MUICache",
        "description": "Files named in the MuiCache key of each user's UsrClass.dat, with the friendly name and "
                       "company text stored for each, the user and the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from each user's UsrClass.dat, named in the report's located-at line. The values of Local "
                 "Settings\\Software\\Microsoft\\Windows\\Shell\\MuiCache are named for a file path followed by "
                 ".FriendlyAppName or .ApplicationCompany, and each path is one row. Program is the path, as stored; "
                 "Friendly App Name and Company are the text of its two values, blank when the key has no such value "
                 "for the path. The suffix is matched without case, and two spellings of one path are two rows. User "
                 "is the folder after Users in the hive's path. Key Last Written (UTC) is the last-written time of "
                 "the MuiCache key, so every row of one hive shares it and no row has a time of its own. A value "
                 "named for neither suffix is not reported and is counted in the run log; on the tested hives that "
                 "is one value per key, LangID. RECmd's DFIR batch file reads the same key, under Program Execution, "
                 "with the comment 'Displays new applications that have been executed within Windows' (Andrew "
                 "Rathbun, 'DFIR RECmd Batch File', "
                 "https://github.com/EricZimmerman/RECmd/blob/bcd0ac33ed98de61ea6de551eef96052bddbbd49/BatchExamples/DFIRBatch.reb#L1950-L1956). "
                 "Microsoft's application registration page says the association query for an application's friendly "
                 "name reads the FriendlyAppName registry entry, falls back to the FileDescription name in the "
                 "version information and, if that is missing, to the display name of the file (Microsoft, "
                 "'Application Registration', "
                 "https://github.com/MicrosoftDocs/win32/blob/e103fa4e8810bd8d42c4777e17081e24dbe62dbd/desktop-src/shell/app-registration.md#L114). "
                 "The stored text fits that. The tested hives give 13, 19, 41 and 24 rows on af_case2_win10, "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10, from 1, 1, 1 and 4 user hives. Each of the 97 "
                 "paths begins with a drive letter; 76 end in .exe and 21 in .dll, and 53 of the 76 .exe paths have "
                 "a Prefetch row for the same executable name (see Prefetch). The images hold a file at 83 of the 97 "
                 "paths, 81 of them with version strings, read here with pefile. Friendly App Name equals the file's "
                 "FileDescription on 69 of the 81. On 7 the FileDescription is empty and the stored text is the "
                 "file's name, without its extension on 6 and with it on 1. On the other 5 it is another name: Word "
                 "2016, Excel 2016, WordPad twice and Windows Media Player Legacy. Company equals the file's "
                 "CompanyName on 80 of the 81 and is blank on the one whose file has no CompanyName. The other 14 "
                 "paths, 8 on drive C and 6 on drive D, name a file the image does not hold. Company is blank on 4 "
                 "rows of pc_mus_001_win11, where the key has no ApplicationCompany value for the path, and Friendly "
                 "App Name is filled on every row. On 4 of the 7 hives Key Last Written (UTC) is within 1 second of "
                 "a Prefetch run time of a .exe the key names; on the other 3 the nearest is 96 to 649 seconds away. "
                 "Key Last Written (UTC) and User held one value on every row of af_case2_win10, lonewolf_win10 and "
                 "pc_mus_001_win11, where one user hive holds the key, and Company held one value on every row of "
                 "af_case2_win10. A row records that the key of that user's hive holds text for the path; it does "
                 "not by itself show that the user ran the file, or when. Reading the hive needs the python-registry "
                 "package. A dirty hive, one whose base block's two sequence numbers differ, is read after the "
                 "entries in its .LOG1 and .LOG2 transaction logs that continue its sequence are applied, following "
                 "Maxim Suhanov's 'Windows registry file format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/AppData/Local/Microsoft/Windows/[Uu]sr[Cc]lass.[Dd]at',
                  '*/AppData/Local/Microsoft/Windows/[Uu][Ss][Rr][Cc][Ll][Aa][Ss][Ss].[Dd][Aa][Tt].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "tag",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 41 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 13 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 19 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 24 rows",
        },
    },
}


def _text(value):
    """A value's data as text: a string as stored, anything else through str(), '' for none."""
    data = value.value()
    if isinstance(data, str):
        return data
    return '' if data is None else str(data)


def mui_rows(key, user):
    """(rows, skipped) for a MuiCache key.

    One row per path, in the order the key first names it; a value whose name ends in
    neither suffix (compared without case) is counted in skipped and not reported.
    """
    written = key_written_utc(key)
    programs = {}
    skipped = 0
    for value in key.values():
        name = value.name()
        for suffix, slot in _SUFFIXES:
            if name.lower().endswith(suffix) and len(name) > len(suffix):
                programs.setdefault(name[:-len(suffix)], ['', ''])[slot] = _text(value)
                break
        else:
            skipped += 1
    rows = [(written, user, program, friendly, company)
            for program, (friendly, company) in programs.items()]
    return rows, skipped


@artifact_processor
def muiCache(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'User', 'Program', 'Friendly App Name',
                    'Company')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in found_hives(context, 'USRCLASS.DAT'):
        relative_source = context.get_relative_path(source)
        try:
            key = open_key(open_hive(source, context), _MUICACHE)
            rows, skipped = ([], 0) if key is None else mui_rows(key, user_from_path(relative_source))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        if skipped:
            logfunc(f'{_LABEL}: {skipped} value(s) of {relative_source} are not named for a '
                    f'friendly name or a company and are not reported')
        data_list.extend(rows)

    return data_headers, data_list, '\n'.join(sources)
