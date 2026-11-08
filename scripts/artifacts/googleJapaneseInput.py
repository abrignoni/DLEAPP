"""Google Japanese Input (Mozc) user history and user dictionary on Windows, for DLEAPP.

Google Japanese Input is Google's build of Mozc. It keeps its per-user files in
AppData\\LocalLow\\Google\\Google Japanese Input (the open-source Mozc build in
AppData\\LocalLow\\Mozc). The learned-input history, history.db, is AES-256 encrypted with a
key derived from a random password that encrypt_key.db holds as a user DPAPI blob; the user
dictionary, user_dictionary.db, is a plain protobuf. Line references are to google/mozc at
c4ed4683fb400b240e81d0a3895d024e3e21325e.
"""

__artifacts_v2__ = {
    "googleJapaneseInputHistory": {
        "name": "Google Japanese Input History",
        "description": "Entries in the encrypted learning history of Google Japanese Input (Mozc) on Windows: when each was last learned, the reading, the text committed and how many times it was learned. Decrypting the history needs the user's DPAPI key, recovered from the account's ARSO (TBAL) secret or from a password supplied with --windows-user-password.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Japanese IME",
        "notes": "Reads history.db in the Google Japanese Input folder under AppData\\LocalLow\\Google (and the open-source build's AppData\\LocalLow\\Mozc), the folder Mozc uses on Windows, including when the input method runs inside an AppContainer (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/base/system_util.cc#L193-L203, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/base/win32/win_util.cc#L98-L171). history.db is a 32-byte salt followed by the AES-256-CBC encryption, zero IV and PKCS#5 padding, of a serialized UserHistory protobuf (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/storage/encrypted_string_storage.cc#L55 and #L61-L122, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/base/encryptor.cc#L93-L153 and #L212-L257, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/prediction/user_history_storage.cc#L75 and #L203-L253). The AES key is the first 32 bytes of the CryptDeriveKey-style SHA-1 expansion of a 32-byte random password plus the salt; the password is kept in encrypt_key.db in the same folder as a user DPAPI blob with no extra entropy (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/base/password_manager.cc#L64-L70 and #L235-L259, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/base/encryptor.cc#L262-L308). The blob is opened with the vendored dpapiprobe library (scripts/vendor/dpapiprobe, with PyCryptodome), using the user master keys under AppData\\Roaming\\Microsoft\\Protect unlocked by the account's ARSO (TBAL) secret from the SYSTEM and SECURITY hives or by a cleartext password supplied with --windows-user-password, the same key recovery the Windows Chromium Saved Passwords artifact uses. One row per history entry, from the UserHistory fields in https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/prediction/user_history_predictor.proto. Reading is key, the text typed before conversion; Text is value, the text committed; Description is description, a note Mozc attached to the candidate, shown as stored. Last Learned (UTC) is last_access_time, Unix seconds, set to the current time each time the entry is learned (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/prediction/user_history_predictor.cc#L2054-L2058 and #L604-L607). Times Learned is suggestion_freq, raised by one at each learning. Removed is Yes when the removed flag is set: Mozc sets it, and sets suggestion_freq to 0, when the entry was among the first five results of finished conversions often but chosen in under 5% of them (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/prediction/user_history_predictor.cc#L2069-L2096 and #L2146), and when the user deletes the entry (#L530-L560). A removed entry still holds its Reading and Text. shown_freq, the count that rule uses, is not shown: on the known data it was 2 or 3 for words typed once, and what it counts there was not established. Mozc also learns the parts of a converted phrase, so one committed sentence gives several entries with the same Last Learned time. Status is 'decrypted', or says why the file was not read: no DPAPI key was recovered for encrypt_key.db (no TBAL secret and no password supplied, or the account's master keys absent), the opened blob was not a 32-byte password, encrypt_key.db is missing, or the key did not open history.db (bad padding or not a UserHistory protobuf); such a file gives one row with only Status and User. User is the account folder name from the path. The files are opened read only. Validated on the known data windows11_arm_japanese_ime_known_20261108 (Google Japanese Input 3.34.6260.0 on Windows 11 ARM64, typed offline in a test account; the password is in the known data's mint folder): the history decrypted through the supplied account password gave 12 entries, the same plaintext Windows' own CryptUnprotectData and AES gave inside the account; every Reading and Text matched what was typed, Last Learned matched the logged commit key to the second for the two words whose commit key was logged, and a word committed in two separate sessions had Times Learned 2. The ARSO (TBAL) route, Description and Removed were not exercised: no entry on the known data had a description or was removed, and Description held an empty value and Removed was blank on all rows; Status was 'decrypted' and User held one value on all rows. Not covered: macOS (the password is kept in the Keychain) and Linux (~/.mozc) builds, and segment.db, boundary.db and cform.db, which keep only 64-bit fingerprints of the text with a time and a small value (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/storage/lru_storage.cc#L75-L95), not the text.",
        "paths": (
            '*/AppData/LocalLow/Google/Google Japanese Input/history.db',
            '*/AppData/LocalLow/Google/Google Japanese Input/encrypt_key.db',
            '*/AppData/LocalLow/Mozc/history.db',
            '*/AppData/LocalLow/Mozc/encrypt_key.db',
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Users/*/AppData/Roaming/Microsoft/Protect/*/*',
        ),
        "output_types": "standard",
        "artifact_icon": "type",
        "sample_data": {
            "windows11_arm_japanese_ime_known_20261108": "Windows 11 build 26200 (ARM64), Google Japanese Input 3.34.6260.0 | 12 rows (with --windows-user-password)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no Google Japanese Input history.db; only the hives and DPAPI master keys match)",
        },
    },
    "googleJapaneseInputUserDictionary": {
        "name": "Google Japanese Input User Dictionary",
        "description": "Entries in Google Japanese Input (Mozc) user dictionaries on Windows: the reading, the word, its part of speech and the comment.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-08",
        "last_update_date": "2026-11-08",
        "requirements": "none",
        "category": "Japanese IME",
        "notes": "Reads user_dictionary.db in the Google Japanese Input folder under AppData\\LocalLow\\Google (and the open-source build's AppData\\LocalLow\\Mozc), a plain serialized UserDictionaryStorage protobuf (https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/dictionary/user_dictionary_util.cc#L55, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/client/user_dictionary/user_dictionary_storage.cc#L106-L134, https://github.com/google/mozc/blob/c4ed4683fb400b240e81d0a3895d024e3e21325e/src/protocol/user_dictionary_storage.proto). One row per entry of each dictionary. Dictionary is the dictionary's name; Reading, Word and Comment are the entry's key, value and comment; Part of Speech is the entry's pos, shown as the proto's enum name with the Japanese label from the proto's comment, and NOUN when the field is absent, the proto's default; Locale is shown as stored. The store keeps no time for an entry, so none is shown. User is the account folder name from the path. The file is opened read only. Validated on the known data windows11_arm_japanese_ime_known_20261108 (Google Japanese Input 3.34.6260.0 on Windows 11 ARM64): the one word added with Google Japanese Input's own dictionary tool showed with its reading, word, comment and part of speech, and Locale held an empty value; every column held one value there, as the known data has one entry. Words imported from other IMEs and dictionaries synced from other devices were not exercised.",
        "paths": (
            '*/AppData/LocalLow/Google/Google Japanese Input/user_dictionary.db',
            '*/AppData/LocalLow/Mozc/user_dictionary.db',
        ),
        "output_types": "standard",
        "artifact_icon": "book",
        "sample_data": {
            "windows11_arm_japanese_ime_known_20261108": "Windows 11 build 26200 (ARM64), Google Japanese Input 3.34.6260.0 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
        },
    },
}

