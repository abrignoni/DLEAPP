"""Pin scripts/artifacts/electrum.py on wallet files built here (made-up values).

Field names follow Electrum 4.8.4's wallet file as written on windows11_arm_electrum_known_20261108.
"""
import base64
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import electrum  # pylint: disable=wrong-import-position

TXID = 'ab' * 32
PLAIN = {
    'seed_version': 74, 'wallet_type': 'standard', 'use_encryption': False,
    'db_metadata': {'creation_timestamp': 1700000000, 'first_electrum_version_used': '4.8.4'},
    'keystore': {'type': 'bip32', 'seed_type': 'segwit', 'seed': 'NEVER SHOWN SEED', 'xprv': 'NEVER SHOWN XPRV'},
    'addresses': {'receiving': ['a1', 'a2'], 'change': ['c1']},
    'transactions': {TXID: '00'},
    'labels': {'bc1qtest': 'my address', TXID: 'my tx', TXID + ':1': 'my output'},
    'payment_requests': {'r1': {'amount_msat': 100000000, 'message': 'pay me', 'time': 1700000100, 'exp': 3600,
                                'height': 0, 'outputs': [[0, 'bc1qtest', 100000]], 'bip70': None}},
    'invoices': {'i1': {'amount_msat': '!', 'message': 'to pay', 'time': 1700000200, 'exp': 0,
                        'outputs': [[0, 'bc1qother', 0]], 'lightning_invoice': None}},
}


class FakeContext:
    def __init__(self, root, files):
        self.root = root
        self.files = files

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def t(value):
    return datetime.fromtimestamp(value, timezone.utc)


class ElectrumTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        wallets = pathlib.Path(self.tmp.name, 'Users', 'lab', 'AppData', 'Roaming', 'Electrum', 'wallets')
        wallets.mkdir(parents=True)
        (wallets / 'plain').write_text(json.dumps(PLAIN), encoding='utf-8')
        (wallets / 'locked').write_bytes(base64.b64encode(b'BIE1' + b'\x00' * 60))
        (wallets / 'notes.txt').write_text('not a wallet', encoding='utf-8')
        testnet = pathlib.Path(self.tmp.name, 'home', 'u', '.electrum', 'testnet', 'wallets')
        testnet.mkdir(parents=True)
        (testnet / 'tw').write_text(json.dumps({'seed_version': 74, 'labels': {}}), encoding='utf-8')
        self.files = [str(p) for p in wallets.iterdir()] + [str(testnet / 'tw')]
        self.context = FakeContext(self.tmp.name, self.files)

    def tearDown(self):
        self.tmp.cleanup()

    def test_wallets(self):
        with mock.patch.object(electrum, 'logfunc') as log:
            headers, rows, _ = electrum.electrumWallets.__wrapped__(self.context)
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        self.assertEqual(rows, [
            ('', 'locked', 'Yes (user password)', '', '', '', '', '', '', '', '', '', '', '', '', 'mainnet', 'lab'),
            (t(1700000000), 'plain', 'No', 'No', '4.8.4', 'standard', 'bip32', 'segwit', '74', 2, 1, 1, 3, 1, 1,
             'mainnet', 'lab'),
            ('', 'tw', 'No', '', '', '', '', '', '74', 0, 0, 0, 0, 0, 0, 'testnet', 'u')])
        self.assertNotIn('NEVER SHOWN', repr(rows))
        self.assertIn('notes.txt is not an Electrum wallet file', log.call_args.args[0])

    def test_labels(self):
        with mock.patch.object(electrum, 'logfunc'):
            _, rows, _ = electrum.electrumLabels.__wrapped__(self.context)
        self.assertEqual(rows, [('plain', 'Transaction or payment hash', TXID, 'my tx', 'mainnet', 'lab'),
                                ('plain', 'Output', TXID + ':1', 'my output', 'mainnet', 'lab'),
                                ('plain', 'Address or other', 'bc1qtest', 'my address', 'mainnet', 'lab')])

    def test_requests(self):
        with mock.patch.object(electrum, 'logfunc'):
            headers, rows, _ = electrum.electrumRequests.__wrapped__(self.context)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [
            (t(1700000100), t(1700003700), 'plain', 'Payment request', 100000, 'pay me', 'bc1qtest', 'No', 'r1',
             'mainnet', 'lab'),
            (t(1700000200), '', 'plain', 'Invoice', '!', 'to pay', 'bc1qother', 'No', 'i1', 'mainnet', 'lab')])


if __name__ == '__main__':
    unittest.main()
