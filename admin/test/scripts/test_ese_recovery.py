"""Pin scripts/ese_log (reading ESE transaction logs) and scripts/ese_recovery (replaying them
onto a database in memory).

The parser and replay tests build small logs and databases here, field by field, from the
layouts the two modules cite. The tests at the end use the two UAL corpus images
(szechuan_dc01_server2012r2 and ou_ransomware_server2022) when their Sum folders are staged
at REAL_ROOT, and skip otherwise: nothing derived from them is committed.
"""
import hashlib
import json
import os
import pathlib
import random
import shutil
import struct
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import ese_log, ese_recovery, ese_rows
# pylint: enable=wrong-import-position

REAL_ROOT = pathlib.Path('/Users/alexisbrignoni/Downloads/ual-replay-2026-10-14')
# Windows/NTDS of the three domain controller images, copied out read-only; see RealNtds.
NTDS_ROOT = pathlib.Path('/Users/alexisbrignoni/Downloads/dleapp-build3-2026-10-17/ese8k/orig')

SIGN_LOG = bytes(range(1, 29))
SIGN_DB = bytes(range(101, 129))
PAGE = 4096
LEAF_FLAGS = 0x2000 | 0x0002 | 0x0001        # new checksum format, leaf, root
OBJID = 5
PGNO = 3


# ---------------------------------------------------------------- building logs

def log_header(generation, tm_create=b'\x01' * 8, tm_prev=b'\x00' * 8, csec=8, sign=SIGN_LOG, attachments=b''):
    header = bytearray(PAGE)
    struct.pack_into('<iHHHH', header, 4, generation, PAGE, 1, csec, PAGE)
    header[16:24] = tm_create
    header[24:32] = tm_prev
    struct.pack_into('<III', header, 32, 8, 4000, 4)
    header[44:72] = sign
    struct.pack_into('<I', header, 667, 3)
    header[671:671 + len(attachments)] = attachments          # rgbAttach, src/inc/log.hxx#L231
    struct.pack_into('<I', header, 0, ese_log.checksum_old(bytes(header)))
    return header


def segment(generation, isec, body):
    seg = bytearray(PAGE)
    struct.pack_into('<HHi', seg, 8, 0, isec, generation)
    struct.pack_into('<I', seg, 36, 0x2000)
    seg[40:40 + len(body)] = body
    struct.pack_into('<Q', seg, 0, ese_log.checksum_new(bytes(seg), isec))
    return seg


def log_file(generation, bodies, csec=8, **kwargs):
    """A log whose segments 1.. hold `bodies` (one bytes per segment); the rest is zeros."""
    data = log_header(generation, csec=csec, **kwargs)
    for isec, body in enumerate(bodies, start=1):
        data += segment(generation, isec, body)
    data += bytes(PAGE * (csec - 1 - len(bodies)))
    return bytes(data)


def attach_info(dbid, lgpos_attach, lgpos_consistent, sign_db=SIGN_DB, names='C:\\x\\ntds.dit'):
    """One ATTACHINFO (src/inc/log.hxx#L85-L101) for a log header's attachment list."""
    name = names.encode('utf-16-le') + b'\0\0'
    return (struct.pack('<BBHqII', dbid, 0x20, len(name), 1000, 50, 0)
            + struct.pack('<HHi', lgpos_attach[2], lgpos_attach[1], lgpos_attach[0])
            + struct.pack('<HHi', lgpos_consistent[2], lgpos_consistent[1], lgpos_consistent[0])
            + sign_db + name)


def begin0(procid):
    return struct.pack('<BHBI', 8, procid, 0x20, 0x1000)


def begin(procid, level_from=1, levels=1):
    """LRBEGIN: levelBeginFrom in the low four bits, clevelsToBegin in the high four
    (src/inc/logapi.hxx#L1376-L1386)."""
    return struct.pack('<BHB', 5, procid, level_from | levels << 4)


def commit(procid, level_to=1):
    return struct.pack('<BHB', 6, procid, level_to)


def macro(lrtyp, procid, dbtime):
    """LRMACROBEGIN (11) or LRMACROEND (12 commit, 13 abort), src/inc/logapi.hxx#L1474-L1493."""
    return struct.pack('<BHq', lrtyp, procid, dbtime)


def trace(procid=5):
    return struct.pack('<BHH', 22, procid, 0)         # LRTRACE with no text, src/inc/logapi.hxx#L2059-L2077


def page_op(lrtyp, dbid, pgno, dbtime, before, size, others=(), procid=5, level=2):
    """A record of `size` fixed bytes starting with LRPAGE_ (src/inc/logapi.hxx#L377-L423),
    every variable length zero, with (offset, pgno) pairs written after LRPAGE_."""
    data = bytearray(size)
    struct.pack_into('<BHBIqqIBHB', data, 0, lrtyp, procid, dbid, pgno, dbtime, before, 0x1000, level, 1, 0)
    for offset, number in others:
        struct.pack_into('<I', data, offset, number)
    return bytes(data)


def delete(dbid, pgno, dbtime, before, **kwargs):
    return page_op(35, dbid, pgno, dbtime, before, 44, **kwargs)        # LRDELETE, LRNODE_ only


def split2(dbid, pgno, dbtime, new, right, parent, **kwargs):
    # LRSPLITNEW, 110 fixed bytes: pgnoNew 32, pgnoRight 36, pgnoParent 48 (src/inc/logapi.hxx#L873-L940)
    return page_op(62, dbid, pgno, dbtime, dbtime - 1, 110, ((32, new), (36, right), (48, parent)), **kwargs)


def merge2(dbid, pgno, dbtime, right, left, parent, **kwargs):
    # LRMERGENEW, 96 fixed bytes: pgnoRight 32, pgnoLeft 44, pgnoParent 56 (src/inc/logapi.hxx#L954-L998)
    return page_op(63, dbid, pgno, dbtime, dbtime - 1, 96, ((32, right), (44, left), (56, parent)), **kwargs)


def commit0(procid):
    return struct.pack('<BHBI', 9, procid, 0, 0x1002)


def rollback(procid):
    return struct.pack('<BHB', 7, procid, 1)


def attach(dbid, lgpos_consistent, sign_db=SIGN_DB, sign_log=SIGN_LOG, path='C:\\x\\Current.mdb'):
    name = path.encode('utf-16-le') + b'\0\0'
    return (struct.pack('<BHBI', 15, 0, dbid, 0) + struct.pack('<HHi', lgpos_consistent[2],
            lgpos_consistent[1], lgpos_consistent[0]) + sign_db + sign_log
            + struct.pack('<HB', len(name), 0x08) + name)


def node_header(lrtyp, dbid, pgno, dbtime, before, iline, procid=5, versioned=True, objid=OBJID):
    return struct.pack('<BHBIqqIBHB', lrtyp, procid, dbid, pgno, dbtime, before, 0x1000, 2,
                       iline, 0x01 if versioned else 0) + struct.pack('<III', 7, 2, objid)


def replace_d(dbid, pgno, dbtime, before, iline, diff, cb_new, procid=5, fdiff2=True, **kwargs):
    return node_header(34, dbid, pgno, dbtime, before, iline, procid, **kwargs) + \
        struct.pack('<HHH', (0x8000 if fdiff2 else 0) | len(diff), 0, cb_new) + diff


def replace(dbid, pgno, dbtime, before, iline, data, procid=5):
    return node_header(33, dbid, pgno, dbtime, before, iline, procid) + \
        struct.pack('<HHH', len(data), 0, len(data)) + data


def insert(dbid, pgno, dbtime, before, iline, suffix, data, procid=5, prefix=b''):
    """LRINSERT: cbSuffix, cbPrefix, cbData, then prefix, suffix and data
    (src/inc/logapi.hxx#L637-L659)."""
    return node_header(29, dbid, pgno, dbtime, before, iline, procid) + \
        struct.pack('<HHH', len(suffix), len(prefix), len(data)) + prefix + suffix + data