import hashlib
from datetime import datetime, timezone

from Crypto.Cipher import AES

from scripts.chromium.windows_oscrypt import recover_os_keys
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import user_from_path
from scripts.vendor import dpapiprobe

_LABEL = 'Google Japanese Input History'
_SALT_SIZE = 32          # storage/encrypted_string_storage.cc
_PASSWORD_SIZE = 32      # base/password_manager.cc

# UserDictionary.PosType names and the Japanese labels in the proto's comments.
_POS = {
    0: 'NO_POS (品詞なし)', 1: 'NOUN (名詞)', 2: 'ABBREVIATION (短縮よみ)', 3: 'SUGGESTION_ONLY (サジェストのみ)',
    4: 'PROPER_NOUN (固有名詞)', 5: 'PERSONAL_NAME (人名)', 6: 'FAMILY_NAME (姓)', 7: 'FIRST_NAME (名)',
    8: 'ORGANIZATION_NAME (組織)', 9: 'PLACE_NAME (地名)', 10: 'SA_IRREGULAR_CONJUGATION_NOUN (名詞サ変)',
    11: 'ADJECTIVE_VERBAL_NOUN (名詞形動)', 12: 'NUMBER (数)', 13: 'ALPHABET (アルファベット)',
    14: 'SYMBOL (記号)', 15: 'EMOTICON (顔文字)', 16: 'ADVERB (副詞)', 17: 'PRENOUN_ADJECTIVAL (連体詞)',
    18: 'CONJUNCTION (接続詞)', 19: 'INTERJECTION (感動詞)', 20: 'PREFIX (接頭語)',
    21: 'COUNTER_SUFFIX (助数詞)', 22: 'GENERIC_SUFFIX (接尾一般)', 23: 'PERSON_NAME_SUFFIX (接尾人名)',
    24: 'PLACE_NAME_SUFFIX (接尾地名)', 25: 'WA_GROUP1_VERB (動詞ワ行五段)', 26: 'KA_GROUP1_VERB (動詞カ行五段)',
    27: 'SA_GROUP1_VERB (動詞サ行五段)', 28: 'TA_GROUP1_VERB (動詞タ行五段)', 29: 'NA_GROUP1_VERB (動詞ナ行五段)',
    30: 'MA_GROUP1_VERB (動詞マ行五段)', 31: 'RA_GROUP1_VERB (動詞ラ行五段)', 32: 'GA_GROUP1_VERB (動詞ガ行五段)',
    33: 'BA_GROUP1_VERB (動詞バ行五段)', 34: 'HA_GROUP1_VERB (動詞ハ行四段)', 35: 'GROUP2_VERB (動詞一段)',
    36: 'KURU_GROUP3_VERB (動詞カ変)', 37: 'SURU_GROUP3_VERB (動詞サ変)', 38: 'ZURU_GROUP3_VERB (動詞ザ変)',
    39: 'RU_GROUP3_VERB (動詞ラ変)', 40: 'ADJECTIVE (形容詞)', 41: 'SENTENCE_ENDING_PARTICLE (終助詞)',
    42: 'PUNCTUATION (句読点)', 43: 'FREE_STANDING_WORD (独立語)', 44: 'SUPPRESSION_WORD (抑制単語)',
}


