"""BitLocker Key Protectors: rows built from what the vendored qnxprobe reads.

Two sources: the BitLocker fixture the raw-image tests use, read through the real
FileSeekerRaw, locked and opened; and two protector setups Windows 11 wrote for a test
VM's system volume (admin/test/data/bitlocker_tpm, from qnxprobe's fixtures), whose
TPM protectors manage-bde listed with PCRs 7, 11 and 0, 2, 4, 11.
"""
import gzip
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.raw_image import FileSeekerRaw, ImageKeys  # pylint: disable=wrong-import-position
from scripts.vendor import qnxprobe  # pylint: disable=wrong-import-position
from scripts.artifacts.bitlockerMetadata import protector_rows  # pylint: disable=wrong-import-position

RAW = REPO_ROOT / 'admin' / 'test' / 'data' / 'raw_images'
TPM = REPO_ROOT / 'admin' / 'test' / 'data' / 'bitlocker_tpm'
WINDOWS_NAMES = {'Numerical Password': 'recovery password', 'TPM': 'TPM'}


class _Ranges:
    """The captured header and metadata at their volume offsets, zeros elsewhere."""

    def __init__(self, parts, size):
        self.parts, self.size, self.pos = parts, size, 0

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def tell(self):
        return self.pos

    def read(self, n=-1):
        end = self.size if n is None or n < 0 else min(self.size, self.pos + n)
        out = bytearray(max(0, end - self.pos))
        for start, data in self.parts:
            lo, hi = max(start, self.pos), min(start + len(data), end)
            if lo < hi:
                out[lo - self.pos:hi - self.pos] = data[lo - start:hi - start]
        self.pos = max(self.pos, end)
        return bytes(out)


def _tpm_volume(state, info):
    with gzip.open(TPM / f'{state}.bin.gz', 'rb') as handle:
        raw = handle.read()
    parts = [(0, raw[:512])] + [(off, raw[512 + i * 65536:512 + (i + 1) * 65536])
                                for i, off in enumerate(info['metadata_offsets'])]
    volume = qnxprobe.BitLocker.open(_Ranges(parts, info['partition_size']), 0,
                                     info['partition_size'])
    return {'name': state, 'kind': 'bitlocker', 'bitlocker': volume.facts()}


class TpmProtectors(unittest.TestCase):

    def test_each_protector_is_what_manage_bde_listed(self):
        with open(TPM / 'manifest.json', encoding='utf-8') as handle:
            states = json.load(handle)['states']
        for state, info in states.items():
            rows = protector_rows([_tpm_volume(state, info)])
            got = sorted((r[4], r[3], r[5]) for r in rows)
            want = sorted((w['id'], WINDOWS_NAMES[w['type']],
                           ', '.join(map(str, w['pcrs'])) if w['pcrs'] else '')
                          for w in info['windows'])
            self.assertEqual(got, want, state)
            self.assertTrue(all(r[9] == 'Locked' for r in rows))
            self.assertTrue(all(r[0] and r[1] for r in rows), 'both times are filled')

    def test_pcr_meaning_follows_the_pcrs(self):
        with open(TPM / 'manifest.json', encoding='utf-8') as handle:
            info = json.load(handle)['states']['01-tpm-default']
        tpm = [r for r in protector_rows([_tpm_volume('01-tpm-default', info)]) if r[3] == 'TPM']
        self.assertEqual(tpm[0][6], '7: Secure Boot State; 11: BitLocker access control')

    def test_disagreeing_pcr_lists_name_neither(self):
        facts = {'protectors': [{'kind': 'TPM', 'id': 'X', 'pcrs': None, 'pcrs_disagree': True}]}
        row = protector_rows([{'name': 'v', 'bitlocker': facts}])[0]
        self.assertEqual(row[5], 'Not read: the two stored PCR lists disagree')
        self.assertEqual(row[6], '')

    def test_a_volume_with_no_protectors_still_gets_a_row(self):
        facts = {'protectors': [], 'why': 'its metadata is in the Windows Vista layout, which this does not read'}
        rows = protector_rows([{'name': 'v', 'bitlocker': facts}, {'name': 'plain', 'kind': 'ntfs'}])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0][9].startswith('Locked: its metadata is in the Windows Vista layout'))


class RawImageProtectors(unittest.TestCase):
    """The same rows through the seeker DLEAPP uses for raw images."""

    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp()
        cls.image = os.path.join(cls.work, 'bitlocker-xts128.img')
        with gzip.open(RAW / 'bitlocker-xts128.img.gz', 'rb') as src, open(cls.image, 'wb') as dst:
            shutil.copyfileobj(src, dst)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def _rows(self, keys=None):
        seeker = FileSeekerRaw(self.image, tempfile.mkdtemp(dir=self.work), password=keys)
        self.addCleanup(seeker.cleanup)
        return protector_rows(seeker.volumes)

    def test_locked_volume_lists_its_protectors(self):
        rows = self._rows()
        self.assertEqual(sorted(r[3] for r in rows), ['password', 'recovery password', 'startup key'])
        self.assertTrue(all(r[9] == 'Locked' for r in rows))
        self.assertTrue(all(r[5] == '' for r in rows), 'no TPM, so no PCRs')

    def test_opened_volume_says_by_what(self):
        rows = self._rows(ImageKeys(bitlocker_keys=[str(RAW / 'bitlocker-xts128.BEK')]))
        self.assertTrue(rows)
        self.assertTrue(all(r[9] == 'Opened with its startup key' for r in rows))


if __name__ == '__main__':
    unittest.main()
