"""Windows SRUM (System Resource Usage Monitor) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.SRUM artifact; the
provider-table GUID names of the first four artifacts are taken from that artifact,
and those of the WPN and Energy Usage providers from the SRUM Extensions registry key. SRUDB.dat is an
ESE (Extensible Storage Engine) database and is read with the ESE reader adapted
from impacket in scripts/vendor/impacket_ese.py.

The entry TimeStamp column is decoded as an OLE automation date. That reading is
corroborated against the EndTime FILETIME on the Execution Stats table, which
shares the same instant on a row and agrees to within a minute; EndTime and
ConnectStartTime are Windows FILETIMEs, matching the Velociraptor artifact's
winfiletime handling of those columns.
"""

import os
import struct
import binascii
from datetime import datetime, timedelta, timezone

try:
    from scripts.vendor import impacket_ese
    from scripts import ese_recovery, ese_rows
except ImportError:
    impacket_ese = None
    ese_recovery = ese_rows = None

from scripts.ilapfuncs import artifact_processor, logfunc

# SRUM keeps one ESE table per provider, named by a GUID. These four provider
# GUIDs and their names are from the Velociraptor Windows.Forensics.SRUM artifact
# (NetworkUsageGUID, ApplicationResourceUsageGUID, NetworkConnectionsGUID,
# ExecutionGUID). Each row's AppId and UserId are integer indexes into
# SruDbIdMapTable, which resolves them to an application id string or a user SID.
_NETWORK_USAGE = "{973F5D5C-1D90-4944-BE8E-24B94231A174}"
_APP_RESOURCE = "{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}"
_NETWORK_CONNECTIONS = "{DD6636C4-8929-4683-974E-22C046A43763}"
_EXECUTION = "{5C8CF1C7-7257-4F13-B223-970EF5939312}"
# The names of these two are the ones each provider's key carries under
# SOFTWARE\Microsoft\Windows NT\CurrentVersion\SRUM\Extensions on the tested images.
_WPN = "{D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}"        # WPN SRUM Provider
_ENERGY_USAGE = "{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}"  # Energy Usage Provider
# Named SDP Cpu, Physical Disk, Volume and Network Provider (sdprov.dll) in the same key on
# ou_ransomware_server2022 and alihadi_threatsim_server2019.
_SDP_CPU = "{DC3D3B50-BB90-5066-FA4E-A5F90DD8B677}"
_SDP_PHYSICAL_DISK = "{841A7317-3805-518B-C2EA-AD224CB4AF84}"
_SDP_VOLUME = "{17F4D97B-F26A-5E79-3A82-90040A47D13D}"
_SDP_NETWORK = "{EEE2F477-0659-5C47-EF03-6D6BEFD441B3}"

_IDMAP = "SruDbIdMapTable"
_SRUDB = "srudb.dat"

