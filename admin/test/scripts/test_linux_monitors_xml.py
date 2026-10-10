"""Pin the Display Configurations (monitors.xml) artifact (scripts/artifacts/linuxMonitorsXml.py).

EXAMPLE is the example configuration in the comment of mutter 50.1's meta-monitor-config-store.c, shortened; ONE has
the single-line layout mutter wrote on ubuntu2604_arm64_monitors.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxMonitorsXml as mx
# pylint: enable=wrong-import-position


def spec(connector, letter):
    return (f'<monitorspec><connector>{connector}</connector><vendor>Vendor {letter}</vendor>'
            f'<product>Product {letter}</product><serial>Serial {letter}</serial></monitorspec>')


EXAMPLE = ('<monitors version="2">\n  <configuration>\n    <layoutmode>logical</layoutmode>\n    <logicalmonitor>\n'
           '      <x>0</x><y>0</y><scale>1</scale>\n      <monitor>' + spec('LVDS1', 'A')
           + '<mode><width>1920</width><height>1080</height><rate>60.049972534179688</rate></mode></monitor>\n'
           '      <transform><rotation>right</rotation><flipped>no</flipped></transform>\n      <primary>yes</primary>\n'
           '    </logicalmonitor>\n    <logicalmonitor><x>1920</x><y>1080</y><monitor>' + spec('LVDS2', 'B')
           + '<mode><width>1280</width><height> 720 </height><rate>59.9</rate></mode></monitor>\n'
           '    </logicalmonitor>\n    <disabled>' + spec('LVDS3', 'C') + spec('LVDS4', 'D') + '</disabled>\n'
           '    <forlease>' + spec('LVDS5', 'E') + '</forlease>\n  </configuration>\n'
           '  <configuration><logicalmonitor><x>0</x><y>0</y><monitor>' + spec('DP-1', 'F')
           + '</monitor></logicalmonitor></configuration>\n</monitors>\n').encode()
ONE = (b'<monitors version="2"><configuration><logicalmonitor><monitor><monitorspec><connector>Virtual-1</connector>'
       b'<vendor>unknown</vendor><product>unknown</product><serial>unknown</serial></monitorspec><mode>'
       b'<width>1024</width><height>768</height><rate>59.949383</rate></mode></monitor><x>0</x><y>0</y>'
       b'<scale>1</scale><primary>yes</primary></logicalmonitor></configuration></monitors>')
ROWS = [
    (1, 'Enabled', 'LVDS1', 'Vendor A', 'Product A', 'Serial A', '1920', '1080', '60.049972534179688', '0', '0', '1',
     'yes', 'right', 'logical'),
    (1, 'Enabled', 'LVDS2', 'Vendor B', 'Product B', 'Serial B', '1280', '720', '59.9', '1920', '1080', '', '', '',
     'logical'),
    (1, 'Disabled', 'LVDS3', 'Vendor C', 'Product C', 'Serial C', '', '', '', '', '', '', '', '', 'logical'),
    (1, 'Disabled', 'LVDS4', 'Vendor D', 'Product D', 'Serial D', '', '', '', '', '', '', '', '', 'logical'),
    (1, 'For Lease', 'LVDS5', 'Vendor E', 'Product E', 'Serial E', '', '', '', '', '', '', '', '', 'logical'),
    (2, 'Enabled', 'DP-1', 'Vendor F', 'Product F', 'Serial F', '', '', '', '0', '0', '', '', '', '')]


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class Rows(unittest.TestCase):
    def test_the_example(self):
        self.assertEqual(mx.monitor_rows(EXAMPLE), ROWS)

    def test_the_layout_mutter_wrote(self):
        self.assertEqual(mx.monitor_rows(ONE), [(1, 'Enabled', 'Virtual-1', 'unknown', 'unknown', 'unknown', '1024',
                                                 '768', '59.949383', '0', '0', '1', 'yes', '', '')])

    def test_two_monitors_of_one_logical_monitor_share_its_place(self):
        data = (b'<monitors version="2"><configuration><logicalmonitor><x>5</x><y>6</y><scale>2</scale><monitor>'
                + spec('A-1', 'A').encode() + b'</monitor><monitor>' + spec('B-1', 'B').encode()
                + b'</monitor></logicalmonitor></configuration></monitors>')
        self.assertEqual([(r[2], r[9], r[10], r[11]) for r in mx.monitor_rows(data)],
                         [('A-1', '5', '6', '2'), ('B-1', '5', '6', '2')])

    def test_white_space_around_a_disabled_monitor_name(self):
        data = (b'<monitors version="2"><configuration><disabled><monitorspec><connector>\n  DP-9\n</connector>'
                b'</monitorspec></disabled></configuration></monitors>')
        self.assertEqual(mx.monitor_rows(data)[0][:4], (1, 'Disabled', 'DP-9', ''))

    def test_no_configuration(self):
        self.assertEqual(mx.monitor_rows(b'<monitors version="2"></monitors>'), [])

    def test_other_versions(self):
        self.assertIs(mx.monitor_rows(b'<monitors version="1"><configuration/></monitors>'), False)
        self.assertIs(mx.monitor_rows(b'<monitors><configuration/></monitors>'), False)

    def test_not_a_monitors_file(self):
        for data in (b'', b'not xml', b'<monitors version="2">', b'<other version="2"/>', ONE[:-5]):
            self.assertIsNone(mx.monitor_rows(data), data[:20])


class Processor(unittest.TestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as root:
            files = {'home/a/.config/monitors.xml': ONE, 'home/a/.config/monitors.xml~': EXAMPLE,
                     'home/b/.config/monitors.xml': b'<monitors version="1"/>', 'home/c/.config/monitors.xml': b'junk',
                     'home/d/.config/monitors.xml': b'<monitors version="2"/>'}
            paths = []
            for name, data in files.items():
                path = os.path.join(root, *name.split('/'))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as handle:
                    handle.write(data)
                paths.append(path)
            paths += [os.path.join(root, 'home', 'e', '.config', 'monitors.xml'), os.path.join(root, 'home')]
            with mock.patch.object(mx, 'logfunc') as log:
                headers, data, located = mx.linuxMonitorsXml.__wrapped__(FakeContext(paths[::-1], root))
        self.assertEqual(len(headers), 16)
        self.assertEqual(headers[-1], 'Source File')
        first = os.path.join('home', 'a', '.config', 'monitors.xml')
        self.assertEqual(data[0][0:3] + data[0][-1:], (1, 'Enabled', 'Virtual-1', first))
        self.assertEqual(data[1:], [row + (first + '~',) for row in ROWS])
        self.assertEqual([os.path.relpath(p, root) for p in located.split('\n')], [first, first + '~'])
        message = log.call_args[0][0]
        for part in ('1 files that could not be read', '1 files that are not a monitors.xml, not read',
                     '1 files in a format version other than 2, not read'):
            self.assertIn(part, message)

    def test_nothing_found(self):
        with mock.patch.object(mx, 'logfunc') as log:
            self.assertEqual(mx.linuxMonitorsXml.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
