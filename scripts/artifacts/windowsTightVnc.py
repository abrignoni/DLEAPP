"""TightVNC Server settings parser for DLEAPP.

Author: @AlexisBrignoni, Claude.

TightVNC Server run as a Windows service keeps its settings, its three passwords among them, in the
TightVNC\\Server key of the SOFTWARE hive. This reads that key and decodes the passwords, which TightVNC
stores DES-encrypted under a key fixed in its source. Value names and the key are cited in the notes.
"""

import os

from Crypto.Cipher import DES

from scripts.windows_registry import Registry

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import key_written_utc, open_hive

_KEYS = ('TightVNC\\Server', 'Wow6432Node\\TightVNC\\Server')
# VncPassCrypt::m_key in TightVNC's util/VncPassCrypt.cpp (see notes).
_SOURCE_KEY = bytes((23, 82, 107, 6, 35, 78, 88, 7))
# The DES key that decrypts the stored values: each byte of the source key with its bits in reverse order.
_DES_KEY = bytes(int(f'{byte:08b}'[::-1], 2) for byte in _SOURCE_KEY)
_PASSWORDS = ('Password', 'PasswordViewOnly', 'ControlPassword')
_SETTINGS = ('UseVncAuthentication', 'UseControlAuthentication', 'AcceptRfbConnections', 'RfbPort',
             'AcceptHttpConnections', 'HttpPort', 'LoopbackOnly', 'AllowLoopback', 'IpAccessControl', 'ExtraPorts')

__artifacts_v2__ = {
    "windowsTightVncServer": {
        "name": "TightVNC Server Settings",
        "description": "TightVNC Server settings in the SOFTWARE hive: its primary, view-only and control "
                       "passwords, decoded, and its authentication, port and access settings as read from the key, with "
                       "the key's last written time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-11",
        "last_update_date": "2026-11-11",
        "requirements": "PyCryptodome",
        "category": "TightVNC",
        "notes": ('Reads the TightVNC\\Server key, and Wow6432Node\\TightVNC\\Server, of the SOFTWARE hive, one row per '
                  "key found; Registry Key says which. The value names are the ones TightVNC's server configuration "
                  'code writes '
                  '(https://github.com/chenall/tightvnc/blob/9f3910aac17fda4b44bb37a0209a5722a3bdb474/server-config-lib/Configurator.cpp#L533-L626 '
                  'for eleven of them, #L496 for IpAccessControl and #L223 for ExtraPorts) and reads back (#L644-L797, '
                  '#L509, #L238). That is a public copy of the TightVNC source whose tvnserver.rc marks it version '
                  '2.8.27; the tested build is 2.8.89, so the names are sourced for 2.8.27 and five of them were seen '
                  'on 2.8.89. That code stores each password as 8 bytes of binary data '
                  '(https://github.com/chenall/tightvnc/blob/9f3910aac17fda4b44bb37a0209a5722a3bdb474/server-config-lib/Configurator.cpp#L578-L610, '
                  'the size at '
                  'https://github.com/chenall/tightvnc/blob/9f3910aac17fda4b44bb37a0209a5722a3bdb474/server-config-lib/ServerConfig.h#L50), '
                  'encrypted with DES under a key fixed in the source '
                  '(https://github.com/chenall/tightvnc/blob/9f3910aac17fda4b44bb37a0209a5722a3bdb474/util/VncPassCrypt.cpp#L29-L54). '
                  'The installer code keeps at most the first 8 characters of a password and converts it with the '
                  'system ANSI code page before encrypting it '
                  '(https://github.com/chenall/tightvnc/blob/9f3910aac17fda4b44bb37a0209a5722a3bdb474/setup-helper/CustomAction.cpp#L59-L74), '
                  'so a decoded value can be the start of a longer password and a non-ASCII character can read '
                  'differently from what was typed; neither was exercised on real data. Password, View-Only Password '
                  'and Control Password are the Password, PasswordViewOnly and ControlPassword values decrypted as one '
                  'DES block with that key, the bits of each key byte in reverse order, and read as Latin-1 text up to '
                  'the first NUL byte; a value that is not 8 bytes is not decoded. The bit order was settled by '
                  'measurement: on the Windows 11 build 26200 known data, made with TightVNC 2.8.89 and three random '
                  '8-character passwords given to its installer, each of the three values decoded to the password set '
                  'for it. A password shorter than 8 characters is exercised by the tests only. The three (stored, hex) '
                  'columns give the same values as stored. Use VNC Authentication, Use Control Authentication, Accept '
                  'RFB Connections, RFB Port, Accept HTTP Connections, HTTP Port, Loopback Only, Allow Loopback, IP '
                  'Access Control and Extra Ports are the UseVncAuthentication, UseControlAuthentication, '
                  'AcceptRfbConnections, RfbPort, AcceptHttpConnections, HttpPort, LoopbackOnly, AllowLoopback, '
                  'IpAccessControl and ExtraPorts values as read from the key (a number as an integer, binary data as '
                  "hex), blank when the value is absent; the key's other values are not reported. On the known data the "
                  'key held five values, the three passwords and Use VNC Authentication and Use Control Authentication '
                  '(each 1), all set through the installer, with the service running: Accept RFB Connections, RFB Port, '
                  'Accept HTTP Connections, HTTP Port, Loopback Only, Allow Loopback, IP Access Control and Extra Ports '
                  'each held no value on the one row, so a blank is a value absent from the key and does not show that '
                  'the setting is off; what the server does when a value is absent is not reported. Key Last Written '
                  "(UTC) is the key's last written time, on the known data about 11 seconds after the logged start of "
                  'the install; Microsoft describes it as the last time the key or any of its values was modified '
                  '(https://github.com/MicrosoftDocs/sdk-api/blob/a4fd3f7efe2e3378a96c6fe5a6a9455eba9fa021/sdk-api-src/content/winreg/nf-winreg-regqueryinfokeyw.md#L140-L141), '
                  'so it does not date each value. On the same VM the key and its five values were still present after '
                  'TightVNC was uninstalled; that state is not in the known-data hive. Measured on that one input only: '
                  'none of the 8 SOFTWARE hives of the other inputs below held a TightVNC key, so other TightVNC '
                  'versions, a server that has written its other settings and the Wow6432Node key are unexercised. Not '
                  "read: a TightVNC key in a user's NTUSER.DAT, and the settings of other VNC servers. A hive that "
                  'cannot be opened is named in the run log and skipped.'),
        "paths": ('*/Windows/System32/config/SOFTWARE',
                  '*/Windows/System32/config/[Ss][Oo][Ff][Tt][Ww][Aa][Rr][Ee].[Ll][Oo][Gg][12]'),
        "output_types": ["standard"],
        "artifact_icon": "monitor",
        "sample_data": {
            "windows11_arm_tightvnc_known_20261111": "Windows 11 build 26200 (ARM64), TightVNC 2.8.89 | 1 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
            "sans_nromanoff_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (the SOFTWARE hive holds no TightVNC key)",
        },
    },
}


