"""Soft recovery of an ESE database in memory: replay its transaction logs onto a copy of
its bytes the way ESE's own recovery would, so a database whose header records a dirty
shutdown can be read as Windows would read it after `esentutl /r`.

Nothing here writes a file. The database and log bytes are read, the replay works on a
bytearray copy, and the caller gets either the whole replayed copy or None with the reason.
A replay never returns a partly replayed database: any record, page or log this module
cannot reproduce exactly makes the whole replay refuse (fail closed), and the caller then
reads the database as stored.

Every rule below is cited to Microsoft's ESE source (MIT licence) at the commit DLEAPP
already cites, 7030fe7407615160e54d152e4ef704eede2fdd7e, as path#Lline relative to
dev/ese; see scripts/ese_log.py for the log format itself. What is implemented:

* Which logs: every generation from the header's minimum required generation to the newest
  log present, each carrying the database's log signature and following the one before it
  (tmPrevGen equal to the previous log's tmCreate, src/ese/_log/logredo.cxx#L4403). The
  newest must be the current log (the base name with no generation), as redo ends there
  (src/ese/_log/logredo.cxx#L4263-L4297, #L4317-L4323), and must reach both the header's
  maximum required and maximum committed generations (ErrLGCheckDatabaseGens,
  src/ese/_log/logredo.cxx#L13614-L13636). Otherwise the newest changes could be missing
  and the replay refuses.
* Where the replay starts for this database: its LRATTACHDB record, the one at the
  header's lgposAttach whose database signature, log signature and lgposConsistent match
  the header. Both the header and that record name a consistent point before the attach
  (on the two UAL corpus images, the detach that preceded it); the replay requires that point
  and does not replay anything before the attach. Records name a database by dbid, and a
  dbid means only what the last attach gave it (the ou_ransomware_server2022 Svc.log reuses
  dbid 1 for SystemIdentity.mdb between two attaches of Current.mdb).
  When the attach lies in a log older than the first required one (the logs that held it are
  gone), the replay starts at the first record of the first required log and takes the dbid
  from that log's header, as ESE does when it starts redo at a log file rather than at a
  checkpoint (LGFakeCheckpointToLogFile copies the log header's attachment list,
  src/ese/_log/logredo.cxx#L14742-L14755, used at #L15160-L15166 and #L15204-L15222). The
  header's list (rgbAttach, src/inc/log.hxx#L201-L231) must hold an ATTACHINFO
  (src/inc/log.hxx#L85-L124, read as ErrLGIDumpAttachments walks it,
  src/ese/_log/logdump.cxx#L909-L929) with this database's signature, lgposAttach and
  lgposConsistent; otherwise the replay refuses.
* Records passed over: NOP2, MacroInfo, MacroInfo2, CommitCtx and Trace, which change no
  page (src/ese/_log/logredo.cxx#L7650-L7693, #L12475, #L12489-L12493), and a SetDbVersion
  naming the version the header already holds (redone by ErrDBRedoSetDbVersion, src/ese/_log/logredo.cxx#L13231-L13270).
  MacroBegin, MacroCommit and MacroAbort change no page by themselves: ESE holds a session's
  Split2 and Merge2 records from MacroBegin and redoes them at MacroCommit, or drops them at
  MacroAbort (src/ese/_log/logredo.cxx#L12572-L12620, #L7189-L7273). Any other record type
  after the attach makes the replay refuse.
* Records passed over only when they are already on every page they name: Delete,
  FlagDelete, Delta, Split2 and Merge2 for this dbid. ESE redoes a page only when the
  record's dbtime is above the page's (FLGINeedRedo, below), so a record whose pages all hold
  its dbtime or a later one changes nothing. Delete, FlagDelete and Delta name one page, the
  LRPAGE_ pgno (redone in ErrLGRIRedoNodeOperation, src/ese/_log/logredo.cxx#L3613-L3815);
  Split2 names that page and pgnoNew, pgnoRight and pgnoParent (LRSPLIT_,
  src/inc/logapi.hxx#L873-L909), Merge2 that page and pgnoRight, pgnoLeft and pgnoParent
  (LRMERGE_, src/inc/logapi.hxx#L954-L998); a pgno of 0 names no page. When any page named
  is older than the record, the change would have to be redone, which this module does
  not do for those types, and the replay refuses. The same required-range rule applies as
  for a redone type.
* Which records change a page: Insert, Replace and ReplaceD for this dbid, redone as
  ErrLGRIRedoNodeOperation does (src/ese/_log/logredo.cxx#L3027-L3815). A record is redone only when its
  dbtime is above the page's (FLGINeedRedo, src/ese/_log/logredo.cxx#L253-L265), and then the page's
  dbtime must equal the record's dbtimeBefore, otherwise ESE stops with a dbtime mismatch
  (FLGNeedRedoCheckDbtimeBefore, src/ese/_log/logredo.cxx#L336-L442), and so does this module. A record
  that is not redone because the page is already newer is allowed only up to the header's
  maximum required generation (src/ese/_log/logredo.cxx#L425-L439, #L6344-L6349, #L11685-L11750).
  After the change the page takes the record's dbtime (src/ese/_log/logredo.cxx#L3806-L3808).
* Transactions: ESE redoes everything and then rolls back what never committed to level 0.
  This module tracks each session (procid): a change to this database is kept only when a
  Commit0 for its session follows it. A session that rolls back, or reaches the end of the
  log, with a change to this database still open makes the replay refuse: undo is not
  implemented, so such a log is read as stored. ESE redoes a session's records only after
  it has seen that session begin a transaction from level 0 (FAfterFirstBT,
  src/ese/_log/logredo.cxx#L7012-L7052, #L2896-L2925); a record that would change a page
  for a session this replay has not seen begin, or for a session inside a macro, makes the
  replay refuse, since the replay may start at a different place than ESE's checkpoint.
* Page sizes: 4 KiB and 8 KiB. ESE uses one page layout, the small format, for every page
  of 8 KiB or less (FIsSmallPage, src/inc/daedef.hxx#L5795; m_fSmallFormat,
  src/ese/cpage.cxx#L2104): the 40-byte PGHDR (CbPageHeader, src/inc/cpage.hxx#L1118), tags
  with 13-bit sizes and offsets (mskSmallTagIbCb, src/inc/cpage.hxx#L941-L945), and one
  XOR-ECC checksum over the whole page (ComputePageChecksum, src/ese/_osu/checksumu.cxx#L284-L327).
  16 and 32 KiB pages use another layout (the 80-byte PGHDR2, src/inc/cpage.hxx#L1014-L1021,
  15-bit tag fields, and a checksum per block of the page) and are refused.
* Page checksums: every page is checked before it is changed (ESE's XOR-ECC checksum,
  src/ese/_osu/checksumu.cxx#L270-L335), and every changed page gets a new one the way SetPageChecksum
  writes it before a page goes to disk (src/ese/_osu/checksumu.cxx#L666-L676, src/ese/cpage.cxx#L5144-L5167).

What is not reproduced, by design: the database header is left as stored (it still says
dirty shutdown), and the two flush-type bits ESE sets in a page's flags when it writes the
page (SetFlushType_, src/ese/cpage.cxx#L5152-L5156, used for lost-flush detection with the .jfm
flush map) are left as they were. Neither is read by DLEAPP's ESE reader.
"""

