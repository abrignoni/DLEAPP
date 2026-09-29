"""Decoding the history files libedit writes, for the DLEAPP artifacts that read them.

libedit writes _HiStOrY_V2_ as a file's first line and each entry after it encoded with strvis(VIS_WHITE), and
decodes each line with strunvis when it reads the file back (NetBSD lib/libedit/history.c, lib/libc/gen/unvis.c).
"""

LIBEDIT_COOKIE = b'_HiStOrY_V2_'
_SIMPLE = {ord('n'): 10, ord('r'): 13, ord('b'): 8, ord('a'): 7, ord('v'): 11, ord('t'): 9, ord('f'): 12,
           ord('s'): 32, ord('E'): 27}
_OCTAL = b'01234567'
_HEX = b'0123456789abcdefABCDEF'


def unvis(line):
    """A libedit history line decoded as its reader decodes it, with strunvis: unvis() with no flags, applied byte by
    byte (NetBSD lib/libc/gen/unvis.c). None when the line holds a sequence that decoder rejects."""
    out = bytearray()
    state, cur, i = 'ground', 0, 0
    while i < len(line):
        c = line[i]
        i += 1
        if state == 'ground':
            if c == 0x5C:
                state, cur = 'start', 0
            else:
                out.append(c)
        elif state == 'start':
            state = 'ground'
            if c == 0x5C:
                out.append(c)
            elif c in _OCTAL:
                cur, state = c - 0x30, 'octal2'
            elif c == ord('M'):
                cur, state = 0o200, 'meta'
            elif c == ord('^'):
                state = 'ctrl'
            elif c in _SIMPLE:
                out.append(_SIMPLE[c])
            elif c == ord('x'):
                state = 'hex'
            elif c in (0x0A, ord('$')):
                pass
            elif 0x21 <= c <= 0x7E:
                out.append(c)
            else:
                return None
        elif state == 'meta':
            if c == ord('-'):
                state = 'meta1'
            elif c == ord('^'):
                state = 'ctrl'
            else:
                return None
        elif state == 'meta1':
            out.append(cur | c)
            state = 'ground'
        elif state == 'ctrl':
            out.append((cur | 0o177) if c == ord('?') else (cur | (c & 0o37)) & 0xFF)
            state = 'ground'
        elif state in ('octal2', 'octal3'):
            if c in _OCTAL:
                cur = ((cur << 3) + c - 0x30) & 0xFF
                if state == 'octal3':
                    out.append(cur)
                    state = 'ground'
                else:
                    state = 'octal3'
            else:
                out.append(cur)
                state = 'ground'
                i -= 1
        elif state == 'hex':
            if c not in _HEX:
                return None
            cur, state = int(chr(c), 16), 'hex2'
        elif state == 'hex2':
            state = 'ground'
            if c in _HEX:
                out.append((cur << 4) | int(chr(c), 16))
            else:
                out.append(cur)
                i -= 1
    if state in ('octal2', 'octal3', 'hex2'):
        out.append(cur)
    return bytes(out)
