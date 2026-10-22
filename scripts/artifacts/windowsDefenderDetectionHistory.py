"""Microsoft Defender Antivirus DetectionHistory parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads the files under ProgramData\\Microsoft\\Windows Defender\\Scans\\History\\
Service\\DetectionHistory\\<nn>\\<GUID>, one row per file. The layout and the
sources for each field are in the notes; the reading is in
scripts/windows_defender_history.py.
"""

import os
import re

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_defender_history import (
    TYPE_BINARY, TYPE_FILETIME, TYPE_GUID, TYPE_INTEGER_32, TYPE_INTEGER_64, TYPE_STRING,
    Detection, filetime_utc, read_threat_tracking, read_values)

_LABEL = 'Microsoft Defender Detection History'
_DETECTION_FOLDER = '/programdata/microsoft/windows defender/scans/history/service/detectionhistory/'
_GUID_NAME = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-'
                        r'[0-9a-fA-F]{12}$')

# MPTHREAT_SEVERITY and MPTHREAT_CATEGORY, MpClient.h, as Microsoft documents them (see notes).
_SEVERITY = {0: 'UNKNOWN', 1: 'LOW', 2: 'MODERATE', 4: 'HIGH', 5: 'SEVERE'}
_CATEGORY = {
    0: 'INVALID', 1: 'ADWARE', 2: 'SPYWARE', 3: 'PASSWORDSTEALER', 4: 'TROJANDOWNLOADER',
    5: 'WORM', 6: 'BACKDOOR', 7: 'REMOTEACCESSTROJAN', 8: 'TROJAN', 9: 'EMAILFLOODER',
    10: 'KEYLOGGER', 11: 'DIALER', 12: 'MONITORINGSOFTWARE', 13: 'BROWSERMODIFIER',
    14: 'COOKIE', 15: 'BROWSERPLUGIN', 16: 'AOLEXPLOIT', 17: 'NUKER', 18: 'SECURITYDISABLER',
    19: 'JOKEPROGRAM', 20: 'HOSTILEACTIVEXCONTROL', 21: 'SOFTWAREBUNDLER',
    22: 'STEALTHNOTIFIER', 23: 'SETTINGSMODIFIER', 24: 'TOOLBAR', 25: 'REMOTECONTROLSOFTWARE',
    26: 'TROJANFTP', 27: 'POTENTIALUNWANTEDSOFTWARE', 28: 'ICQEXPLOIT', 29: 'TROJANTELNET',
    30: 'EXPLOIT', 31: 'FILESHARINGPROGRAM', 32: 'MALWARE_CREATION_TOOL',
    33: 'REMOTE_CONTROL_SOFTWARE', 34: 'TOOL', 36: 'TROJAN_DENIALOFSERVICE',
    37: 'TROJAN_DROPPER', 38: 'TROJAN_MASSMAILER', 39: 'TROJAN_MONITORINGSOFTWARE',
    40: 'TROJAN_PROXYSERVER', 42: 'VIRUS', 43: 'KNOWN', 44: 'UNKNOWN', 45: 'SPP',
    46: 'BEHAVIOR', 47: 'VULNERABILTIY', 48: 'POLICY',
}

# Positions after the separator that opens the last resource set, counted from 0 at the
# resource type (dtformats "Known values - set 3", whose index 0 is the separator itself).
_LAST_STATUS_CHANGE = 5
_ENTRY_GUID = 8
_DOMAIN_USER = 11
_PROCESS = 13
_INITIAL_DETECTION = 17
_REMEDIATION = 19
_SECOND_USER = 23
_NULL_GUID = '00000000-0000-0000-0000-000000000000'
_TRAILING = (
    ('changed', _LAST_STATUS_CHANGE, TYPE_FILETIME), ('entry', _ENTRY_GUID, TYPE_GUID),
    ('user', _DOMAIN_USER, TYPE_STRING), ('process', _PROCESS, TYPE_STRING),
    ('initial', _INITIAL_DETECTION, TYPE_FILETIME), ('remediated', _REMEDIATION, TYPE_FILETIME),
    ('second_user', _SECOND_USER, TYPE_STRING))

