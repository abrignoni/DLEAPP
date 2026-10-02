"""Group Policy operational event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Reads every Microsoft-Windows-GroupPolicy record of the provider's Operational event log: policy processing that
started and completed for the computer or a user account, the domain controller and account details the service
logged, the Group Policy objects it listed, and the provider's other events of that log. A field can hold a
parameter reference (%%n); each is given the text of that message from the English (en-US) gpsvc.dll.mui on the
log's own volume (_ParameterText), and is reported as stored when that file is not there. The Event IDs, the
message text and the field names are sourced in the notes.
"""

import collections
import os

from scripts import windows_messages
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_evtx import read_event_records

_LABEL = 'Group Policy Operational Events'
_LOG = 'Microsoft-Windows-GroupPolicy%4Operational.evtx'
_PROVIDER = 'Microsoft-Windows-GroupPolicy'
_ACCOUNT = 'PrincipalSamName'

# Event ID: the first sentence of the first line of the provider's message for it (see notes).
_EVENTS = {
    '4000': 'Starting computer boot policy processing for %2.',
    '4001': 'Starting user logon Policy processing for %2.',
    '4002': 'Starting policy processing due to network state change for computer %2.',
    '4003': 'Starting policy processing due to network state change for user %2.',
    '4004': 'Starting manual processing of policy for computer %2.',
    '4005': 'Starting manual processing of policy for user %2.',
    '4006': 'Starting periodic policy processing for computer %2.',
    '4007': 'Starting periodic policy processing for user %2.',
    '4016': 'Starting %2 Extension Processing.',
    '4017': '%1',
    '4018': 'Starting %2 for %1.',
    '4019': 'Running script name %1.',
    '4115': 'Group Policy Service started.',
    '4116': 'Started the Group Policy service initialization phase.',
    '4117': 'Group Policy Session started.',
    '4126': 'Group Policy receiving applicable GPOs from the domain controller.',
    '4216': 'Starting to save policies to the local datastore.',
    '4217': 'Starting to load policies from the local datastore.',
    '4218': 'Starting the first WMI query for the policy.',
    '4257': 'Starting to download policies.',
    '4326': 'Group Policy is trying to discover the Domain Controller information.',
    '5016': 'Completed %3 Extension Processing in %1 milliseconds.',
    '5017': '%3',
    '5018': 'Completed %4 for %3 in %1 seconds.',
    '5019': 'Completed %3 in %1 seconds.',
    '5115': 'Group Policy Service stopped.',
    '5116': 'Successfully completed the Group Policy Service initialization phase.',
    '5117': 'Group policy session completed successfully.',
    '5126': 'Group Policy successfully got applicable GPOs from the domain controller.',
    '5216': 'Successfully saved policies to the local datastore.',
    '5217': 'Successfully loaded policies from the local datastore.',
    '5218': 'Successfully completed the first WMI query.',
    '5257': 'Successfully completed downloading policies.',
    '5308': 'Domain Controller details:',
    '5309': 'Computer details:',
    '5310': 'Account details:',
    '5311': 'The loopback policy processing mode is %1.',
    '5312': 'List of applicable Group Policy objects:',
    '5313': 'The following Group Policy objects were not applicable because they were filtered out :',
    '5314': 'A %6 link was detected.',
    '5315': 'Next policy processing for %1 will be attempted in %2 %3.',
    '5320': '%1',
    '5321': '%1 Parameter: %2',
    '5322': 'Group Policy waited for %3 milliseconds for the network subsystem at computer boot.',
    '5323': 'Invalid Error Message.',
    '5324': 'Group Policy received the notification %1 from Winlogon for session %2.',
    '5325': 'Group Policy received %1 notification from Service Control Manager.',
    '5326': 'Group Policy successfully discovered the Domain Controller in %1 milliseconds.',
    '5327': 'Estimated network bandwidth on one of the connections: %1 kbps.',
    '5331': 'Service configuration update to standalone was attempted due to the presence of Group Policy '
            'client extension %1 that is not part of the operating system and completed with status %3.',
    '5332': 'Group Policy waited for %3 milliseconds for the Direct Access CorpNet connectivity at computer boot.',
    '5340': 'The Group Policy processing mode is %1.',
    '5351': 'Group policy session returned to winlogon.',
    '6000': 'Invalid Error Message.',
    '6001': 'Invalid Error Message.',
    '6002': 'Invalid Error Message.',
    '6003': 'Invalid Error Message.',
    '6004': 'Invalid Error Message.',
    '6005': 'Invalid Error Message.',
    '6006': 'Invalid Error Message.',
    '6007': 'Invalid Error Message.',
    '6016': 'Completed %3 Extension Processing in %1 milliseconds.',
    '6017': 'Invalid Error Message.',
    '6018': 'Invalid Error Message.',
    '6019': 'Invalid Error Message.',
    '6033': 'Skipped %1 Extension based on Group Policy client-side processing rules.',
    '6034': 'Group Policy changed from synchronous foreground to asynchronous foreground based on slow link '
            'detection.',
    '6035': '%1 Extension deferred processing until next synchronous foreground.',
    '6226': 'Invalid Error Message.',
    '6308': 'Invalid Error Message.',
    '6309': 'Invalid Error Message.',
    '6310': 'Invalid Error Message.',
    '6311': 'Invalid Error Message.',
    '6312': 'Invalid Error Message.',
    '6313': 'Invalid Error Message.',
    '6314': 'Group Policy bandwidth estimation failed.',
    '6315': 'Invalid Error Message.',
    '6320': 'Warning: %1 Warning code %2.',
    '6321': 'Warning: %1 Parameter: %3 : Warning code %2.',
    '6322': 'Invalid Error Message.',
    '6323': 'Group Policy dependency (%1) did not start.',
    '6324': 'Invalid Error Message.',
    '6325': 'Invalid Error Message.',
    '6326': 'Invalid Error Message.',
    '6327': 'Invalid Error Message.',
    '6330': 'An unfinished invocation of the Group Policy Client Side Extension %1 from a previous instance '
            'of the Group Policy Service was detected.',
    '6331': 'Invalid Error Message.',
    '6332': 'Invalid Error Message.',
    '6337': 'Group Policy network connection is via Direct Access.',
    '6338': 'Group Policy Winlogon status reporting has completed.',
    '6339': 'Group Policy Winlogon Start Shell handling completed.',
    '6341': 'A Group Policy setting was used to override the fast/slow link detection.',
    '6342': 'The network connection is using a WWAN device for connectivity.',
    '6344': 'Group Policy detected a slow link during sync mode processing.',
    '6345': 'The connection to DC timed out during the Group Policy sync mode process.',
    '6346': 'Group Policy switched the sync mode process to async mode.',
    '7000': 'Computer boot policy processing failed for %3 in %1 seconds.',
    '7001': 'User logon policy processing failed for %3 in %1 seconds.',
    '7002': 'Policy processing due to network state change failed for computer %3 in %1 seconds.',
    '7003': 'Policy processing due to network state change failed for user %3 in %1 seconds.',
    '7004': 'Manual processing of policy failed for computer %3 in %1 seconds.',
    '7005': 'Manual processing of policy failed for user %3 in %1 seconds.',
    '7006': 'Periodic policy processing failed for computer %3 in %1 seconds.',
    '7007': 'Periodic policy processing failed for user %3 in %1 seconds.',
    '7016': 'Completed %3 Extension Processing in %1 milliseconds.',
    '7017': '%3',
    '7018': 'Script for %3 failed in %1 seconds.',
    '7019': 'Invalid Error Message.',
    '7117': 'Group policy session completed with error.',
    '7126': 'Group Policy could not get applicable GPOs from the domain controller.',
    '7216': 'Saved policies to the local datastore with error.',
    '7217': 'Loaded policies from the local datastore with error.',
    '7257': 'Downloaded policies with error.',
    '7308': 'Invalid Error Message.',
    '7309': 'Invalid Error Message.',
    '7310': 'Invalid Error Message.',
    '7311': 'Invalid Error Message.',
    '7312': 'Invalid Error Message.',
    '7313': 'Invalid Error Message.',
    '7314': 'Invalid Error Message.',
    '7315': 'Invalid Error Message.',
    '7320': 'Error: %1 Error code %2.',
    '7321': 'Error: %1 Parameter: %3 : Error code %2.',
    '7322': 'Invalid Error Message.',
    '7323': 'Invalid Error Message.',
    '7324': 'Invalid Error Message.',
    '7325': 'Invalid Error Message.',
    '7326': 'Group Policy failed to discover the Domain Controller details in %1 milliseconds.',
    '7327': 'Invalid Error Message.',
    '7331': 'Service configuration update to standalone was attempted due to the presence of Group Policy '
            'client extension %1 that is not part of the operating system and completed with status %3.',
    '7332': 'Invalid Error Message.',
    '8000': 'Completed computer boot policy processing for %3 in %1 seconds.',
    '8001': 'Completed user logon policy processing for %3 in %1 seconds.',
    '8002': 'Completed policy processing due to network state change for computer %3 in %1 seconds.',
    '8003': 'Completed policy processing due to network state change for user %3 in %1 seconds.',
    '8004': 'Completed manual processing of policy for computer %3 in %1 seconds.',
    '8005': 'Completed manual processing of policy for user %3 in %1 seconds.',
    '8006': 'Completed periodic policy processing for computer %3 in %1 seconds.',
    '8007': 'Completed periodic policy processing for user %3 in %1 seconds.',
    '8016': '%1 Extension (%2) requests a sync mode process.',
    '9001': 'This machine is configured to retrieve Group Policy files from a file share in an insecure way.',
}


