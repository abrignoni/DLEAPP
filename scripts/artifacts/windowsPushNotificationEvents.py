"""Push Notification Platform event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-PushNotifications-Platform record of the PushNotification-Platform Operational event
log: applications registered and unregistered for notifications, toast and tile sessions and deliveries, the
connection to the Windows Push Notification Service and the commands sent and received over it. The Event IDs, the
message text and the field names are sourced in the notes.
"""

import base64
import re

from scripts.ilapfuncs import artifact_processor
from scripts.windows_evtx import read_event_records

_LABEL = 'Push Notification Platform Events'
_LOG = 'Microsoft-Windows-PushNotification-Platform%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-PushNotifications-Platform'

# The two spellings of the application field (no manifest entry holds both) and the three other fields with a
# column of their own; every other field goes to Other Fields.
_APP = ('AppUserModelId', 'AppUserModelID')
_PACKAGE = 'PackageFullName'
_PROCESS = 'ProcessName'
_PAYLOAD = 'Payload'

# Base64 in its padded form: groups of four characters, the last one padded with = when it stands for one or two
# bytes. Python versions differ on what b64decode accepts beyond this, so the form is tested here.
_BASE64 = re.compile(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?')

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '19': 'The Windows Push Notification Platform has encountered an error in File: %1, Function %2, Line '
          '%3, Error %4, ErrorMessage %5.',
    '20': 'The Windows Push Notification Platform has encountered error %2 opening file %1.',
    '37': 'The Windows Push Notification Platform is required to connect on startup, ValidChannelsExist : %1.',
    '42': 'Cloud Notifications must be enabled in GP and MDM to receive push notifications.',
    '1003': 'Connect request sent to the Connection Provider.',
    '1004': 'Disconnect request sent the Connection Provider.',
    '1005': 'The Connection Provider status changed to %1.',
    '1006': 'Sending a channel request to the Connection Provider with parameters: %1 [PackageFullName] %2 '
            '[Properties] %3 [Cookie] %4 [TransactionId].',
    '1007': 'The Connection Provider completed the channel request for transaction id %1.',
    '1008': 'Sending a channel revoke request to the Connection Provider for channel id %1.',
    '1010': '%1 received for ChannelId %2 and AppUserModelId %3 with TrackingId %4, X-WNS-MSG-ID %5, '
            'timestamp %6 and expiration %7 tag: %8, group: %9, action: %10, bundle: '
            'count=%11;missed=%12;Id=%13.',
    '1011': 'Sending a request to the Connection Provider to renew a channel with parameters: %1 [ChannelId] '
            '%2 [PackageFullName] %3 [Properties] %4 [Cookie] %5 [TransactionId].',
    '1013': 'Configuring notification delivery for AppUserModelId %4 with channel id %1.',
    '1015': 'Configuring notification policy for %1 [NotificationType] %2 [Enabled].',
    '1020': 'The Connection Provider status changed to a failure state: %1.',
    '1021': 'The Connection Manager has failed to connect: %1.',
    '1022': 'ConnectWork is requesting ConnectionManager to connect.',
    '1023': 'No internet connection available, %1 is queued for next network status change.',
    '1024': 'Internet connection status changed to %1, submitting pending workitems: count = %2.',
    '1025': 'A Power event was fired: %1 [PowerEventType] %2 [Enabled].',
    '1113': 'Device Compact Ticket request completed with Device Id %1 for the %2.',
    '1116': 'Device Compact Ticket request failed with error %1 for the %2.',
    '1117': 'Windows Push Notification Service was disconnected due to error: %1 and will now enter reconnect mode.',
    '1205': 'WNP Transport Layer Disconnect call initiated for the %1.',
    '1206': 'WNP Transport Layer Disconnect call completed for the %1.',
    '1207': 'WNP Transport Layer resolving DNS initiated for host %2 for the %1.',
    '1208': 'WNP Transport Layer resolving DNS completed for the %1 with code %2.',
    '1211': 'WNP Transport Layer initial server connection initiated to server %2 on port %3 for the %1.',
    '1212': 'WNP Transport Layer initial server connection completed to server %2 on port %3 for the %1.',
    '1213': 'WNP Transport Layer proxy connection initiated for the %1.',
    '1214': 'WNP Transport Layer proxy connection completed to server %2 for the %1.',
    '1215': 'WNP Transport Layer proxy negotiation initiated for the %1.',
    '1216': 'WNP Transport Layer proxy negotiation completed for the %1.',
    '1217': 'WNP Transport Layer TLS negotiation initiated for the %1.',
    '1218': 'WNP Transport Layer TLS negotiation completed for the %1 with code %2.',
    '1223': 'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes of '
            'payload: %6.',
    '1224': 'WNP Transport Layer received %1 bytes of payload: %2.',
    '1225': 'WNP Transport Layer received command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes '
            'of payload: %6.',
    '1226': 'WNP Transport Layer received proxy server response for the %3 of %1 bytes with payload: %2.',
    '1227': 'WNP Transport Layer received command when disconnected with Verb: %1, Trid: %2, Namespace: %3, '
            'CV: %4 containing %5 bytes of payload: %6.',
    '1233': 'Fast reconnect triggered for previous WNS session (%1) on the %3.',
    '1238': 'WNP Keep Alive Detector starting Test Connection',
    '1239': 'WNP Keep Alive Detector starting KA measurement with value: %2 seconds; type: %1; Min Limit: %3 seconds',
    '1240': 'WNP Keep Alive Detector stopping KA measurement',
    '1241': 'WNP Keep Alive Detector lost network over %1.',
    '1242': 'WNP Transport Layer received Power Management event with type %1 on the %2.',
    '1244': 'Connection to the Windows Push Notification Service (%1:%2) failed because proxy host detected '
            '(%3) could not be used to establish the connection.',
    '1246': 'WNP Transport Layer was disconnected from the Windows Push Notification Service due to a loss '
            'of network connectivity.',
    '1252': 'The KA value has converged.',
    '1254': 'WNP Transport Layer for %1 detected preferred interface change.',
    '1255': 'WNP Transport Layer for %1 reacting to preferred interface change, disconnect and immediately '
            'reconnect.',
    '1256': 'WNP Transport Layer for %1 reacting to preferred interface change, immediately reconnect.',
    '1257': 'WNP Transport Layer for %1 called InitializeSecurityContext and got return code %2.',
    '1258': 'WNP Transport Layer for %1 received asynchronous connection error %2.',
    '1259': 'WNP Transport Layer for the Data Connection sending out of band keep alive (PNG) request.',
    '1260': 'WNP Transport Layer for the Data Connection received cellular state change WNF event.',
    '1261': 'Adding new user to the Windows Push Notification Service.',
    '1262': 'Removing existing user from the Windows Push Notification Service.',
    '1263': 'Replacing existing user from the Windows Push Notification Service.',
    '1264': 'Adding new user to the Windows Push Notification Service completed.',
    '1265': 'Removing existing user from the Windows Push Notification Service completed.',
    '1266': 'Replacing existing user from the Windows Push Notification Service completed.',
    '1267': 'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes of '
            'payload only.',
    '1268': 'WNP Transport Layer received command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes '
            'of payload only.',
    '1310': 'WNP Transport Layer for %1 detected first fallback interface change.',
    '1311': 'WNP Transport Layer for %1 detected second fallback interface change.',
    '1312': 'WNP Transport Layer detected low WIFI signal quality level (value = %1); and hence sending out '
            'of band keep alive (PNG) request.',
    '1313': 'WNP Transport Layer detected a significant drop in WIFI signal quality (delta = %1); and hence '
            'sending out of band keep alive (PNG) request.',
    '1314': 'WNP Transport Layer detected a change in WIFI interface availability (event %1); and hence '
            'sending out of band keep alive (PNG) request.',
    '1315': 'WNP Transport Layer detected a change in WIFI interface connectivity status (event %1); and '
            'hence sending out of band keep alive (PNG) request.',
    '2001': 'The channel table has added a valid channel mapping: %1 [ChannelId] %2 [AppUserModelId] %3 [ErrorCode].',
    '2002': 'The channel table has removed a channel mapping: %1 [ChannelId] %2 [AppUserModelId] %3 [ErrorCode].',
    '2003': 'The channel table has updated a channel mapping: %1 [ChannelId] %2 [AppUserModelId] %3 [ErrorCode].',
    '2033': 'A raw notification has activated a background task: %1 [AppUserModelID] %2 [EventId] %3 '
            '[NotificationID].',
    '2053': 'A periodic update has failed polling URL because X-WNS-GROUP header is invalid: %1 '
            '[AppUserModelId] %2 [Type] %3 [URL].',
    '2171': 'A call to the settings endpoint happened to unblock all channels for all types.',
    '2413': 'An application was registered with the following parameters: %1 [PackageFullName] %2 '
            '[AppUserModelId] %3 [Settings] %4 [AppType] %5 [ErrorCode].',
    '2414': 'An application resgistration was updated with the following parameters: %1 [PackageFullName] %2 '
            '[AppUserModelId] %3 [Settings] %4 [AppType] %5 [ErrorCode].',
    '2415': 'An application was unregistered with the following parameters: %1 [AppUserModelId] %2 [ErrorCode]',
    '3000': 'Tile session creation is requested for %2 endpoint %1.',
    '3001': 'Tile session creation is finished for %4 from endpoint %1 with result %3, and %2 is assigned as '
            'session id.',
    '3004': 'Tile session %1 is being closed',
    '3005': 'Tile session %1 is closed with error code %2.',
    '3006': 'Toast session creation is requested for %2 from endpoint %1.',
    '3007': 'Toast session creation is finished for %4 from endpoint %1 with result %3, and %2 is assigned '
            'as session id.',
    '3008': 'Toast session %1 is being closed',
    '3009': 'Toast session %1 is closed with error code %2.',
    '3049': 'Endpoint %1 is being cleanedup',
    '3052': 'Toast with notification tracking id %1 is being delivered to %2 on session %3.',
    '3053': '%1 with notification tracking id %2 is being delivered to %3.',
    '3054': 'Toast with notification tracking id %1 is canceled by %2 - informed session %3.',
    '3055': 'Some toast notifications have been cleared - informed session %1.',
    '3056': '%1 are being cleared for %2 - informed session %3.',
    '3057': 'Presentation Endpoint received a call to close session %1.',
    '3058': 'Presentation Endpoint ended a call to close session %1.',
    '3110': 'Toast Notification Forwarding Global Settings: isFwToCdpEnabled = %1 '
            'isMirrorMasterSwitchEnabled = %2 MirroringDisabled = %3',
    '3111': 'Start Toast Notification Forwarding activity',
    '3112': 'Stop Toast Notification Forwarding activity',
    '3113': 'Toast Notification Forwarding Local Settings: isDeveloperAppMirroringEnabled = %1 '
            'isMirrorMasterSwitchEnabled = %2 isGroupPolicyEnabled = %3',
    '3114': 'Start Toast Notification Forwarding Do Forward To AFC',
    '3115': 'Stop Toast Notification Forwarding Do Forward To AFC',
    '3116': 'Start Toast Notification Forwarding Make Activity from Notification',
    '3117': 'Stop Toast Notification Forwarding Make Activity from Notification',
    '3118': 'Toast Notification Forwarding Finished Decorating Payload',
    '3119': 'Toast Notification Forwarding Finished Loading Payload onto Activity',
    '3120': 'Toast Notification Forwarding Finished setting attributes onto activity',
    '3121': 'Start Toast Notification Forwarding Asset Resolution',
    '3122': 'Toast Notification Forwarding Asset Resolution Successful',
    '3123': 'Toast Notification Forwarding Making Activity TrackingId = %1 AppUserModelId = %2',
    '3124': 'Toast Notification Forwarding Published Activity with Result = %1',
    '3125': '%1',
    '3126': 'Sync Dismiss: Dismiss Activities for App Start',
    '3127': 'Sync Dismiss: Dismiss Activities for App Stop',
    '3128': 'Sync Dismiss: Dismiss Activities Start',
    '3129': 'Sync Dismiss: Dismiss Activities Stop',
    '3130': 'Sync Dismiss: Dismiss Activities Start',
    '3131': 'Sync Dismiss: Dismiss Activities Stop',
    '3132': 'Sync Dismiss: Remove Notification using Activity Start',
    '3133': 'Sync Dismiss: Remove Notification using Activity Stop',
    '3134': 'Sync Dismiss: Get Activities Start',
    '3135': 'Sync Dismiss: Get Activities Stop',
    '3136': 'Sync Dismiss: CDPGetPlatformDeviceId Start',
    '3137': 'Sync Dismiss: CDPGetPlatformDeviceId Stop',
    '3138': '%1',
    '3139': 'Sync Dismiss Removed Activity with Result = %1',
    '3140': 'Sync Dismiss Removed Notification with Result = %1',
    '3141': 'SyncDismissRemoveNotificationUsingActivityParams: MatchOnNotificationId = %1 NotificationId = '
            '%2 ActivityId = %3',
    '3142': 'Sync Dismiss: Matched Activity using Notification!',
    '3143': 'Sync Dismiss: Matched Notification using Activity!',
    '3144': 'Received WNF_CDP_CDPUSERSVC_READY',
    '3146': '[Sqlite][Warning] Status: %1.',
    '3147': '[Sqlite][Error] Status: %1.',
}