import os
import re
import struct

from scripts import ese_log
from scripts.ese_log import LogError

# DBFILEHDR, src/inc/daedef.hxx#L2785-L2972
_DB_STATE_DIRTY = 2          # JET_dbstateDirtyShutdown
_DB_STATE_CLEAN = 3          # JET_dbstateCleanShutdown
DB_STATES = {1: 'just created', 2: 'dirty shutdown', 3: 'clean shutdown', 4: 'being converted',
             5: 'force detach'}
# Small-format pages (FIsSmallPage, src/inc/daedef.hxx#L5795); see the module docstring.
_SUPPORTED_PAGE_SIZES = (4096, 8192)

# PGHDR, src/inc/cpage.hxx#L992-L1010: checksum 0, dbtimeDirtied 8, pgnoPrev 16, pgnoNext 20,
# objidFDP 24, cbFree 28, cbUncommittedFree 30, ibMicFree 32, itagState 34, fFlags 36.
_PAGE_HEADER = 40
_PAGE_NEW_CHECKSUM = 0x2000  # fPageNewChecksumFormat, src/inc/cpage.hxx#L703
_ITAG_MIC_FREE_MASK = 0x0fff  # src/inc/cpage.hxx#L1006
_SHF_CTAG_RESERVED = 12       # src/inc/cpage.hxx#L1008
# TAG on a small page: cb_ then ib_, 13 bits each, flags in the top 3 bits of ib_
# (src/inc/cpage.hxx#L941-L945, #L960-L961; src/ese/cpage.cxx#L1196-L1235).
_TAG_MASK = 0x1fff
_TAG_FLAGS_SHIFT = 13
# Node flags, src/inc/node.hxx#L247-L249; key counts are masked with usNDCbKeyMask, src/inc/node.hxx#L245.
_ND_VERSION = 0x01
_ND_COMPRESSED = 0x04
_KEY_MASK = 0x1fff
# JET_efvReservedTags needs database version 1568.270.560 (src/ese/sysver.cxx#L97); below it a page
# keeps the legacy itagState (src/inc/cpage.hxx#L1603-L1625, src/ese/cpage.cxx#L3393-L3403, src/ese/db.cxx#L6529-L6545).
_RESERVED_TAGS_DB_VERSION = (1568, 270, 560)

# Log record types this replay knows what to do with after the attach.
_LR_INSERT, _LR_REPLACE, _LR_REPLACE_D = 29, 33, 34
_LR_BEGIN, _LR_COMMIT, _LR_ROLLBACK, _LR_BEGIN0, _LR_COMMIT0 = 5, 6, 7, 8, 9
_LR_ATTACH, _LR_DETACH, _LR_SET_DB_VERSION = 15, 16, 92
_LR_MACRO_BEGIN, _LR_MACRO_COMMIT, _LR_MACRO_ABORT = 11, 12, 13
_LR_FLAG_DELETE, _LR_DELETE, _LR_DELTA, _LR_SPLIT2, _LR_MERGE2 = 32, 35, 37, 62, 63
# Types passed over when every page they name is already newer (see the module docstring),
# with the offsets of the pgnos they name after LRPAGE_'s own (src/inc/logapi.hxx#L873-L998).
_ALREADY_ON_PAGE_ONLY = {_LR_FLAG_DELETE: (), _LR_DELETE: (), _LR_DELTA: (),
                         _LR_SPLIT2: (32, 36, 48), _LR_MERGE2: (32, 44, 56)}
_ATTACH_INFO_OFFSET = 671     # rgbAttach in LGFILEHDR, src/inc/log.hxx#L231
_ATTACH_INFO_SIZE = 64        # ATTACHINFO without its names, packed (src/inc/log.hxx#L80, #L85-L101)
_ATTACH_LIST_SIZE = 2048      # cbAttach, src/inc/log.hxx#L132
# LRIGNORED types ESE's redo passes over (src/inc/logapi.hxx#L226-L233); others carrying a dbid
# (ExtendDB, ScanCheck, ReAttach, FreeFDP) could concern this database and are refused.
_IGNORABLE = {67: 'MacroInfo', 69: 'CommitCtx', 71: 'NOP2', 73: 'MacroInfo2'}
# Trace is a debug record redo does nothing with (src/ese/_log/logredo.cxx#L12489-L12493).
_IGNORABLE[22] = 'Trace'
# Records that carry a page operation (LRPAGE_ first, src/inc/logapi.hxx#L377-L423).
_PAGE_RECORD_TYPES = set(range(24, 40)) | {48, 58, 62, 63, 64, 65, 93}