__artifacts_v2__ = {
    "srumNetworkUsage": {
        "name": "SRUM Network Usage",
        "description": "Per-application network bytes sent and received recorded by "
                       "SRUM, from the Network Usage provider in SRUDB.dat, with the "
                       "application, user SID, network interface and snapshot time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Network Usage table "
                 "{973F5D5C-1D90-4944-BE8E-24B94231A174}. Bytes Sent and Bytes "
                 "Received are byte counts for the snapshot as stored. Interface "
                 "LUID and L2 Profile ID are the network interface and profile "
                 "identifiers as stored; they are not resolved to a network name "
                 "here. Read from SRUDB.dat, named in Source File, with the ESE "
                 "reader adapted from impacket in scripts/vendor. Each row is one "
                 "entry in this SRUM provider table. Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since "
                 "1899-12-30); decoded as a Windows FILETIME the same value is out "
                 "of range, and the OLE reading places every row in the same period "
                 "as the FILETIME columns in these tables. "
                 "Application and User are resolved from SruDbIdMapTable: "
                 "Application is the stored application id (such as a package "
                 "moniker, a service name, or an executable path, as stored) and "
                 "User is the account SID; either is blank when the entry's id is 0, "
                 "is absent from the map or maps to an entry with no IdBlob. SRUM "
                 "aggregates usage into periodic snapshots, so a "
                 "row is a recorded total for a snapshot and not a single user "
                 "action, and it does not record who was at the keyboard. A record "
                 "ESE marks deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log, and no SRUM table read on the tested images "
                 "held either. A SruDbIdMapTable IdBlob that ESE stores apart from its "
                 "record (the record flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from that table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for "
                 "example, or a piece stored compressed, which is not decompressed) "
                 "leaves Application or User blank, and the run log counts it and names "
                 "the reason. No SRUDB.dat on the tested images held any value stored "
                 "apart. In a SRUDB.dat cut short, such as a partial copy, a page of a "
                 "table, SruDbIdMapTable included, that lies past the end of the file is passed over,"
                 " with every page beneath it, and the pages that remain are read, and the run log "
                 "names "
                 "the table and counts the pages it reached that lie past the end; an id whose SruDbIdMapTable "
                 "record was not read is not resolved. Copies of lonewolf_win10's file cut to "
                 "90, 75, 50 and 25 percent of its length gave 2,471, 2,471, 1,652 and "
                 "827 of the 2,471 rows the whole file gives, and on the 90 percent copy "
                 "136 rows had a blank Application against 113 with the whole file. A "
                 "SRUDB.dat that does "
                 "not carry this provider table "
                 "gives this artifact no rows for that file, and the file is named in "
                 "the run log. "
                 "A SRUDB.dat whose header records a dirty shutdown is first brought up to date in memory from the"
                 " transaction logs beside it, by the replay in scripts/ese_recovery that the User Access Logging "
                 "artifacts also use; the replay refuses any log record it cannot reproduce exactly, and the file "
                 "is then read as stored, with the reason in the run log. On windows11_arm_srum_live_20261024, a "
                 "SRUDB.dat copied from a Volume Shadow Copy of a running Windows 11 build 26200 machine, the "
                 "header records a dirty shutdown, the replay refused at a SetExternalHeader record, which it does"
                 " not redo, and the file was read as stored. Its newest log held 122 Insert records whose dbtime is"
                 " above that of the page they change. ESE's own recovery of a copy (esentutl /r, run on Windows 11"
                 " build 26200) rolled back a transaction still open at the capture and marked deleted the 72"
                 " Application Resource Usage entries it had inserted, all stamped in the minute the copy was taken;"
                 " 56 of them are on the pages and are reported by that artifact, and 16 were only in the log. Every"
                 " other table read the same after that recovery as it reads here. "
                 "Every other tested SRUDB.dat records a clean shutdown. "
                 "GUID "
                 "names: Velocidex, Windows.Forensics.SRUM, https://github.com/"
                 "Velocidex/velociraptor/blob/master/artifacts/definitions/Windows/"
                 "Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "download",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2242 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 57 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 2471 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 217 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 9 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no such table)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 8862 rows",
        },
    },
    "srumApplicationResourceUsage": {
        "name": "SRUM Application Resource Usage",
        "description": "Per-application disk bytes read and written and CPU cycle "
                       "time recorded by SRUM, from the Application Resource Usage "
                       "provider in SRUDB.dat, with the application, user SID and "
                       "snapshot time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Application Resource Usage table "
                 "{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}. Foreground and Background "
                 "Bytes Read and Bytes Written are disk byte counts for the snapshot "
                 "as stored. Foreground and Background Cycle Time are CPU cycle "
                 "counts as stored; their unit is not converted. On the two server images, "
                 "ou_ransomware_server2022 and alihadi_threatsim_server2019, Foreground Bytes Read, Foreground "
                 "Bytes Written, Background Bytes Read and Background Bytes Written held 0 on all 73,965 and all 490 "
                 "rows, while Foreground Cycle Time took 71,106 and 489 distinct values. Read from "
                 "SRUDB.dat, named in Source File, with the ESE reader adapted from "
                 "impacket in scripts/vendor. Each row is one entry in this SRUM "
                 "provider table. Timestamp (UTC) is the entry's TimeStamp column "
                 "decoded as an OLE automation date (days since 1899-12-30); decoded "
                 "as a Windows FILETIME the same value is out of range, and the OLE "
                 "reading places every row in the same period as the FILETIME "
                 "columns in these tables. Application and User "
                 "are resolved from SruDbIdMapTable: Application is the stored "
                 "application id (such as a package moniker, a service name, or an "
                 "executable path, as stored) and User is the account SID; either is "
                 "blank when the entry's id is 0 or absent from the map. SRUM "
                 "aggregates usage into periodic snapshots, so a row is a recorded "
                 "total for a snapshot and not a single user action, and it does not "
                 "record who was at the keyboard. A record ESE marks deleted (its "
                 "fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log, and no SRUM table read on the tested images "
                 "held either. A SruDbIdMapTable IdBlob that ESE stores apart from its "
                 "record (the record flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from that table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for "
                 "example, or a piece stored compressed, which is not decompressed) "
                 "leaves Application or User blank, and the run log counts it and names "
                 "the reason. No SRUDB.dat on the tested images held any value stored "
                 "apart. In a SRUDB.dat cut short, such as a partial copy, a page of a "
                 "table, SruDbIdMapTable included, that lies past the end of the file is passed over,"
                 " with every page beneath it, and the pages that remain are read, and the run log "
                 "names "
                 "the table and counts the pages it reached that lie past the end; an id whose SruDbIdMapTable "
                 "record was not read is not resolved. Copies of lonewolf_win10's file cut to "
                 "90, 75, 50 and 25 percent of its length gave 10,546, 8,784, 5,920 and "
                 "0 of the 15,055 rows the whole file gives. On windows11_arm_srum_live_20261024 the last leaf page of "
                 "this table links to a page owned by another object, from which no record is taken, "
                 "as the run log says, "
                 "and the 47,728 rows read are the rows dissect.esedb 3.18 reads from the table. Of those, ESE's own "
                 "recovery of a copy keeps 47,672 and marks the other 56 deleted, rolling back the transaction that "
                 "inserted them; they are reported here as stored. A SRUDB.dat that does "
                 "not carry this provider table "
                 "gives this artifact no rows for that file, and the file is named in "
                 "the run log. "
                 "A SRUDB.dat whose header records a dirty shutdown is first brought up to date in memory from the"
                 " transaction logs beside it, by the replay in scripts/ese_recovery that the User Access Logging "
                 "artifacts also use; the replay refuses any log record it cannot reproduce exactly, and the file "
                 "is then read as stored, with the reason in the run log. On windows11_arm_srum_live_20261024, a "
                 "SRUDB.dat copied from a Volume Shadow Copy of a running Windows 11 build 26200 machine, the "
                 "header records a dirty shutdown, the replay refused at a SetExternalHeader record, which it does"
                 " not redo, and the file was read as stored. Its newest log held 122 Insert records whose dbtime is"
                 " above that of the page they change. ESE's own recovery of a copy (esentutl /r, run on Windows 11"
                 " build 26200) rolled back a transaction still open at the capture and marked deleted the 72"
                 " Application Resource Usage entries it had inserted, all stamped in the minute the copy was taken;"
                 " 56 of them are on the pages and are reported by that artifact, and 16 were only in the log. Every"
                 " other table read the same after that recovery as it reads here. "
                 "Every other tested SRUDB.dat records a clean shutdown. "
                 "GUID names: Velocidex, "
                 "Windows.Forensics.SRUM, https://github.com/Velocidex/velociraptor/"
                 "blob/master/artifacts/definitions/Windows/Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 14667 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1458 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 15055 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 766 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 54 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 73965 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 490 rows",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 47728 rows",
        },
    },
    "srumNetworkConnections": {
        "name": "SRUM Network Connections",
        "description": "Network interface connection periods recorded by SRUM, from "
                       "the Network Connections provider in SRUDB.dat, with the "
                       "connection start time and the connected-time counter.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Network Connections table "
                 "{DD6636C4-8929-4683-974E-22C046A43763}. Connect Start Time (UTC) "
                 "is a Windows FILETIME as stored, matching the Velociraptor "
                 "artifact's winfiletime handling of that column. Connected Time is "
                 "the connected-time counter as stored; its unit is not converted. "
                 "Interface LUID and L2 Profile ID are the network interface and "
                 "profile identifiers as stored. The application and user ids are 1 "
                 "and 2 on every row of the eight tested images, and SruDbIdMapTable "
                 "holds no IdBlob for either, so no application or user is surfaced "
                 "here. "
                 "Read from SRUDB.dat, named in Source File, "
                 "with the ESE reader adapted from impacket in scripts/vendor. Each "
                 "row is one entry in this SRUM provider table. Timestamp (UTC) is "
                 "the entry's TimeStamp column decoded as an OLE automation date "
                 "(days since 1899-12-30); decoded as a Windows FILETIME the same "
                 "value is out of range, and the OLE reading places every row in the "
                 "same period as the Connect Start Time FILETIME. SRUM aggregates "
                 "usage into periodic snapshots, so "
                 "a row is a recorded total for a snapshot and not a single user "
                 "action, and it does not record who was at the keyboard. A record "
                 "ESE marks deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are "
                 "counted in the run log, and no SRUM table read on the tested images "
                 "held either. In a SRUDB.dat cut short, such as a partial copy, a "
                 "page of the table that lies past the end of the file is passed over, with every "
                 "page beneath it, and the pages that remain are read, and the run log counts the "
                 "pages it reached that lie past the end. "
                 "Copies of lonewolf_win10's file cut to 90, 75, 50 and 25 percent of "
                 "its length gave 201, 159, 159 and 159 of the 201 rows the whole file "
                 "gives. A SRUDB.dat that does not carry this provider table "
                 "gives this artifact no rows for that file, and the file is named in "
                 "the run log. "
                 "A SRUDB.dat whose header records a dirty shutdown is first brought up to date in memory from the"
                 " transaction logs beside it, by the replay in scripts/ese_recovery that the User Access Logging "
                 "artifacts also use; the replay refuses any log record it cannot reproduce exactly, and the file "
                 "is then read as stored, with the reason in the run log. On windows11_arm_srum_live_20261024, a "
                 "SRUDB.dat copied from a Volume Shadow Copy of a running Windows 11 build 26200 machine, the "
                 "header records a dirty shutdown, the replay refused at a SetExternalHeader record, which it does"
                 " not redo, and the file was read as stored. Its newest log held 122 Insert records whose dbtime is"
                 " above that of the page they change. ESE's own recovery of a copy (esentutl /r, run on Windows 11"
                 " build 26200) rolled back a transaction still open at the capture and marked deleted the 72"
                 " Application Resource Usage entries it had inserted, all stamped in the minute the copy was taken;"
                 " 56 of them are on the pages and are reported by that artifact, and 16 were only in the log. Every"
                 " other table read the same after that recovery as it reads here. "
                 "Every other tested SRUDB.dat records a clean shutdown. "
                 "GUID "
                 "names: Velocidex, Windows.Forensics.SRUM, https://github.com/"
                 "Velocidex/velociraptor/blob/master/artifacts/definitions/Windows/"
                 "Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "globe",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 224 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 10 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 201 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 10 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 2 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 1347 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 9 rows",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 707 rows",
        },
    },
    "srumExecutionStats": {
        "name": "SRUM Execution Stats",
        "description": "Per-application foreground execution periods recorded by "
                       "SRUM, from the Execution Stats provider in SRUDB.dat, with "
                       "the application, user SID, end time and duration.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM Execution Stats table "
                 "{5C8CF1C7-7257-4F13-B223-970EF5939312}. End Time (UTC) is a "
                 "Windows FILETIME as stored, matching the Velociraptor artifact's "
                 "winfiletime handling of that column. Duration (ms) and Span (ms) "
                 "are the recorded duration and span for the entry in milliseconds "
                 "as stored. The table's other timeline and cycle columns are not "
                 "surfaced here. Read from SRUDB.dat, named in Source File, with the "
                 "ESE reader adapted from impacket in scripts/vendor. Each row is one "
                 "entry in this SRUM provider table. Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since "
                 "1899-12-30); decoded as a Windows FILETIME the same value is out "
                 "of range, and the OLE reading places every row in the same period "
                 "as the End Time FILETIME in this table. Timestamp is the snapshot "
                 "time and End Time is when the entry's execution period ended, so "
                 "the two need not be the same instant on a row. Application and User are "
                 "resolved from "
                 "SruDbIdMapTable: Application is the stored application id (a "
                 "package moniker, a service name, or an executable path as stored) "
                 "and User is the account SID; either is blank when the entry's id is 0, "
                 "is absent from the map or maps to an entry with no IdBlob. SRUM "
                 "aggregates usage into periodic "
                 "snapshots, so a row is a recorded total for a snapshot and not a "
                 "single user action, and it does not record who was at the "
                 "keyboard. A record ESE marks deleted (its fNDDeleted node flag, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/node.hxx#L248) "
                 "is not read, since ESE's own code treats such a record as not there "
                 "unless its version store still holds an update to it "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/ese/node.cxx#L1049-L1079), "
                 "and a record the ESE reader cannot convert is skipped; both are counted "
                 "in the run log, and no SRUM table read on the tested images held either. "
                 "A SruDbIdMapTable IdBlob that ESE stores apart from its record (the record "
                 "flags it fSeparated, "
                 "https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/tagfld.hxx#L46-L53) "
                 "is read from that table's long value tree "
                 "(https://github.com/microsoft/Extensible-Storage-Engine/blob/7030fe7407615160e54d152e4ef704eede2fdd7e/dev/ese/src/inc/lv.hxx#L36-L62); "
                 "one that cannot be assembled from that tree (a piece missing, for example, "
                 "or a piece stored compressed, which is not decompressed) leaves "
                 "Application or User blank, and the run log counts it and names the reason. "
                 "No SRUDB.dat on the tested images held any value stored apart. In a "
                 "SRUDB.dat cut short, such as a partial copy, a page of a table, "
                 "SruDbIdMapTable included, that lies past the end of the file is passed over, with "
                 "every page beneath it, and the pages that remain are read, and the run log names "
                 "the table and counts the pages it reached that lie past the end; an id whose "
                 "SruDbIdMapTable record was not read is not "
                 "resolved. Copies of lonewolf_win10's file cut to 90, 75, 50 and 25 percent of "
                 "its length gave 10,412, 7,640, 0 and 0 of the 12,332 rows the whole file gives. "
                 "A SRUDB.dat that does not carry this provider table gives this artifact "
                 "no rows for that file, and the file is named in the run log. "
                 "A SRUDB.dat whose header records a dirty shutdown is first brought up to date in memory from the"
                 " transaction logs beside it, by the replay in scripts/ese_recovery that the User Access Logging "
                 "artifacts also use; the replay refuses any log record it cannot reproduce exactly, and the file "
                 "is then read as stored, with the reason in the run log. On windows11_arm_srum_live_20261024, a "
                 "SRUDB.dat copied from a Volume Shadow Copy of a running Windows 11 build 26200 machine, the "
                 "header records a dirty shutdown, the replay refused at a SetExternalHeader record, which it does"
                 " not redo, and the file was read as stored. Its newest log held 122 Insert records whose dbtime is"
                 " above that of the page they change. ESE's own recovery of a copy (esentutl /r, run on Windows 11"
                 " build 26200) rolled back a transaction still open at the capture and marked deleted the 72"
                 " Application Resource Usage entries it had inserted, all stamped in the minute the copy was taken;"
                 " 56 of them are on the pages and are reported by that artifact, and 16 were only in the log. Every"
                 " other table read the same after that recovery as it reads here. "
                 "Every other tested SRUDB.dat records a clean shutdown. "
                 "GUID names: Velocidex, "
                 "Windows.Forensics.SRUM, "
                 "https://github.com/Velocidex/velociraptor/blob/master/artifacts/"
                 "definitions/Windows/Forensics/SRUM.yaml",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "clock",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 19708 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 2777 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 12332 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1,488 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no such table)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 20842 rows",
        },
    },
    "srumWpnNotifications": {
        "name": "SRUM WPN Notifications",
        "description": "Notification entries recorded by SRUM per application, from the WPN SRUM Provider "
                       "table in SRUDB.dat, with the application, user SID, notification type, payload size "
                       "and the entry's recorded time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}. On the six images "
                 "whose SOFTWARE hive was read (af_case2_win10, lonewolf_win10, pc_mus_001_win11, szechuan_win10, "
                 "ou_ransomware_server2022 and alihadi_threatsim_server2019) the key of that GUID under SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SRUM\\"
                 "Extensions is named WPN SRUM Provider with the DLL wpnsruprov.dll. Each row is one entry of "
                 "the table. Application and User SID are resolved from SruDbIdMapTable and are blank when the "
                 "entry's id is absent from the map or maps to an entry with no IdBlob. Notification Type, Payload Size and Network Type are the "
                 "NotificationType, PayloadSize and NetworkType columns as stored; no source for the meaning "
                 "of the Notification Type and Network Type numbers or for the unit of Payload Size was read, "
                 "so they are not translated. On the tested images Notification Type held 1, 4 and 128 and "
                 "Network Type held 0 on every row, and User SID held one value on every row of af_case2_win10, "
                 "lonewolf_win10 and pc_mus_001_win11 and three values on szechuan_win10. "
                 "Read from SRUDB.dat, named in Source File, with the ESE reader adapted from impacket in "
                 "scripts/vendor, the same way as the SRUM Network Usage artifact, whose notes say how "
                 "deleted records, values stored apart, a file cut short and a file in dirty shutdown are handled. "
                 "Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since 1899-12-30). "
                 "A row is an entry SRUM recorded for an application; it does not show that a notification "
                 "was displayed or read.",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "bell",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 73 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 13 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 90 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 11 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no such table)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 6 rows",
        },
    },
    "srumEnergyUsage": {
        "name": "SRUM Energy Usage",
        "description": "Battery state entries recorded by SRUM, from the Energy Usage Provider table in "
                       "SRUDB.dat: the event time, state transition, charge level and battery capacities.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}. On af_case2_win10, "
                 "lonewolf_win10, pc_mus_001_win11 and szechuan_win10 the key of that GUID under "
                 "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SRUM\\Extensions is named Energy Usage "
                 "Provider with the DLL energyprov.dll; the SOFTWARE hives of ou_ransomware_server2022 and "
                 "alihadi_threatsim_server2019 carry no such key, and that of windows11_arm_srum_live_20261024 was "
                 "not read. Each row is one entry "
                 "of the table. Event Time (UTC) is the EventTimestamp column read as a Windows FILETIME: on "
                 "lonewolf_win10 and pc_mus_001_win11 that reading puts every value at or before the row's own "
                 "Timestamp (UTC), or after it by less than a tenth of a second, with a median gap under one "
                 "hour and a largest gap of about 29 hours on lonewolf_win10 and about 235 hours on "
                 "pc_mus_001_win11. State Transition, Designed Capacity, Full Charged "
                 "Capacity, Charge Level, Cycle Count, Battery Count, Battery Charge Limited and Configuration "
                 "Hash are the columns of those names as stored, Configuration Hash as text; no source for the meaning of the State "
                 "Transition numbers or for the unit of the capacity and charge columns was read, so they are "
                 "not translated. Battery Count and Battery Charge Limited are blank where the file has no such "
                 "column (lonewolf_win10) or the entry holds no value (188 of 494 rows on pc_mus_001_win11). "
                 "Cycle Count held 0 on every row of both images and Configuration Hash held one value on every "
                 "row of each. On lonewolf_win10 Designed Capacity and Full Charged Capacity each held one "
                 "value on all 289 rows, and on pc_mus_001_win11 Full Charged Capacity equalled Designed "
                 "Capacity on all 494 rows. The table's AppId and UserId held 1 and 2 on "
                 "every row and are not shown. On af_case2_win10 and szechuan_win10 the table is "
                 "empty. Not read: the long-term table {FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}LT (1 and 7 "
                 "rows on the two images), and three other provider tables, named in the same registry key on "
                 "the images that carry them, Energy Estimation Provider {DA73FB89-2BEA-4DDC-86B8-6E048C6DA477} and Tagged "
                 "Energy Provider {B6D82AF1-F780-4E17-8077-6CB9AD8A6FC4}, whose payload columns are binary, with no layout "
                 "read here, and vfuprov {7ACBBAA3-D029-4BE4-9A7A-0885927F1D8F}, whose "
                 "entries are keyed by short codes and not by application. "
                 "Read from SRUDB.dat, named in Source File, with the ESE reader adapted from impacket in "
                 "scripts/vendor, the same way as the SRUM Network Usage artifact, whose notes say how "
                 "deleted records, values stored apart, a file cut short and a file in dirty shutdown are handled. "
                 "Timestamp (UTC) is the entry's "
                 "TimeStamp column decoded as an OLE automation date (days since 1899-12-30). "
                 "A row is a battery state SRUM recorded, not a user action.",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "battery-charging",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 494 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the table is empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 289 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the table is empty)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 0 rows (no such table)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 1188 rows",
        },
    },
    "srumSdpCpu": {
        "name": "SRUM SDP Cpu",
        "description": "Entries of the SDP Cpu Provider table in SRUDB.dat, as found on Windows Server images: the entry time, the SruDbIdMapTable value its AppId names and its ProcessorTime value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {DC3D3B50-BB90-5066-FA4E-A5F90DD8B677}. On ou_ransomware_server2022 and"
                 " alihadi_threatsim_server2019 the key of that GUID under SOFTWARE\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\SRUM\\Extensions is named SDP Cpu Provider with the DLL sdprov.dll. Each row is"
                 " one entry of the table. AppId Entry is the SruDbIdMapTable value the row's AppId names, decoded"
                 " as text as for the Application column of the other SRUM artifacts; it is blank when the id is "
                 "absent from the map or maps to an entry with no IdBlob. The table's UserId held 2 on every row of both tested images, and that id "
                 "maps to an entry with no IdBlob, so no user is shown. The value columns are the table's columns "
                 "of those names as stored (64-bit integers, ESE column type LongLong); no source for their "
                 "meaning or unit was read, so they are not converted, and what the provider measures is not "
                 "established. Timestamp (UTC) is the entry's TimeStamp column decoded as an OLE automation date "
                 "(days since 1899-12-30). Read from SRUDB.dat, named in Source File, with the ESE reader adapted "
                 "from impacket in scripts/vendor, the same way as the SRUM Network Usage artifact, whose notes "
                 "say how deleted records, values stored apart, a file cut short and a file in dirty shutdown are "
                 "handled. The table is present on the two server images tested, Windows Server 2022 "
                 "(ou_ransomware_server2022) and Windows Server 2019 (alihadi_threatsim_server2019), and on none "
                 "of the six Windows 10, 11 and 8.1 SRUDB.dat files tested; a SRUDB.dat without it gives this "
                 "artifact no rows. Eric Zimmerman's SrumECmd reads the same table (EricZimmerman/Srum, "
                 "SrumData/Srum.cs, commit 46fb4e9611c33fdc96236e79d0075db9090bd91c), naming it after its columns "
                 "and describing what the providers measure as not documented. A row is a value the provider "
                 "recorded, not a user action. AppId Entry held Total on every row of both images. "
                 "ProcessorTime held integers from 0 to 92 on ou_ransomware_server2022 (3,005 rows, 24 September "
                 "2023 to 9 February 2024) and 0 to 83 on alihadi_threatsim_server2019 (21 rows, 21 August 2021 to"
                 " 17 June 2022).",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "cpu",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 3005 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no such table)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no such table)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no such table)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no such table)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 0 rows (no such table)",
        },
    },
    "srumSdpPhysicalDisk": {
        "name": "SRUM SDP Physical Disk",
        "description": "Entries of the SDP Physical Disk Provider table in SRUDB.dat, as found on Windows Server images: the entry time, the SruDbIdMapTable value its AppId names and its SizeInBytes value as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {841A7317-3805-518B-C2EA-AD224CB4AF84}. On ou_ransomware_server2022 and"
                 " alihadi_threatsim_server2019 the key of that GUID under SOFTWARE\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\SRUM\\Extensions is named SDP Physical Disk Provider with the DLL sdprov.dll. "
                 "Each row is one entry of the table. AppId Entry is the SruDbIdMapTable value the row's AppId "
                 "names, decoded as text as for the Application column of the other SRUM artifacts; it is blank "
                 "when the id is absent from the map or maps to an entry with no IdBlob. The table's UserId held 2 on every row of both tested "
                 "images, and that id maps to an entry with no IdBlob, so no user is shown. The value columns are "
                 "the table's columns of those names as stored (64-bit integers, ESE column type LongLong); no "
                 "source for their meaning or unit was read, so they are not converted, and what the provider "
                 "measures is not established. Timestamp (UTC) is the entry's TimeStamp column decoded as an OLE "
                 "automation date (days since 1899-12-30). Read from SRUDB.dat, named in Source File, with the ESE"
                 " reader adapted from impacket in scripts/vendor, the same way as the SRUM Network Usage "
                 "artifact, whose notes say how deleted records, values stored apart, a file cut short and a file "
                 "in dirty shutdown are handled. The table is present on the two server images tested, Windows "
                 "Server 2022 (ou_ransomware_server2022) and Windows Server 2019 (alihadi_threatsim_server2019), "
                 "and on none of the six Windows 10, 11 and 8.1 SRUDB.dat files tested; a SRUDB.dat without it "
                 "gives this artifact no rows. Eric Zimmerman's SrumECmd reads the same table (EricZimmerman/Srum,"
                 " SrumData/Srum.cs, commit 46fb4e9611c33fdc96236e79d0075db9090bd91c), naming it after its columns"
                 " and describing what the providers measure as not documented. A row is a value the provider "
                 "recorded, not a user action. AppId Entry held a GUID followed by a tab and 0 on every row. "
                 "Size In Bytes (as stored) held one value on all 3,005 rows of ou_ransomware_server2022 (53,687,091,200, which "
                 "is 50 times 2 to the 30th) and two values on the 21 rows of alihadi_threatsim_server2019 (40 and"
                 " 60 times 2 to the 30th).",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "hard-drive",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 3005 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no such table)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no such table)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no such table)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no such table)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 0 rows (no such table)",
        },
    },
    "srumSdpVolume": {
        "name": "SRUM SDP Volume",
        "description": "Entries of the SDP Volume Provider table in SRUDB.dat, as found on Windows Server images: the entry time, the SruDbIdMapTable value its AppId names and its Total and Used values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {17F4D97B-F26A-5E79-3A82-90040A47D13D}. On ou_ransomware_server2022 and"
                 " alihadi_threatsim_server2019 the key of that GUID under SOFTWARE\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\SRUM\\Extensions is named SDP Volume Provider with the DLL sdprov.dll. Each row"
                 " is one entry of the table. AppId Entry is the SruDbIdMapTable value the row's AppId names, "
                 "decoded as text as for the Application column of the other SRUM artifacts; it is blank when the "
                 "id is absent from the map or maps to an entry with no IdBlob. The table's UserId held 2 on every row of both tested images, and "
                 "that id maps to an entry with no IdBlob, so no user is shown. The value columns are the table's "
                 "columns of those names as stored (64-bit integers, ESE column type LongLong); no source for "
                 "their meaning or unit was read, so they are not converted, and what the provider measures is not"
                 " established. Timestamp (UTC) is the entry's TimeStamp column decoded as an OLE automation date "
                 "(days since 1899-12-30). Read from SRUDB.dat, named in Source File, with the ESE reader adapted "
                 "from impacket in scripts/vendor, the same way as the SRUM Network Usage artifact, whose notes "
                 "say how deleted records, values stored apart, a file cut short and a file in dirty shutdown are "
                 "handled. The table is present on the two server images tested, Windows Server 2022 "
                 "(ou_ransomware_server2022) and Windows Server 2019 (alihadi_threatsim_server2019), and on none "
                 "of the six Windows 10, 11 and 8.1 SRUDB.dat files tested; a SRUDB.dat without it gives this "
                 "artifact no rows. Eric Zimmerman's SrumECmd reads the same table (EricZimmerman/Srum, "
                 "SrumData/Srum.cs, commit 46fb4e9611c33fdc96236e79d0075db9090bd91c), naming it after its columns "
                 "and describing what the providers measure as not documented. A row is a value the provider "
                 "recorded, not a user action. AppId Entry held tab-separated text beginning with a GUID-shaped "
                 "value, with a drive letter (C) in one entry and the label System Reserved in another on each "
                 "image, and on ou_ransomware_server2022 a third entry with neither; the fields are shown as stored and not split. Used was not larger than Total on any of "
                 "the 9,015 and 42 rows. Total held three values on ou_ransomware_server2022 and two on "
                 "alihadi_threatsim_server2019, one per AppId.",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "database",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 9015 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 42 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no such table)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no such table)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no such table)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no such table)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 0 rows (no such table)",
        },
    },
    "srumSdpNetwork": {
        "name": "SRUM SDP Network",
        "description": "Entries of the SDP Network Provider table in SRUDB.dat, as found on Windows Server images: the entry time, the SruDbIdMapTable value its AppId names and its BytesInBound, BytesOutBound and BytesTotal values as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-24",
        "last_update_date": "2026-10-24",
        "requirements": "none (vendored ESE reader)",
        "category": "Windows",
        "notes": "Rows from the SRUM table {EEE2F477-0659-5C47-EF03-6D6BEFD441B3}. On ou_ransomware_server2022 and"
                 " alihadi_threatsim_server2019 the key of that GUID under SOFTWARE\\Microsoft\\Windows "
                 "NT\\CurrentVersion\\SRUM\\Extensions is named SDP Network Provider with the DLL sdprov.dll. Each "
                 "row is one entry of the table. AppId Entry is the SruDbIdMapTable value the row's AppId names, "
                 "decoded as text as for the Application column of the other SRUM artifacts; it is blank when the "
                 "id is absent from the map or maps to an entry with no IdBlob. The table's UserId held 2 on every row of both tested images, and "
                 "that id maps to an entry with no IdBlob, so no user is shown. The value columns are the table's "
                 "columns of those names as stored (64-bit integers, ESE column type LongLong); no source for "
                 "their meaning or unit was read, so they are not converted, and what the provider measures is not"
                 " established. Timestamp (UTC) is the entry's TimeStamp column decoded as an OLE automation date "
                 "(days since 1899-12-30). Read from SRUDB.dat, named in Source File, with the ESE reader adapted "
                 "from impacket in scripts/vendor, the same way as the SRUM Network Usage artifact, whose notes "
                 "say how deleted records, values stored apart, a file cut short and a file in dirty shutdown are "
                 "handled. The table is present on the two server images tested, Windows Server 2022 "
                 "(ou_ransomware_server2022) and Windows Server 2019 (alihadi_threatsim_server2019), and on none "
                 "of the six Windows 10, 11 and 8.1 SRUDB.dat files tested; a SRUDB.dat without it gives this "
                 "artifact no rows. Eric Zimmerman's SrumECmd reads the same table (EricZimmerman/Srum, "
                 "SrumData/Srum.cs, commit 46fb4e9611c33fdc96236e79d0075db9090bd91c), naming it after its columns "
                 "and describing what the providers measure as not documented. A row is a value the provider "
                 "recorded, not a user action. AppId Entry held a GUID in braces, a network adapter description "
                 "and a number, separated by backslashes, as stored. The values do not behave as byte counts: "
                 "BytesTotal equalled BytesInBound plus BytesOutBound on 2 of the 3,004 rows of "
                 "ou_ransomware_server2022 and none of the 21 of alihadi_threatsim_server2019, was smaller than "
                 "one of the two on 371 and 9 rows, and the values exceed 4.6 times 10 to the 18th. dissect.esedb "
                 "3.18 read the same values on every row of the four SDP tables on both images, so they are as "
                 "stored and not a decoding error here. They are shown as text.",
        "paths": ("*/Windows/System32/sru/SRUDB.dat", "*/Windows/System32/sru/*.log"),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "ou_ransomware_server2022": "Windows Server 2022 Standard (build 20348) | 3004 rows",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard (build 17763) | 21 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no such table)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no such table)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no such table)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no such table)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise (build 9600) | 0 rows (no such table)",
            "windows11_arm_srum_live_20261024": "Windows 11 25H2 (build 26200), live capture | 0 rows (no such table)",
        },
    },
}


