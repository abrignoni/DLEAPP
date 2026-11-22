"""Exodus desktop wallet artifacts for DLEAPP.

Author: @AlexisBrignoni, Claude.

Three artifacts over a folder named exodus.wallet inside a folder named Exodus:

- Exodus Wallet Secrets: recovers the wallet passphrase and, from seed.seco, the BIP-39
  recovery phrase and 64-byte seed, when the wallet opens with its stored passphrase or a
  supplied password. The container format is read with scripts/exodus_wallet.py, sourced
  from Exodus's own MIT packages.
- Exodus Wallet App State: the analytics identifiers and the has-balance flag from the
  plaintext unsafe-storage.json. The market price history that fills most of that file is
  not reported.
- Exodus Wallet Files: lists the files in the folder with their sizes and the times the
  input holds, without staging them, for context.

Recovered secrets are placed only in the report. No seed, passphrase, key or recovery
phrase value is written to the run log.
"""

import json
import os
from datetime import datetime, timezone

from scripts import exodus_wallet as ew
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.search_files import PeekUnsupported

__artifacts_v2__ = {
    "exodusWallet": {
        "name": "Exodus Wallet Secrets",
        "description": "Wallet passphrase and, from seed.seco, the stored 64-byte seed and the BIP-39 "
                       "phrase for the stored entropy, shown when seed.seco opens with the stored "
                       "passphrase or a supplied password. When neither opens it, the row says so and "
                       "shows no secret.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "PyCryptodome. A password can be supplied with --exodus-password (not exercised "
                        "on known data).",
        "category": "Exodus",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per seed.seco in a folder named exodus.wallet inside a folder named Exodus. "
                 "passphrase.json holds the wallet passphrase and a system flag. On the known data, a "
                 "wallet where no password was set, system was true and the stored passphrase opened "
                 "seed.seco; what system means is not sourced from Exodus code. seed.seco is a SECO "
                 "container (secure-container 2.0.0, commit 4c005ec; seco-file 2.0.0, commit 94441f8; "
                 "seco-rw 0.0.2); the versions Exodus 26.11.20 ships were not read, and the layout was "
                 "measured on the known data. scrypt stretches the passphrase with the parameters the "
                 "file stores (n=16384 r=8 p=1 on the known data and in the package default), AES-256-GCM "
                 "unwraps a blob key, AES-256-GCM decrypts the blob, and a SHA-256 checksum covers the "
                 "metadata and the encrypted blob. The plaintext uses the framing seco-keyval 0.7.0 and "
                 "buffer-noise 1.0.1 use: a 4-byte length, then gzip, then noise to 32768 bytes; its "
                 "content is not the JSON a seco-keyval store holds. On the known data the gunzipped "
                 "payload was 80 bytes: a 64-byte seed followed by 16 bytes of entropy; another length "
                 "is not decoded and is reported as unrecognised, with the passphrase shown and the seed "
                 "and phrase blank. Recovery Phrase is entropyToMnemonic(entropy) with the standard "
                 "BIP-39 English wordlist (@exodus/bip39 1.1.1); it was not compared with the phrase the "
                 "Exodus app displays. Phrase Verified is Yes when mnemonicToSeed(phrase), "
                 "PBKDF2-HMAC-SHA512 with salt mnemonic over 2048 iterations, equals the stored 64-byte "
                 "seed, so the phrase derives the stored seed with an empty BIP-39 passphrase; No means "
                 "it did not, and the phrase and seed are still shown. Passphrase is the value that "
                 "opened seed.seco. Protection reads Stored passphrase (system flag set) when the stored "
                 "passphrase opened the wallet and the flag was the boolean true, Stored passphrase "
                 "(system flag not set) when it opened and the flag was the boolean false, Stored "
                 "passphrase (system flag unknown) when it opened and the flag was missing or not a "
                 "boolean, User password (supplied) when a supplied "
                 "password opened it, seed.seco did not read when the container was damaged or not a "
                 "SECO file, and Not opened (a password may be needed, see --exodus-password) when a "
                 "passphrase was present but did not open it or none was available. Seed (hex) is the "
                 "stored 64-byte seed in hex. Modified (UTC) is the seed.seco modified time the input "
                 "holds, blank when it holds none in UTC. User is the folder after Users or home in the "
                 "path. On the known data (windows11_arm_exodus_known_20261122) system was true, "
                 "seed.seco opened with the stored passphrase, and Phrase Verified was Yes on the 1 row. "
                 "A wallet the user protected with a password was not part of the known data, so the "
                 "--exodus-password path is provided but unexercised: the supplied password is tried as "
                 "the SECO passphrase and counts as opening the wallet when the AES-GCM tag on the blob "
                 "key checks; a password that does not open it is reported as not opening the wallet and "
                 "no secret is shown, and whether Exodus uses the user password directly as this "
                 "passphrase is not established. A seed and phrase being present does not show that the "
                 "wallet was funded or used. storage.seco is not read by this artifact.",
        "paths": ("*/Exodus/exodus.wallet/passphrase.json", "*/Exodus/exodus.wallet/seed.seco"),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "key",
        "sample_data": {
            "windows11_arm_exodus_known_20261122": "Windows 11 build 26200 (ARM64), Exodus 26.11.20 | 1 row",
        },
    },
    "exodusWalletState": {
        "name": "Exodus Wallet App State",
        "description": "Analytics identifiers and the has-balance flag Exodus stores in the "
                       "plaintext unsafe-storage.json of a desktop wallet.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Exodus",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per unsafe-storage.json in a folder named exodus.wallet inside a folder named "
                 "Exodus. unsafe-storage.json is the plaintext (unencrypted) store, with keys separated "
                 "by exclamation marks. Anonymous ID is !analytics!anonymousId, User ID is "
                 "!analytics!userId: identifiers Exodus stores for the install. They are reported as "
                 "stored, and how Exodus generates them is not established. Has Balance is "
                 "!balances!hasBalance: Yes or No for a JSON boolean, blank for any other type. On the "
                 "known data the other keys were market price "
                 "history (55 of 70 keys, most of the file), migration flags, remote configuration, A/B "
                 "testing data and an announcements entry; they are not reported. On the known data the "
                 "file did not contain the seed, passphrase or phrase text. On the known data, a wallet "
                 "that was never funded, Has Balance was No. A field is blank when the file does not "
                 "hold it.",
        "paths": ("*/Exodus/exodus.wallet/unsafe-storage.json",),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "activity",
        "sample_data": {
            "windows11_arm_exodus_known_20261122": "Windows 11 build 26200 (ARM64), Exodus 26.11.20 | 1 row",
        },
    },
    "exodusWalletFiles": {
        "name": "Exodus Wallet Files",
        "description": "Files in an Exodus desktop wallet folder (exodus.wallet): name, size and the "
                       "modified and created times the input holds for each file. This artifact lists "
                       "them without staging or parsing them.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-22",
        "last_update_date": "2026-11-22",
        "requirements": "none",
        "category": "Exodus",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per file under a folder named exodus.wallet inside a folder named Exodus. This "
                 "artifact lists the files through the seeker's peek() and stages none; the other two "
                 "Exodus artifacts stage passphrase.json, seed.seco and unsafe-storage.json when they "
                 "run. File is the path below exodus.wallet as the input names it, and Source File is the "
                 "file's full input-relative path, which separates two wallet copies that share a profile "
                 "name. On the known data "
                 "(windows11_arm_exodus_known_20261122) the folder held passphrase.json, seed.seco, "
                 "storage.seco and unsafe-storage.json, which were present after Exodus 26.11.20 first "
                 "started with nothing clicked or typed. Their presence alone does not show that a "
                 "person set up, funded or used a wallet. "
                 "Modified (UTC) and Created (UTC) are the UTC times the input holds for the file, blank "
                 "when it holds none in UTC. Time Source names where the input's times came from, and "
                 "reads none when no time was read. On the known data, a tar, Time Source held tar header "
                 "on all 4 rows, Modified equalled the file's NTFS last-write second on all 4 rows, and "
                 "Created is blank on all 4 rows (the tar carries no creation time). User is the folder "
                 "after Users or home in the path, empty when the path has neither, and held one profile "
                 "folder name on all 4 rows of the known data.",
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "credit-card",
        "sample_data": {
            "windows11_arm_exodus_known_20261122": "Windows 11 build 26200 (ARM64), Exodus 26.11.20 | 4 rows",
        },
    },
}


def _instant(value):
    if value is None:
        return ''
    try:
        return datetime.fromtimestamp(float(value), timezone.utc)
    except (OverflowError, OSError, ValueError, TypeError):
        return ''


def _within_wallet(relative):
    """The path below the exodus.wallet folder, when it sits directly inside a folder named Exodus."""
    parts = relative.replace('\\', '/').split('/')
    for index in range(1, len(parts) - 1):
        if parts[index] == 'exodus.wallet' and parts[index - 1].lower() == 'exodus':
            return '/'.join(parts[index + 1:])
    return ''


def _wallet_folder(relative):
    """The path of the exodus.wallet folder in a relative path, or '' when it is not one."""
    parts = relative.replace('\\', '/').split('/')
    for index in range(1, len(parts)):
        if parts[index] == 'exodus.wallet' and parts[index - 1].lower() == 'exodus':
            return '/'.join(parts[:index + 1])
    return ''


def _profile_user(path):
    """The folder after the first Users or home folder of a path, or '' when it has neither."""
    parts = path.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'home'):
            return parts[index + 1]
    return ''