class ReplayRefused(ValueError):
    """The replay cannot reproduce ESE's recovery; the message says why."""


class DatabaseHeader:
    """The DBFILEHDR fields the replay uses (src/inc/daedef.hxx#L2785-L2972)."""

    def __init__(self, data):
        if len(data) < 4096:
            raise ReplayRefused('the database is shorter than its header')
        if struct.unpack_from('<I', data, 4)[0] != 0x89abcdef:   # ulDAEMagic, src/inc/daedef.hxx#L2320
            raise ReplayRefused('not an ESE database (no magic number)')
        # le_cbPageSize, 0 meaning g_cbPageDefault (4 KiB) (src/inc/daedef.hxx#L1039, #L2850).
        self.page_size = struct.unpack_from('<I', data, 236)[0] or 4096
        if self.page_size not in (2048, 4096, 8192, 16384, 32768) or len(data) < self.page_size:
            raise ReplayRefused(f'a header page size of {self.page_size}')
        # ESE checksums the header page over the page size it names, as databaseHeader, which
        # takes the old XOR checksum (src/ese/_osu/fileu.cxx#L196-L227, src/ese/_osu/checksumu.cxx#L214-L222).
        page = bytes(data[:self.page_size])
        if struct.unpack_from('<I', page, 0)[0] != ese_log.checksum_old(page):
            raise ReplayRefused('the database header checksum does not match')
        self.version = struct.unpack_from('<I', page, 8)[0]
        self.dbtime = struct.unpack_from('<q', page, 16)[0]
        self.sign_db = page[24:52]
        self.state = struct.unpack_from('<I', page, 52)[0]
        self.lgpos_consistent = _lgpos(page, 56)
        self.lgpos_attach = _lgpos(page, 80)
        self.dbid = struct.unpack_from('<I', page, 104)[0]
        self.sign_log = page[108:136]
        self.update_major = struct.unpack_from('<I', page, 232)[0]
        self.gen_min_required, self.gen_max_required = struct.unpack_from('<ii', page, 296)
        self.gen_max_committed = struct.unpack_from('<i', page, 416)[0]   # src/inc/daedef.hxx#L2913-L2916
        self.update_minor = struct.unpack_from('<I', page, 644)[0]

    @property
    def db_version(self):
        return (self.version, self.update_major, self.update_minor)

    @property
    def state_name(self):
        return DB_STATES.get(self.state, f'state {self.state}')


def _lgpos(data, offset):
    """LE_LGPOS as (generation, isec, ib), src/inc/daedef.hxx#L877-L885."""
    ib, isec, generation = struct.unpack_from('<HHi', data, offset)
    return (generation, isec, ib)


def _fmt_lgpos(lgpos):
    return f'({lgpos[0]:#x},{lgpos[1]:X},{lgpos[2]:X})'


# ---------------------------------------------------------------- pages

