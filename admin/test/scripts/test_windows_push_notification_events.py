"""Pin the rows in scripts/artifacts/windowsPushNotificationEvents.py.

The records are built from XML of the shape python-evtx renders for the events (made-up application names and
values); the expected rows and both text tables are written out.
"""
import base64
import datetime
import pathlib
import sys
import unittest
from unittest import mock
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsPushNotificationEvents as push  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

NS = 'http://schemas.microsoft.com/win/2004/08/events/event'
LOG = '/case/data/vol1/Windows/System32/winevt/Logs/Microsoft-Windows-PushNotification-Platform%4Operational.evtx'
TIME = datetime.datetime(2023, 1, 3, 17, 29, 35, 500000, tzinfo=datetime.timezone.utc)
SID = 'S-1-5-21-1111111111-2222222222-3333333333-1001'
FULL = 'Vendor.App_1.2.3.4_x64__abcdefgh12345'
APP = 'Vendor.App_abcdefgh12345!App'


def b64(data):
    return base64.b64encode(data).decode('ascii')


def record(record_id, event_id, fields, user='S-1-5-18'):
    data = ''.join(f'<Data Name="{name}">{value}</Data>' for name, value in fields)
    security = f'<Security UserID="{user}"></Security>' if user else '<Security></Security>'
    xml = (f'<Event xmlns="{NS}"><System><Provider Name="Microsoft-Windows-PushNotifications-Platform" '
           f'Guid="{{88cd9180-4491-4640-b571-e3bee2527943}}"></Provider><EventID>{event_id}</EventID>'
           f'<Version>0</Version><Level>4</Level><TimeCreated SystemTime="2023-01-03 17:29:35.500000+00:00">'
           f'</TimeCreated><EventRecordID>{record_id}</EventRecordID><Execution ProcessID="4" ThreadID="8"></Execution>'
           f'<Channel>Microsoft-Windows-PushNotification-Platform/Operational</Channel><Computer>LAB-PC</Computer>'
           f'{security}</System><EventData>{data}</EventData></Event>')
    return EventRecord(ElementTree.fromstring(xml), LOG)


class _Context:
    @staticmethod
    def get_files_found():
        return [LOG]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1] if '/data/' in path else path


class RowTest(unittest.TestCase):
    def test_a_registration_record_has_the_application_and_the_package(self):
        fields = [('PackageFullName', f' {FULL} '), ('AppUserModelId', f' {APP}\n'), ('AppSettings', '0'), ('AppType', ' 2 '),
                  ('ErrorCode', '0')]
        self.assertEqual(push.push_notification_row(record('7', '2413', fields, user=SID)),
                         (TIME, '2413', 'An application was registered with the following parameters: %1 [PackageFullName] %2 '
                          '[AppUserModelId] %3 [Settings] %4 [AppType] %5 [ErrorCode].', APP, FULL, '',
                          'AppSettings: 0 | AppType: 2 | ErrorCode: 0', '', SID, '7', 'LAB-PC'))

    def test_the_second_spelling_of_the_application_field_fills_the_same_column(self):
        fields = [('AppUserModelID', APP), ('EventId', '{a-b}'), ('Notification Id', '9')]
        row = push.push_notification_row(record('8', '2033', fields))
        self.assertEqual(row[3:8], (APP, '', '', 'EventId: {a-b} | Notification Id: 9', ''))

    def test_of_two_application_fields_the_first_in_the_fixed_order_is_shown_and_the_other_is_kept(self):
        fields = [('AppUserModelID', 'Second'), ('AppUserModelId', 'First')]
        row = push.push_notification_row(record('9', '9999', fields))
        self.assertEqual((row[2], row[3], row[6]), ('', 'First', 'AppUserModelID: Second'))

    def test_an_empty_application_field_still_takes_the_column(self):
        row = push.push_notification_row(record('10', '9999', [('AppUserModelId', ''), ('AppUserModelID', 'Second')]))
        self.assertEqual((row[3], row[6]), ('', 'AppUserModelID: Second'))

    def test_a_session_record_has_the_process_name(self):
        fields = [('Object', '0x1F0'), ('ProcessName', ' C:\\Windows\\explorer.exe ')]
        row = push.push_notification_row(record('11', '3000', fields, user=''))
        self.assertEqual(row, (TIME, '3000', 'Tile session creation is requested for %2 endpoint %1.', '', '',
                               'C:\\Windows\\explorer.exe', 'Object: 0x1F0', '', '', '11', 'LAB-PC'))

    def test_a_command_record_has_its_payload_as_text_and_its_other_fields_in_record_order(self):
        payload = b'CNT 1 CON 12\r\nA\\B: \x00\xff~ \x7f'
        fields = [('Verb', 'CNT'), ('TrID', '1'), ('Namespace', 'CON'), ('CorrelationVector', ''), ('Bytes', '26'),
                  ('Payload', f' {b64(payload)} '), ('ConnectionType', '0'), ('Blank', '  '), ('Text', 'a\nb  c')]
        row = push.push_notification_row(record('12', '1225', fields))
        self.assertEqual(row[2:8], (
            'WNP Transport Layer received command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes of payload: %6.',
            '', '', '', 'Verb: CNT | TrID: 1 | Namespace: CON | Bytes: 26 | ConnectionType: 0 | Text: a\nb  c',
            'CNT 1 CON 12\\x0d\\x0aA\\x5cB: \\x00\\xff~ \\x7f'))

    def test_a_record_with_no_field_and_an_event_id_outside_the_table(self):
        self.assertEqual(push.push_notification_row(record('13', '1005', []))[2:8],
                         ('The Connection Provider status changed to %1.', '', '', '', '', ''))
        row = push.push_notification_row(record('14', '9999', [('Extra', 'kept')]))
        self.assertEqual((row[1], row[2], row[6]), ('9999', '', 'Extra: kept'))


