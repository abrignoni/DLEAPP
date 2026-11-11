"""CryptnetUrlCache parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

Each Windows profile can hold AppData/LocalLow/Microsoft/CryptnetUrlCache with two
folders, MetaData and Content, holding a file of the same name for each cached URL.
The MetaData file records the URL, two times, an E-Tag and a size in the layout
AbdulRhman Alfaifi's analysis describes; the Content file holds what was fetched.
This reads every MetaData file, pairs it with the Content file of the same name in the
same cache folder, and reports the Content file's size, SHA-256 and first bytes.
"""

import hashlib
import os
import struct

from urllib.parse import urlsplit

from scripts import ocsp
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import filetime_utc

_CACHE_FOLDER = '/appdata/locallow/microsoft/cryptneturlcache/'
_HEADER_LEN = 116

__artifacts_v2__ = {
    "windowsCryptnetUrlCache": {
        "name": "CryptnetUrlCache",
        "description": "URLs recorded in the CryptnetUrlCache MetaData files of each Windows "
                       "profile, with the recorded times, E-Tag and size, and the size, SHA-256 "
                       "and first bytes of the Content file of the same name.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads every file in the MetaData folder of "
                 "AppData/LocalLow/Microsoft/CryptnetUrlCache in any profile the declared path "
                 "reaches, which includes Windows/System32/config/systemprofile, "
                 "Windows/SysWOW64/config/systemprofile and the LocalService and NetworkService "
                 "folders under Windows/ServiceProfiles; Velociraptor's Windows.Forensics.CertUtil "
                 "artifact reads the cache in Users and in the systemprofile folders "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/CertUtil.yaml#L40-L43). "
                 "Phill Moore found that running certutil -urlcache -split -f wrote a Content file and "
                 "a MetaData file of the same name there (Reference: Phill Moore, 'Certutil download "
                 "artefacts', https://thinkdfir.com/2020/07/30/certutil-download-artefacts/). The "
                 "MetaData fields follow AbdulRhman Alfaifi's analysis and parser (Reference: "
                 "AbdulRhman Alfaifi, 'Certutil Artifacts Analysis', "
                 "https://u0041.co/posts/articals/certutil-artifacts-analysis/; "
                 "https://github.com/AbdulRhmanAlfaifi/CryptnetURLCacheParser/blob/5dc1ca6e8c26735923cdc110fed18c310a405b92/CryptnetUrlCacheParser.py#L1-L14, "
                 "https://github.com/AbdulRhmanAlfaifi/CryptnetURLCacheParser/blob/5dc1ca6e8c26735923cdc110fed18c310a405b92/CryptnetUrlCacheParser.py#L68-L73). "
                 "Last Downloaded (UTC) is the FILETIME at offset 0x10, which the analysis describes "
                 "as the last time the file was downloaded, and Last-Modified (UTC) the FILETIME at "
                 "0x58, which it describes as the Last-Modified header of the response; a zero time is "
                 "shown blank, and Last-Modified was zero on 29 of the 187 tested files. File Size is "
                 "the 32-bit value at 0x70, the downloaded file's size by the analysis. URL and E-Tag "
                 "are the UTF-16LE strings after the 116-byte header, whose sizes sit at 0x0C and "
                 "0x64, shown without their terminating NUL; the analysis describes the second as the "
                 "response's E-Tag header, and it is shown as stored, quotation marks included. On the "
                 "tested images every MetaData file's length was exactly 116 bytes plus the two string "
                 "sizes, every URL ended in a NUL, and File Size equalled the size of the Content file "
                 "of the same name on all 187. Last Downloaded matched that Content file's "
                 "modification time within two seconds on 68 of the 187, so what the time records "
                 "beyond the analysis's description was not established. Cache File is the name the "
                 "two files share. The analysis gives that name as the MD5 of the URL in UTF-16LE: on "
                 "the tested images that held for all 62 names without an underscore, and for none of "
                 "the 125 names with one, not even for the part before the underscore; on all 125 the "
                 "part after the underscore was that MD5, and how the part before it is derived was not "
                 "established. Content Size, Content SHA-256 and Content Header (hex) "
                 "are the size, SHA-256 and first eight bytes of the Content file of the same name in "
                 "the same cache folder, blank when there is none; every tested MetaData file had one. "
                 "Of the 187 Content files 147 began with 3082, 20 with MSCF (4D534346) and 3 with "
                 "3003, 17 were empty, and none began with MZ (4D5A), the header Velociraptor's "
                 "artifact checks for before it reads an executable's version information "
                 "(https://github.com/Velocidex/velociraptor/blob/2871c23d0bf6714fc0fe21c9db02a6a1e9364fb4/artifacts/definitions/Windows/Forensics/CertUtil.yaml#L109-L114). "
                 "Profile Folder is the part of the path before AppData, and with Cache File it "
                 "identifies the MetaData file. On af_case2_win10 there were 11 rows, 6 in "
                 "Users/IEUser and 5 in the System32 systemprofile; on lonewolf_win10 92, 5 of them "
                 "under Windows/ServiceProfiles; on pc_mus_001_win11 42, 2 of them under "
                 "Windows/ServiceProfiles; and on szechuan_win10 42, 1 of them under "
                 "Windows/ServiceProfiles. The 187 URLs all used http and named 37 hosts, most often "
                 "ocsp.digicert.com (73) and ctldl.windowsupdate.com (37). Values not reported include "
                 "the bytes the analysis leaves unknown, at 0x00 to 0x0B, 0x18 to 0x57, 0x60 to 0x63 "
                 "and 0x68 to 0x6F; the first 32-bit value was 112 in every tested file.",
        "paths": ('*/AppData/LocalLow/Microsoft/CryptnetUrlCache/*',),
        "output_types": ["standard"],
        "artifact_icon": "certificate",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 11 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 92 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 42 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 42 rows",
        },
    },
    "windowsCryptnetUrlCacheOcsp": {
        "name": "CryptnetUrlCache OCSP Certificate Checks",
        "description": "Certificates named by the OCSP requests and responses in the CryptnetUrlCache of each "
                       "Windows profile: the serial number and issuer hashes of each, with the status and "
                       "times the cached response gives for it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "none",
        "category": "Windows",
        "notes": ("Reads the same MetaData and Content files as CryptnetUrlCache, which gives each entry's URL and "
                  'other fields; Profile Folder and Cache File identify the entry in both. An OCSP request sent with '
                  "GET is the base-64 text of the DER request appended to the responder's URL (RFC 6960, Appendix A.1), "
                  'and the reply is a DER OCSP response; scripts/ocsp.py reads both and names the source of each '
                  'structure it reads. An entry gets rows when its URL carries a request or its Content file reads as a '
                  'response that answers for at least one certificate: one row for each certificate the response '
                  'answers for (a SingleResponse), and one for each certificate of the request that the response does '
                  "not answer for. Named In says which: 'request and response', 'response' or 'request'. Certificate "
                  'Serial Number (hex), Issuer Name Hash and Issuer Key Hash are the serialNumber, issuerNameHash and '
                  'issuerKeyHash of the CertID, as upper-case hex of the stored bytes, so a serial keeps the leading 00 '
                  "its encoding carries (22 rows on the inputs below); Hash Algorithm is the CertID's hashAlgorithm, by "
                  'name for SHA-1, SHA-224, SHA-256, SHA-384 and SHA-512 and as its object identifier otherwise, and it '
                  "was SHA-1 on every row. The two hashes are of the issuer's name and public key (RFC 6960, 4.1.1), so "
                  'a row identifies a certificate by issuer and serial. It does not hold the certificate, its subject '
                  "or the name of the host that presented it. Certificate Status is the response's certStatus for that "
                  'certificate, good, revoked or unknown; Revocation Time (UTC) and Revocation Reason are the '
                  'revocationTime and the CRLReason name (RFC 5280, 5.3.1) of a revoked status. This Update (UTC) and '
                  "Next Update (UTC) are the SingleResponse's thisUpdate and nextUpdate and Produced At (UTC) the "
                  "response's producedAt, each a GeneralizedTime in UTC; they are times the responder states, and RFC "
                  '6960 (2.4) defines none of them as the time of the request. On the inputs below Produced At was '
                  'never within 60 seconds of Last Downloaded (418 rows). Last Downloaded (UTC) is the FILETIME at '
                  'offset 0x10 of the MetaData file, as CryptnetUrlCache reports it. Response Status is the '
                  "OCSPResponseStatus name (RFC 6960, 4.2.1) and Responder Key Hash the responder's key hash when the "
                  'response identifies it that way, blank when it is identified by name and when the response carries '
                  "no response data. Responder Host is the host part of the entry's URL, with the port when the URL "
                  "gives one. A 'request' row with a blank Response Status has no Content file that reads as a "
                  'response; none was met. No field read here names the process or the user action that made the '
                  'request; the MetaData bytes the analysis leaves unknown are not interpreted. No signature is checked '
                  "and nothing is looked up. On the inputs below there were 427 rows from 393 entries: 384 'request and "
                  "response', 34 'response' (two entries, on lonewolf_win10 and sans_nromanoff_win7, whose response "
                  "answered for 16 and 20 certificates) and 9 'request', whose response had a status other than "
                  'successful (7 unauthorized, 1 malformedRequest, 1 internalError) and so named no certificate; those '
                  '9 rows have no Certificate Status, Produced At, This Update, Next Update or Responder Key Hash. '
                  'Certificate Status was good on 414 rows and revoked on 4, never unknown: an unknown status, and a '
                  'response type other than the basic one (which gets a row for the request only), are read as RFC 6960 '
                  'gives them and were not met in any input. The 4 revoked rows are on the Windows 11 build 26200 known '
                  'data, where certutil -urlfetch -verify was run on test certificates, two of which the cached '
                  "responses give as revoked: each row's serial equalled the serial Windows and OpenSSL printed for the "
                  'certificate, and its Revocation Time and Revocation Reason (superseded on two rows, unspecified on '
                  'two) equalled what openssl ocsp -resp_text printed for the cached response. On every other input '
                  'Revocation Time (UTC) and Revocation Reason held no value on any row. Several columns held one value '
                  'on all rows of an input: Certificate Status (good) and Response Status (successful) on '
                  'af_case2_win10, cfreds_leakage_win7, hexordia_mvs2025_win11, pc_mus_001_win11, sans_nromanoff_win7 '
                  'and szechuan_win10; Named In on the same inputs but sans_nromanoff_win7; Responder Host on '
                  'af_case2_win10 and szechuan_win10; Issuer Name Hash, Issuer Key Hash and Responder Key Hash on '
                  'af_case2_win10 (4 rows); and Profile Folder on cfreds_leakage_win7 and the known data. Checked '
                  'against other readers: the cryptography package (49.0.0) read 344 of the 384 successful responses '
                  'and all 393 requests and gave the same serial, hashes, hash algorithm, status and times for each, '
                  'and the same response status for the 9 others; it refused the other 40 responses, and for those '
                  'OpenSSL 3.6.3 printed the same serial, hashes, status, This Update, Next Update and Produced At. An '
                  'entry whose Content file does not read as an OCSP response and whose URL carries no request gets no '
                  'row. The same holds for a response that answers for no certificate when the URL carries no request, '
                  'and for a MetaData file too short to read; neither was met. The run found no CryptnetUrlCache file '
                  'in alihadi_challenge3_win81.'),
        "paths": ('*/AppData/LocalLow/Microsoft/CryptnetUrlCache/*',),
        "output_types": ["standard"],
        "artifact_icon": "certificate",
        "sample_data": {
            "windows11_arm_cryptnet_ocsp_known_20261111": "Windows 11 build 26200 (ARM64) | 67 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 34 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 62 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 4 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 79 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 25 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 91 rows",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 65 rows",
        },
    },
}