class _Page:
    """One small-format (4 or 8 KiB) page inside the replay's bytearray, changed with the same
    steps CPAGE uses (src/ese/cpage.cxx#L5211-L5614)."""

    def __init__(self, buffer, offset, size, pgno, reserved_tags_enabled):
        self.buf = buffer
        self.base = offset
        self.size = size
        self.pgno = pgno
        self.reserved_tags_enabled = reserved_tags_enabled

    def _u16(self, offset):
        return struct.unpack_from('<H', self.buf, self.base + offset)[0]

    def _set_u16(self, offset, value):
        struct.pack_into('<H', self.buf, self.base + offset, value & 0xffff)

    @property
    def dbtime(self):
        return struct.unpack_from('<q', self.buf, self.base + 8)[0]

    @dbtime.setter
    def dbtime(self, value):
        struct.pack_into('<q', self.buf, self.base + 8, value)

    @property
    def objid(self):
        return struct.unpack_from('<I', self.buf, self.base + 24)[0]

    @property
    def flags(self):
        return struct.unpack_from('<I', self.buf, self.base + 36)[0]

    cb_free = property(lambda self: self._u16(28), lambda self, v: self._set_u16(28, v))
    cb_uncommitted_free = property(lambda self: self._u16(30))
    ib_mic_free = property(lambda self: self._u16(32), lambda self, v: self._set_u16(32, v))

    @property
    def itag_mic_free(self):
        return self._u16(34) & _ITAG_MIC_FREE_MASK

    @property
    def ctag_reserved(self):
        """InitItagState: a legacy page stores 0 and means 1, src/inc/cpage.hxx#L1543-L1554."""
        return max(1, self._u16(34) >> _SHF_CTAG_RESERVED)

    def set_itag_mic_free(self, value):
        """SetITagMicFree_ / SetITagState_, src/inc/cpage.hxx#L1581-L1625."""
        stored = self._u16(34)
        if self.reserved_tags_enabled or stored >> _SHF_CTAG_RESERVED:
            self._set_u16(34, (self.ctag_reserved << _SHF_CTAG_RESERVED) | value)
        else:
            self._set_u16(34, value)

    @property
    def lines(self):
        return self.itag_mic_free - self.ctag_reserved

    def _tag_offset(self, itag):
        return self.base + self.size - 4 * (itag + 1)     # PtagFromItag_, src/ese/cpage.cxx#L1797-L1831

    def tag(self, itag):
        cb_, ib_ = struct.unpack_from('<HH', self.buf, self._tag_offset(itag))
        return cb_ & _TAG_MASK, ib_ & _TAG_MASK, (ib_ >> _TAG_FLAGS_SHIFT) & 0x7

    def set_tag(self, itag, cb, ib, flags):
        struct.pack_into('<HH', self.buf, self._tag_offset(itag), cb,
                         ib | (flags << _TAG_FLAGS_SHIFT))

    def line(self, itag):
        cb, ib, flags = self.tag(itag)
        start = self.base + _PAGE_HEADER + ib
        return bytes(self.buf[start:start + cb]), flags

    def _contiguous_free(self):
        """CbContiguousFree_, src/ese/cpage.cxx#L1692-L1718 (a normal-sized page has no adjustment)."""
        return (self.size - _PAGE_HEADER) - self.ib_mic_free - 4 * self.itag_mic_free

    def _reorganize(self):
        """ReorganizeData_: move every line down in order of ib, src/ese/cpage.cxx#L5518-L5614.
        Runtime scrubbing (JET_paramZeroDatabaseUnusedSpace) is not reproduced."""
        tags = sorted(range(self.itag_mic_free), key=lambda t: self.tag(t)[1])
        destination = 0
        data_start = self.base + _PAGE_HEADER
        for itag in tags:
            cb, ib, flags = self.tag(itag)
            if cb:
                if ib < destination:
                    raise ReplayRefused(f'page {self.pgno}: lines overlap')
                self.buf[data_start + destination:data_start + destination + cb] = \
                    self.buf[data_start + ib:data_start + ib + cb]
            self.set_tag(itag, cb, destination, flags)
            destination += cb
        self.ib_mic_free = destination

    def _free_space(self, cb):
        """FreeSpace_, src/ese/cpage.cxx#L1738-L1755."""
        if not 0 < cb <= self.cb_free:
            raise ReplayRefused(f'page {self.pgno}: no room for {cb} bytes')
        if self._contiguous_free() < cb:
            self._reorganize()
        if self._contiguous_free() < cb:
            raise ReplayRefused(f'page {self.pgno}: no room for {cb} bytes after reorganizing')

    def _copy(self, itag, data):
        _cb, ib, _flags = self.tag(itag)
        start = self.base + _PAGE_HEADER + ib
        self.buf[start:start + len(data)] = data

    def replace(self, iline, data, flags):
        """CPAGE::Replace / Replace_, src/ese/cpage.cxx#L3233-L3248, #L5211-L5313."""
        itag = iline + self.ctag_reserved
        cb_old, ib_old, _ = self.tag(itag)
        cb_total = len(data)
        cb_diff = cb_old - cb_total
        at_end = ib_old + cb_old == self.ib_mic_free
        if cb_diff >= 0 or (at_end and self._contiguous_free() >= -cb_diff):
            if at_end:
                self.ib_mic_free = self.ib_mic_free - cb_diff
            self.cb_free = self.cb_free + cb_diff
            ib_new = ib_old
        else:
            self.cb_free = self.cb_free + cb_old
            self.set_tag(itag, 0, 0, 0)
            self._free_space(cb_total)
            ib_new = self.ib_mic_free
            self.ib_mic_free = self.ib_mic_free + cb_total
            self.cb_free = self.cb_free - cb_total
        self.set_tag(itag, cb_total, ib_new, flags)
        self._copy(itag, data)

    def insert(self, iline, data, flags):
        """CPAGE::Insert / Insert_ / ExpandTagArray_, src/ese/cpage.cxx#L3269-L3294, #L5333-L5461."""
        itag = iline + self.ctag_reserved
        cb_total = len(data)
        self._free_space(cb_total + 4)
        mic = self.itag_mic_free
        if itag != mic:
            # move tags itag .. mic-1 one slot down in memory (to itag+1 .. mic)
            low = self._tag_offset(mic)
            high = self._tag_offset(itag) + 4
            self.buf[low:high - 4] = self.buf[low + 4:high]
        self.set_itag_mic_free(mic + 1)
        self.set_tag(itag, cb_total, self.ib_mic_free, flags)
        self.ib_mic_free = self.ib_mic_free + cb_total
        self.cb_free = self.cb_free - (cb_total + 4)
        self._copy(itag, data)

    def checksum_ok(self):
        stored = struct.unpack_from('<Q', self.buf, self.base)[0]
        page = bytes(self.buf[self.base:self.base + self.size])
        if self.flags & _PAGE_NEW_CHECKSUM:
            return stored == ese_log.checksum_new(page, self.pgno)
        return stored == ((self.pgno << 32) | ese_log.checksum_old(page))

    def set_checksum(self):
        """SetPageChecksum for a small page: set the new-format flag, then the XOR-ECC
        checksum of the whole page with the first 8 bytes counted as zero
        (src/ese/_osu/checksumu.cxx#L141-L151, #L270-L335, #L666-L676)."""
        struct.pack_into('<I', self.buf, self.base + 36, self.flags | _PAGE_NEW_CHECKSUM)
        page = bytes(self.buf[self.base:self.base + self.size])
        struct.pack_into('<Q', self.buf, self.base, ese_log.checksum_new(page, self.pgno))


def _split_node(line, flags):
    """(prefix count, suffix bytes, data bytes) of a node, NDILineToKeydataflags,
    src/ese/node.cxx#L143-L229."""
    position = 0
    prefix = 0
    if flags & _ND_COMPRESSED:
        prefix = struct.unpack_from('<H', line, 0)[0] & _KEY_MASK
        position = 2
    suffix = struct.unpack_from('<H', line, position)[0] & _KEY_MASK
    position += 2
    if position + suffix > len(line):
        raise ReplayRefused('a node whose key runs past its line')
    return prefix, line[position:position + suffix], line[position + suffix:]


def _node_bytes(prefix_count, suffix, data):
    """CdataNDIKeydataflagsToDataflags / CdataNDIPrefixAndKeydataflagsToDataflags with the
    prefix count unchanged (src/ese/node.cxx#L233-L362): the prefix count when there is one, the
    suffix count, the suffix, the data."""
    out = bytearray()
    if prefix_count:
        out += struct.pack('<H', prefix_count)
    out += struct.pack('<H', len(suffix))
    out += suffix
    out += data
    return bytes(out)