def set_db_version(dbid, version):
    return struct.pack('<BBIII', 92, dbid, *version)


def detach(dbid, path='C:\\x\\Current.mdb'):
    name = path.encode('utf-16-le') + b'\0\0'
    return struct.pack('<BHBHB', 16, 0, dbid, len(name), 0x10) + name


def diff2(ib, new, same_length=True, old_length=None):
    """One DIFFHDR2 entry (src/inc/logapi.hxx#L36-L65) replacing bytes at ib."""
    if same_length:
        return struct.pack('<HBB', ib, 0x20, len(new)) + new
    return struct.pack('<HBBB', ib, 0, len(new), old_length) + new


# ---------------------------------------------------------------- building a database

def node(suffix, data):
    return struct.pack('<H', len(suffix)) + suffix + data


def leaf_page(pgno, dbtime, nodes, external=b'', flags=LEAF_FLAGS, node_flags=0, layout=None, size=PAGE):
    """A small-format leaf page: tag 0 is the external header, then one tag per node. The
    data is laid out from the start of the data area in tag order, or in the order of the
    tag numbers listed in `layout`."""
    page = bytearray(size)
    lines = [(external, 0)] + [(n, node_flags) for n in nodes]
    ib = 0
    for itag in layout or range(len(lines)):
        data, line_flags = lines[itag]
        page[40 + ib:40 + ib + len(data)] = data
        struct.pack_into('<HH', page, size - 4 * (itag + 1), len(data), ib | (line_flags << 13))
        ib += len(data)
    used = ib + 4 * len(lines)
    struct.pack_into('<qIIIHHHHI', page, 8, dbtime, 0, 0, OBJID, size - 40 - used, 0, ib, len(lines), flags)
    struct.pack_into('<Q', page, 0, ese_log.checksum_new(bytes(page), pgno))
    return page


def build_database(pages, state=2, lgpos_attach=(1, 1, 0), lgpos_consistent=(1, 0, 8),
                   gens=(1, 1), version=(0x620, 20, 0), committed=None, page_size=PAGE):
    header = bytearray(page_size)
    struct.pack_into('<IIi', header, 4, 0x89abcdef, version[0], 0)
    struct.pack_into('<q', header, 16, 100)
    header[24:52] = SIGN_DB
    struct.pack_into('<I', header, 52, state)
    struct.pack_into('<HHi', header, 56, lgpos_consistent[2], lgpos_consistent[1], lgpos_consistent[0])
    struct.pack_into('<HHi', header, 80, lgpos_attach[2], lgpos_attach[1], lgpos_attach[0])
    struct.pack_into('<I', header, 104, 1)
    header[108:136] = SIGN_LOG
    struct.pack_into('<I', header, 232, version[1])
    struct.pack_into('<I', header, 236, page_size)
    struct.pack_into('<ii', header, 296, *gens)
    struct.pack_into('<i', header, 416, gens[1] if committed is None else committed)
    struct.pack_into('<I', header, 644, version[2])
    struct.pack_into('<I', header, 0, ese_log.checksum_old(bytes(header)))
    out = header + header
    for pgno in range(1, max(pages) + 1):
        out += pages.get(pgno, bytes(page_size))
    return bytes(out)


def page_of(db_bytes, pgno, size=PAGE):
    return bytes(db_bytes[(pgno + 1) * size:(pgno + 2) * size])


def lines_of(page_bytes, pgno=PGNO):
    page = ese_recovery._Page(bytearray(page_bytes), 0, len(page_bytes), pgno, False)  # pylint: disable=protected-access
    return [page.line(itag) for itag in range(page.ctag_reserved, page.itag_mic_free)]


def run(db, bodies, generation=1):
    return ese_recovery.replay(db, {generation: ('Svc.log', log_file(generation, bodies))})


# ---------------------------------------------------------------- checksums

class Checksums(unittest.TestCase):
    def test_old_format_is_xor_after_first_word(self):
        block = bytearray(PAGE)
        struct.pack_into('<II', block, 0, 0xdeadbeef, 0x01020304)
        self.assertEqual(ese_log.checksum_old(bytes(block)), 0x89abcdef ^ 0x01020304)

    def test_new_format_ignores_its_own_first_eight_bytes(self):
        block = bytearray(random.Random(1).randbytes(PAGE))
        first = ese_log.checksum_new(bytes(block), 7)
        block[0:8] = b'\xff' * 8
        self.assertEqual(ese_log.checksum_new(bytes(block), 7), first)

    def test_page_number_is_folded_into_the_xor_half(self):
        block = random.Random(2).randbytes(PAGE)
        self.assertEqual(ese_log.checksum_new(block, 7) ^ ese_log.checksum_new(block, 4), 7 ^ 4)

    def test_one_flipped_bit_is_located_by_the_ecc_as_ese_corrects_it(self):
        # FECCErrorIsCorrectable and IbitCorrupted, src/checksum/checksum.cxx#L347-L414: for one flipped
        # bit the two ECC halves differ in a pattern that names the bit.
        block = bytearray(random.Random(3).randbytes(PAGE))
        before = ese_log.checksum_new(bytes(block), 9) >> 32
        for bit in (64, 1000, 8 * PAGE - 1, 12345):
            changed = bytearray(block)
            changed[bit // 8] ^= 1 << (bit % 8)
            ecc = before ^ (ese_log.checksum_new(bytes(changed), 9) >> 32)
            mask = (PAGE << 3) - 1
            self.assertEqual(((ecc >> 16) ^ ecc) & mask, mask, bit)
            self.assertEqual(ecc & 0xffff, bit)


# ---------------------------------------------------------------- the log reader

class LogReader(unittest.TestCase):
    def test_records_and_positions(self):
        # the rest of segment 1 is NOP fill, so the record in segment 2 carries the position
        # where the fill began (m_pbNext, src/ese/_log/logread.cxx#L2284-L2294)
        body = begin0(5) + commit0(5)
        header, records = ese_log.read_records(log_file(1, [body, begin0(6)]))
        self.assertEqual(header.generation, 1)
        self.assertEqual([(r.name, r.lgpos) for r in records],
                         [('Begin0', (1, 1, 0)), ('Commit0', (1, 1, 48)), ('Begin0', (1, 1, 56))])

    def test_a_record_after_nop_fill_keeps_the_fill_position(self):
        # m_pbNext stays on the NOPs while the reader moves to the next segment
        body = begin0(5) + b'\x00' * (PAGE - 40 - 8)
        _header, records = ese_log.read_records(log_file(1, [body, commit0(5)]))
        self.assertEqual(records[1].lgpos, (1, 1, 48))

    def test_fragments_are_joined(self):
        record = replace(1, 3, 10, 9, 0, b'x' * 5000)
        first = PAGE - 40 - 7
        rest = len(record) - first
        body1 = struct.pack('<BIH', 76, len(record), first) + record[:first]
        body2 = struct.pack('<BH', 77, rest) + record[first:]
        _header, records = ese_log.read_records(log_file(1, [body1, body2]))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].data, record)
        self.assertEqual(records[0].lgpos, (1, 1, 0))

    def test_an_older_segment_ends_the_log(self):
        data = bytearray(log_file(1, [begin0(5), commit0(5)]))
        data[3 * PAGE:4 * PAGE] = segment(0, 3, begin0(9))     # left over from an older generation
        _header, records = ese_log.read_records(bytes(data))
        self.assertEqual(len(records), 2)

    def test_data_after_the_end_is_corruption(self):
        data = bytearray(log_file(1, [begin0(5)]))
        data[3 * PAGE:4 * PAGE] = segment(1, 3, begin0(9))     # segment 2 is zeros
        with self.assertRaisesRegex(ese_log.LogError, 'after the end'):
            ese_log.read_records(bytes(data))

    def test_a_flipped_byte_fails_the_segment_checksum(self):
        data = bytearray(log_file(1, [begin0(5) + commit0(5)]))
        data[PAGE + 45] ^= 0xff
        with self.assertRaisesRegex(ese_log.LogError, 'segment 1 fails its checksum'):
            ese_log.read_records(bytes(data))

    def test_a_flipped_header_byte_fails(self):
        data = bytearray(log_file(1, [begin0(5)]))
        data[100] ^= 1
        with self.assertRaisesRegex(ese_log.LogError, 'header checksum'):
            ese_log.read_records(bytes(data))

    def test_an_unsized_record_type_is_refused(self):
        with self.assertRaisesRegex(ese_log.LogError, 'not sized'):
            ese_log.read_records(log_file(1, [bytes([60]) + b'\x01' * 20]))

    def test_the_old_lrck_format_is_refused(self):
        data = bytearray(log_file(1, [begin0(5)]))
        struct.pack_into('<I', data, 32, 7)
        struct.pack_into('<I', data, 0, ese_log.checksum_old(bytes(data[:PAGE])))
        with self.assertRaisesRegex(ese_log.LogError, 'LRCHECKSUM'):
            ese_log.LogHeader(bytes(data))