class ProtoError(ValueError):
    """The bytes are not a well-formed protobuf message."""


def _varint(data, pos):
    result = shift = 0
    while True:
        if pos >= len(data) or shift > 63:
            raise ProtoError('truncated varint')
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, pos


def proto_fields(data):
    """Every (field number, wire type, value) of a protobuf message, in order.

    Varints come back as ints, length-delimited fields as bytes, fixed fields as bytes.
    """
    pos, out = 0, []
    while pos < len(data):
        key, pos = _varint(data, pos)
        number, wire = key >> 3, key & 7
        if number == 0:
            raise ProtoError('field number 0')
        if wire == 0:
            value, pos = _varint(data, pos)
        elif wire == 1:
            value, pos = data[pos:pos + 8], pos + 8
        elif wire == 5:
            value, pos = data[pos:pos + 4], pos + 4
        elif wire == 2:
            size, pos = _varint(data, pos)
            value, pos = data[pos:pos + size], pos + size
        else:
            raise ProtoError(f'unsupported wire type {wire}')
        if pos > len(data):
            raise ProtoError('field runs past the end')
        out.append((number, wire, value))
    return out


def _text(raw):
    return bytes(raw).decode('utf-8', 'replace')


def derive_key(password, salt):
    """Encryptor::Key::DeriveFromPassword: SHA-1 ipad/opad expansion, first 32 bytes."""
    digest = hashlib.sha1(password + salt).digest()
    ipad = bytes(0x36 ^ b for b in digest) + b'\x36' * (64 - len(digest))
    opad = bytes(0x5C ^ b for b in digest) + b'\x5c' * (64 - len(digest))
    return (hashlib.sha1(ipad).digest() + hashlib.sha1(opad).digest())[:32]


def decrypt_history(data, password):
    """The plaintext UserHistory bytes, or None when the key does not open the file."""
    if len(data) < _SALT_SIZE + 16 or (len(data) - _SALT_SIZE) % 16:
        return None
    salt, body = data[:_SALT_SIZE], data[_SALT_SIZE:]
    clear = AES.new(derive_key(password, salt), AES.MODE_CBC, b'\x00' * 16).decrypt(body)
    pad = clear[-1]
    if not 0 < pad <= 16 or clear[-pad:] != bytes([pad]) * pad or len(clear) <= pad:
        return None
    return clear[:-pad]


def parse_history(plain):
    """UserHistory entries (field 6) as dicts, in stored order."""
    entries = []
    for number, wire, value in proto_fields(plain):
        if number != 6 or wire != 2:
            continue
        entry = {'key': '', 'value': '', 'description': '', 'suggestion_freq': 0,
                 'shown_freq': 0, 'last_access_time': 0, 'removed': False}
        for field, field_wire, field_value in proto_fields(value):
            if field_wire == 2 and field in (1, 2, 6):
                entry[{1: 'key', 2: 'value', 6: 'description'}[field]] = _text(field_value)
            elif field_wire == 0 and field == 3:
                entry['suggestion_freq'] = field_value
            elif field_wire == 0 and field == 22:
                entry['shown_freq'] = field_value
            elif field_wire == 0 and field == 4:
                entry['last_access_time'] = field_value
            elif field_wire == 0 and field == 8:
                entry['removed'] = bool(field_value)
        entries.append(entry)
    return entries