# Event ID: the field names and the text of an earlier manifest's entry that differs from build 26100's in both.
# A record that carries exactly those field names is given that text (see notes).
_EARLIER = {
    '19': (('FileName', 'FunctionName', 'LineNumber', 'ErrorCode'),
           'The Windows Push Notification Platform has encountered an error in file: %1, function %2, line '
           '%3: %4.'),
    '1024': (('WasConnected',),
             'Internet connection status changed to Connected (last known status was %1), submitting pending '
             'workitems.'),
    '1223': (('Verb', 'TrID', 'Namespace', 'Bytes', 'Payload', 'ConnectionType'),
             'WNP Transport Layer sent command for the %6 with Verb: %1, Trid: %2, Namespace: %3 containing '
             '%4 bytes of payload: %5.'),
    '1225': (('Verb', 'TrID', 'Namespace', 'Bytes', 'Payload', 'ConnectionType'),
             'WNP Transport Layer received command for the %6 with Verb: %1, Trid: %2, Namespace: %3 '
             'containing %4 bytes of payload: %5.'),
    '1227': (('Verb', 'TrID', 'Namespace', 'Bytes', 'Payload', 'ConnectionType'),
             'WNP Transport Layer received command when disconnected for the %6 with Verb: %1, Trid: %2, '
             'Namespace: %3 containing %4 bytes of payload: %5.'),
    '1267': (('Verb', 'TrID', 'Namespace', 'Bytes', 'Payload', 'ConnectionType'),
             'WNP Transport Layer sent command for the %6 with Verb: %1, Trid: %2, Namespace: %3 containing '
             '%4 bytes of payload only.'),
    '1268': (('Verb', 'TrID', 'Namespace', 'Bytes', 'Payload', 'ConnectionType'),
             'WNP Transport Layer received command for the %6 with Verb: %1, Trid: %2, Namespace: %3 '
             'containing %4 bytes of payload only.'),
}