# ---------------------------------------------------------------- after images

class AfterImage(unittest.TestCase):
    def test_diffhdr2_same_length(self):
        self.assertEqual(ese_recovery.after_image(diff2(2, b'XY'), b'abcdef', True, PAGE), b'abXYef')

    def test_diffhdr2_different_length(self):
        self.assertEqual(ese_recovery.after_image(diff2(1, b'XYZ', False, 1), b'abcdef', True, PAGE),
                         b'aXYZcdef')

    def test_diffhdr_insert(self):
        diff = struct.pack('<HB', 0x4000 | 3, 2) + b'--'
        self.assertEqual(ese_recovery.after_image(diff, b'abcdef', False, PAGE), b'abc--def')

    def test_a_diff_past_its_data_is_refused(self):
        with self.assertRaises(ese_recovery.ReplayRefused):
            ese_recovery.after_image(diff2(5, b'XYZ', False, 9), b'abcdef', True, PAGE)


# ---------------------------------------------------------------- the replay

class Replay(unittest.TestCase):
    def setUp(self):
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        self.db = build_database({PGNO: self.page})
        self.attach = attach(1, (1, 0, 8))

    def test_replace_d_changes_the_record_and_the_page_dbtime(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit0(5)
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.refused)
        page = page_of(result.data, PGNO)
        self.assertEqual(struct.unpack_from('<q', page, 8)[0], 60)
        self.assertEqual([line for line, _ in lines_of(page)], [node(b'k1', b'AAAA'), node(b'k2', b'BZBB')])
        self.assertEqual([flags for _, flags in lines_of(page)], [0, 1])   # versioned: fNDVersion set
        self.assertEqual(struct.unpack_from('<Q', page, 0)[0], ese_log.checksum_new(page, PGNO))
        self.assertEqual(result.pages, [PGNO])
        self.assertEqual(page_of(result.data, -1) + page_of(result.data, 0),
                         self.db[:2 * PAGE])        # header and shadow left as stored

    def test_a_growing_replace_reorganizes_when_the_free_space_is_split(self):
        page = leaf_page(PGNO, 50, [node(b'k1', b'a' * 2000), node(b'k2', b'b' * 1900)])
        db = build_database({PGNO: page})
        body = begin0(5) + replace(1, PGNO, 60, 50, 0, b'c' * 2096) + commit0(5)
        result = run(db, [self.attach, body])
        self.assertIsNone(result.refused)
        changed = page_of(result.data, PGNO)
        self.assertEqual([line for line, _ in lines_of(changed)], [node(b'k1', b'c' * 2096), node(b'k2', b'b' * 1900)])
        # k2 moved down to the start of the data area, the grown k1 follows it
        self.assertEqual(struct.unpack_from('<HH', changed, PAGE - 12), (1904, 0))
        self.assertEqual(struct.unpack_from('<HH', changed, PAGE - 8), (2100, 1904 | 1 << 13))

    def test_a_growing_replace_moves_the_line(self):
        body = begin0(5) + replace(1, PGNO, 60, 50, 0, b'C' * 40) + commit0(5)
        page = page_of(run(self.db, [self.attach, body]).data, PGNO)
        self.assertEqual([line for line, _ in lines_of(page)], [node(b'k1', b'C' * 40), node(b'k2', b'BBBB')])
        cb_free, _unc, ib_mic_free = struct.unpack_from('<HHH', page, 28)
        self.assertEqual(ib_mic_free, len(node(b'k1', b'AAAA')) + len(node(b'k2', b'BBBB')) + 44)
        self.assertEqual(cb_free, PAGE - 40 - ib_mic_free - 12 + len(node(b'k1', b'AAAA')))

    def test_insert_shifts_the_tags(self):
        body = begin0(5) + insert(1, PGNO, 60, 50, 1, b'k15', b'NEW') + commit0(5)
        page = page_of(run(self.db, [self.attach, body]).data, PGNO)
        self.assertEqual([line for line, _ in lines_of(page)],
                         [node(b'k1', b'AAAA'), node(b'k15', b'NEW'), node(b'k2', b'BBBB')])
        self.assertEqual(struct.unpack_from('<H', page, 34)[0], 4)     # legacy itagState kept

    def test_a_dbtime_mismatch_refuses(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 49, 1, diff2(1, b'Z'), 4) + commit0(5)
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.data)
        self.assertIn('expects 49', result.refused)

    def test_a_change_already_on_the_page_is_skipped(self):
        body = begin0(5) + replace_d(1, PGNO, 50, 40, 1, diff2(1, b'Z'), 4) + commit0(5)
        result = run(self.db, [self.attach, body])
        self.assertEqual(result.skipped_newer, 1)
        self.assertEqual(result.data, self.db)

    def test_an_uncommitted_change_refuses(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4)
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.data)
        self.assertIn('never committed', result.refused)

    def test_a_rollback_refuses(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + rollback(5)
        self.assertIn('rolls back', run(self.db, [self.attach, body]).refused)

    def test_records_for_another_dbid_and_before_the_attach_are_not_applied(self):
        early = begin0(5) + replace_d(1, PGNO, 55, 50, 1, diff2(1, b'Q'), 4) + commit0(5)
        later = begin0(6) + replace_d(2, PGNO, 61, 50, 1, diff2(1, b'Q'), 4) + commit0(6)
        # segment 1 ends in NOP fill, so the attach in segment 2 carries the fill's position
        db = build_database({PGNO: self.page}, lgpos_attach=(1, 1, 40 + len(early)))
        result = run(db, [early, self.attach, later])
        self.assertIsNone(result.refused)
        self.assertEqual(result.data, db)

    def test_an_attach_of_another_database_is_refused(self):
        other = attach(1, (1, 0, 8), sign_db=b'\x07' * 28)
        self.assertIn('different database', run(self.db, [other]).refused)

    def test_an_unhandled_page_record_for_this_database_refuses(self):
        body = begin0(5) + node_header(32, 1, PGNO, 60, 50, 1) + commit0(5)    # FlagDelete
        self.assertIn('FlagDelete', run(self.db, [self.attach, body]).refused)

    def test_a_bad_page_checksum_refuses(self):
        broken = bytearray(self.page)
        broken[300] ^= 1
        db = build_database({PGNO: bytes(broken)})
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit0(5)
        self.assertIn('fails its checksum', run(db, [self.attach, body]).refused)

    def test_a_missing_or_foreign_log_refuses(self):
        self.assertIn('missing', ese_recovery.replay(self.db, {}).refused)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'Svc.log')
            with open(path, 'wb') as handle:
                handle.write(log_file(1, [self.attach], sign=b'\x09' * 28))
            logs, skipped = ese_recovery.find_logs(folder, ese_recovery.DatabaseHeader(self.db))
        self.assertEqual(logs, {})
        self.assertEqual(skipped, [('Svc.log', 'a different log signature')])

    def test_a_log_that_does_not_follow_the_one_before_refuses(self):
        db = build_database({PGNO: self.page}, gens=(1, 2))
        logs = {1: ('Svc00001.log', log_file(1, [self.attach], tm_create=b'\x02' * 8)),
                2: ('Svc.log', log_file(2, [begin0(5)], tm_prev=b'\x03' * 8))}
        self.assertIn('does not follow', ese_recovery.replay(db, logs).refused)

    def test_a_clean_database_is_returned_unchanged(self):
        db = build_database({PGNO: self.page}, state=3)
        result = run(db, [self.attach])
        self.assertEqual(result.data, db)
        self.assertEqual(result.summary(), 'not replayed: the header records clean shutdown')

    def test_replayed_database_reads_the_folder_and_never_writes(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit0(5)
        with tempfile.TemporaryDirectory() as folder:
            db_path = os.path.join(folder, 'Current.mdb')
            with open(db_path, 'wb') as handle:
                handle.write(self.db)
            with open(os.path.join(folder, 'Svc.log'), 'wb') as handle:
                handle.write(log_file(1, [self.attach, body]))
            before = {name: os.stat(os.path.join(folder, name)).st_mtime_ns for name in os.listdir(folder)}
            data, summary = ese_recovery.replayed_database(db_path)
            after = {name: os.stat(os.path.join(folder, name)).st_mtime_ns for name in os.listdir(folder)}
            with open(db_path, 'rb') as handle:
                self.assertEqual(handle.read(), self.db)
        self.assertEqual(before, after)
        self.assertIsNotNone(data)
        self.assertEqual(summary, 'replayed 1 change(s) from Svc.log onto 1 page(s) (0 already on the page)')


# ---------------------------------------------------------------- page rules, checked by hand

def page_header(page_bytes):
    """(cbFree, cbUncommittedFree, ibMicFree, itagState) of a page (src/inc/cpage.hxx#L992-L1010)."""
    return struct.unpack_from('<HHHH', page_bytes, 28)


def tags(page_bytes):
    """[(cb, ib with flags)] of every tag, tag 0 first."""
    count = struct.unpack_from('<H', page_bytes, 34)[0] & 0x0fff
    return [struct.unpack_from('<HH', page_bytes, PAGE - 4 * (itag + 1)) for itag in range(count)]


class PageRules(unittest.TestCase):
    """Each expectation is worked out by hand from CPAGE::Replace_ and Insert_
    (src/ese/cpage.cxx#L5211-L5461), ReorganizeData_ (src/ese/cpage.cxx#L5518-L5614) and the
    node layout of CdataNDIKeydataflagsToDataflags (src/ese/node.cxx#L233-L362)."""

    def setUp(self):
        # tag 0 empty; k1 (8 bytes) at ib 0; k2 (8 bytes) at ib 8; cbFree 4096-40-16-12
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        self.db = build_database({PGNO: self.page})
        self.attach = attach(1, (1, 0, 8))
        self.assertEqual(page_header(self.page), (4028, 0, 16, 3))

    def changed(self, record):
        result = run(self.db, [self.attach, begin0(5) + record + commit0(5)])
        self.assertIsNone(result.refused)
        return page_of(result.data, PGNO)

    def test_shrinking_the_last_line_gives_back_its_tail(self):
        # cbDiff 3 and the line ends at ibMicFree: ibMicFree -= 3, cbFree += 3, the line
        # stays where it was and the bytes past its new end are left as they were
        page = self.changed(replace(1, PGNO, 60, 50, 1, b'B'))
        self.assertEqual(page_header(page), (4031, 0, 13, 3))
        self.assertEqual(tags(page)[2], (5, 8 | 1 << 13))
        self.assertEqual(page[40 + 8:40 + 16], node(b'k2', b'B') + b'BBB')

    def test_shrinking_a_line_inside_the_page_keeps_ibmicfree(self):
        page = self.changed(replace(1, PGNO, 60, 50, 0, b'A'))
        self.assertEqual(page_header(page), (4031, 0, 16, 3))
        self.assertEqual(tags(page)[1], (5, 0 | 1 << 13))
        self.assertEqual(page[40:48], node(b'k1', b'A') + b'AAA')

    def test_an_insert_with_a_compressed_prefix(self):
        # node = prefix count, suffix count, suffix, data (no prefix bytes); flags
        # fNDCompressed | fNDVersion; it lands at ibMicFree; cbFree loses node + one tag
        page = self.changed(insert(1, PGNO, 60, 50, 1, b'9', b'NEW', prefix=b'kpx'))
        expected = struct.pack('<HH', 3, 1) + b'9' + b'NEW'
        self.assertEqual(page_header(page), (4028 - len(expected) - 4, 0, 16 + len(expected), 4))
        self.assertEqual(tags(page), [(0, 0), (8, 0), (len(expected), 16 | 5 << 13), (8, 8)])
        self.assertEqual(page[40 + 16:40 + 16 + len(expected)], expected)
        self.assertEqual([line for line, _ in lines_of(page)],
                         [node(b'k1', b'AAAA'), expected, node(b'k2', b'BBBB')])

    def test_an_insert_without_a_prefix(self):
        page = self.changed(insert(1, PGNO, 60, 50, 2, b'k3', b'C'))
        self.assertEqual(page_header(page), (4028 - 5 - 4, 0, 21, 4))
        self.assertEqual(tags(page)[3], (5, 16 | 1 << 13))

    def test_reorganizing_moves_lines_in_order_of_ib_not_of_tag(self):
        # data laid out as tag 3, tag 2, tag 1; growing tag 3 (at ib 0) past the contiguous
        # free space moves tag 2 to ib 0 and tag 1 after it, then tag 3 after both
        nodes = [node(b'k1', b'a' * 1000), node(b'k2', b'b' * 1000), node(b'k3', b'c' * 1500)]
        db = build_database({PGNO: leaf_page(PGNO, 50, nodes, layout=[0, 3, 2, 1])})
        result = run(db, [self.attach, begin0(5) + replace(1, PGNO, 60, 50, 2, b'd' * 1700) + commit0(5)])
        self.assertIsNone(result.refused)
        page = page_of(result.data, PGNO)
        self.assertEqual(tags(page), [(0, 0), (1004, 1004), (1004, 0), (1704, 2008 | 1 << 13)])
        self.assertEqual(page_header(page), (328, 0, 3712, 4))
        self.assertEqual([line for line, _ in lines_of(page)],
                         [nodes[0], nodes[1], node(b'k3', b'd' * 1700)])

    def test_an_old_style_diff_header_is_read_as_diffhdr(self):
        # LRREPLACE's top bit off: DIFFHDR, 13-bit ib with same-length 0x2000 (src/inc/logapi.hxx#L15-L34)
        diff = struct.pack('<HB', 0x2000 | 1, 1) + b'Z'
        page = self.changed(replace_d(1, PGNO, 60, 50, 1, diff, 4, fdiff2=False))
        self.assertEqual(lines_of(page)[1][0], node(b'k2', b'BZBB'))


class Refusals(unittest.TestCase):
    """Cases the replay must refuse rather than return a wrong database."""

    def setUp(self):
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        self.db = build_database({PGNO: self.page})
        self.attach = attach(1, (1, 0, 8))
        self.change = replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4)

    def refused(self, *bodies, db=None):
        result = run(db or self.db, list(bodies))
        self.assertIsNone(result.data)
        return result.refused

    def test_a_new_transaction_over_open_changes(self):
        self.assertIn('begins a transaction', self.refused(self.attach, begin0(5) + self.change + begin0(5) + commit0(5)))

    def test_a_page_of_another_object(self):
        record = replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4, objid=OBJID + 1)
        self.assertIn('belongs to object', self.refused(self.attach, begin0(5) + record + commit0(5)))

    def test_a_page_that_is_not_a_leaf(self):
        db = build_database({PGNO: leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')],
                                             flags=0x2000 | 0x0001)})
        self.assertIn('not a leaf', self.refused(self.attach, begin0(5) + self.change + commit0(5), db=db))

    def test_this_database_detached_or_attached_again(self):
        self.assertIn('attached or detached again', self.refused(self.attach, detach(1)))
        self.assertIn('attached or detached again', self.refused(self.attach, attach(1, (1, 0, 8))))

    def test_a_detach_of_another_dbid_is_passed_over(self):
        self.assertIsNone(run(self.db, [self.attach, detach(2)]).refused)

    def test_a_database_version_change(self):
        self.assertIn('version change', self.refused(self.attach, set_db_version(1, (0x620, 21, 0))))
        self.assertIsNone(run(self.db, [self.attach, set_db_version(1, (0x620, 20, 0))]).refused)

    def test_an_attach_whose_consistent_point_differs(self):
        self.assertIn('lgposConsistent', self.refused(attach(1, (1, 0, 9))))

    def test_a_change_that_does_not_move_the_dbtime_forward(self):
        for dbtime, before in ((60, 60), (40, 45)):
            record = replace_d(1, PGNO, dbtime, before, 1, diff2(1, b'Z'), 4)
            self.assertIn('forward', self.refused(self.attach, begin0(5) + record + commit0(5)))

    def test_a_diff_cut_short_refuses_and_never_raises(self):
        record = replace_d(1, PGNO, 60, 50, 1, b'\x01\x00', 4, fdiff2=False)
        self.assertIn('diff length', self.refused(self.attach, begin0(5) + record + commit0(5)))
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, 'Current.mdb'), 'wb') as handle:
                handle.write(self.db)
            with open(os.path.join(folder, 'Svc.log'), 'wb') as handle:
                handle.write(log_file(1, [self.attach, begin0(5) + record + commit0(5)]))
            data, summary = ese_recovery.replayed_database(os.path.join(folder, 'Current.mdb'))
        self.assertIsNone(data)
        self.assertIn('diff length', summary)

    def test_an_unexpected_error_becomes_a_refusal(self):
        with mock.patch.object(ese_log, 'read_records', side_effect=KeyError('boom')):
            result = run(self.db, [self.attach])
        self.assertIsNone(result.data)
        self.assertIn('unexpected KeyError', result.refused)