def _norm_row(row):
    """impacket returns column-name keys as bytes; decode them to str."""
    out = {}
    for key, value in row.items():
        name = key.decode("latin-1") if isinstance(key, (bytes, bytearray)) else key
        out[name] = value
    return out


def _unhex(blob):
    """impacket returns binary columns as ASCII hex bytes; recover the raw bytes."""
    if blob is None:
        return None
    if isinstance(blob, (bytes, bytearray)):
        try:
            return binascii.unhexlify(blob)
        except (binascii.Error, ValueError):
            return bytes(blob)
    return None


def _fmt_sid(raw):
    """Format a binary Windows SID as S-1-<authority>-<sub>-<sub>..."""
    if not raw or len(raw) < 8:
        return ""
    revision = raw[0]
    subauth_count = raw[1]
    authority = int.from_bytes(raw[2:8], "big")
    subs = []
    offset = 8
    for _ in range(subauth_count):
        if offset + 4 > len(raw):
            break
        subs.append(struct.unpack("<I", raw[offset:offset + 4])[0])
        offset += 4
    return "S-%d-%d%s" % (revision, authority, "".join("-%d" % s for s in subs))


def _decode_idblob(blob, id_type):
    raw = _unhex(blob)
    if raw is None:
        return ""
    if id_type == 3:  # user SID
        return _fmt_sid(raw)
    return raw.decode("utf-16-le", "replace").rstrip("\x00")


