"""Pin scripts/artifacts/bitcoinCore.py on a debug.log and wallets built here (made-up values).

Line shapes follow Bitcoin Core v32.1 as logged on windows11_arm_bitcoincore_known_20261108.
"""
import pathlib
import sqlite3
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import bitcoinCore as btc  # pylint: disable=wrong-import-position

TX1 = 'ab' * 32
TX2 = 'cd' * 32
LOG = f"""2026-01-01T00:00:01Z orphan line before any start
2026-01-01T00:00:02Z Bitcoin Core version v32.1.0 (release build)
2026-01-01T00:00:02Z Using data directory C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\regtest
2026-01-01T00:00:02Z Config file: C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\bitcoin.conf (not found, skipping)
2026-01-01T00:00:03Z [warning] ThreadRPCServer incorrect password attempt from 127.0.0.1:5000
2026-01-01T00:00:03Z [net] some debug line
2026-01-01T00:00:04Z [w1] AddToWallet {TX1} new Confirmed (block={TX2}, height=1, index=0)
2026-01-01T00:00:05Z [w1] CommitTransaction:
CTransaction(hash=abababab, ver=2, vin.size=1, vout.size=1, nLockTime=1)
    CTxOut(nValue=1.00000000, scriptPubKey=0014aa)

2026-01-01T00:00:05.123456Z [w1] Submitting wtx {TX1} to mempool and for broadcast to peers
2026-01-01T00:00:06Z [w1] Fee Calculation: not an event
2026-01-01T00:00:06Z [msghand] [w1] Submitting wtx {TX2} to mempool without broadcast
2026-01-01T00:00:07Z Shutdown done
2026-01-01T00:01:00Z Bitcoin Core version v32.1.0 (release build)
2026-01-01T00:01:01Z [warning] ThreadRPCServer incorrect password attempt from [::1]:5001
"""


def _cs(data):
    return bytes([len(data)]) + data


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def t(*args):
    return datetime(*args, tzinfo=timezone.utc)


class BitcoinCoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        root = pathlib.Path(self.tmp.name, 'Users', 'lab', 'AppData', 'Local', 'Bitcoin', 'regtest')
        (root / 'wallets' / 'w1').mkdir(parents=True)
        (root / 'debug.log').write_text(LOG, encoding='utf-8')
        db = sqlite3.connect(root / 'wallets' / 'w1' / 'wallet.dat')
        db.execute('CREATE TABLE main(key BLOB PRIMARY KEY NOT NULL, value BLOB NOT NULL)')
        rows = [(_cs(b'name') + _cs(b'bcrt1qaaa'), _cs(b'my label')), (_cs(b'purpose') + _cs(b'bcrt1qaaa'), _cs(b'receive')),
                (_cs(b'purpose') + _cs(b'bcrt1qbbb'), _cs(b'send')),
                (_cs(b'walletdescriptorkey') + b'\x01\x02', b'SECRET-KEY-BYTES')]
        db.executemany('INSERT INTO main VALUES (?, ?)', rows)
        db.commit()
        db.close()
        legacy = pathlib.Path(self.tmp.name, 'Users', 'lab', 'AppData', 'Roaming', 'Bitcoin', 'wallet.dat')
        legacy.parent.mkdir(parents=True)
        legacy.write_bytes(b'\x00' * 12 + b'\x62\x31\x05\x00' + b'\x00' * 16)
        self.files = [str(root / 'debug.log'), str(root / 'wallets' / 'w1' / 'wallet.dat'), str(legacy)]
        self.context = FakeContext(self.tmp.name, self.files)

    def tearDown(self):
        self.tmp.cleanup()

    def test_wallet_log(self):
        headers, rows, _ = btc.bitcoinCoreWalletLog.__wrapped__(self.context)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (t(2026, 1, 1, 0, 0, 4), 'w1', 'AddToWallet', TX1, f'new Confirmed (block={TX2}, height=1, index=0)',
             'regtest', 'lab'),
            (t(2026, 1, 1, 0, 0, 5), 'w1', 'CommitTransaction', '',
             'CTransaction(hash=abababab, ver=2, vin.size=1, vout.size=1, nLockTime=1)\n'
             'CTxOut(nValue=1.00000000, scriptPubKey=0014aa)', 'regtest', 'lab'),
            (datetime(2026, 1, 1, 0, 0, 5, 123456, tzinfo=timezone.utc), 'w1', 'Submitting wtx', TX1,
             'to mempool and for broadcast to peers', 'regtest', 'lab'),
            # A thread name before the wallet's name (-logthreadnames) is passed over.
            (t(2026, 1, 1, 0, 0, 6), 'w1', 'Submitting wtx', TX2, 'to mempool without broadcast', 'regtest', 'lab')])

    def test_sessions(self):
        _, rows, _ = btc.bitcoinCoreSessions.__wrapped__(self.context)
        self.assertEqual(rows, [
            (t(2026, 1, 1, 0, 0, 1), t(2026, 1, 1, 0, 0, 1), '', '', '', 'No', 0, '', 1, 'regtest', 'lab'),
            (t(2026, 1, 1, 0, 0, 2), t(2026, 1, 1, 0, 0, 7), 'v32.1.0',
             'C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\regtest',
             'C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\bitcoin.conf (not found, skipping)', 'Yes', 1, '127.0.0.1',
             11, 'regtest', 'lab'),
            (t(2026, 1, 1, 0, 1, 0), t(2026, 1, 1, 0, 1, 1), 'v32.1.0', '', '', 'No', 1, '::1', 2, 'regtest', 'lab')])

    def test_address_book_and_legacy_wallet(self):
        with mock.patch.object(btc, 'logfunc') as log:
            _, rows, _ = btc.bitcoinCoreAddressBook.__wrapped__(self.context)
        self.assertEqual(rows, [('bcrt1qaaa', 'my label', 'receive', 'w1', 'SQLite', 'regtest', 'lab'),
                                ('bcrt1qbbb', '', 'send', 'w1', 'SQLite', 'regtest', 'lab')])
        self.assertNotIn('SECRET', repr(rows))
        self.assertIn('is not a SQLite or readable Berkeley DB wallet', log.call_args.args[0])