__artifacts_v2__ = {
    "defenderDetectionHistory": {
        "name": "Microsoft Defender Detection History",
        "description": "Microsoft Defender Antivirus DetectionHistory files, one row per "
                       "file: the threat name and ID, severity and category, the detected "
                       "resources, the hashes Defender stored for them, the user and process "
                       "the file names, and its detection, status change and remediation "
                       "times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-22",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the files under ProgramData/Microsoft/Windows "
                 "Defender/Scans/History/Service/DetectionHistory/<folder>/ whose name is a GUID, each "
                 "named in the Source File column and the report's located-at line. One row per file. "
                 "plaso_testdata_f951fc6 and dhparser_detectionhistory_gpl keep their files at their "
                 "repository names, which the paths do not match, so neither gives rows as registered; "
                 "what these notes say about those files was checked on copies of the same files placed "
                 "at the DetectionHistory path, which are not registered (2 rows and 1 row). "
                 "The layout is the one in Joachim Metz's 'Windows Defender scan DetectionHistory file "
                 "format' (libyal dtformats, "
                 "https://github.com/libyal/dtformats/blob/308ce8c38df2eb95a71b6e832b3f9803f0c4b169/documentation/Windows%20Defender%20scan%20DetectionHistory%20file%20format.asciidoc#L66-L218,"
                 " threat tracking data #L320-L435) and in plaso's windefender_history parser "
                 "(https://github.com/log2timeline/plaso/blob/d028e5bcb0160dc033531115e30b264fb325ec42/plaso/parsers/windefender_history.py#L59-L75);"
                 " this is an independent implementation. Jordan Klepser's DHParser "
                 "(https://github.com/jklepsercyber/defender-detectionhistory-parser/tree/c5543f2d4807ac75f830c54c3f4f1361e84c5302)"
                 " is earlier research on the same files, by a byte scan; its code was not used. "
                 "dissect.target at b43db37 has no reader for these files. A file is a run of values, "
                 "each a 32-bit size, a 32-bit type and the data, padded to 8 bytes; a string value "
                 "Magic.Version:1.2 separates the sets. Threat ID is the first value and Detection ID "
                 "the second, a GUID, which dtformats describes as the GUID of the file name "
                 "(#L112-L114); it is shown in capitals, as the file names in the tested files are. "
                 "Counting the separator as index 0, as dtformats does, Threat Name is index 1 of the "
                 "threat set, the first value after the separator (#L125); Severity is index 3, which "
                 "dtformats lists only as a possible SeverityID (#L129), and Category index 4 "
                 "(#L131); both are shown as the name Microsoft's MPTHREAT_SEVERITY and "
                 "MPTHREAT_CATEGORY enumerations give the number, followed by the number "
                 "(https://github.com/MicrosoftDocs/win32/blob/2ec0df659644a793ed4f6160f238a95c9d9a9dcf/desktop-src/lwef/mpthreat-severity.md#L29-L33,"
                 " "
                 "https://github.com/MicrosoftDocs/win32/blob/2ec0df659644a793ed4f6160f238a95c9d9a9dcf/desktop-src/lwef/mpthreat-category.md#L28-L74),"
                 " and a number neither enumeration names is shown as stored. dtformats' own severity "
                 "table (#L282-L292) numbers severities differently and is not used. Resource Count is "
                 "the last value of the threat set (#L151). Resources lists each resource set's type and"
                 " location (#L160-L162) as 'type: location', one per line, as stored; in the two "
                 "plaso_testdata_f951fc6 files the webfile location holds three parts separated by '|', "
                 "which neither dtformats nor plaso documents. SHA-256, SHA-1 and MD5 are the ThreatTrackingSha256, "
                 "ThreatTrackingSha1 and ThreatTrackingMD5 values (#L415, #L424, #L427) in each "
                 "resource's threat tracking data, each distinct value once, one per line. The remaining"
                 " columns are read at fixed positions after the separator that opens the last resource "
                 "set, dtformats' set 3 indexes (#L169-L202): Last Status Change Time (UTC) index 6, "
                 "GUID at Index 9, Domain User index 12, Process Name index 14, Initial Detection Time "
                 "(UTC) index 18, Remediation Time (UTC) index 20 and Second User (as stored) index 24. "
                 "dtformats marks the three times as unconfirmed, with the names "
                 "LastThreatStatusChangeTime, InitialDetectionTime and RemediationTime, and index 9 as "
                 "an unknown GUID; plaso names the times the same way. The times are FILETIME values "
                 "(#L77-L96), counted in UTC and cut to whole microseconds; a stored 0 is left blank. A "
                 "value at one of these positions whose type is not the one expected is left blank and "
                 "named in Read Note, as is a missing detection time. Read Note is empty when the file's"
                 " values end exactly at its size, the threat set's count equals the resource sets read,"
                 " every threat tracking block reads to its stated end, the GUID equals the file name "
                 "and the detection time is in place; otherwise it says which did not hold, and the run "
                 "log names the file. Read Note was empty on every row of the known data and of those "
                 "copies. Known data "
                 "(windows11_arm_defender_eicar_known_20261018): Defender platform 4.18.26090.9 on "
                 "Windows 11 build 26200 detected and quarantined three files holding the EICAR test "
                 "string, written locally; the three rows matched Get-MpThreatDetection and Get-MpThreat"
                 " on the same machine and the Defender Operational 1116 and 1117 records with the same "
                 "Detection ID: Threat ID, Threat Name, Severity (5, which the 1116 record names "
                 "Severe), Category (42, which it names Virus), the resource path (the 1116 Path without"
                 " its file:_ prefix), Domain User and Process Name were equal; Initial Detection Time, "
                 "Last Status Change Time and Remediation Time equalled InitialDetectionTime, "
                 "LastThreatStatusChangeTime and RemediationTime to the millisecond; Initial Detection "
                 "Time equalled the Detection Time of the 1116 and 1117 records when cut to the "
                 "millisecond, the precision the event carries, and Remediation Time came less than 2 ms before the 1117 "
                 "record's time. SHA-256, SHA-1 and MD5 equalled the hashes of the 68 bytes written, on "
                 "all three rows. On the known data Threat Name, Threat ID, Severity, Category, Resource"
                 " Count, SHA-256, SHA-1, MD5, Domain User, Process Name and Second User each held one "
                 "value on all three rows, as the three detections were of one test string written by "
                 "one process under one account. Second User held the Remediation User of the matching "
                 "1117 record on all three rows; dtformats names index 24 only as a domain user, so its "
                 "meaning beyond that is not established. GUID at Index 9 equalled the GUID in the name "
                 "of a file in ProgramData/Microsoft/Windows Defender/Quarantine/Entries on all three "
                 "rows (the file name wraps it in braces); that is the only basis for linking it to a "
                 "quarantine entry. GUID at Index 9 is left blank for an all-zero GUID, which both "
                 "plaso_testdata_f951fc6 files store, so it held no value on their rows. In the "
                 "plaso_testdata_f951fc6 file with three resources the webfile resource carried the same"
                 " hashes as the file resource read from inside the archive, so a hash is the one "
                 "Defender stored for that resource and need not be the hash of the file at its "
                 "location. One plaso_testdata_f951fc6 file stores 0 for Remediation Time and an empty "
                 "Second User. Not reported: the other values of the threat set and of the last resource"
                 " set, integers dtformats lists as unknown (on the known data several held the same "
                 "small numbers as Get-MpThreatDetection's status and action fields, so no position "
                 "could be tied to one field), and the other threat tracking keys. The file does not "
                 "name the action taken in a way sourced here; the Defender Operational 1117 record for "
                 "the same Detection ID does (Microsoft Defender Detection Events). Not read: the files "
                 "under Scans/History/Results/Resource and Results/Quick, 86 on six of the ten "
                 "registered disk images (lonewolf_win10 38, alihadi_challenge3_win81 23, "
                 "ou_ransomware_server2022 15, pc_mus_001_win11 6, af_case2_win10 3, szechuan_win10 1; "
                 "none on the other four) and 24 in the known data. The 24 in the known data each open "
                 "with the RC4 key and "
                 "60-byte header dissect.target uses for quarantine entry files "
                 "(https://github.com/fox-it/dissect.target/blob/b43db371c891fa3f382c5152e16f91b0bcde418c/dissect/target/plugins/os/windows/defender/quarantine.py#L92,"
                 " #L169-L177): on all 24 the 60-byte header plus the two section sizes it holds equals "
                 "the file size and the first section begins with the GUID of the file name. No layout "
                 "for the second section is given in the sources cited here, and this module does not "
                 "decode it. Also not read: "
                 "Scans/History Store, RemCheck, CacheManager and the Service .Log files, and the "
                 "Quarantine folder. On the ten registered Windows disk images in sample_data no file "
                 "matched the declared path. No value read from the public files names the Windows or "
                 "Defender version that wrote them. A row records what Defender stored about a "
                 "detection; it does not by itself establish who placed the file or ran the process.",
        "paths": ('*/ProgramData/Microsoft/Windows Defender/Scans/History/Service/'
                  'DetectionHistory/*/*-*-*-*-*',),
        "output_types": ["standard"],
        "artifact_icon": "shield",
        "sample_data": {
                           "windows11_arm_defender_eicar_known_20261018": "Windows 11 build 26200 (ARM64), Defender platform 4.18.26090.9 | 3 rows",
                           "plaso_testdata_f951fc6": "DetectionHistory files only, Windows and Defender versions not established | 0 rows (its two files are kept at repository paths, which the paths do not match)",
                           "dhparser_detectionhistory_gpl": "DetectionHistory file only, Windows and Defender versions not established | 0 rows (its file is kept at its repository name, which the paths do not match)",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
                           "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
                           "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
                           "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
                           "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
                           "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no member matches the declared paths)",
                           "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
                           "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
                           "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
                       },
    },
}