def _build_idmap(database, label, relative_source):
    """Map SruDbIdMapTable's IdIndex to its resolved application id or user SID."""
    idmap = {}
    walk = ese_rows.TableRows(database, _IDMAP, long_value_columns={"IdBlob"})
    for row in walk:
        row = _norm_row(row)
        idmap[row.get("IdIndex")] = _decode_idblob(row.get("IdBlob"),
                                                    row.get("IdType"))
    if not walk.found:
        logfunc(f"{label}: {relative_source} has no {_IDMAP}, so Application and "
                "User are left blank")
    elif walk.summary():
        logfunc(f"{label}: {relative_source}, {walk.summary()}")
    return idmap


def _ole_datetime(value):
    """SRUM TimeStamp: an OLE automation date (days since 1899-12-30) stored as a
    float64, which the ESE reader returns as its raw 8-byte integer."""
    if value is None:
        return ""
    try:
        packed = struct.pack("<Q", int(value) & 0xFFFFFFFFFFFFFFFF)
        days = struct.unpack("<d", packed)[0]
        return datetime(1899, 12, 30, tzinfo=timezone.utc) + timedelta(days=days)
    except (struct.error, OverflowError, ValueError, OSError):
        return ""


def _filetime_datetime(value):
    """A Windows FILETIME: 100-nanosecond intervals since 1601-01-01 UTC."""
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=int(value) / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _srudb_sources(context):
    return [str(f) for f in context.get_files_found()
            if os.path.basename(str(f)).lower() == _SRUDB]


