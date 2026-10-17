"""Boundary, PCR and raw/E01 integration tests for the metadata inventory."""

import copy
import gzip
import hashlib
import json
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from admin.test.scripts.bitlocker_fixture import (  # pylint: disable=wrong-import-position
    OFFSETS, RAW_TIME, TPM_GUID, block, capture_result, volume, write_capture, protector_variants)
from admin.test.scripts.test_raw_image_seeker import write_ewf  # pylint: disable=wrong-import-position
from scripts import bitlocker_metadata as bde  # pylint: disable=wrong-import-position
from scripts.artifacts import bitlockerMetadata as artifact  # pylint: disable=wrong-import-position
from scripts.raw_image import FileSeekerRaw, ImageKeys  # pylint: disable=wrong-import-position


class MetadataTest(unittest.TestCase):
    def parsed(self, **kwargs):
        manifest, files = capture_result(volume(**kwargs))
        return bde.analyze_capture(manifest, files)

    def test_three_crc_valid_copies_and_pcr_0_2_11(self):
        result = self.parsed()
        self.assertEqual([b['valid'] for b in result['copies']], [True] * 3)
        self.assertTrue(result['copies_agree'])
        self.assertEqual(result['selected']['method_raw'], 0x8005)
        tpm = result['selected']['protectors'][0]
        self.assertEqual(tpm['id'], str(TPM_GUID))
        self.assertEqual(tpm['policies'][0]['pcrs'], [0, 2, 11])
        self.assertEqual(tpm['policies'][0]['status'], 'outer and inner PCR bitmaps agree')
        self.assertEqual(tpm['policies'][0]['offset'], OFFSETS[0] + 112 + 52 + 36 + 8)

    def test_pcr_7_11_and_zero_bitmap(self):
        for bitmap, expected in ((0x880, [7, 11]), (0, [])):
            with self.subTest(bitmap=bitmap):
                self.assertEqual(self.parsed(bitmap=bitmap)['selected']['protectors'][0]
                                 ['policies'][0]['pcrs'], expected)

    def test_a_disagreement_is_not_a_successful_pcr_decode(self):
        p = self.parsed(inner=0x880)['selected']['protectors'][0]['policies'][0]
        self.assertEqual(p['pcrs'], [])
        self.assertIn('disagree', p['status'])
        self.assertEqual(p['bitmap'], 0x805)

    def test_tpm_blob_truncation_and_an_unknown_inner_layout(self):
        for payload in (b'', b'\x05\x08\x00', struct.pack('<I', 0x805) + b'opaque'):
            with self.subTest(payload=payload):
                parsed = bde.tpm_policy(payload)
                self.assertIn('status', parsed)
        self.assertEqual(bde.tpm_policy(struct.pack('<I', 0x805) + b'opaque')['pcrs'], [0, 2, 11])

    def test_crc_failure_falls_back_without_reading_bad_copy_protectors(self):
        result = self.parsed(copies=[block(bad_crc=True), block(), block()])
        self.assertEqual(result['selected']['number'], 2)
        self.assertEqual(result['copies'][0]['protectors'], [])
        self.assertEqual(result['copies'][0]['status'], 'CRC32 mismatch')

    def test_all_bad_copies_still_report_their_locations(self):
        result = self.parsed(copies=[block(bad_crc=True)] * 3)
        self.assertIsNone(result['selected'])
        self.assertEqual(len(result['copies']), 3)

    def test_different_valid_datasets_are_not_silently_reconciled(self):
        result = self.parsed(copies=[block(), block(counter=2), block()])
        self.assertFalse(result['copies_agree'])
        self.assertEqual(result['selected']['number'], 1)

    def test_partial_capture_holds_one_full_information_and_crc(self):
        result = self.parsed(truncated=8192)
        self.assertTrue(result['copies'][0]['valid'])
        self.assertEqual(result['copies'][0]['capture_status'], 'partial capture')
        self.assertEqual(result['copies'][1]['captured'], 0)
        self.assertEqual(result['copies'][2]['status'], 'not captured')

    def test_unknown_entry_types_keep_their_numbers_and_offsets(self):
        result = self.parsed(unknown=True)
        entry = result['selected']['entries'][-1]
        self.assertEqual((entry['role'], entry['type']), (0x1234, 0x5678))
        self.assertEqual(entry['size'], 21)

    def test_clear_protector_is_an_observation_not_an_unlock(self):
        result = self.parsed(clear=True)
        self.assertEqual([p['type'] for p in result['selected']['protectors']], [0x100, 0x800, 0])
        self.assertNotIn('fvek', result)

    def test_a_bad_entry_does_not_become_a_good_copy_after_a_good_crc(self):
        result = self.parsed(broken_entry=True)
        self.assertIsNone(result['selected'])
        self.assertIn('malformed entries', result['copies'][0]['status'])

    def test_data_and_manifest_must_agree(self):
        manifest, files = capture_result(volume())
        with self.subTest('hash'):
            bad = dict(files)
            bad['metadata-1.bin'] = b'wrong'
            with self.assertRaises(ValueError):
                bde.analyze_capture(manifest, bad)
        with self.subTest('offset'):
            bad = copy.deepcopy(manifest)
            bad['ranges'][1]['volume_offset'] += 1
            with self.assertRaises(ValueError):
                bde.analyze_capture(bad, files)

    def test_malformed_manifests_fail_with_a_bounded_validation_error(self):
        manifest, files = capture_result(volume())
        for bad in (None, [], {}, dict(manifest, ranges=None),
                    dict(manifest, ranges=[None]), dict(manifest, volume_size=-1)):
            with self.subTest(manifest=bad):
                with self.assertRaises(ValueError):
                    bde.analyze_capture(bad, files)

    def test_invalid_header_sizes_and_versions_do_not_raise_or_scan(self):
        good = bytearray(block())
        for offset, fmt, value in ((8, '<H', 65535), (10, '<H', 1), (72, '<I', 0xffffffff)):
            bad = bytearray(good)
            struct.pack_into(fmt, bad, offset, value)
            self.assertFalse(bde.parse_block(bad, 4096, 1)['valid'])

    def test_capture_reads_only_the_header_and_three_bounded_ranges(self):
        raw, calls = volume(), []

        def read_at(offset, length):
            calls.append((offset, length))
            return raw[offset:offset + length]

        bde.capture_ranges(read_at, 0, len(raw), len(raw), 'test.img', 'lba0')
        self.assertEqual(calls, [(0, 512)] + [(o, 65536) for o in OFFSETS])

    def test_filetime_is_utc_and_zero_and_overflow_are_not_events(self):
        self.assertEqual(bde.filetime(RAW_TIME).isoformat(), '2025-01-01T00:00:00+00:00')
        self.assertIsNone(bde.filetime(0))
        self.assertIsNone(bde.filetime(0xffffffffffffffff))