def _seed_times(context, staged_path):
    """The StagedTimes the seeker holds for a staged file, or None."""
    seeker = context.get_seeker()
    extraction_path = context.get_source_file_path(staged_path)
    file_info = seeker.file_infos.get(extraction_path) if seeker else None
    return getattr(file_info, 'times', None) if file_info else None


def _group_by_wallet(context):
    """Map each wallet folder (relative) to {basename: staged path} for the files found."""
    wallets = {}
    for staged in sorted({str(found) for found in context.get_files_found()}):
        if os.path.isdir(staged):
            continue
        relative = context.get_relative_path(staged)
        folder = _wallet_folder(relative)
        if not folder:
            continue
        wallets.setdefault(folder, {})[os.path.basename(relative)] = staged
    return wallets


@artifact_processor
def exodusWallet(context):
    data_headers = (('Modified (UTC)', 'datetime'), 'User', 'Protection', 'Passphrase',
                    'Recovery Phrase', 'Seed (hex)', 'Phrase Verified', 'Source File')
    data_list = []
    sources = []
    supplied_password = context.get_app_secret('exodus_password')
    for folder, files in sorted(_group_by_wallet(context).items()):
        seed_path = files.get('seed.seco')
        if not seed_path:
            continue
        sources.append(seed_path)
        relative = context.get_relative_path(seed_path)
        user = _profile_user(relative)
        modified = ''
        times = _seed_times(context, seed_path)
        if times is not None:
            modified = _instant(times.modified)

        stored_passphrase = system_flag = None
        passphrase_path = files.get('passphrase.json')
        if passphrase_path:
            sources.append(passphrase_path)
            try:
                with open(passphrase_path, 'rb') as handle:
                    stored_passphrase, system_flag = ew.read_passphrase_file(handle.read())
            except OSError as exc:
                logfunc(f'Exodus Wallet Secrets: could not read passphrase.json in {folder}: {exc}')

        try:
            with open(seed_path, 'rb') as handle:
                seed_bytes = handle.read()
        except OSError as exc:
            logfunc(f'Exodus Wallet Secrets: could not read seed.seco in {folder}: {exc}')
            continue

        attempts = []
        if stored_passphrase:
            attempts.append(('stored', stored_passphrase))
        if supplied_password:
            attempts.append(('supplied', supplied_password))

        opened_with = None
        payload = None
        unreadable = False
        for label, secret in attempts:
            try:
                payload = ew.seco_store_payload(seed_bytes, secret)
                opened_with = label
                break
            except ew.WrongPassphrase:
                continue
            except ew.SecoError as exc:
                logfunc(f'Exodus Wallet Secrets: seed.seco in {folder} did not read: {exc}')
                unreadable = True
                break

        if opened_with == 'stored':
            if system_flag is True:
                protection = 'Stored passphrase (system flag set)'
            elif system_flag is False:
                protection = 'Stored passphrase (system flag not set)'
            else:
                protection = 'Stored passphrase (system flag unknown)'
            passphrase_value = stored_passphrase
        elif opened_with == 'supplied':
            protection = 'User password (supplied)'
            passphrase_value = supplied_password
        elif unreadable:
            protection = 'seed.seco did not read'
            passphrase_value = ''
        else:
            protection = 'Not opened (a password may be needed, see --exodus-password)'
            passphrase_value = ''

        if payload is None:
            data_list.append((modified, user, protection, '', '', '', '', relative))
            continue

        parsed = ew.parse_seed_payload(payload)
        if not parsed['recognised']:
            logfunc(f'Exodus Wallet Secrets: seed.seco in {folder} opened but its payload '
                    f'was {parsed["length"]} bytes, not the expected 80')
            data_list.append((modified, user, protection + ' (unrecognised seed payload)',
                              passphrase_value or '', '', '', '', relative))
            continue

        phrase_verified = 'Yes' if parsed['verified'] else 'No'
        data_list.append((modified, user, protection, passphrase_value or '',
                          parsed['mnemonic'], parsed['seed'].hex(), phrase_verified, relative))

    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def exodusWalletState(context):
    data_headers = ('User', 'Anonymous ID', 'User ID', 'Has Balance', 'Source File')
    data_list = []
    sources = []
    for folder, files in sorted(_group_by_wallet(context).items()):
        unsafe_path = files.get('unsafe-storage.json')
        if not unsafe_path:
            continue
        relative = context.get_relative_path(unsafe_path)
        # Record the store as found before reading it, so an unreadable one still shows in the
        # source list rather than looking like a run that found no store.
        sources.append(unsafe_path)
        try:
            with open(unsafe_path, 'rb') as handle:
                parsed = json.loads(handle.read())
        except (OSError, ValueError) as exc:
            logfunc(f'Exodus Wallet App State: could not read unsafe-storage.json in {folder}: {exc}')
            continue
        if not isinstance(parsed, dict):
            logfunc(f'Exodus Wallet App State: unsafe-storage.json in {folder} is not a JSON object')
            continue
        anonymous_id = parsed.get('!analytics!anonymousId', '')
        user_id = parsed.get('!analytics!userId', '')
        has_balance = parsed.get('!balances!hasBalance')
        # Only a JSON boolean gives Yes or No; a string such as "false" or another type stays blank.
        has_balance_text = ('Yes' if has_balance else 'No') if isinstance(has_balance, bool) else ''
        data_list.append((_profile_user(relative),
                          anonymous_id if isinstance(anonymous_id, str) else '',
                          user_id if isinstance(user_id, str) else '',
                          has_balance_text, relative))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def exodusWalletFiles(context):
    data_headers = (('Modified (UTC)', 'datetime'), ('Created (UTC)', 'datetime'), 'File',
                    ('Size (bytes)', 'number'), 'Time Source', 'User', 'Source File')
    data_list, sources = [], []
    seeker = context.get_seeker()
    if seeker is None or not hasattr(seeker, 'peek'):
        logfunc('Exodus Wallet Files: this input gives no way to list a file without staging it')
        return data_headers, data_list, ''
    try:
        peeked = seeker.peek('*/Exodus/exodus.wallet/*', 1)
    except PeekUnsupported as exc:
        logfunc(f'Exodus Wallet Files: {exc}')
        return data_headers, data_list, ''
    seen = set()
    for item in sorted(peeked, key=lambda entry: entry.path):
        name = _within_wallet(item.path)
        if not name or item.path in seen:
            continue
        seen.add(item.path)
        times = getattr(item.info, 'times', None)
        data_list.append((_instant(times.modified) if times else '', _instant(times.created) if times else '',
                          name, item.size, times.source if times else '', _profile_user(item.path), item.path))
        sources.append(item.path)
    return data_headers, data_list, '\n'.join(sources)
