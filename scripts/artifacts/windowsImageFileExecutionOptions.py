"""Windows Image File Execution Options and SilentProcessExit parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads two keys of the SOFTWARE hive under Microsoft\\Windows NT\\CurrentVersion:
Image File Execution Options, where a subkey named for a program can hold a
Debugger and a GlobalFlag value, and SilentProcessExit, where a subkey named for
a program holds the settings for monitoring its silent exit. Each reported value
is one row, with the last written time of the key that holds it. The values
were measured on known data made on a Windows 11 lab machine; sources are in
the notes.
"""

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import Registry, found_hives, key_written_utc, open_hive, open_key

_LABEL = 'Image File Execution Options'
_NT = r"Microsoft\Windows NT\CurrentVersion"
# Key paths under the SOFTWARE hive root. No tested hive holds the WOW6432Node ones.
_IFEO_KEYS = (_NT + r"\Image File Execution Options",
              "WOW6432Node\\" + _NT + r"\Image File Execution Options")
_SILENT_EXIT_KEYS = (_NT + r"\SilentProcessExit",
                     "WOW6432Node\\" + _NT + r"\SilentProcessExit")
# The Image File Execution Options values reported; a program's other values are not.
_IFEO_VALUES = ('debugger', 'globalflag')

__artifacts_v2__ = {
    "imageFileExecutionOptions": {
        "name": "Image File Execution Options",
        "description": "Debugger and GlobalFlag values under the Image File Execution Options key and the values "
                       "under the SilentProcessExit key of the SOFTWARE hive, with the image name each is stored "
                       "under and the last written time of the key holding it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-01",
        "last_update_date": "2026-10-01",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SOFTWARE hive, named in the report's located-at line. Two keys under "
                 "Microsoft\\Windows NT\\CurrentVersion are read: Image File Execution Options and SilentProcessExit. "
                 "Microsoft's GFlags documentation gives Image File Execution Options\\ImageFileName\\Debugger as "
                 "where the debugger for an image file is stored and Image File Execution "
                 "Options\\ImageFileName\\GlobalFlag as where program-specific settings are stored (Microsoft, 'GFlags "
                 "Details', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/debugger/gflags-details.md#L54, "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/debugger/gflags-details.md#L62), "
                 "and gives SilentProcessExit as where the global settings for silent exit monitoring are stored and "
                 "SilentProcessExit\\ProcessName as where a program's are (Microsoft, 'Monitoring Silent Process "
                 "Exit', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/debugger/registry-entries-for-silent-process-exit.md#L34-L40). "
                 "MITRE ATT&CK describes the use of both keys for persistence as T1546.012, Image File Execution "
                 "Options Injection "
                 "(https://attack.mitre.org/techniques/T1546/012/). "
                 "Each row is one value. From Image File Execution Options only the Debugger and GlobalFlag values "
                 "are reported, matched by name without case, from each subkey of the key and from the subkeys "
                 "directly below it; a subkey's other values, such as MitigationOptions, are not reported. From "
                 "SilentProcessExit every value of the key and of each of its subkeys is reported. Image is the name "
                 "of the subkey of either key that the value is in or under, which those pages give as an image file "
                 "or process name; it is blank for a value of the SilentProcessExit key itself. Value Name is the "
                 "value's name as stored. Value Data is the value's data: text as stored, and a number written in "
                 "hexadecimal; binary data is written as hexadecimal digits and a list of strings joined by commas, "
                 "and no reported value of the tested hives holds either. Filter Path is the FilterFullPath value of "
                 "the key holding the value, for a value in a subkey below an image's. Registry Key is the path, "
                 "under the hive root, of the key holding the value, and Key Last Written (UTC) is that key's "
                 "last-written time, so every value of one key shares it. On windows11_arm_known_20261001, known "
                 "data made on a Windows 11 build 26200 ARM64 virtual machine on 1 October 2026, five made-up values "
                 "were added with reg.exe, the hive was saved and the values were then removed, and the 5 rows are "
                 "those values: Debugger and GlobalFlag for one made-up image name, Debugger for a second, and "
                 "ReportingMode and MonitorProcess under SilentProcessExit for the first. The Debugger and "
                 "MonitorProcess rows hold the commands written. GlobalFlag, written as the number 512, reads 0x200, "
                 "which Microsoft gives as the flag that enables silent process exit monitoring (Microsoft, 'Enable "
                 "Silent Process Exit Monitoring', "
                 "https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/debugger/enable-silent-process-exit-monitoring.md#L14-L28). "
                 "ReportingMode, written as the number 1, reads 0x1, which Microsoft describes as launching the "
                 "monitor process when a silent exit is detected "
                 "(https://github.com/MicrosoftDocs/windows-driver-docs/blob/6de78e042e0eaba466569c7f5ed65c250c644a0b/windows-driver-docs-pr/debugger/registry-entries-for-silent-process-exit.md#L49-L53). "
                 "Each row's Key Last Written (UTC) is 11 to 18 ms after the time logged just before the last "
                 "command that wrote to its key started and no more than 1 ms after the time logged when that "
                 "command returned. The second image name was added under the WOW6432Node path of Image File "
                 "Execution Options and is in the same key as the first: none of the five tested hives holds an "
                 "Image File Execution Options or a SilentProcessExit key under WOW6432Node, so those two paths, "
                 "which are read when present, were not exercised. Velociraptor's Windows.Persistence.Debug artifact "
                 "describes the WOW6432Node key as kept inline with the other (Velociraptor, "
                 "'Windows.Persistence.Debug', "
                 "https://github.com/Velocidex/velociraptor/blob/74d2e0a9442f93f2ddedeca16436e7499209bcb6/artifacts/definitions/Windows/Persistence/Debug.yaml#L12-L15). "
                 "Microsoft lists Image File Execution Options as shared by 32-bit and 64-bit applications on "
                 "Windows 7, Windows Server 2008 R2 and newer and as redirected on Windows Vista, Windows Server "
                 "2008 and earlier (Microsoft, 'Registry Keys Affected by WOW64', as updated 23 October 2025, "
                 "https://learn.microsoft.com/en-us/windows/win32/winprog64/shared-registry-keys); "
                 "the WOW6432Node paths are read for that reason, and no hive from those earlier versions was "
                 "tested. No program of either made-up name was started in the session, so whether Windows acts on "
                 "these values was not tested. Image File Execution Options holds 21, 49, 25 and 21 subkeys on "
                 "af_case2_win10, lonewolf_win10, pc_mus_001_win11 and szechuan_win10 and 48 on the capture; apart "
                 "from the two made-up ones, none holds a Debugger or GlobalFlag value, and none of the four images "
                 "has a SilentProcessExit key, so those four give no rows. Subkeys below an image's are present on "
                 "pc_mus_001_win11 (3) and on the capture (4), all under notepad.exe, each with a FilterFullPath "
                 "value and no Debugger or GlobalFlag value; Filter Path is therefore blank on every row, and a "
                 "value in such a subkey was not exercised on real data. A row records a value the hive holds; it "
                 "does not show that the program ran, that a debugger or a monitor process was started, or who wrote "
                 "the value. Reading the hive needs the python-registry package. A dirty hive, one whose base "
                 "block's two sequence numbers differ, is read after the entries in its .LOG1 and .LOG2 transaction "
                 "logs that continue its sequence are applied, following Maxim Suhanov's 'Windows registry file "
                 "format specification' "
                 "(https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L679-L728, "
                 "https://github.com/msuhanov/regf/blob/88e878de51bae393143b0ac8daae6c2dfc256bf7/Windows%20registry%20file%20format%20specification.md#L746-L749). "
                 "Logs in the older format used before Windows 8.1 are not applied, and neither is a replay that "
                 "would give a key an earlier last-written time than the hive already holds, a check added here "
                 "beyond the specification; the run log names each hive replayed, with the sequence numbers applied, "
                 "and each dirty hive read as it is, with the reason.",
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "crosshair",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 5 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
}


def data_text(value):
    """A value's data for the report: text as stored, a number in hexadecimal."""
    data = value.value()
    if isinstance(data, str):
        return data
    if isinstance(data, bool):
        return str(data)
    if isinstance(data, int):
        return hex(data)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data).hex()
    if isinstance(data, (list, tuple)):
        return ', '.join(str(item) for item in data)
    return str(data)