__artifacts_v2__ = {
    "groupPolicyOperationalEvents": {
        "name": "Group Policy Operational Events",
        "description": "Microsoft-Windows-GroupPolicy records of the provider's Operational event log, such as the "
                       "start and finish of policy processing for the computer or an account, the domain controller "
                       "and account details the service logged and the Group Policy objects it listed, with each "
                       "record's other fields.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-02",
        "last_update_date": "2026-10-02",
        "requirements": "python-evtx; pefile to give the parameter references their text",
        "category": "Windows",
        "notes": "Reads every Microsoft-Windows-GroupPolicy%4Operational.evtx the paths match with python-evtx and "
                 "reports, one row per record, every record whose provider is Microsoft-Windows-GroupPolicy, "
                 "whatever its Event ID. The provider's manifest of Windows 11 build 26100.1742 sends 165 entries to "
                 "this log's channel: 141 Event IDs, 24 of them with a version 0 and a version 1 "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L785-L3243). "
                 "The manifests of Windows 10 builds 16299.15, 17763.107 and 19041.208 and Windows 11 build "
                 "22621.819 hold the same entries with the same messages and fields "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1709/W10_1709_Pro_20171114_16299.15/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L785-L3243, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/1809/W10_1809_Pro_20181113_17763.107/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L785-L3243, "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows10/2004/W10_2004_Pro_20200416_19041.208/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L785-L3243 "
                 "and "
                 "https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/22H2/W11_22H2_Pro_20221115_22621.819/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L785-L3243). "
                 "These are the manifests nasbench's EVTX-ETW-Resources repository publishes. The two versions of an "
                 "Event ID have the same message and field names; their IsMachine field is a win:Boolean in version "
                 "0 and a win:UInt32 in version 1. Event is, for the record's Event ID, the first sentence of the "
                 "first line of the build 26100 message: the first line that holds more than white space, with each "
                 "run of white space made one space, cut after the first period that a space or the end of the line "
                 "follows (whole when it has none), with its placeholders (such as %1) as the manifest writes them. "
                 "A placeholder is an insertion string for a data item of the event's template by its position "
                 "(Microsoft's Defining Events page: 'to include the third data item in the template, include %3', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/defining-events.md?plain=1#L19) "
                 "and is not filled in. Event is a placeholder alone for 4017, 5017, 5320 and 7017, whose first line "
                 "is one field, and 42 Event IDs share the message 'Invalid Error Message.', none of which a tested "
                 "record had. Event is blank for an Event ID outside the 141, which no tested record had. Account is "
                 "the PrincipalSamName field, which the manifests give 28 Event IDs. On the 170 tested rows that "
                 "have one (4000, 4001, 4004 and 4005 and the 8000, 8001, 8004 and 8005 that complete them) it is "
                 "two names joined by a backslash, and on the computer events (4000, 4004, 8000 and 8004) the second "
                 "name ends with $. Activity ID is the ActivityID of the record's Correlation element, a GUID in "
                 "braces; 1,556 of the 3,859 tested rows have one. The PolicyActivityId field of 4000 to 4007 held "
                 "the same value on each of the 85 tested records, and each of those 85 rows has a completion row "
                 "whose Event ID is 4000 higher, at the same time or later, with the same Activity ID and Account. "
                 "No Activity ID has two of those start rows, and one has 36 rows at most. Other Fields lists every "
                 "other named field that holds more than white space as 'name: value', in the record's order, joined "
                 "with ' | '. Each value is as python-evtx renders it with any white space at either end removed (90 "
                 "tested values had some, each a DescriptionString), and line breaks inside a value are kept (the "
                 "DescriptionString of 83 tested records holds some). Microsoft's documentation describes a "
                 "parameter string of the form %%n as the identifier of a message in the message table of the "
                 "provider's parameter file (Microsoft, 'ProviderType complex type', "
                 "https://github.com/MicrosoftDocs/win32/blob/7d0a1e3842939462dc8c4c1f36b31f494c483ebe/desktop-src/WES/eventmanifestschema-providertype-complextype.md?plain=1#L168), "
                 "and the manifests name gpsvc.dll as that file "
                 "(https://github.com/nasbench/EVTX-ETW-Resources/blob/065476ce28fa290d088214b94ba698ee3558fe06/ETWProvidersManifests/Windows11/24H2/W11_24H2_Pro_2024102_26100.1742/WEPExplorer/Microsoft-Windows-GroupPolicy.xml#L7). "
                 "A value holding such a reference is given the text of that message from the English gpsvc.dll.mui "
                 "in System32's en-US folder on the volume the log was read from, written 'text (%%n)', as in "
                 "'Changes were detected. (%%4102)'; the .mui is named in the located-at line when it gave a "
                 "reference its text, otherwise the reference is reported as stored, and the run log says how many "
                 "were given text or kept. On the tested logs 1,033 values are a reference alone, with 19 distinct "
                 "numbers: InfoDescription of 5320 and 5321 (791 and 168), OperationDescription of 4017, 5017 and "
                 "7017 (30, 29 and 1), LinkDescription of 5314 (11), GPOListStatusString of 4016 (2) and "
                 "ErrorDescription of 7320 (1). Each was given its text from the image's own gpsvc.dll.mui, and the "
                 "four copies hold the same 224 messages. A value holding several references, or a reference beside "
                 "other text, has each given its text, which no tested record exercised. Values are reported as "
                 "stored. IsMachine is 0 or 1 on the version 1 records and True or False on the others. ErrorCode "
                 "held 0 on 139 tested records and 1355 on the 7017 and the 7320 record of szechuan_win10; "
                 "NotificationType held 0, 1, 2, 3 or 4 on 5324 and 0 on 5325. What those numbers stand for is not "
                 "established here. A data item that has no name is not shown, and no tested record had one. If a "
                 "record named a field twice the last would be read. The tested records carried the field names "
                 "their image's build manifest gives the Event ID and version. Tested on the logs of four public "
                 "images (af_case2_win10, build 17763; lonewolf_win10, build 16299; pc_mus_001_win11, build 22621; "
                 "szechuan_win10, build 19041), which gave 962, 737, 1,433 and 727 rows in that order; the two "
                 "captures of a Windows 11 build 26200 machine hold no such log. 46 of the 141 Event IDs occur: 24 "
                 "on all four images and 22 on szechuan_win10 alone, the only image with records whose "
                 "IsDomainJoined is True (13 of its 21 records of 4000 to 4005). Among those 22 are the domain "
                 "controller, computer and account details (5308, 5309 and 5310, 12 records each) and manual policy "
                 "processing (4004 and 4005, 3 and 1). The DescriptionString of 5312 held text on each of the 83 "
                 "tested records, and its GPOInfoList held a GPO element on 5 records of szechuan_win10. The other "
                 "95 Event IDs are unexercised. Event Time (UTC) is the record's TimeCreated SystemTime, which "
                 "python-evtx renders from the FILETIME the record stores, counted in UTC (python-evtx 0.8.1, "
                 "https://github.com/williballenthin/python-evtx/blob/cab997af04b6caae68b306e5c2c40b3aa751454e/Evtx/BinaryParser.py#L105-L113). "
                 "User SID is the UserID of the record's Security element: S-1-5-18 on 3,631 tested rows and an "
                 "S-1-5-21 account on 228. Record ID is the record's EventRecordID and Computer the machine name the "
                 "record stores, which held one value on pc_mus_001_win11, two on af_case2_win10 and lonewolf_win10 "
                 "and three on szechuan_win10. Rows are in the order the file holds them, which was rising Record ID "
                 "on every tested log; in time order 3 rows are earlier than the row before them (1 each on "
                 "af_case2_win10, lonewolf_win10 and szechuan_win10). Every record of the tested logs rendered and "
                 "is the provider's. A record python-evtx cannot render, or whose XML does not parse, is counted in "
                 "the run log and not reported. A log marked dirty is read past the chunks its header counts, and "
                 "the run log says how many records came from there. Reading needs the python-evtx package (pip "
                 "install python-evtx); giving the references their text needs the pefile package (pip install "
                 "pefile), and without it they are reported as stored. Not read: the 36 entries these manifests send "
                 "to the System log.",
        "paths": ("*/Windows/System32/winevt/Logs/Microsoft-Windows-GroupPolicy%4Operational.evtx",
                  "*/Windows/System32/en-US/gpsvc.dll.mui"),
        "output_types": ["standard"],
        "artifact_icon": "sliders",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 962 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 737 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1433 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 727 rows",
            "windows11_arm_4688_known": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (no member matches the declared paths)",
        },
    },
}


