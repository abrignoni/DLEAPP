"""Pin scripts/artifacts/bitcoinCore.py on a debug.log and wallets built here (made-up values).

Line shapes follow Bitcoin Core v32.1 as logged on windows11_arm_bitcoincore_known_20261108.
"""
import pathlib
import sqlite3
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
             'to mempool and for broadcast to peers', 'regtest', 'lab')])

    def test_sessions(self):
        _, rows, _ = btc.bitcoinCoreSessions.__wrapped__(self.context)
        self.assertEqual(rows, [
            (t(2026, 1, 1, 0, 0, 1), t(2026, 1, 1, 0, 0, 1), '', '', '', 'No', 0, '', 1, 'regtest', 'lab'),
            (t(2026, 1, 1, 0, 0, 2), t(2026, 1, 1, 0, 0, 7), 'v32.1.0',
             'C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\regtest',
             'C:\\\\Users\\\\lab\\\\AppData\\\\Local\\\\Bitcoin\\\\bitcoin.conf (not found, skipping)', 'Yes', 1, '127.0.0.1',
             10, 'regtest', 'lab'),
            (t(2026, 1, 1, 0, 1, 0), t(2026, 1, 1, 0, 1, 1), 'v32.1.0', '', '', 'No', 1, '::1', 2, 'regtest', 'lab')])

    def test_address_book_and_legacy_wallet(self):
        with mock.patch.object(btc, 'logfunc') as log:
            _, rows, _ = btc.bitcoinCoreAddressBook.__wrapped__(self.context)
        self.assertEqual(rows, [('bcrt1qaaa', 'my label', 'receive', 'w1', 'regtest', 'lab'),
                                ('bcrt1qbbb', '', 'send', 'w1', 'regtest', 'lab')])
        self.assertNotIn('SECRET', repr(rows))
        self.assertIn('legacy Berkeley DB wallet is not read', log.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