def _stored_text(key, name):
    for value in key.values():
        if value.name().lower() == name.lower():
            return data_text(value)
    return ''


def ifeo_rows(key, key_path):
    """Rows for the Debugger and GlobalFlag values of each program subkey and of its subkeys."""
    for program in key.subkeys():
        program_path = f'{key_path}\\{program.name()}'
        for holder, holder_path, filter_path in (
                [(program, program_path, '')]
                + [(nested, f'{program_path}\\{nested.name()}', _stored_text(nested, 'FilterFullPath'))
                   for nested in program.subkeys()]):
            for value in holder.values():
                if value.name().lower() in _IFEO_VALUES:
                    yield (key_written_utc(holder), program.name(), value.name(), data_text(value),
                           filter_path, holder_path)


def silent_exit_rows(key, key_path):
    """Rows for every value of the SilentProcessExit key and of each program subkey."""
    for value in key.values():
        yield (key_written_utc(key), '', value.name(), data_text(value), '', key_path)
    for program in key.subkeys():
        for value in program.values():
            yield (key_written_utc(program), program.name(), value.name(), data_text(value), '',
                   f'{key_path}\\{program.name()}')


@artifact_processor
def imageFileExecutionOptions(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Image', 'Value Name', 'Value Data',
                    'Filter Path', 'Registry Key')
    data_list = []
    sources = []
    if Registry is None:
        logfunc(f'{_LABEL}: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in found_hives(context, 'SOFTWARE'):
        relative_source = context.get_relative_path(source)
        try:
            reg = open_hive(source, context)
            rows = []
            present = []
            for paths, rows_of in ((_IFEO_KEYS, ifeo_rows), (_SILENT_EXIT_KEYS, silent_exit_rows)):
                for key_path in paths:
                    key = open_key(reg, key_path)
                    if key is None:
                        continue
                    present.append(key_path)
                    rows.extend(rows_of(key, key_path))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative_source}: {exc}')
            continue
        sources.append(source)
        logfunc(f'{_LABEL}: {len(rows)} value(s) reported from {relative_source}; keys present: '
                f'{", ".join(present) if present else "none"}')
        data_list.extend(rows)

    return data_headers, data_list, '\n'.join(sources)