def after_image(diff, old, fdiff2, page_size):
    """ErrLGGetAfterImage, src/ese/logdiff.cxx#L1150-L1292: rebuild the new record data from the
    logged diff and the data on the page."""
    new = bytearray()
    old_position = 0
    position = 0
    end = len(diff)
    while position < end:
        if fdiff2:
            # DIFFHDR2: ib (2 bytes) then flags, src/inc/logapi.hxx#L36-L65
            if position + 3 > end:
                raise ReplayRefused('a diff header runs past the record')
            ib = struct.unpack_from('<H', diff, position)[0]
            hflags = diff[position + 2]
            position += 3
            same_length, insert, two_bytes = hflags & 0x20, hflags & 0x40, hflags & 0x80
        else:
            # DIFFHDR: 13-bit ib and three flags in one word, src/inc/logapi.hxx#L15-L34
            if position + 2 > end:
                raise ReplayRefused('a diff header runs past the record')
            word = struct.unpack_from('<H', diff, position)[0]
            position += 2
            ib = word & 0x1fff
            same_length, insert, two_bytes = word & 0x2000, word & 0x4000, word & 0x8000
        if ib < old_position:
            raise ReplayRefused('a diff that goes backwards')
        new += old[old_position:ib]
        old_position = ib
        cb_new, position = _diff_length(diff, position, two_bytes)
        if insert:
            new += diff[position:position + cb_new]
            position += cb_new
        else:
            if same_length:
                cb_old = cb_new
            else:
                cb_old, position = _diff_length(diff, position, two_bytes)
            new += diff[position:position + cb_new]
            position += cb_new
            old_position += cb_old
        if position > end or old_position > len(old) or len(new) > page_size:
            raise ReplayRefused('a diff that runs past its data')
    new += old[old_position:]
    if len(new) > page_size:
        raise ReplayRefused('a rebuilt record larger than a page')
    return bytes(new)


def _diff_length(diff, position, two_bytes):
    """(length, next position) of a diff length field, one or two bytes as the header says
    (src/ese/logdiff.cxx#L1202-L1242). A field that runs past the diff is refused: ESE checks the
    diff pointer against its end after each piece (src/ese/logdiff.cxx#L1252-L1256)."""
    size = 2 if two_bytes else 1
    if position + size > len(diff):
        raise ReplayRefused('a diff length runs past the record')
    if two_bytes:
        return struct.unpack_from('<H', diff, position)[0], position + 2
    return diff[position], position + 1


# ---------------------------------------------------------------- finding the logs

_LOG_NAME = re.compile(r'^(?P<base>.+?)(?P<gen>[0-9A-Fa-f]{5}|[0-9A-Fa-f]{8})?\.log$', re.IGNORECASE)


def log_role(path, generation):
    """'archive', 'current' or 'temp' for a log file name, as LGMakeLogName builds them
    (src/ese/_log/logstream.cxx#L269-L334): base plus generation digits for an archived
    generation, base alone for the current log, base plus 'tmp' for the temp log."""
    name = os.path.basename(path)
    match = _LOG_NAME.match(name)
    if match is None:
        return 'other'
    if match.group('gen'):
        return 'archive' if int(match.group('gen'), 16) == generation else 'other'
    if name[:-4].lower().endswith('tmp'):
        return 'temp'
    return 'current'


def find_logs(folder, header):
    """{generation: (path, bytes)} of the logs in `folder` that carry the database's log
    signature, and a list of (name, reason) for .log files that were passed over."""
    found = {}
    skipped = []
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith('.log'):
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        with open(path, 'rb') as handle:
            head = handle.read(ese_log.LOG_HEADER_SIZE)
            try:
                log_header = ese_log.LogHeader(head)
            except LogError as exc:
                skipped.append((name, str(exc)))
                continue
            if log_header.sign_log != header.sign_log:
                skipped.append((name, 'a different log signature'))
                continue
            data = head + handle.read()
        match = _LOG_NAME.match(name)
        if match and match.group('gen') and int(match.group('gen'), 16) != log_header.generation:
            raise ReplayRefused(f'{name} holds generation {log_header.generation}, not the one its name gives')
        previous = found.get(log_header.generation)
        if previous is not None and previous[1] != data:
            raise ReplayRefused(f'two different logs hold generation {log_header.generation}')
        found[log_header.generation] = (path, data)
    return found, skipped


# ---------------------------------------------------------------- the replay

class ReplayResult:
    """What a replay did. `data` is the replayed copy, or None when it refused."""

    def __init__(self):
        self.data = None
        self.refused = None
        self.state = None
        self.logs = []
        self.records = 0
        self.redone = 0
        self.skipped_newer = 0
        self.pages = []

    def summary(self):
        if self.refused:
            return f'not replayed: {self.refused}'
        if self.data is None or not self.logs:
            return f'not replayed: the header records {self.state}'
        names = [os.path.basename(path) for path in self.logs]
        logs = ', '.join(names) if len(names) <= 3 else f'{len(names)} logs, {names[0]} to {names[-1]}'
        return (f'replayed {self.redone} change(s) from {logs} onto {len(self.pages)} page(s) '
                f'({self.skipped_newer} already on the page)')


def replay(db_bytes, logs):
    """Replay `logs` ({generation: (path, bytes)}) onto a copy of `db_bytes`.

    Returns a ReplayResult; its `data` is the replayed bytes, the unchanged bytes for a
    database already in clean shutdown, or None with `refused` set."""
    result = ReplayResult()
    try:
        _replay(bytes(db_bytes), logs, result)
    except (ReplayRefused, LogError) as exc:
        result.data = None
        result.refused = str(exc) or type(exc).__name__
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Anything else is a case this module did not foresee: refuse rather than raise.
        result.data = None
        result.refused = f'unexpected {type(exc).__name__}: {exc}'
    return result


