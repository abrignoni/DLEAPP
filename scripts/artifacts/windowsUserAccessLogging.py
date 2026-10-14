"""The system identity snapshots in User Access Logging's SystemIdentity.mdb, for DLEAPP.

Author: @AlexisBrignoni, Claude.

SystemIdentity.mdb is an ESE database and is read with scripts/ese_rows over the vendored ESE reader. Its
SYSTEM_IDENTITY table holds one record per snapshot. CreationTime is read as a FILETIME, as plaso's User Access
Logging parser reads it (plaso/parsers/esedb_plugins/user_access_logging.py, github.com/log2timeline/plaso at
commit 2320e8dc947fc9ec1d8ceebc884a3c8c35479177). OSLastBootUpTime is a CIM DATETIME string,
yyyymmddHHMMSS.mmmmmmsUUU, a time and the minutes its zone deviates from UTC (MicrosoftDocs/win32,
desktop-src/WmiSdk/cim-datetime.md at commit 497e7a7dd17a495a277c4a7afa54aca9eb902782).
"""

__artifacts_v2__ = {
    "windowsUserAccessLoggingSystemIdentity": {
        "name": "User Access Logging - System Identity",
        "description": "The system identity snapshots that Windows Server's User Access Logging keeps in "
                       "Windows/System32/LogFiles/Sum/SystemIdentity.mdb: host name, domain, product type, "
                       "operating system version, last boot time and hardware, one row per snapshot.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-14",
        "last_update_date": "2026-10-14",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the SYSTEM_IDENTITY table of Windows/System32/LogFiles/Sum/SystemIdentity.mdb, an ESE '
                 'database, and reports one row per record, ordered by Snapshot Created. Microsoft describes User '
                 'Access Logging as a Windows Server feature, installed and enabled by default, that aggregates '
                 'client usage data by role and product (Reference: "Get Started with User Access Logging", '
                 'Microsoft Learn, '
                 'https://github.com/MicrosoftDocs/windowsserverdocs/blob/7c489ebf866ebbd7074f453d436ed8c65f4bb9bd/WindowsServerDocs/administration/user-access-logging/get-started-with-user-access-logging.md).'
                 " Snapshot Created is the record's CreationTime, a column typed JET_coltypDateTime whose eight "
                 "bytes the vendored ESE reader returns as an unsigned integer, read as a FILETIME, as plaso's "
                 'User Access Logging parser reads it (Reference: plaso, '
                 "'plaso/parsers/esedb_plugins/user_access_logging.py', "
                 'https://github.com/log2timeline/plaso/blob/2320e8dc947fc9ec1d8ceebc884a3c8c35479177/plaso/parsers/esedb_plugins/user_access_logging.py).'
                 ' OS Last Boot (as stored) is OSLastBootUpTime as the database holds it, a CIM DATETIME string, a'
                 ' local time followed by the minutes its zone deviates from UTC (Reference: "CIM_DATETIME", '
                 'MicrosoftDocs/win32, '
                 'https://github.com/MicrosoftDocs/win32/blob/497e7a7dd17a495a277c4a7afa54aca9eb902782/desktop-src/WmiSdk/cim-datetime.md),'
                 ' and OS Last Boot is that time moved to UTC by its own offset; a string in another shape leaves '
                 'OS Last Boot blank. Time Zone Offset (Minutes) is OSCurrentTimeZone, stored in an unsigned '
                 "16-bit column, read as a signed 16-bit number of minutes, the type of Win32_OperatingSystem's "
                 'CurrentTimeZone, and Product Type is OSProductType with the name Win32_OperatingSystem gives the'
                 ' same number for ProductType: 1 Work Station, 2 Domain Controller, 3 Server (Reference: '
                 '"Win32_OperatingSystem class", MicrosoftDocs/win32, '
                 'https://github.com/MicrosoftDocs/win32/blob/3f42ac423191be263920ddf69b1ae6c2975c81b0/desktop-src/CIMWin32Prov/win32-operatingsystem.md).'
                 ' Those two readings rest on the column names matching the WMI properties; no Microsoft source '
                 "was found that documents this table's columns. OS Version joins OSMajor, OSMinor and "
                 'OSBuildNumber, and Service Pack joins ServicePackMajor and ServicePackMinor. The other columns '
                 'are reported as stored, with the NULs that pad the strings and any surrounding whitespace '
                 'removed: OS Serial Number (OSSerialNumber), System Manufacturer, System Product Name, SMBIOS '
                 'UUID (SystemSMBIOSUUID), System Serial Number, Physical Processors, Cores per Processor, Logical'
                 ' Processors per Processor, Maximum Memory and OS Country Code. Not reported: OSPlatformId, '
                 'OSSuiteMask and OSDaylightInEffect, whose meaning in this table is not established. Validated on'
                 ' szechuan_dc01_server2012r2, the Szechuan Sauce case domain controller (Windows Server 2012 R2, '
                 'build 9600): 3 rows from a database whose header records a clean shutdown (state 3, '
                 "JET_dbstateCleanShutdown, in ESE's published header, Reference: Extensible-Storage-Engine, "
                 "'dev/ese/published/inc/jethdr.w', "
                 'https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/published/inc/jethdr.w#L5406-L5408).'
                 ' Host Name took two values and Domain two values across the rows, and Product Type went from 3 '
                 '(Server) on the first row to 2 (Domain Controller) on the second and third. OS Version, Service '
                 'Pack, OS Serial Number, System Manufacturer, System Product Name, SMBIOS UUID, System Serial '
                 'Number, Physical Processors, Cores per Processor, Logical Processors per Processor, Maximum '
                 'Memory, OS Country Code and Time Zone Offset (Minutes) each held one value on all 3 rows. OS '
                 "Last Boot was compared with the image's System event log: on each row it equals the StartTime of"
                 ' a Microsoft-Windows-Kernel-General event 12 to within one microsecond, and the time zone offset'
                 " inside the string equals Time Zone Offset (Minutes) on every row. Each row's Snapshot Created "
                 "fell between two and four minutes after an event 12 start, and each row's OS Last Boot was a "
                 "later start than that one, so on szechuan_dc01_server2012r2 a row's OS Last Boot is later than "
                 'its Snapshot Created and the two do not describe the same boot. Also validated on '
                 "ou_ransomware_server2022, the Open University's simulated compromised server (Windows Server "
                 '2022 Standard, build 20348): 5 rows, and on each the time zone offset inside OS Last Boot (as '
                 'stored) equals Time Zone Offset (Minutes), which took three values. Host Name held one value on '
                 'all 5 rows and Domain two; Cores per Processor and Logical Processors per Processor were '
                 'identical on all 5 rows, each taking two values. There OS Last Boot equals the StartTime of an '
                 'event 12 exactly on 3 rows. On one row it is later than the nearest event 12 StartTime by '
                 '3,594.640575 seconds, and the System log records the clock being moved forward by 3,594.640576 '
                 'seconds after that start (Microsoft-Windows-Kernel-General event 1), so OS Last Boot can move '
                 'with a clock change made after the boot. On the other row it is earlier than the first event 12 '
                 'in the log. The same log records the clock being set back by more than seven hours on the day of'
                 ' the first three rows, and Snapshot Created does not put the row with Product Type 3 (Server) '
                 'before the rows with 2 (Domain Controller), the order seen on szechuan_dc01_server2012r2: it has'
                 ' a later Snapshot Created than two of them. On ou_ransomware_server2022 Snapshot Created is not '
                 'a reliable order of the records. How User Access Logging decides to start a new record is not '
                 'established. Snapshot Created was not compared with a second source. Not read: the client access'
                 " records, which Patrick Bennett's research places in the CLIENTS table of Current.mdb and of the"
                 " per-year {GUID}.mdb databases that SystemIdentity.mdb's CHAINED_DATABASES table names "
                 '(Reference: "UAL Thank Us Later: Leveraging User Access Logging for Forensic Investigations", '
                 'CrowdStrike, 8 June 2021, '
                 'https://www.crowdstrike.com/en-us/blog/user-access-logging-ual-overview/); on '
                 "szechuan_dc01_server2012r2 Current.mdb's header records a dirty shutdown (state 2, "
                 'JET_dbstateDirtyShutdown) and, read without replaying the ESE transaction logs beside it '
                 '(Svc.log), which this artifact does not do, its CLIENTS, DNS, ROLE_ACCESS and VIRTUALMACHINES '
                 "tables held no records; the per-year database named for 2020 is not among the image's live "
                 "files. SystemIdentity.mdb's ROLE_IDS table is not reported: on szechuan_dc01_server2012r2 its 13"
                 " rows each name a role; 11 match an entry on Microsoft's list of the roles User Access Logging "
                 'can support by name, and two (File Server, Remote Access) resemble entries on it (File Services;'
                 ' Routing and Remote Access Service); whether a row records a role installed on the server is not'
                 " established. The corpus's other Windows disk images, pc_mus_001_win11, af_case2_win10, "
                 'lonewolf_win10, szechuan_win10 and cfreds_leakage_win7, all client editions, hold no '
                 'SystemIdentity.mdb.',
        "paths": ('*/Windows/System32/LogFiles/Sum/SystemIdentity.mdb',),
        "output_types": "standard",
        "artifact_icon": "server",
        "sample_data": {
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 3 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 5 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no SystemIdentity.mdb)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no SystemIdentity.mdb)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no SystemIdentity.mdb)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no SystemIdentity.mdb)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no SystemIdentity.mdb)",
        },
    },
}

