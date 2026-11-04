"""Saved Wi-Fi keys from the Windows WLAN profiles, decrypted offline, for DLEAPP.

A WLAN profile stores its pre-shared key in <sharedKey><keyMaterial>. When
<protected> is true the key material is a DPAPI blob protected in the LocalSystem
(SYSTEM) context. Recovering it offline needs, from the same image, the SYSTEM and
SECURITY registry hives and the SYSTEM DPAPI master keys; the vendored dpapiprobe
library (scripts/vendor/dpapiprobe) runs that chain with PyCryptodome and
python-registry.
"""

__artifacts_v2__ = {
    "windowsWifiKeys": {
        "name": "Windows Wi-Fi Keys",
        "description": "Saved wireless networks from the Windows WLAN profiles, with the pre-shared key "
                       "recovered from the profile's key material where one is stored: SSID, authentication "
                       "and encryption, the key, and how the key was obtained.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-02",
        "last_update_date": "2026-11-02",
        "requirements": "none",
        "category": "Windows Network",
        "notes": "Reads each WLAN profile under ProgramData\\Microsoft\\Wlansvc\\Profiles\\Interfaces, and any copy under Wlansvc\\MigrationData\\Profiles\\Interfaces, and recovers the pre-shared key from the profile's sharedKey/keyMaterial. When sharedKey/protected is true the key material is a DPAPI blob; on every image run its master key was one of the SYSTEM (S-1-5-18) master keys, opened with the DPAPI_SYSTEM secret. It is decrypted offline by the vendored dpapiprobe library (scripts/vendor/dpapiprobe, PyCryptodome and python-registry) from four inputs that must all be in the same extraction: the boot key from the SYSTEM hive, the DPAPI_SYSTEM LSA secret from the SECURITY hive, the SYSTEM DPAPI master keys under Windows\\System32\\Microsoft\\Protect\\S-1-5-18, and the profile. All seven images run had the hives and the S-1-5-18 master keys. The hives and master key files are opened read only. Key is the recovered key material decoded as UTF-8 and cut at the first NUL byte (on the three images the recovered material was the passphrase followed by one NUL byte); on the tested images it was ASCII. Key Status says how it was obtained: 'recovered' is decrypted from a protected blob; 'stored unprotected' is a profile whose protected flag is false, where keyMaterial is the key as stored (not seen on any image run); 'no keyMaterial in profile' is a profile with no sharedKey/keyMaterial (Microsoft documents sharedKey as optional and only necessary when WEP, PSK or SAE keys are included, so 802.1X profiles and open networks without WEP need not store one; not seen on any image run); 'decrypt failed' is key material that is not a decodable blob, or a protected blob whose master key file was not in the extraction or did not open (not seen on any image run); and 'hives or master keys not available' (or 'hives did not yield the decryption inputs') is an extraction that cannot supply the decryption inputs, where a protected key is left blank, which is not evidence that no key is stored (not seen on any image run). SSID, Authentication, Encryption, Key Type and Connection Mode are the profile's SSIDConfig name, authentication, encryption, sharedKey keyType and connectionMode as stored, surrounding whitespace trimmed. Interface is the GUID-named folder under Interfaces the profile sits in. Source File names the profile each row came from; a live profile and its MigrationData copy are separate rows with their own paths, so one network can appear twice with the same key, as it did on pc_mus_001_win11. Tested on seven Windows images; three had a profile and each decrypted the protected key (authentication WPA2PSK on two, WPA3SAE on one), pc_mus_001_win11 holding it twice (live and migration) and the others once. The DPAPI chain (boot key, DPAPI_SYSTEM secret, SYSTEM master keys, blob) was also checked with a value known in advance, protected under the SYSTEM account on a test system, and recovered it unchanged; that check covers the DPAPI chain, not the WLAN profile parsing. The master key each blob named was decrypted on one Windows 10 and two Windows 11 images. Not covered: profiles with no sharedKey (802.1X, and open networks without WEP) have no stored key to recover. No other LEAPP core reads this profile.",
        "paths": (
            '*/ProgramData/Microsoft/Wlansvc/Profiles/Interfaces/*/*.xml',
            '*/ProgramData/Microsoft/Wlansvc/MigrationData/Profiles/Interfaces/*/*.xml',
            '*/Windows/System32/config/SYSTEM',
            '*/Windows/System32/config/SECURITY',
            '*/Windows/System32/Microsoft/Protect/S-1-5-18/*',
            '*/Windows/System32/Microsoft/Protect/S-1-5-18/User/*',
        ),
        "output_types": "standard",
        "artifact_icon": "wifi",
        "sample_data": {
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 2 rows (a profile and its migration copy)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no WLAN profile)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no WLAN profile)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no WLAN profile)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no WLAN profile)",
        },
    },
}