def _utf16(raw):
    return raw.decode('utf-16-le', 'replace').rstrip('\x00')


def parse_metadata(data):
    """The fields of a CryptnetUrlCache MetaData file; raises ValueError when it is too short."""
    if len(data) < _HEADER_LEN:
        raise ValueError(f'{len(data)} bytes, shorter than the {_HEADER_LEN}-byte header')
    url_size, etag_size = struct.unpack_from('<I', data, 12)[0], struct.unpack_from('<I', data, 100)[0]
    if _HEADER_LEN + url_size + etag_size > len(data):
        raise ValueError('the URL and E-Tag sizes run past the end of the file')
    url_end = _HEADER_LEN + url_size
    return {'downloaded': struct.unpack_from('<Q', data, 16)[0],
            'last_modified': struct.unpack_from('<Q', data, 88)[0],
            'file_size': struct.unpack_from('<I', data, 112)[0],
            'url': _utf16(data[_HEADER_LEN:url_end]),
            'etag': _utf16(data[url_end:url_end + etag_size])}


def cache_parts(relative):
    """(cache folder key, 'metadata' or 'content', file name) of a path in a cache, or None."""
    path = '/' + relative.replace('\\', '/').lstrip('/')
    at = path.lower().find(_CACHE_FOLDER)
    if at < 0:
        return None
    rest = path[at + len(_CACHE_FOLDER):].split('/')
    if len(rest) != 2 or rest[0].lower() not in ('metadata', 'content') or not rest[1]:
        return None
    return path[:at + len(_CACHE_FOLDER)].lower(), rest[0].lower(), rest[1]


