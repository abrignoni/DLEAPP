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
                 'lonewolf_win10, szechuan_win10, cfreds_leakage_win7 and alihadi_challenge3_win81, all client '
                 'editions, hold no SystemIdentity.mdb.',
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
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no SystemIdentity.mdb)",
        },
    },
    "windowsUserAccessLoggingClients": {
        "name": "User Access Logging - Client Access",
        "description": "Client access records from Windows Server's User Access Logging databases (Current.mdb and "
                       "the per-year {GUID}.mdb files in Windows/System32/LogFiles/Sum): role, user name and client "
                       "address, with the record's insert and last access times and its access counts per day.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-14",
        "last_update_date": "2026-10-14",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the CLIENTS table of Current.mdb and of each {GUID}.mdb in Windows/System32/LogFiles/Sum, '
                 'and the ROLE_IDS table of the SystemIdentity.mdb in the same folder to name each role. A record '
                 "found with the same values in several of the folder's databases is one row, and Databases names "
                 'each database it was found in; a record that differs in any value is a row of its own. Patrick '
                 'Bennett\'s research describes the table (Reference: "UAL Thank Us Later: Leveraging User Access '
                 'Logging for Forensic Investigations", CrowdStrike, 8 June 2021, '
                 'https://www.crowdstrike.com/en-us/blog/user-access-logging-ual-overview/): CLIENTS holds records'
                 " of users accessing the server's roles, one per RoleGuid, AuthenticatedUserName and Address for "
                 'the year; InsertDate is the first access of the year, LastAccess the most recent, TotalAccesses '
                 'the count for the year, and Day1 to Day366 a count per day of the year; Current.mdb holds the '
                 "current year's data and is copied to a {GUID}.mdb; the research, quoting Microsoft, says a new "
                 '{GUID}.mdb starts each year and the old one is kept for two years. Insert Date and Last Access '
                 'are read as FILETIMEs, Role GUID is RoleGuid read as a little-endian GUID, and Client Address is'
                 " Address read as an IP address, as plaso's User Access Logging parser reads them (Reference: "
                 "plaso, 'plaso/parsers/esedb_plugins/user_access_logging.py', "
                 'https://github.com/log2timeline/plaso/blob/2320e8dc947fc9ec1d8ceebc884a3c8c35479177/plaso/parsers/esedb_plugins/user_access_logging.py).'
                 ' The vendored ESE reader returns Address as hex text, which is read as 4 bytes for IPv4 or 16 '
                 'for IPv6; any other value is shown as the reader gave it. Role is the RoleName that ROLE_IDS '
                 'gives the GUID, blank when it gives none. Authenticated User Name is the stored string with the '
                 'NULs that pad it and any surrounding whitespace removed. Total Accesses is as stored. Accesses '
                 "per Day lists each non-zero DayN column as the date of day N of Insert Date's year, with its "
                 'count. Tenant ID is TenantId read as a GUID; the research reports seeing it populated with the '
                 'Active Directory Domain Services role and calls its interpretation unclear. ClientName is not '
                 'reported: the research reports not having seen it populated, and it held no value on any record '
                 'here. Validated on ou_ransomware_server2022 (Windows Server 2022 Standard, build 20348), a '
                 'simulation whose README states its user names and IP addresses are synthetic: 315 rows. There '
                 "Current.mdb's header records a dirty shutdown (state 2) and the 2024 {GUID}.mdb's a clean one "
                 '(state 3); read as they are, without replaying the transaction logs, both held the same 315 '
                 'CLIENTS records, so Databases held one value on all 315 rows, naming both. The {GUID}.mdb that '
                 "SystemIdentity.mdb's CHAINED_DATABASES table names for 2023 is not among the image's live files."
                 " Every row's Role resolved through ROLE_IDS: File Server 163, Active Directory Domain Services "
                 "147, DHCP Server 5. On every row the first non-zero DayN is Insert Date's day of the year, the "
                 "last non-zero DayN is Last Access's, and the counts sum to Total Accesses; reading DayN as day N"
                 " of Insert Date's year rests on that agreement. Client Address held a 4-byte address on 312 rows"
                 ' and a 16-byte one on 3. Tenant ID held the all-zero GUID on 168 rows and one other GUID on the '
                 "147 Active Directory Domain Services rows. Compared with the image's Security event log, which "
                 'holds events from 4 to 9 February 2024 only: 92 rows have a Last Access in that span, and on 81 '
                 'of them a logon event 4624 of logon type 3 for the same account name (the part after the '
                 'backslash) and IP address is within one second of Last Access, on 1 within a minute, and on 10 '
                 'there is none (5 DHCP Server, 3 File Server, 2 Active Directory Domain Services). A row is a '
                 'count User Access Logging kept, not a list of accesses: it gives a time only for the first and '
                 'the last access of the year. Not read: the transaction logs (Svc*.log) beside the databases, '
                 "which this artifact does not replay. On szechuan_dc01_server2012r2 Current.mdb's header records "
                 'a dirty shutdown and, read without its logs, its CLIENTS table held no records, so the artifact '
                 "gives 0 rows there. The corpus's other Windows disk images, pc_mus_001_win11, af_case2_win10, "
                 'lonewolf_win10, szechuan_win10, cfreds_leakage_win7 and alihadi_challenge3_win81, hold no User '
                 'Access Logging databases among their live files.',
        "paths": ('*/Windows/System32/LogFiles/Sum/*.mdb',),
        "output_types": "standard",
        "artifact_icon": "server",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 315 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (Current.mdb dirty, CLIENTS empty without log replay)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no User Access Logging databases)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no User Access Logging databases)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no User Access Logging databases)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no User Access Logging databases)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no User Access Logging databases)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no User Access Logging databases)",
        },
    },
    "windowsUserAccessLoggingRoleAccess": {
        "name": "User Access Logging - Role Access",
        "description": "One record per role for the year in Windows Server's User Access Logging databases (Current.mdb "
                       'and the per-year {GUID}.mdb files in Windows/System32/LogFiles/Sum), with its first and last '
                       'seen times.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-14",
        "last_update_date": "2026-10-14",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the ROLE_ACCESS table of Current.mdb and of each {GUID}.mdb in '
                 'Windows/System32/LogFiles/Sum, and names each role from the ROLE_IDS table of the '
                 'SystemIdentity.mdb in the same folder. A record found with the same values in several of the '
                 "folder's databases is one row, and Databases names each database it was found in. Patrick "
                 "Bennett's research describes FirstSeen as the earliest access to the role for the year and "
                 'LastSeen as the most recent (Reference: "UAL Thank Us Later: Leveraging User Access Logging for '
                 'Forensic Investigations", CrowdStrike, 8 June 2021, '
                 'https://www.crowdstrike.com/en-us/blog/user-access-logging-ual-overview/). First Seen and Last '
                 "Seen are read as FILETIMEs and Role GUID as a little-endian GUID, as plaso's User Access Logging"
                 " parser reads them (Reference: plaso, 'plaso/parsers/esedb_plugins/user_access_logging.py', "
                 'https://github.com/log2timeline/plaso/blob/2320e8dc947fc9ec1d8ceebc884a3c8c35479177/plaso/parsers/esedb_plugins/user_access_logging.py).'
                 ' Role is the RoleName that ROLE_IDS gives the GUID, blank when it gives none. Validated on '
                 'ou_ransomware_server2022 (Windows Server 2022 Standard, build 20348): 4 rows, Active Directory '
                 'Domain Services, File Server, DHCP Server and Print and Document Services; Current.mdb (dirty '
                 'shutdown, read without replaying its logs) and the 2024 {GUID}.mdb held the same 4 records, so '
                 'Databases held one value on all 4 rows, naming both. Compared with the User Access Logging - '
                 'Client Access rows from the same databases: for File Server and DHCP Server, First Seen equals '
                 "the earliest Insert Date and Last Seen the latest Last Access of that role's client rows; for "
                 'Active Directory Domain Services Last Seen equals the latest Last Access and First Seen is about'
                 ' 7 milliseconds after the earliest Insert Date; Print and Document Services has no client rows. '
                 "On szechuan_dc01_server2012r2 Current.mdb's header records a dirty shutdown and, read without "
                 'its logs, its ROLE_ACCESS table held no records, so the artifact gives 0 rows there. The '
                 "corpus's other Windows disk images, pc_mus_001_win11, af_case2_win10, lonewolf_win10, "
                 'szechuan_win10, cfreds_leakage_win7 and alihadi_challenge3_win81, hold no User Access Logging '
                 'databases among their live files.',
        "paths": ('*/Windows/System32/LogFiles/Sum/*.mdb',),
        "output_types": "standard",
        "artifact_icon": "server",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 4 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (Current.mdb dirty, ROLE_ACCESS empty without log replay)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no User Access Logging databases)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no User Access Logging databases)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no User Access Logging databases)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no User Access Logging databases)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no User Access Logging databases)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no User Access Logging databases)",
        },
    },
    "windowsUserAccessLoggingDns": {
        "name": "User Access Logging - DNS",
        "description": "The DNS table of Windows Server's User Access Logging databases (Current.mdb and the per-year "
                       '{GUID}.mdb files in Windows/System32/LogFiles/Sum): host name and address as text, and the last '
                       'seen time.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-14",
        "last_update_date": "2026-10-14",
        "requirements": "none",
        "category": "Windows",
        "notes": 'Reads the DNS table of Current.mdb and of each {GUID}.mdb in Windows/System32/LogFiles/Sum. A '
                 "record found with the same values in several of the folder's databases is one row, and Databases"
                 " names each database it was found in. Patrick Bennett's research reports that the table appears "
                 'to be populated only when the server has the DNS Server role, that it holds IP address to host '
                 'name mappings, and that what fills it needs more research (Reference: "UAL Thank Us Later: '
                 'Leveraging User Access Logging for Forensic Investigations", CrowdStrike, 8 June 2021, '
                 'https://www.crowdstrike.com/en-us/blog/user-access-logging-ual-overview/). Last Seen is read as '
                 "a FILETIME, as plaso's User Access Logging parser reads it (Reference: plaso, "
                 "'plaso/parsers/esedb_plugins/user_access_logging.py', "
                 'https://github.com/log2timeline/plaso/blob/2320e8dc947fc9ec1d8ceebc884a3c8c35479177/plaso/parsers/esedb_plugins/user_access_logging.py).'
                 ' Host Name and Address are the stored strings with the NULs that pad them and any surrounding '
                 'whitespace removed. Validated on ou_ransomware_server2022 (Windows Server 2022 Standard, build '
                 '20348): 11 rows, 11 host names and 6 addresses; Current.mdb (dirty shutdown, read without '
                 'replaying its logs) and the 2024 {GUID}.mdb held the same 11 records, so Databases held one '
                 'value on all 11 rows, naming both. What a row shows about any client or lookup is not '
                 'established, and Last Seen was not compared with a second source. On szechuan_dc01_server2012r2 '
                 "Current.mdb's header records a dirty shutdown and, read without its logs, its DNS table held no "
                 'records, so the artifact gives 0 rows there. The VIRTUALMACHINES table of the same databases is '
                 "not reported: it held no records on either server. The corpus's other Windows disk images, "
                 'pc_mus_001_win11, af_case2_win10, lonewolf_win10, szechuan_win10, cfreds_leakage_win7 and '
                 'alihadi_challenge3_win81, hold no User Access Logging databases among their live files.',
        "paths": ('*/Windows/System32/LogFiles/Sum/*.mdb',),
        "output_types": "standard",
        "artifact_icon": "server",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 11 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation (build 9600) | 0 rows (Current.mdb dirty, DNS empty without log replay)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no User Access Logging databases)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no User Access Logging databases)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no User Access Logging databases)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no User Access Logging databases)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 (build 7601) | 0 rows (no User Access Logging databases)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no User Access Logging databases)",
        },
    },
}

