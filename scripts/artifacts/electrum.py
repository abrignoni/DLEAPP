__artifacts_v2__ = {
    "electrumWallets": {
        "name": "Electrum Wallets",
        "description": "Electrum wallet files: when each was created and by which Electrum version, whether the "
                       "file is encrypted or its keys password-protected, wallet and seed type, and counts of "
                       "addresses, transactions, labels, payment requests and invoices.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Electrum",
        "notes": "One row per wallet file: a file in the wallets folder of Electrum's data directory, AppData\\Roaming\\Electrum on Windows and ~/.electrum on macOS and Linux (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/util.py#L718-L728), or of a network's folder inside it (testnet, testnet4, regtest, simnet, signet or mutinynet; https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/constants.py#L129-L133; Network is that folder, or mainnet). A wallet kept elsewhere, or a data directory set with ELECTRUMDIR, is not matched. A file is encrypted when it is base64 whose decoded bytes start with BIE1 (a user password) or BIE2 (a password derived from a hardware wallet), as Electrum's storage decides (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/storage.py#L181-L191); any other file is read as JSON, and one that is not a JSON object with a seed_version is named in the run log and not read. An encrypted file cannot be read without its password. For an encrypted file only Wallet, File Encrypted, Network and User are filled. Created and First Electrum Version are the wallet's db_metadata, written when the wallet is created (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/wallet_db.py#L89-L94 and #L1701). Keys Password-Protected is use_encryption, which Electrum reads as whether signing needs a password (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/wallet.py#L3302-L3309). Wallet Type, Seed Version, the keystore's type and seed type are as stored. The counts are the sizes of the wallet's addresses (receiving and change), transactions, labels, payment_requests and invoices. The seed, private keys and extended keys in the file are not shown. On the known data (windows11_arm_electrum_known_20261108: Electrum 4.8.4 on Windows 11, run --offline with no network) kd_plain's Created fell within 4 seconds before the step that logged its creation, it showed the label and payment request the rig added, and kd_locked, made with a password and file encryption, showed as encrypted with a user password. Network and User were uniform on the known data; Transactions and Invoices were 0, as the wallets were never funded or used to pay. A row records a wallet file, not who used it.",
        "paths": ('*/Electrum/wallets/*', '*/Electrum/*/wallets/*', '*/.electrum/wallets/*', '*/.electrum/*/wallets/*'),
        "output_types": "standard",
        "artifact_icon": "credit-card",
        "sample_data": {
            "windows11_arm_electrum_known_20261108": "Windows 11 build 26200 (ARM64), Electrum 4.8.4 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "electrumLabels": {
        "name": "Electrum Labels",
        "description": "Labels an Electrum wallet keeps for its addresses and transactions.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Electrum",
        "notes": "One row per label in a wallet file: a file in the wallets folder of Electrum's data directory, AppData\\Roaming\\Electrum on Windows and ~/.electrum on macOS and Linux (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/util.py#L718-L728), or of a network's folder inside it (testnet, testnet4, regtest, simnet, signet or mutinynet; https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/constants.py#L129-L133; Network is that folder, or mainnet). A wallet kept elsewhere, or a data directory set with ELECTRUMDIR, is not matched. A file is encrypted when it is base64 whose decoded bytes start with BIE1 (a user password) or BIE2 (a password derived from a hardware wallet), as Electrum's storage decides (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/storage.py#L181-L191); any other file is read as JSON, and one that is not a JSON object with a seed_version is named in the run log and not read. An encrypted file cannot be read without its password. The labels are a map from a key to the text the user or a plugin set; the key is an address, a transaction ID, an output (transaction ID and index) or a Lightning payment hash (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/wallet.py#L1744-L1820). Labelled Item Type is read from the key's shape: Output for an ID and index, Transaction or payment hash for 64 hexadecimal digits (the two look alike), and Address or other for anything else. On the known data (windows11_arm_electrum_known_20261108: Electrum 4.8.4 on Windows 11, run --offline with no network) the one row was the label the rig set on kd_plain's first address. Wallet, Labelled Item Type, Network and User were uniform on the known data. A label records text kept in the wallet, not who wrote it.",
        "paths": ('*/Electrum/wallets/*', '*/Electrum/*/wallets/*', '*/.electrum/wallets/*', '*/.electrum/*/wallets/*'),
        "output_types": "standard",
        "artifact_icon": "tag",
        "sample_data": {
            "windows11_arm_electrum_known_20261108": "Windows 11 build 26200 (ARM64), Electrum 4.8.4 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "electrumRequests": {
        "name": "Electrum Payment Requests and Invoices",
        "description": "Payment requests (to receive) and invoices (to pay) kept in Electrum wallets: when each "
                       "was made, when it expires, the amount, the message and the address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Electrum",
        "notes": "One row per payment request (to receive) or invoice (to pay) in a wallet file: a file in the wallets folder of Electrum's data directory, AppData\\Roaming\\Electrum on Windows and ~/.electrum on macOS and Linux (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/util.py#L718-L728), or of a network's folder inside it (testnet, testnet4, regtest, simnet, signet or mutinynet; https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/constants.py#L129-L133; Network is that folder, or mainnet). A wallet kept elsewhere, or a data directory set with ELECTRUMDIR, is not matched. A file is encrypted when it is base64 whose decoded bytes start with BIE1 (a user password) or BIE2 (a password derived from a hardware wallet), as Electrum's storage decides (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/storage.py#L181-L191); any other file is read as JSON, and one that is not a JSON object with a seed_version is named in the run log and not read. An encrypted file cannot be read without its password. Created is the record's time and Expires that time plus its exp, blank when exp is 0, which means never (https://github.com/spesmilo/electrum/blob/54ff65dfe1b77ef6e00f00f296a557d86c454ca0/electrum/invoices.py#L95-L113 and #L157-L159). Amount (sat) is amount_msat divided by 1,000, shown as stored when it is not a number (! or blank). Message is as stored, Address is the first output's address, from the outputs Electrum stores as type, address and value, and Lightning Invoice says whether a Lightning invoice is stored. Request ID is the record's key. Whether a request was paid is not stored in the record and is not shown. On the known data (windows11_arm_electrum_known_20261108: Electrum 4.8.4 on Windows 11, run --offline with no network) the one row was the request the rig added to kd_plain: its Created on the second the rig logged the step, 100,000 sat (0.001 BTC), the rig's memo, the address the rig labelled, and Expires 3,600 seconds later. Every column but the two times was uniform on the known data, which held one request. A row records a request or invoice kept in the wallet, not that it was paid.",
        "paths": ('*/Electrum/wallets/*', '*/Electrum/*/wallets/*', '*/.electrum/wallets/*', '*/.electrum/*/wallets/*'),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "windows11_arm_electrum_known_20261108": "Windows 11 build 26200 (ARM64), Electrum 4.8.4 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
}

import base64
import binascii
import json
import os
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path

_ROOTS = ('Electrum', '.electrum')
# Folders other networks keep their data in, named after the network (electrum/constants.py).
_NETWORKS = ('testnet', 'testnet4', 'regtest', 'simnet', 'signet', 'mutinynet')
_HASH = re.compile(r'^[0-9a-f]{64}$')
_OUTPOINT = re.compile(r'^[0-9a-f]{64}:\d+$')
_MAGICS = {b'BIE1': 'Yes (user password)', b'BIE2': 'Yes (hardware wallet)'}


def _home_user(parts):
    if 'home' in parts and parts.index('home') + 1 < len(parts):
        return parts[parts.index('home') + 1]
    return ''


def _time(value):
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return ''
    return ''


def read_wallet(raw):
    """(encrypted, wallet dict or None) for one wallet file, as Electrum's storage decides it.

    A file that is base64 whose decoded bytes start with BIE1 or BIE2 is encrypted
    (electrum/storage.py, _init_encryption_version); anything else is read as JSON.
    """
    try:
        magic = base64.b64decode(raw, validate=True)[0:4]
    except (binascii.Error, ValueError):
        magic = b''
    if magic in _MAGICS:
        return _MAGICS[magic], None
    try:
        data = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        return 'No', None
    return 'No', data if isinstance(data, dict) else None


def _wallets(context, label):
    """(path, parts, wallet name, network, user, encrypted, data) for each wallet file found."""
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path):
            continue
        relative_path = context.get_relative_path(path)
        parts = PurePosixPath(str(relative_path).replace('\\', '/')).parts
        if len(parts) < 3 or parts[-2] != 'wallets':
            continue
        if parts[-3] in _ROOTS:
            network = 'mainnet'
        elif len(parts) >= 4 and parts[-3] in _NETWORKS and parts[-4] in _ROOTS:
            network = parts[-3]
        else:
            continue
        with open(path, 'rb') as handle:
            raw = handle.read()
        encrypted, data = read_wallet(raw)
        if encrypted == 'No' and (data is None or 'seed_version' not in data):
            logfunc(f'{label}: {"/".join(parts)} is not an Electrum wallet file, not read')
            continue
        yield path, parts[-1], network, user_from_path(relative_path) or _home_user(parts), encrypted, data


def _count(data, key):
    value = data.get(key)
    return len(value) if isinstance(value, (dict, list)) else 0


@artifact_processor
def electrumWallets(context):
    data_headers = (('Created', 'datetime'), 'Wallet', 'File Encrypted', 'Keys Password-Protected',
                    'First Electrum Version', 'Wallet Type', 'Keystore Type', 'Seed Type', 'Seed Version',
                    ('Receiving Addresses', 'number'), ('Change Addresses', 'number'), ('Transactions', 'number'),
                    ('Labels', 'number'), ('Payment Requests', 'number'), ('Invoices', 'number'), 'Network', 'User')
    data_list = []
    sources = []
    for path, name, network, user, encrypted, data in _wallets(context, 'Electrum Wallets'):
        if data is None:
            # An encrypted file cannot be read without its password: only its name and state are shown.
            data_list.append(('', name, encrypted) + ('',) * (len(data_headers) - 5) + (network, user))
            sources.append(path)
            continue
        meta = data.get('db_metadata') if isinstance(data.get('db_metadata'), dict) else {}
        keystore = data.get('keystore') if isinstance(data.get('keystore'), dict) else {}
        addresses = data.get('addresses') if isinstance(data.get('addresses'), dict) else {}
        use_encryption = data.get('use_encryption')
        data_list.append((
            _time(meta.get('creation_timestamp')), name, encrypted,
            'Yes' if use_encryption is True else 'No' if use_encryption is False else '',
            str(meta.get('first_electrum_version_used') or ''), str(data.get('wallet_type') or ''),
            str(keystore.get('type') or ''), str(keystore.get('seed_type') or ''), str(data.get('seed_version') or ''),
            _count(addresses, 'receiving'), _count(addresses, 'change'), _count(data, 'transactions'),
            _count(data, 'labels'), _count(data, 'payment_requests'), _count(data, 'invoices'),
            network, user))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def electrumLabels(context):
    data_list = []
    sources = []
    for path, name, network, user, _encrypted, data in _wallets(context, 'Electrum Labels'):
        labels = data.get('labels') if data else None
        if not isinstance(labels, dict) or not labels:
            continue
        for item in sorted(labels):
            # Keys are addresses, transaction IDs, outputs (txid:index) or Lightning payment hashes
            # (electrum/wallet.py, the get_label_for_* methods); an ID and a payment hash look alike.
            key = str(item)
            kind = ('Output' if _OUTPOINT.match(key) else
                    'Transaction or payment hash' if _HASH.match(key) else 'Address or other')
            data_list.append((name, kind, str(item), str(labels[item]), network, user))
        sources.append(path)
    data_headers = ('Wallet', 'Labelled Item Type', 'Labelled Item', 'Label', 'Network', 'User')
    return data_headers, data_list, '\n'.join(sources)


def _address(record):
    """The first output's address of a stored request or invoice (legacy [type, address, value] tuples)."""
    outputs = record.get('outputs')
    if isinstance(outputs, list) and outputs and isinstance(outputs[0], list) and len(outputs[0]) >= 2:
        return str(outputs[0][1])
    return ''


def _amount_sat(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value // 1000
    return '' if value is None else str(value)


@artifact_processor
def electrumRequests(context):
    data_list = []
    sources = []
    for path, name, network, user, _encrypted, data in _wallets(context, 'Electrum Payment Requests and Invoices'):
        if not data:
            continue
        rows = 0
        for key, kind in (('payment_requests', 'Payment request'), ('invoices', 'Invoice')):
            records = data.get(key)
            if not isinstance(records, dict):
                continue
            for record_id in sorted(records):
                record = records[record_id]
                if not isinstance(record, dict):
                    continue
                created = record.get('time')
                exp = record.get('exp')
                expires = ''
                if isinstance(created, int) and isinstance(exp, int) and exp:
                    expires = _time(created + exp)
                data_list.append((_time(created), expires, name, kind, _amount_sat(record.get('amount_msat')),
                                  str(record.get('message') or ''), _address(record),
                                  'Yes' if record.get('lightning_invoice') else 'No', str(record_id), network, user))
                rows += 1
        if rows:
            sources.append(path)
    data_headers = (('Created', 'datetime'), ('Expires', 'datetime'), 'Wallet', 'Type', 'Amount (sat)', 'Message',
                    'Address', 'Lightning Invoice', 'Request ID', 'Network', 'User')
    return data_headers, data_list, '\n'.join(sources)
