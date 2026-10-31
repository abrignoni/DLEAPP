"""cimreader: a read-only reader for the Windows WMI CIM repository.

One file, pure Python, standard library only. It opens the repository Windows keeps
in ``C:\\Windows\\System32\\wbem\\Repository`` (``OBJECTS.DATA``, ``INDEX.BTR`` and
``MAPPING1.MAP`` to ``MAPPING3.MAP``), resolves the active mapping, walks the index
B-tree, and decodes namespaces, class definitions and instances against their class
definitions. Its first use is listing WMI event subscriptions (``__EventFilter``,
the ``__EventConsumer`` subclasses and ``__FilterToConsumerBinding``), a common
persistence mechanism.

    with cimreader.open_repository("Repository") as repo:
        for inst in repo.instances("root\\subscription", "__FilterToConsumerBinding"):
            print(inst.properties)

It reads only the live view: the objects the active mapping and the index reach.
Pages that an older mapping generation or a deleted object left behind are not read,
so a deleted object is never reported as live, and nothing is recovered from them.

This file is a port of python-cim, part of Mandiant's flare-wmi
(https://github.com/mandiant/flare-wmi, python-cim/cim/cim.py and objects.py at commit
b0a5a094ff9ca7d7a1c4fc711dc00c74dec4b6b1, 2018-07-23), written by Willi Ballenthin
with contributions from davidpany and fhouse, and licensed under the Apache License,
Version 2.0. The structures, constants and lookup logic are python-cim's. What
changed: the vstruct (vivisect-vstruct-wb) structure definitions are replaced by
``struct`` reads; the funcy, PyQt and hexdump dependencies are gone; a read that
runs past its buffer, a page whose table of contents does not parse, an unknown
property type and an instance with dynamic properties raise or are reported per
object instead of being skipped; a full index walk is added; and the subscription
listing and command line are new. Where this file departs from python-cim's
behaviour, the comment at that point says so and why.

Modified from python-cim by Alexis Brignoni, 2026. Licensed under the Apache
License, Version 2.0; see LICENSE and NOTICE.
"""

import argparse
import datetime
import hashlib
import json
import os
import struct
import sys

__version__ = "0.1.0"

# ------------------------------------------------------------ constants (python-cim)

LAYOUT_XP = "xp"
LAYOUT_WIN7 = "win7"

MAPPING_START_SIGNATURE = 0xABCD
MAPPING_END_SIGNATURE = 0xDCBA
MAX_MAPPING_FILES = 3
MAPPING_PAGE_ID_MASK = 0x3FFFFFFF
UNMAPPED_PAGE_VALUE = 0x3FFFFFFF

DATA_PAGE_SIZE = 0x2000
INDEX_PAGE_SIZE = 0x2000

INDEX_PAGE_INVALID = 0xFFFFFFFF
INDEX_PAGE_INVALID2 = 0x00000000

PAGE_TYPE_ACTIVE = 0xACCC
PAGE_TYPE_DELETED = 0xBADD
PAGE_TYPE_ADMIN = 0xADDD

ROOT_NAMESPACE_NAME = "root"
SYSTEM_NAMESPACE_NAME = "__SystemClass"
NAMESPACE_CLASS_NAME = "__namespace"

# CIM property types (python-cim objects.py CIM_TYPES, which cites [MS-WMIO]).
CIM_TYPE_INT16 = 0x2
CIM_TYPE_INT32 = 0x3
CIM_TYPE_REAL32 = 0x4
CIM_TYPE_REAL64 = 0x5
CIM_TYPE_STRING = 0x8
CIM_TYPE_BOOLEAN = 0xB
CIM_TYPE_OBJECT = 0xD    # python-cim calls it CIM_TYPE_UNKNOWN; its comment lists 13 as OBJECT
CIM_TYPE_INT8 = 0x10
CIM_TYPE_UINT8 = 0x11
CIM_TYPE_UINT16 = 0x12
CIM_TYPE_UINT32 = 0x13
CIM_TYPE_INT64 = 0x14
CIM_TYPE_UINT64 = 0x15
CIM_TYPE_DATETIME = 0x65
CIM_TYPE_REFERENCE = 0x66

CIM_TYPE_NAMES = {
    CIM_TYPE_INT16: "sint16", CIM_TYPE_INT32: "sint32", CIM_TYPE_REAL32: "real32",
    CIM_TYPE_REAL64: "real64", CIM_TYPE_STRING: "string", CIM_TYPE_BOOLEAN: "boolean",
    CIM_TYPE_OBJECT: "object", CIM_TYPE_INT8: "sint8", CIM_TYPE_UINT8: "uint8",
    CIM_TYPE_UINT16: "uint16", CIM_TYPE_UINT32: "uint32", CIM_TYPE_INT64: "sint64",
    CIM_TYPE_UINT64: "uint64", CIM_TYPE_DATETIME: "datetime", CIM_TYPE_REFERENCE: "reference",
}

# The on-disk width of a value slot, as python-cim's value_parser reads it. python-cim's
# CIM_TYPE_SIZES table gives real64 four bytes, but its parser reads a double, and the
# parser is what positions every later slot, so the parser's width is used here.
_VALUE_FORMATS = {
    CIM_TYPE_INT16: "<h", CIM_TYPE_INT32: "<i", CIM_TYPE_REAL32: "<f", CIM_TYPE_REAL64: "<d",
    CIM_TYPE_STRING: "<I", CIM_TYPE_BOOLEAN: "<H", CIM_TYPE_OBJECT: "<I", CIM_TYPE_INT8: "<b",
    CIM_TYPE_UINT8: "<B", CIM_TYPE_UINT16: "<H", CIM_TYPE_UINT32: "<I", CIM_TYPE_INT64: "<q",
    CIM_TYPE_UINT64: "<Q", CIM_TYPE_DATETIME: "<I", CIM_TYPE_REFERENCE: "<I",
}

ARRAY_STATE_ARRAY = 0x20