class LogChain(unittest.TestCase):
    """The newest committed changes must be present (src/ese/_log/logredo.cxx#L13614-L13636,
    #L4263-L4323)."""

    def setUp(self):
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        attach_record = attach(1, (1, 0, 8))
        self.gen1 = log_file(1, [attach_record, begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4)
                                 + commit0(5)], tm_create=b'\x02' * 8)
        self.gen2 = log_file(2, [begin0(5) + replace_d(1, PGNO, 70, 60, 1, diff2(2, b'Y'), 4) + commit0(5)],
                             tm_prev=b'\x02' * 8, tm_create=b'\x03' * 8)

    def test_both_logs_replay_both_changes(self):
        db = build_database({PGNO: self.page}, gens=(1, 1), committed=2)
        result = ese_recovery.replay(db, {1: ('Svc00001.log', self.gen1), 2: ('Svc.log', self.gen2)})
        self.assertIsNone(result.refused)
        self.assertEqual(lines_of(page_of(result.data, PGNO))[1][0], node(b'k2', b'BZYB'))

    def test_a_missing_committed_generation_refuses(self):
        db = build_database({PGNO: self.page}, gens=(1, 1), committed=2)
        result = ese_recovery.replay(db, {1: ('Svc00001.log', self.gen1)})
        self.assertIsNone(result.data)
        self.assertIn('generation 2 (committed) is missing', result.refused)

    def test_a_missing_current_log_refuses(self):
        db = build_database({PGNO: self.page}, gens=(1, 1), committed=1)
        result = ese_recovery.replay(db, {1: ('Svc00001.log', self.gen1)})
        self.assertIsNone(result.data)
        self.assertIn('current log is missing', result.refused)

    def test_a_current_log_followed_by_a_newer_generation_refuses(self):
        db = build_database({PGNO: self.page}, gens=(1, 1), committed=1)
        result = ese_recovery.replay(db, {1: ('Svc.log', self.gen1), 2: ('Svc00002.log', self.gen2)})
        self.assertIsNone(result.data)

    def test_a_page_already_newer_past_the_required_range_refuses(self):
        # the page (dbtime 50) is already at or past a change logged in generation 2, beyond
        # lGenMaxRequired 1 (src/ese/_log/logredo.cxx#L425-L439)
        gen2 = log_file(2, [begin0(5) + replace_d(1, PGNO, 50, 40, 1, diff2(1, b'Q'), 4) + commit0(5)],
                        tm_prev=b'\x02' * 8)
        gen1 = log_file(1, [attach(1, (1, 0, 8))], tm_create=b'\x02' * 8)
        db = build_database({PGNO: self.page}, gens=(1, 1), committed=2)
        result = ese_recovery.replay(db, {1: ('Svc00001.log', gen1), 2: ('Svc.log', gen2)})
        self.assertIn('past the required range', result.refused)
        # inside the required range the same record is passed over as already on the page
        db = build_database({PGNO: self.page}, gens=(1, 2), committed=2)
        result = ese_recovery.replay(db, {1: ('Svc00001.log', gen1), 2: ('Svc.log', gen2)})
        self.assertIsNone(result.refused)
        self.assertEqual(result.skipped_newer, 1)

    def test_find_logs_reads_only_the_header_of_a_foreign_log(self):
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, 'Svc.log'), 'wb') as handle:
                handle.write(self.gen1)
            with open(os.path.join(folder, 'Abc.log'), 'wb') as handle:
                handle.write(log_file(1, [begin0(5)], sign=b'\x09' * 28))
            reads = []
            real_open = open

            def counting_open(path, *args, **kwargs):
                handle = real_open(path, *args, **kwargs)
                if 'b' in (args[0] if args else kwargs.get('mode', 'r')):
                    real_read = handle.read
                    handle.read = lambda size=-1: reads.append((os.path.basename(path), size)) or real_read(size)
                return handle
            with mock.patch('builtins.open', counting_open):
                logs, skipped = ese_recovery.find_logs(folder, ese_recovery.DatabaseHeader(
                    build_database({PGNO: self.page})))
        self.assertEqual(sorted(logs), [1])
        self.assertEqual(skipped, [('Abc.log', 'a different log signature')])
        self.assertEqual([size for name, size in reads if name == 'Abc.log'], [ese_log.LOG_HEADER_SIZE])