def profile_folder(relative):
    """The part of a cache file's path before AppData."""
    path = '/' + relative.replace('\\', '/').lstrip('/')
    at = path.lower().find(_CACHE_FOLDER)
    return path[1:at] if at >= 0 else os.path.dirname(path[1:])


def content_facts(path):
    """(size, SHA-256, first 8 bytes in hex) of a Content file."""
    digest = hashlib.sha256()
    first = b''
    with open(path, 'rb') as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            if not first:
                first = chunk[:8]
            digest.update(chunk)
    return os.path.getsize(path), digest.hexdigest(), first.hex().upper()


def _entries(context):
    """([(relative MetaData path, staged path, cache folder key, file name)], {(folder, NAME): Content path})."""
    metadata, contents = [], {}
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        parts = cache_parts(relative)
        if parts is None:
            continue
        folder, kind, name = parts
        if kind == 'metadata':
            metadata.append((relative, path, folder, name))
        else:
            contents[(folder, name.upper())] = path
    return sorted(set(metadata)), contents


@artifact_processor
def windowsCryptnetUrlCache(context):
    data_headers = (('Last Downloaded (UTC)', 'datetime'), 'URL', 'File Size', 'E-Tag',
                    ('Last-Modified (UTC)', 'datetime'), 'Profile Folder', 'Cache File',
                    'Content Size', 'Content SHA-256', 'Content Header (hex)')
    metadata, contents = _entries(context)
    data_list = []
    sources = []
    unreadable = 0
    for relative, path, folder, name in metadata:
        with open(path, 'rb') as handle:
            data = handle.read()
        try:
            fields = parse_metadata(data)
        except ValueError as ex:
            unreadable += 1
            logfunc(f'CryptnetUrlCache: {relative}: {ex}')
            continue
        sources.append(path)
        content = contents.get((folder, name.upper()))
        size = sha256 = header = ''
        if content:
            size, sha256, header = content_facts(content)
            sources.append(content)
        data_list.append((filetime_utc(fields['downloaded']), fields['url'], fields['file_size'],
                          fields['etag'], filetime_utc(fields['last_modified']),
                          profile_folder(relative), name, size, sha256, header))
    if unreadable:
        logfunc(f'CryptnetUrlCache: {unreadable} MetaData files could not be read')
    missing = sum(1 for row in data_list if row[7] == '')
    if missing:
        logfunc(f'CryptnetUrlCache: {missing} MetaData files have no Content file of the same name')
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[1]))
    return data_headers, data_list, '\n'.join(sources)


