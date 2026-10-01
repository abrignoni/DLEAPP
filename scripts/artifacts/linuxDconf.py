"""Keys and values in a user's dconf database (GNOME settings), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxDconfUserSettings": {
        "name": "dconf User Settings",
        "description": "Keys and values in a user's dconf settings database, each value printed as dconf dump "
                       "prints it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-30",
        "last_update_date": "2026-09-30",
        "requirements": "none",
        "category": "Desktop (Linux)",
        "notes": "Reads the dconf database at .config/dconf/user in a home folder, one row per key. dconf is "
                 "a key and value store built for user preferences "
                 "(https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/README#L1-4); "
                 "when no dconf profile says otherwise, a user's settings are read from and written to this "
                 "file (dconf 0.49.0, "
                 "https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/engine/dconf-engine-profile.c#L62-65, "
                 "https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/engine/dconf-engine-source-user.c#L46). "
                 "A database under another name set by a profile, or in the folder $XDG_CONFIG_HOME names "
                 "when it is set to one other than .config "
                 "(https://gitlab.freedesktop.org/xdg/xdg-specs/-/blob/d546132d944a5f1e729c52aa6c2623edeaf750ed/basedir/basedir-spec.xml#L142-145), "
                 "is not read. The file is a GVDB table (the GVDB revision dconf 0.49.0 builds with, "
                 "https://gitlab.gnome.org/GNOME/gvdb/-/blob/4758f6fb7f889e074e13df3f914328f3eecb1fd3/gvdb/gvdb-format.h#L40-62): "
                 "the artifact builds each key's name from its item and its parent items, as GVDB's reader "
                 "does "
                 "(https://gitlab.gnome.org/GNOME/gvdb/-/blob/4758f6fb7f889e074e13df3f914328f3eecb1fd3/gvdb/gvdb-reader.c#L352-485), "
                 "and decodes the value, a serialised GVariant of type v "
                 "(https://gitlab.gnome.org/GNOME/gvdb/-/blob/4758f6fb7f889e074e13df3f914328f3eecb1fd3/gvdb/gvdb-reader.c#L605-625). "
                 "Path is the key's folder, Key its name, Type the value's GVariant type string and Value "
                 "the value printed as dconf dump prints it, with g_variant_print and type annotations "
                 "(https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/bin/dconf.c#L464; "
                 "GLib 2.88.0, "
                 "https://gitlab.gnome.org/GNOME/glib/-/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gvariant.c#L2217-2637). "
                 "A GVDB item holds no time, so the file gives no time for any key. The dconf service writes "
                 "the whole database from its values on each change "
                 "(https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/service/dconf-writer.c#L122, "
                 "https://gitlab.gnome.org/GNOME/dconf/-/blob/a6b86bd66d3b42d8cfeacc2cc71a4fc78abadb71/service/dconf-writer.c#L174, "
                 "https://gitlab.gnome.org/GNOME/gvdb/-/blob/4758f6fb7f889e074e13df3f914328f3eecb1fd3/gvdb/gvdb-builder.c#L537-551), "
                 "so a key reset to its default leaves no entry. A value that cannot be decoded is reported "
                 "with Type and Value blank and counted in the run log. A symbolic link at the path is "
                 "counted in the run log and not followed. A database in the other byte order is read by the "
                 "same rules, with GVariant's framing offsets little-endian in either order "
                 "(https://gitlab.gnome.org/GNOME/glib/-/blob/7a03e2ef692204d8bf0fa5f2b1a32bbac14634f4/glib/gvariant-serialiser.c#L559-561); "
                 "the unit tests cover it with values GLib 2.88.0 byte-swapped, but no such database was "
                 "available. Known data, ubuntu2604_arm64_dconf (Ubuntu 26.04, dconf 0.49.0, GLib 2.88.0, VM "
                 "clock about 5,157.9 s ahead of real time): dconf write set 38 keys under "
                 "/org/dleapp/known/ through the session's dconf service, one for each GVariant type and "
                 "several edge cases, and dconf reset then removed one of them. The file held the other 37 "
                 "and the VM's own 48, and the reset key was not in it; its modification time was the time "
                 "of the reset, the last write. The 85 rows' values each equal the line dconf dump printed "
                 "for that key after the steps. On ubuntu2604_arm64_chromium the path matched only a link a "
                 "snap package keeps to the user's database.",
        "paths": ('*/.config/dconf/user',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "ubuntu2604_arm64_dconf": "Ubuntu 26.04 LTS aarch64, dconf 0.49.0 | 85 rows",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (the path matches only a symbolic link, not followed)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

import struct
import unicodedata
from collections import Counter

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_link, seeker_of

SIG0, SIG1 = 1918981703, 1953390953
BASIC = {'b': 1, 'y': 1, 'n': 2, 'q': 2, 'i': 4, 'u': 4, 'h': 4, 'x': 8, 't': 8, 'd': 8}
FORMAT = {'b': 'B', 'y': 'B', 'n': 'h', 'q': 'H', 'i': 'i', 'u': 'I', 'h': 'i', 'x': 'q', 't': 'Q', 'd': 'd'}


class GVariantError(ValueError):
    pass


def type_end(t, i=0):
    if i >= len(t):
        raise GVariantError('truncated type')
    c = t[i]
    if c in BASIC or c in 'sogv':
        return i + 1
    if c in 'am':
        return type_end(t, i + 1)
    if c == '(':
        i += 1
        while i < len(t) and t[i] != ')':
            i = type_end(t, i)
        if i >= len(t):
            raise GVariantError('unclosed tuple')
        return i + 1
    if c == '{':
        i = type_end(t, type_end(t, i + 1))
        if i >= len(t) or t[i] != '}':
            raise GVariantError('bad dict entry')
        return i + 1
    raise GVariantError(f'unknown type {c!r}')


def members(t):
    inner, out, i = t[1:-1], [], 0
    while i < len(inner):
        j = type_end(inner, i)
        out.append(inner[i:j])
        i = j
    return out


def alignment(t):
    c = t[0]
    if c in BASIC:
        return BASIC[c]
    if c in 'sog':
        return 1
    if c == 'v':
        return 8
    if c in 'am':
        return alignment(t[1:])
    return max([alignment(m) for m in members(t)] + [1])


def round_up(n, a):
    return (n + a - 1) // a * a


def fixed_size(t):
    c = t[0]
    if c in BASIC:
        return BASIC[c]
    if c in 'sogvam':
        return None
    offset = 0
    for m in members(t):
        size = fixed_size(m)
        if size is None:
            return None
        offset = round_up(offset, alignment(m)) + size
    return round_up(offset, alignment(t)) if offset else 1


def offset_size(n):
    if n == 0:
        return 0
    if n <= 0xff:
        return 1
    if n <= 0xffff:
        return 2
    if n <= 0xffffffff:
        return 4
    return 8


def decode(t, data, order):
    """(type, value) where value is a Python scalar, a list of child nodes, a child node or None."""
    c = t[0]
    if c in BASIC:
        if len(data) != BASIC[c]:
            raise GVariantError(f'{t}: {len(data)} bytes')
        value = struct.unpack(order + FORMAT[c], data)[0]
        return t, bool(value) if c == 'b' else value
    if c in 'sog':
        if not data or data[-1] != 0:
            raise GVariantError(f'{t}: no terminating nul')
        return t, data[:-1].decode('utf-8', 'replace')
    if c == 'v':
        cut = data.rfind(b'\0')
        if cut < 0:
            raise GVariantError('variant with no type')
        inner = data[cut + 1:].decode('ascii', 'replace')
        if type_end(inner) != len(inner):
            raise GVariantError(f'variant type {inner!r}')
        return t, decode(inner, data[:cut], order)
    if c == 'm':
        element, size = t[1:], fixed_size(t[1:])
        if not data:
            return t, None
        if size is not None:
            return t, decode(element, data, order)
        return t, decode(element, data[:-1], order)
    if c == 'a':
        return t, [decode(t[1:], piece, order) for piece in array_pieces(t[1:], data, order)]
    return t, [decode(m, piece, order) for m, piece in zip(members(t), tuple_pieces(t, data, order))]


def read_offset(data, pos, size, _order):
    """A framing offset, which GVariant stores little-endian whatever the byte order of the values."""
    return int.from_bytes(data[pos:pos + size], 'little')


def array_pieces(element, data, order):
    size = fixed_size(element)
    if size is not None:
        if len(data) % size:
            raise GVariantError('array length not a multiple of the element size')
        return [data[i:i + size] for i in range(0, len(data), size)]
    if not data:
        return []
    osz = offset_size(len(data))
    last = read_offset(data, len(data) - osz, osz, order)
    if last > len(data) or (len(data) - last) % osz:
        raise GVariantError('bad array framing')
    ends = [read_offset(data, p, osz, order) for p in range(last, len(data), osz)]
    pieces, start = [], 0
    for end in ends:
        start = round_up(start, alignment(element))
        if not start <= end <= last:
            raise GVariantError('bad array offset')
        pieces.append(data[start:end])
        start = end
    return pieces


def tuple_pieces(t, data, order):
    parts = members(t)
    if not parts:
        return []
    osz = offset_size(len(data))
    variable = [i for i, m in enumerate(parts[:-1]) if fixed_size(m) is None]
    frame_end = len(data) - osz * len(variable)
    pieces, start, k = [], 0, 0
    for i, m in enumerate(parts):
        start = round_up(start, alignment(m))
        size = fixed_size(m)
        if size is not None:
            end = start + size
        elif i == len(parts) - 1:
            end = frame_end
        else:
            k += 1
            end = read_offset(data, len(data) - osz * k, osz, order)
        if not start <= end <= frame_end:
            raise GVariantError('bad tuple framing')
        pieces.append(data[start:end])
        start = end
    return pieces


def _isprint(ch):
    return unicodedata.category(ch) not in ('Cc', 'Cf', 'Cn', 'Cs')


ESC = {'\a': 'a', '\b': 'b', '\f': 'f', '\n': 'n', '\r': 'r', '\t': 't', '\v': 'v'}


def _quote(text):
    quote = '"' if "'" in text else "'"
    out = [quote]
    for ch in text:
        if ch in (quote, '\\'):
            out.append('\\')
        if _isprint(ch):
            out.append(ch)
        else:
            out.append('\\')
            code = ord(ch)
            out.append(ESC.get(ch) or (f'u{code:04x}' if code < 0x10000 else f'U{code:08x}'))
    out.append(quote)
    return ''.join(out)


def _strescape(raw):
    out = []
    for b in raw:
        ch = chr(b)
        if ch in '\b\f\n\r\t\v':
            out.append('\\' + ESC[ch])
        elif ch in '\\"':
            out.append('\\' + ch)
        elif b < 0x20 or b >= 0x7f:
            out.append(f'\\{b:03o}')
        else:
            out.append(ch)
    return ''.join(out)


PREFIX = {'y': 'byte ', 'n': 'int16 ', 'q': 'uint16 ', 'h': 'handle ', 'u': 'uint32 ', 'x': 'int64 ', 't': 'uint64 ',
          'o': 'objectpath ', 'g': 'signature '}


def gv_print(node, annotate=True):
    t, value = node
    c = t[0]
    if c == 'm':
        out = f'@{t} ' if annotate else ''
        if value is None:
            return out + 'nothing'
        depth = len(t) - len(t.lstrip('m'))
        element, i = node, 0
        while i < depth and element is not None:
            element = element[1]
            i += 1
        if element is None:
            return out + 'just ' * max(i - 1, 0) + 'nothing'
        return out + gv_print(element, False)
    if c == 'a':
        if t[1] == 'y':
            raw = bytes(v for _, v in value)
            if raw and raw.index(0) == len(raw) - 1:
                body = _strescape(raw[:-1])
                return f'b"{body}"' if b"'" in raw else f"b'{body}'"
        if not value:
            return (f'@{t} ' if annotate else '') + ('{}' if t[1] == '{' else '[]')
        parts = []
        for child in value:
            if t[1] == '{':
                parts.append(gv_print(child[1][0], annotate) + ': ' + gv_print(child[1][1], annotate))
            else:
                parts.append(gv_print(child, annotate))
            annotate = False
        return ('{' + ', '.join(parts) + '}') if t[1] == '{' else ('[' + ', '.join(parts) + ']')
    if c == '(':
        parts = [gv_print(child, annotate) for child in value]
        return '(' + ', '.join(parts) + (',' if len(parts) == 1 else '') + ')'
    if c == '{':
        return '{' + gv_print(value[0], annotate) + ', ' + gv_print(value[1], annotate) + '}'
    if c == 'v':
        return '<' + gv_print(value, True) + '>'
    if c == 'b':
        return 'true' if value else 'false'
    if c == 's':
        return _quote(value)
    if c in 'og':
        return (PREFIX[c] if annotate else '') + f"'{value}'"
    if c == 'y':
        return (PREFIX[c] if annotate else '') + f'0x{value:02x}'
    if c == 'd':
        text = '%.17g' % value
        if not any(x in text for x in '.enN'):
            text += '.0'
        return text
    return (PREFIX.get(c, '') if annotate else '') + str(value)


def gvdb_values(data):
    """(full key, (type, value)) for each value item; (full key, error) when a value cannot be decoded."""
    if len(data) < 24:
        raise GVariantError('file shorter than a GVDB header')
    s0, s1, version = struct.unpack_from('<III', data, 0)
    if (s0, s1) == (SIG0, SIG1):
        order = '<'
    elif (s0, s1) == tuple(struct.unpack('>II', struct.pack('<II', SIG0, SIG1))):
        order = '>'
    else:
        raise GVariantError('not a GVDB file')
    if version != 0:
        raise GVariantError(f'GVDB version {version}')
    start, end = struct.unpack_from('<II', data, 16)
    if not start <= end <= len(data) or end - start < 8:
        raise GVariantError('bad root pointer')
    n_bloom, n_buckets = struct.unpack_from('<II', data, start)
    n_bloom &= (1 << 27) - 1
    items_at = start + 8 + 4 * n_bloom + 4 * n_buckets
    if items_at > end or (end - items_at) % 24:
        raise GVariantError('bad hash table')
    items = [struct.unpack_from('<IIIHcxII', data, p) for p in range(items_at, end, 24)]
    names = [None] * len(items)
    changed = True
    while changed:
        changed = False
        for i, (_h, parent, kstart, ksize, _t, _a, _b) in enumerate(items):
            if names[i] is not None:
                continue
            key = data[kstart:kstart + ksize].decode('utf-8', 'replace')
            if parent == 0xffffffff:
                names[i] = key
            elif parent < len(items) and names[parent] is not None:
                names[i] = names[parent] + key
            else:
                continue
            changed = True
    for i, (_h, _p, _ks, _kz, kind, vstart, vend) in enumerate(items):
        if kind != b'v' or names[i] is None:
            continue
        if not vstart <= vend <= len(data) or vstart % 8:
            yield names[i], GVariantError('bad value pointer')
            continue
        try:
            yield names[i], decode('v', data[vstart:vend], order)[1]
        except GVariantError as exc:
            yield names[i], exc


@artifact_processor
def linuxDconfUserSettings(context):
    data_headers = ('Path', 'Key', 'Type', 'Value', 'Source File')
    data_list, read, counts = [], [], Counter()
    seeker = seeker_of(context)
    for path in sorted({str(f) for f in context.get_files_found()}):
        if recorded_link(seeker, path) is not None:
            counts['symbolic links to a database, not followed'] += 1
            continue
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
            values = sorted(gvdb_values(data), key=lambda item: item[0])
        except (OSError, GVariantError) as exc:
            logfunc(f'dconf User Settings: could not read {relative}: {exc}')
            continue
        for name, node in values:
            folder, _, key = name.rpartition('/')
            if isinstance(node, GVariantError):
                counts['values that could not be decoded, left blank'] += 1
                data_list.append((folder + '/', key, '', '', relative))
            else:
                data_list.append((folder + '/', key, node[0], gv_print(node), relative))
        read.append(path)
    if counts:
        logfunc('dconf User Settings: ' + ', '.join(f'{n} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(read)