def _replay(db_bytes, logs, result):
    header = DatabaseHeader(db_bytes)
    result.state = header.state_name
    if header.state == _DB_STATE_CLEAN:
        result.data = db_bytes
        return
    if header.state != _DB_STATE_DIRTY:
        raise ReplayRefused(f'the header records {header.state_name}')
    if header.page_size not in _SUPPORTED_PAGE_SIZES:
        raise ReplayRefused(f'a page size of {header.page_size}')
    if header.gen_min_required <= 0 or header.gen_max_required < header.gen_min_required:
        raise ReplayRefused('the header names no required log generations')
    first = header.gen_min_required
    if not logs or first not in logs:
        raise ReplayRefused(f'log generation {first} (required) is missing')
    last = max(logs)
    for generation in range(first, last + 1):
        if generation not in logs:
            raise ReplayRefused(f'log generation {generation} is missing')
    if last < header.gen_max_required:
        raise ReplayRefused(f'log generation {header.gen_max_required} (required) is missing')
    if last < header.gen_max_committed:
        # ErrLGCheckDatabaseGens: JET_errCommittedLogFilesMissing (src/ese/_log/logredo.cxx#L13614-L13636)
        raise ReplayRefused(f'log generation {header.gen_max_committed} (committed) is missing')
    if log_role(logs[last][0], last) != 'current':
        # Redo ends at the current log; without it ESE stops with JET_errMissingLogFile
        # (src/ese/_log/logredo.cxx#L4263-L4297, #L4317-L4323). ESE carries on when the temp log
        # exists; this module does not.
        raise ReplayRefused(f'the newest log present, generation {last}, is not the current log '
                            '(base name with no generation); the current log is missing')
    if not (0 < header.lgpos_consistent[0] and header.lgpos_consistent < header.lgpos_attach):
        raise ReplayRefused('the header records no consistent point before its last attach')
    attached_dbid = None
    attach_seen = False
    if header.lgpos_attach[0] < first:
        # The attach is in a log no longer needed: start at the first required log, with the
        # dbid its header's attachment list gives (LGFakeCheckpointToLogFile).
        attached_dbid = _attach_from_log_header(logs[first][1], header)
        attach_seen = True

    state = _ReplayState(bytearray(db_bytes), header)
    previous_create = None

    for generation in range(first, last + 1):
        path, data = logs[generation]
        log_header, records = ese_log.read_records(data)
        if previous_create is not None and log_header.tm_prev_gen != previous_create:
            raise ReplayRefused(f'{os.path.basename(path)} does not follow the log before it')
        previous_create = log_header.tm_create
        result.logs.append(path)
        for record in records:
            if not attach_seen:
                if record.lgpos == header.lgpos_attach:
                    attached_dbid = _check_attach(record, header)
                    attach_seen = True
                continue
            result.records += 1
            _apply(record, attached_dbid, state, result)

    if not attach_seen:
        raise ReplayRefused(f'no attach record at {_fmt_lgpos(header.lgpos_attach)}')
    still_open = sorted(procid for procid, count in state.open_changes.items() if count)
    if still_open:
        raise ReplayRefused(f'session(s) {still_open} changed this database and never committed; '
                            'undo is not implemented')
    for pgno in sorted(state.pages):
        state.pages[pgno].set_checksum()
    result.pages = sorted(state.pages)
    result.data = bytes(state.work)


class _ReplayState:
    """The replay's working copy and what it has seen so far."""

    def __init__(self, work, header):
        self.work = work
        self.header = header
        self.page_size = header.page_size
        self.reserved_tags = header.db_version >= _RESERVED_TAGS_DB_VERSION
        self.pages = {}            # pgno -> _Page changed by the replay
        self.checked = set()       # pgnos whose stored checksum was verified
        self.open_changes = {}     # procid -> number of changes to this database not yet committed
        self.begun = set()         # procids seen beginning a transaction from level 0
        self.macros = {}           # procid -> dbtimes of its macros begun and not yet ended

    def page(self, pgno, where):
        """The page as the replay has it, its stored checksum verified on first use."""
        page = self.pages.get(pgno)
        if page is not None:
            return page
        offset = (pgno + 1) * self.page_size              # page 0 and its shadow come first
        if pgno <= 0 or offset + self.page_size > len(self.work):
            raise ReplayRefused(f'page {pgno} lies outside the database file ({where})')
        page = _Page(self.work, offset, self.page_size, pgno, self.reserved_tags)
        if pgno not in self.checked:
            if not page.checksum_ok():
                raise ReplayRefused(f'page {pgno} fails its checksum')
            self.checked.add(pgno)
        return page


def _attach_from_log_header(log_bytes, header):
    """The dbid the log header's attachment list gives this database: the ATTACHINFO whose
    signDb, lgposAttach and lgposConsistent are the database header's (dbid 0, flags 1,
    cbNames 2, dbtime 4, objidLast 12, cpgDatabaseSizeMax 16, lgposAttach 20, lgposConsistent
    28, signDb 36, then the names; src/inc/log.hxx#L85-L101). The list ends at a dbid of 0."""
    ese_log.LogHeader(log_bytes)                          # its checksum covers the list
    position = _ATTACH_INFO_OFFSET
    end = _ATTACH_INFO_OFFSET + _ATTACH_LIST_SIZE
    while position < end and log_bytes[position] != 0:
        if position + _ATTACH_INFO_SIZE > end:
            raise ReplayRefused('the log header attachment list runs past its end')
        dbid = log_bytes[position]
        cb_names = struct.unpack_from('<H', log_bytes, position + 2)[0]
        if (log_bytes[position + 36:position + 64] == header.sign_db
                and _lgpos(log_bytes, position + 20) == header.lgpos_attach
                and _lgpos(log_bytes, position + 28) == header.lgpos_consistent):
            return dbid
        position += _ATTACH_INFO_SIZE + cb_names
    raise ReplayRefused('the database was attached in a log older than the first required one, '
                        "and that log's header does not list this attachment")


def _check_attach(record, header):
    """The LRATTACHDB at the header's lgposAttach must name this database
    (src/inc/logapi.hxx#L1696-L1716: dbid at 3, lgposConsistent at 8, signDb at 16, signLog at 44)."""
    if record.lrtyp != _LR_ATTACH:
        raise ReplayRefused(f'the record at {_fmt_lgpos(header.lgpos_attach)} is not an attach')
    data = record.data
    if data[16:44] != header.sign_db:
        raise ReplayRefused('the attach record names a different database signature')
    if data[44:72] != header.sign_log:
        raise ReplayRefused('the attach record names a different log signature')
    if _lgpos(data, 8) != header.lgpos_consistent:
        raise ReplayRefused('the attach record and the header disagree on lgposConsistent')
    return data[3]