def _same_certificate(one, other):
    return all(one[key] == other[key] for key in ('hash_oid', 'issuer_name_hash', 'issuer_key_hash', 'serial'))


def ocsp_rows(url, content):
    """The certificates one cache entry names: [(named in, CertID dict, single response or None, response)].

    `content` is the Content file's bytes or None. One row for each SingleResponse of a response read from
    it, marked 'request and response' when the URL's request names the same CertID and 'response' when it
    does not; then one row, marked 'request', for each CertID of the URL's request that no SingleResponse
    carries. `response` is the parsed response, or None when the content is not one. Returns [] when the
    URL carries no request and the content gives no SingleResponse."""
    requested = ocsp.request_in_url(url) or []
    response = None
    if content:
        try:
            response = ocsp.parse_response(content)
        except ocsp.OcspError:
            response = None
    rows = []
    answered = set()
    for single in (response['responses'] if response else []):
        match = [at for at, wanted in enumerate(requested) if _same_certificate(wanted, single)]
        answered.update(match)
        rows.append(('request and response' if match else 'response', single, single, response))
    for at, wanted in enumerate(requested):
        if at not in answered:
            rows.append(('request', wanted, None, response))
    return rows


@artifact_processor
def windowsCryptnetUrlCacheOcsp(context):
    data_headers = (('Last Downloaded (UTC)', 'datetime'), ('Produced At (UTC)', 'datetime'),
                    ('This Update (UTC)', 'datetime'), ('Next Update (UTC)', 'datetime'),
                    ('Revocation Time (UTC)', 'datetime'), 'Certificate Serial Number (hex)', 'Certificate Status',
                    'Revocation Reason', 'Issuer Name Hash', 'Issuer Key Hash', 'Hash Algorithm', 'Named In',
                    'Response Status', 'Responder Key Hash', 'Responder Host', 'Profile Folder', 'Cache File')
    metadata, contents = _entries(context)
    data_list = []
    sources = []
    unread = 0
    for relative, path, folder, name in metadata:
        with open(path, 'rb') as handle:
            data = handle.read()
        try:
            fields = parse_metadata(data)
        except ValueError:
            continue
        content_path = contents.get((folder, name.upper()))
        content = None
        if content_path:
            with open(content_path, 'rb') as handle:
                content = handle.read()
        rows = ocsp_rows(fields['url'], content)
        if not rows:
            continue
        sources.append(path)
        if content_path:
            sources.append(content_path)
        try:
            host = urlsplit(fields['url']).netloc
        except ValueError:
            host = ''
        for named_in, cert, single, response in rows:
            if response is None and content:
                unread += 1
            status = '' if response is None else ocsp.RESPONSE_STATUS.get(response['status'], str(response['status']))
            reason = '' if single is None or single['revocation_reason'] is None else ocsp.CRL_REASON.get(
                single['revocation_reason'], str(single['revocation_reason']))
            data_list.append((
                filetime_utc(fields['downloaded']),
                '' if response is None or response['produced_at'] is None else response['produced_at'],
                '' if single is None else single['this_update'],
                '' if single is None or single['next_update'] is None else single['next_update'],
                '' if single is None or single['revocation_time'] is None else single['revocation_time'],
                cert['serial'], '' if single is None else single['status'], reason, cert['issuer_name_hash'],
                cert['issuer_key_hash'], ocsp.HASH_NAMES.get(cert['hash_oid'], cert['hash_oid']), named_in, status,
                '' if response is None else response['responder_key_hash'], host,
                profile_folder(relative), name))
    if unread:
        logfunc(f'CryptnetUrlCache OCSP: {unread} requests whose Content file is not empty and did not read as '
                'an OCSP response')
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[16], row[5]))
    return data_headers, data_list, '\n'.join(sources)
