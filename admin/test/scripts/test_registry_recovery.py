"""Transaction log replay, on hives and logs built here the way the format specification lays them out."""

import os
import struct
import tempfile
import unittest
from unittest import mock

from scripts import registry_recovery as rr
from scripts import windows_registry


def base_block(primary, secondary, file_type, hive_bins_size, size=4096, flags=0):
    block = bytearray(size)
    block[0:4] = b'regf'
    struct.pack_into('<II', block, 4, primary, secondary)
    struct.pack_into('<IIII', block, 20, 1, 5, file_type, 1)
    struct.pack_into('<I', block, 40, hive_bins_size)
    struct.pack_into('<I', block, 144, flags)
    struct.pack_into('<I', block, 508, rr.xor32(block))
    return bytes(block)


def hive(primary, secondary, pages=2):
    bins = bytearray(4096 * pages)
    for index in range(pages):
        bins[4096 * index:4096 * index + 4] = b'hbin'
        struct.pack_into('<II', bins, 4096 * index + 4, 4096 * index, 4096)
    return base_block(primary, secondary, 0, len(bins)) + bytes(bins)


def entry(sequence, pages, hive_bins_size=8192, flags=0, spoil=False):
    references = b''.join(struct.pack('<II', offset, len(data)) for offset, data in pages)
    body = references + b''.join(data for _offset, data in pages)
    size = -(-(40 + len(body)) // 512) * 512
    body += b'\x00' * (size - 40 - len(body))
    head = bytearray(b'HvLE' + struct.pack('<IIIII', size, flags, sequence, hive_bins_size, len(pages)))
    head += struct.pack('<Q', rr.marvin32(body))
    head += struct.pack('<Q', rr.marvin32(bytes(head)))
    data = bytes(head) + body
    if spoil:
        data = data[:-1] + bytes([data[-1] ^ 0xFF])
    return data


def log(sequence, entries, file_type=6):
    return base_block(sequence, sequence, file_type, 8192, size=512) + b''.join(entries)


def page(fill):
    return bytes([fill]) * 4096


def key_page(bin_offset, stamp, name=b'Run', parent=0x1020):
    """A one-page hive bin holding one key node and a free cell after it."""
    data = bytearray(4096)
    data[0:4] = b'hbin'
    struct.pack_into('<II', data, 4, bin_offset, 4096)
    size = -(-(4 + 76 + len(name)) // 8) * 8
    struct.pack_into('<i', data, 32, -size)
    data[36:38] = b'nk'
    struct.pack_into('<Q', data, 40, stamp)
    struct.pack_into('<I', data, 52, parent)
    struct.pack_into('<H', data, 108, len(name))
    data[112:112 + len(name)] = name
    struct.pack_into('<i', data, 32 + size, 4096 - 32 - size)
    return bytes(data)


def key_hive(primary, secondary, stamp, name=b'Run'):
    return base_block(primary, secondary, 0, 8192) + key_page(0, stamp, name) + key_page(4096, 1)


class Marvin32Test(unittest.TestCase):
    def test_symcrypt_known_answer(self):
        # SymCrypt's self-test: its default seed, the message 'abc', and the eight result bytes.
        value = rr.marvin32(b'abc', (0xd53cd9ce << 32) | 0xcd0893b7)
        self.assertEqual(struct.pack('<Q', value), bytes.fromhex('bf6927493943c722'))


class ChecksumTest(unittest.TestCase):
    def test_zero_and_all_ones_are_remapped(self):
        self.assertEqual(rr.xor32(bytes(512)), 1)
        self.assertEqual(rr.xor32(b'\xff\xff\xff\xff' + bytes(508)), 0xFFFFFFFE)
        self.assertEqual(rr.xor32(struct.pack('<II', 0x12345678, 0x0F0F0F0F) + bytes(504)), 0x12345678 ^ 0x0F0F0F0F)


class RecoverTest(unittest.TestCase):
    def test_a_clean_hive_is_returned_as_it_is(self):
        primary = hive(7, 7)
        data, summary = rr.recover(primary, [('X.LOG1', log(7, [entry(7, [(0, page(1))])]))])
        self.assertEqual((data, summary['state']), (primary, 'clean'))

    def test_entries_of_both_logs_are_applied_in_sequence_and_the_base_block_updated(self):
        primary = hive(10, 9)
        log2 = log(12, [entry(12, [(4096, page(0xBB))], hive_bins_size=12288, flags=1)])
        log1 = log(10, [entry(10, [(0, page(0xAA))]), entry(11, [(4096, page(0xCC))])])
        data, summary = rr.recover(primary, [('H.LOG2', log2), ('H.LOG1', log1)])
        self.assertEqual(summary['state'], 'recovered')
        self.assertEqual(summary['applied'], [('H.LOG1', 10, 11), ('H.LOG2', 12, 12)])
        self.assertEqual((summary['entries'], summary['pages']), (3, 3))
        self.assertEqual(data[4096:8192], page(0xAA))
        self.assertEqual(data[8192:12288], page(0xBB))
        self.assertEqual(len(data), 4096 + 12288)
        self.assertEqual(struct.unpack_from('<II', data, 4), (12, 12))
        self.assertEqual(struct.unpack_from('<I', data, 40)[0], 12288)
        self.assertEqual(struct.unpack_from('<I', data, 144)[0] & 1, 1)
        self.assertEqual(struct.unpack_from('<I', data, 508)[0], rr.xor32(data))

    def test_a_log_whose_entries_come_first_is_applied_first_whatever_its_name(self):
        primary = hive(20, 19)
        data, summary = rr.recover(primary, [('H.LOG1', log(21, [entry(21, [(0, page(2))])])),
                                             ('H.LOG2', log(20, [entry(20, [(0, page(1))])]))])
        self.assertEqual(summary['applied'], [('H.LOG2', 20, 20), ('H.LOG1', 21, 21)])
        self.assertEqual(data[4096:8192], page(2))

    def test_an_entry_failing_its_hash_stops_the_replay(self):
        primary = hive(5, 4)
        data, summary = rr.recover(primary, [('H.LOG1', log(5, [entry(5, [(0, page(1))]),
                                                                  entry(6, [(0, page(2))], spoil=True),
                                                                  entry(7, [(0, page(3))])]))])
        self.assertEqual(summary['applied'], [('H.LOG1', 5, 5)])
        self.assertEqual(data[4096:8192], page(1))

    def test_an_older_entry_left_after_the_chain_in_the_same_log_is_not_applied(self):
        primary = hive(5, 4)
        data, summary = rr.recover(primary, [('H.LOG1', log(5, [entry(5, [(0, page(1))]),
                                                                  entry(3, [(0, page(2))])]))])
        self.assertEqual(summary['applied'], [('H.LOG1', 5, 5)])
        self.assertEqual(data[4096:8192], page(1))

    def test_an_entry_whose_hive_bins_size_is_not_whole_pages_stops_the_replay(self):
        primary = hive(5, 4)
        data, summary = rr.recover(primary, [('H.LOG1', log(5, [entry(5, [(0, page(1))]),
                                                                  entry(6, [(0, page(2))], hive_bins_size=5000)]))])
        self.assertEqual(summary['applied'], [('H.LOG1', 5, 5)])
        self.assertEqual(data[4096:8192], page(1))

    def test_a_log_whose_base_block_is_mid_update_or_torn_is_not_applied(self):
        primary = hive(60, 59)
        mid_update = bytearray(log(60, [entry(60, [(0, page(1))])]))
        struct.pack_into('<I', mid_update, 8, 59)
        struct.pack_into('<I', mid_update, 508, rr.xor32(mid_update))
        torn = bytearray(log(60, [entry(60, [(0, page(2))])]))
        torn[100] ^= 0xFF
        data, summary = rr.recover(primary, [('H.LOG1', bytes(mid_update)), ('H.LOG2', bytes(torn))])
        self.assertEqual((data, summary['state']), (primary, 'dirty, not recovered'))
        self.assertEqual(summary['reasons'], {'H.LOG1': 'base block not valid', 'H.LOG2': 'base block not valid'})

    def test_a_log_behind_the_hive_or_not_starting_at_its_own_sequence_is_not_applied(self):
        primary = hive(30, 29)
        behind = log(20, [entry(20, [(0, page(1))])])
        misaligned = log(31, [entry(35, [(0, page(2))])])
        data, summary = rr.recover(primary, [('H.LOG1', behind), ('H.LOG2', misaligned)])
        self.assertEqual((data, summary['state']), (primary, 'dirty, not recovered'))
        self.assertEqual(summary['reasons'], {'H.LOG1': 'no subsequent log entries',
                                              'H.LOG2': 'no subsequent log entries'})

    def test_a_second_log_that_does_not_continue_the_sequence_is_left_out(self):
        primary = hive(40, 39)
        data, summary = rr.recover(primary, [('H.LOG1', log(40, [entry(40, [(0, page(1))])])),
                                             ('H.LOG2', log(45, [entry(45, [(0, page(2))])]))])
        self.assertEqual(summary['applied'], [('H.LOG1', 40, 40)])
        self.assertEqual(summary['reasons'], {'H.LOG2': 'does not continue the sequence of the log applied before it'})
        self.assertEqual(data[4096:8192], page(1))

    def test_old_format_logs_and_a_hive_with_a_bad_checksum_are_not_replayed(self):
        primary = hive(50, 49)
        _data, summary = rr.recover(primary, [('H.LOG1', log(50, [], file_type=1))])
        self.assertEqual(summary['state'], 'dirty, not recovered')
        self.assertEqual(summary['reasons'], {'H.LOG1': 'file type 1, not the format this replay reads'})
        broken = bytearray(hive(50, 50))
        broken[508] ^= 0xFF
        data, summary = rr.recover(bytes(broken), [('H.LOG1', log(50, [entry(50, [(0, page(1))])]))])
        self.assertEqual((data, summary['state']), (bytes(broken), 'dirty, not recovered'))
        self.assertEqual(summary['reasons'], {'hive': 'base block checksum wrong'})

    def test_logs_that_would_set_a_key_back_are_not_applied(self):
        primary = key_hive(9, 8, stamp=2_000)
        stale = log(9, [entry(9, [(0, key_page(0, 1_000))])])
        data, summary = rr.recover(primary, [('SYSTEM.LOG1', stale)])
        self.assertEqual((data, summary['state']), (primary, 'dirty, not recovered'))
        self.assertEqual(summary['applied'], [])
        self.assertEqual(summary['reasons'], {'hive': 'replaying SYSTEM.LOG1, sequence 9 to 9, would give 1 key '
                                                      'an earlier last-written time than the hive holds'})

    def test_logs_that_move_a_key_forward_or_rewrite_its_cell_for_another_key_are_applied(self):
        primary = key_hive(9, 8, stamp=2_000)
        for replacement in (key_page(0, 3_000), key_page(0, 1_000, name=b'RunOnce'), key_page(0, 2_000)):
            data, summary = rr.recover(primary, [('SYSTEM.LOG1', log(9, [entry(9, [(0, replacement)])]))])
            self.assertEqual(summary['state'], 'recovered')
            self.assertEqual(data[4096:8192], replacement)

    def test_a_key_set_back_by_the_second_log_stops_the_whole_replay(self):
        primary = key_hive(9, 8, stamp=2_000)
        log1 = log(9, [entry(9, [(0, key_page(0, 3_000))])])
        log2 = log(10, [entry(10, [(0, key_page(0, 1_500))])])
        data, summary = rr.recover(primary, [('SYSTEM.LOG1', log1), ('SYSTEM.LOG2', log2)])
        self.assertEqual((data, summary['state']), (primary, 'dirty, not recovered'))
        self.assertIn('sequence 9 to 10, would give 1 key', summary['reasons']['hive'])

    def test_a_file_that_is_not_a_primary_hive_is_left_alone(self):
        data, summary = rr.recover(b'not a hive', [])
        self.assertEqual((data, summary['state']), (b'not a hive', 'not a hive'))
        as_log = log(3, [])
        self.assertEqual(rr.recover(as_log, [])[1]['state'], 'not a hive')


class OpenHiveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = self._tmp.name
        self.logs = []

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, data):
        path = os.path.join(self.folder, name)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def _open(self, path, context=None):
        """The bytes open_hive hands python-registry."""
        read = []
        with mock.patch.object(windows_registry, 'logfunc', self.logs.append), \
                mock.patch.object(windows_registry.Context, '_data_folder', self.folder), \
                mock.patch.object(windows_registry.Registry, 'Registry', side_effect=lambda f: read.append(f.read())):
            windows_registry.open_hive(path, context)
        return read[0]

    def test_logs_beside_the_hive_are_found_without_case_and_replayed(self):
        path = self._write('NTUSER.DAT', hive(8, 7))
        self._write('ntuser.dat.LOG1', log(8, [entry(8, [(0, page(9))])]))
        self._write('ntuser.dat.LOG2', log(9, [entry(9, [(4096, page(4))])]))
        self._write('NTUSER.DAT.bak.LOG1', log(10, [entry(10, [(0, page(5))])]))

        class Context:
            @staticmethod
            def get_relative_path(_path):
                return 'Users/alice/NTUSER.DAT'
        data = self._open(path, Context())
        self.assertEqual(data[4096:8192], page(9))
        self.assertEqual(data[8192:12288], page(4))
        self.assertEqual(self.logs, ['Registry: Users/alice/NTUSER.DAT was dirty; replayed 2 transaction log '
                                     'entries, sequence 8 to 9, from ntuser.dat.LOG1 and ntuser.dat.LOG2.'])

    def test_a_dirty_hive_without_logs_is_read_as_it_is_and_logged(self):
        # No context is passed, so the hive is named by its path inside the staged data.
        primary = hive(8, 7)
        os.makedirs(os.path.join(self.folder, 'Windows'))
        path = self._write(os.path.join('Windows', 'SYSTEM'), primary)
        self.assertEqual(self._open(path), primary)
        self.assertEqual(self.logs, ['Registry: Windows/SYSTEM is dirty and was read as it is '
                                     '(no transaction log beside it).'])

    def test_a_single_replayed_entry_is_named_in_the_singular(self):
        path = self._write('SAM', hive(3, 2))
        self._write('SAM.LOG1', log(3, [entry(3, [(0, page(7))])]))
        self._open(path)
        self.assertEqual(self.logs, ['Registry: SAM was dirty; replayed 1 transaction log entry, '
                                     'sequence 3 to 3, from SAM.LOG1.'])

    def test_a_clean_hive_is_read_as_it_is_without_a_log_line(self):
        primary = hive(8, 8)
        path = self._write('SOFTWARE', primary)
        self.assertEqual(self._open(path), primary)
        self.assertEqual(self.logs, [])

    def test_a_transaction_log_is_known_by_its_name(self):
        for name, expected in (('SYSTEM.LOG1', True), ('ntuser.dat.log2', True), ('SAM.LOG', True),
                               ('SYSTEM', False), ('NTUSER.DAT', False), ('catalog', False)):
            self.assertEqual(windows_registry.is_transaction_log('/x/' + name), expected, name)


if __name__ == '__main__':
    unittest.main()
