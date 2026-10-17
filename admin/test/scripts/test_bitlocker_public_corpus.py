"""Byte-preserving public corpus checks against independently recorded fields."""

import json
import pathlib
import sys
import unittest
import zipfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import bitlocker_metadata as bde  # pylint: disable=wrong-import-position

DATA = REPO_ROOT / 'admin/test/cases/data/bitlockerMetadata'


class PublicReferenceMatrixTest(unittest.TestCase):
    def test_ctf_ranges_match_independent_reader_observations(self):
        sample = json.loads((DATA / 'public_ctf_gteksd.json').read_text(encoding='utf-8'))
        fixture = DATA / 'testdata.bitlockerMetadata.bitlockerKeyProtectors.casepublic_ctf_gteksd.zip'
        with zipfile.ZipFile(fixture) as archive:
            self.check_sample(archive, sample)

    def test_public_ranges_match_independent_reader_observations(self):
        observations = json.loads((DATA / 'public_reference_matrix.json').read_text(encoding='utf-8'))
        fixture = DATA / 'testdata.bitlockerMetadata.bitlockerKeyProtectors.casepublic_reference_matrix.zip'
        with zipfile.ZipFile(fixture) as archive:
            for sample in observations['inputs']:
                with self.subTest(source=sample['name']):
                    self.check_sample(archive, sample)

    def check_sample(self, archive, sample):
        prefix = sample['name'] + '/' + sample.get('volume', 'lba0') + '/$BitLocker/'
        files = {path.rsplit('/', 1)[-1]: archive.read(path) for path in archive.namelist()
                 if path.startswith(prefix) and not path.endswith('/')}
        result = bde.analyze_capture(json.loads(files['ranges.json']), files)
        expected = sample['expected']
        self.assertEqual(result['manifest']['volume_offset'], sample.get('volume_offset', 0))
        self.assertEqual(result['header']['layout'], expected['layout'])
        self.assertEqual(result['header']['sector_size'], expected['sector_size'])
        self.assertEqual(len(result['copies']), len(expected['copies']))
        for actual, reference in zip(result['copies'], expected['copies']):
            self.assertEqual(actual['number'], reference['number'])
            self.assertEqual(actual['offset'], reference['offset'])
            self.assertEqual(actual['valid'], reference['valid'])
            if not reference['valid']:
                self.assertEqual(actual['protectors'], [])
                continue
            for key in ('volume_id', 'created_raw', 'current_state', 'next_state'):
                self.assertEqual(actual[key], reference[key])
            self.assertEqual(actual['method_raw'] & 0xffff, reference['method'])
            self.assertEqual([{key: item[key] for key in ('id', 'type', 'modified_raw')}
                              for item in actual['protectors']], reference['protectors'])
            self.assertTrue(all(not p['policies'] for p in actual['protectors']))
        if sample['name'] == 'dfvfs_bdetogo':
            self.assertIsNone(result['selected'])
            self.assertEqual([b['status'] for b in result['copies']], ['CRC32 mismatch'] * 3)
        if sample['name'] == 'dissect_vista':
            self.assertIsNone(result['selected'])
            self.assertEqual(result['copies'], [])
        if sample['name'] == 'dissect_decrypted':
            self.assertEqual(bde.METHODS[result['selected']['method_raw'] & 0xffff], 'None')


if __name__ == '__main__':
    unittest.main()