PAGE = 512


def _page(number, kind, entries=0, free=0, following=0, level=1, lsn=(0, 1)):
    page = bytearray(PAGE)
    struct.pack_into('<IIIIIHHBB', page, 0, lsn[0], lsn[1], number, 0, following, entries, free, level, kind)
    return page


def _meta(number, root):
    page = bytearray(PAGE)
    struct.pack_into('<IIIIII', page, 0, 0, 1, number, 0x00053162, 9, PAGE)
    page[25] = 9
    struct.pack_into('<I', page, 48, 0x20)
    struct.pack_into('<I', page, 88, root)
    return page


def _items(page, items):
    """Place raw items from the end of the page, with their index after the header."""
    end = PAGE
    for entry, item in enumerate(items):
        end -= len(item)
        page[end:end + len(item)] = item
        struct.pack_into('<H', page, 26 + 2 * entry, end)
    return page


def _data(value, deleted=False):
    return struct.pack('<HB', len(value), 0x81 if deleted else 1) + value


def _bdb_wallet(lsn=(0, 1)):
    """A wallet file: outer root, main subdatabase, one internal page, two leaves and an overflow label."""
    long_label = b'L' * 300
    overflow = _page(6, 7, entries=1, free=len(_cs_long(long_label)), level=0)
    overflow[26:26 + len(_cs_long(long_label))] = _cs_long(long_label)
    pages = [
        _meta(0, 1),
        _items(_page(1, 5, entries=2), [_data(b'main'), _data(struct.pack('>I', 2))]),
        _meta(2, 3),
        _items(_page(3, 3, entries=2), [struct.pack('<HBBII', 0, 1, 0, 4, 2), struct.pack('<HBBII', 0, 1, 0, 5, 1)]),
        _items(_page(4, 5, entries=6, lsn=lsn), [
            _data(_cs(b'name') + _cs(b'addr1')), _data(_cs(b'first')),
            _data(_cs(b'purpose') + _cs(b'addr1')), _data(_cs(b'receive')),
            _data(_cs(b'name') + _cs(b'gone'), deleted=True), _data(_cs(b'old'), deleted=True)]),
        _items(_page(5, 5, entries=4), [
            _data(_cs(b'name') + _cs(b'addr2')), struct.pack('<HBBII', 0, 3, 0, 6, len(_cs_long(long_label))),
            _data(_cs(b'key') + b'\x01'), _data(b'SECRET-KEY-BYTES')]),
        overflow,
    ]
    return b''.join(bytes(page) for page in pages)


def _cs_long(data):
    return b'\xfd' + struct.pack('<H', len(data)) + data


class BerkeleyDbWalletTest(unittest.TestCase):
    def test_records_across_pages_with_overflow(self):
        records, flushed = btc.bdb_wallet_records(_bdb_wallet())
        self.assertTrue(flushed)
        self.assertEqual(btc.book_from_records(records),
                         {'addr1': ['first', 'receive'], 'addr2': ['L' * 300, '']})

    def test_a_page_with_a_live_log_sequence_number_is_not_flushed(self):
        records, flushed = btc.bdb_wallet_records(_bdb_wallet(lsn=(1, 28)))
        self.assertFalse(flushed)
        self.assertIn('addr1', btc.book_from_records(records))

    def test_truncated_file_raises(self):
        with self.assertRaises(ValueError):
            btc.bdb_wallet_records(_bdb_wallet()[:PAGE * 5])

    def test_loop_in_the_tree_raises(self):
        data = bytearray(_bdb_wallet())
        offset = struct.unpack_from('<H', data, 3 * PAGE + 26)[0]
        struct.pack_into('<I', data, 3 * PAGE + offset + 4, 3)
        with self.assertRaises(ValueError):
            btc.bdb_wallet_records(bytes(data))

    def test_berkeley_db_encryption_is_refused(self):
        data = bytearray(_bdb_wallet())
        data[24] = 1
        with self.assertRaises(ValueError):
            btc.bdb_wallet_records(bytes(data))


if __name__ == '__main__':
    unittest.main()