import os
import re
from datetime import datetime, timedelta, timezone

try:
    from scripts import ese_rows
except ImportError:
    ese_rows = None

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_ntfs import filetime

_LABEL = 'User Access Logging - System Identity'
_TABLE = 'SYSTEM_IDENTITY'
# yyyymmddHHMMSS.mmmmmmsUUU (cim-datetime.md)
_CIM_DATETIME = re.compile(r'(\d{14})\.(\d{6})([+-])(\d{3})$')
# Win32_OperatingSystem ProductType (MicrosoftDocs/win32, desktop-src/CIMWin32Prov/win32-operatingsystem.md
# at commit 3f42ac423191be263920ddf69b1ae6c2975c81b0)
_PRODUCT_TYPES = {1: 'Work Station', 2: 'Domain Controller', 3: 'Server'}


def text(value):
    """A stored string with the NULs that pad it removed; '' for a missing value."""
    if value is None:
        return ''
    if isinstance(value, (bytes, bytearray)):
        value = value.decode('utf-8', 'replace')
    return str(value).split('\0', 1)[0].strip()


def cim_datetime_utc(value):
    """A CIM DATETIME string as an aware UTC datetime, or '' when it is not one or has no zone offset."""
    match = _CIM_DATETIME.match(value)
    if not match:
        return ''
    stamp, micro, sign, minutes = match.groups()
    try:
        local = datetime.strptime(stamp, '%Y%m%d%H%M%S').replace(microsecond=int(micro))
    except ValueError:
        return ''
    offset = int(minutes) if sign == '+' else -int(minutes)
    return (local - timedelta(minutes=offset)).replace(tzinfo=timezone.utc)