def _cell(value):
    """Present a missing numeric value as blank, otherwise the value itself."""
    return "" if value is None else value


# What each SRUDB.dat read as, by path, size and modification time: (the replayed bytes, or None
# for the file as stored, and the replay's summary). The artifacts read the same file, so it is
# replayed once.
_REPLAYED = {}


def _open(source, label, relative_source):
    """SRUDB.dat as ESE's recovery would leave it: a file in dirty shutdown is replayed in memory
    from the logs beside it (scripts/ese_recovery); when that is refused it is read as stored and
    the reason is logged. The files are only read."""
    stat = os.stat(source)
    key = (source, stat.st_size, stat.st_mtime_ns)
    if key not in _REPLAYED:
        try:
            data, summary = ese_recovery.replayed_database(source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            data, summary = None, f'not replayed: {type(exc).__name__}: {exc}'
        replayed = data is not None and summary.startswith('replayed')
        _REPLAYED[key] = (data if replayed else None, summary)
    data, summary = _REPLAYED[key]
    if data is not None or 'clean shutdown' not in summary:
        logfunc(f"{label}: {relative_source}, {summary}" + ('' if data is not None else '; read as stored'))
    return ese_rows.ESEDatabase(source, data=data) if data is not None else ese_rows.ESEDatabase(source)


def _read_table(source, guid, row_builder, label, relative_source):
    """Open SRUDB.dat, build the id map, and build a row per entry of one table."""
    database = _open(source, label, relative_source)
    try:
        database.mountDB()
        idmap = _build_idmap(database, label, relative_source)
        rows = []
        walk = ese_rows.TableRows(database, guid, long_value_columns=())
        for row in walk:
            rows.append(row_builder(_norm_row(row), idmap))
        if not walk.found:
            logfunc(f"{label}: {relative_source} has no {guid} table, so it holds "
                    "no rows for this SRUM provider")
        elif walk.summary():
            logfunc(f"{label}: {relative_source}, {walk.summary()}")
        return rows
    finally:
        database.close()


def _run(context, guid, headers, row_builder, label):
    data_list = []
    sources = []
    if impacket_ese is None:
        logfunc(f"{label}: the vendored ESE reader is not available")
        return headers, data_list, ""
    for source in _srudb_sources(context):
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            rows = _read_table(source, guid, row_builder, label, relative_source)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"{label}: could not read {relative_source}: {exc}")
            continue
        for row in rows:
            data_list.append(row + (relative_source,))
            rows_here += 1
        if rows_here:
            sources.append(source)
    return headers, data_list, "\n".join(sources)


