"""Windows Wifi.etl (WLAN trace session log) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads Windows\\System32\\LogFiles\\WMI\\Wifi.etl with scripts/etl.py and reports two kinds of manifest event
from it: the visible networks WLAN AutoConfig records after a scan, and the connection, disconnection and
association events of WLAN AutoConfig and the NWiFi driver. The event layouts are the provider templates of
Windows 11 build 26200, sourced in the notes.
"""

__artifacts_v2__ = {
    "windowsWifiEtlVisibleNetworks": {
        "name": "Wi-Fi Visible Networks (Wifi.etl)",
        "description": "Each visible network WLAN AutoConfig recorded in the Wifi.etl trace log, with its SSID, BSSID "
                       "count, authentication and cipher algorithm IDs and RSSI value, as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Windows Network",
        "notes": ('Reads Windows\\System32\\LogFiles\\WMI\\Wifi.etl, the file the trace session writes, with '
                  'scripts/etl.py, which names the source of each layout it reads: the buffer and record headers '
                  "(Geoff Chappell's pages on WMI_BUFFER_HEADER and the trace headers), and Microsoft's "
                  'EVENT_HEADER, EVENT_DESCRIPTOR and TRACE_LOGFILE_HEADER. One row per WLAN AutoConfig event 20025'
                  ' (provider Microsoft-Windows-WLAN-AutoConfig, 9580d7dd-0379-4658-9870-d5be7d52d6de), whose '
                  "message is 'Visible Network: %1, %2 BSSIDS, %3/%4, %5 RSSI'; its template gives Ssid "
                  '(UnicodeString), BssidCount, AuthAlgoId, CipherAlgoId and Rssi (each UInt32). A network the '
                  'trace records on several scans has a row per event. Event layouts: the provider templates '
                  'Windows 11 build 26200 gives through its provider metadata (Get-WinEvent -ListProvider; '
                  'wlansvc.dll 10.0.26100.9549, nwifi.sys 10.0.26100.1), for version 0 of each event; an event of '
                  'another version is counted in the run log and not decoded. On the corpus files every event '
                  'decoded was version 0, used exactly the bytes its template gives, and decoded to the same values'
                  " as the properties Get-WinEvent returned for it. Times: each event's own time stamp, converted "
                  'the way that module states (StartTime plus the counter difference scaled by a floating-point '
                  'multiply and truncated), which gave the same time to the 100 ns as Get-WinEvent on Windows 11 '
                  'build 26200 for every event of the corpus files below that Get-WinEvent returned; the report '
                  'shows microseconds. The same connection events (WLAN AutoConfig 8001 and 8003) are also in the '
                  'WLAN-AutoConfig Operational log, which WLAN Connection Events reads: on pc_mus_001_win11 the '
                  'first 8001 was 3 microseconds apart in the two logs, and an 8003 and 8001 about 36 hours later '
                  'were 18.0 seconds later in Wifi.etl than in the Operational log. Which of the two times is '
                  'closer to the real time is not established. Authentication Algorithm (DOT11 name) and Cipher '
                  'Algorithm (DOT11 name) are the names Microsoft gives the value in DOT11_AUTH_ALGORITHM '
                  '(https://learn.microsoft.com/en-us/windows/win32/nativewifi/dot11-auth-algorithm) and '
                  'DOT11_CIPHER_ALGORITHM '
                  '(https://learn.microsoft.com/en-us/windows/win32/nativewifi/dot11-cipher-algorithm), blank for a'
                  ' value those pages do not list. The template does not name the enumeration; on the tested files '
                  "the values present were 1, 6 and 7 (authentication) and 0 and 4 (cipher), and Windows' own "
                  'message text for them read Open, RSNA, RSNA PSK, NONE and CCMP, which agree with those names. '
                  'RSSI (as stored) is the unsigned 32-bit value the template declares; the values as stored lay '
                  'between 4294967202 and 4294967257. SSID (as stored) held an empty string on 23 of 320 rows of '
                  'pc_mus_001_win11 and 118 of 1,606 rows of hexordia_mvs2025_win11. The events do not carry the '
                  'BSSIDs or the interface. Known data: pc_mus_001_win11 gave 320 rows with 65 distinct SSID values'
                  ' over about 1.4 days and hexordia_mvs2025_win11 1,606 rows with 35, 17 of them from the last '
                  'buffer described next. Get-WinEvent returned no event from the last buffer of the lonewolf_win10'
                  ' and hexordia_mvs2025_win11 files, a buffer that ends past the 8 MB maximum file size their '
                  "logfile header records; that buffer's sequence number lay among the other buffers' and its "
                  'records framed like theirs, and it is read. The Wifi.etl files of lonewolf_win10, af_case2_win10'
                  " and szechuan_win10 held no 20025 event. Not read: the trace's other events, including WLAN "
                  'AutoConfig 20024 (a count of networks per scan), and its WPP records (most of each tested file),'
                  ' whose format information is not in the file and which Get-WinEvent did not decode either. '
                  'Wifi.etl is written over in a circle, so it holds a recent window of events, and an empty '
                  'artifact says only that the file held none.'),
        "paths": ("*/Windows/System32/LogFiles/WMI/Wifi.etl",),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 320 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the Wifi.etl holds no 20025 event)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1606 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the Wifi.etl holds no 20025 event)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the Wifi.etl holds no 20025 event)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no member matches the declared paths)",
            "windows11_arm_usn_rewind_known_20261025": "Windows 11 25H2 build 26200 (NTFS test volume) | 0 rows (no member matches the declared paths)",
        },
    },
    "windowsWifiEtlConnections": {
        "name": "Wi-Fi Connection Events (Wifi.etl)",
        "description": "Wireless connection, disconnection and association events from the Wifi.etl trace log, with "
                       "the SSID, profile and association MAC each event stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Windows Network",
        "notes": ('Reads Windows\\System32\\LogFiles\\WMI\\Wifi.etl, the file the trace session writes, with '
                  'scripts/etl.py, which names the source of each layout it reads: the buffer and record headers '
                  "(Geoff Chappell's pages on WMI_BUFFER_HEADER and the trace headers), and Microsoft's "
                  'EVENT_HEADER, EVENT_DESCRIPTOR and TRACE_LOGFILE_HEADER. One row per event of five kinds: WLAN '
                  'AutoConfig (Microsoft-Windows-WLAN-AutoConfig, 9580d7dd-0379-4658-9870-d5be7d52d6de) 8001, 8003 '
                  'and 14045, and NWiFi (Microsoft-Windows-NWiFi, 0bd3506a-9030-4f76-9b88-3e8fe1f7cfb6) 10040 and '
                  "10041. The Event column is shortened from each event's manifest message: 'WLAN AutoConfig "
                  "service has successfully connected to a wireless network.' (8001), '... disconnected from a "
                  "wireless network.' (8003), 'Connection (auto = %4) to %5 (multiple=%6) using profile %3.' "
                  "(14045), 'Association Start: %3' (10040) and 'Association Completion: %3 AssocStatus=%4' "
                  '(10041). Event layouts: the provider templates Windows 11 build 26200 gives through its provider'
                  ' metadata (Get-WinEvent -ListProvider; wlansvc.dll 10.0.26100.9549, nwifi.sys 10.0.26100.1), for'
                  ' version 0 of each event; an event of another version is counted in the run log and not decoded.'
                  ' On the corpus files every event decoded was version 0, used exactly the bytes its template '
                  'gives, and decoded to the same values as the properties Get-WinEvent returned for it. Times: '
                  "each event's own time stamp, converted the way that module states (StartTime plus the counter "
                  'difference scaled by a floating-point multiply and truncated), which gave the same time to the '
                  '100 ns as Get-WinEvent on Windows 11 build 26200 for every event of the corpus files below that '
                  'Get-WinEvent returned; the report shows microseconds. The same connection events (WLAN '
                  'AutoConfig 8001 and 8003) are also in the WLAN-AutoConfig Operational log, which WLAN Connection'
                  ' Events reads: on pc_mus_001_win11 the first 8001 was 3 microseconds apart in the two logs, and '
                  'an 8003 and 8001 about 36 hours later were 18.0 seconds later in Wifi.etl than in the '
                  'Operational log. Which of the two times is closer to the real time is not established. Columns '
                  'are the template fields of the same name, as stored: SSID, Profile Name, Authentication and '
                  'Encryption (AuthenticationAlgorithm and CipherAlgorithm, text on 8001), BSS Type, PHY Type and '
                  'Connection Mode (8001), Disconnect Reason and Disconnect Reason Code (Reason and ReasonCode, '
                  '8003), Automatic (Auto, 14045), Connection ID (ConnectionId, 8001 and 8003, in hexadecimal as '
                  "the template's output type gives it). Association MAC (as stored) is the MAC field of 10040 and "
                  '10041, six bytes written as hexadecimal pairs; the manifest does not say which station it names.'
                  " Association Status (as stored) is 10041's Status in hexadecimal, its output type; "
                  'lonewolf_win10 held 0x0 on 10 rows, 0x2 on 4 and 0x5 on 1, whose meanings are not established. '
                  'Interface GUID is InterfaceGuid (WLAN AutoConfig) or AdapterGuid (NWiFi): on both tested images '
                  'they held the same GUID, and Interface GUID held one value on all rows of each image. SSID and '
                  'Profile Name were identical on all rows of both images where either was filled. Not reported: '
                  'the SSIDList of 14045 and the OnexEnabled and NonBroadcast fields of 8001. Known data: '
                  'pc_mus_001_win11 gave 39 rows (16 10040, 16 10041, 3 14045, 3 8001, 1 8003) and lonewolf_win10 '
                  '33 (15, 15, 1, 1, 1). Compared with the Operational log: on pc_mus_001_win11 one 8001 in '
                  "Wifi.etl is later than that log's last record, and on lonewolf_win10 the Wifi.etl 8003 and 8001 "
                  "both fall after that log's last record. Get-WinEvent returned no event from the last buffer of "
                  'the lonewolf_win10 and hexordia_mvs2025_win11 files, a buffer that ends past the 8 MB maximum '
                  "file size their logfile header records; that buffer's sequence number lay among the other "
                  "buffers' and its records framed like theirs, and it is read; none of the rows here came from it."
                  ' The Wifi.etl files of hexordia_mvs2025_win11, af_case2_win10 and szechuan_win10 held none of '
                  "these events. Not read: the trace's other events, including WLAN AutoConfig 20024 (a count of "
                  'networks per scan), and its WPP records (most of each tested file), whose format information is '
                  'not in the file and which Get-WinEvent did not decode either. Wifi.etl is written over in a '
                  'circle, so it holds a recent window of events, and an empty artifact says only that the file '
                  'held none.'),
        "paths": ("*/Windows/System32/LogFiles/WMI/Wifi.etl",),
        "output_types": ["standard"],
        "artifact_icon": "wifi",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 39 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 33 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (the Wifi.etl holds none of these events)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the Wifi.etl holds none of these events)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the Wifi.etl holds none of these events)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
            "cfreds_hacking_case_winxp": "Windows XP (per the acquisition metadata) | 0 rows (no member matches the declared paths)",
            "windows11_arm_usn_rewind_known_20261025": "Windows 11 25H2 build 26200 (NTFS test volume) | 0 rows (no member matches the declared paths)",
        },
    },
}