class ContextForTest:
    """No global Context mutation is needed to exercise undecorated artifacts."""

    def __init__(self, root):
        self.root = pathlib.Path(root)

    def get_files_found(self):
        return [str(p) for p in self.root.rglob('*') if p.is_file()]

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


class ArtifactRowsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        write_capture(self.root, volume(), volume_name='volume-a')
        self.context = ContextForTest(self.root)

    def rows(self, function):
        return getattr(artifact, function).__wrapped__(self.context)

    def test_one_compact_artifact_deduplicates_copies_and_explains_pcrs(self):
        self.assertEqual(list(artifact.__artifacts_v2__), ['bitlockerKeyProtectors'])
        headers, rows, source = self.rows('bitlockerKeyProtectors')
        self.assertEqual(len(headers), 6)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(len(row) == len(headers) for row in rows))
        tpm, recovery = rows
        self.assertEqual((tpm[1], tpm[3]), ('TPM', '0, 2, 11'))
        self.assertIn('0: Core firmware code', tpm[4])
        self.assertIn('11: BitLocker access control', tpm[4])
        self.assertEqual(recovery[3:5], ('', ''))
        self.assertEqual(source, 'volume-a/$BitLocker/ranges.json')
        self.assertNotIn(self.temp.name, repr(rows))
        self.assertTrue(all(row[5] == 'Validated' for row in rows))

    def test_two_volumes_double_rows_without_merging_identical_guids(self):
        old = self.rows('bitlockerKeyProtectors')[1]
        write_capture(self.root, volume(bitmap=0x880), source='second.img', volume_name='volume-b')
        new = self.rows('bitlockerKeyProtectors')[1]
        self.assertEqual(len(new), len(old) * 2)
        self.assertTrue(all(row in new for row in old))
        self.assertEqual({r[3] for r in new if r[1] == 'TPM'}, {'0, 2, 11', '7, 11'})
        self.assertEqual(len({r[0] for r in new}), 2)

    def test_same_protector_with_different_policies_is_not_collapsed(self):
        raw = volume(copies=[block(), block(bitmap=0x880), block(bitmap=0x880)])
        write_capture(self.root, raw, volume_name='volume-a')
        rows = self.rows('bitlockerKeyProtectors')[1]
        self.assertEqual(len(rows), 3)
        self.assertEqual({r[3] for r in rows if r[1] == 'TPM'}, {'0, 2, 11', '7, 11'})
        self.assertTrue(all('metadata copies differ' in r[5] for r in rows))
        self.assertIn('Copies 1', rows[0][5])

    def test_partial_metadata_and_all_bad_copies_stay_visible(self):
        for raw, count, text in [(volume(truncated=8192), 2, 'partial metadata'),
                                 (volume(copies=[block(bad_crc=True)] * 3), 1, 'CRC32 mismatch')]:
            with self.subTest(status=text):
                for path in (self.root / 'volume-a' / '$BitLocker').iterdir():
                    path.unlink()
                write_capture(self.root, raw, volume_name='volume-a')
                rows = self.rows('bitlockerKeyProtectors')[1]
                self.assertEqual(len(rows), count)
                self.assertTrue(all(text in r[5] for r in rows))
        self.assertEqual(rows[0][1], 'Not assessed')
        self.assertEqual(rows[0][2:5], ('', '', ''))

    def test_pcr_conflict_zero_and_outer_only_qualifications_survive(self):
        for kwargs, profile, warning in [({'inner': 0x880}, 'Not decoded', 'disagree'),
                                         ({'bitmap': 0}, 'None selected', 'Validated')]:
            with self.subTest(kwargs=kwargs):
                write_capture(self.root, volume(**kwargs), volume_name='volume-a')
                tpm = self.rows('bitlockerKeyProtectors')[1][0]
                self.assertEqual(tpm[3], profile)
                self.assertIn(warning, tpm[5])
        profiles, meanings, warnings = artifact._policy_fields([bde.tpm_policy(bytes.fromhex('05080000') + b'opaque')])  # pylint: disable=protected-access
        self.assertEqual(profiles, '0, 2, 11')
        self.assertIn('11: BitLocker access control', meanings)
        self.assertIn('outer bitmap only', warnings[0])

    def test_standard_protector_variants_and_unknown_codes_remain_visible(self):
        write_capture(self.root, volume(protectors=protector_variants()), volume_name='volume-a')
        rows = self.rows('bitlockerKeyProtectors')[1]
        expected = {'Clear key', 'TPM', 'External key', 'TPM and external startup key',
                    'TPM and PIN', 'TPM, PIN and external startup key', 'Recovery password',
                    'Password', 'Unknown (0x1234)'}
        self.assertEqual(len(rows), 9)
        self.assertEqual({r[1] for r in rows}, expected)
        for row in rows:
            if row[1].startswith('TPM'):
                self.assertEqual(row[3], '7, 11')
                self.assertIn('7: Secure Boot policy', row[4])
            else:
                self.assertEqual(row[3:5], ('', ''))

    def test_a_manifest_cannot_direct_the_parser_to_another_file(self):
        manifest_path = self.root / 'volume-a' / '$BitLocker' / 'ranges.json'
        meta = json.loads(manifest_path.read_text())
        meta['ranges'][1]['file'] = '../outside.bin'
        manifest_path.write_text(json.dumps(meta))
        with mock.patch.object(artifact, 'logfunc') as log:
            self.assertEqual(self.rows('bitlockerKeyProtectors')[1], [])
            self.assertTrue(log.called)


class ImageIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.log_patch = mock.patch('scripts.raw_image.logfunc')
        self.log_patch.start()
        self.addCleanup(self.log_patch.stop)

    def seeker(self, path, keys=None):
        output = self.root / ('data-' + str(len(list(self.root.glob('data-*')))))
        output.mkdir()
        seeker = FileSeekerRaw(str(path), str(output), password=keys)
        self.addCleanup(seeker.cleanup)
        return seeker

    def test_locked_raw_and_segmented_e01_expose_the_same_metadata_bytes(self):
        raw = volume(base=1048576)
        image = self.root / 'disk.img'
        image.write_bytes(raw)
        segments = write_ewf(str(self.root), 'disk', raw, chunks_per_segment=20)
        self.assertGreater(len(segments), 1)
        for source in (image, pathlib.Path(segments[0]), pathlib.Path(segments[1])):
            with self.subTest(source=source.name):
                before = hashlib.sha256(source.read_bytes()).hexdigest()
                seeker = self.seeker(source)
                self.assertEqual(seeker.search('*/$BitLocker/*')[0].endswith('.bin'), True)
                found = seeker.search('*/$BitLocker/*')
                self.assertEqual(len(found), 5)
                data = {pathlib.Path(p).name: pathlib.Path(p).read_bytes() for p in found}
                self.assertEqual(data['volume-header.bin'], raw[1048576:1048576 + 512])
                result = bde.analyze_capture(json.loads(data.pop('ranges.json')), data)
                self.assertEqual(result['selected']['protectors'][0]['policies'][0]['pcrs'], [0, 2, 11])
                self.assertEqual(result['manifest']['volume_offset'], 1048576)
                self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())

    def test_metadata_does_not_pollute_a_normal_filesystem_glob(self):
        image = self.root / 'disk.img'
        image.write_bytes(volume())
        seeker = self.seeker(image)
        self.assertEqual(seeker.search('*'), [])
        self.assertIsNone(seeker.metadata_list)
        self.assertEqual(len(seeker.search('*/$BitLocker/*')), 5)
        self.assertEqual(seeker.search('*', force=True), [])

    def test_multiple_image_sources_keep_their_own_range_views(self):
        paths = []
        for number, bitmap in enumerate((0x805, 0x880)):
            image = self.root / f'volume-{number}.img'
            image.write_bytes(volume(bitmap=bitmap))
            paths.append(str(image))
        output = self.root / 'multi-data'
        output.mkdir()
        seeker = FileSeekerRaw(paths, str(output))
        self.addCleanup(seeker.cleanup)
        found = seeker.search('*/$BitLocker/*')
        self.assertEqual(len(found), 10)
        manifests = [json.loads(pathlib.Path(p).read_bytes()) for p in found if p.endswith('ranges.json')]
        self.assertEqual({m['source_image'] for m in manifests}, {'volume-0.img', 'volume-1.img'})
        self.assertEqual(len({m['volume_name'] for m in manifests}), 2)

    def test_existing_public_fixture_works_before_and_after_password_unlock(self):
        fixture = REPO_ROOT / 'admin/test/data/raw_images/bitlocker-xts128.img.gz'
        raw = gzip.decompress(fixture.read_bytes())
        image = self.root / 'fixture.img'
        image.write_bytes(raw)
        key = REPO_ROOT / 'admin/test/data/raw_images/bitlocker-xts128.BEK'
        results = []
        for keys in (None, ImageKeys(bitlocker_keys=[key.read_bytes()])):
            seeker = self.seeker(image, keys)
            found = seeker.search('*/$BitLocker/*')
            self.assertTrue(found)
            data = {pathlib.Path(p).name: pathlib.Path(p).read_bytes() for p in found}
            # Even a synthetic decryption fixture with no valid CRC is reported,
            # and its exact metadata bytes survive the decrypted wrapper.
            self.assertEqual(data['volume-header.bin'], raw[:512])
            results.append(data)
        self.assertEqual(results[0], results[1])


if __name__ == '__main__':
    unittest.main()