class OtherPageSizes(unittest.TestCase):
    def header_db(self, state):
        db = bytearray(build_database({PGNO: bytes(8192)}, state=state, page_size=8192))
        for base in (0, 8192):
            db[base + 6000] = 0x5a     # a byte only the 8 KiB checksum covers
            struct.pack_into('<I', db, base, ese_log.checksum_old(bytes(db[base:base + 8192])))
        return bytes(db)

    def test_a_clean_8k_database_comes_back_as_stored(self):
        db = self.header_db(3)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'Current.mdb')
            with open(path, 'wb') as handle:
                handle.write(db)
            data, summary = ese_recovery.replayed_database(path)
        self.assertEqual(data, db)
        self.assertEqual(summary, 'not replayed: the header records clean shutdown')

    def test_a_dirty_large_page_database_refuses_for_its_page_size(self):
        # 16 and 32 KiB pages use the large page format (PGHDR2, 15-bit tags, a checksum per
        # block), which the replay does not write
        for size in (16384, 32768):
            db = bytearray(build_database({PGNO: bytes(size)}, state=2, page_size=size))
            for base in (0, size):
                struct.pack_into('<I', db, base, ese_log.checksum_old(bytes(db[base:base + size])))
            result = ese_recovery.replay(bytes(db), {1: ('edb.log', log_file(1, [attach(1, (1, 0, 8))]))})
            self.assertIsNone(result.data)
            self.assertEqual(result.refused, f'a page size of {size}')


