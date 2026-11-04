"""Write a small synthetic ETL file from the layouts scripts/etl.py cites, for its tests.

Author: @AlexisBrignoni, Claude.

Every value is made up. The file has two 4 KiB buffers: the first holds the logfile header record, then
WLAN AutoConfig 20025 and 8001 events and one WPP record; the second holds NWiFi 10040 and 10041 events. The
performance counter runs at 2,628,198 Hz so that integer, rounded and truncated scaling give different times.
Run as a script to write the file: python admin/test/scripts/etl_fixture.py OUT.etl
"""

import struct
import sys
import uuid

BUFFER = 4096
PERF_FREQ = 2_628_198
START_TIME = 133_000_000_000_000_000          # a FILETIME in 2022
T0 = 900_000_000_000                         # the counter at the logfile header record
AUTOCONFIG = uuid.UUID('9580d7dd-0379-4658-9870-d5be7d52d6de')
NWIFI = uuid.UUID('0bd3506a-9030-4f76-9b88-3e8fe1f7cfb6')
INTERFACE = uuid.UUID('11111111-2222-3333-4444-555555555555')
WPP_GUID = uuid.UUID('99999999-8888-7777-6666-555555555555')


def _ustr(text):
    return text.encode('utf-16-le') + b'\x00\x00'


def _align(blob):
    return blob + b'\x00' * (-len(blob) % 8)


def logfile_header_record():
    body = struct.pack('<IIIIqIIII', BUFFER, 0x0501000a, 26200, 2, 0, 156250, 8, 0x80000002, 0)
    body += struct.pack('<IIII', 1, 8, 0, 3000)
    body += struct.pack('<QQ', 0, 0)                        # LoggerName, LogFileName pointers
    body += struct.pack('<i', 300) + b'\x00' * 168          # TIME_ZONE_INFORMATION, Bias then the rest
    body += b'\x00' * (-len(body) % 8)
    body += struct.pack('<qqqII', START_TIME - 10_000_000, PERF_FREQ, START_TIME, 1, 0)
    body += _ustr('Wifi') + _ustr('C:\\Windows\\System32\\LogFiles\\WMI\\Wifi.etl')
    size = 0x20 + len(body)
    header = struct.pack('<HBBHHIIqII', 2, 0x02, 0xc0, size, 0x0000, 4, 8, T0, 0, 0)
    return _align(header + body)


def event_record(provider, event_id, stamp, data, version=0):
    size = 0x50 + len(data)
    header = struct.pack('<HHHHIIq', size, 0xc013, 0x0040, 0, 100, 200, stamp)
    header += provider.bytes_le
    header += struct.pack('<HBBBBHQ', event_id, version, 16, 4, 0, 0, 0x8000000000000000)
    header += struct.pack('<Q', 0) + b'\x00' * 16
    return _align(header + data)


def wpp_record(stamp):
    args = struct.pack('<I', 7)
    flags = 0x0001 | 0x0002 | 0x0008 | 0x0020
    body = struct.pack('<I', 1) + WPP_GUID.bytes_le + struct.pack('<qII', stamp, 100, 200) + args
    size = 8 + len(body)
    marker = 0x80000000 | 0x10000000 | size
    return _align(struct.pack('<IHH', marker, 10, flags) + body)


def visible_network(ssid, bssids, auth, cipher, rssi):
    return _ustr(ssid) + struct.pack('<IIII', bssids, auth, cipher, rssi)


def connected(ssid, profile, connection_id):
    return (INTERFACE.bytes_le + _ustr('Fixture Wireless Adapter') + _ustr('Automatic connection with a profile')
            + _ustr(profile) + _ustr(ssid) + _ustr('Infrastructure') + _ustr('802.11ac') + _ustr('WPA2-Personal')
            + _ustr('AES') + struct.pack('<IQI', 0, connection_id, 0))


def association(mac, status=None):
    blob = struct.pack('<Q', 0xffff800012345678) + INTERFACE.bytes_le + bytes(mac)
    return blob if status is None else blob + struct.pack('<I', status)


def buffer(records, sequence, stamp, first=False):
    """A WMI_BUFFER_HEADER and its records. ClientContext (logger 0x11 in its high word), State 3, Offset,
    BufferFlag and BufferType are set as the buffers of a corpus Wifi.etl have them: Get-WinEvent refused this
    file as corrupted while they were zero."""
    payload = b''.join(records)
    saved = 0x48 + len(payload)
    if saved > BUFFER:
        raise ValueError('records do not fit one buffer')
    header = struct.pack('<IIIiqqQIIIHH', BUFFER, saved, saved, 0, stamp, sequence, 0, 0x00110000, 3, saved,
                         0x21 if first else 0x20, 4 if first else 0)
    header += b'\x00' * (0x48 - len(header))
    return (header + payload).ljust(BUFFER, b'\xff')


# (stamp offset from T0 in counter ticks, record). The two NWiFi offsets, about 2.2 days, are ones where integer
# division and the truncated floating-point scale differ by one tick.
EVENTS_1 = [
    (1_000_003, event_record(AUTOCONFIG, 20025, T0 + 1_000_003, visible_network('fixture-net-a', 2, 7, 4, 4294967216))),
    (1_000_017, event_record(AUTOCONFIG, 20025, T0 + 1_000_017, visible_network('', 5, 6, 4, 4294967238))),
    (2_500_001, wpp_record(T0 + 2_500_001)),
    (3_141_593, event_record(AUTOCONFIG, 8001, T0 + 3_141_593, connected('fixture-net-a', 'fixture-net-a', 0x2a))),
]
EVENTS_2 = [
    (500_000_008_780, event_record(NWIFI, 10040, T0 + 500_000_008_780, association(b'\x02\x00\x5e\x10\x20\x30'))),
    (500_000_018_231, event_record(NWIFI, 10041, T0 + 500_000_018_231, association(b'\x02\x00\x5e\x10\x20\x30', 0))),
]


def build():
    first = buffer([logfile_header_record()] + [record for _, record in EVENTS_1], 0, 0, first=True)
    second = buffer([record for _, record in EVENTS_2], 1, T0 + 500_000_018_231)
    return first + second


if __name__ == '__main__':
    with open(sys.argv[1], 'wb') as handle:
        handle.write(build())
