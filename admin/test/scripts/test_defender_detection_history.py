"""Pin the DetectionHistory reading in scripts/windows_defender_history.py and
scripts/artifacts/windowsDefenderDetectionHistory.py.

Every file below is built by the test from the layout the reader documents (libyal dtformats,
"Windows Defender scan DetectionHistory file format"); no value comes from a real device.
Expected values are written out, never read back from the code.
"""
import fnmatch
import pathlib
import struct
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import windows_defender_history as dh  # pylint: disable=wrong-import-position
from scripts.artifacts import windowsDefenderDetectionHistory as artifact  # pylint: disable=wrong-import-position

DETECTION_ID = uuid.UUID('11111111-2222-3333-4444-555555555555')
ENTRY_ID = uuid.UUID('80001234-0000-0000-abcd-ef0123456789')
# 2026-01-02 03:04:05.123456 UTC, ten seconds later, and twenty seconds later, as FILETIMEs.
DETECTED = 134117966451234560
CHANGED = 134117966551234560
REMEDIATED = 134117966651234560
WHEN = datetime(2026, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
LATER = datetime(2026, 1, 2, 3, 4, 15, 123456, tzinfo=timezone.utc)
LATEST = datetime(2026, 1, 2, 3, 4, 25, 123456, tzinfo=timezone.utc)
SHA256 = 'a' * 64
SHA1 = 'b' * 40
MD5 = 'c' * 32


def value(data_type, data):
    """A value: data size, data type, data, padding to a multiple of 8 (dtformats 'Value')."""
    raw = struct.pack('<II', len(data), data_type) + data
    return raw + bytes(-len(raw) % 8)


def text(string):
    return value(0x15, (string + '\x00').encode('utf-16-le'))


def u32(number, data_type=0x06):
    return value(data_type, struct.pack('<I', number))


def filetime(number):
    return value(0x0A, struct.pack('<Q', number))


def guid(identifier):
    return value(0x1E, identifier.bytes_le)


SEPARATOR = text('Magic.Version:1.2')


def tracking_value(key, kind, data):
    raw_key = (key + '\x00').encode('utf-16-le')
    return struct.pack('<I', len(raw_key)) + raw_key + struct.pack('<I', kind) + data


def tracking_string(key, string):
    raw = (string + '\x00').encode('utf-16-le')
    return tracking_value(key, 6, struct.pack('<I', len(raw)) + raw)


def tracking(sha256=SHA256, sha1=SHA1, md5=MD5):
    """Threat tracking data: the 20-byte header, the values data size, then the values."""
    values = (tracking_string('ThreatTrackingSha256', sha256)
              + tracking_value('ThreatTrackingSize', 4, struct.pack('<Q', 68))
              + tracking_string('ThreatTrackingSha1', sha1)
              + tracking_value('ThreatTrackingIsEsuSig', 5, b'\x00')
              + tracking_value('ThreatTrackingResearchData', 7, bytes(5))
              + tracking_string('ThreatTrackingMD5', md5)
              + tracking_value('ThreatTrackingThreatId', 3, struct.pack('<I', 99)))
    total = 24 + len(values)
    return struct.pack('<5I', 1, 20, len(values), total, 0) + struct.pack('<I', len(values)) + values


HEADER_ONLY_TRACKING = struct.pack('<5I', 1, 20, 0, 20, 0)


def resource(kind, location, tracking_data):
    return (SEPARATOR + text(kind) + text(location) + u32(0x10000001)
            + u32(len(tracking_data)) + value(0x28, tracking_data))


def trailing(changed=CHANGED, entry=ENTRY_ID, user='HOST\\tester', process='C:\\Tools\\app.exe',
             detected=DETECTED, remediated=REMEDIATED, second='NT AUTHORITY\\SYSTEM'):
    """The values after the last resource set, in dtformats 'set 3' order from index 6."""
    return (filetime(changed) + u32(0, 0x05) + u32(0) + guid(entry) + u32(1) + u32(2)
            + text(user) + u32(3) + text(process) + u32(3) + u32(1) + u32(0)
            + filetime(detected) + u32(0) + filetime(remediated) + u32(0) + u32(0, 0x00)
            + u32(0) + text(second) + u32(0) + u32(0) + u32(1))


def detection_file(resources=None, count=None, threat_name='Test:Win32/Sample', severity=5,
                   category=42, tail=None, detection_id=DETECTION_ID):
    resources = resources if resources is not None else [
        resource('file', 'C:\\Users\\tester\\sample.txt', tracking())]
    count = len(resources) if count is None else count
    head = value(0x08, struct.pack('<Q', 2147519003)) + guid(detection_id)
    threat = (SEPARATOR + text(threat_name) + u32(0) + u32(severity) + u32(category) + u32(110)
              + u32(4) + u32(3) + u32(3) + u32(2) + u32(3) + u32(6) + u32(count))
    return head + threat + b''.join(resources) + (trailing() if tail is None else tail)


class ValueTest(unittest.TestCase):
    def test_values_and_alignment(self):
        values, note = dh.read_values(text('ab') + u32(7) + filetime(DETECTED) + guid(ENTRY_ID))
        self.assertEqual(note, '')
        self.assertEqual([(v.offset, v.data_type, v.decoded) for v in values], [
            (0, 0x15, 'ab'), (16, 0x06, 7), (32, 0x0A, DETECTED),
            (48, 0x1E, '80001234-0000-0000-abcd-ef0123456789')])

    def test_empty_string(self):
        values, note = dh.read_values(value(0x15, b''))
        self.assertEqual((note, values[0].decoded), ('', ''))

    def test_unknown_type_kept_as_bytes(self):
        values, _ = dh.read_values(value(0x33, b'\x01\x02'))
        self.assertEqual(values[0].decoded, b'\x01\x02')

    def test_value_past_the_end(self):
        data = struct.pack('<II', 500, 0x15) + b'a\x00'
        values, note = dh.read_values(data)
        self.assertEqual(values, [])
        self.assertIn('past the end of the file', note)

    def test_short_tail(self):
        values, note = dh.read_values(u32(1) + b'\x01\x00')
        self.assertEqual(len(values), 1)
        self.assertEqual(note, '2 bytes at offset 16 too short for a value')

    def test_filetime(self):
        self.assertEqual(dh.filetime_utc(DETECTED), WHEN)
        self.assertEqual(dh.filetime_utc(0), '')


class TrackingTest(unittest.TestCase):
    def test_values(self):
        fields, note = dh.read_threat_tracking(tracking())
        self.assertEqual(note, '')
        self.assertEqual(fields, {
            'ThreatTrackingSha256': SHA256, 'ThreatTrackingSize': 68,
            'ThreatTrackingSha1': SHA1, 'ThreatTrackingIsEsuSig': 0,
            'ThreatTrackingResearchData': bytes(5), 'ThreatTrackingMD5': MD5,
            'ThreatTrackingThreatId': 99})

    def test_header_only(self):
        self.assertEqual(dh.read_threat_tracking(HEADER_ONLY_TRACKING), ({}, ''))

    def test_without_header(self):
        values = tracking_string('ThreatTrackingSha256', SHA256)
        data = struct.pack('<I', 4 + len(values)) + values
        self.assertEqual(dh.read_threat_tracking(data), ({'ThreatTrackingSha256': SHA256}, ''))

    def test_unknown_value_type(self):
        values = tracking_value('ThreatTrackingOther', 9, b'')
        data = struct.pack('<I', 4 + len(values)) + values
        self.assertEqual(dh.read_threat_tracking(data)[1],
                         'threat tracking value type 9 not in the layout')

    def test_truncated(self):
        self.assertEqual(dh.read_threat_tracking(tracking()[:-2])[1],
                         'threat tracking data ends inside a value')


class Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return [str(f) for f in self.files]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


HEADERS = ('Initial Detection Time (UTC)', 'Last Status Change Time (UTC)', 'Remediation Time (UTC)',
           'Threat Name', 'Threat ID', 'Severity', 'Category', 'Resource Count', 'Resources',
           'SHA-256', 'SHA-1', 'MD5', 'Domain User', 'Process Name', 'Second User (as stored)',
           'GUID at Index 9', 'Detection ID', 'Read Note', 'Source File')
FOLDER = 'ProgramData/Microsoft/Windows Defender/Scans/History/Service/DetectionHistory/06'
NAME = '11111111-2222-3333-4444-555555555555'.upper()


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.logged = []
        patcher = patch.object(artifact, 'logfunc', self.logged.append)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, data, folder=FOLDER, name=NAME, volume='C'):
        path = self.root/volume/folder/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_artifact(self, files):
        return artifact.defenderDetectionHistory.__wrapped__(Context(self.root, files))

    def test_row(self):
        path = self.write(detection_file())
        headers, rows, sources = self.run_artifact([path])
        self.assertEqual(tuple(h[0] if isinstance(h, tuple) else h for h in headers), HEADERS)
        self.assertEqual(rows, [(
            WHEN, LATER, LATEST, 'Test:Win32/Sample', 2147519003, 'SEVERE (5)', 'VIRUS (42)', 1,
            'file: C:\\Users\\tester\\sample.txt', SHA256, SHA1, MD5, 'HOST\\tester',
            'C:\\Tools\\app.exe', 'NT AUTHORITY\\SYSTEM', '80001234-0000-0000-ABCD-EF0123456789',
            NAME, '', f'C/{FOLDER}/{NAME}')])
        self.assertEqual(sources, str(path))

    def test_three_resources_and_header_only_tracking(self):
        resources = [resource('containerfile', 'C:\\x\\a.zip', HEADER_ONLY_TRACKING),
                     resource('file', 'C:\\x\\a.zip->b.com', tracking()),
                     resource('webfile', 'C:\\x\\a.zip|https://example.com/a.zip|pid:1',
                              tracking(sha256='d' * 64))]
        _, rows, _ = self.run_artifact([self.write(detection_file(resources))])
        row = rows[0]
        self.assertEqual(row[7:12], (
            3, 'containerfile: C:\\x\\a.zip\nfile: C:\\x\\a.zip->b.com\n'
               'webfile: C:\\x\\a.zip|https://example.com/a.zip|pid:1',
            SHA256 + '\n' + 'd' * 64, SHA1, MD5))
        self.assertEqual(row[0], WHEN)
        self.assertEqual(row[17], '')

    def test_unset_remediation_and_null_entry(self):
        tail = trailing(remediated=0, entry=uuid.UUID(int=0), second='')
        _, rows, _ = self.run_artifact([self.write(detection_file(tail=tail))])
        self.assertEqual((rows[0][2], rows[0][14], rows[0][15]), ('', '', ''))

    def test_undocumented_codes_kept_as_stored(self):
        _, rows, _ = self.run_artifact([self.write(detection_file(severity=3, category=51))])
        self.assertEqual(rows[0][5:7], ('3', '51'))

    def test_count_mismatch_is_noted(self):
        _, rows, _ = self.run_artifact([self.write(detection_file(count=2))])
        self.assertEqual(rows[0][17], 'threat set counts 2 resources; 1 read')
        self.assertTrue(any('threat set counts 2' in line for line in self.logged))

    def test_truncated_file_is_reported_with_a_note(self):
        data = detection_file()
        _, rows, _ = self.run_artifact([self.write(data[:len(data) - 300])])
        self.assertEqual(rows[0][3], 'Test:Win32/Sample')
        self.assertEqual(rows[0][0], '')
        self.assertIn('no detection time at its position after the last resource', rows[0][17])

    def test_wrong_type_at_a_position_is_blank(self):
        tail = trailing().replace(text('HOST\\tester'), u32(5), 1)
        _, rows, _ = self.run_artifact([self.write(detection_file(tail=tail))])
        self.assertEqual(rows[0][12], '')
        self.assertEqual(rows[0][17], 'user position holds type 0x06, not 0x15')

    def test_guid_differs_from_name(self):
        data = detection_file(detection_id=uuid.UUID(int=5))
        _, rows, _ = self.run_artifact([self.write(data)])
        self.assertEqual(rows[0][17], 'detection GUID differs from the file name')

    def test_two_volumes_and_decoys(self):
        first = self.write(detection_file())
        second = self.write(detection_file(threat_name='Test:Win32/Other'), volume='D')
        decoy = self.write(detection_file(), folder='ProgramData/Other/DetectionHistory/06')
        not_guid = self.write(detection_file(), name='History.Log')
        folder = self.root/'C'/FOLDER/'07'
        folder.mkdir()
        _, rows, sources = self.run_artifact([first, second, decoy, not_guid, folder])
        self.assertEqual([row[3] for row in rows], ['Test:Win32/Sample', 'Test:Win32/Other'])
        self.assertEqual(sources.splitlines(), [str(first), str(second)])

    def test_paths_pattern(self):
        pattern, = artifact.__artifacts_v2__['defenderDetectionHistory']['paths']
        hit = f'root/p3_lba1026048_basic_data_partition/{FOLDER}/{NAME}'
        self.assertTrue(fnmatch.fnmatchcase(hit, pattern))
        self.assertTrue(fnmatch.fnmatchcase(f'root/{FOLDER}/{NAME}', pattern))
        self.assertFalse(fnmatch.fnmatchcase(f'root/{FOLDER}', pattern))
        self.assertFalse(fnmatch.fnmatchcase(
            'root/ProgramData/Microsoft/Windows Defender/Scans/History/Service/History.Log',
            pattern))


if __name__ == '__main__':
    unittest.main()
