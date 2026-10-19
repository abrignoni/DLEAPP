"""WhatsApp Web helper cases; every value is built by hand for the test."""

import base64
import hashlib
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position,protected-access
from scripts import whatsapp_web as ww
from scripts.artifacts import whatsappWeb as art


def snappy_literal(data):
    """A raw Snappy block made only of literals, from the format description."""
    out, size = bytearray(), len(data)
    while True:
        byte = size & 0x7F
        size >>= 7
        out.append(byte | (0x80 if size else 0))
        if not size:
            break
    for start in range(0, len(data), 60):
        chunk = data[start:start + 60]
        out.append((len(chunk) - 1) << 2)
        out += chunk
    return bytes(out)


def framed(data):
    """Snappy framing: stream identifier, one compressed chunk, one uncompressed chunk."""
    half = len(data) // 2
    compressed = b'\x00\x00\x00\x00' + snappy_literal(data[:half])
    plain = b'\x00\x00\x00\x00' + data[half:]
    out = b'\xff\x06\x00\x00sNaPpY'
    out += b'\x00' + len(compressed).to_bytes(3, 'little') + compressed
    out += b'\x01' + len(plain).to_bytes(3, 'little') + plain
    return out


class HelperTest(unittest.TestCase):

    def test_message_key_parts(self):
        self.assertEqual(art._key_parts('true_123@c.us_3EB0ABC_out'), (True, '123@c.us'))
        self.assertEqual(art._key_parts('false_120363@g.us_ABC_456@lid'), (False, '120363@g.us'))
        self.assertEqual(art._key_parts('garbage'), (None, ''))
        self.assertEqual(art._key_parts(None), (None, ''))

    def test_hash_and_device_ids(self):
        digest = hashlib.sha256(b'file').digest()
        self.assertEqual(art._hex_sha256(base64.b64encode(digest).decode()), digest.hex())
        self.assertEqual(art._hex_sha256('not base64!'), '')
        self.assertEqual(art._hex_sha256(base64.b64encode(b'short').decode()), '')
        self.assertEqual(art._user('15551234567:12@c.us'), '15551234567@c.us')
        self.assertEqual(art._user('99887766:3@lid'), '99887766@lid')
        self.assertEqual(art._user(None), '')

    def test_firefox_markers_become_python_values(self):
        value = {'a': {'$undefined': True}, 'b': {'$typedarray': 'Uint8Array', 'hex': '0102'},
                 'c': [{'$arraybuffer': 'ff'}], 'd': {'e': 1}}
        self.assertEqual(ww._plain_firefox(value), {'b': b'\x01\x02', 'c': [b'\xff'], 'd': {'e': 1}})

    def test_snappy_framing(self):
        data = bytes(range(200))
        self.assertEqual(ww._unframe_snappy(framed(data)), data)
        with self.assertRaises(ValueError):
            ww._unframe_snappy(framed(data)[:-5])


class FirefoxMediaTest(unittest.TestCase):

    def test_only_bodies_that_hash_to_their_key_are_kept(self):
        good, bad = b'\xff\xd8\xff' + b'good jpeg', b'\xff\xd8\xff' + b'other bytes'
        good_key = base64.b64encode(hashlib.sha256(good).digest()).decode()
        wrong_key = base64.b64encode(hashlib.sha256(b'something else').digest()).decode()
        with tempfile.TemporaryDirectory() as root:
            cache = os.path.join(root, 'cache')
            os.makedirs(os.path.join(cache, 'morgue', '17'))
            db = sqlite3.connect(os.path.join(cache, 'caches.sqlite'))
            db.execute('CREATE TABLE entries (request_url_no_query TEXT, response_body_id TEXT)')
            entries = (('{good}', good_key, good), ('{bad}', wrong_key, bad))
            for body_id, key, body in entries:
                db.execute('INSERT INTO entries VALUES (?, ?)', (ww.MEDIA_PREFIX + key.replace('/', '%2F'), body_id))
                with open(os.path.join(cache, 'morgue', '17', body_id + '.final'), 'wb') as handle:
                    handle.write(framed(body))
            db.execute('INSERT INTO entries VALUES (?, ?)', ('https://web.whatsapp.com/sw.js', '{sw}'))
            db.commit()
            db.close()
            profile = ww.Profile('Firefox', root, root)
            found = ww.media(profile)
        self.assertEqual(list(found), [good_key])
        self.assertEqual(found[good_key][1], good)


if __name__ == '__main__':
    unittest.main()