def decode_password(stored):
    """The password a stored 8-byte value holds, or '' for a value that is not 8 bytes.

    The value is one DES block. Decrypted, it is the password padded with NUL bytes to 8; the text up to the
    first NUL is returned, read as Latin-1."""
    if not isinstance(stored, bytes) or len(stored) != 8:
        return ''
    plain = DES.new(_DES_KEY, DES.MODE_ECB).decrypt(stored)
    return plain.split(b'\x00', 1)[0].decode('latin-1')


def _stored(value):
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, list):
        return '; '.join(str(item) for item in value)
    return value


@artifact_processor
def windowsTightVncServer(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Password', 'View-Only Password', 'Control Password',
                    'Password (stored, hex)', 'View-Only Password (stored, hex)', 'Control Password (stored, hex)',
                    'Use VNC Authentication', 'Use Control Authentication', 'Accept RFB Connections', 'RFB Port',
                    'Accept HTTP Connections', 'HTTP Port', 'Loopback Only', 'Allow Loopback', 'IP Access Control',
                    'Extra Ports', 'Registry Key')
    data_list, sources = [], []
    for source in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(source) or os.path.basename(source).upper() != 'SOFTWARE':
            continue
        relative = context.get_relative_path(source)
        try:
            hive = open_hive(source, context)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'TightVNC Server Settings: could not read {relative}: {exc}')
            continue
        found = False
        for path in _KEYS:
            try:
                key = hive.open(path)
            except Registry.RegistryKeyNotFoundException:
                continue
            values = {}
            for value in key.values():
                try:
                    values[value.name()] = value.value()
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logfunc(f'TightVNC Server Settings: could not read {value.name()} in {relative}: {exc}')
            row = [key_written_utc(key)]
            row.extend(decode_password(values.get(name)) for name in _PASSWORDS)
            row.extend(_stored(values[name]) if name in values else '' for name in _PASSWORDS)
            row.extend(_stored(values[name]) if name in values else '' for name in _SETTINGS)
            row.append(path)
            data_list.append(tuple(row))
            found = True
        if found:
            sources.append(source)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[-1]))
    return data_headers, data_list, '\n'.join(sources)