BUILTIN_QUALIFIERS = {
    0x1: "PROP_QUALIFIER_KEY", 0x3: "PROP_QUALIFIER_READ_ACCESS", 0x6: "CLASS_QUALIFIER_PROVIDER",
    0x7: "CLASS_QUALIFIER_DYNAMIC", 0xA: "PROP_QUALIFIER_TYPE",
}
# Property names stored as a built-in reference rather than a string. The labels are
# python-cim's, except 0x6: on the Windows 11 26200 known data the live name of that
# property is "provider" (the provider registration classes), so that is used.
BUILTIN_PROPERTIES = {
    0x1: "PRIMARY_KEY", 0x3: "READ", 0x4: "WRITE", 0x5: "VOLATILE", 0x6: "provider",
    0x7: "DYNAMIC", 0xA: "TYPE",
}

DYNPROPS_NONE = 0x1
DYNPROPS_PRESENT = 0x2

# Classes whose instances make up a WMI event subscription. A class is reported when
# one of these is the class itself or one of its ancestors, so a consumer class a
# product registers is found by its derivation, not by a list of known names.
SUBSCRIPTION_BASES = ("__EventFilter", "__EventConsumer", "__FilterToConsumerBinding")
SUBSCRIPTION_NAMESPACES = ("root\\subscription", "root\\default")


class CimError(Exception):
    """The repository, or one object in it, cannot be read as python-cim describes it."""


class UnmappedPage(CimError):
    pass


class NotFound(CimError):
    pass


# ------------------------------------------------------------------ small readers

def _unpack(fmt, buf, off):
    try:
        return struct.unpack_from(fmt, buf, off)
    except struct.error:
        raise CimError("read of %d bytes at offset 0x%x runs past a %d-byte buffer"
                       % (struct.calcsize(fmt), off, len(buf)))


def _u8(buf, off):
    return _unpack("<B", buf, off)[0]


def _u16(buf, off):
    return _unpack("<H", buf, off)[0]


def _u32(buf, off):
    return _unpack("<I", buf, off)[0]


def _u64(buf, off):
    return _unpack("<Q", buf, off)[0]


