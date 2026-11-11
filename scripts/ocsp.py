"""Read an OCSP request or response (RFC 6960) from its DER bytes, for the fields that name a certificate.

Author: @AlexisBrignoni, Claude.

Nothing here verifies a signature, follows a URL or looks anything up. What is read, with its source:

* DER. Each element is a tag byte, a length and the content (ITU-T X.690, 8.1): bits 8 and 7 of the tag give
  the class, bit 6 says constructed, bits 5 to 1 the number; a length under 0x80 is the content's size,
  and otherwise the low seven bits say how many bytes hold it. This reader takes up to four (0x81 to 0x84)
  and refuses more. An indefinite length (0x80), which DER does not allow (X.690, 10.1), and a tag number
  of 31, the multi-byte form, are refused. Every length is checked against the bytes that hold it.
* The request and response structures (RFC 6960, 4.1.1 and 4.2.1, https://www.rfc-editor.org/rfc/rfc6960):
  OCSPRequest, TBSRequest, Request and CertID; OCSPResponse, ResponseBytes, BasicOCSPResponse, ResponseData,
  ResponderID, SingleResponse, CertStatus and RevokedInfo. CertID is hashAlgorithm, issuerNameHash,
  issuerKeyHash and serialNumber.
* OCSPResponseStatus names (RFC 6960, 4.2.1) and CRLReason names (RFC 5280, 5.3.1,
  https://www.rfc-editor.org/rfc/rfc5280#section-5.3.1).
* GeneralizedTime in the form RFC 6960 (4.2.2.1) and RFC 5280 (4.1.2.5.2) require, YYYYMMDDHHMMSSZ. A
  fraction of a second, which RFC 5280 does not allow, is also read. Any other form is refused.
* An OCSP request sent with GET is the base-64 encoding of the DER request, URL-encoded, appended to the
  responder's URL after a slash (RFC 6960, Appendix A.1). Base-64 text can itself hold slashes, so
  `request_in_url` tries each slash of the URL's path as the start of the request, longest tail first, and
  keeps the first tail that is strict base-64 and reads as a whole OCSPRequest.

Not read: signatures, the certificates a response carries, and extensions (they are stepped over).
"""

import base64
import binascii
import urllib.parse
from datetime import datetime, timedelta, timezone

BASIC_RESPONSE = '1.3.6.1.5.5.7.48.1.1'            # id-pkix-ocsp-basic, RFC 6960 4.2.1

RESPONSE_STATUS = {0: 'successful', 1: 'malformedRequest', 2: 'internalError', 3: 'tryLater',
                   5: 'sigRequired', 6: 'unauthorized'}
CRL_REASON = {0: 'unspecified', 1: 'keyCompromise', 2: 'cACompromise', 3: 'affiliationChanged', 4: 'superseded',
              5: 'cessationOfOperation', 6: 'certificateHold', 8: 'removeFromCRL', 9: 'privilegeWithdrawn',
              10: 'aACompromise'}
# Hash algorithm object identifiers: SHA-1 (RFC 3279, 2.2.1, the OIW identifier) and the SHA-2 family
# (RFC 5754, 2).
HASH_NAMES = {'1.3.14.3.2.26': 'SHA-1', '2.16.840.1.101.3.4.2.1': 'SHA-256', '2.16.840.1.101.3.4.2.2': 'SHA-384',
              '2.16.840.1.101.3.4.2.3': 'SHA-512', '2.16.840.1.101.3.4.2.4': 'SHA-224'}

_UNIVERSAL, _CONTEXT = 0, 2
_INTEGER, _OCTET_STRING, _OID, _ENUMERATED, _SEQUENCE, _GENERALIZED_TIME = 2, 4, 6, 10, 16, 24


class OcspError(ValueError):
    """Bytes this reader cannot read as the structure asked for."""


class _Element:
    __slots__ = ('cls', 'constructed', 'number', 'content', 'end')

    def __init__(self, cls, constructed, number, content, end):
        self.cls, self.constructed, self.number, self.content, self.end = cls, constructed, number, content, end

    def is_a(self, cls, number):
        return self.cls == cls and self.number == number


def _element(data, at, limit):
    """The element that starts at `at` and must end by `limit`."""
    if at + 2 > limit:
        raise OcspError('an element header runs past its container')
    tag = data[at]
    number = tag & 0x1f
    if number == 0x1f:
        raise OcspError('a multi-byte tag number')
    first = data[at + 1]
    start = at + 2
    if first < 0x80:
        size = first
    elif first == 0x80:
        raise OcspError('an indefinite length')
    else:
        count = first & 0x7f
        if count > 4 or start + count > limit:
            raise OcspError('a length field this reader does not take')
        size = int.from_bytes(data[start:start + count], 'big')
        start += count
    if start + size > limit:
        raise OcspError('an element runs past its container')
    return _Element(tag >> 6, bool(tag & 0x20), number, data[start:start + size], start + size)