import binascii
import os
import re
import struct
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import dpapiprobe

_LABEL = 'Windows Wi-Fi Keys'
_NS = '{http://www.microsoft.com/networking/WLAN/profile/v1}'
_GUID_FILE = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$')


def _text(root, path):
    value = root.findtext(path)
    return value.strip() if value else ''


class _Vault:
    """Decrypts the SYSTEM master keys of an image once, and opens blobs against them."""

    def __init__(self, system_hive, security_hive, mk_files):
        bootkey = dpapiprobe.get_bootkey(system_hive)
        dpapi_system = dpapiprobe.get_dpapi_system(security_hive, bootkey)
        self._candidates = dpapiprobe.system_master_key_candidates(dpapi_system)
        self._mk_files = mk_files  # {guid: path}
        self._keys = {}

    def _master_key(self, guid):
        if guid not in self._keys:
            path = self._mk_files.get(guid)
            self._keys[guid] = None
            if path:
                with open(path, 'rb') as handle:
                    self._keys[guid] = dpapiprobe.decrypt_master_key(handle.read(), self._candidates)
        return self._keys[guid]

    def decrypt(self, key_material):
        raw = binascii.unhexlify(key_material)
        master_key = self._master_key(dpapiprobe.DpapiBlob(raw).mk_guid)
        if master_key is None:
            return None
        return dpapiprobe.decrypt_blob(raw, master_key)


@artifact_processor
def windowsWifiKeys(context):
    data_headers = ('SSID', 'Authentication', 'Encryption', 'Key Type', 'Key', 'Key Status',
                    'Connection Mode', 'Profile Name', 'Interface', 'Source File')
    data_list = []
    sources = []

    hives = {'SYSTEM': None, 'SECURITY': None}
    mk_files = {}
    profiles = []
    for found in context.get_files_found():
        path = str(found)
        if not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        if name in hives and hives[name] is None:
            hives[name] = path
        elif _GUID_FILE.match(name) and 'Protect' in path:
            mk_files.setdefault(name, path)
        elif path.lower().endswith('.xml') and 'Wlansvc' in path:
            profiles.append(path)

    if not profiles:
        return data_headers, data_list, ''

    vault = None
    unavailable = 'hives or master keys not available'
    if hives['SYSTEM'] and hives['SECURITY'] and mk_files:
        try:
            vault = _Vault(hives['SYSTEM'], hives['SECURITY'], mk_files)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: could not read the SYSTEM master keys: {type(ex).__name__}: {ex}')
            unavailable = 'hives did not yield the decryption inputs'
    if vault is None:
        logfunc(f'{_LABEL}: protected keys cannot be decrypted (need the SYSTEM and SECURITY hives and the '
                f'SYSTEM DPAPI master keys in the extraction)')

    for path in sorted(profiles):
        relative = context.get_relative_path(path)
        try:
            root = ElementTree.parse(path).getroot()
        except ElementTree.ParseError as ex:
            logfunc(f'{_LABEL}: could not parse {relative}: {ex}')
            continue
        sources.append(path)
        ssid = _text(root, f'.//{_NS}SSIDConfig/{_NS}SSID/{_NS}name')
        profile_name = _text(root, f'{_NS}name')
        auth = _text(root, f'.//{_NS}authEncryption/{_NS}authentication')
        enc = _text(root, f'.//{_NS}authEncryption/{_NS}encryption')
        mode = _text(root, f'{_NS}connectionMode')
        interface = os.path.basename(os.path.dirname(path))
        key_type = _text(root, f'.//{_NS}sharedKey/{_NS}keyType')
        protected = _text(root, f'.//{_NS}sharedKey/{_NS}protected')
        material = _text(root, f'.//{_NS}sharedKey/{_NS}keyMaterial')

        key, status = '', ''
        if not material:
            status = 'no keyMaterial in profile'
        elif protected.lower() == 'false':
            key, status = material, 'stored unprotected'
        elif vault is None:
            status = unavailable
        else:
            try:
                cleartext = vault.decrypt(material)
            except (binascii.Error, ValueError, KeyError, struct.error) as ex:
                logfunc(f'{_LABEL}: {relative}: key material did not decode ({type(ex).__name__})')
                cleartext = None
            if not cleartext:
                status = 'decrypt failed'
            else:
                key, status = cleartext.split(b'\x00', 1)[0].decode('utf-8', 'replace'), 'recovered'
        data_list.append((ssid, auth, enc, key_type, key, status, mode, profile_name, interface, relative))

    return data_headers, data_list, '\n'.join(sources)