class PayloadTextTest(unittest.TestCase):
    def test_bytes_from_space_to_tilde_are_written_and_the_others_escaped(self):
        self.assertEqual(push.payload_text(b64(bytes(range(256)))),
                         ''.join(f'\\x{n:02x}' for n in range(32)) + ''.join(chr(n) for n in range(32, 92)) + '\\x5c'
                         + ''.join(chr(n) for n in range(93, 127)) + ''.join(f'\\x{n:02x}' for n in range(127, 256)))
        self.assertEqual(push.payload_text(b64(b' ~')), ' ~')
        self.assertEqual(push.payload_text(b64(b'\x1f\x7f')), '\\x1f\\x7f')

    def test_an_empty_value_and_a_value_that_is_not_base64_are_returned_as_they_are(self):
        self.assertEqual(push.payload_text(''), '')
        self.assertEqual(push.payload_text('not base64!'), 'not base64!')
        self.assertEqual(push.payload_text('QUJD='), 'QUJD=')
        self.assertEqual(push.payload_text('QUJ'), 'QUJ')
        self.assertEqual(push.payload_text('QUJD===='), 'QUJD====')
        self.assertEqual(push.payload_text('QQ==QUJD'), 'QQ==QUJD')
        self.assertEqual(push.payload_text('QUJD\n'), 'QUJD\n')
        self.assertEqual(push.payload_text('QUJ-'), 'QUJ-')
        self.assertEqual(push.payload_text('QU JD'), 'QU JD')
        self.assertEqual(push.payload_text('caf\u00e9'), 'caf\u00e9')
        self.assertEqual(push.payload_text('QUJD'), 'ABC')
        self.assertEqual(push.payload_text('QQ=='), 'A')
        self.assertEqual(push.payload_text('QUI='), 'AB')
        self.assertEqual(push.payload_text('QUJDQQ=='), 'ABCA')
        self.assertEqual(push.payload_text('+/+/'), '\\xfb\\xff\\xbf')


