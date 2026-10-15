"""Read the records of an ESE transaction log (Svc.log, edb.log and the like) the way ESE's
own recovery reads them, standard library only.

Every structure and rule below is taken from Microsoft's ESE source (MIT licence) at the
commit DLEAPP already cites:
https://github.com/microsoft/Extensible-Storage-Engine/tree/7030fe7407615160e54d152e4ef704eede2fdd7e
Paths in the comments are relative to dev/ese there, written as path#Lline.

Only the log format ESE has written since log major version 8 is read: a 4096-byte file
header, then 4096-byte segments, each with its own header and checksum
(src/inc/_logstream.hxx#L11-L25). The older LRCHECKSUM format (major version 7 and below,
src/inc/_logstream.hxx#L27, src/inc/daedef.hxx#L2565-L2567) is refused. Nothing here guesses: a checksum
that does not match, a segment out of place, a record type whose size this module does not
know, or a record that runs past its segment raises LogError with the reason.

ESE corrects a single flipped bit in a segment from its ECC checksum
(src/ese/_osu/checksumu.cxx#L474-L510, called from src/ese/_log/logread.cxx#L1451-L1460). This module does not: a
segment whose checksum does not match is never read as data. That is stricter than ESE, so
a log ESE would repair is refused here instead.
"""

import struct

SEGMENT_SIZE = 4096          # LOG_SEGMENT_SIZE, src/inc/_logstream.hxx#L24
LOG_HEADER_SIZE = 4096       # cbLogFileHeader, src/inc/log.hxx#L130
SEGMENT_HEADER_SIZE = 40     # LGSEGHDR, src/inc/_logstream.hxx#L11-L19: checksum 8, lgpos 8, logtime 8, reserved 12, flags 4
JET_FILETYPE_LOG = 3         # published/inc/jethdr.w#L5432
OLD_LRCK_MAJOR = 7           # ulLGVersionMajor_OldLrckFormat, src/inc/daedef.hxx#L2565-L2567
ZERO_FILLED_VERSION = (8, 4000, 2)  # ulLGVersion*_ZeroFilled, src/inc/daedef.hxx#L2569-L2572

# LRTYP numbers, src/inc/logapi.hxx#L111-L272.
LRTYP_NAMES = {
    0: 'NOP', 1: 'Init', 2: 'Term', 3: 'MS', 4: 'End', 5: 'Begin', 6: 'Commit', 7: 'Rollback',
    8: 'Begin0', 9: 'Commit0', 10: 'Refresh', 11: 'MacroBegin', 12: 'MacroCommit',
    13: 'MacroAbort', 14: 'CreateDB', 15: 'AttachDB', 16: 'DetachDB', 17: 'RecoveryUndo',
    18: 'RecoveryQuit', 19: 'FullBackup', 20: 'IncBackup', 21: 'JetOp', 22: 'Trace',
    23: 'ShutDownMark', 24: 'CreateMultipleExtentFDP', 25: 'CreateSingleExtentFDP',
    26: 'ConvertFDP', 27: 'Split', 28: 'Merge', 29: 'Insert', 30: 'FlagInsert',
    31: 'FlagInsertAndReplaceData', 32: 'FlagDelete', 33: 'Replace', 34: 'ReplaceD',
    35: 'Delete', 36: 'UndoInfo', 37: 'Delta', 38: 'SetExternalHeader', 39: 'Undo',
    42: 'Checksum', 45: 'ExtRestore', 46: 'Backup', 48: 'EmptyTree', 49: 'Init2', 50: 'Term2',
    51: 'RecoveryUndo2', 52: 'RecoveryQuit2', 53: 'BeginDT', 54: 'PrepCommit',
    55: 'PrepRollback', 57: 'ForceWriteLog', 58: 'ConvertFDP2', 59: 'ExtRestore2',
    60: 'Backup2', 61: 'ForceLogRollover', 62: 'Split2', 63: 'Merge2', 64: 'Scrub',
    65: 'PageMove', 66: 'PagePatchRequest', 67: 'MacroInfo', 68: 'ExtendDB', 69: 'CommitCtx',
    70: 'ScanCheck', 71: 'NOP2', 72: 'ReAttach', 73: 'MacroInfo2', 74: 'FreeFDP',
    75: 'Ignored9', 76: 'FragmentBegin', 77: 'Fragment', 78: 'ShrinkDB', 79: 'CreateDBFinish',
    80: 'RecoveryQuitKeepAttachments', 81: 'TrimDB', 92: 'SetDbVersion', 93: 'Delta64',
    94: 'ShrinkDB2', 95: 'NewPage', 96: 'RootPageMove', 97: 'SignalAttachDb', 98: 'ScanCheck2',
    99: 'ShrinkDB3', 100: 'ExtentFreed', 101: 'ExtentFreed2',
}
for _n in range(82, 92):
    LRTYP_NAMES[_n] = f'Ignored{_n - 72}'