import binascii
import ipaddress
import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone

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


# ---- client access, role access and DNS (Current.mdb and the per-year {GUID}.mdb files) ----------------------

_ACCESS_DATABASE = re.compile(r'(current|\{[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}\})\.mdb$', re.IGNORECASE)


def guid(value):
    """A GUID column's 16 bytes as {xxxxxxxx-...}, read little-endian as plaso reads it; '' when not 16 bytes."""
    if not isinstance(value, (bytes, bytearray)) or len(value) != 16:
        return ''
    return '{' + str(uuid.UUID(bytes_le=bytes(value))) + '}'


def client_address(value):
    """CLIENTS.Address, a binary column the vendored reader returns as hex text: 4 bytes IPv4, 16 bytes IPv6. Any
    other value is returned as the reader gave it."""
    if value is None:
        return ''
    try:
        return str(ipaddress.ip_address(binascii.unhexlify(value)))
    except (binascii.Error, TypeError, ValueError):
        return value.decode('latin-1') if isinstance(value, (bytes, bytearray)) else str(value)


def daily_counts(row, year):
    """'yyyy-mm-dd: n' for each non-zero DayN column, DayN read as day N of the given year; '' without a year."""
    if not year:
        return ''
    out = []
    for index in range(1, 367):
        count = row.get(f'Day{index}')
        if not count:
            continue
        try:
            day = date(year, 1, 1) + timedelta(days=index - 1)
        except (OverflowError, ValueError):
            return ''
        out.append(f'{day.isoformat()}: {count}')
    return '; '.join(out)