def filetime_to_iso(value):
    """A FILETIME (100 ns ticks since 1601-01-01 UTC) as ISO 8601 UTC, or None for 0."""
    if not value:
        return None
    try:
        dt = datetime.datetime(1601, 1, 1, tzinfo=datetime.timezone.utc) + \
            datetime.timedelta(microseconds=value // 10)
    except OverflowError:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def _wmi_string(buf, off):
    """A string in a data region: one leading byte, then NUL-terminated text.

    python-cim (objects.py WMIString) skips the leading byte and decodes the rest as
    UTF-8 up to the first NUL. Measured on a Windows 11 26200 repository: the byte is 0
    and the text is Latin-1 (one byte per character) for strings whose characters all
    fit Latin-1, and the byte is 1 and the text is UTF-16LE up to a two-byte NUL for
    strings that do not. Both are decoded here; python-cim's UTF-8 reading gives the
    wrong text for both kinds whenever a character falls outside ASCII.
    """
    flag = _u8(buf, off)
    start = off + 1
    if flag == 0:
        end = buf.find(b"\x00", start)
        if end == -1:
            raise CimError("string at 0x%x has no terminator" % off)
        return buf[start:end].decode("latin-1")
    if flag == 1:
        end = start
        while True:
            end = buf.find(b"\x00\x00", end)
            if end == -1:
                raise CimError("UTF-16 string at 0x%x has no terminator" % off)
            if (end - start) % 2 == 0:
                break
            end += 1
        return buf[start:end].decode("utf-16-le", errors="replace")
    raise CimError("string at 0x%x has leading byte 0x%02x, which is not 0 or 1" % (off, flag))


# ----------------------------------------------------------------------- mapping

class Mapping(object):
    """One page mapping (data or index): logical page number -> physical page number."""

    def __init__(self, layout, version, physical_page_count, entries, used_space, first_id=None,
                 second_id=None):
        self.layout = layout
        self.version = version
        self.physical_page_count = physical_page_count
        self.entries = entries          # masked physical page numbers, by logical page
        self.used_space = used_space    # win7 only: the used_space field per entry
        self.first_id = first_id
        self.second_id = second_id

    def __len__(self):
        return len(self.entries)

    def is_mapped(self, logical):
        return 0 <= logical < len(self.entries) and self.entries[logical] != UNMAPPED_PAGE_VALUE

    def physical(self, logical):
        if not 0 <= logical < len(self.entries):
            raise UnmappedPage("logical page %d is beyond the %d mapping entries" % (logical, len(self.entries)))
        pnum = self.entries[logical]
        if pnum == UNMAPPED_PAGE_VALUE:
            raise UnmappedPage("logical page %d is not mapped" % logical)
        return pnum


def _parse_mapping(buf, off, layout):
    """Parse one mapping (header, entries, free list, footer) at ``off``; return it and the end offset."""
    if layout == LAYOUT_WIN7:
        sig, version, first_id, second_id, phys, count = _unpack("<6I", buf, off)
        off += 24
        entries = []
        used = []
        for _ in range(count):
            pn, _crc, _free, used_space, _fid, _sid = _unpack("<6I", buf, off)
            off += 24
            entries.append(pn & MAPPING_PAGE_ID_MASK)
            used.append(used_space)
    else:
        sig, version, phys, count = _unpack("<4I", buf, off)
        first_id = second_id = None
        off += 16
        entries = [v & MAPPING_PAGE_ID_MASK for v in _unpack("<%dI" % count, buf, off)]
        used = None
        off += 4 * count
    if sig != MAPPING_START_SIGNATURE:
        raise CimError("mapping start signature 0x%x, expected 0x%x" % (sig, MAPPING_START_SIGNATURE))
    free_count = _u32(buf, off)
    off += 4 + 4 * free_count
    footer = _u32(buf, off)
    off += 4
    if footer != MAPPING_END_SIGNATURE:
        raise CimError("mapping end signature 0x%x, expected 0x%x" % (footer, MAPPING_END_SIGNATURE))
    return Mapping(layout, version, phys, entries, used, first_id, second_id), off


def guess_layout(header):
    """python-cim's guess_cim_type, from the first 24 bytes of a mapping file."""
    sig, version, first_id, second_id, phys_count, map_count = _unpack("<6I", header, 0)
    if sig != MAPPING_START_SIGNATURE:
        raise CimError("unexpected mapping file signature 0x%x" % sig)
    if map_count > phys_count:
        return LAYOUT_XP
    if map_count < phys_count // 10:
        return LAYOUT_XP
    if first_id - 1 != second_id:
        return LAYOUT_XP
    return LAYOUT_WIN7


# --------------------------------------------------------------------------- keys

class Key(object):
    """An index key: slash-separated parts, the last carrying ``.page.record.length`` when it
    refers to data."""

    __slots__ = ("s",)

    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s

    def __repr__(self):
        return "Key(%s)" % self.s

    @property
    def is_data_reference(self):
        return "." in self.s

    def _data_part(self, i):
        parts = self.s.split(".")
        if len(parts) != 4:
            raise CimError("key is not a data reference: %s" % self.s)
        return int(parts[i])

    @property
    def data_page(self):
        return self._data_part(1)

    @property
    def data_id(self):
        return self._data_part(2)

    @property
    def data_length(self):
        return self._data_part(3)


# ------------------------------------------------------------------------ index

class IndexPage(object):
    def __init__(self, buf, logical, physical):
        self.logical = logical
        self.physical = physical
        self.sig, self.logical_id, _zero, self.root_page, count = _unpack("<5I", buf, 0)
        off = 20 + 4 * count                                      # skip unk0[count]
        self.children = _unpack("<%dI" % (count + 1), buf, off)
        off += 4 * (count + 1)
        self.key_refs = _unpack("<%dH" % count, buf, off)
        off += 2 * count
        sdt_len = _u16(buf, off)
        off += 2
        self.string_definitions = _unpack("<%dH" % sdt_len, buf, off)
        off += 2 * sdt_len
        st_len = _u16(buf, off)
        off += 2
        self.string_offsets = _unpack("<%dH" % (st_len + 1), buf, off)
        off += 2 * (st_len + 1)
        self.data = buf[off:]
        self.count = count
        self._keys = {}

    def _part(self, string_index):
        o = self.string_offsets[string_index]
        end = self.data.find(b"\x00", o)
        if end == -1:
            raise CimError("index page %d: key string at 0x%x has no terminator" % (self.logical, o))
        return self.data[o:end].decode("utf-8")

    def key(self, i):
        k = self._keys.get(i)
        if k is None:
            try:
                sd = self.key_refs[i]
                n = self.string_definitions[sd]
                parts = [self._part(self.string_definitions[sd + 1 + j]) for j in range(n)]
            except IndexError:
                raise CimError("index page %d: key %d points outside its tables" % (self.logical, i))
            k = self._keys[i] = Key("/".join(parts))
        return k


# ------------------------------------------------------------------- data pages

def _parse_toc(buf):
    """python-cim's TOC.vsParse: 16-byte entries up to an all-zero entry.

    python-cim returns an empty table when the entries do not end in an empty entry,
    and every object on the page then reads as absent. This returns None for that case
    so the caller can say the page did not parse.
    """
    end = buf.find(b"\x00" * 0x10, 0)
    if end == -1:
        return None
    entries = []
    off = 0
    while off < end + 0x10:
        rid, o, size, crc = _unpack("<4I", buf, off)
        off += 16
        if rid == 0 and o == 0 and size == 0 and crc == 0:
            return entries
        if rid == 0 or o >= DATA_PAGE_SIZE or o == 0 or size == 0:
            return None
        entries.append((rid, o, size, crc))
    return None


# ------------------------------------------------------------ values and regions

class CimType(object):
    __slots__ = ("type", "array_state", "raw")

    def __init__(self, buf, off):
        self.type, self.array_state, b2, b3 = _unpack("<4B", buf, off)
        self.raw = (self.type, self.array_state, b2, b3)

    @property
    def is_array(self):
        return self.array_state == ARRAY_STATE_ARRAY

    @property
    def name(self):
        n = CIM_TYPE_NAMES.get(self.type, "0x%02x" % self.type)
        return n + "[]" if self.is_array else n

    def slot_format(self):
        if self.is_array:
            return "<I"
        fmt = _VALUE_FORMATS.get(self.type)
        if fmt is None:
            raise CimError("unknown CIM type 0x%02x" % self.type)
        return fmt


def _read_slot(buf, off, cim_type):
    fmt = cim_type.slot_format()
    return _unpack(fmt, buf, off)[0], struct.calcsize(fmt)


def _region(buf, off):
    """A data region: a 32-bit size (top bit masked off), then that many bytes."""
    size = _u32(buf, off) & 0x7FFFFFFF
    data = buf[off + 4:off + 4 + size]
    if len(data) != size:
        raise CimError("data region at 0x%x declares %d bytes, %d present" % (off, size, len(data)))
    return data, off + 4 + size


def _decode_value(region, raw, cim_type):
    """Resolve a slot value against its data region (python-cim DataRegion.get_value)."""
    if cim_type.is_array:
        base = cim_type.type
        fmt = _VALUE_FORMATS.get(base)
        if fmt is None:
            raise CimError("unknown CIM array element type 0x%02x" % base)
        if base == CIM_TYPE_OBJECT:
            raise CimError("arrays of embedded objects are not decoded")
        count = _u32(region, raw)
        width = struct.calcsize(fmt)
        items = []
        off = raw + 4
        for _ in range(count):
            v = _unpack(fmt, region, off)[0]
            off += width
            items.append(_decode_scalar(region, v, base))
        return items
    return _decode_scalar(region, raw, cim_type.type)


def _decode_scalar(region, v, t):
    if t in (CIM_TYPE_STRING, CIM_TYPE_REFERENCE, CIM_TYPE_DATETIME):
        return _wmi_string(region, v)
    if t == CIM_TYPE_BOOLEAN:
        return v != 0
    if t == CIM_TYPE_OBJECT:
        raise CimError("embedded objects are not decoded")
    if t in _VALUE_FORMATS:
        return v
    raise CimError("unknown CIM type 0x%02x" % t)


class Qualifier(object):
    __slots__ = ("key_reference", "type", "raw")

    @property
    def is_builtin(self):
        return self.key_reference & 0x80000000 != 0

    def name(self, region):
        k = self.key_reference & 0x7FFFFFFF
        if self.is_builtin:
            return BUILTIN_QUALIFIERS.get(k, "BUILTIN_QUALIFIER_0x%x" % k)
        return _wmi_string(region, k)

    def value(self, region):
        return _decode_value(region, self.raw, self.type)


def _parse_qualifiers(buf, off):
    """A qualifier list: a 32-bit size that counts itself, then 9-byte-plus entries."""
    start = off
    size = _u32(buf, off)
    off += 4
    end = start + size
    out = []
    while off + 9 <= end:
        q = Qualifier()
        q.key_reference = _u32(buf, off)
        q.type = CimType(buf, off + 5)
        q.raw, width = _read_slot(buf, off + 9, q.type)
        off += 9 + width
        out.append(q)
    return out, off


def _qualifier_dict(qualifiers, region):
    out = {}
    for q in qualifiers:
        try:
            out[q.name(region)] = q.value(region)
        except CimError as exc:
            out[q.name(region) if q.is_builtin else "?0x%x" % q.key_reference] = "<%s>" % exc
    return out


def _property_states(buf, off, count):
    """Two bits per property, rounded up to whole bytes (python-cim PropertyStates)."""
    n = (2 * count + 7) // 8
    data = buf[off:off + n]
    if len(data) != n:
        raise CimError("property state bitmap at 0x%x runs past the object" % off)
    return data, off + n


def _state_bits(states, index):
    return (states[index // 4] >> (2 * (index % 4))) & 0x3


# ------------------------------------------------------------- class definitions

class ClassProperty(object):
    """A property as one class definition declares it."""

    def __init__(self, cd, name_ref, struct_ref):
        region = cd.property_data
        self.type = CimType(region, struct_ref)
        self.index = _u16(region, struct_ref + 4)
        self.offset = _u32(region, struct_ref + 6)
        self.level = _u32(region, struct_ref + 10)
        self._qualifiers, _ = _parse_qualifiers(region, struct_ref + 14)
        self._region = region
        if name_ref & 0x80000000:
            k = name_ref & 0x7FFFFFFF
            self.name = BUILTIN_PROPERTIES.get(k, "BUILTIN_PROPERTY_0x%x" % k)
        else:
            self.name = _wmi_string(region, name_ref)

    @property
    def qualifiers(self):
        return _qualifier_dict(self._qualifiers, self._region)


class ClassDefinition(object):
    def __init__(self, buf):
        sc_len = _u32(buf, 0)
        off = 4
        raw = buf[off:off + 2 * sc_len]
        if len(raw) != 2 * sc_len:
            raise CimError("class definition super class name runs past the object")
        self.super_class_name = raw.decode("utf-16-le", errors="replace").split("\x00")[0]
        off += 2 * sc_len
        self.timestamp = _u64(buf, off)
        self.data_length = _u32(buf, off + 8)
        # unk1 (1 byte) at off + 12
        self.offset_class_name = _u32(buf, off + 13)
        pdv_len = _u32(buf, off + 17)
        sca_len = _u32(buf, off + 21)
        off += 25
        if sca_len != 4:
            # the ASCII super class name (one leading byte, NUL-terminated) and a second length
            end = buf.find(b"\x00", off + 1)
            if end == -1:
                raise CimError("class definition super class ASCII name has no terminator")
            off = end + 1 + 4
        self._qualifiers, off = _parse_qualifiers(buf, off)
        count = _u32(buf, off)
        off += 4
        self._prop_refs = [_unpack("<2I", buf, off + 8 * i) for i in range(count)]
        off += 8 * count
        self.default_values_data = buf[off:off + pdv_len]
        if len(self.default_values_data) != pdv_len:
            raise CimError("class definition default values run past the object")
        off += pdv_len
        self.property_data, off = _region(buf, off)
        # The method part's 32-bit size counts its own four bytes, unlike the property
        # region's. python-cim reads it as a second DataRegion and so asks for four bytes
        # past the object, which vstruct's slicing let pass unnoticed. Measured: on the
        # Windows 11 26200 known-data repository every class definition ends exactly
        # where a self-counting size puts the end (see the README).
        msize = _u32(buf, off)
        self.method_data = buf[off + 4:off + msize]
        self.method_end = off + msize
        self.class_name = _wmi_string(self.property_data, self.offset_class_name)
        self._properties = None

    @property
    def qualifiers(self):
        return _qualifier_dict(self._qualifiers, self.property_data)

    @property
    def properties(self):
        """The properties this definition declares itself (not those it inherits)."""
        if self._properties is None:
            self._properties = [ClassProperty(self, n, s) for n, s in self._prop_refs]
        return self._properties

    @property
    def key_names(self):
        return [p.name for p in self.properties if p.qualifiers.get("PROP_QUALIFIER_KEY") is True]


class LayoutProperty(object):
    """A property in a class's full layout, with its default-value state."""

    def __init__(self, prop, layout):
        self.prop = prop
        self.layout = layout
        self.name = prop.name
        self.index = prop.index
        self.type = prop.type

    @property
    def qualifiers(self):
        return self.prop.qualifiers

    def _state(self, layout):
        bits = _state_bits(layout.default_states, self.index)
        # python-cim ClassDefinitionPropertyState(is_inherited, has_default_value)
        return bits & 0b10 != 0, bits & 0b01 == 0

    @property
    def is_inherited(self):
        return self._state(self.layout)[0]

    @property
    def has_default_value(self):
        return self._state(self.layout)[1]

    def default_value(self):
        """python-cim ClassLayoutProperty.default_value: the leaf's, else the nearest ancestor's."""
        for cl in reversed(self.layout.derivation):
            if self.index >= len(cl.properties_by_index):
                break
            inherited, has_default = self._state(cl)
            if not has_default:
                raise CimError("property %s: an ancestor in its default-value chain has no default" % self.name)
            if inherited:
                continue
            return _decode_value(cl.cd.property_data, cl.default_slots[self.index], self.type)
        raise CimError("property %s: no ancestor holds its default value" % self.name)


class ClassLayout(object):
    def __init__(self, repo, namespace, cd):
        self.repo = repo
        self.namespace = namespace
        self.cd = cd
        self.name = cd.class_name
        self._derivation = None
        self._props = None
        self._defaults = None

    @property
    def derivation(self):
        """Class layouts from the root class to this one."""
        if self._derivation is None:
            chain = [self]
            seen = {self.name.upper()}
            cl = self
            while cl.cd.super_class_name:
                sup = cl.cd.super_class_name
                if sup.upper() in seen:
                    raise CimError("class %s: derivation loops at %s" % (self.name, sup))
                seen.add(sup.upper())
                cl = self.repo.class_layout(self.namespace, sup)
                chain.append(cl)
            chain.reverse()
            self._derivation = chain
        return self._derivation

    @property
    def ancestor_names(self):
        return [cl.name for cl in self.derivation]

    @property
    def properties_by_index(self):
        if self._props is None:
            by_index = {}
            for cl in self.derivation:
                for p in cl.cd.properties:
                    by_index[p.index] = LayoutProperty(p, self)
            ordered = [by_index[i] for i in sorted(by_index)]
            for pos, p in enumerate(ordered):
                if p.index != pos:
                    raise CimError("class %s: property indexes are not contiguous (%d at position %d)"
                                   % (self.name, p.index, pos))
            self._props = ordered
        return self._props

    def _parse_defaults(self):
        props = self.properties_by_index
        buf = self.cd.default_values_data
        states, off = _property_states(buf, 0, len(props))
        slots = []
        for p in props:
            v, w = _read_slot(buf, off, p.type)
            slots.append(v)
            off += w
        self._defaults = (states, slots)

    @property
    def default_states(self):
        if self._defaults is None:
            self._parse_defaults()
        return self._defaults[0]

    @property
    def default_slots(self):
        if self._defaults is None:
            self._parse_defaults()
        return self._defaults[1]

    @property
    def key_names(self):
        return [p.name for p in self.properties_by_index if p.qualifiers.get("PROP_QUALIFIER_KEY") is True]


# --------------------------------------------------------------------- instances

class Instance(object):
    """One decoded class instance.

    ``properties`` maps each property name, in property-index order, to its value, or
    to None when the instance marks the property as not initialized (NULL).
    ``timestamp_1`` and ``timestamp_2`` are the two FILETIMEs at the head of the
    instance record, which python-cim names ts1 and ts2 without saying what they are;
    see the README for what known data shows about them.
    """

    def __init__(self, namespace, class_name, key):
        self.namespace = namespace
        self.class_name = class_name
        self.key = key
        self.properties = {}
        self.property_types = {}
        self.defaulted = []
        self.timestamp_1 = None
        self.timestamp_2 = None
        self.errors = []

    location = None   # set by Repository.instances from Repository.read_object

    def to_dict(self):
        return {
            "namespace": self.namespace,
            "class": self.class_name,
            "timestamp_1": filetime_to_iso(self.timestamp_1),
            "timestamp_2": filetime_to_iso(self.timestamp_2),
            "properties": self.properties,
            "property_types": self.property_types,
            "from_class_default": self.defaulted,
            "location": self.location,
            "errors": self.errors,
        }


def _parse_instance(layout_kind, cl, buf, inst):
    props = cl.properties_by_index
    if buf[0:4] == b"\x00\x00\x00\x00":
        # python-cim's CoreClassInstance (XP __NAMESPACE): it compares the bytes with a
        # str, so on Python 3 this branch never ran there. It is taken here as python-cim
        # intended it.
        inst.timestamp_1 = _u64(buf, 4)
        off = 4 + 8 + 4 + 8
        slots = []
        for p in props:
            v, w = _read_slot(buf, off, p.type)
            slots.append(v)
            off += w
        _, off = _parse_qualifiers(buf, off)
        off += 4
        region, _ = _region(buf, off)
        for p, raw in zip(props, slots):
            inst.property_types[p.name] = p.type.name
            try:
                inst.properties[p.name] = _decode_value(region, raw, p.type)
            except CimError as exc:
                inst.properties[p.name] = None
                inst.errors.append("property %s: %s" % (p.name, exc))
        return
    off = 0x40 if layout_kind == LAYOUT_XP else 0x80          # the class name hash, UTF-16
    inst.timestamp_1 = _u64(buf, off)
    inst.timestamp_2 = _u64(buf, off + 8)
    off += 16 + 4 + 4 + 1          # data_length2, offset_instance_class_name, unk0
    states, off = _property_states(buf, off, len(props))
    slots = []
    for p in props:
        v, w = _read_slot(buf, off, p.type)
        slots.append(v)
        off += w
    _, off = _parse_qualifiers(buf, off)
    dyn = _u8(buf, off)
    off += 1
    if dyn == DYNPROPS_PRESENT:
        # python-cim's Dynprops parser reads the count twice and never reads the entries,
        # so the data region after them would be misplaced. Refuse rather than misread.
        raise CimError("instance carries dynamic properties (flag 2), which are not decoded")
    if dyn != DYNPROPS_NONE:
        raise CimError("instance dynamic-properties flag is 0x%02x, expected 1 or 2" % dyn)
    region, _ = _region(buf, off)
    for p, raw in zip(props, slots):
        inst.property_types[p.name] = p.type.name
        bits = _state_bits(states, p.index)
        # python-cim InstancePropertyState(use_default_value, is_initialized)
        use_default, initialized = bits & 0b10 != 0, bits & 0b01 == 0
        try:
            if not initialized:
                inst.properties[p.name] = None
            elif use_default:
                inst.properties[p.name] = p.default_value()
                inst.defaulted.append(p.name)
            else:
                inst.properties[p.name] = _decode_value(region, raw, p.type)
        except CimError as exc:
            inst.properties[p.name] = None
            inst.errors.append("property %s: %s" % (p.name, exc))


# -------------------------------------------------------------------- repository

def _find_case_insensitive(directory, name):
    try:
        names = os.listdir(directory)
    except OSError:
        return None
    for n in names:
        if n.upper() == name.upper():
            return os.path.join(directory, n)
    return None


def _resolve_directory(path):
    """The folder holding OBJECTS.DATA: ``path`` itself, or its Repository or FS folder."""
    for _ in range(3):
        if _find_case_insensitive(path, "OBJECTS.DATA"):
            return path
        for name in ("Repository", "FS"):
            sub = _find_case_insensitive(path, name)
            if sub and os.path.isdir(sub):
                path = sub
                break
        else:
            break
    raise CimError("%s holds no OBJECTS.DATA (nor does a Repository or FS folder in it)" % path)


class Repository(object):
    """A WMI CIM repository folder, opened read-only."""

    def __init__(self, path, layout=None):
        self.directory = _resolve_directory(path)
        self._data_path = _find_case_insensitive(self.directory, "OBJECTS.DATA")
        self._index_path = _find_case_insensitive(self.directory, "INDEX.BTR")
        if not self._data_path or not self._index_path:
            raise CimError("%s lacks OBJECTS.DATA or INDEX.BTR" % self.directory)
        maps = []
        for i in range(MAX_MAPPING_FILES):
            p = _find_case_insensitive(self.directory, "MAPPING%d.MAP" % (i + 1))
            if p:
                maps.append(p)
        if not maps:
            # Not in python-cim. An early Windows XP repository (Repository\FS) keeps its
            # data mapping in OBJECTS.MAP and its index mapping in INDEX.MAP. Measured on
            # one image (corpus key cfreds_hacking_case_winxp, XP build 2600 with no service
            # pack): each file is exactly one mapping in python-cim's XP structure, start
            # and end signatures in place and every byte consumed.
            om = _find_case_insensitive(self.directory, "OBJECTS.MAP")
            im = _find_case_insensitive(self.directory, "INDEX.MAP")
            if not (om and im):
                raise CimError("%s holds neither MAPPING1.MAP to MAPPING3.MAP nor OBJECTS.MAP and INDEX.MAP"
                               % self.directory)
            self._open_split_mapping(om, im, layout or LAYOUT_XP)
            return
        if layout is None:
            with open(maps[0], "rb") as f:
                layout = guess_layout(f.read(24))
        if layout not in (LAYOUT_XP, LAYOUT_WIN7):
            raise CimError("unknown layout %r" % layout)
        self.layout = layout
        # python-cim picks the mapping file whose header version is highest.
        self.mapping_versions = {}
        best = None
        for p in maps:
            with open(p, "rb") as f:
                head = f.read(8)
            if len(head) < 8:
                continue
            sig, version = struct.unpack("<II", head)
            if sig != MAPPING_START_SIGNATURE:
                continue
            self.mapping_versions[os.path.basename(p)] = version
            if best is None or version > best[1]:
                best = (p, version)
        if best is None:
            raise CimError("no mapping file has a valid header")
        self.mapping_path = best[0]
        with open(self.mapping_path, "rb") as f:
            buf = f.read()
        self.data_mapping, off = _parse_mapping(buf, 0, layout)
        self.index_mapping, off = _parse_mapping(buf, off, layout)
        self.mapping_bytes_used = off
        self.mapping_file_size = len(buf)
        self._open_files()

    def _open_split_mapping(self, objects_map, index_map, layout):
        if layout not in (LAYOUT_XP, LAYOUT_WIN7):
            raise CimError("unknown layout %r" % layout)
        self.layout = layout
        used = size = 0
        versions = {}
        mappings = []
        for p in (objects_map, index_map):
            with open(p, "rb") as f:
                buf = f.read()
            m, off = _parse_mapping(buf, 0, layout)
            mappings.append(m)
            versions[os.path.basename(p)] = m.version
            used += off
            size += len(buf)
        self.data_mapping, self.index_mapping = mappings
        self.mapping_versions = versions
        self.mapping_path = objects_map
        self.mapping_bytes_used = used
        self.mapping_file_size = size
        self._open_files()

    def _open_files(self):
        self._data = open(self._data_path, "rb")
        self._index = open(self._index_path, "rb")
        self.data_page_count = os.path.getsize(self._data_path) // DATA_PAGE_SIZE
        self.index_page_count = os.path.getsize(self._index_path) // INDEX_PAGE_SIZE
        self._index_pages = {}
        self._cds = {}
        self._cls = {}
        self.stats = {"index_pages_not_active": 0}

    # context manager
    def close(self):
        self._data.close()
        self._index.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -------- pages
    @staticmethod
    def _read_page(f, pnum, count, what):
        if not 0 <= pnum < count:
            raise CimError("%s physical page %d is beyond the file's %d pages" % (what, pnum, count))
        f.seek(pnum * DATA_PAGE_SIZE)
        buf = f.read(DATA_PAGE_SIZE)
        if len(buf) != DATA_PAGE_SIZE:
            raise CimError("%s physical page %d read short (%d bytes)" % (what, pnum, len(buf)))
        return buf

    def data_page(self, logical):
        return self._read_page(self._data, self.data_mapping.physical(logical), self.data_page_count,
                               "OBJECTS.DATA")

    def index_page(self, logical):
        p = self._index_pages.get(logical)
        if p is None:
            pnum = self.index_mapping.physical(logical)
            p = IndexPage(self._read_page(self._index, pnum, self.index_page_count, "INDEX.BTR"),
                          logical, pnum)
            if p.sig != PAGE_TYPE_ACTIVE:
                self.stats["index_pages_not_active"] += 1
            self._index_pages[logical] = p
        return p

    @property
    def root_index_page_number(self):
        if self.layout == LAYOUT_WIN7:
            # python-cim: the used_space field of the index mapping's first entry
            return self.index_mapping.used_space[0]
        return self.index_page(0).root_page

    # -------- index
    def _child(self, page, i):
        c = page.children[i]
        if c in (INDEX_PAGE_INVALID, INDEX_PAGE_INVALID2):
            return None
        return self.index_page(c)

    def lookup(self, prefix):
        """Index keys that contain ``prefix`` (python-cim Index.lookup_keys).

        python-cim visits the child between two matching keys twice, once as the right
        child of the first and once as the left child of the second, and returns its
        keys twice; it removed the repeats later, by instance key. They are removed
        here, by index key, keeping the first.
        """
        out = []
        seen = set()
        for k in self._lookup(str(prefix), self.index_page(self.root_index_page_number), 0):
            if k.s not in seen:
                seen.add(k.s)
                out.append(k)
        return out

    def _lookup(self, skey, page, depth):
        if depth > 64:
            raise CimError("index walk deeper than 64 levels at page %d" % page.logical)
        matches = []

        def side(i):
            child = self._child(page, i)
            return self._lookup(skey, child, depth + 1) if child is not None else []

        n = page.count
        for i in range(n):
            sk = page.key(i).s
            last = i == n - 1
            if skey in sk:
                matches.extend(side(i))
                matches.append(page.key(i))
                matches.extend(side(i + 1))
                if last:
                    break
                continue
            if skey < sk:
                matches.extend(side(i))
                break
            if last:
                matches.extend(side(i + 1))
        return matches

    def iter_keys(self):
        """Every key the index reaches from its root, in order."""
        seen = set()

        def walk(page, depth):
            if depth > 64:
                raise CimError("index walk deeper than 64 levels at page %d" % page.logical)
            if page.logical in seen:
                raise CimError("index page %d is reached twice" % page.logical)
            seen.add(page.logical)
            for i in range(page.count + 1):
                child = self._child(page, i)
                if child is not None:
                    for k in walk(child, depth + 1):
                        yield k
                if i < page.count:
                    yield page.key(i)

        return walk(self.index_page(self.root_index_page_number), 0)

    # -------- objects
    def object_bytes(self, key):
        """The bytes of the object a data-reference key names (python-cim get_object_buffer)."""
        return self.read_object(key)[0]

    def read_object(self, key):
        """The object's bytes and where they are: its first physical page in OBJECTS.DATA,
        the byte offset of its first byte in that file, and how many pages it spans."""
        if not key.is_data_reference:
            raise CimError("key is not a data reference: %s" % key)
        physical = self.data_mapping.physical(key.data_page)
        page = self.data_page(key.data_page)
        toc = _parse_toc(page)
        if toc is None:
            raise CimError("data page %d: table of contents does not parse" % key.data_page)
        want = key.data_length
        for rid, o, size, _crc in toc:
            if rid == key.data_id:
                if size < want:
                    raise CimError("data page %d record %d: TOC size %d is less than the key's %d"
                                   % (key.data_page, rid, size, want))
                first = page[o:o + size]
                break
        else:
            raise NotFound("data page %d holds no record %d" % (key.data_page, key.data_id))
        where = {"logical_page": key.data_page, "physical_page": physical, "record_id": key.data_id,
                 "length": want, "file_offset": physical * DATA_PAGE_SIZE + o, "pages": 1}
        if len(first) >= want:
            return first[:want], where
        # an object larger than its page continues on the following logical pages
        parts = [first]
        got = len(first)
        i = 1
        while got < want:
            nxt = self.data_page(key.data_page + i)
            take = min(len(nxt), want - got)
            parts.append(nxt[:take])
            got += take
            i += 1
        where["pages"] = i
        return b"".join(parts), where

    # -------- names
    def _hash(self, name):
        h = hashlib.md5() if self.layout == LAYOUT_XP else hashlib.sha256()
        h.update(name.upper().encode("utf-16-le"))
        return h.hexdigest().upper()

    def NS(self, name=None):
        return "NS_" + (self._hash(name) if name is not None else "")

    def CD(self, name=None):
        return "CD_" + (self._hash(name) if name is not None else "")

    def CI(self, name=None):
        return "CI_" + (self._hash(name) if name is not None else "")

    def IL(self, name=None):
        return "IL_" + (self._hash(name) if name is not None else "")

    # -------- classes
    def _single(self, prefix):
        refs = self.lookup(prefix)
        if len(refs) > 1:
            raise CimError("%d index keys match %s" % (len(refs), prefix))
        return refs[0] if refs else None

    def class_definition(self, namespace, name):
        """The class definition, looked up in ``namespace`` and then in __SystemClass."""
        cid = (namespace.upper(), name.upper())
        cd = self._cds.get(cid)
        if cd is None:
            ref = self._single("%s/%s" % (self.NS(namespace), self.CD(name)))
            if ref is None:
                ref = self._single("%s/%s" % (self.NS(SYSTEM_NAMESPACE_NAME), self.CD(name)))
            if ref is None:
                raise NotFound("class %s not found in %s or %s" % (name, namespace, SYSTEM_NAMESPACE_NAME))
            cd = self._cds[cid] = ClassDefinition(self.object_bytes(ref))
        return cd

    def class_layout(self, namespace, name):
        cid = (namespace.upper(), name.upper())
        cl = self._cls.get(cid)
        if cl is None:
            cl = self._cls[cid] = ClassLayout(self, namespace, self.class_definition(namespace, name))
        return cl

    def own_class_names(self, namespace):
        """Names of the classes defined in ``namespace`` itself (python-cim get_ns_children_cd)."""
        out = []
        for ref in self.lookup("%s/%s" % (self.NS(namespace), self.CD())):
            out.append(ClassDefinition(self.object_bytes(ref)).class_name)
        return out

    def class_names(self, namespace):
        """Classes visible in ``namespace``: __SystemClass's, then its own (python-cim TreeNamespace.classes)."""
        seen = set()
        out = []
        names = [] if namespace.upper() == SYSTEM_NAMESPACE_NAME.upper() else self.own_class_names(SYSTEM_NAMESPACE_NAME)
        for n in names + self.own_class_names(namespace):
            if n.upper() not in seen:
                seen.add(n.upper())
                out.append(n)
        return out

    # -------- instances
    def instances(self, namespace, class_name):
        """Every instance of exactly ``class_name`` in ``namespace``, as Instance objects.

        An instance that cannot be read is still yielded, with its ``errors`` set, so a
        caller can tell "none there" from "could not read".
        """
        cl = self.class_layout(namespace, class_name)
        prefix = "%s/%s/%s" % (self.NS(namespace), self.CI(class_name), self.IL())
        for ref in self.lookup(prefix):
            inst = Instance(namespace, cl.name, ref)
            try:
                buf, inst.location = self.read_object(ref)
                _parse_instance(self.layout, cl, buf, inst)
            except CimError as exc:
                inst.errors.append(str(exc))
            yield inst

    def child_namespaces(self, namespace):
        out = []
        for inst in self.instances(namespace, NAMESPACE_CLASS_NAME):
            name = inst.properties.get("Name")
            if inst.errors or not name:
                raise CimError("__namespace instance in %s unreadable: %s" % (namespace, "; ".join(inst.errors)))
            out.append(namespace + "\\" + name)
        return out

    def namespaces(self, start=ROOT_NAMESPACE_NAME):
        """``start`` and every namespace below it, depth first."""
        out = []
        stack = [start]
        seen = set()
        while stack:
            ns = stack.pop()
            if ns.upper() in seen:
                continue
            seen.add(ns.upper())
            out.append(ns)
            stack.extend(reversed(self.child_namespaces(ns)))
        return out


def open_repository(path, layout=None):
    return Repository(path, layout)


# ------------------------------------------------------------------ subscriptions

def subscription_classes(repo, namespace):
    """Classes in ``namespace`` that are, or derive from, one of SUBSCRIPTION_BASES."""
    bases = {b.upper(): b for b in SUBSCRIPTION_BASES}
    out = []
    errors = []
    for name in repo.class_names(namespace):
        try:
            chain = repo.class_layout(namespace, name).ancestor_names
        except CimError as exc:
            errors.append("class %s: %s" % (name, exc))
            continue
        hit = [bases[c.upper()] for c in chain if c.upper() in bases]
        if hit:
            out.append((name, hit[0], chain))
    return out, errors


def subscriptions(repo, namespaces=SUBSCRIPTION_NAMESPACES):
    """Every instance of a subscription class in ``namespaces``, as a dict for JSON."""
    result = {"namespaces": {}, "errors": []}
    for ns in namespaces:
        try:
            classes, errs = subscription_classes(repo, ns)
        except CimError as exc:
            result["errors"].append("%s: %s" % (ns, exc))
            continue
        result["errors"].extend("%s: %s" % (ns, e) for e in errs)
        rows = []
        for name, base, chain in classes:
            try:
                for inst in repo.instances(ns, name):
                    d = inst.to_dict()
                    d["kind"] = base
                    d["derivation"] = chain
                    rows.append(d)
            except CimError as exc:
                result["errors"].append("%s:%s: %s" % (ns, name, exc))
        result["namespaces"][ns] = rows
    return result


# -------------------------------------------------------------------- command line

def _info(repo):
    return {
        "directory": repo.directory,
        "layout": repo.layout,
        "mapping_files": sorted(repo.mapping_versions) if repo.mapping_path.upper().endswith("OBJECTS.MAP")
        else [os.path.basename(repo.mapping_path)],
        "mapping_versions": repo.mapping_versions,
        "mapping_bytes_used": repo.mapping_bytes_used,
        "mapping_file_size": repo.mapping_file_size,
        "data_mapping_entries": len(repo.data_mapping),
        "index_mapping_entries": len(repo.index_mapping),
        "data_pages_in_file": repo.data_page_count,
        "index_pages_in_file": repo.index_page_count,
        "root_index_page": repo.root_index_page_number,
        "root_index_page_signature": "0x%04x" % repo.index_page(repo.root_index_page_number).sig,
    }


def _dump(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="cimreader",
        description="Read a Windows WMI CIM repository (OBJECTS.DATA, INDEX.BTR, MAPPING*.MAP), read-only.")
    ap.add_argument("--version", action="version", version="cimreader " + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("repository", help="the Repository folder (or the wbem folder holding it)")
        p.add_argument("--layout", choices=[LAYOUT_XP, LAYOUT_WIN7],
                       help="skip layout detection")
        return p

    add("info", "layout, active mapping and page counts")
    add("namespaces", "every namespace below root")
    p = add("classes", "classes visible in a namespace")
    p.add_argument("namespace")
    p = add("instances", "instances of one class, decoded")
    p.add_argument("namespace")
    p.add_argument("class_name")
    p = add("subscriptions", "WMI event subscription objects, as JSON")
    p.add_argument("--namespace", action="append",
                   help="namespace to list (repeatable; default root\\subscription and root\\default)")
    p = add("keys", "index keys (all, or those containing a prefix)")
    p.add_argument("--prefix")
    args = ap.parse_args(argv)

    try:
        with open_repository(args.repository, args.layout) as repo:
            if args.cmd == "info":
                _dump(_info(repo))
            elif args.cmd == "namespaces":
                for ns in repo.namespaces():
                    print(ns)
            elif args.cmd == "classes":
                for n in repo.class_names(args.namespace):
                    print(n)
            elif args.cmd == "instances":
                rows = [i.to_dict() for i in repo.instances(args.namespace, args.class_name)]
                _dump(rows)
                return 2 if any(r["errors"] for r in rows) else 0
            elif args.cmd == "subscriptions":
                res = subscriptions(repo, tuple(args.namespace) if args.namespace else SUBSCRIPTION_NAMESPACES)
                _dump(res)
                bad = res["errors"] or any(r["errors"] for rows in res["namespaces"].values() for r in rows)
                return 2 if bad else 0
            elif args.cmd == "keys":
                keys = repo.lookup(args.prefix) if args.prefix else repo.iter_keys()
                for k in keys:
                    print(k)
    except CimError as exc:
        sys.stderr.write("cimreader: %s\n" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