def signed_minutes(value):
    """OSCurrentTimeZone, stored as the unsigned 16-bit form of Win32_OperatingSystem's sint16 CurrentTimeZone,
    as signed minutes; '' for a missing value."""
    if value is None:
        return ''
    return value - 0x10000 if value >= 0x8000 else value


def product_type(value):
    if value is None:
        return ''
    name = _PRODUCT_TYPES.get(value)
    return f'{value} ({name})' if name else str(value)


def number(value):
    return '' if value is None else value


def _version(row):
    parts = [row.get(name) for name in ('OSMajor', 'OSMinor', 'OSBuildNumber')]
    return '.'.join(str(part) for part in parts) if all(part is not None for part in parts) else ''


def _service_pack(row):
    major, minor = row.get('ServicePackMajor'), row.get('ServicePackMinor')
    return '' if major is None or minor is None else f'{major}.{minor}'


def identity_row(row):
    """One report row for a SYSTEM_IDENTITY record, given as a dict of column name to value."""
    boot = text(row.get('OSLastBootUpTime'))
    created = row.get('CreationTime')
    return (filetime(created) if isinstance(created, int) else '',
            cim_datetime_utc(boot),
            boot,
            signed_minutes(row.get('OSCurrentTimeZone')),
            text(row.get('SystemDNSHostName')),
            text(row.get('SystemDomainName')),
            product_type(row.get('OSProductType')),
            _version(row),
            _service_pack(row),
            text(row.get('OSSerialNumber')),
            text(row.get('SystemManufacturer')),
            text(row.get('SystemProductName')),
            text(row.get('SystemSMBIOSUUID')),
            text(row.get('SystemSerialNumber')),
            number(row.get('PhysicalProcessorCount')),
            number(row.get('CoresPerPhysicalProcessor')),
            number(row.get('LogicalProcessorsPerPhysicalProcessor')),
            number(row.get('MaximumMemory')),
            text(row.get('OSCountryCode')))


def _named(record):
    return {(key.decode('latin-1') if isinstance(key, (bytes, bytearray)) else key): value
            for key, value in record.items()}


def _read(path, relative):
    database = ese_rows.ESEDatabase(path)
    try:
        database.mountDB()
        walk = ese_rows.TableRows(database, _TABLE)
        rows = [identity_row(_named(record)) for record in walk]
        if not walk.found:
            logfunc(f'{_LABEL}: {relative} has no {_TABLE} table')
        elif walk.summary():
            logfunc(f'{_LABEL}: {relative}, {walk.summary()}')
        return rows
    finally:
        database.close()


@artifact_processor
def windowsUserAccessLoggingSystemIdentity(context):
    data_headers = (('Snapshot Created', 'datetime'), ('OS Last Boot', 'datetime'), 'OS Last Boot (as stored)',
                    'Time Zone Offset (Minutes)', 'Host Name', 'Domain', 'Product Type', 'OS Version',
                    'Service Pack', 'OS Serial Number', 'System Manufacturer', 'System Product Name',
                    'SMBIOS UUID', 'System Serial Number', 'Physical Processors', 'Cores per Processor',
                    'Logical Processors per Processor', 'Maximum Memory', 'OS Country Code')
    data_list, read = [], []
    if ese_rows is None:
        logfunc(f'{_LABEL}: the vendored ESE reader is not available')
        return data_headers, data_list, ''
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isdir(path) or os.path.basename(path).lower() != 'systemidentity.mdb':
            continue
        relative = context.get_relative_path(path)
        try:
            rows = _read(path, relative)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read {relative}: {type(exc).__name__}: {exc}')
            continue
        data_list.extend(sorted(rows, key=lambda row: (str(row[0]), row[2])))
        read.append(path)
    return data_headers, data_list, '\n'.join(read)