def _time(value):
    return filetime(value) if isinstance(value, int) else ''


def _table(path, table, label, relative):
    """The records of one table of one database as dicts, or [] with the reason logged."""
    database = ese_rows.ESEDatabase(path)
    try:
        database.mountDB()
        walk = ese_rows.TableRows(database, table)
        rows = [_named(record) for record in walk]
        if not walk.found:
            logfunc(f'{label}: {relative} has no {table} table')
        elif walk.summary():
            logfunc(f'{label}: {relative}, {walk.summary()}')
        return rows
    finally:
        database.close()


def _folders(context):
    """{folder: [database paths]} for the Sum folders holding Current.mdb or a {GUID}.mdb, sorted."""
    folders = {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isfile(path) and _ACCESS_DATABASE.fullmatch(os.path.basename(path)):
            folders.setdefault(os.path.dirname(path), []).append(path)
    return folders


def _role_names(folder, label, context):
    """{role GUID: role name} from the ROLE_IDS table of the SystemIdentity.mdb beside the databases."""
    path = os.path.join(folder, 'SystemIdentity.mdb')
    if not os.path.isfile(path):
        return {}
    relative = context.get_relative_path(path)
    try:
        rows = _table(path, 'ROLE_IDS', label, relative)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logfunc(f'{label}: could not read {relative}: {type(exc).__name__}: {exc}')
        return {}
    return {guid(row.get('RoleGuid')): text(row.get('RoleName')) for row in rows if guid(row.get('RoleGuid'))}


def _merged(context, table, label, build):
    """Rows built from one table across each folder's databases. A record found identically in several databases
    is one row naming each of them; the last column is the databases, and the paths read are returned."""
    data_list, read = [], []
    for folder, paths in _folders(context).items():
        roles = _role_names(folder, label, context)
        seen = {}
        for path in paths:
            relative = context.get_relative_path(path)
            try:
                records = _table(path, table, label, relative)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logfunc(f'{label}: could not read {relative}: {type(exc).__name__}: {exc}')
                continue
            read.append(path)
            for record in records:
                key = tuple(sorted((name, repr(value)) for name, value in record.items()))
                if key not in seen:
                    seen[key] = (build(record, roles), [])
                seen[key][1].append(os.path.basename(path))
        data_list.extend(row + ('; '.join(names),) for row, names in seen.values())
    data_list.sort(key=lambda row: tuple(str(value) for value in row))
    return data_list, read


def _role(record, roles):
    role = guid(record.get('RoleGuid'))
    return roles.get(role, ''), role


def client_row(record, roles):
    name, role = _role(record, roles)
    inserted = _time(record.get('InsertDate'))
    return (_time(record.get('LastAccess')), inserted, name, text(record.get('AuthenticatedUserName')),
            client_address(record.get('Address')), number(record.get('TotalAccesses')),
            daily_counts(record, inserted.year if inserted else None), role, guid(record.get('TenantId')))


def role_access_row(record, roles):
    name, role = _role(record, roles)
    return (_time(record.get('LastSeen')), _time(record.get('FirstSeen')), name, role)


def dns_row(record, _roles):
    return (_time(record.get('LastSeen')), text(record.get('HostName')), text(record.get('Address')))


def _access(context, table, label, headers, build):
    if ese_rows is None:
        logfunc(f'{label}: the vendored ESE reader is not available')
        return headers, [], ''
    data_list, read = _merged(context, table, label, build)
    return headers, data_list, '\n'.join(read)


@artifact_processor
def windowsUserAccessLoggingClients(context):
    data_headers = (('Last Access', 'datetime'), ('Insert Date', 'datetime'), 'Role', 'Authenticated User Name',
               'Client Address', 'Total Accesses', 'Accesses per Day', 'Role GUID', 'Tenant ID', 'Databases')
    return _access(context, 'CLIENTS', 'User Access Logging - Client Access', data_headers, client_row)


@artifact_processor
def windowsUserAccessLoggingRoleAccess(context):
    data_headers = (('Last Seen', 'datetime'), ('First Seen', 'datetime'), 'Role', 'Role GUID', 'Databases')
    return _access(context, 'ROLE_ACCESS', 'User Access Logging - Role Access', data_headers, role_access_row)


@artifact_processor
def windowsUserAccessLoggingDns(context):
    data_headers = (('Last Seen', 'datetime'), 'Host Name', 'Address', 'Databases')
    return _access(context, 'DNS', 'User Access Logging - DNS', data_headers, dns_row)