BIG = 8192


class EightKiBPages(unittest.TestCase):
    """The same redo on 8 KiB pages, with lines and tags past the first 4 KiB, so a 4 KiB
    assumption anywhere (tag array, checksum, page offset, free space) shows."""

    def setUp(self):
        self.nodes = [node(b'k1', b'a' * 3000), node(b'k2', b'b' * 2500), node(b'k3', b'CCCC')]
        self.page = leaf_page(PGNO, 50, self.nodes, size=BIG)
        self.db = build_database({PGNO: self.page, PGNO + 1: leaf_page(PGNO + 1, 40, [], size=BIG)},
                                 page_size=BIG)
        self.attach = attach(1, (1, 0, 8))

    def test_the_fixture_is_an_8k_page_with_a_line_past_4k(self):
        cb_free, _unc, ib_mic_free, itag_state = page_header(self.page)
        self.assertEqual(ib_mic_free, sum(len(n) for n in self.nodes))
        self.assertGreater(ib_mic_free, PAGE)
        self.assertEqual(itag_state, 4)
        self.assertEqual(cb_free, BIG - 40 - ib_mic_free - 16)
        self.assertEqual(struct.unpack_from('<Q', self.page, 0)[0], ese_log.checksum_new(self.page, PGNO))

    def test_replace_d_on_the_line_past_4k(self):
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 2, diff2(1, b'Z'), 4) + commit0(5)
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.refused)
        page = page_of(result.data, PGNO, BIG)
        self.assertEqual([line for line, _ in lines_of(page)], self.nodes[:2] + [node(b'k3', b'CZCC')])
        self.assertEqual(struct.unpack_from('<q', page, 8)[0], 60)
        # the checksum covers all 8 KiB (src/ese/_osu/checksumu.cxx#L284-L327)
        self.assertEqual(struct.unpack_from('<Q', page, 0)[0], ese_log.checksum_new(page, PGNO))
        # the other page and the header pages are left as stored
        self.assertEqual(page_of(result.data, -1, BIG) + page_of(result.data, 0, BIG), self.db[:2 * BIG])
        self.assertEqual(page_of(result.data, PGNO + 1, BIG), page_of(self.db, PGNO + 1, BIG))

    def test_an_insert_writes_its_tag_at_the_end_of_the_8k_page(self):
        body = begin0(5) + insert(1, PGNO, 60, 50, 3, b'k4', b'DD') + commit0(5)
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.refused)
        page = page_of(result.data, PGNO, BIG)
        start = sum(len(n) for n in self.nodes)
        self.assertEqual(struct.unpack_from('<HH', page, BIG - 20), (len(node(b'k4', b'DD')), start | 1 << 13))
        self.assertEqual(page_header(page)[2:], (start + len(node(b'k4', b'DD')), 5))

    def test_a_growing_replace_reorganizes_inside_8k(self):
        # k2 grows by 1500 bytes: the 2620 contiguous free bytes after ibMicFree are too few
        # for its 4004, so k1 and k3 move down in order of ib and k2 is written after them
        grown = b'B' * 4000
        result = run(self.db, [self.attach, begin0(5), replace(1, PGNO, 60, 50, 1, grown), commit0(5)])
        self.assertIsNone(result.refused)
        page = page_of(result.data, PGNO, BIG)
        self.assertEqual([line for line, _ in lines_of(page)], [self.nodes[0], node(b'k2', grown), self.nodes[2]])
        self.assertEqual(struct.unpack_from('<HH', page, BIG - 16), (8, 3004))
        self.assertEqual(struct.unpack_from('<HH', page, BIG - 12), (4004, 3012 | 1 << 13))
        self.assertEqual(page_header(page), (BIG - 40 - 7016 - 16, 0, 7016, 4))

    def test_the_wrong_page_size_reads_the_wrong_page(self):
        # control: the same records against the database read at 4 KiB offsets fail the checksum
        body = begin0(5) + replace_d(1, PGNO, 60, 50, 2, diff2(1, b'Z'), 4) + commit0(5)
        with mock.patch.object(ese_recovery.DatabaseHeader, '__init__', autospec=True,
                               side_effect=_header_at(PAGE)):
            result = run(self.db, [self.attach, body])
        self.assertIsNone(result.data)


def _header_at(size):
    real = ese_recovery.DatabaseHeader.__init__

    def init(self, data):
        real(self, data)
        self.page_size = size
    return init