class EventTextTest(unittest.TestCase):
    OLD = [('Verb', 'CNT'), ('TrID', '1'), ('Namespace', 'CON'), ('Bytes', '4'), ('Payload', 'QUJDRA=='), ('ConnectionType', '0')]
    NEW = OLD[:3] + [('CorrelationVector', 'cv')] + OLD[3:]

    def test_a_record_with_the_field_names_of_an_earlier_entry_is_given_the_earlier_text(self):
        self.assertEqual(push.event_text(record('1', '1223', self.OLD)),
                         'WNP Transport Layer sent command for the %6 with Verb: %1, Trid: %2, Namespace: %3 containing %4 bytes '
                         'of payload: %5.')
        self.assertEqual(push.event_text(record('2', '1223', self.NEW)),
                         'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes of payload: %6.')
        self.assertEqual(push.event_text(record('3', '1024', [('WasConnected', 'false')])),
                         'Internet connection status changed to Connected (last known status was %1), submitting pending '
                         'workitems.')
        self.assertEqual(push.event_text(record('4', '1024', [('IsConnected', 'true'), ('PendingCount', '0')])),
                         'Internet connection status changed to %1, submitting pending workitems: count = %2.')
        self.assertEqual(push.push_notification_row(record('5', '1268', self.OLD))[2],
                         'WNP Transport Layer received command for the %6 with Verb: %1, Trid: %2, Namespace: %3 containing %4 '
                         'bytes of payload only.')

    def test_the_earlier_text_needs_exactly_the_earlier_field_names_in_their_order(self):
        new = 'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 bytes of payload only.'
        self.assertEqual(push.event_text(record('1', '1267', self.OLD[:5])), new)
        self.assertEqual(push.event_text(record('2', '1267', self.OLD + [('Extra', '1')])), new)
        self.assertEqual(push.event_text(record('3', '1267', self.OLD[1:2] + self.OLD[:1] + self.OLD[2:])), new)
        self.assertEqual(push.event_text(record('4', '1267', [])), new)
        self.assertEqual(push.event_text(record('5', '1005', [])), 'The Connection Provider status changed to %1.')
        self.assertEqual(push.event_text(record('6', '9999', self.OLD)), '')
        self.assertEqual(push.event_text(record('7', '1020', [('Status', '1')])),
                         'The Connection Provider status changed to a failure state: %1.')

    def test_the_earlier_table(self):
        self.assertEqual(push._EARLIER, {  # pylint: disable=protected-access
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
        })

    def test_the_table_holds_the_events_of_the_operational_channel(self):
        self.assertEqual(push._EVENTS, {  # pylint: disable=protected-access
            '19': 'The Windows Push Notification Platform has encountered an error in File: %1, Function %2, '
                  'Line %3, Error %4, ErrorMessage %5.',
            '20': 'The Windows Push Notification Platform has encountered error %2 opening file %1.',
            '37': 'The Windows Push Notification Platform is required to connect on startup, '
                  'ValidChannelsExist : %1.',
            '42': 'Cloud Notifications must be enabled in GP and MDM to receive push notifications.',
            '1003': 'Connect request sent to the Connection Provider.',
            '1004': 'Disconnect request sent the Connection Provider.',
            '1005': 'The Connection Provider status changed to %1.',
            '1006': 'Sending a channel request to the Connection Provider with parameters: %1 '
                    '[PackageFullName] %2 [Properties] %3 [Cookie] %4 [TransactionId].',
            '1007': 'The Connection Provider completed the channel request for transaction id %1.',
            '1008': 'Sending a channel revoke request to the Connection Provider for channel id %1.',
            '1010': '%1 received for ChannelId %2 and AppUserModelId %3 with TrackingId %4, X-WNS-MSG-ID %5, '
                    'timestamp %6 and expiration %7 tag: %8, group: %9, action: %10, bundle: '
                    'count=%11;missed=%12;Id=%13.',
            '1011': 'Sending a request to the Connection Provider to renew a channel with parameters: %1 '
                    '[ChannelId] %2 [PackageFullName] %3 [Properties] %4 [Cookie] %5 [TransactionId].',
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
            '1117': 'Windows Push Notification Service was disconnected due to error: %1 and will now enter '
                    'reconnect mode.',
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
            '1223': 'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 '
                    'bytes of payload: %6.',
            '1224': 'WNP Transport Layer received %1 bytes of payload: %2.',
            '1225': 'WNP Transport Layer received command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 '
                    'bytes of payload: %6.',
            '1226': 'WNP Transport Layer received proxy server response for the %3 of %1 bytes with payload: %2.',
            '1227': 'WNP Transport Layer received command when disconnected with Verb: %1, Trid: %2, '
                    'Namespace: %3, CV: %4 containing %5 bytes of payload: %6.',
            '1233': 'Fast reconnect triggered for previous WNS session (%1) on the %3.',
            '1238': 'WNP Keep Alive Detector starting Test Connection',
            '1239': 'WNP Keep Alive Detector starting KA measurement with value: %2 seconds; type: %1; Min '
                    'Limit: %3 seconds',
            '1240': 'WNP Keep Alive Detector stopping KA measurement',
            '1241': 'WNP Keep Alive Detector lost network over %1.',
            '1242': 'WNP Transport Layer received Power Management event with type %1 on the %2.',
            '1244': 'Connection to the Windows Push Notification Service (%1:%2) failed because proxy host '
                    'detected (%3) could not be used to establish the connection.',
            '1246': 'WNP Transport Layer was disconnected from the Windows Push Notification Service due to '
                    'a loss of network connectivity.',
            '1252': 'The KA value has converged.',
            '1254': 'WNP Transport Layer for %1 detected preferred interface change.',
            '1255': 'WNP Transport Layer for %1 reacting to preferred interface change, disconnect and '
                    'immediately reconnect.',
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
            '1267': 'WNP Transport Layer sent command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 '
                    'bytes of payload only.',
            '1268': 'WNP Transport Layer received command: %1, Trid: %2, Namespace: %3, CV: %4 containing %5 '
                    'bytes of payload only.',
            '1310': 'WNP Transport Layer for %1 detected first fallback interface change.',
            '1311': 'WNP Transport Layer for %1 detected second fallback interface change.',
            '1312': 'WNP Transport Layer detected low WIFI signal quality level (value = %1); and hence '
                    'sending out of band keep alive (PNG) request.',
            '1313': 'WNP Transport Layer detected a significant drop in WIFI signal quality (delta = %1); '
                    'and hence sending out of band keep alive (PNG) request.',
            '1314': 'WNP Transport Layer detected a change in WIFI interface availability (event %1); and '
                    'hence sending out of band keep alive (PNG) request.',
            '1315': 'WNP Transport Layer detected a change in WIFI interface connectivity status (event %1); '
                    'and hence sending out of band keep alive (PNG) request.',
            '2001': 'The channel table has added a valid channel mapping: %1 [ChannelId] %2 [AppUserModelId] '
                    '%3 [ErrorCode].',
            '2002': 'The channel table has removed a channel mapping: %1 [ChannelId] %2 [AppUserModelId] %3 '
                    '[ErrorCode].',
            '2003': 'The channel table has updated a channel mapping: %1 [ChannelId] %2 [AppUserModelId] %3 '
                    '[ErrorCode].',
            '2033': 'A raw notification has activated a background task: %1 [AppUserModelID] %2 [EventId] %3 '
                    '[NotificationID].',
            '2053': 'A periodic update has failed polling URL because X-WNS-GROUP header is invalid: %1 '
                    '[AppUserModelId] %2 [Type] %3 [URL].',
            '2171': 'A call to the settings endpoint happened to unblock all channels for all types.',
            '2413': 'An application was registered with the following parameters: %1 [PackageFullName] %2 '
                    '[AppUserModelId] %3 [Settings] %4 [AppType] %5 [ErrorCode].',
            '2414': 'An application resgistration was updated with the following parameters: %1 '
                    '[PackageFullName] %2 [AppUserModelId] %3 [Settings] %4 [AppType] %5 [ErrorCode].',
            '2415': 'An application was unregistered with the following parameters: %1 [AppUserModelId] %2 '
                    '[ErrorCode]',
            '3000': 'Tile session creation is requested for %2 endpoint %1.',
            '3001': 'Tile session creation is finished for %4 from endpoint %1 with result %3, and %2 is '
                    'assigned as session id.',
            '3004': 'Tile session %1 is being closed',
            '3005': 'Tile session %1 is closed with error code %2.',
            '3006': 'Toast session creation is requested for %2 from endpoint %1.',
            '3007': 'Toast session creation is finished for %4 from endpoint %1 with result %3, and %2 is '
                    'assigned as session id.',
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
            '3141': 'SyncDismissRemoveNotificationUsingActivityParams: MatchOnNotificationId = %1 '
                    'NotificationId = %2 ActivityId = %3',
            '3142': 'Sync Dismiss: Matched Activity using Notification!',
            '3143': 'Sync Dismiss: Matched Notification using Activity!',
            '3144': 'Received WNF_CDP_CDPUSERSVC_READY',
            '3146': '[Sqlite][Warning] Status: %1.',
            '3147': '[Sqlite][Error] Status: %1.',
        })