from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts import etl
from scripts.ilapfuncs import artifact_processor, logfunc

_AUTOCONFIG = '9580d7dd-0379-4658-9870-d5be7d52d6de'   # Microsoft-Windows-WLAN-AutoConfig
_NWIFI = '0bd3506a-9030-4f76-9b88-3e8fe1f7cfb6'        # Microsoft-Windows-NWiFi
_G, _U, _I, _B, _P = 'win:GUID', 'win:UnicodeString', 'win:UInt32', 'win:Boolean', 'win:Pointer'

# Event templates as Windows 11 build 26200 (wlansvc.dll 10.0.26100.9549, nwifi.sys 10.0.26100.1) gives them
# through its provider metadata; keyed by provider, event ID and version.
_TEMPLATES = {
    (_AUTOCONFIG, 8001, 0): (('InterfaceGuid', _G), ('InterfaceDescription', _U), ('ConnectionMode', _U),
                             ('ProfileName', _U), ('SSID', _U), ('BSSType', _U), ('PHYType', _U),
                             ('AuthenticationAlgorithm', _U), ('CipherAlgorithm', _U), ('OnexEnabled', _I),
                             ('ConnectionId', _P), ('NonBroadcast', _B)),
    (_AUTOCONFIG, 8003, 0): (('InterfaceGuid', _G), ('InterfaceDescription', _U), ('ConnectionMode', _U),
                             ('ProfileName', _U), ('SSID', _U), ('BSSType', _U), ('Reason', _U),
                             ('ConnectionId', _P), ('ReasonCode', _I)),
    (_AUTOCONFIG, 14045, 0): (('InterfaceGuid', _G), ('InterfaceDescription', _U), ('ProfileName', _U),
                              ('Auto', _B), ('SSID', _U), ('Multiple', _B), ('SSIDListSize', 'win:UInt16'),
                              ('SSIDList', 'win:Binary', 'SSIDListSize')),
    (_AUTOCONFIG, 20025, 0): (('Ssid', _U), ('BssidCount', _I), ('AuthAlgoId', _I), ('CipherAlgoId', _I),
                              ('Rssi', _I)),
    (_NWIFI, 10040, 0): (('ContextHandle', _P), ('AdapterGuid', _G), ('MAC', 'win:Binary', 6)),
    (_NWIFI, 10041, 0): (('ContextHandle', _P), ('AdapterGuid', _G), ('MAC', 'win:Binary', 6), ('Status', _I)),
}
_CONNECTION_EVENTS = {
    (_AUTOCONFIG, 8001): 'WLAN AutoConfig: connected to a wireless network',
    (_AUTOCONFIG, 8003): 'WLAN AutoConfig: disconnected from a wireless network',
    (_AUTOCONFIG, 14045): 'WLAN AutoConfig: connection using a profile',
    (_NWIFI, 10040): 'NWiFi: association start',
    (_NWIFI, 10041): 'NWiFi: association completion',
}
# DOT11_AUTH_ALGORITHM and DOT11_CIPHER_ALGORITHM (wlantypes.h), see the notes.
_AUTH = {1: 'DOT11_AUTH_ALGO_80211_OPEN', 2: 'DOT11_AUTH_ALGO_80211_SHARED_KEY', 3: 'DOT11_AUTH_ALGO_WPA',
         4: 'DOT11_AUTH_ALGO_WPA_PSK', 5: 'DOT11_AUTH_ALGO_WPA_NONE', 6: 'DOT11_AUTH_ALGO_RSNA',
         7: 'DOT11_AUTH_ALGO_RSNA_PSK', 8: 'DOT11_AUTH_ALGO_WPA3_ENT_192', 9: 'DOT11_AUTH_ALGO_WPA3_SAE',
         10: 'DOT11_AUTH_ALGO_OWE', 11: 'DOT11_AUTH_ALGO_WPA3_ENT'}