def _apply(record, dbid, state, result):
    lrtyp = record.lrtyp
    data = record.data
    where = _fmt_lgpos(record.lgpos)
    if lrtyp in _IGNORABLE:
        return
    if lrtyp in (_LR_BEGIN, _LR_BEGIN0):
        procid = struct.unpack_from('<H', data, 1)[0]   # LRTRX_, src/inc/logapi.hxx#L1362-L1373
        if data[3] & 0x0f:
            # levelBeginFrom above 0 (LRBEGIN, src/inc/logapi.hxx#L1376-L1386): a nested
            # transaction inside one already open, whose changes stay open
            return
        if state.open_changes.get(procid):
            raise ReplayRefused(f'session {procid} begins a transaction with changes open at {where}')
        # a transaction from level 0: ESE starts redoing this session's records here
        # (src/ese/_log/logredo.cxx#L7012-L7052)
        state.begun.add(procid)
        return
    if lrtyp == _LR_COMMIT:
        return
    if lrtyp == _LR_COMMIT0:
        state.open_changes[struct.unpack_from('<H', data, 1)[0]] = 0
        return
    if lrtyp == _LR_ROLLBACK:
        procid = struct.unpack_from('<H', data, 1)[0]
        if state.open_changes.get(procid):
            raise ReplayRefused(f'session {procid} rolls back a change to this database at {where}; '
                                'undo is not implemented')
        return
    if lrtyp in (_LR_MACRO_BEGIN, _LR_MACRO_COMMIT, _LR_MACRO_ABORT):
        # LRMACROBEGIN / LRMACROEND: procid, then the macro's dbtime (src/inc/logapi.hxx#L1474-L1493);
        # ESE keeps a macro per session and dbtime (ErrSetMacroGoing / ResetMacroGoing,
        # src/ese/_log/logredo.cxx#L12572-L12620)
        procid, macro_dbtime = struct.unpack_from('<Hq', data, 1)
        macros = state.macros.setdefault(procid, set())
        if lrtyp == _LR_MACRO_BEGIN:
            macros.add(macro_dbtime)
        else:
            macros.discard(macro_dbtime)
        return
    if lrtyp in (_LR_ATTACH, _LR_DETACH):
        if data[3] == dbid:
            raise ReplayRefused(f'the database is attached or detached again at {where}')
        return
    if lrtyp == _LR_SET_DB_VERSION:
        # LRSETDBVERSION: dbid at 1, then three ULONG version parts, src/inc/logapi.hxx#L2456-L2494
        if data[1] == dbid and struct.unpack_from('<III', data, 2) != state.header.db_version:
            raise ReplayRefused(f'a database version change at {where}')
        return
    if lrtyp in _PAGE_RECORD_TYPES:
        if data[3] != dbid:
            return                                       # another database
        if lrtyp in _ALREADY_ON_PAGE_ONLY:
            _pass_over(record, state, result)
            return
        if lrtyp not in (_LR_INSERT, _LR_REPLACE, _LR_REPLACE_D):
            raise ReplayRefused(f'a {record.name} record for this database at {where} is not replayed '
                                'by this module')
        _redo_node(record, state, result)
        return
    raise ReplayRefused(f'a {record.name} record at {where} is not handled by this module')


def _count_change(state, procid, level):
    """A change to this database inside a transaction, kept open until its Commit0."""
    if level > 0:
        state.open_changes[procid] = state.open_changes.get(procid, 0) + 1


def _pass_over(record, state, result):
    """Delete, FlagDelete, Delta, Split2 or Merge2: allowed only when every page it names
    already holds its dbtime or a later one, so that ESE's redo would change nothing."""
    data = record.data
    where = _fmt_lgpos(record.lgpos)
    procid, _dbid, pgno, dbtime, _before, _trx, level = struct.unpack_from('<HBIqqIB', data, 1)
    _count_change(state, procid, level)
    named = [pgno] + [struct.unpack_from('<I', data, offset)[0]
                      for offset in _ALREADY_ON_PAGE_ONLY[record.lrtyp]]
    for number in named:
        if number == 0:
            continue
        page = state.page(number, where)
        if dbtime > page.dbtime:
            raise ReplayRefused(f'a {record.name} record for this database at {where} would change page '
                                f'{number}, and this module does not redo {record.name}')
    if record.lgpos[0] > state.header.gen_max_required:
        raise ReplayRefused(f'page {pgno} is newer than the log at {where} past the required range')
    result.skipped_newer += 1