@artifact_processor
def srumNetworkUsage(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               'Interface LUID', 'L2 Profile ID', 'Bytes Sent', 'Bytes Received',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _cell(row.get('InterfaceLuid')),
                _cell(row.get('L2ProfileId')),
                _cell(row.get('BytesSent')),
                _cell(row.get('BytesRecvd')))

    return _run(context, _NETWORK_USAGE, headers, build, "SRUM Network Usage")


@artifact_processor
def srumApplicationResourceUsage(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               'Foreground Bytes Read', 'Foreground Bytes Written',
               'Background Bytes Read', 'Background Bytes Written',
               'Foreground Cycle Time', 'Background Cycle Time', 'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _cell(row.get('ForegroundBytesRead')),
                _cell(row.get('ForegroundBytesWritten')),
                _cell(row.get('BackgroundBytesRead')),
                _cell(row.get('BackgroundBytesWritten')),
                _cell(row.get('ForegroundCycleTime')),
                _cell(row.get('BackgroundCycleTime')))

    return _run(context, _APP_RESOURCE, headers, build,
                "SRUM Application Resource Usage")


@artifact_processor
def srumNetworkConnections(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Interface LUID', 'L2 Profile ID',
               ('Connect Start Time (UTC)', 'datetime'), 'Connected Time',
               'Source File')

    def build(row, _idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                _cell(row.get('InterfaceLuid')),
                _cell(row.get('L2ProfileId')),
                _filetime_datetime(row.get('ConnectStartTime')),
                _cell(row.get('ConnectedTime')))

    return _run(context, _NETWORK_CONNECTIONS, headers, build,
                "SRUM Network Connections")