class StartAtTheFirstRequiredLog(unittest.TestCase):
    """The attach is in a log that is gone; the dbid comes from the first required log's
    header (LGFakeCheckpointToLogFile, src/ese/_log/logredo.cxx#L14742-L14755)."""

    def setUp(self):
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        self.db = build_database({PGNO: self.page}, lgpos_attach=(1, 5, 616), lgpos_consistent=(1, 3, 8),
                                 gens=(2, 2))
        self.body = begin0(5) + replace_d(3, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit0(5)

    def logs(self, attachments):
        return {2: ('edb.log', log_file(2, [self.body], attachments=attachments))}

    def test_the_dbid_from_the_log_header_is_replayed(self):
        listed = attach_info(7, (1, 1, 0), (1, 0, 8), sign_db=b'\x05' * 28) + attach_info(3, (1, 5, 616), (1, 3, 8))
        result = ese_recovery.replay(self.db, self.logs(listed))
        self.assertIsNone(result.refused)
        self.assertEqual(lines_of(page_of(result.data, PGNO))[1][0], node(b'k2', b'BZBB'))

    def test_another_dbid_in_the_log_is_not_this_database(self):
        result = ese_recovery.replay(self.db, self.logs(attach_info(4, (1, 5, 616), (1, 3, 8))))
        self.assertIsNone(result.refused)
        self.assertEqual(result.redone, 0)
        self.assertEqual(result.data, self.db)

    def test_a_header_that_does_not_list_this_attachment_refuses(self):
        for listed in (b'', attach_info(3, (1, 4, 616), (1, 3, 8)), attach_info(3, (1, 5, 616), (1, 2, 8)),
                       attach_info(3, (1, 5, 616), (1, 3, 8), sign_db=b'\x05' * 28)):
            result = ese_recovery.replay(self.db, self.logs(listed))
            self.assertIsNone(result.data)
            self.assertIn('does not list this attachment', result.refused)


class RecordsAlreadyOnThePage(unittest.TestCase):
    """Delete, FlagDelete, Delta, Split2 and Merge2 are passed over only when every page they
    name already holds their dbtime; otherwise the replay refuses."""

    def setUp(self):
        self.pages = {pgno: leaf_page(pgno, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
                      for pgno in (3, 4, 5, 6)}
        self.db = build_database(self.pages)
        self.attach = attach(1, (1, 0, 8))

    def outcome(self, record):
        return run(self.db, [self.attach, begin0(5) + record + commit0(5)])

    def test_on_the_page_they_change_nothing(self):
        for record in (delete(1, 3, 50, 49), page_op(32, 1, 3, 45, 44, 44), page_op(37, 1, 3, 50, 49, 54),
                       split2(1, 3, 50, 4, 5, 6), merge2(1, 3, 48, 4, 0, 6)):
            with self.subTest(record[0]):
                result = self.outcome(record)
                self.assertIsNone(result.refused)
                self.assertEqual(result.data, self.db)
                self.assertEqual(result.skipped_newer, 1)

    def test_any_named_page_still_older_refuses(self):
        for record, page in ((delete(1, 3, 51, 50), 3), (split2(1, 3, 51, 4, 5, 6), 3),
                             (split2(1, 4, 50, 3, 0, 6), 3), (merge2(1, 3, 50, 4, 5, 0), 3)):
            pages = dict(self.pages)
            if record[0] == 62 and record != split2(1, 3, 51, 4, 5, 6):
                pages[3] = leaf_page(3, 40, [node(b'k1', b'AAAA')])        # the new page is older
                db = build_database(pages)
            elif record[0] == 63:
                pages[5] = leaf_page(5, 40, [node(b'k1', b'AAAA')])        # the right page is older
                db, page = build_database(pages), 5
            else:
                db = self.db
            with self.subTest(record[0]):
                result = run(db, [self.attach, begin0(5) + record + commit0(5)])
                self.assertIsNone(result.data)
                self.assertIn(f'would change page {page}', result.refused)

    def test_another_dbid_is_not_checked(self):
        self.assertIsNone(self.outcome(delete(2, 3, 99, 98)).refused)

    def test_an_uncommitted_pass_over_still_refuses(self):
        result = run(self.db, [self.attach, begin0(5) + delete(1, 3, 50, 49)])
        self.assertIn('never committed', result.refused)

    def test_on_the_page_past_the_required_range_refuses(self):
        db = build_database(self.pages, gens=(1, 1), committed=2)
        gen1 = log_file(1, [self.attach], tm_create=b'\x02' * 8)
        gen2 = log_file(2, [begin0(5) + delete(1, 3, 50, 49) + commit0(5)], tm_prev=b'\x02' * 8)
        result = ese_recovery.replay(db, {1: ('edb00001.log', gen1), 2: ('edb.log', gen2)})
        self.assertIn('past the required range', result.refused)

    def test_a_flagdelete_that_would_change_the_page_refuses(self):
        self.assertIn('does not redo FlagDelete', self.outcome(page_op(32, 1, 3, 60, 50, 44)).refused)


class Sessions(unittest.TestCase):
    def setUp(self):
        self.page = leaf_page(PGNO, 50, [node(b'k1', b'AAAA'), node(b'k2', b'BBBB')])
        self.db = build_database({PGNO: self.page})
        self.attach = attach(1, (1, 0, 8))

    def test_a_nested_begin_keeps_the_changes_open_and_replays(self):
        body = (begin0(5) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit(5) + begin(5)
                + replace_d(1, PGNO, 61, 60, 1, diff2(2, b'Y'), 4) + commit(5) + commit0(5))
        result = run(self.db, [self.attach, body])
        self.assertIsNone(result.refused)
        self.assertEqual(lines_of(page_of(result.data, PGNO))[1][0], node(b'k2', b'BZYB'))

    def test_a_change_for_a_session_not_seen_beginning_refuses(self):
        body = replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4, procid=9) + commit0(9)
        self.assertIn('began before the replay started', run(self.db, [self.attach, body]).refused)

    def test_a_nested_begin_does_not_count_as_a_first_begin(self):
        body = begin(9) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4, procid=9) + commit0(9)
        self.assertIn('began before the replay started', run(self.db, [self.attach, body]).refused)

    def test_a_change_inside_a_macro_refuses(self):
        body = (begin0(5) + macro(11, 5, 60) + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4)
                + macro(12, 5, 60) + commit0(5))
        self.assertIn('inside a macro', run(self.db, [self.attach, body]).refused)

    def test_a_change_while_a_second_macro_is_still_open_refuses(self):
        body = (begin0(5) + macro(11, 5, 55) + macro(11, 5, 56) + macro(12, 5, 55)
                + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + macro(12, 5, 56) + commit0(5))
        self.assertIn('inside a macro', run(self.db, [self.attach, body]).refused)

    def test_a_closed_macro_and_a_trace_change_nothing(self):
        for end in (12, 13):
            body = (begin0(5) + macro(11, 5, 55) + macro(end, 5, 55) + trace()
                    + replace_d(1, PGNO, 60, 50, 1, diff2(1, b'Z'), 4) + commit0(5))
            result = run(self.db, [self.attach, body])
            self.assertIsNone(result.refused, end)
            self.assertEqual(result.redone, 1)


# ---------------------------------------------------------------- the reader hook

class ReaderHook(unittest.TestCase):
    def test_bytes_source_behaves_like_the_remote_file_the_reader_expects(self):
        source = ese_rows._BytesSource(b'abcdef')   # pylint: disable=protected-access
        source.read(3)
        source.open()
        self.assertEqual(source.read(), b'abcdef')


# ---------------------------------------------------------------- the two corpus images

def row_hashes(database, table):
    """The per-row hash count.py uses, so the result compares with its after.json."""
    return sorted(hashlib.sha256(repr(sorted((k, repr(v)) for k, v in dict(r).items())).encode()).hexdigest()
                  for r in ese_rows.TableRows(database, table))