def _coded(value, names):
    """'NAME (n)' when the documented enumeration names n, else n as stored."""
    if value is None:
        return ''
    name = names.get(value)
    return f'{name} ({value})' if name else str(value)


def _text(value):
    return value if isinstance(value, str) else ''


def _detection_files(context):
    for path in sorted(str(f) for f in context.get_files_found()):
        relative = '/' + context.get_relative_path(path).replace('\\', '/').lower()
        if _DETECTION_FOLDER not in relative or os.path.isdir(path):
            continue
        if _GUID_NAME.match(os.path.basename(path)):
            yield path


def _distinct(values):
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return '\n'.join(seen)


@artifact_processor
def defenderDetectionHistory(context):  # pylint: disable=too-many-locals
    data_headers = (('Initial Detection Time (UTC)', 'datetime'),
                    ('Last Status Change Time (UTC)', 'datetime'),
                    ('Remediation Time (UTC)', 'datetime'), 'Threat Name', 'Threat ID',
                    'Severity', 'Category', 'Resource Count', 'Resources', 'SHA-256', 'SHA-1',
                    'MD5', 'Domain User', 'Process Name', 'Second User (as stored)',
                    'GUID at Index 9', 'Detection ID', 'Read Note',
                    'Source File')
    data_list = []
    sources = []
    for path in _detection_files(context):
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: could not read {relative}: {exc.strerror}')
            continue
        sources.append(path)
        values, note = read_values(data)
        notes = [note] if note else []
        detection = Detection(values)
        at = Detection.at
        threat_id = at(detection.head, 0, TYPE_INTEGER_64, *TYPE_INTEGER_32)
        detection_id = at(detection.head, 1, TYPE_GUID)
        if detection_id and detection_id.lower() != os.path.basename(path).lower():
            notes.append('detection GUID differs from the file name')
        threat = detection.threat
        count = at(threat, len(threat) - 1, *TYPE_INTEGER_32) if len(threat) > 4 else None
        if count is not None and count != len(detection.resources):
            notes.append(f'threat set counts {count} resources; {len(detection.resources)} read')
        resources, sha256, sha1, md5 = [], [], [], []
        for resource in detection.resources:
            kind = _text(at(resource, 0, TYPE_STRING))
            location = _text(at(resource, 1, TYPE_STRING))
            resources.append(f'{kind}: {location}' if kind else location)
            tracking = at(resource, 4, TYPE_BINARY)
            if isinstance(tracking, bytes):
                fields, tracking_note = read_threat_tracking(tracking)
                if tracking_note:
                    notes.append(tracking_note)
                sha256.append(_text(fields.get('ThreatTrackingSha256')))
                sha1.append(_text(fields.get('ThreatTrackingSha1')))
                md5.append(_text(fields.get('ThreatTrackingMD5')))
        last = detection.resources[-1] if detection.resources else []
        trailing = {name: at(last, index, kind) for name, index, kind in _TRAILING}
        for name, index, kind in _TRAILING:
            if index < len(last) and last[index].data_type != kind:
                notes.append(f'{name} position holds type 0x{last[index].data_type:02x}, '
                             f'not 0x{kind:02x}')
        if last and trailing['initial'] is None:
            notes.append('no detection time at its position after the last resource')
        if not detection.resources:
            notes.append('no resource set')
        entry = trailing['entry'].upper() if trailing['entry'] not in (None, _NULL_GUID) else ''
        data_list.append((
            filetime_utc(trailing['initial']), filetime_utc(trailing['changed']),
            filetime_utc(trailing['remediated']), _text(at(threat, 0, TYPE_STRING)),
            threat_id if threat_id is not None else '',
            _coded(at(threat, 2, *TYPE_INTEGER_32), _SEVERITY),
            _coded(at(threat, 3, *TYPE_INTEGER_32), _CATEGORY),
            count if count is not None else '', '\n'.join(resources), _distinct(sha256),
            _distinct(sha1), _distinct(md5), _text(trailing['user']), _text(trailing['process']),
            _text(trailing['second_user']), entry, (detection_id or '').upper(), '; '.join(notes),
            relative))
        if notes:
            logfunc(f'{_LABEL}: {relative}: ' + '; '.join(notes))
    logfunc(f'{_LABEL}: {len(data_list)} DetectionHistory file(s) read')
    return data_headers, data_list, '\n'.join(sources)