@artifact_processor
def srumExecutionStats(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               ('End Time (UTC)', 'datetime'), 'Duration (ms)', 'Span (ms)',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _filetime_datetime(row.get('EndTime')),
                _cell(row.get('DurationMS')),
                _cell(row.get('SpanMS')))

    return _run(context, _EXECUTION, headers, build, "SRUM Execution Stats")


def _text(value):
    """An identifier as text: a 64-bit hash can be larger than the report database's integers hold."""
    return "" if value is None else str(value)


@artifact_processor
def srumWpnNotifications(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'Application', 'User SID',
               'Notification Type', 'Payload Size', 'Network Type', 'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                idmap.get(row.get('UserId'), ''),
                _cell(row.get('NotificationType')),
                _cell(row.get('PayloadSize')),
                _cell(row.get('NetworkType')))

    return _run(context, _WPN, headers, build, "SRUM WPN Notifications")


@artifact_processor
def srumEnergyUsage(context):
    headers = (('Event Time (UTC)', 'datetime'), ('Timestamp (UTC)', 'datetime'),
               'State Transition', 'Charge Level', 'Full Charged Capacity',
               'Designed Capacity', 'Cycle Count', 'Battery Count',
               'Battery Charge Limited', 'Configuration Hash', 'Source File')

    def build(row, _idmap):
        return (_filetime_datetime(row.get('EventTimestamp')),
                _ole_datetime(row.get('TimeStamp')),
                _cell(row.get('StateTransition')),
                _cell(row.get('ChargeLevel')),
                _cell(row.get('FullChargedCapacity')),
                _cell(row.get('DesignedCapacity')),
                _cell(row.get('CycleCount')),
                _cell(row.get('BatteryCount')),
                _cell(row.get('BatteryChargeLimited')),
                _text(row.get('ConfigurationHash')))

    return _run(context, _ENERGY_USAGE, headers, build, "SRUM Energy Usage")