LRTYP_MAX = 102              # lrtypMax, src/inc/logapi.hxx#L272
LRTYP_NOP = 0
LRTYP_UNDO_INFO = 36
LRTYP_RECOVERY_UNDO = 17
LRTYP_RECOVERY_UNDO2 = 51
LRTYP_FRAGMENT_BEGIN = 76
LRTYP_FRAGMENT = 77

# Sizes of the fixed part of each record (mplrtypn, src/ese/_log/logread.cxx#L3434-L3542), worked out from
# the packed structures in logapi.hxx (#include <pshpack1.h> at src/inc/logapi.hxx#L6). LRPAGE_ is
# 32 bytes (src/inc/logapi.hxx#L377-L423) and LRNODE_ 44 (src/inc/logapi.hxx#L426-L439); the source asserts
# LRDELTA32 at 54 and LRDELTA64 at 58 (src/inc/logapi.hxx#L785-L786), which pins both.
_LRPAGE = 32
_LRNODE = 44
FIXED_SIZE = {
    0: 1,                    # LRNOP, src/inc/logapi.hxx#L311
    1: 568, 49: 576,         # LRINIT / LRINIT2: LR + DBMS_PARAM (567, src/inc/daedef.hxx#L3835-L3850) + LOGTIME
    2: 18, 18: 18,           # LRTERMREC, src/inc/logapi.hxx#L1905-L1915
    50: 26, 52: 26, 80: 26,  # LRTERMREC2, src/inc/logapi.hxx#L1918-L1926
    3: 9,                    # LRMS, src/inc/logapi.hxx#L1803-L1813
    4: 1,                    # lrtypEnd is a bare LRTYP, src/ese/_log/logread.cxx#L3440
    5: 4,                    # LRBEGIN, src/inc/logapi.hxx#L1376-L1386
    6: 4,                    # LRCOMMIT, src/inc/logapi.hxx#L1433-L1441
    7: 4,                    # LRROLLBACK, src/inc/logapi.hxx#L1455-L1463
    8: 8, 53: 8,             # LRBEGIN0 / LRBEGINDT, src/inc/logapi.hxx#L1389-L1403
    9: 8,                    # LRCOMMIT0, src/inc/logapi.hxx#L1444-L1452
    10: 7,                   # LRREFRESH, src/inc/logapi.hxx#L1407-L1415
    11: 11, 12: 11, 13: 11,  # LRMACROBEGIN / LRMACROEND, src/inc/logapi.hxx#L1474-L1493
    14: 43,                  # LRCREATEDB, src/inc/logapi.hxx#L1608-L1626
    15: 75,                  # LRATTACHDB, src/inc/logapi.hxx#L1696-L1716
    16: 7,                   # LRDETACHDB, src/inc/logapi.hxx#L1739-L1774
    17: 1, 51: 9,            # LRRECOVERYUNDO / 2, src/inc/logapi.hxx#L1929-L1947
    21: 4,                   # LRJETOP, src/inc/logapi.hxx#L2047-L2056
    22: 5, 61: 5,            # LRTRACE (and LRFORCELOGROLLOVER), src/inc/logapi.hxx#L2059-L2077
    23: 1,                   # LRSHUTDOWNMARK, src/inc/logapi.hxx#L303
    24: _LRPAGE + 24,        # LRCREATEMEFDP, src/inc/logapi.hxx#L1270-L1283
    25: _LRPAGE + 16,        # LRCREATESEFDP, src/inc/logapi.hxx#L1286-L1297
    26: _LRPAGE + 28,        # LRCONVERTFDP_OBSOLETE, src/inc/logapi.hxx#L1300-L1317
    58: _LRPAGE + 36,        # LRCONVERTFDP, src/inc/logapi.hxx#L1320-L1329
    29: _LRNODE + 6,         # LRINSERT, src/inc/logapi.hxx#L637-L659
    30: _LRNODE + 4,         # LRFLAGINSERT, src/inc/logapi.hxx#L662-L681
    31: _LRNODE + 8,         # LRFLAGINSERTANDREPLACEDATA, src/inc/logapi.hxx#L684-L704
    32: _LRNODE,             # LRFLAGDELETE, src/inc/logapi.hxx#L789-L794
    33: _LRNODE + 6, 34: _LRNODE + 6,  # LRREPLACE, src/inc/logapi.hxx#L708-L738
    35: _LRNODE,             # LRDELETE, src/inc/logapi.hxx#L797-L802
    36: _LRNODE + 12,        # LRUNDOINFO, src/inc/logapi.hxx#L829-L852
    37: 54, 93: 58,          # LRDELTA32 / LRDELTA64, src/inc/logapi.hxx#L785-L786
    38: _LRNODE + 2,         # LRSETEXTERNALHEADER, src/inc/logapi.hxx#L855-L870
    39: _LRNODE + 7,         # LRUNDO, src/inc/logapi.hxx#L805-L826
    48: _LRNODE + 2,         # LREMPTYTREE, src/inc/logapi.hxx#L1037-L1052
    54: 7, 55: 3,            # LRPREPCOMMIT / LRPREPROLLBACK, src/inc/logapi.hxx#L1421-L1471
    57: 3,                   # LRFORCEWRITELOG, src/inc/logapi.hxx#L1594-L1599
    62: _LRPAGE + 78,        # LRSPLITNEW: LRSPLIT_ (src/inc/logapi.hxx#L873-L909) + flags + cbPageBeforeImage
    63: _LRPAGE + 64,        # LRMERGENEW: LRMERGE_ (src/inc/logapi.hxx#L954-L998) + flags + cbPageBeforeImage
    64: _LRNODE + 10,        # LRSCRUB, src/inc/logapi.hxx#L442-L472
    66: 46,                  # LRPAGEPATCHREQUEST, src/inc/logapi.hxx#L323-L347
    76: 7,                   # LRFRAGMENTBEGIN, src/inc/logapi.hxx#L2427-L2440
    77: 3,                   # LRFRAGMENT, src/inc/logapi.hxx#L2442-L2454
    78: 10, 94: 10,          # LRSHRINKDB, src/inc/logapi.hxx#L2254-L2307
    79: 4,                   # LRCREATEDBFINISH, src/inc/logapi.hxx#L1679-L1688
    81: 10,                  # LRTRIMDB, src/inc/logapi.hxx#L2351-L2394
    92: 14,                  # LRSETDBVERSION, src/inc/logapi.hxx#L2456-L2494
    95: 20,                  # LRNEWPAGE, src/inc/logapi.hxx#L1055-L1094
    96: 16,                  # LRROOTPAGEMOVE, src/inc/logapi.hxx#L1218-L1264
    97: 2,                   # LRSIGNALATTACHDB, src/inc/logapi.hxx#L1777-L1800
    98: 27,                  # LRSCANCHECK2, src/inc/logapi.hxx#L535-L633
    99: 18,                  # LRSHRINKDB3, src/inc/logapi.hxx#L2315-L2349
    100: 11,                 # LREXTENTFREED, src/inc/logapi.hxx#L2496-L2544
    101: 19,                 # LREXTENTFREED2, src/inc/logapi.hxx#L2546-L2560
}
# LRIGNORED and the types that reuse it (lrtypMacroInfo .. lrtypIgnored19): LR + ULONG cb,
# src/inc/logapi.hxx#L352-L367, sized by src/ese/_log/logread.cxx#L3383-L3405.
IGNORED_TYPES = set(range(67, 76)) | set(range(82, 92))
for _n in IGNORED_TYPES:
    FIXED_SIZE[_n] = 5