class _ParameterText:
    """Text for the parameter references (%%n) a record stores.

    The text comes from the English (en-US) gpsvc.dll.mui in the System32 folder of the volume the record's log
    was read from. A resolved reference reads 'text (%%n)'; a reference that file does not resolve is kept as
    stored.
    """

    _LOG_DIR = '/windows/system32/winevt/logs/'
    _MESSAGE_FILE = '/windows/system32/en-us/gpsvc.dll.mui'

    def __init__(self, context, label):
        self.context = context
        self.label = label
        self.files = {}        # volume root -> staged path
        self.tables = {}       # staged path -> {message id: text}
        self.resolved = collections.Counter()
        self.kept = 0
        for path in sorted(str(f) for f in context.get_files_found()):
            if os.path.isdir(path):
                continue
            relative = self._relative(path)
            if relative.endswith(self._MESSAGE_FILE):
                self.files.setdefault(relative[:-len(self._MESSAGE_FILE)], path)

    def _relative(self, path):
        return '/' + self.context.get_relative_path(path).replace('\\', '/').lower()

    def _message_file(self, record):
        relative = self._relative(record.source) if record.source else ''
        at = relative.find(self._LOG_DIR)
        return self.files.get(relative[:at]) if at >= 0 else None

    def text(self, record, value):
        """The value with each reference the volume's gpsvc.dll.mui resolves written 'text (%%n)'."""
        if not windows_messages.REFERENCE.search(value or ''):
            return value
        path = self._message_file(record)
        if path and path not in self.tables:
            self.tables[path] = windows_messages.read_message_table(path)
        table = self.tables.get(path, {})

        def shown(match):
            message = (table.get(int(match.group(1))) or '').strip()
            if not message:
                self.kept += 1
                return match.group(0)
            self.resolved[path] += 1
            return f'{message} ({match.group(0)})'

        return windows_messages.REFERENCE.sub(shown, value)

    def files_used(self):
        """The message files that gave text to at least one reference, for the source path."""
        return sorted(self.resolved)

    def log(self):
        for path, count in sorted(self.resolved.items()):
            logfunc(f'{self.label}: {count} parameter reference(s) given their text from '
                    f'{self.context.get_relative_path(path)}')
        if self.kept:
            missing = '' if windows_messages.pefile else ' (pefile is not installed)'
            logfunc(f'{self.label}: {self.kept} parameter reference(s) reported as stored; '
                    f'no English gpsvc.dll.mui on the same volume gave their text{missing}')


def group_policy_row(record, parameters):
    other = ' | '.join(f'{name}: {parameters.text(record, record.get(name))}' for name in record.fields
                       if name != _ACCOUNT and record.get(name))
    return (record.time, record.event_id, _EVENTS.get(record.event_id, ''), record.get(_ACCOUNT), record.activity_id,
            other, record.user_sid, record.record_id, record.computer)


@artifact_processor
def groupPolicyOperationalEvents(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'Account', 'Activity ID', 'Other Fields',
                    'User SID', 'Record ID', 'Computer')
    records, sources = read_event_records(context, _LOG, _LABEL, provider=_PROVIDER)
    parameters = _ParameterText(context, _LABEL)
    data_list = [group_policy_row(record, parameters) for record in records]
    parameters.log()
    return data_headers, data_list, '\n'.join(list(sources) + parameters.files_used())
