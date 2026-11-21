__artifacts_v2__ = {
    "bitcoinCoreWalletLog": {
        "name": "Bitcoin Core Wallet Log Events",
        "description": "Wallet lines of Bitcoin Core's debug.log: when a wallet added, updated or re-saw a "
                       "transaction, submitted one for broadcast or to the node's memory pool, or committed one it "
                       "created, with the wallet name and "
                       "transaction ID.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Bitcoin Core",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per wallet event line in debug.log in a Bitcoin Core data directory or in its chain folder (testnet3, testnet4, signet or regtest, https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/chainparamsbase.cpp#L44-L52; Network is that folder, or main). The data directory defaults to AppData\\Local\\Bitcoin on Windows for a fresh install of v32.1, AppData\\Roaming\\Bitcoin when that folder already exists, ~/Library/Application Support/Bitcoin on macOS and ~/.bitcoin on Linux (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/common/args.cpp#L858-L888); a data directory set with -datadir elsewhere is not matched. Each logged line starts with its time in UTC, to the second or, under -logtimemicros, the microsecond (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/logging.cpp#L309-L329); a line without a time continues the one before it. A debug.log written with -nologtimestamps is not read. Bitcoin Core writes a wallet's lines with the wallet's name in brackets (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/wallet/wallet.h#L951-L954); a bracketed name that is one of the logger's own levels or debug categories at v32.1 (warning, net and the like) is not read as a wallet, and a thread name or source location in brackets before the wallet's name is passed over. Rows are three events that name a transaction: AddToWallet, written when the wallet adds or updates a transaction, with its ID, whether it is new, updated, both, or unchanged, and its state (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/wallet/wallet.cpp#L1161); Submitting wtx, written when the wallet submits one of its transactions to the memory pool, for broadcast, or both, the rest of the line saying which (#L2066-L2078); and CommitTransaction, written when the wallet commits a transaction it created, followed by the transaction itself (#L2367). Detail (as logged) is the rest of the line after the event name and the transaction ID, and for CommitTransaction the continuation lines with their leading spaces removed: the transaction's short hash, its inputs, and its outputs with their amounts, each output script cut to its first 30 hexadecimal digits by the writer (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/primitives/transaction.cpp#L63), so an address cannot be read from it. Transaction ID is the first 64-digit hexadecimal ID in the line, blank for CommitTransaction, whose line carries only the short hash. Other wallet lines (fee calculation, coin selection, loading) are not reported. On the known data (windows11_arm_bitcoincore_known_20261108: Bitcoin Core 32.1 on Windows 11, on its private regtest chain with no network, driven through bitcoin-cli over two sessions) the 115 rows matched the rig's RPC results: kd_wallet logged AddToWallet for 105 distinct transaction IDs, the 103 coinbase transactions of the blocks the rig mined and its two sends, and Submitting wtx and CommitTransaction once for each send, the Submitting wtx IDs being the IDs sendtoaddress returned; kd_other logged AddToWallet twice for the one transaction it received. Network and User were uniform on the known data, which had one data directory. A row records what the wallet logged, not who used it, and when Bitcoin Core starts without -debug and its debug.log is over 11,000,000 bytes, it keeps only the last 10,000,000 bytes (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/logging.cpp#L519-L545 and https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/init/common.cpp#L45 and #L112), so older lines may be gone.",
        "paths": ('*/Bitcoin/debug.log', '*/Bitcoin/*/debug.log', '*/.bitcoin/debug.log', '*/.bitcoin/*/debug.log'),
        "output_types": "standard",
        "artifact_icon": "dollar-sign",
        "sample_data": {
            "windows11_arm_bitcoincore_known_20261108": "Windows 11 build 26200 (ARM64), Bitcoin Core 32.1 | 115 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "bitcoinCoreSessions": {
        "name": "Bitcoin Core Log Sessions",
        "description": "One row per start of Bitcoin Core recorded in its debug.log: version, data directory, "
                       "config file, first and last logged time, whether it logged Shutdown done, and failed RPC "
                       "password attempts with their source address.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Bitcoin Core",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per start of Bitcoin Core recorded in debug.log in a Bitcoin Core data directory or in its chain folder (testnet3, testnet4, signet or regtest, https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/chainparamsbase.cpp#L44-L52; Network is that folder, or main). The data directory defaults to AppData\\Local\\Bitcoin on Windows for a fresh install of v32.1, AppData\\Roaming\\Bitcoin when that folder already exists, ~/Library/Application Support/Bitcoin on macOS and ~/.bitcoin on Linux (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/common/args.cpp#L858-L888); a data directory set with -datadir elsewhere is not matched. Each logged line starts with its time in UTC, to the second or, under -logtimemicros, the microsecond (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/logging.cpp#L309-L329); a line without a time continues the one before it. A debug.log written with -nologtimestamps is not read. A session starts at the version line Bitcoin Core writes at startup (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/init/common.cpp#L158) and lasts until the next one; lines before the first version line in the file form a row of their own with Version blank. First Logged and Last Logged are the times of the session's first and last lines. Data Directory and Config File are as logged (#L127-L141). Shutdown Done is Yes when the session logged Shutdown done, the last line of a clean shutdown (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/init.cpp#L434); No can mean a crash, a forced stop or a log cut off. Failed RPC Password Attempts counts the session's lines saying an RPC request carried the wrong password (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/httprpc.cpp#L216), and Failed RPC Sources lists their source addresses without the port. Log Entries counts the session's timestamped entries; continuation lines are not counted. On the known data (windows11_arm_bitcoincore_known_20261108: Bitcoin Core 32.1 on Windows 11, on its private regtest chain with no network, driven through bitcoin-cli over two sessions) the two rows matched the two sessions the rig ran, each starting at the version line and ending with Shutdown done, and each held one failed RPC password attempt from 127.0.0.1, logged within two seconds of start while the rig was polling the node with bitcoin-cli. Version, Data Directory, Config File, Shutdown Done, Failed RPC Password Attempts, Failed RPC Sources, Network and User were uniform on the known data, which had one installation and two clean sessions. When Bitcoin Core starts without -debug and its debug.log is over 11,000,000 bytes, it keeps only the last 10,000,000 bytes (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/logging.cpp#L519-L545 and https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/init/common.cpp#L45 and #L112), so older sessions may be gone, and the first row of a trimmed file can begin mid-session.",
        "paths": ('*/Bitcoin/debug.log', '*/Bitcoin/*/debug.log', '*/.bitcoin/debug.log', '*/.bitcoin/*/debug.log'),
        "output_types": "standard",
        "artifact_icon": "power",
        "sample_data": {
            "windows11_arm_bitcoincore_known_20261108": "Windows 11 build 26200 (ARM64), Bitcoin Core 32.1 | 2 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
    "bitcoinCoreAddressBook": {
        "name": "Bitcoin Core Wallet Address Book",
        "description": "Address book entries of Bitcoin Core wallets kept in SQLite or legacy Berkeley DB: address, "
                       "label and purpose decoded as UTF-8, with the wallet folder and format.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "Bitcoin Core",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per address in the address book of a Bitcoin Core wallet kept in SQLite or legacy Berkeley DB: a file named wallet.dat anywhere under a data directory (see the Wallet Log Events artifact for the locations), which takes in its chain folder, its wallets folder and wallet folders, read only. A SQLite wallet's main table holds key and value pairs (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/wallet/sqlite.cpp#L333). A Berkeley DB wallet holds the same pairs in its main database; the address book is the name records (the label) and purpose records keyed by address (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/wallet/walletdb.cpp#L48-L52 and #L77-L92), each a length-prefixed string. Address, label and purpose are decoded as UTF-8, and bytes that are not valid UTF-8 are replaced. Purpose is not mapped or translated; v32.1 names receive, send and refund (https://github.com/bitcoin/bitcoin/blob/f0de87f040621468b956f01f526a43a010310501/src/wallet/wallet.h#L280-L286), and any other string is kept as it is. Other records, the wallet's keys among them, are skipped once their record type is read, and nothing from them is output. Wallet is the folder holding wallet.dat, blank for a wallet.dat directly in a data directory, chain folder or wallets folder. Wallet Format is SQLite, Berkeley DB, or Berkeley DB (not flushed). A Berkeley DB wallet is read directly from the file by following Bitcoin Core's own read-only reader (https://github.com/bitcoin/bitcoin/blob/32efe850438ef22e2de39e562af557872a402c31/src/wallet/migrate.cpp#L524-L700), with the same name and purpose records. That reader refuses a file whose page log sequence numbers are not reset, because newer changes can be only in the wallet's database log. This artifact reads such a file, marks it not flushed and names it in the run log, and does not read the log. A wallet.dat that is neither format, or that the reader cannot walk, gives a run log line and no row. Wallet encryption covers only private keys (https://github.com/bitcoin/bitcoin/blob/32efe850438ef22e2de39e562af557872a402c31/doc/managing-wallets.md#L50) and left the address book readable on the two encrypted wallets tested. Berkeley DB's own file encryption is not read. On six Berkeley DB wallets made by Bitcoin Core 0.21.2 and 28.1 (windows11_arm_bitcoin_legacy_v0212_known_20261121 and windows11_arm_bitcoin_legacy_v281_known_20261121, private regtest chain), every key and value pair equalled db_dump 4.7.25 and the address books equalled what listlabels and getaddressesbylabel returned, including a 6,008-character label held on one overflow page. A value spread over more than one overflow page was not in the test data. One further wallet, on the 28.1 key, was force-stopped after 12 labelled addresses: it was marked not flushed and all 12 were in the file. Another unclean stop may leave entries only in the log. Wallet Format held one value on windows11_arm_bitcoincore_known_20261108 (SQLite) and on windows11_arm_bitcoin_legacy_v0212_known_20261121 (Berkeley DB), and two values on windows11_arm_bitcoin_legacy_v281_known_20261121. On the known data (windows11_arm_bitcoincore_known_20261108: Bitcoin Core 32.1 on Windows 11, on its private regtest chain with no network, driven through bitcoin-cli over two sessions) the four SQLite rows matched what the rig's getnewaddress, setlabel and listlabels returned: kd_wallet's two receive addresses with their labels and one send address labelled for kd_other's address, and kd_other's own receive address, with no label. Network is the chain folder the wallet.dat is under (testnet3, testnet4, signet or regtest), or main when there is none. It comes from the path, not from the wallet. User is the profile folder in the path. Network and User were uniform on the known data. A row records an address the wallet kept, not that it received or sent anything.",
        "paths": ('*/Bitcoin/*wallet.dat', '*/.bitcoin/*wallet.dat'),
        "output_types": "standard",
        "artifact_icon": "book-open",
        "sample_data": {
            "windows11_arm_bitcoincore_known_20261108": "Windows 11 build 26200 (ARM64), Bitcoin Core 32.1 | 4 rows",
            "windows11_arm_bitcoin_legacy_v0212_known_20261121": "Windows 11 build 26200 (ARM64), Bitcoin Core 0.21.2 | 248 rows",
            "windows11_arm_bitcoin_legacy_v281_known_20261121": "Windows 11 build 26200 (ARM64), Bitcoin Core 28.1 | 260 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22 (Wilma), Cinnamon | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
import re
import sqlite3
import struct
from datetime import datetime, timezone
from pathlib import PurePosixPath

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly
from scripts.macos_plists import user_from_path

# Chain folders inside the data directory (src/chainparamsbase.cpp, lines 44 to 52); mainnet uses the data directory itself.
_CHAIN_FOLDERS = ('testnet3', 'testnet4', 'signet', 'regtest')
_ROOTS = ('Bitcoin', '.bitcoin')
# A logged line starts with an ISO 8601 UTC time, with microseconds under -logtimemicros, and a mock time
# under -mocktime (src/logging.cpp, LogTimestampStr).
_LINE = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{6}))?Z(?: \(mocktime: [^)]*\))? (.*)$')
_TXID = re.compile(r'\b[0-9a-f]{64}\b')
# Bracketed prefixes the logger itself writes, which are not wallet names: the levels and the debug
# categories at v32.1 (src/logging.cpp, LOG_CATEGORIES_BY_STR from line 179, LogLevelToStr, and all from LogCategoryToStr).
_NOT_WALLETS = {'warning', 'error', 'info', 'debug', 'trace', 'net', 'tor', 'mempool', 'http', 'bench', 'zmq',
                'walletdb', 'rpc', 'estimatefee', 'addrman', 'selectcoins', 'reindex', 'cmpctblock', 'rand', 'prune',
                'proxy', 'mempoolrej', 'coindb', 'qt', 'leveldb', 'validation', 'i2p', 'ipc', 'lock',
                'blockstorage', 'txreconciliation', 'scan', 'txpackages', 'kernel', 'privatebroadcast', 'mining', 'all'}
_EVENTS = ('AddToWallet', 'Submitting wtx', 'CommitTransaction')
_VERSION = re.compile(r'^Bitcoin(?: Core)?(?: Daemon)? version (\S+)')
_RPC_FAIL = re.compile(r'ThreadRPCServer incorrect password attempt from (\S+)')
_SQLITE_MAGIC = b'SQLite format 3\x00'
# Berkeley DB btree layout as Bitcoin Core's own read-only reader gives it (src/wallet/migrate.cpp at v28.1).
_BDB_MAGIC = 0x00053162
_BDB_VERSION = 9
_BDB_SUBDB = 0x20
_BDB_PAGE_HEADER = 26
_BDB_INTERNAL, _BDB_LEAF, _BDB_OVERFLOW, _BDB_META = 3, 5, 7, 9
_BDB_KEYDATA, _BDB_OVERFLOW_RECORD, _BDB_DELETED = 1, 3, 0x80


def _relative(context, path):
    return str(context.get_relative_path(path)).replace('\\', '/')


def _home_user(parts):
    if 'home' in parts and parts.index('home') + 1 < len(parts):
        return parts[parts.index('home') + 1]
    return ''


def _network(parts):
    """The chain named by the folder after the data directory, or main."""
    for index, part in enumerate(parts):
        if part in _ROOTS and index + 1 < len(parts) and parts[index + 1] in _CHAIN_FOLDERS:
            return parts[index + 1]
    return 'main'


def _in_data_dir(parts):
    """True for a debug.log directly in a data directory or its chain folder."""
    if len(parts) >= 2 and parts[-2] in _ROOTS:
        return True
    return len(parts) >= 3 and parts[-2] in _CHAIN_FOLDERS and parts[-3] in _ROOTS


def _time(stamp, micros):
    value = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    return value.replace(microsecond=int(micros)) if micros else value


def read_log(handle):
    """Yield (time, message, continuation lines) for each logged entry of a debug.log."""
    when, message, more = None, None, []
    for raw in handle:
        line = raw.rstrip('\r\n')
        match = _LINE.match(line)
        if match:
            if when is not None:
                yield when, message, more
            when, message, more = _time(match.group(1), match.group(2)), match.group(3), []
        elif when is not None and line.strip():
            more.append(line.strip())
    if when is not None:
        yield when, message, more


_WALLET_EVENT = re.compile(r'^(?:\[[^\]]*\] )*\[([^\]]*)\] (?=AddToWallet|Submitting wtx|CommitTransaction)')


def _wallet_prefix(message):
    """(wallet name, rest) when a wallet event follows the wallet's bracketed name, else ('', message).

    The name is the bracket right before the event word, so a thread name (-logthreadnames), a source
    location (-logsourcelocations) or a level or category written before it is passed over.
    """
    match = _WALLET_EVENT.match(message)
    if match and match.group(1).split(':')[0].lower() not in _NOT_WALLETS:
        return match.group(1), message[match.end():]
    return '', message


def _log_files(context):
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path):
            continue
        relative_path = context.get_relative_path(path)
        parts = PurePosixPath(str(relative_path).replace('\\', '/')).parts
        if parts[-1] != 'debug.log' or not _in_data_dir(parts):
            continue
        yield path, parts, user_from_path(relative_path) or _home_user(parts)


@artifact_processor
def bitcoinCoreWalletLog(context):
    data_list = []
    sources = []
    for path, parts, user in _log_files(context):
        with open(path, encoding='utf-8', errors='replace') as handle:
            for when, message, more in read_log(handle):
                wallet, rest = _wallet_prefix(message)
                if not wallet or not rest.startswith(_EVENTS):
                    continue
                event = next(name for name in _EVENTS if rest.startswith(name))
                txid = _TXID.search(rest)
                detail = rest[len(event):].strip(' :')
                if txid:
                    detail = detail.replace(txid.group(0), '', 1).strip()
                if more:
                    detail = '\n'.join(([detail] if detail else []) + more)
                data_list.append((when, wallet, event, txid.group(0) if txid else '', detail, _network(parts), user))
        sources.append(path)
    data_headers = (('Time', 'datetime'), 'Wallet', 'Event', ('Transaction ID', 'hash'), 'Detail (as logged)',
                    'Network', 'User')
    return data_headers, data_list, '\n'.join(sources)


def _without_port(peer):
    """The address of a logged peer, without its port: 127.0.0.1:1234 or [::1]:1234."""
    match = re.match(r'^\[(.*)\]:\d+$', peer) or re.match(r'^([^:]*):\d+$', peer)
    return match.group(1) if match else peer


@artifact_processor
def bitcoinCoreSessions(context):
    data_list = []
    sources = []
    for path, parts, user in _log_files(context):
        sessions = []
        current = None
        with open(path, encoding='utf-8', errors='replace') as handle:
            for when, message, _more in read_log(handle):
                version = _VERSION.match(message)
                if version or current is None:
                    current = {'start': when, 'end': when, 'version': version.group(1) if version else '',
                               'datadir': '', 'config': '', 'shutdown': False, 'rpc': [], 'lines': 0}
                    sessions.append(current)
                current['end'] = when
                current['lines'] += 1
                if message.startswith('Using data directory '):
                    current['datadir'] = message[len('Using data directory '):]
                elif message.startswith('Config file: '):
                    current['config'] = message[len('Config file: '):]
                elif message == 'Shutdown done':
                    current['shutdown'] = True
                rpc = _RPC_FAIL.search(message)
                if rpc:
                    current['rpc'].append(_without_port(rpc.group(1)))
        for session in sessions:
            data_list.append((session['start'], session['end'], session['version'], session['datadir'],
                              session['config'], 'Yes' if session['shutdown'] else 'No', len(session['rpc']),
                              ', '.join(sorted(set(session['rpc']))), session['lines'], _network(parts), user))
        sources.append(path)
    data_headers = (('First Logged', 'datetime'), ('Last Logged', 'datetime'), 'Version', 'Data Directory',
                    'Config File', 'Shutdown Done', ('Failed RPC Password Attempts', 'number'),
                    'Failed RPC Sources', ('Log Entries', 'number'), 'Network', 'User')
    return data_headers, data_list, '\n'.join(sources)


def _compact(blob, index):
    """A Bitcoin CompactSize length and the bytes it prefixes (src/serialize.h)."""
    if index >= len(blob):
        raise ValueError('past the end')
    size = blob[index]
    index += 1
    if size == 253:
        size, index = int.from_bytes(blob[index:index + 2], 'little'), index + 2
    elif size == 254:
        size, index = int.from_bytes(blob[index:index + 4], 'little'), index + 4
    elif size == 255:
        size, index = int.from_bytes(blob[index:index + 8], 'little'), index + 8
    if index + size > len(blob):
        raise ValueError('string runs past the end')
    return blob[index:index + size], index + size


def book_from_records(records):
    """{address: [label, purpose]} from a wallet's key and value pairs."""
    book = {}
    for key, value in records:
        try:
            record, index = _compact(bytes(key), 0)
            if record not in (b'name', b'purpose'):
                continue
            address, _ = _compact(bytes(key), index)
            text, _ = _compact(bytes(value), 0)
        except (ValueError, TypeError):
            continue
        entry = book.setdefault(address.decode('utf-8', 'replace'), ['', ''])
        entry[0 if record == b'name' else 1] = text.decode('utf-8', 'replace')
    return book


def address_book(db):
    """{address: [label, purpose]} from the name and purpose records of a SQLite wallet."""
    return book_from_records(db.execute('SELECT key, value FROM main'))


class _BdbFile:
    """The pages of a Berkeley DB btree file, each read checked against its own page number."""

    def __init__(self, data):
        if len(data) < 512:
            raise ValueError('shorter than a metadata page')
        magic = struct.unpack_from('<I', data, 12)[0]
        if magic == _BDB_MAGIC:
            self.order = '<'
        elif magic == int.from_bytes(_BDB_MAGIC.to_bytes(4, 'little'), 'big'):
            self.order = '>'
        else:
            raise ValueError('no btree magic')
        self.data = data
        self.page_size = self.u32(0, 20)
        if self.page_size < 512 or self.page_size > 65536 or self.page_size & (self.page_size - 1):
            raise ValueError('bad page size')

    def u32(self, base, offset):
        return struct.unpack_from(self.order + 'I', self.data, base + offset)[0]

    def u16(self, base, offset):
        return struct.unpack_from(self.order + 'H', self.data, base + offset)[0]

    def page(self, number):
        """The byte offset of a page, after checking that it is whole and carries its own number."""
        base = number * self.page_size
        if base + self.page_size > len(self.data) or self.u32(base, 8) != number:
            raise ValueError(f'page {number} is missing or misnumbered')
        return base

    def meta(self, number):
        """The root page of the btree whose metadata page this is."""
        base = self.page(number)
        if self.u32(base, 12) != _BDB_MAGIC or self.u32(base, 16) != _BDB_VERSION:
            raise ValueError('unsupported btree version')
        if self.data[base + 25] != _BDB_META or self.u32(base, 48) != _BDB_SUBDB:
            raise ValueError('not a wallet btree')
        if self.data[base + 24]:
            raise ValueError('Berkeley DB encryption')
        return self.u32(base, 88)

    def flushed(self):
        """True when every page's log sequence number is the reset value, file 0 offset 1."""
        last = len(self.data) // self.page_size
        return all(self.u32(n * self.page_size, 0) == 0 and self.u32(n * self.page_size, 4) == 1 for n in range(last))

    def overflow(self, number):
        out = bytearray()
        seen = set()
        while number:
            if number in seen:
                raise ValueError('overflow chain loops')
            seen.add(number)
            base = self.page(number)
            if self.data[base + 25] != _BDB_OVERFLOW:
                raise ValueError('bad overflow page')
            out += self.data[base + _BDB_PAGE_HEADER:base + _BDB_PAGE_HEADER + self.u16(base, 22)]
            number = self.u32(base, 16)
        return bytes(out)

    def items(self, base):
        """(kind, deleted, offset, length) for each item of a page."""
        for entry in range(self.u16(base, 20)):
            offset = base + self.u16(base, _BDB_PAGE_HEADER + 2 * entry)
            kind = self.data[offset + 2]
            yield kind & ~_BDB_DELETED, bool(kind & _BDB_DELETED), offset, self.u16(offset, 0)

    def leaf_values(self, base):
        values = []
        for kind, deleted, offset, length in self.items(base):
            if kind not in (_BDB_KEYDATA, _BDB_OVERFLOW_RECORD):
                raise ValueError('unknown record type')
            if deleted:
                continue
            values.append(self.data[offset + 3:offset + 3 + length] if kind == _BDB_KEYDATA
                          else self.overflow(self.u32(offset, 4)))
        if len(values) % 2:
            raise ValueError('a key without a value')
        return values


def bdb_wallet_records(data):
    """([(key, value)], whether the file is flushed) for the live records of a Berkeley DB wallet's main database.

    Follows BerkeleyRODatabase::Open (src/wallet/migrate.cpp at v28.1), except that a file with log sequence
    numbers not reset is read and reported as not flushed instead of being refused.
    """
    bdb = _BdbFile(data)
    outer = bdb.page(bdb.meta(0))
    if bdb.data[outer + 25] != _BDB_LEAF:
        raise ValueError('unexpected outer root')
    names = bdb.leaf_values(outer)
    if len(names) != 2 or names[0] != b'main' or len(names[1]) != 4:
        raise ValueError('no main subdatabase')
    pending = [bdb.meta(int.from_bytes(names[1], 'big'))]
    seen, records = set(), []
    while pending:
        number = pending.pop()
        if number in seen:
            raise ValueError('btree loops')
        seen.add(number)
        base = bdb.page(number)
        kind = bdb.data[base + 25]
        if kind == _BDB_INTERNAL:
            pending.extend(bdb.u32(offset, 4) for _kind, deleted, offset, _length in bdb.items(base) if not deleted)
        elif kind == _BDB_LEAF:
            values = bdb.leaf_values(base)
            records.extend(zip(values[0::2], values[1::2]))
        else:
            raise ValueError('unexpected page type')
    return records, bdb.flushed()


def _wallet_book(context, path):
    """(address book, wallet format) of one wallet.dat, or None when it could not be read (logged)."""
    label = 'Bitcoin Core Wallet Address Book'
    with open(path, 'rb') as handle:
        data = handle.read()
    if data[:16] == _SQLITE_MAGIC:
        db = open_sqlite_db_readonly(path)
        if db is None:
            return None
        try:
            return address_book(db), 'SQLite'
        except sqlite3.Error as exc:
            logfunc(f'{label}: could not read {_relative(context, path)}: {exc}')
            return None
        finally:
            db.close()
    try:
        records, flushed = bdb_wallet_records(data)
    except (ValueError, IndexError, struct.error) as exc:
        logfunc(f'{label}: {_relative(context, path)} is not a SQLite or readable Berkeley DB wallet: {exc}')
        return None
    if not flushed:
        logfunc(f'{label}: {_relative(context, path)} is not flushed, so newer changes may be only in its database log')
    return book_from_records(records), 'Berkeley DB' if flushed else 'Berkeley DB (not flushed)'


@artifact_processor
def bitcoinCoreAddressBook(context):
    data_list = []
    sources = []
    for path in sorted(str(p) for p in context.get_files_found()):
        if not os.path.isfile(path) or os.path.basename(path) != 'wallet.dat':
            continue
        result = _wallet_book(context, path)
        if result is None:
            continue
        book, wallet_format = result
        relative_path = context.get_relative_path(path)
        parts = PurePosixPath(str(relative_path).replace('\\', '/')).parts
        wallet = parts[-2] if len(parts) >= 2 and parts[-2] not in _ROOTS + _CHAIN_FOLDERS + ('wallets',) else ''
        user = user_from_path(relative_path) or _home_user(parts)
        for address in sorted(book):
            label, purpose = book[address]
            data_list.append((address, label, purpose, wallet, wallet_format, _network(parts), user))
        sources.append(path)
    data_headers = ('Address', 'Label', 'Purpose', 'Wallet', 'Wallet Format', 'Network', 'User')
    return data_headers, data_list, '\n'.join(sources)