def _redo_node(record, state, result):
    """ErrLGRIRedoNodeOperation for Insert, Replace and ReplaceD (src/ese/_log/logredo.cxx#L3027-L3815)."""
    data = record.data
    header = state.header
    where = _fmt_lgpos(record.lgpos)
    # LRPAGE_ / LRNODE_, src/inc/logapi.hxx#L377-L439
    procid, _dbid, pgno, dbtime, dbtime_before, _trx, level, iline, page_flags = \
        struct.unpack_from('<HBIqqIBHB', data, 1)
    objid_fdp = struct.unpack_from('<I', data, 40)[0]
    versioned = page_flags & 0x01                         # fLRPageVersioned, src/inc/logapi.hxx#L369
    if level <= 0:
        raise ReplayRefused(f'a change outside a transaction at {where}')
    if dbtime <= dbtime_before:
        # ESE only asserts that a change moves the page's dbtime forward
        # (src/ese/_log/logredo.cxx#L408-L413); a record that does not cannot be placed.
        raise ReplayRefused(f'the record at {where} does not move the page dbtime forward')
    _count_change(state, procid, level)

    page = state.page(pgno, where)
    if dbtime <= page.dbtime:
        # FLGINeedRedo is false. Allowed only while the database may hold pages from these
        # logs, src/ese/_log/logredo.cxx#L425-L439.
        if record.lgpos[0] > header.gen_max_required:
            raise ReplayRefused(f'page {pgno} is newer than the log at {where} past the required range')
        result.skipped_newer += 1
        return
    if procid not in state.begun:
        raise ReplayRefused(f'the record at {where} would change page {pgno} for session {procid}, '
                            'whose transaction began before the replay started')
    if state.macros.get(procid):
        raise ReplayRefused(f'the record at {where} would change page {pgno} inside a macro')
    if pgno not in state.pages and page.cb_uncommitted_free:
        raise ReplayRefused(f'page {pgno} holds uncommitted free space, which the replay does not track')
    if page.dbtime != dbtime_before:
        raise ReplayRefused(f'page {pgno} has dbtime {page.dbtime}, the record at {where} expects '
                            f'{dbtime_before}')
    if page.objid != objid_fdp:
        raise ReplayRefused(f'page {pgno} belongs to object {page.objid}, the record at {where} to {objid_fdp}')
    if page.flags & 0x0002 == 0:                          # fPageLeaf, src/inc/cpage.hxx#L677
        raise ReplayRefused(f'page {pgno} is not a leaf page ({where})')
    state.pages[pgno] = page
    version_flag = _ND_VERSION if versioned else 0       # fDIRNull vs fDIRNoVersion, src/ese/_log/logredo.cxx#L3039
    if record.lrtyp == _LR_INSERT:
        _redo_insert(record, page, iline, version_flag)
    else:
        _redo_replace(record, page, iline, version_flag, state.page_size)
    page.dbtime = dbtime                                  # src/ese/_log/logredo.cxx#L3806-L3808
    result.redone += 1


def _redo_insert(record, page, iline, version_flag):
    """lrtypInsert (src/ese/_log/logredo.cxx#L3296-L3346) through ErrNDInsert and NDInsert
    (src/ese/node.cxx#L1447-L1540, #L1204-L1235)."""
    data = record.data
    # LRINSERT: cbSuffix, cbPrefix, cbData, then prefix, suffix and data, src/inc/logapi.hxx#L637-L659
    cb_suffix, cb_prefix, cb_data = struct.unpack_from('<HHH', data, 44)
    body = data[50:]
    suffix = body[cb_prefix:cb_prefix + cb_suffix]
    value = body[cb_prefix + cb_suffix:cb_prefix + cb_suffix + cb_data]
    if not 0 <= iline <= page.lines:
        raise ReplayRefused(f'page {page.pgno}: insert at line {iline} of {page.lines}')
    flags = (_ND_COMPRESSED if cb_prefix else 0) | version_flag
    node = _node_bytes(cb_prefix, suffix, value)
    # ErrNDInsert's room check against free space less uncommitted free (src/ese/node.cxx#L1475-L1501);
    # the uncommitted-free path it can take is not reproduced, so a page that needs it refuses.
    if len(node) + 4 > page.cb_free - page.cb_uncommitted_free:
        raise ReplayRefused(f'page {page.pgno}: no room to insert')
    page.insert(iline, node, flags)


def _redo_replace(record, page, iline, version_flag, page_size):
    """lrtypReplace / lrtypReplaceD (src/ese/_log/logredo.cxx#L3493-L3611) through ErrNDReplace
    (src/ese/node.cxx#L1659-L1788)."""
    data = record.data
    # LRREPLACE: cb (top bit = DIFFHDR2), cbOldData, cbNewData, then the data, src/inc/logapi.hxx#L708-L738
    cb_raw, _cb_old, cb_new = struct.unpack_from('<HHH', data, 44)
    payload = data[50:50 + (cb_raw & 0x7fff)]
    if not 0 <= iline < page.lines:
        raise ReplayRefused(f'page {page.pgno}: replace at line {iline} of {page.lines}')
    line, line_flags = page.line(iline + page.ctag_reserved)
    prefix, suffix, old_value = _split_node(line, line_flags)
    if record.lrtyp == _LR_REPLACE_D:
        new_value = after_image(payload, old_value, bool(cb_raw & 0x8000), page_size)
    else:
        new_value = payload
    if len(new_value) != cb_new:
        raise ReplayRefused(f'page {page.pgno}: the rebuilt record is {len(new_value)} bytes, '
                            f'the log says {cb_new}')
    grow = len(new_value) - len(old_value)
    if grow > 0 and grow > page.cb_free - page.cb_uncommitted_free:
        raise ReplayRefused(f'page {page.pgno}: no room to grow a record')
    flags = (line_flags | version_flag) & ~_ND_COMPRESSED
    if prefix:
        flags |= _ND_COMPRESSED
    page.replace(iline, _node_bytes(prefix, suffix, new_value), flags)


# ---------------------------------------------------------------- the caller's entry point

def replayed_database(path):
    """(bytes or None, summary) for the ESE database at `path`, replaying the logs beside it.

    Returns the replayed bytes when the header records a dirty shutdown and the replay
    succeeds, the bytes as stored when it records a clean shutdown, and None when the
    replay refused; the summary says which and why. The files are only read."""
    with open(path, 'rb') as handle:
        db_bytes = handle.read()
    try:
        header = DatabaseHeader(db_bytes)
    except ReplayRefused as exc:
        return None, f'not replayed: {exc}'
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, f'not replayed: unexpected {type(exc).__name__}: {exc}'
    if header.state == _DB_STATE_CLEAN:
        return db_bytes, 'not replayed: the header records clean shutdown'
    if header.state != _DB_STATE_DIRTY:
        return None, f'not replayed: the header records {header.state_name}'
    try:
        logs, _skipped = find_logs(os.path.dirname(os.path.abspath(path)), header)
    except (ReplayRefused, OSError) as exc:
        return None, f'not replayed: {exc}'
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return None, f'not replayed: unexpected {type(exc).__name__}: {exc}'
    result = replay(db_bytes, logs)
    return result.data, result.summary()
