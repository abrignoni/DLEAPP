"""Pin how the USB Storage Devices artifacts (scripts/artifacts/linuxUsbDevices.py) attach the SCSI devices the
usb-storage driver made to the USB connections the kernel logged.

The lines are built from the kernel's own format strings: usb_stor_probe1() in drivers/usb/storage/usb.c, the host
name scsi_add_host() prints, scsi_add_lun()'s identification line in drivers/scsi/scsi_scan.c and the sd driver's
capacity, write protect and attach lines in drivers/scsi/sd.c, in their forms before Linux 2.6.28, from 2.6.28 to
2.6.30 and from 2.6.31. The devices are made up. The journal files are written with journal_writer.py.
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
from scripts.artifacts import linuxUsbDevices as usb
# pylint: enable=wrong-import-position

UTC = timezone.utc
BOOT_1 = bytes.fromhex('0f1e2d3c4b5a69788796a5b4c3d2e1f0')


def syslog(*lines, host='vm'):
    """A syslog file of (time, kernel message) lines."""
    return ('\n'.join(f'{stamp} {host} kernel: {message}' for stamp, message in lines) + '\n').encode()


def ident(kind, vendor, model, revision):
    """The text scsi_add_lun() prints between the address and PQ, with the strings padded as Linux 4.6 on pads
    them and the device type as scsi_device_type() spells it."""
    return f'{kind:<16} {vendor:<8.8} {model:<16.16} {revision:<4.4}'


def stick(port='3-1', number=2, host=6, disk='sdb', stamp='2026-09-29T10:20:22.', serial='KNOWN0001', lun='0'):
    """The lines Linux 7.0 logs for a USB flash drive, stamps from stamp."""
    address = f'{host}:0:0:{lun}'
    return [(f'{stamp}100000-04:00', f'usb {port}: new high-speed USB device number {number} using ehci-pci'),
            (f'{stamp}100001-04:00', f'usb {port}: New USB device found, idVendor=abcd, idProduct=1234, bcdDevice= 1.00'),
            (f'{stamp}100002-04:00', f'usb {port}: Product: Known Stick'),
            (f'{stamp}100003-04:00', f'usb {port}: Manufacturer: Known Maker'),
            (f'{stamp}100004-04:00', f'usb {port}: SerialNumber: {serial}'),
            (f'{stamp}200000-04:00', f'usb-storage {port}:1.0: USB Mass Storage device detected'),
            (f'{stamp}200001-04:00', f'scsi host{host}: usb-storage {port}:1.0'),
            (f'{stamp}300000-04:00', f'scsi {address}: {ident("Direct-Access", "Known", "Known Stick", "1.00")} '
                                     f'PQ: 0 ANSI: 6'),
            (f'{stamp}300001-04:00', f'sd {address}: Attached scsi generic sg2 type 0'),
            (f'{stamp}300002-04:00', f'sd {address}: [{disk}] 31588352 512-byte logical blocks: (16.2 GB/15.1 GiB)'),
            (f'{stamp}300003-04:00', f'sd {address}: [{disk}] Write Protect is off'),
            (f'{stamp}300004-04:00', f'sd {address}: [{disk}] Attached SCSI removable disk')]


def run_syslog(files):
    counts = Counter()
    connections = usb.syslog_connections(files, counts, usb.StorageAssembler, usb._storage_message)  # pylint: disable=protected-access
    return usb.storage_rows(connections, counts), counts


def disk_fields(disk):
    return (disk.name, disk.vendor, disk.model, disk.revision, disk.kind, disk.capacity, disk.blocks, disk.block_size,
            disk.removable, disk.write_protect, disk.address)


class FormatTest(unittest.TestCase):
    def test_identification_split_by_the_padded_widths(self):
        self.assertEqual(usb.split_identification(ident('Direct-Access', 'Known', 'Known Stick', '1.00')),
                         ('Direct-Access', 'Known', 'Known Stick', '1.00', False))
        self.assertEqual(usb.split_identification(ident('CD-ROM', 'AB CD', 'Two  Spaces', '')),
                         ('CD-ROM', 'AB CD', 'Two  Spaces', '', False))

    def test_identification_a_nul_cut_short_is_kept_whole(self):
        # before Linux 4.6 a NUL ends %.8s early, so the widths no longer hold
        self.assertEqual(usb.split_identification('Direct-Access     Kn Stick 1.0'),
                         ('', '', 'Direct-Access     Kn Stick 1.0', '', True))

    def test_capacity_in_each_kernel_form(self):
        for body, expected in (('31588352 512-byte logical blocks: (16.2 GB/15.1 GiB)',
                                ('31588352', '512', '16.2 GB/15.1 GiB')),
                               ('31588352 512-byte hardware sectors: (16.1 GB/15.0 GiB)',
                                ('31588352', '512', '16.1 GB/15.0 GiB')),
                               ('31588352 512-byte hardware sectors (16173 MB)', ('31588352', '512', '16173 MB'))):
            match = usb.CAPACITY.fullmatch(body) or usb.CAPACITY_MB.fullmatch(body)
            self.assertEqual(match.groups(), expected)


class SyslogTest(unittest.TestCase):
    def test_one_stick_from_connection_to_disk(self):
        rows, counts = run_syslog([('var/log/syslog', syslog(*stick(), ('2026-09-29T10:21:41.189126-04:00',
                                                                         'usb 3-1: USB disconnect, device number 2')))])
        self.assertEqual(len(rows), 1)
        connection, disk = rows[0]
        self.assertEqual(disk_fields(disk), ('sdb', 'Known', 'Known Stick', '1.00', 'Direct-Access',
                                             '16.2 GB/15.1 GiB', '31588352', '512', 'Yes', 'off', '6:0:0:0'))
        self.assertEqual((connection.interface, connection.scsi_host, connection.vendor, connection.serial,
                          connection.connected_recorded, connection.disconnected_recorded),
                         ('3-1:1.0', '6', 'abcd', 'KNOWN0001', '2026-09-29T10:20:22.100000-04:00',
                          '2026-09-29T10:21:41.189126-04:00'))
        self.assertEqual(counts, Counter())

    def test_a_stick_behind_a_hub(self):
        rows, _counts = run_syslog([('var/log/syslog', syslog(*stick(port='3-1.4')))])
        self.assertEqual([(c.port, c.interface, d.name) for c, d in rows], [('3-1.4', '3-1.4:1.0', 'sdb')])

    def test_only_the_detected_line_makes_a_storage_device(self):
        lines = stick()[:5] + [('2026-09-29T10:20:22.2-04:00', 'usb-storage 3-1:1.0: Quirks match for vid abcd pid 1234: 800000')]
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(rows, [])

    def test_the_ccs_suffix_is_read(self):
        lines = stick()
        lines[7] = (lines[7][0], lines[7][1] + ' CCS')
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(disk_fields(rows[0][1])[1:5], ('Known', 'Known Stick', '1.00', 'Direct-Access'))

    def test_the_first_disk_name_is_kept(self):
        lines = stick() + [('2026-09-29T10:20:22.400000-04:00', 'sd 6:0:0:0: [sdz] Write Protect is off')]
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(rows[0][1].name, 'sdb')

    def test_disk_lines_only_kern_log_holds_are_added(self):
        rows, _counts = run_syslog([('var/log/syslog', syslog(*stick()[:7])), ('var/log/kern.log', syslog(*stick()))])
        self.assertEqual([(c.sources, d.name if d else None) for c, d in rows],
                         [(['var/log/syslog', 'var/log/kern.log'], 'sdb')])

    def test_a_host_number_reused_after_a_disconnect_names_the_new_device(self):
        lines = stick() + [('2026-09-29T10:21:41.189126-04:00', 'usb 3-1: USB disconnect, device number 2')] + \
            stick(port='3-2', number=3, stamp='2026-09-29T10:38:35.', serial='KNOWN0002')
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual([(c.port, c.serial, d.name, d.address) for c, d in rows],
                         [('3-1', 'KNOWN0001', 'sdb', '6:0:0:0'), ('3-2', 'KNOWN0002', 'sdb', '6:0:0:0')])

    def test_a_disk_line_after_the_disconnect_is_counted_not_applied(self):
        lines = stick() + [('2026-09-29T10:21:41.1-04:00', 'usb 3-1: USB disconnect, device number 2'),
                           ('2026-09-29T10:21:41.2-04:00', 'sd 6:0:0:0: [sdb] Synchronize Cache(10) failed')]
        rows, counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(len(rows), 1)
        self.assertEqual(counts[usb.STORAGE_ORPHAN], 1)

    def test_a_card_reader_with_two_slots_gives_a_row_for_each(self):
        lines = stick(host=7, disk='sdc') + [
            ('2026-09-29T10:20:22.4-04:00', f'scsi 7:0:0:1: {ident("Direct-Access", "Known", "SD Slot", "1.00")} '
                                            f'PQ: 0 ANSI: 6'),
            ('2026-09-29T10:20:22.5-04:00', 'sd 7:0:0:1: [sdd] Attached SCSI removable disk')]
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual([disk_fields(d) for _c, d in rows], [
            ('sdc', 'Known', 'Known Stick', '1.00', 'Direct-Access', '16.2 GB/15.1 GiB', '31588352', '512', 'Yes',
             'off', '7:0:0:0'),
            ('sdd', 'Known', 'SD Slot', '1.00', 'Direct-Access', '', '', '', 'Yes', '', '7:0:0:1')])

    def test_built_in_disks_and_ports_with_no_connection_are_counted(self):
        lines = [('2026-09-29T09:00:00.1-04:00', f'scsi 0:0:0:0: {ident("Direct-Access", "ATA", "Disk", "1.0")} '
                                                 f'PQ: 0 ANSI: 5'),
                 ('2026-09-29T09:00:00.2-04:00', 'sd 0:0:0:0: [sda] 134217728 512-byte logical blocks: (68.7 GB/64.0 GiB)'),
                 ('2026-09-29T09:00:00.3-04:00', 'usb-storage 9-9:1.0: USB Mass Storage device detected'),
                 ('2026-09-29T09:00:00.4-04:00', 'scsi host9: usb-storage 9-9:1.0')]
        rows, counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(rows, [])
        self.assertEqual(counts[usb.STORAGE_ORPHAN], 4)

    def test_a_storage_device_whose_disk_lines_never_came(self):
        rows, counts = run_syslog([('var/log/syslog', syslog(*stick()[:7]))])
        self.assertEqual([(c.interface, d) for c, d in rows], [('3-1:1.0', None)])
        self.assertEqual(counts['USB storage devices with no SCSI device lines, reported without a disk'], 1)

    def test_a_usb_device_the_storage_driver_never_claimed_gives_no_row(self):
        rows, _counts = run_syslog([('var/log/syslog', syslog(*stick()[:5]))])
        self.assertEqual(rows, [])

    def test_syslog_and_kern_log_give_one_row_naming_both(self):
        data = syslog(*stick())
        rows, _counts = run_syslog([('var/log/kern.log', data), ('var/log/syslog', data)])
        self.assertEqual([c.sources for c, _d in rows], [['var/log/syslog', 'var/log/kern.log']])

    def test_an_identification_line_not_split_is_counted_per_row(self):
        lines = stick()
        lines[7] = ('2026-09-29T10:20:22.300000-04:00', 'scsi 6:0:0:0: Direct-Access     Kn Stick 1.0 PQ: 0 ANSI: 2')
        rows, counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(disk_fields(rows[0][1])[1:4], ('', 'Direct-Access     Kn Stick 1.0', ''))
        self.assertEqual(counts[usb.IDENT_UNSPLIT], 1)

    def test_debian_5_forms_with_the_kernel_time_kept(self):
        lines = [('Sep 29 10:20:22', '[  12.100000] usb 1-1: new high speed USB device using ehci_hcd and address 2'),
                 ('Sep 29 10:20:22', '[  12.200000] usb 1-1: New USB device found, idVendor=abcd, idProduct=1234'),
                 ('Sep 29 10:20:22', '[  12.300000] usb-storage 1-1:1.0: USB Mass Storage device detected'),
                 ('Sep 29 10:20:22', '[  12.400000] scsi host4: usb-storage 1-1:1.0'),
                 ('Sep 29 10:20:23', '[  13.100000] sd 4:0:0:0: [sdb] 31588352 512-byte hardware sectors (16173 MB)'),
                 ('Sep 29 10:20:23', '[  13.200000] sd 4:0:0:0: [sdb] Attached SCSI removable disk')]
        rows, _counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertEqual(disk_fields(rows[0][1]), ('sdb', '', '', '', '', '16173 MB', '31588352', '512', 'Yes', '',
                                                   '4:0:0:0'))
        self.assertEqual(rows[0][0].connected, '')

    def test_a_new_boot_forgets_the_hosts(self):
        lines = stick()[:7] + [('2026-09-29T11:00:00.0-04:00', 'Linux version 7.0.0-34-generic (buildd@host) #34'),
                               ('2026-09-29T11:00:01.0-04:00', 'sd 6:0:0:0: [sdb] Attached SCSI removable disk')]
        rows, counts = run_syslog([('var/log/syslog', syslog(*lines))])
        self.assertIsNone(rows[0][1])
        self.assertEqual(counts[usb.STORAGE_ORPHAN], 1)


def journal(entries):
    """A journal file of (realtime seconds, monotonic seconds, kernel MESSAGE) entries."""
    writer = jw.JournalWriter(boot_id=BOOT_1)
    for realtime, monotonic, message in entries:
        writer.add_entry([('_TRANSPORT', b'kernel'), ('MESSAGE', message.encode()), ('_HOSTNAME', b'vm')],
                         int(realtime * 1000000), int(monotonic * 1000000), boot_id=BOOT_1)
    return writer.bytes()


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):
    T0 = 1790690000.0

    def test_syslog_artifact(self):
        with tempfile.TemporaryDirectory() as root:
            log_dir = os.path.join(root, 'var', 'log')
            os.makedirs(log_dir)
            paths = []
            for name in ('syslog', 'kern.log'):
                paths.append(os.path.join(log_dir, name))
                with open(paths[-1], 'wb') as handle:
                    handle.write(syslog(('2026-09-29T09:00:00.1-04:00', 'usb usb3: Product: EHCI Host Controller'),
                                        *stick(), ('2026-09-29T09:00:00.2-04:00',
                                                   'sd 0:0:0:0: [sda] Attached SCSI disk')))
            paths.append(log_dir)
            with mock.patch.object(usb, 'logfunc') as log:
                headers, rows, source = usb.linuxUsbStorageSyslog.__wrapped__(FakeContext(paths, root))
        self.assertEqual(headers, (
            ('Connected (UTC)', 'datetime'), ('Disconnected (UTC)', 'datetime'), 'Connected as Recorded',
            'Disconnected as Recorded', 'Disk', 'SCSI Vendor', 'SCSI Model', 'SCSI Revision', 'Device Type', 'Capacity',
            'Blocks', 'Block Size', 'Removable', 'Write Protect', 'SCSI Address', 'Vendor ID', 'Product ID',
            'Manufacturer', 'Product', 'Serial Number', 'Port', 'Interface', 'Hostname', 'Source File'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][:5], (datetime(2026, 9, 29, 14, 20, 22, 100000, UTC), '',
                                       '2026-09-29T10:20:22.100000-04:00', '', 'sdb'))
        self.assertEqual(rows[0][15:], ('abcd', '1234', 'Known Maker', 'Known Stick', 'KNOWN0001', '3-1', '3-1:1.0',
                                        'vm', 'var/log/syslog\nvar/log/kern.log'))
        self.assertEqual(source, 'var/log/syslog\nvar/log/kern.log')
        log.assert_called_once_with('USB Storage Devices (syslog): 1 ' + usb.STORAGE_ORPHAN)

    def test_journal_artifact(self):
        t = self.T0
        entries = [(t + i * 0.01, 10 + i * 0.01, message) for i, (_stamp, message) in enumerate(stick())]
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, 'var', 'log', 'journal', 'm', 'system.journal')
            os.makedirs(os.path.dirname(path))
            with open(path, 'wb') as handle:
                handle.write(journal(entries))
            with mock.patch.object(usb, 'logfunc') as log:
                headers, rows, source = usb.linuxUsbStorageJournal.__wrapped__(
                    FakeContext([path, os.path.dirname(path)], root))
        self.assertEqual(len(headers), 23)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][:7], (datetime.fromtimestamp(t, UTC), '', 'sdb', 'Known', 'Known Stick', '1.00',
                                       'Direct-Access'))
        self.assertEqual(rows[0][-3:], ('vm', BOOT_1.hex(), 'var/log/journal/m/system.journal'))
        self.assertEqual(source, 'var/log/journal/m/system.journal')
        log.assert_not_called()

    def test_the_usb_devices_artifacts_still_read_only_usb_lines(self):
        counts = Counter()
        connections = usb.syslog_connections([('var/log/syslog', syslog(*stick()))], counts)
        self.assertEqual([(c.interface, c.disks) for c in connections], [('', [])])
        self.assertEqual(counts, Counter())


if __name__ == '__main__':
    unittest.main()