def _children(data):
    """The elements that fill `data` exactly."""
    out = []
    at = 0
    while at < len(data):
        element = _element(data, at, len(data))
        out.append(element)
        at = element.end
    return out


def _whole(data):
    """The one element that is all of `data`."""
    element = _element(data, 0, len(data))
    if element.end != len(data):
        raise OcspError('bytes after the outer element')
    return element


def _expect(element, cls, number, what):
    if not element.is_a(cls, number):
        raise OcspError(f'{what} is not where the structure puts it')
    return element


def _integer(element):
    if not element.content:
        raise OcspError('an empty INTEGER')
    return int.from_bytes(element.content, 'big', signed=True)


def _oid(element):
    raw = element.content
    if not raw:
        raise OcspError('an empty OBJECT IDENTIFIER')
    arcs = []
    value = 0
    for position, byte in enumerate(raw):
        value = (value << 7) | (byte & 0x7f)
        if byte & 0x80:
            if position == len(raw) - 1:
                raise OcspError('an OBJECT IDENTIFIER cut short')
            continue
        if not arcs:
            first = min(value // 40, 2)
            arcs.extend((first, value - 40 * first))
        else:
            arcs.append(value)
        value = 0
    return '.'.join(str(arc) for arc in arcs)


def _time(element):
    """A UTC datetime from a GeneralizedTime of the form YYYYMMDDHHMMSS[.f]Z."""
    try:
        text = element.content.decode('ascii')
    except UnicodeDecodeError as exc:
        raise OcspError('a GeneralizedTime that is not ASCII') from exc
    if not text.endswith('Z') or len(text) < 15 or not text[:14].isdigit():
        raise OcspError(f'a GeneralizedTime of a form not read: {text!r}')
    fraction = text[14:-1]
    micro = 0
    if fraction:
        if fraction[0] != '.' or not fraction[1:].isdigit():
            raise OcspError(f'a GeneralizedTime of a form not read: {text!r}')
        micro = int(fraction[1:7].ljust(6, '0'))
    try:
        moment = datetime.strptime(text[:14], '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise OcspError(f'a GeneralizedTime that is not a date: {text!r}') from exc
    return moment + timedelta(microseconds=micro)


def _cert_id(element):
    """{'hash_oid', 'issuer_name_hash', 'issuer_key_hash', 'serial'} of a CertID. Hashes and the serial are
    upper-case hex of the content bytes as stored (the serial keeps any leading 00 the encoding carries)."""
    _expect(element, _UNIVERSAL, _SEQUENCE, 'a CertID')
    parts = _children(element.content)
    if len(parts) != 4:
        raise OcspError(f'a CertID of {len(parts)} members')
    algorithm = _children(_expect(parts[0], _UNIVERSAL, _SEQUENCE, 'a hash algorithm').content)
    if not algorithm:
        raise OcspError('an empty hash algorithm')
    _expect(parts[1], _UNIVERSAL, _OCTET_STRING, 'an issuer name hash')
    _expect(parts[2], _UNIVERSAL, _OCTET_STRING, 'an issuer key hash')
    _expect(parts[3], _UNIVERSAL, _INTEGER, 'a serial number')
    if not parts[3].content:
        raise OcspError('an empty serial number')
    return {'hash_oid': _oid(_expect(algorithm[0], _UNIVERSAL, _OID, 'a hash algorithm identifier')),
            'issuer_name_hash': parts[1].content.hex().upper(),
            'issuer_key_hash': parts[2].content.hex().upper(),
            'serial': parts[3].content.hex().upper()}


def parse_request(data):
    """The CertIDs of an OCSPRequest, in order. Raises OcspError when `data` is not one whole request."""
    outer = _expect(_whole(data), _UNIVERSAL, _SEQUENCE, 'an OCSPRequest')
    members = _children(outer.content)
    if not members:
        raise OcspError('an empty OCSPRequest')
    tbs = _children(_expect(members[0], _UNIVERSAL, _SEQUENCE, 'a TBSRequest').content)
    at = 0
    while at < len(tbs) and tbs[at].cls == _CONTEXT and tbs[at].number in (0, 1):      # version, requestorName
        at += 1
    if at >= len(tbs):
        raise OcspError('a TBSRequest with no request list')
    requests = _children(_expect(tbs[at], _UNIVERSAL, _SEQUENCE, 'a request list').content)
    if not requests:
        raise OcspError('an empty request list')
    found = []
    for request in requests:
        parts = _children(_expect(request, _UNIVERSAL, _SEQUENCE, 'a Request').content)
        if not parts:
            raise OcspError('an empty Request')
        found.append(_cert_id(parts[0]))
    return found


def _single(element):
    parts = _children(_expect(element, _UNIVERSAL, _SEQUENCE, 'a SingleResponse').content)
    if len(parts) < 3:
        raise OcspError(f'a SingleResponse of {len(parts)} members')
    out = _cert_id(parts[0])
    status = parts[1]
    if status.cls != _CONTEXT or status.number not in (0, 1, 2):
        raise OcspError('a certificate status this reader does not know')
    out['status'] = ('good', 'revoked', 'unknown')[status.number]
    out['revocation_time'] = out['revocation_reason'] = None
    if status.number == 1:
        info = _children(status.content)
        if not info:
            raise OcspError('a revoked status with no time')
        out['revocation_time'] = _time(_expect(info[0], _UNIVERSAL, _GENERALIZED_TIME, 'a revocation time'))
        if len(info) > 1 and info[1].is_a(_CONTEXT, 0):
            out['revocation_reason'] = _integer(
                _expect(_whole(info[1].content), _UNIVERSAL, _ENUMERATED, 'a revocation reason'))
    out['this_update'] = _time(_expect(parts[2], _UNIVERSAL, _GENERALIZED_TIME, 'thisUpdate'))
    out['next_update'] = None
    if len(parts) > 3 and parts[3].is_a(_CONTEXT, 0):
        out['next_update'] = _time(_expect(_whole(parts[3].content), _UNIVERSAL, _GENERALIZED_TIME, 'nextUpdate'))
    return out


def parse_response(data):
    """{'status', 'response_type', 'produced_at', 'responder_key_hash', 'responses'} of an OCSPResponse.

    `status` is the OCSPResponseStatus number. A response with no responseBytes (any status but successful)
    has response_type None and no responses. A response type other than the basic one is named and its
    bytes are not read. `responder_key_hash` is the ResponderID's KeyHash in hex, or '' when the responder
    is identified by name. Each of `responses` is a SingleResponse: the CertID members, 'status' ('good',
    'revoked' or 'unknown'), 'revocation_time', 'revocation_reason' (the CRLReason number or None),
    'this_update' and 'next_update'. Raises OcspError when `data` is not one whole response."""
    outer = _expect(_whole(data), _UNIVERSAL, _SEQUENCE, 'an OCSPResponse')
    members = _children(outer.content)
    if not members:
        raise OcspError('an empty OCSPResponse')
    out = {'status': _integer(_expect(members[0], _UNIVERSAL, _ENUMERATED, 'a response status')),
           'response_type': None, 'produced_at': None, 'responder_key_hash': '', 'responses': []}
    if len(members) == 1:
        return out
    wrapper = _children(_expect(_whole(_expect(members[1], _CONTEXT, 0, 'responseBytes').content),
                                _UNIVERSAL, _SEQUENCE, 'ResponseBytes').content)
    if len(wrapper) != 2:
        raise OcspError(f'ResponseBytes of {len(wrapper)} members')
    out['response_type'] = _oid(_expect(wrapper[0], _UNIVERSAL, _OID, 'a response type'))
    if out['response_type'] != BASIC_RESPONSE:
        return out
    basic = _children(_expect(_whole(_expect(wrapper[1], _UNIVERSAL, _OCTET_STRING, 'a response').content),
                              _UNIVERSAL, _SEQUENCE, 'a BasicOCSPResponse').content)
    if not basic:
        raise OcspError('an empty BasicOCSPResponse')
    tbs = _children(_expect(basic[0], _UNIVERSAL, _SEQUENCE, 'ResponseData').content)
    at = 0
    if tbs and tbs[0].is_a(_CONTEXT, 0):                                               # version
        at = 1
    if at + 3 > len(tbs):
        raise OcspError('ResponseData cut short')
    responder = tbs[at]
    if responder.cls != _CONTEXT or responder.number not in (1, 2):
        raise OcspError('a responder ID this reader does not know')
    if responder.number == 2:
        out['responder_key_hash'] = _expect(_whole(responder.content), _UNIVERSAL, _OCTET_STRING,
                                            'a responder key hash').content.hex().upper()
    out['produced_at'] = _time(_expect(tbs[at + 1], _UNIVERSAL, _GENERALIZED_TIME, 'producedAt'))
    singles = _children(_expect(tbs[at + 2], _UNIVERSAL, _SEQUENCE, 'the responses').content)
    out['responses'] = [_single(single) for single in singles]
    return out


def request_in_url(url):
    """The CertIDs of the OCSP GET request a URL carries, or None when it carries none."""
    try:
        path = urllib.parse.urlsplit(url).path
    except ValueError:
        return None
    for at, char in enumerate(path):
        if char != '/':
            continue
        tail = urllib.parse.unquote(path[at + 1:])
        if not tail:
            continue
        try:
            raw = base64.b64decode(tail, validate=True)
        except (binascii.Error, ValueError):
            continue
        try:
            return parse_request(raw)
        except OcspError:
            continue
    return None