class ArtifactTest(unittest.TestCase):
    HEADERS = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event', 'App User Model ID', 'Package', 'Process Name',
               'Other Fields', 'Payload', 'User SID', 'Record ID', 'Computer')

    def test_the_log_is_read_for_every_record_of_the_provider_in_record_order(self):
        records = [record('23', '2415', [('AppUserModelId', APP)]), record('21', '1005', [('Status', '1')]),
                   record('22', '2415', [('AppUserModelId', APP)]), record('24', '9999', [])]
        with mock.patch.object(push, 'read_event_records', return_value=(records, [LOG])) as reader:
            headers, rows, source = push.pushNotificationPlatformEvents.__wrapped__(_Context())
        reader.assert_called_once_with(mock.ANY, 'Microsoft-Windows-PushNotification-Platform%4Operational.evtx',
                                       'Push Notification Platform Events', provider='Microsoft-Windows-PushNotifications-Platform')
        self.assertEqual([(row[9], row[1], row[3], row[6]) for row in rows], [
            ('23', '2415', APP, ''), ('21', '1005', '', 'Status: 1'), ('22', '2415', APP, ''), ('24', '9999', '', '')])
        self.assertEqual(source, LOG)
        self.assertEqual(headers, self.HEADERS)
        self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_two_logs_give_both_sources(self):
        with mock.patch.object(push, 'read_event_records', return_value=([record('1', '1005', [])], [LOG, LOG + '.copy'])):
            self.assertEqual(push.pushNotificationPlatformEvents.__wrapped__(_Context())[2], LOG + '\n' + LOG + '.copy')

    def test_a_log_that_was_not_found_gives_no_rows_and_no_source(self):
        with mock.patch.object(push, 'read_event_records', return_value=([], [])):
            self.assertEqual(push.pushNotificationPlatformEvents.__wrapped__(_Context()), (self.HEADERS, [], ''))


if __name__ == '__main__':
    unittest.main()