@unittest.skipUnless(REAL_ROOT.is_dir(), f'the UAL corpus Sum folders are not staged at {REAL_ROOT}')
class RealImages(unittest.TestCase):
    IMAGES = {'dc01': {'logs': 1, 'changed_pages': [35, 36, 37, 38, 39, 40]},
              'srv2022': {'logs': 1, 'changed_pages': [31, 73, 87, 95, 96]}}

    def setUp(self):
        self.images = [name for name in self.IMAGES if (REAL_ROOT / name / 'orig' / 'Current.mdb').is_file()]
        if not self.images:
            self.skipTest(f'no image under {REAL_ROOT}')

    def test_replay_matches_esentutl_row_for_row(self):
        for name in self.images:
            with self.subTest(name):
                path = REAL_ROOT / name / 'orig' / 'Current.mdb'
                data, summary = ese_recovery.replayed_database(str(path))
                self.assertIsNotNone(data, summary)
                after_json = REAL_ROOT / name / 'after.json'
                if not after_json.is_file():
                    self.skipTest(f'{after_json} is not staged')
                known = json.loads(after_json.read_text())['Current.mdb']['tables']
                database = ese_rows.ESEDatabase(str(path), data=data)
                try:
                    for table, expected in known.items():
                        self.assertEqual(row_hashes(database, table), expected['hashes'], table)
                finally:
                    database.close()

    def test_changed_pages_match_esentutl_but_for_the_flush_type(self):
        for name in self.images:
            with self.subTest(name):
                known_path = REAL_ROOT / name / 'replayed' / 'Current.mdb'
                if not known_path.is_file():
                    self.skipTest(f'{known_path} is not staged')
                orig = (REAL_ROOT / name / 'orig' / 'Current.mdb').read_bytes()
                known = known_path.read_bytes()
                data, _summary = ese_recovery.replayed_database(str(REAL_ROOT / name / 'orig' / 'Current.mdb'))
                changed = [n - 1 for n in range(2, len(orig) // PAGE)
                           if data[n * PAGE:(n + 1) * PAGE] != orig[n * PAGE:(n + 1) * PAGE]]
                self.assertEqual(changed, self.IMAGES[name]['changed_pages'])
                for pgno in changed:
                    mine = bytearray(page_of(data, pgno))
                    theirs = page_of(known, pgno)
                    # take esentutl's flush-type bits (maskFlushType 0x18000, src/inc/cpage.hxx#L713)
                    flags = struct.unpack_from('<I', mine, 36)[0] & ~0x18000
                    struct.pack_into('<I', mine, 36, flags | struct.unpack_from('<I', theirs, 36)[0] & 0x18000)
                    struct.pack_into('<Q', mine, 0, ese_log.checksum_new(bytes(mine), pgno))
                    self.assertEqual(bytes(mine), theirs, pgno)

    def test_bytes_and_file_read_the_same(self):
        path = REAL_ROOT / self.images[0] / 'orig' / 'Current.mdb'
        from_file = ese_rows.ESEDatabase(str(path))
        from_bytes = ese_rows.ESEDatabase(str(path), data=path.read_bytes())
        try:
            for table in ('CLIENTS', 'ROLE_ACCESS', 'DNS'):
                self.assertEqual(row_hashes(from_bytes, table), row_hashes(from_file, table), table)
        finally:
            from_file.close()
            from_bytes.close()

    def test_the_row_comparison_catches_a_broken_redo_step(self):
        # skip the last Replace/ReplaceD redo: the comparison above must then fail
        name = self.images[0]
        after_json = REAL_ROOT / name / 'after.json'
        if not after_json.is_file():
            self.skipTest(f'{after_json} is not staged')
        known = json.loads(after_json.read_text())['Current.mdb']['tables']
        real = ese_recovery._redo_replace   # pylint: disable=protected-access
        path = str(REAL_ROOT / name / 'orig' / 'Current.mdb')
        calls = []
        try:
            ese_recovery._redo_replace = lambda *args: calls.append(args)   # pylint: disable=protected-access
            ese_recovery.replayed_database(path)
            count = len(calls)
            calls.clear()

            def skip_last(*args):
                calls.append(args)
                if len(calls) < count:
                    real(*args)
            ese_recovery._redo_replace = skip_last   # pylint: disable=protected-access
            data, _summary = ese_recovery.replayed_database(path)
        finally:
            ese_recovery._redo_replace = real   # pylint: disable=protected-access
        database = ese_rows.ESEDatabase(path, data=data)
        try:
            differs = [table for table, expected in known.items()
                       if row_hashes(database, table) != expected['hashes']]
        finally:
            database.close()
        self.assertTrue(differs)

    def test_controls(self):
        for name in self.images:
            with self.subTest(name):
                folder = REAL_ROOT / name / 'orig'
                db = (folder / 'Current.mdb').read_bytes()
                header = ese_recovery.DatabaseHeader(db)
                logs, _skipped = ese_recovery.find_logs(str(folder), header)
                required = header.gen_min_required
                # the required log removed
                self.assertIn('missing', ese_recovery.replay(
                    db, {g: v for g, v in logs.items() if g != required}).refused)
                # one byte flipped inside a record of the last log, in a segment after the attach
                path, data = logs[max(logs)]
                flipped = bytearray(data)
                isec = header.lgpos_attach[1] + 3
                flipped[isec * PAGE + 60] ^= 0xff
                self.assertIn('fails its checksum', ese_recovery.replay(
                    db, {**logs, max(logs): (path, bytes(flipped))}).refused)
                # a database in clean shutdown is returned as stored
                clean_path = REAL_ROOT / name / 'replayed' / 'Current.mdb'
                if clean_path.is_file():
                    clean = clean_path.read_bytes()
                    self.assertEqual(ese_recovery.replay(clean, logs).data, clean)

    def test_a_copy_staged_elsewhere_replays_the_same(self):
        name = self.images[0]
        with tempfile.TemporaryDirectory() as folder:
            for item in (REAL_ROOT / name / 'orig').iterdir():
                if item.suffix.lower() in ('.mdb', '.log'):
                    shutil.copyfile(item, os.path.join(folder, item.name))
            staged, _ = ese_recovery.replayed_database(os.path.join(folder, 'Current.mdb'))
        direct, _ = ese_recovery.replayed_database(str(REAL_ROOT / name / 'orig' / 'Current.mdb'))
        self.assertEqual(staged, direct)


@unittest.skipUnless(NTDS_ROOT.is_dir(), f'the NTDS folders are not staged at {NTDS_ROOT}')
class RealNtds(unittest.TestCase):
    """ntds.dit (8 KiB pages) with its edb*.log, from szechuan_dc01_server2012r2 (dc01),
    ou_ransomware_server2022 (srv2022) and alihadi_threatsim_server2019 (srv2019). Counts
    only; nothing derived from the images is committed."""
    BIG_PAGE = 8192
    EXPECTED = {'dc01': 'replayed 0 change(s) from edb.log onto 0 page(s) (304 already on the page)',
                'srv2022': 'replayed 610 change(s) from 23 logs, edb0001A.log to edb.log onto 4 page(s) '
                           '(61118 already on the page)',
                'srv2019': 'not replayed: the header records clean shutdown'}

    def folder(self, name):
        folder = NTDS_ROOT / name
        if not (folder / 'ntds.dit').is_file():
            self.skipTest(f'{folder} is not staged')
        return folder

    def test_summaries(self):
        for name, expected in self.EXPECTED.items():
            with self.subTest(name):
                data, summary = ese_recovery.replayed_database(str(self.folder(name) / 'ntds.dit'))
                self.assertEqual(summary, expected)
                self.assertIsNotNone(data)

    def test_dc01_comes_back_byte_for_byte(self):
        path = self.folder('dc01') / 'ntds.dit'
        self.assertEqual(ese_recovery.replayed_database(str(path))[0], path.read_bytes())

    def test_srv2022_changes_only_four_pages_and_each_checksum_holds(self):
        path = self.folder('srv2022') / 'ntds.dit'
        stored = path.read_bytes()
        data, _summary = ese_recovery.replayed_database(str(path))
        size = self.BIG_PAGE
        changed = [n - 1 for n in range(2, len(stored) // size) if data[n * size:(n + 1) * size] != stored[n * size:(n + 1) * size]]
        self.assertEqual(changed, [1733, 1794, 1814, 2908])
        for pgno in changed:
            page = page_of(data, pgno, size)
            self.assertEqual(struct.unpack_from('<Q', page, 0)[0], ese_log.checksum_new(page, pgno))

    def test_srv2022_controls(self):
        folder = self.folder('srv2022')
        db = (folder / 'ntds.dit').read_bytes()
        logs, _skipped = ese_recovery.find_logs(str(folder), ese_recovery.DatabaseHeader(db))
        self.assertEqual(sorted(logs), list(range(26, 49)))
        # a generation in the middle removed
        self.assertIn('generation 37 is missing', ese_recovery.replay(
            db, {g: v for g, v in logs.items() if g != 37}).refused)
        # the current log removed: generation 48, the committed one, is missing
        self.assertIn('generation 48', ese_recovery.replay(db, {g: v for g, v in logs.items() if g != 48}).refused)
        # one byte flipped in a segment holding a redone change
        path, data = logs[48]
        flipped = bytearray(data)
        flipped[1000 * PAGE + 200] ^= 0xff
        self.assertIn('fails its checksum', ese_recovery.replay(db, {**logs, 48: (path, bytes(flipped))}).refused)
        # the first required log's header without its attachment list
        path, data = logs[26]
        bare = bytearray(data)
        bare[671:671 + 2048] = bytes(2048)
        struct.pack_into('<I', bare, 0, ese_log.checksum_old(bytes(bare[:PAGE])))
        self.assertIn('does not list this attachment', ese_recovery.replay(db, {**logs, 26: (path, bytes(bare))}).refused)


if __name__ == '__main__':
    unittest.main()