class LogError(ValueError):
    """The log cannot be read the way ESE would read it; the message says why."""


def _u16(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def _u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def record_size(data, offset=0):
    """The full size of the record at data[offset], as CbLGSizeOfRec computes it
    (src/ese/_log/logread.cxx#L3192-L3423). Raises LogError for a type this module does not size."""
    lrtyp = data[offset]
    if lrtyp >= LRTYP_MAX:
        raise LogError(f'record type {lrtyp} is not a type ESE writes (lrtypMax {LRTYP_MAX})')
    fixed = FIXED_SIZE.get(lrtyp)
    if fixed is None:
        raise LogError(f'record type {lrtyp} ({LRTYP_NAMES.get(lrtyp, "?")}) is not sized by this reader')
    if offset + fixed > len(data):
        raise LogError(f'record type {lrtyp} is cut short')
    o = offset
    if lrtyp == 15:          # LRATTACHDB + CbPath, src/ese/_log/logread.cxx#L3232-L3237
        return fixed + _u16(data, o + 72)
    if lrtyp == 16:          # LRDETACHDB + CbPath, src/ese/_log/logread.cxx#L3238-L3243
        return fixed + _u16(data, o + 4)
    if lrtyp == 14:          # LRCREATEDB + CbPath + VersionInfo when flagged, src/ese/_log/logread.cxx#L3224-L3231
        return fixed + _u16(data, o + 40) + (4 if data[o + 42] & 0x04 else 0)
    if lrtyp == 29:          # LRINSERT, src/ese/_log/logread.cxx#L3302-L3307
        return fixed + _u16(data, o + 44) + _u16(data, o + 46) + _u16(data, o + 48)
    if lrtyp in (30, 31):    # LRFLAGINSERT / LRFLAGINSERTANDREPLACEDATA, src/ese/_log/logread.cxx#L3309-L3320
        return fixed + _u16(data, o + 44) + _u16(data, o + 46)
    if lrtyp in (33, 34):    # LRREPLACE: Cb() is mle_cb & 0x7fff, src/inc/logapi.hxx#L726, src/ese/_log/logread.cxx#L3322-L3327
        return fixed + (_u16(data, o + 44) & 0x7fff)
    if lrtyp == 36:          # LRUNDOINFO, src/ese/_log/logread.cxx#L3329-L3335
        return fixed + _u16(data, o + 54) + _u16(data, o + 44) + _u16(data, o + 46)
    if lrtyp in (37, 93):    # LRDELTA32 / LRDELTA64, src/ese/_log/logread.cxx#L3288-L3300
        return fixed + _u16(data, o + 44) + _u16(data, o + 46)
    if lrtyp == 39:          # LRUNDO, src/ese/_log/logread.cxx#L3337-L3344
        return fixed + _u16(data, o + 44) + _u16(data, o + 46)
    if lrtyp in (22, 61):    # LRTRACE, src/ese/_log/logread.cxx#L3346-L3351
        return fixed + _u16(data, o + 3)
    if lrtyp == 38:          # LRSETEXTERNALHEADER, src/ese/_log/logread.cxx#L3353-L3357
        return fixed + _u16(data, o + 44)
    if lrtyp == 64:          # LRSCRUB, src/ese/_log/logread.cxx#L3359-L3363
        return fixed + _u16(data, o + 52)
    if lrtyp == 54:          # LRPREPCOMMIT, src/ese/_log/logread.cxx#L3377-L3381
        return fixed + _u32(data, o + 3)
    if lrtyp == 48:          # LREMPTYTREE, src/ese/_log/logread.cxx#L3282-L3286
        return fixed + _u16(data, o + 44)
    if lrtyp == 62:          # LRSPLITNEW, src/ese/_log/logread.cxx#L3254-L3262
        return (fixed + _u16(data, o + 100) + _u16(data, o + 96) + _u16(data, o + 98)
                + _u32(data, o + 106))
    if lrtyp == 63:          # LRMERGENEW, src/ese/_log/logread.cxx#L3270-L3274
        return fixed + _u16(data, o + 86) + _u32(data, o + 92)
    if lrtyp in IGNORED_TYPES:  # LRIGNORED + Cb(), src/ese/_log/logread.cxx#L3383-L3405
        return fixed + _u32(data, o + 1)
    if lrtyp == 76:          # LRFRAGMENTBEGIN, src/ese/_log/logread.cxx#L3407-L3411
        return fixed + _u16(data, o + 5)
    if lrtyp == 77:          # LRFRAGMENT, src/ese/_log/logread.cxx#L3413-L3417
        return fixed + _u16(data, o + 1)
    return fixed


# ---------------------------------------------------------------- checksums

def _parity(dword):
    """lParityMask as a 0/1 bit: the parity of a 32-bit value (src/checksum/checksum_amd64.cxx#L385-L397)."""
    dword ^= dword >> 16
    dword ^= dword >> 8
    return bin(dword & 0xff).count('1') & 1


def checksum_old(block):
    """ChecksumOldFormat: XOR of every 32-bit word after the first, seeded with 0x89abcdef
    (src/checksum/checksum.cxx#L165-L199). Used for log and database headers (src/ese/_osu/checksumu.cxx#L214-L222,
    #L270-L335 with pagetype logfileHeader / databaseHeader, src/inc/_osu/checksumu.hxx#L44-L53)."""
    words = struct.unpack(f'<{len(block) // 4}I', block)
    value = 0x89abcdef
    for word in words[1:]:
        value ^= word
    return value


def checksum_new(block, pgno, header_block=True):
    """ChecksumNewFormat, the XOR-ECC checksum of one block of 1 to 8 KiB, ported from
    ChecksumNewFormatSlowly (src/checksum/checksum_amd64.cxx#L612-L784). With header_block the first
    8 bytes (the stored checksum) count as zero. The low 32 bits are the XOR checksum with
    the page number folded in, the high 32 bits the ECC (MakeChecksumFromECCXORAndPgno,
    src/checksum/checksum_amd64.cxx#L349-L357)."""
    size = len(block)
    if size & (size - 1) or not 1024 <= size <= 8192:
        raise LogError(f'no checksum for a block of {size} bytes')
    words = struct.unpack(f'<{size // 4}I', block)
    p = p0 = p1 = p2 = p3 = 0
    index = 0xff800000
    for i in range(0, len(words), 4):
        a, b, c, d = words[i:i + 4]
        if header_block and i == 0:
            a = b = 0
        p0 ^= a
        p1 ^= b
        p2 ^= c
        p3 ^= d
        if _parity(a ^ b ^ c ^ d):
            p ^= index
        index = (index + 0xff800080) & 0xffffffff
    if _parity(p0 ^ p1):
        p |= 0x00400000
    if _parity(p2 ^ p3):
        p |= 0x00000040
    r0, r1 = p0 ^ p2, p1 ^ p3
    if _parity(r0):
        p |= 0x00200000
    if _parity(r1):
        p |= 0x00000020
    r2 = r0 ^ r1
    r = 0
    index = 0xffff0000
    for bit in range(32):
        if r2 >> bit & 1:
            r ^= index
        index = (index + 0xffff0001) & 0xffffffff
    mask = ((size << 19) - 1) & 0xffffffff
    ecc = (p & 0xffe0ffe0 & mask) | (r & 0x001f001f)
    return (ecc << 32) | ((r2 ^ pgno) & 0xffffffff)


def segment_checksum_ok(segment, isec):
    """Whether a log segment's stored checksum matches the one computed with isec as its page
    number: log segments use the database-page checksum (logfilePage == databasePage,
    src/inc/_osu/checksumu.hxx#L46-L49) with the sector number passed as pgno (src/ese/_log/logread.cxx#L1451-L1460).
    A segment always carries the new-format flag in the same place as a page
    (src/inc/_logstream.hxx#L21-L22, src/ese/_osu/checksumu.cxx#L103-L118)."""
    stored = struct.unpack_from('<Q', segment, 0)[0]
    flags = _u32(segment, 36)
    if flags & 0x2000:
        return stored == checksum_new(segment, isec)
    # Old format with a long checksum: XOR checksum in the low half, pgno in the high half
    # (src/ese/_osu/checksumu.cxx#L56-L62, #L328-L331).
    return stored == ((isec << 32) | checksum_old(segment))


# ---------------------------------------------------------------- the log file

class LogHeader:
    """The fields of LGFILEHDR_FIXED (src/inc/log.hxx#L143-L196) this reader uses."""

    def __init__(self, data):
        if len(data) < LOG_HEADER_SIZE:
            raise LogError('the log file is shorter than its header')
        block = bytes(data[:LOG_HEADER_SIZE])
        stored = _u32(block, 0)
        if stored != checksum_old(block):
            # ChecksumPage over sizeof(LGFILEHDR) as logfileHeader, src/ese/_log/log.cxx#L944-L957
            raise LogError('the log file header checksum does not match')
        (self.generation, self.cb_sec, self.csec_header, self.csec_file,
         self.cb_page) = struct.unpack_from('<iHHHH', block, 4)
        self.tm_create = block[16:24]
        self.tm_prev_gen = block[24:32]
        self.major, self.minor, self.update_major = struct.unpack_from('<III', block, 32)
        self.sign_log = block[44:72]               # SIGNATURE, src/inc/daedef.hxx#L2298-L2303
        self.update_minor = _u32(block, 648)       # after fLGFlags (639) and le_lgposCheckpoint (640)
        self.filetype = _u32(block, 667)           # src/inc/log.hxx#L194-L199
        if self.filetype not in (0, JET_FILETYPE_LOG):
            raise LogError(f'file type {self.filetype} is not a log file')
        if self.major <= OLD_LRCK_MAJOR:
            raise LogError(f'log format {self.major}.{self.minor} uses the older LRCHECKSUM layout, '
                           'which this reader does not read')
        if self.cb_sec != SEGMENT_SIZE:
            raise LogError(f'a sector size of {self.cb_sec}, not {SEGMENT_SIZE}')

    @property
    def zero_filled(self):
        """FLGVersionZeroFilled, src/ese/_log/log.cxx#L1231-L1241."""
        return (self.major, self.minor, self.update_major) >= ZERO_FILLED_VERSION

    @property
    def version(self):
        return (self.major, self.minor, self.update_major, self.update_minor)


class LogRecord:
    """One record: its LGPOS as (generation, isec, ib), its type and its bytes."""

    __slots__ = ('lgpos', 'lrtyp', 'data')

    def __init__(self, lgpos, data):
        self.lgpos = lgpos
        self.lrtyp = data[0]
        self.data = bytes(data)

    @property
    def name(self):
        return LRTYP_NAMES.get(self.lrtyp, str(self.lrtyp))

    def __repr__(self):
        return f'LogRecord({self.lgpos}, {self.name}, {len(self.data)} bytes)'


def _lgpos_tuple(segment):
    ib, isec, generation = struct.unpack_from('<HHi', segment, 8)   # LE_LGPOS, src/inc/daedef.hxx#L877-L885
    return (generation, isec, ib)


def last_valid_segment(header, data):
    """The index of the last segment holding this generation's data, found the way
    ErrLGCheckReadLastLogRecordFF does (src/ese/_log/logread.cxx#L1442-L1682): a segment whose checksum
    holds and whose LGPOS is this one is data; one whose LGPOS is older, or which is the
    shadow copy of the segment before it, or (on zero-filled versions) all zeros, marks the
    end; data after an end mark, an LGPOS ahead of its place, or any other checksum failure is
    corruption. The last sector is never read as data (loop bound, src/ese/_log/logread.cxx#L1443)."""
    generation = header.generation
    last = None
    empty_seen = False
    end = min(header.csec_file - 1, len(data) // SEGMENT_SIZE)
    if header.csec_file * SEGMENT_SIZE > len(data):
        raise LogError(f'the log file holds {len(data)} bytes, its header says {header.csec_file} sectors')
    for isec in range(header.csec_header, end):
        segment = data[isec * SEGMENT_SIZE:(isec + 1) * SEGMENT_SIZE]
        if segment_checksum_ok(segment, isec):
            position = _lgpos_tuple(segment)
            if position < (generation, isec, 0):
                empty_seen = True
                continue
            if position > (generation, isec, 0):
                raise LogError(f'segment {isec} names a position ahead of its place')
            if empty_seen:
                raise LogError(f'segment {isec} holds data after the end of the log')
            last = isec
            continue
        if isec != header.csec_header and segment_checksum_ok(segment, isec - 1):
            empty_seen = True      # the shadow copy of the segment before, src/ese/_log/logread.cxx#L1463-L1492
            continue
        if header.zero_filled and not any(segment):
            empty_seen = True      # src/ese/_log/logread.cxx#L1495-L1503
            continue
        # ESE would try the next sector as a shadow copy of this one and, if it holds, use
        # it (src/ese/_log/logread.cxx#L1560-L1678); that rewrites the log, which this reader never does.
        raise LogError(f'segment {isec} fails its checksum')
    return last


def read_records(data):
    """(LogHeader, [LogRecord, ...]) for one log file's bytes.

    Records are read as ErrLGIGetRecordAtPbNext reads them (src/ese/_log/logread.cxx#L2108-L2352): a
    record never crosses a segment unless it is split into a FragmentBegin and Fragments,
    which are joined back together; NOPs fill the rest of a segment; reading stops at the
    end of the last valid segment (m_lgposLastRec, src/ese/_log/logread.cxx#L1845-L1847). A record's LGPOS
    is where reading of it began (GetLgposDuringReading, src/ese/_log/logread.cxx#L72-L103), so a record
    after NOP fill carries the position of the fill."""
    header = LogHeader(data)
    last = last_valid_segment(header, data)
    records = []
    if last is None:
        return header, records
    generation = header.generation
    view = memoryview(data)
    fragment = None          # (lgpos, total, bytearray)
    start = None             # LGPOS where the record being read began
    for isec in range(header.csec_header, last + 1):
        base = isec * SEGMENT_SIZE
        segment = view[base:base + SEGMENT_SIZE]
        position = SEGMENT_HEADER_SIZE
        if start is None:
            start = (generation, isec, 0)
        while position < SEGMENT_SIZE:
            lrtyp = segment[position]
            room = SEGMENT_SIZE - position
            if lrtyp == LRTYP_NOP:
                # skip NOPs to the end of the segment (src/ese/_log/logread.cxx#L2284-L2294)
                while position < SEGMENT_SIZE and segment[position] == LRTYP_NOP:
                    position += 1
                continue
            if lrtyp == LRTYP_FRAGMENT_BEGIN:
                if room < 7:
                    raise LogError(f'a fragment header runs past segment {isec}')
                if fragment is not None and (position != SEGMENT_HEADER_SIZE
                                             or segment[position + 7] != LRTYP_UNDO_INFO):
                    raise LogError(f'a fragment starts inside another at segment {isec}')
                total = _u32(segment, position + 1)
                size = _u16(segment, position + 5)
                if size >= total or size > room - 7:
                    raise LogError(f'a fragment of bad size at segment {isec}')
                fragment = (start, total, bytearray(segment[position + 7:position + 7 + size]))
                position += 7 + size
                if position >= SEGMENT_SIZE:
                    start = None
                else:
                    start = (generation, isec, position)
                continue
            if lrtyp == LRTYP_FRAGMENT:
                if fragment is None or room < 3:
                    raise LogError(f'a fragment continuation without its start at segment {isec}')
                size = _u16(segment, position + 1)
                first, total, buffer = fragment
                if size > total - len(buffer) or size > room - 3:
                    raise LogError(f'a fragment continuation of bad size at segment {isec}')
                buffer.extend(segment[position + 3:position + 3 + size])
                position += 3 + size
                if len(buffer) == total:
                    if (buffer[0] >= LRTYP_MAX or FIXED_SIZE.get(buffer[0], total + 1) > total
                            or record_size(buffer) != total):
                        raise LogError(f'a joined fragment does not hold one whole record at segment {isec}')
                    records.append(LogRecord(first, buffer))
                    fragment = None
                start = None if position >= SEGMENT_SIZE else (generation, isec, position)
                continue
            if fragment is not None:
                # A torn fragment is allowed only when recovery's undo phase or an UndoInfo
                # starts the next segment (src/ese/_log/logread.cxx#L2296-L2332).
                if position == SEGMENT_HEADER_SIZE and lrtyp in (LRTYP_RECOVERY_UNDO,
                                                                 LRTYP_RECOVERY_UNDO2,
                                                                 LRTYP_UNDO_INFO):
                    fragment = None
                    start = (generation, isec, 0)
                else:
                    raise LogError(f'a record starts inside a fragment at segment {isec}')
            if lrtyp >= LRTYP_MAX:
                raise LogError(f'record type {lrtyp} at segment {isec} offset {position}')
            fixed = FIXED_SIZE.get(lrtyp)
            if fixed is None:
                raise LogError(f'record type {lrtyp} ({LRTYP_NAMES.get(lrtyp, "?")}) at segment '
                               f'{isec} is not sized by this reader')
            if fixed > room:
                raise LogError(f'record at segment {isec} offset {position} runs past its segment')
            size = record_size(segment, position)
            if size > room:
                raise LogError(f'record at segment {isec} offset {position} runs past its segment')
            records.append(LogRecord(start, segment[position:position + size]))
            position += size
            start = None if position >= SEGMENT_SIZE else (generation, isec, position)
    return header, records
