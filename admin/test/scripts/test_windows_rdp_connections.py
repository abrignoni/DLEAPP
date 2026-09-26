"""Pin the rows of scripts/artifacts/windowsRdpConnections.py."""
import pathlib
import sys
import unittest
from xml.etree import ElementTree

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsRdpConnections as rdp  # pylint: disable=wrong-import-position
from scripts.windows_evtx import EventRecord  # pylint: disable=wrong-import-position

_NS = 'http://schemas.microsoft.com/win/2004/08/events/event'


def event(event_id, fields):
    data = ''.join(f'<{name}>{value}</{name}>' for name, value in fields.items())
    xml = (f'<Event xmlns="{_NS}"><System><Provider Name="{rdp._PROVIDER}"/>'  # pylint: disable=protected-access
           f'<EventID>{event_id}</EventID><TimeCreated SystemTime="2020-09-19 03:36:23.009739+00:00"/>'
           '<EventRecordID>39</EventRecordID><Computer>HOST</Computer></System>'
           f'<UserData><EventXML xmlns="Event_NS">{data}</EventXML></UserData></Event>')
    return EventRecord(ElementTree.fromstring(xml), 'log.evtx')


class ConnectionRowTest(unittest.TestCase):
    def test_authentication_succeeded(self):
        row = rdp.connection_row(event('1149', {'Param1': 'Administrator', 'Param2': 'C137',
                                                'Param3': '10.42.85.10'}))
        self.assertEqual(row[1:], ('1149', 'Remote Desktop Services: User authentication succeeded',
                                   'Administrator', 'C137', '10.42.85.10', '', 'HOST', '39'))
        self.assertEqual(row[0].isoformat(), '2020-09-19T03:36:23.009739+00:00')

    def test_config_merged_accepted_and_listener(self):
        self.assertEqual(rdp.connection_row(event('1150', {'Param1': 'u', 'Param2': 'd',
                                                           'Param3': '10.0.0.1'}))[3:6],
                         ('u', 'd', '10.0.0.1'))
        self.assertEqual(rdp.connection_row(event('1158', {'Param1': '10.0.0.2'}))[3:7],
                         ('', '', '10.0.0.2', ''))
        self.assertEqual(rdp.connection_row(event('261', {'listenerName': 'RDP-Tcp'}))[2:7],
                         ('Listener received a connection', '', '', '', 'RDP-Tcp'))


if __name__ == '__main__':
    unittest.main()