__artifacts_v2__ = {
    "pushNotificationPlatformEvents": {
        "name": "Push Notification Platform Events",
        "description": "Microsoft-Windows-PushNotifications-Platform records of the PushNotification-Platform "
                       "Operational event log, such as an application registered or unregistered for notifications, "
                       "a toast being delivered to an application, and commands the WNP Transport Layer sent and "
                       "received, with the application, package, process name and command payload where a record "
                       "carries them, and each record's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-PushNotification-Platform%4Operational.evtx the paths match with "
                 "python-evtx and reports, one row per record, every record whose provider is "
                 "Microsoft-Windows-PushNotifications-Platform, whatever its Event ID. The provider's name and the "
                 "manifests' name for the channel (Microsoft-Windows-PushNotifications-Platform/Operational) have an "
                 "s that the log's file name and the channel the tested records name "
                 "(Microsoft-Windows-PushNotification-Platform/Operational) do not. The provider's manifest of "
                 "Windows 11 build 26100.1742 sends 131 events to this log's channel, each version 0; they sit among "
                 "lines 678 to 6162 of the file, with entries of the provider's other channels between them "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-PushNotifications-Platform.xml#L678-L6162). "
                 "The manifests of Windows 11 build 22621.819 and Windows 10 build 19041.208 hold the same 131, that "
                 "of build 17763.107 those 131 and 1020, and that of build 16299.15 127 of them (not 42, 1025, 3146 "
                 "and 3147) and 1020 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-PushNotifications-Platform.xml#L678-L6160, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-PushNotifications-Platform.xml#L677-L6159, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-PushNotifications-Platform.xml#L662-L6158 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-PushNotifications-Platform.xml#L662-L6080). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. Event is, for the "
                 "record's Event ID, the first sentence of the first line of the build 26100 message (for 1020, of "
                 "the build 17763 message, which the build 16299 one equals): the first line that holds more than "
                 "white space, with each run of white space made one space, cut after the first period that a space "
                 "or the end of the line follows (whole when it has none), with its placeholders (such as %1) as the "
                 "manifest writes them. A placeholder is an insertion string for a data item of the event's template "
                 "by its position (Microsoft's Defining Events page: 'to include the third data item in the "
                 "template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in; 88 of the 131 build 26100 texts hold one. Event is blank for an Event ID "
                 "outside the table, which no tested record had. The manifests of builds 16299 and 17763 word 1024, "
                 "1223, 1225, 1227, 1267 and 1268 differently, and those two and that of build 19041 word 19 "
                 "differently. Where such an earlier entry also gives other field names than build 26100's, a record "
                 "that carries exactly those field names in that order is given the earlier entry's first sentence: "
                 "on the tested logs, the 688 rows of 1024, 1223, 1225, 1267 and 1268 on lonewolf_win10 (build "
                 "16299) and the 1 row of 19 on szechuan_win10 (build 19041). The build 17763 manifest words 1223, "
                 "1225, 1227, 1267 and 1268 the earlier way while giving them the build 26100 fields, so its records "
                 "of those events are given the build 26100 text, as the 62 such rows of af_case2_win10 were. On "
                 "every other tested row Event is the first sentence of the message its own image's build manifest "
                 "gives the event. App User Model ID is the AppUserModelId field, or AppUserModelID, the spelling "
                 "the manifests give 2033 and 2053; no entry holds both, and if a record did, AppUserModelId would "
                 "be shown and the other listed in Other Fields. 920 of the 5,203 tested rows have one, 1 of them "
                 "through AppUserModelID. Package is the PackageFullName field, which the manifests give 1006, 1011, "
                 "2413 and 2414 (570 tested rows have one), and Process Name the ProcessName field, which they give "
                 "3000, 3001, 3006 and 3007. On each of the 224 tested rows that have a Process Name it is a full "
                 "path ending .exe; compared without case the file names are explorer.exe on 68 rows, svchost.exe on "
                 "52, runtimebroker.exe on 50, shellexperiencehost.exe on 34 and startmenuexperiencehost.exe on 20. "
                 "2413, whose message begins 'An application was registered with the following parameters', occurs "
                 "on 519 tested rows over three images and 2415 ('An application was unregistered with the following "
                 "parameters') on 181 over four; 3052 ('Toast with notification tracking id %1 is being delivered to "
                 "%2 on session %3.') on 43 and 3053 ('%1 with notification tracking id %2 is being delivered to "
                 "%3.') on 54, each over four images. Payload is the Payload field, a win:Binary field in the "
                 "manifests' 1223 to 1227, 1267 and 1268, which python-evtx renders as Base64 text "
                 "(https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/Nodes.py#L1339-L1360). "
                 "The column shows the bytes that text stands for: each byte from space to tilde as that character, "
                 "except the backslash, and every other byte, the backslash included, as \\x followed by two "
                 "lower-case hexadecimal digits, so the bytes can be read back exactly. A value not in padded Base64 "
                 "form is shown as stored; no tested value was. On each of the 1,607 tested rows that have a Payload "
                 "its byte count equals the record's Bytes field, and each holds at least one byte written as \\x "
                 "with two digits. The Verb field of those rows held one of ACK, ATH, BND, CNT, GET, NFY, OUT, PNG, "
                 "PUT, UBD, XFR and 911; what the commands and their payloads stand for is not established here. "
                 "Other Fields lists every other named field that holds more than white space as 'name: value', in "
                 "the record's order, joined with ' | '. Each value, here and in App User Model ID, Package, Process "
                 "Name and Payload, is as python-evtx renders it with any white space at either end removed; no "
                 "tested value had any. A data item that has no name is not shown, and no tested record had one. If "
                 "a record named a field twice the last would be read. The tested records carried the field names "
                 "their image's build manifest gives the event. Tested on the logs of four public images "
                 "(af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; "
                 "szechuan_win10, build 19041), which gave 848, 1,546, 1,670 and 1,139 rows in that order; the two "
                 "captures of a Windows 11 build 26200 machine hold no such log. 71 of the 132 Event IDs in the "
                 "table occur, 30 of them on all four images and 14 on one image only. The other 61 Event IDs are "
                 "unexercised. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "scripts/windows_evtx.py renders from the FILETIME the record stores with integer arithmetic, "
                 "counted in UTC and cut to whole microseconds, in place of python-evtx 0.8.1's conversion through a "
                 "floating-point number, which can differ by microseconds ("
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on 2,971 tested rows and an "
                 "S-1-5-21 account on 2,232. Record ID is the record's EventRecordID and Computer the machine name "
                 "the record stores, which held one value on af_case2_win10, lonewolf_win10 and pc_mus_001_win11 and "
                 "two on szechuan_win10. Rows are in the order the file holds them. Record ID rises from row to row "
                 "except at one row each on lonewolf_win10 and pc_mus_001_win11, where it falls; in time order 3 "
                 "rows are earlier than the row before them (1 each on lonewolf_win10, pc_mus_001_win11 and "
                 "szechuan_win10). Every record of the tested logs rendered and is the provider's. A record "
                 "python-evtx cannot render, or whose XML does not parse, is counted in the run log and not "
                 "reported. A log marked dirty is read past the chunks its header counts, and the run log says how "
                 "many records came from there. Reading needs the python-evtx package (pip install python-evtx). Not "
                 "read: the events these manifests send to the provider's Admin and Debug channels.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-PushNotification-Platform%4Operational.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "bell",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 848 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1546 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1670 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 1139 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


def event_text(record):
    names, text = _EARLIER.get(record.event_id, ((), ''))
    if text and tuple(record.fields) == names:
        return text
    return _EVENTS.get(record.event_id, '')


def payload_text(value):
    """The bytes of a Base64 value as text: space to tilde as written (the backslash excepted), any other byte as
    \\xNN. A value that is not Base64 is returned as it is."""
    if not _BASE64.fullmatch(value):
        return value
    data = base64.b64decode(value)
    return ''.join(chr(byte) if 32 <= byte < 127 and byte != 92 else f'\\x{byte:02x}' for byte in data)


def push_notification_row(record):
    app = next((name for name in _APP if name in record.fields), '')
    other = ' | '.join(f'{name}: {record.get(name)}' for name in record.fields
                       if name not in (app, _PACKAGE, _PROCESS, _PAYLOAD) and record.get(name))
    return (record.time, record.event_id, event_text(record), record.get(app), record.get(_PACKAGE),
            record.get(_PROCESS), other, payload_text(record.get(_PAYLOAD)), record.user_sid, record.record_id,
            record.computer)


@artifact_processor
def pushNotificationPlatformEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'App User Model ID', 'Package',
                    'Process Name', 'Other Fields', 'Payload', 'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    data_list = [push_notification_row(record) for record in records]
    return data_headers, data_list, '\n'.join(sources)
