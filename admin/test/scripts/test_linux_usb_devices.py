"""Pin how the USB Devices artifacts (scripts/artifacts/linuxUsbDevices.py) assemble device connections from the
kernel's messages in syslog files and in the systemd journal.

The lines are built from the kernel's own format strings (drivers/usb/core/hub.c): hub_port_init()'s connection
line in its forms before and from Linux 2.6.39, announce_device()'s lines with and without bcdDevice (added in
4.17), show_string() and usb_disconnect(). The journal files are written with journal_writer.py.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / 'admin' / 'test' / 'scripts'))

# pylint: disable=wrong-import-position
import journal_writer as jw
from scripts import systemd_journal
from scripts.artifacts import linuxUsbDevices as usb
# pylint: enable=wrong-import-position

UTC = timezone.utc
BOOT_1 = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')
BOOT_2 = bytes.fromhex('00112233445566778899aabbccddeeff')


def syslog(*lines, host='vm'):
    """A syslog file of (time, kernel message) lines, or (time, program, message) for another program."""
    out = []
    for line in lines:
        stamp, program, message = line if len(line) == 3 else (line[0], 'kernel', line[1])
        out.append(f'{stamp} {host} {program}: {message}')
    return ('\n'.join(out) + '\n').encode()


def known_device(stamp='2026-09-26T08:24:43.3', port='2-1', number=2, serial='KNOWN0001'):
    """The lines Linux 7.0 logs for one SuperSpeed device, stamps from stamp."""
    return [(f'{stamp}00001-04:00', f'usb {port}: new SuperSpeed USB device number {number} using xhci_hcd'),
            (f'{stamp}00002-04:00', f'usb {port}: LPM exit latency is zeroed, disabling LPM.'),
            (f'{stamp}00003-04:00', f'usb {port}: New USB device found, idVendor=abcd, idProduct=1234, bcdDevice= 1.10'),
            (f'{stamp}00004-04:00', f'usb {port}: New USB device strings: Mfr=1, Product=2, SerialNumber=3'),
            (f'{stamp}00005-04:00', f'usb {port}: Product: Known Drive'),
            (f'{stamp}00006-04:00', f'usb {port}: Manufacturer: Known Maker'),
            (f'{stamp}00007-04:00', f'usb {port}: SerialNumber: {serial}')]


def fields_of(connection):
    return (connection.connected, connection.disconnected, connection.connected_recorded,
            connection.disconnected_recorded, connection.vendor, connection.product_id, connection.manufacturer,
            connection.product, connection.serial, connection.release, connection.port, connection.number,
            connection.speed, connection.driver, connection.host, connection.sources)


class FormatTest(unittest.TestCase):
    def test_connection_lines_in_each_kernel_form(self):
        self.assertEqual(usb.new_line('new SuperSpeed USB device number 8 using xhci_hcd'),
                         ('new', 'SuperSpeed', '8', 'xhci_hcd'))
        self.assertEqual(usb.new_line('new SuperSpeed Plus Gen 2x1 USB device number 3 using xhci_hcd'),
                         ('new', 'SuperSpeed Plus Gen 2x1', '3', 'xhci_hcd'))
        self.assertEqual(usb.new_line('new high-speed USB device number 2 using ehci-pci'),
                         ('new', 'high-speed', '2', 'ehci-pci'))
        self.assertEqual(usb.new_line('new high speed USB device number 4 using ehci_hcd'),  # 2.6.39 to 3.1
                         ('new', 'high speed', '4', 'ehci_hcd'))
        self.assertEqual(usb.new_line('new full speed USB device using uhci_hcd and address 2'),  # before 2.6.39
                         ('new', 'full speed', '2', 'uhci_hcd'))
        self.assertEqual(usb.new_line('reset high-speed USB device number 2 using xhci_hcd')[0], 'reset')
        self.assertIsNone(usb.new_line('New USB device found, idVendor=abcd, idProduct=1234'))

    def test_log_family(self):
        self.assertEqual(usb.log_family('syslog'), ('syslog', (2, 0, '')))
        self.assertEqual(usb.log_family('kern.log.3.gz'), ('kern.log', (0, -3, '')))
        self.assertEqual(usb.log_family('messages-20260920'), ('messages', (1, 0, '20260920')))
        self.assertEqual(usb.log_family('messages-20260920.gz'), ('messages', (1, 0, '20260920')))
        self.assertIsNone(usb.log_family('auth.log'))
        self.assertIsNone(usb.log_family('syslog.old'))


class SyslogTest(unittest.TestCase):
    def test_one_connection_with_everything(self):
        data = syslog(('2026-09-26T08:24:43.1-04:00', 'Linux version 7.0.0-34-generic (buildd@host) #34'),
                      ('2026-09-26T08:24:43.2-04:00', 'usb usb2: New USB device found, idVendor=1d6b, idProduct=0003, '
                                                      'bcdDevice= 7.00'),
                      *known_device(),
                      ('2026-09-26T09:00:00.5-04:00', 'usb 2-1: reset SuperSpeed USB device number 2 using xhci_hcd'),
                      ('2026-09-26T09:30:00.5-04:00', 'systemd', 'usb 2-1: USB disconnect, device number 2'),
                      ('2026-09-26T10:00:00.25-04:00', 'usb 2-1: USB disconnect, device number 2'))
        counts = Counter()
        rows = usb.syslog_connections([('var/log/syslog', data)], counts)
        self.assertEqual([fields_of(r) for r in rows], [(
            datetime(2026, 9, 26, 12, 24, 43, 300001, tzinfo=UTC), datetime(2026, 9, 26, 14, 0, 0, 250000, tzinfo=UTC),
            '2026-09-26T08:24:43.300001-04:00', '2026-09-26T10:00:00.25-04:00', 'abcd', '1234', 'Known Maker',
            'Known Drive', 'KNOWN0001', '1.10', '2-1', '2', 'SuperSpeed', 'xhci_hcd', 'vm', ['var/log/syslog'])])
        self.assertEqual(counts, Counter({usb.RESETS: 1, usb.ROOT_HUBS: 1, usb.OTHER: 1}))

    def test_debian_5_forms_with_the_kernel_time_kept(self):
        data = syslog(('Jan 18 09:31:30', '[    6.160845] usb 1-1: new full speed USB device using uhci_hcd and '
                                          'address 2'),
                      ('Jan 18 09:31:30', '[    6.200000] usb 1-1: configuration #1 chosen from 1 choice'),
                      ('Jan 18 09:31:30', '[    6.268741] usb 1-1: New USB device found, idVendor=0781, idProduct=5567'),
                      ('Jan 18 09:31:30', '[    6.268769] usb 1-1: New USB device strings: Mfr=1, Product=2, '
                                          'SerialNumber=3'),
                      ('Jan 18 09:31:30', '[    6.268800] usb 1-1: Product: Cruzer Blade'),
                      ('Jan 18 09:55:02', '[ 1413.500000] usb 1-1: USB disconnect, address 2'), host='victoria')
        counts = Counter()
        rows = usb.syslog_connections([('var/log/kern.log', data)], counts)
        self.assertEqual([fields_of(r) for r in rows], [(
            '', '', 'Jan 18 09:31:30', 'Jan 18 09:55:02', '0781', '5567', '', 'Cruzer Blade', '', '', '1-1', '2',
            'full speed', 'uhci_hcd', 'victoria', ['var/log/kern.log'])])
        self.assertEqual(counts, Counter({usb.OTHER: 1}))

    def test_a_boot_ends_what_is_open_and_numbers_start_again(self):
        data = syslog(*known_device('2026-09-26T08:00:00.1'),
                      ('2026-09-27T08:00:00.0-04:00', '[    0.000000] Linux version 7.0.0-34-generic'),
                      *known_device('2026-09-27T08:00:01.1'),
                      ('2026-09-27T09:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2'))
        rows = usb.syslog_connections([('var/log/syslog', data)], Counter())
        self.assertEqual([(r.connected_recorded[:10], r.disconnected_recorded[:13]) for r in rows],
                         [('2026-09-26', ''), ('2026-09-27', '2026-09-27T09')])

    def test_rotations_are_read_oldest_first(self):
        older = syslog(*known_device('2026-09-20T08:00:00.1'))
        newer = syslog(('2026-09-21T08:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2'))
        rows = usb.syslog_connections([('var/log/syslog', b''), ('var/log/syslog.1', newer),
                                       ('var/log/syslog.2.gz', older)], Counter())
        self.assertEqual([(r.disconnected_recorded[:10], r.sources) for r in rows],
                         [('2026-09-21', ['var/log/syslog.2.gz', 'var/log/syslog.1'])])

    def test_a_connection_whose_lines_span_a_rotation_names_both_files(self):
        lines = known_device()
        rows = usb.syslog_connections([('var/log/syslog', syslog(*lines[2:])), ('var/log/syslog.1', syslog(*lines[:2]))],
                                      Counter())
        self.assertEqual([(r.vendor, r.serial, r.sources) for r in rows],
                         [('abcd', 'KNOWN0001', ['var/log/syslog.1', 'var/log/syslog'])])
        rows = usb.syslog_connections([('var/log/syslog', syslog(lines[2])), ('var/log/syslog.1', syslog(*lines[:2]))],
                                      Counter())
        self.assertEqual([(r.vendor, r.sources) for r in rows], [('abcd', ['var/log/syslog.1', 'var/log/syslog'])])

    def test_a_name_like_no_syslog_file_is_not_read(self):
        counts = Counter()
        self.assertEqual(usb.syslog_connections([('var/log/syslog.old', syslog(*known_device()))], counts), [])
        self.assertEqual(counts, Counter({'files named like no syslog file, not read': 1}))

    def test_a_boot_line_in_either_form_closes_the_open_port(self):
        for boot_line in ('Linux version 7.0.0-34-generic', '[    0.000000] Linux version 2.6.26-2-686'):
            counts = Counter()
            data = syslog(*known_device(),
                          ('2026-09-27T08:00:00.0-04:00', boot_line),
                          ('2026-09-27T09:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2'))
            rows = usb.syslog_connections([('var/log/syslog', data)], counts)
            self.assertEqual((rows[0].disconnected_recorded, counts[usb.ORPHAN_GONE]), ('', 1), boot_line)

    def test_a_string_line_after_the_disconnect_is_counted_not_applied(self):
        counts = Counter()
        data = syslog(*known_device(), ('2026-09-26T10:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2'),
                      ('2026-09-26T10:00:01.0-04:00', 'usb 2-1: Product: Late'))
        rows = usb.syslog_connections([('var/log/syslog', data)], counts)
        self.assertEqual((rows[0].product, counts[usb.ORPHAN_STRING]), ('Known Drive', 1))

    def test_a_connection_in_syslog_and_kern_log_is_reported_once(self):
        both = [*known_device()]
        syslog_data = syslog(*both)
        kern_data = syslog(*both, ('2026-09-26T10:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2'))
        counts = Counter()
        rows = usb.syslog_connections([('var/log/syslog', syslog_data), ('var/log/kern.log', kern_data)], counts)
        self.assertEqual([(r.disconnected_recorded[:13], r.sources) for r in rows],
                         [('2026-09-26T10', ['var/log/syslog', 'var/log/kern.log'])])
        self.assertEqual(counts[usb.ORPHAN_GONE], 0)

    def test_a_disconnect_is_an_orphan_only_when_no_log_holds_its_connection(self):
        gone = ('2026-09-26T10:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 2')
        syslog_data = syslog(gone, ('2026-09-26T11:00:00.0-04:00', 'usb 3-2: USB disconnect, device number 7'))
        kern_data = syslog(*known_device(), gone)
        counts = Counter()
        rows = usb.syslog_connections([('var/log/syslog', syslog_data), ('var/log/kern.log', kern_data)], counts)
        self.assertEqual(len(rows), 1)
        self.assertEqual(counts[usb.ORPHAN_GONE], 1)

    def test_a_disconnect_of_another_device_number_does_not_close_the_connection(self):
        data = syslog(*known_device(), ('2026-09-26T10:00:00.0-04:00', 'usb 2-1: USB disconnect, device number 9'))
        counts = Counter()
        rows = usb.syslog_connections([('var/log/syslog', data)], counts)
        self.assertEqual((rows[0].disconnected_recorded, counts[usb.ORPHAN_GONE]), ('', 1))

    def test_announced_with_no_connection_line_and_connection_with_no_announcement(self):
        data = syslog(('2026-09-26T08:00:00.1-04:00', 'usb 1-3: new high-speed USB device number 5 using xhci_hcd'),
                      ('2026-09-26T08:00:00.2-04:00', 'usb 1-3: device descriptor read/64, error -71'),
                      ('2026-09-26T08:00:01.1-04:00', 'usb 1-4: New USB device found, idVendor=0781, idProduct=5567, '
                                                      'bcdDevice= 1.00'),
                      ('2026-09-26T08:00:01.2-04:00', 'usb 1-4: Product: Cruzer'),
                      ('2026-09-26T08:00:02.0-04:00', 'usb 1-5: Product: Nothing Before'))
        counts = Counter()
        rows = usb.syslog_connections([('var/log/syslog', data)], counts)
        self.assertEqual([(r.port, r.number, r.speed, r.vendor, r.product) for r in rows],
                         [('1-3', '5', 'high-speed', '', ''), ('1-4', '', '', '0781', 'Cruzer')])
        self.assertEqual(counts, Counter({usb.OTHER: 1, usb.ORPHAN_STRING: 1}))

    def test_a_second_announcement_on_an_open_port_starts_another_connection(self):
        data = syslog(*known_device(),
                      ('2026-09-26T08:30:00.0-04:00', 'usb 2-1: New USB device found, idVendor=0781, idProduct=5567, '
                                                      'bcdDevice= 1.00'))
        rows = usb.syslog_connections([('var/log/syslog', data)], Counter())
        self.assertEqual([r.vendor for r in rows], ['abcd', '0781'])

    def test_offsets_convert_to_utc_and_strings_keep_the_first(self):
        data = syslog(('2026-08-31T20:12:43.686081+04:00', 'usb 2-1: new SuperSpeed USB device number 5 using xhci_hcd'),
                      ('2026-08-31T20:12:43.7+04:00', 'usb 2-1: Product: First'),
                      ('2026-08-31T20:12:43.8+04:00', 'usb 2-1: Product: Second'))
        row = usb.syslog_connections([('var/log/syslog', data)], Counter())[0]
        self.assertEqual((row.connected, row.product), (datetime(2026, 8, 31, 16, 12, 43, 686081, tzinfo=UTC), 'First'))

    def test_lines_of_other_programs_and_other_drivers_are_left_alone(self):
        data = syslog(('2026-09-26T08:00:00.1-04:00', 'systemd', 'usb 2-1: new SuperSpeed USB device number 2 using x'),
                      ('2026-09-26T08:00:00.2-04:00', 'usb-storage 2-1:1.0: USB Mass Storage device detected'),
                      ('2026-09-26T08:00:00.3-04:00', 'hub 2-0:1.0: USB hub found'))
        counts = Counter()
        self.assertEqual(usb.syslog_connections([('var/log/syslog', data)], counts), [])
        self.assertEqual(counts, Counter())


def journal(entries, boot=BOOT_1):
    """A journal file of (realtime seconds, monotonic seconds, MESSAGE, transport, boot) entries."""
    writer = jw.JournalWriter(boot_id=boot)
    for realtime, monotonic, message, transport, entry_boot in entries:
        writer.add_entry([('_TRANSPORT', transport), ('MESSAGE', message.encode()), ('_HOSTNAME', b'vm')],
                         int(realtime * 1000000), int(monotonic * 1000000), boot_id=entry_boot)
    return systemd_journal.JournalFile(writer.bytes())


class JournalTest(unittest.TestCase):
    T0 = 1790000000.0

    def test_a_connection_split_over_two_files_and_boots_kept_apart(self):
        t = self.T0
        first = journal([(t + 1, 1, 'usb 2-1: new SuperSpeed USB device number 2 using xhci_hcd', b'kernel', BOOT_1),
                         (t + 1.1, 1.1, 'usb 2-1: New USB device found, idVendor=abcd, idProduct=1234, bcdDevice= 1.10',
                          b'kernel', BOOT_1),
                         (t + 1.2, 1.2, 'usb 2-1: SerialNumber: KNOWN0001', b'kernel', BOOT_1),
                         (t + 1.3, 1.3, 'usb 2-1: USB disconnect, device number 2', b'syslog', BOOT_1)])
        second = journal([(t + 60, 60, 'usb 2-1: USB disconnect, device number 2', b'kernel', BOOT_1),
                          (t + 100, 1, 'usb 2-1: new SuperSpeed USB device number 2 using xhci_hcd', b'kernel', BOOT_2),
                          (t + 101, 2, 'usb 2-1: USB disconnect, device number 2', b'kernel', BOOT_2)])
        counts = Counter()
        rows = usb.journal_connections([('b.journal', second), ('a.journal', first)], counts)
        self.assertEqual([(r.connected.timestamp(), r.disconnected.timestamp(), r.vendor, r.serial, r.sources)
                          for r in rows],
                         [(t + 1, t + 60, 'abcd', 'KNOWN0001', ['a.journal', 'b.journal']),
                          (t + 100, t + 101, '', '', ['b.journal'])])
        self.assertEqual(len({r.boot for r in rows}), 2)
        self.assertEqual(counts, Counter())

    def test_two_entries_of_one_file_with_the_same_time_and_message_are_both_read(self):
        t = self.T0
        line = 'usb 2-1: new SuperSpeed USB device number 2 using xhci_hcd'
        counts = Counter()
        usb.journal_connections([('a.journal', journal([(t + 1, 1, line, b'kernel', BOOT_1),
                                                        (t + 1, 1, line, b'kernel', BOOT_1)]))], counts)
        self.assertEqual(counts['entries also in another journal file, reported once'], 0)

    def test_an_entry_in_two_files_is_read_once(self):
        t = self.T0
        entries = [(t + 1, 1, 'usb 2-1: new SuperSpeed USB device number 2 using xhci_hcd', b'kernel', BOOT_1)]
        counts = Counter()
        rows = usb.journal_connections([('a.journal', journal(entries)), ('a.journal~', journal(entries))], counts)
        self.assertEqual((len(rows), rows[0].sources), (1, ['a.journal']))
        self.assertEqual(counts['entries also in another journal file, reported once'], 1)


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):
    def test_syslog_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            log_dir = os.path.join(root, 'var', 'log')
            os.makedirs(log_dir)
            paths = []
            for name, data in (('syslog', syslog(*known_device())), ('kern.log', syslog(*known_device())),
                               ('syslog.1', syslog(('2026-09-25T08:00:00.0-04:00', 'usb usb1: Product: xHCI')))):
                paths.append(os.path.join(log_dir, name))
                with open(paths[-1], 'wb') as handle:
                    handle.write(data)
            paths.append(log_dir)
            with mock.patch.object(usb, 'logfunc') as log:
                headers, rows, source = usb.linuxUsbDevicesSyslog.__wrapped__(FakeContext(paths, root))
        self.assertEqual(headers, (('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'),
                                   'Connected as Recorded', 'Disconnected as Recorded', 'Vendor ID', 'Product ID',
                                   'Manufacturer', 'Product', 'Serial Number', 'Device Release', 'Port',
                                   'Device Number', 'Speed', 'Host Controller Driver', 'Hostname', 'Source File'))
        self.assertEqual([row[-1] for row in rows], ['var/log/syslog\nvar/log/kern.log'])
        self.assertEqual(source, 'var/log/syslog\nvar/log/kern.log')
        log.assert_called_once_with('USB Devices (syslog): 1 lines about root hubs (usbN), not reported, '
                                    '1 other lines about a device, not reported')

    def test_journal_artifact(self):
        t = JournalTest.T0
        writer = jw.JournalWriter(boot_id=BOOT_1)
        writer.add_entry([('_TRANSPORT', b'kernel'), ('_HOSTNAME', b'vm'),
                          ('MESSAGE', b'usb 1-1: new high-speed USB device number 2 using xhci_hcd')],
                         int(t * 1000000), 1000000)
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'var', 'log', 'journal', 'm', 'system.journal')
            os.makedirs(os.path.dirname(path))
            with open(path, 'wb') as handle:
                handle.write(writer.bytes())
            with mock.patch.object(usb, 'logfunc') as log:
                headers, rows, source = usb.linuxUsbDevicesJournal.__wrapped__(
                    FakeContext([path, os.path.dirname(path)], root))
        self.assertEqual(len(headers), 15)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0][0], rows[0][8], rows[0][9], rows[0][12], rows[0][13], rows[0][-1]),
                         (datetime.fromtimestamp(t, UTC), '1-1', '2', 'vm', BOOT_1.hex(),
                          'var/log/journal/m/system.journal'))
        self.assertEqual(source, 'var/log/journal/m/system.journal')
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