@artifact_processor
def srumSdpCpu(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'AppId Entry', 'Processor Time (as stored)',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                _cell(row.get('ProcessorTime')))

    return _run(context, _SDP_CPU, headers, build, "SRUM SDP Cpu")


@artifact_processor
def srumSdpPhysicalDisk(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'AppId Entry', 'Size In Bytes (as stored)',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                _text(row.get('SizeInBytes')))

    return _run(context, _SDP_PHYSICAL_DISK, headers, build, "SRUM SDP Physical Disk")


@artifact_processor
def srumSdpVolume(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'AppId Entry', 'Total (as stored)', 'Used (as stored)',
               'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                _text(row.get('Total')),
                _text(row.get('Used')))

    return _run(context, _SDP_VOLUME, headers, build, "SRUM SDP Volume")


@artifact_processor
def srumSdpNetwork(context):
    headers = (('Timestamp (UTC)', 'datetime'), 'AppId Entry', 'Bytes In Bound (as stored)',
               'Bytes Out Bound (as stored)', 'Bytes Total (as stored)', 'Source File')

    def build(row, idmap):
        return (_ole_datetime(row.get('TimeStamp')),
                idmap.get(row.get('AppId'), ''),
                _text(row.get('BytesInBound')),
                _text(row.get('BytesOutBound')),
                _text(row.get('BytesTotal')))

    return _run(context, _SDP_NETWORK, headers, build, "SRUM SDP Network")