_CIPHER = {0x00: 'DOT11_CIPHER_ALGO_NONE', 0x01: 'DOT11_CIPHER_ALGO_WEP40', 0x02: 'DOT11_CIPHER_ALGO_TKIP',
           0x04: 'DOT11_CIPHER_ALGO_CCMP', 0x05: 'DOT11_CIPHER_ALGO_WEP104', 0x06: 'DOT11_CIPHER_ALGO_BIP',
           0x08: 'DOT11_CIPHER_ALGO_GCMP', 0x09: 'DOT11_CIPHER_ALGO_GCMP_256', 0x0a: 'DOT11_CIPHER_ALGO_CCMP_256',
           0x0b: 'DOT11_CIPHER_ALGO_BIP_GMAC_128', 0x0c: 'DOT11_CIPHER_ALGO_BIP_GMAC_256',
           0x0d: 'DOT11_CIPHER_ALGO_BIP_CMAC_256', 0x100: 'DOT11_CIPHER_ALGO_WPA_USE_GROUP or RSN_USE_GROUP',
           0x101: 'DOT11_CIPHER_ALGO_WEP'}
_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _utc(filetime):
    if filetime is None or filetime <= 0:
        return ''
    return _FILETIME_EPOCH + timedelta(microseconds=filetime // 10)


def _mac(value):
    return ':'.join(f'{byte:02X}' for byte in value)


def wifi_events(data, wanted, label, problems):
    """(EtlEvent, values) for each event of one Wifi.etl whose (provider, id) is in `wanted`, decoded with
    its template. Events of a wanted ID with a version not in the templates, and events whose data does not
    match their template, are counted in `problems` and skipped."""
    trace = etl.EtlFile(data)
    found = []
    for event in trace.events():
        if (event.provider, event.event_id) not in wanted:
            continue
        template = _TEMPLATES.get((event.provider, event.event_id, event.version))
        if template is None:
            problems[f'{label}: events {event.event_id} of version {event.version}, which has no template here'] += 1
            continue
        try:
            values, left = etl.decode(event.data, template, event.pointer_size)
        except ValueError:
            problems[f'{label}: events {event.event_id} whose data ends before their template'] += 1
            continue
        if left:
            problems[f'{label}: events {event.event_id} with data left after their template'] += 1
            continue
        found.append((event, values))
    for problem, count in trace.problems.items():
        problems[f'{label}: {problem}'] += count
    if trace.header['clock_type'] not in (etl.CLOCK_PERFORMANCE_COUNTER, etl.CLOCK_SYSTEM_TIME):
        problems[f"{label}: a clock type of {trace.header['clock_type']}, whose times are left blank"] += 1
    return found


def _read(context, label, wanted):
    sources, rows = [], []
    for source in sorted(str(f) for f in context.get_files_found()):
        if not source.lower().endswith('wifi.etl'):
            continue
        problems = Counter()
        try:
            with open(source, 'rb') as handle:
                data = handle.read()
            found = wifi_events(data, wanted, label, problems)
        except (OSError, etl.EtlError) as exc:
            logfunc(f'{label}: {context.get_relative_path(source)} not read: {type(exc).__name__}: {exc}')
            continue
        sources.append(source)
        rows.extend(found)
        for problem, count in sorted(problems.items()):
            logfunc(f'{problem}: {count} in {context.get_relative_path(source)}')
    rows.sort(key=lambda row: (row[0].filetime or 0, row[0].buffer, row[0].offset))
    return rows, sources


@artifact_processor
def windowsWifiEtlVisibleNetworks(context):
    data_headers = (('Scan Event Time (UTC)', 'datetime'), 'SSID (as stored)', 'BSSID Count',
                    'Authentication Algorithm ID', 'Authentication Algorithm (DOT11 name)', 'Cipher Algorithm ID',
                    'Cipher Algorithm (DOT11 name)', 'RSSI (as stored)')
    rows, sources = _read(context, 'Wi-Fi Visible Networks', {(_AUTOCONFIG, 20025)})
    data_list = []
    for event, values in rows:
        auth, cipher = values['AuthAlgoId'], values['CipherAlgoId']
        data_list.append((_utc(event.filetime), values['Ssid'], values['BssidCount'], auth, _AUTH.get(auth, ''),
                          cipher, _CIPHER.get(cipher, ''), values['Rssi']))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def windowsWifiEtlConnections(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'SSID', 'Profile Name',
                    'Association MAC (as stored)', 'Association Status (as stored)', 'Authentication',
                    'Encryption', 'BSS Type', 'PHY Type', 'Connection Mode', 'Disconnect Reason',
                    'Disconnect Reason Code', 'Automatic', 'Connection ID', 'Interface GUID')
    rows, sources = _read(context, 'Wi-Fi Connection Events', set(_CONNECTION_EVENTS))
    data_list = []
    for event, v in rows:
        status = v.get('Status')
        connection = v.get('ConnectionId')
        auto = v.get('Auto')
        data_list.append((
            _utc(event.filetime), event.event_id, _CONNECTION_EVENTS[(event.provider, event.event_id)],
            v.get('SSID', ''), v.get('ProfileName', ''), _mac(v['MAC']) if 'MAC' in v else '',
            '' if status is None else f'{status:#x}', v.get('AuthenticationAlgorithm', ''),
            v.get('CipherAlgorithm', ''), v.get('BSSType', ''), v.get('PHYType', ''), v.get('ConnectionMode', ''),
            v.get('Reason', ''), '' if v.get('ReasonCode') is None else v['ReasonCode'],
            '' if auto is None else ('true' if auto else 'false'),
            '' if connection is None else f'{connection:#x}', v.get('InterfaceGuid') or v.get('AdapterGuid', '')))
    return data_headers, data_list, '\n'.join(sources)
