"""Tests for scripts/ocsp.py and the CryptnetUrlCache OCSP artifact, on DER built here from RFC 6960.

Every value is made up. The builder below writes tag, length and content by hand, so it shares no code with
the reader.
"""

import base64
import os
import struct
import sys
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from scripts import ocsp  # noqa: E402  pylint: disable=wrong-import-position
from scripts.artifacts import windowsCryptnetUrlCache as cache  # noqa: E402  pylint: disable=wrong-import-position

SHA1 = bytes.fromhex('2b0e03021a')                       # 1.3.14.3.2.26
SHA256 = bytes.fromhex('608648016503040201')             # 2.16.840.1.101.3.4.2.1
BASIC = bytes.fromhex('2b0601050507300101')              # 1.3.6.1.5.5.7.48.1.1
NAME_HASH = bytes(range(1, 21))
KEY_HASH = bytes(range(101, 121))
RESPONDER = bytes(range(201, 221))


def tlv(tag, content):
    size = len(content)
    if size < 0x80:
        return bytes([tag, size]) + content
    raw = size.to_bytes((size.bit_length() + 7) // 8, 'big')
    return bytes([tag, 0x80 | len(raw)]) + raw + content


def seq(*parts):
    return tlv(0x30, b''.join(parts))


def cert_id(serial, algorithm=SHA1):
    return seq(seq(tlv(0x06, algorithm), tlv(0x05, b'')), tlv(0x04, NAME_HASH), tlv(0x04, KEY_HASH),
               tlv(0x02, serial))


def gtime(text):
    return tlv(0x18, text.encode('ascii'))


def request(*serials, version=False):
    requests = seq(*(seq(cert_id(serial)) for serial in serials))
    head = tlv(0xa0, tlv(0x02, b'\x00')) if version else b''
    return seq(seq(head, requests))


def single(serial, status, this='20260102030405Z', nxt='20260109030405Z', algorithm=SHA1):
    parts = [cert_id(serial, algorithm), status, gtime(this)]
    if nxt:
        parts.append(tlv(0xa0, gtime(nxt)))
    return seq(*parts)


GOOD = tlv(0x80, b'')
UNKNOWN = tlv(0x82, b'')


def revoked(when, reason=None):
    body = gtime(when)
    if reason is not None:
        body += tlv(0xa0, tlv(0x0a, bytes([reason])))
    return tlv(0xa1, body)


def response(*singles, by_name=False, version=False, produced='20260102030400Z'):
    responder = tlv(0xa1, seq()) if by_name else tlv(0xa2, tlv(0x04, RESPONDER))
    head = tlv(0xa0, tlv(0x02, b'\x00')) if version else b''
    data = seq(head, responder, gtime(produced), seq(*singles))
    basic = seq(data, seq(tlv(0x06, SHA256)), tlv(0x03, b'\x00' + b'\x55' * 16))
    return seq(tlv(0x0a, b'\x00'), tlv(0xa0, seq(tlv(0x06, BASIC), tlv(0x04, basic))))


def utc(*values):
    return datetime(*values, tzinfo=timezone.utc)


class RequestTest(unittest.TestCase):

    def test_cert_ids(self):
        found = ocsp.parse_request(request(b'\x00\xab\xcd', b'\x7f', version=True))
        self.assertEqual(found, [
            {'hash_oid': '1.3.14.3.2.26', 'issuer_name_hash': NAME_HASH.hex().upper(),
             'issuer_key_hash': KEY_HASH.hex().upper(), 'serial': '00ABCD'},
            {'hash_oid': '1.3.14.3.2.26', 'issuer_name_hash': NAME_HASH.hex().upper(),
             'issuer_key_hash': KEY_HASH.hex().upper(), 'serial': '7F'}])

    def test_refusals(self):
        good = request(b'\x01')
        for bad in (good + b'\x00', good[:-1], b'', b'\x30\x80\x00\x00', seq(seq(seq())), seq(seq(seq(seq(seq()))))):
            with self.assertRaises(ocsp.OcspError):
                ocsp.parse_request(bad)
        with self.assertRaises(ocsp.OcspError):
            ocsp.parse_request(bytes([0x3f, 0x01, 0x00]))           # a multi-byte tag number

    def test_request_in_url(self):
        # serials chosen so the base-64 text holds a slash and a plus sign
        raw = next(candidate for candidate in (request(struct.pack('>I', 0x03ff0000 + value))
                                               for value in range(4096))
                   if {'/', '+'} <= set(base64.b64encode(candidate).decode('ascii')))
        text = base64.b64encode(raw).decode('ascii')
        self.assertIn('/', text)
        self.assertIn('+', text)
        expected = ocsp.parse_request(raw)
        plain = 'http://ocsp.fixture.test/path/' + text
        quoted = 'http://ocsp.fixture.test/path/' + urllib.parse.quote(text, safe='')
        self.assertEqual(ocsp.request_in_url(plain), expected)
        self.assertEqual(ocsp.request_in_url(quoted), expected)
        self.assertIsNone(ocsp.request_in_url('http://crl.fixture.test/root.crl'))
        self.assertIsNone(ocsp.request_in_url('http://ocsp.fixture.test/' + text[:-8]))
        self.assertIsNone(ocsp.request_in_url('http://[bad'))


class ResponseTest(unittest.TestCase):

    def test_good_revoked_unknown(self):
        data = response(single(b'\x01', GOOD),
                        single(b'\x02', revoked('20251231235959Z', 1), nxt=None, algorithm=SHA256),
                        single(b'\x03', revoked('20251231235959.25Z')),
                        single(b'\x04', UNKNOWN), version=True)
        parsed = ocsp.parse_response(data)
        self.assertEqual((parsed['status'], parsed['response_type']), (0, ocsp.BASIC_RESPONSE))
        self.assertEqual(parsed['produced_at'], utc(2026, 1, 2, 3, 4, 0))
        self.assertEqual(parsed['responder_key_hash'], RESPONDER.hex().upper())
        self.assertEqual(len(parsed['responses']), 4)
        one, two, three, four = (parsed['responses'][index] for index in range(4))
        self.assertEqual((one['serial'], one['status'], one['this_update'], one['next_update'],
                          one['revocation_time'], one['revocation_reason']),
                         ('01', 'good', utc(2026, 1, 2, 3, 4, 5), utc(2026, 1, 9, 3, 4, 5), None, None))
        self.assertEqual((two['status'], two['revocation_time'], two['revocation_reason'], two['next_update'],
                          two['hash_oid']),
                         ('revoked', utc(2025, 12, 31, 23, 59, 59), 1, None, '2.16.840.1.101.3.4.2.1'))
        self.assertEqual(ocsp.CRL_REASON[two['revocation_reason']], 'keyCompromise')
        self.assertEqual((three['revocation_time'], three['revocation_reason']),
                         (utc(2025, 12, 31, 23, 59, 59, 250000), None))
        self.assertEqual(four['status'], 'unknown')

    def test_responder_by_name_and_no_bytes(self):
        parsed = ocsp.parse_response(response(single(b'\x01', GOOD), by_name=True))
        self.assertEqual(parsed['responder_key_hash'], '')
        self.assertEqual(len(parsed['responses']), 1)
        refused = ocsp.parse_response(seq(tlv(0x0a, b'\x06')))
        self.assertEqual((refused['status'], refused['response_type'], refused['responses']), (6, None, []))
        self.assertEqual(ocsp.RESPONSE_STATUS[6], 'unauthorized')
        other = ocsp.parse_response(seq(tlv(0x0a, b'\x00'), tlv(0xa0, seq(tlv(0x06, SHA256), tlv(0x04, b'xx')))))
        self.assertEqual((other['response_type'], other['responses']), ('2.16.840.1.101.3.4.2.1', []))

    def test_refusals(self):
        good = response(single(b'\x01', GOOD))
        for bad in (good + b'\x00', good[:-3], b'', seq(), request(b'\x01'),
                    response(single(b'\x01', GOOD, this='260102030405Z')),
                    response(single(b'\x01', GOOD, this='20260102030405+0100')),
                    response(single(b'\x01', GOOD, this='20261302030405Z')),
                    response(single(b'\x01', tlv(0x83, b'')))):
            with self.assertRaises(ocsp.OcspError):
                ocsp.parse_response(bad)

    def test_long_lengths(self):
        many = [single(struct.pack('>H', 0x1000 + index), GOOD) for index in range(40)]
        parsed = ocsp.parse_response(response(*many))
        self.assertEqual([r['serial'] for r in parsed['responses']][::39], ['1000', '1027'])


def _metadata(url, downloaded=133_000_000_000_000_000):
    name = url.encode('utf-16-le') + b'\x00\x00'
    header = bytearray(116)
    struct.pack_into('<I', header, 0, 112)
    struct.pack_into('<I', header, 12, len(name))
    struct.pack_into('<Q', header, 16, downloaded)
    return bytes(header) + name


class _Context:

    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')


class ArtifactTest(unittest.TestCase):

    def test_named_in(self):
        asked = request(b'\x01')
        url = 'http://ocsp.fixture.test/' + urllib.parse.quote(base64.b64encode(asked).decode('ascii'), safe='')
        both = cache.ocsp_rows(url, response(single(b'\x01', GOOD), single(b'\x09', GOOD)))
        self.assertEqual([(named, cert['serial']) for named, cert, _single, _resp in both],
                         [('request and response', '01'), ('response', '09')])
        other = cache.ocsp_rows(url, response(single(b'\x09', GOOD)))
        self.assertEqual([(named, cert['serial'], one is None) for named, cert, one, _resp in other],
                         [('response', '09', False), ('request', '01', True)])
        alone = cache.ocsp_rows(url, b'')
        self.assertEqual([(named, one, resp) for named, _cert, one, resp in alone], [('request', None, None)])
        self.assertEqual(cache.ocsp_rows(url, b'MSCF not a response')[0][3], None)
        self.assertEqual(cache.ocsp_rows('http://crl.fixture.test/a.crl', b'\x30\x82'), [])

    def test_artifact_rows(self):
        asked = request(b'\x00\xab')
        url = 'http://ocsp.fixture.test/' + urllib.parse.quote(base64.b64encode(asked).decode('ascii'), safe='')
        entries = {'AAAA': (url, response(single(b'\x00\xab', revoked('20251231235959Z', 4)))),
                   'BBBB': (url, seq(tlv(0x0a, b'\x06'))),
                   'CCCC': ('http://crl.fixture.test/a.crl', b'\x30\x03\x02\x01\x01'),
                   'DDDD': (url, None)}
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, 'Users', 'fixture', 'AppData', 'LocalLow', 'Microsoft', 'CryptnetUrlCache')
            os.makedirs(os.path.join(base, 'MetaData'))
            os.makedirs(os.path.join(base, 'Content'))
            files = []
            for name, (address, content) in entries.items():
                files.append(os.path.join(base, 'MetaData', name))
                with open(files[-1], 'wb') as handle:
                    handle.write(_metadata(address))
                if content is not None:
                    files.append(os.path.join(base, 'Content', name))
                    with open(files[-1], 'wb') as handle:
                        handle.write(content)
            headers, rows, sources = cache.windowsCryptnetUrlCacheOcsp.__wrapped__(_Context(root, files))
        self.assertEqual(len(headers), 17)
        self.assertEqual([row[16] for row in rows], ['AAAA', 'BBBB', 'DDDD'])
        self.assertEqual(len(sources.split('\n')), 5)
        downloaded = utc(2022, 6, 18, 4, 26, 40)
        self.assertEqual(rows[0], (
            downloaded, utc(2026, 1, 2, 3, 4, 0), utc(2026, 1, 2, 3, 4, 5), utc(2026, 1, 9, 3, 4, 5),
            utc(2025, 12, 31, 23, 59, 59), '00AB', 'revoked', 'superseded', NAME_HASH.hex().upper(),
            KEY_HASH.hex().upper(), 'SHA-1', 'request and response', 'successful', RESPONDER.hex().upper(),
            'ocsp.fixture.test', 'Users/fixture', 'AAAA'))
        self.assertEqual(rows[1][1:8], ('', '', '', '', '00AB', '', ''))
        self.assertEqual(rows[1][11:14], ('request', 'unauthorized', ''))
        self.assertEqual(rows[2][11:14], ('request', '', ''))


if __name__ == '__main__':
    unittest.main()