def parse_user_dictionary(data):
    """(dictionary name, reading, word, part of speech, comment, locale) per entry."""
    rows = []
    for number, wire, value in proto_fields(data):
        if number != 2 or wire != 2:
            continue
        name, entries = '', []
        for field, field_wire, field_value in proto_fields(value):
            if field == 3 and field_wire == 2:
                name = _text(field_value)
            elif field == 4 and field_wire == 2:
                entries.append(field_value)
        for raw in entries:
            entry = {1: '', 2: '', 4: '', 12: ''}
            pos = 1
            for field, field_wire, field_value in proto_fields(raw):
                if field_wire == 2 and field in entry:
                    entry[field] = _text(field_value)
                elif field_wire == 0 and field == 5:
                    pos = field_value
            rows.append((name, entry[1], entry[2], _POS.get(pos, f'unknown ({pos})'), entry[4], entry[12]))
    return rows


def _unix(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc) if seconds else ''


def _folder(path):
    return str(path).replace('\\', '/').rsplit('/', 1)[0]


@artifact_processor
def googleJapaneseInputHistory(context):
    data_headers = (('Last Learned (UTC)', 'datetime'), 'Reading', 'Text', 'Description', 'Times Learned',
                    'Removed', 'Status', 'User')
    data_list = []
    histories, keys = [], {}
    for found in context.get_files_found():
        path = str(found)
        name = path.replace('\\', '/').rsplit('/', 1)[-1]
        if name == 'history.db':
            histories.append(path)
        elif name == 'encrypt_key.db':
            keys[_folder(path)] = path
    if not histories:
        return data_headers, data_list, ''

    pool, _os_keys = recover_os_keys(context, _LABEL)
    sources = []
    for path in sorted(histories, key=context.get_relative_path):
        relative = context.get_relative_path(path)
        user = user_from_path(relative)
        sources.append(path)
        with open(path, 'rb') as handle:
            data = handle.read()
        key_path = keys.get(_folder(path))
        if key_path is None:
            data_list.append(('', '', '', '', '', '', 'not decrypted: encrypt_key.db not found', user))
            continue
        with open(key_path, 'rb') as handle:
            blob_bytes = handle.read()
        password = None
        try:
            blob = dpapiprobe.DpapiBlob(blob_bytes)
            master_key = pool.get_key(blob.mk_guid)
            password = blob.decrypt(master_key) if master_key else None
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read the DPAPI blob in {context.get_relative_path(key_path)}: '
                    f'{type(ex).__name__}')
        if not password:
            data_list.append(('', '', '', '', '', '',
                              'not decrypted: no DPAPI key recovered for encrypt_key.db', user))
            continue
        if len(password) != _PASSWORD_SIZE:
            data_list.append(('', '', '', '', '', '',
                              'not decrypted: encrypt_key.db did not hold a 32-byte password', user))
            continue
        plain = decrypt_history(data, password)
        entries = None
        if plain is not None:
            try:
                entries = parse_history(plain)
            except ProtoError as ex:
                logfunc(f'{_LABEL}: {relative} decrypted but did not parse as UserHistory: {ex}')
        if entries is None:
            data_list.append(('', '', '', '', '', '', 'not decrypted: the key did not open history.db',
                              user))
            continue
        for entry in entries:
            data_list.append((_unix(entry['last_access_time']), entry['key'], entry['value'],
                              entry['description'], entry['suggestion_freq'],
                              'Yes' if entry['removed'] else '', 'decrypted', user))
        logfunc(f'{_LABEL}: {relative}: {len(entries)} entries')
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def googleJapaneseInputUserDictionary(context):
    data_headers = ('Dictionary', 'Reading', 'Word', 'Part of Speech', 'Comment', 'Locale', 'User')
    data_list = []
    sources = []
    for found in sorted((str(f) for f in context.get_files_found()), key=context.get_relative_path):
        if not found.replace('\\', '/').endswith('/user_dictionary.db'):
            continue
        relative = context.get_relative_path(found)
        with open(found, 'rb') as handle:
            data = handle.read()
        try:
            rows = parse_user_dictionary(data)
        except ProtoError as ex:
            logfunc(f'Google Japanese Input User Dictionary: {relative} is not a UserDictionaryStorage '
                    f'protobuf: {ex}')
            continue
        sources.append(found)
        user = user_from_path(relative)
        data_list.extend(row + (user,) for row in rows)
    return data_headers, data_list, '\n'.join(sources)
