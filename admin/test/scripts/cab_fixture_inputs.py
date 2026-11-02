"""The made-up inputs behind admin/test/data/cab/*.cab, rebuilt from fixed seeds.

Each cab was made on Windows 11 build 26200 (ARM64) by makecab.exe from the file one of these functions writes, with
"makecab /D CompressionType=LZX /D CompressionMemory=<window bits> <input> <cab>"; the window bits are in the cab's
name. test_cab_reader.py decodes each cab and compares it byte for byte with the input rebuilt here.
"""
import random
import struct

FRAME = 32768


def aligned_records():
    """8-byte records repeated 16 to 64 bytes back, which makecab wrote as aligned offset blocks."""
    rnd = random.Random(1)
    records = [rnd.randbytes(8) for _ in range(40)]
    out = bytearray()
    while len(out) < 60000:
        pick = rnd.random()
        if pick < 0.6 and len(out) >= 64:
            back = 8 * rnd.randrange(2, 9)
            out += out[-back:-back + 8]
        elif pick < 0.9:
            out += rnd.choice(records)
        else:
            out += rnd.randbytes(8)
    return bytes(out[:60000])


def e8_frame_ends():
    """Four frames of repeated text with E8 bytes placed near frame ends, each followed by an operand in the range
    that gets translated: 11 bytes before the end of frame 1 (translated), 8 bytes before the end of frame 2 (not
    translated) and 22 bytes before the end of frame 3."""
    line = b'2026-01-01 00:00:00, Info                  CBS    made-up line for the E8 fixture\r\n'
    out = bytearray((line * (4 * FRAME // len(line) + 1))[:4 * FRAME])
    for frame, back, operand in ((1, 11, 1000), (2, 8, 2000), (3, 22, 3000)):
        at = frame * FRAME - back
        out[at] = 0xE8
        out[at + 1:at + 5] = struct.pack('<i', operand)
    return bytes(out)


def random_odd():
    """Bytes that do not compress, of an odd length, which makecab wrote as uncompressed blocks."""
    return random.Random(3).randbytes(40001)


def cbs_text():
    """CBS-shaped lines with made-up values."""
    rnd = random.Random(4)
    lines = []
    for i in range(1500):
        lines.append(f'2026-01-{1 + i % 28:02d} {i % 24:02d}:{i % 60:02d}:{(i * 7) % 60:02d}, Info                  '
                     f'CBS    Session: {1000 + i}_{rnd.randrange(10 ** 9)} initialized by client MadeUp{i % 7}\r\n')
    return ''.join(lines).encode('ascii')



def short_text():
    """Made-up words with few repeats, which makecab wrote as a verbatim block at a 32 KiB window."""
    rnd = random.Random(5)
    words = [''.join(rnd.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rnd.randrange(3, 9))) for _ in range(800)]
    return ' '.join(rnd.choice(words) for _ in range(4000)).encode('ascii')


INPUTS = {
    'aligned_records.bin': aligned_records,
    'e8_frame_ends.bin': e8_frame_ends,
    'random_odd.bin': random_odd,
    'cbs_text.log': cbs_text,
    'short_text.txt': short_text,
}
WINDOW_BITS = {'aligned_records.bin': 16, 'e8_frame_ends.bin': 21, 'random_odd.bin': 16, 'cbs_text.log': 21, 'short_text.txt': 15}
