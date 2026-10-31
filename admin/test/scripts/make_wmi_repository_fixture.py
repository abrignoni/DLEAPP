"""Writes the public fixture for the WMI Repository artifacts: an authored repository.

Every namespace, class, name, query, command line and SID here is written for the
fixture; nothing comes from a real machine. The files are laid out the way the vendored
reader (scripts/vendor/cimprobe.py) reads them: a MAPPING*.MAP file whose highest version
holds the active data and index mappings (an older, wrong generation sits beside it), an
INDEX.BTR with a root page and two leaves, and an OBJECTS.DATA whose physical pages are in
the reverse of their logical order. The class definition and instance layouts are the
ones cimprobe's own synthetic tests write (github.com/abrignoni/cimprobe,
tests/test_cimprobe.py), which known data from Windows 11 matched.

What the fixture holds, so the expected rows can be read off it:
- root\\subscription: three filters (one bound to a command line consumer, one to a script
  consumer whose script spans four data pages, one bound to a consumer that is not in
  the repository), a CommandLineEventConsumer, an ActiveScriptEventConsumer, a consumer of
  a class derived from __EventConsumer under another name, which no binding names, and
  three bindings. One filter name and one command line hold non-ASCII text.
- root\\default: one filter, one LogFileEventConsumer and the binding between them.

Run it, then hand the archive to the repo's case-data tool:

    python admin/test/scripts/make_wmi_repository_fixture.py --archive wmi_synthetic.zip
    python admin/test/scripts/make_case_data.py windowsWmiRepository --case 1 --input wmi_synthetic.zip
"""

import argparse
import hashlib
import io
import struct
import zipfile

PAGE = 0x2000
ROOT = 'Windows/System32/wbem/Repository/'

T_STRING, T_BOOL, T_UINT8, T_UINT32, T_REF = 0x08, 0x0B, 0x11, 0x13, 0x66
FORMATS = {T_STRING: '<I', T_BOOL: '<H', T_UINT8: '<B', T_UINT32: '<I', T_REF: '<I'}
KEY_QUALIFIER = struct.pack('<IB4BH', 0x80000001, 0, T_BOOL, 0, 0, 0, 0xFFFF)


def h(name):
    return hashlib.sha256(name.upper().encode('utf-16-le')).hexdigest().upper()


def wstr(s):
    try:
        return b'\x00' + s.encode('latin-1') + b'\x00'
    except UnicodeEncodeError:
        return b'\x01' + s.encode('utf-16-le') + b'\x00\x00'


def qualifiers(entries):
    body = b''.join(entries)
    return struct.pack('<I', 4 + len(body)) + body


def states(bits):
    out = bytearray((2 * len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        out[i // 4] |= b << (2 * (i % 4))
    return bytes(out)


class Prop:
    def __init__(self, name, t, array=False, key=False, default=None):
        self.name, self.t, self.array, self.key, self.default = name, t, array, key, default

    def width(self):
        return 4 if self.array else struct.calcsize(FORMATS[self.t])


class Cls:
    def __init__(self, name, sup=None, props=()):
        self.name, self.sup, self.own = name, sup, list(props)


def chain(classes, name):
    out = []
    c = classes[name]
    while c:
        out.append(c)
        c = classes.get(c.sup) if c.sup else None
    out.reverse()
    return out, [p for c in out for p in c.own]


def class_definition(classes, name):
    c = classes[name]
    ch, props = chain(classes, name)
    reg = bytearray()

    def add(b):
        off = len(reg)
        reg.extend(b)
        return off
    name_off = add(wstr(c.name))
    base = len(props) - len(c.own)
    refs = []
    for i, p in enumerate(c.own):
        pn = add(wstr(p.name))
        t = bytes([p.t, 0x20 if p.array else 0, 0, 0])
        q = qualifiers([KEY_QUALIFIER] if p.key else [])
        refs.append((pn, add(t + struct.pack('<HII', base + i, 0, len(ch) - 1) + q)))
    bits, slots = [], b''
    for i, p in enumerate(props):
        own = i >= base
        if p.default is not None and own:
            bits.append(0b00)
            slots += struct.pack(FORMATS[p.t], p.default)
        else:
            bits.append(0b10 if p.default is not None else (0b01 if own else 0b11))
            slots += b'\x00' * p.width()
    pdv = states(bits) + slots
    sup = c.sup or ''
    head = struct.pack('<I', len(sup)) + sup.encode('utf-16-le')
    head += struct.pack('<QIBIII', 0x01DB000000000000, 0, 0, name_off, len(pdv), len(sup) + 8 if sup else 4)
    if sup:
        head += b'\x00' + sup.encode('ascii') + b'\x00' + struct.pack('<I', len(sup))
    body = qualifiers([]) + struct.pack('<I', len(refs)) + b''.join(struct.pack('<II', a, b) for a, b in refs)
    body += pdv + struct.pack('<I', 0x80000000 | len(reg)) + bytes(reg)
    return head + body + struct.pack('<I', 12) + b'\x00' * 8


def instance(classes, name, values):
    _, props = chain(classes, name)
    reg = bytearray(wstr(name))
    bits, slots = [], b''
    for p in props:
        v = values.get(p.name)
        if v is None:
            bits.append(0b01)
            slots += b'\x00' * p.width()
            continue
        bits.append(0b00)
        if p.array:
            ref = len(reg)
            reg.extend(struct.pack('<I', len(v)) + b''.join(struct.pack(FORMATS[p.t], x) for x in v))
            slots += struct.pack('<I', ref)
        elif p.t in (T_STRING, T_REF):
            slots += struct.pack('<I', len(reg))
            reg.extend(wstr(v))
        elif p.t == T_BOOL:
            slots += struct.pack('<H', 0xFFFF if v else 0)
        else:
            slots += struct.pack(FORMATS[p.t], v)
    out = ('A' * 64).encode('utf-16-le')
    out += struct.pack('<QQIIB', 0x01DB000000000001, 0x01DB000000000000, 0, 0, 0)
    out += states(bits) + slots + qualifiers([]) + b'\x01' + struct.pack('<I', len(reg)) + bytes(reg)
    return out


def index_page(keys, children, sig=0xACCC, root_page=0):
    data, offsets, sdt, refs = bytearray(), [], [], []
    for k in keys:
        parts = k.split('/')
        refs.append(len(sdt))
        sdt.append(len(parts))
        for part in parts:
            sdt.append(len(offsets))
            offsets.append(len(data))
            data += part.encode('ascii') + b'\x00'
    offsets = offsets or [0]
    n = len(keys)
    buf = struct.pack('<5I', sig, 0, 0, root_page, n) + b'\x00' * (4 * n)
    buf += struct.pack(f'<{n + 1}I', *children) + struct.pack(f'<{n}H', *refs)
    buf += struct.pack('<H', len(sdt)) + struct.pack(f'<{len(sdt)}H', *sdt)
    buf += struct.pack('<H', len(offsets) - 1) + struct.pack(f'<{len(offsets)}H', *offsets) + bytes(data)
    assert len(buf) <= PAGE
    return buf.ljust(PAGE, b'\x00')


def mapping(version, entries, root=0):
    out = struct.pack('<6I', 0xABCD, version, version + 1, version, len(entries), len(entries))
    for i, e in enumerate(entries):
        out += struct.pack('<6I', e, 0, 0, root if i == 0 else 0, 0, 0)
    return out + struct.pack('<II', 0, 0xDCBA)


SID = [1, 5, 0, 0, 0, 0, 0, 5, 21, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0xE9, 0x03, 0, 0]
SYS = {
    '__SystemClass': Cls('__SystemClass'),
    '__namespace': Cls('__namespace', '__SystemClass', [Prop('Name', T_STRING, key=True)]),
    '__IndicationRelated': Cls('__IndicationRelated', '__SystemClass'),
    '__EventFilter': Cls('__EventFilter', '__IndicationRelated', [
        Prop('CreatorSID', T_UINT8, array=True), Prop('EventNamespace', T_STRING),
        Prop('Name', T_STRING, key=True), Prop('Query', T_STRING), Prop('QueryLanguage', T_STRING)]),
    '__EventConsumer': Cls('__EventConsumer', '__IndicationRelated', [
        Prop('CreatorSID', T_UINT8, array=True), Prop('MachineName', T_STRING),
        Prop('MaximumQueueSize', T_UINT32)]),
    '__FilterToConsumerBinding': Cls('__FilterToConsumerBinding', '__IndicationRelated', [
        Prop('Consumer', T_REF, key=True), Prop('CreatorSID', T_UINT8, array=True),
        Prop('DeliverSynchronously', T_BOOL), Prop('Filter', T_REF, key=True)]),
}
SUB = {
    'CommandLineEventConsumer': Cls('CommandLineEventConsumer', '__EventConsumer', [
        Prop('CommandLineTemplate', T_STRING), Prop('ExecutablePath', T_STRING),
        Prop('KillTimeout', T_UINT32, default=0), Prop('Name', T_STRING, key=True),
        Prop('WorkingDirectory', T_STRING)]),
    'ActiveScriptEventConsumer': Cls('ActiveScriptEventConsumer', '__EventConsumer', [
        Prop('Name', T_STRING, key=True), Prop('ScriptFileName', T_STRING),
        Prop('ScriptingEngine', T_STRING), Prop('ScriptText', T_STRING)]),
    'FixtureNotifyConsumer': Cls('FixtureNotifyConsumer', '__EventConsumer', [
        Prop('Name', T_STRING, key=True), Prop('Target', T_STRING)]),
}
DEF = {
    'LogFileEventConsumer': Cls('LogFileEventConsumer', '__EventConsumer', [
        Prop('Filename', T_STRING), Prop('Name', T_STRING, key=True), Prop('Text', T_STRING)]),
}
ALL = dict(SYS, **SUB, **DEF)

Q = "SELECT * FROM __InstanceCreationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name = 'fixture.exe'"
SCRIPT = '\r\n'.join(f"' fixture script line {i:04d}" for i in range(1000)) + '\r\nDim x : x = 1'
S, D = 'root\\subscription', 'root\\default'
INSTANCES = [
    (S, '__EventFilter', {'Name': 'Fixture Filter \u00e9\u65e5', 'Query': Q, 'QueryLanguage': 'WQL',
                          'EventNamespace': 'root\\cimv2', 'CreatorSID': SID}),
    (S, '__EventFilter', {'Name': 'Fixture Script Filter', 'Query': 'SELECT * FROM __TimerEvent WHERE TimerID = "fixture"',
                          'QueryLanguage': 'WQL', 'CreatorSID': SID}),
    (S, '__EventFilter', {'Name': 'Fixture Orphan Filter', 'Query': 'SELECT * FROM __InstanceDeletionEvent WITHIN 30',
                          'QueryLanguage': 'WQL'}),
    (S, 'CommandLineEventConsumer', {'Name': 'Fixture Command', 'CommandLineTemplate':
                                     'cmd.exe /c echo fixture \u00e9 > C:\\Fixture\\out.txt',
                                     'WorkingDirectory': 'C:\\Fixture', 'CreatorSID': SID}),
    (S, 'ActiveScriptEventConsumer', {'Name': 'Fixture Script', 'ScriptingEngine': 'VBScript',
                                      'ScriptText': SCRIPT, 'CreatorSID': SID}),
    (S, 'FixtureNotifyConsumer', {'Name': 'Fixture Notify', 'Target': 'fixture-target'}),
    (S, '__FilterToConsumerBinding', {'Filter': '\\\\.\\ROOT\\subscription:__EventFilter.Name="Fixture Filter \u00e9\u65e5"',
                                      'Consumer': '\\\\.\\ROOT\\subscription:CommandLineEventConsumer.Name="Fixture Command"',
                                      'CreatorSID': SID, 'DeliverSynchronously': False}),
    (S, '__FilterToConsumerBinding', {'Filter': '__EventFilter.Name="Fixture Script Filter"',
                                      'Consumer': 'ActiveScriptEventConsumer.Name="Fixture Script"', 'CreatorSID': SID}),
    (S, '__FilterToConsumerBinding', {'Filter': '__EventFilter.Name="Fixture Orphan Filter"',
                                      'Consumer': 'CommandLineEventConsumer.Name="Fixture Missing Consumer"'}),
    (D, '__EventFilter', {'Name': 'Fixture Default Filter', 'Query': Q, 'QueryLanguage': 'WQL',
                          'EventNamespace': 'root\\cimv2'}),
    (D, 'LogFileEventConsumer', {'Name': 'Fixture Log', 'Filename': 'C:\\Fixture\\log.txt', 'Text': 'fixture log line'}),
    (D, '__FilterToConsumerBinding', {'Filter': '\\\\.\\ROOT\\default:__EventFilter.Name="Fixture Default Filter"',
                                      'Consumer': '\\\\.\\ROOT\\default:LogFileEventConsumer.Name="Fixture Log"'}),
]


def build():
    pages, keys, cur = [], [], None
    next_id = 0x100

    def place(path, obj):
        nonlocal cur, next_id
        rid = next_id
        next_id += 7
        if len(obj) > PAGE // 2:
            cur = None
            start = len(pages)
            pages.append([[(rid, 32, len(obj))], bytearray(obj[:PAGE - 32])])
            rest = obj[PAGE - 32:]
            while rest:
                pages.append([None, bytearray(rest[:PAGE])])
                rest = rest[PAGE:]
            page = start
        else:
            if cur is None or 16 * (len(cur[0]) + 2) + len(cur[1]) + len(obj) > PAGE - 64:  # pylint: disable=unsubscriptable-object
                cur = [[], bytearray()]
                pages.append(cur)
            cur[0].append((rid, None, len(obj)))
            cur[1] += obj
            page = len(pages) - 1
        keys.append(f'{path}.{page}.{rid}.{len(obj)}')

    for name in SYS:
        place(f'NS_{h("__SystemClass")}/CD_{h(name)}', class_definition(ALL, name))
    for ns, group in ((S, SUB), (D, DEF)):
        for name in group:
            place(f'NS_{h(ns)}/CD_{h(name)}', class_definition(ALL, name))
    for child in ('subscription', 'default'):
        place(f'NS_{h("root")}/CI_{h("__namespace")}/IL_{h(child)}', instance(ALL, '__namespace', {'Name': child}))
    for i, (ns, cls, values) in enumerate(INSTANCES):
        place(f'NS_{h(ns)}/CI_{h(cls)}/IL_{h(str(i))}', instance(ALL, cls, values))

    def data_page(page):
        toc, body = page
        if toc is None:
            return bytes(body).ljust(PAGE, b'\x00')
        if toc[0][1] == 32:
            return (struct.pack('<4I', toc[0][0], 32, toc[0][2], 0) + b'\x00' * 16 + bytes(body))[:PAGE]
        out, off = b'', 16 * (len(toc) + 1)
        for rid, _, size in toc:
            out += struct.pack('<4I', rid, off, size, 0)
            off += size
        return (out + b'\x00' * 16 + bytes(body)).ljust(PAGE, b'\x00')

    keys.sort()
    mid = len(keys) // 2
    ipages = [index_page([], [0], sig=0xADDD, root_page=1), index_page([keys[mid]], [2, 3]),
              index_page(keys[:mid], [0] * (mid + 1)), index_page(keys[mid + 1:], [0] * (len(keys) - mid))]
    dpages = [data_page(p) for p in pages]
    dmap = [len(dpages) - 1 - i for i in range(len(dpages))]
    imap = [len(ipages) - 1 - i for i in range(len(ipages))]
    files = {
        'OBJECTS.DATA': b''.join(dpages[dmap.index(p)] for p in range(len(dpages))),
        'INDEX.BTR': b''.join(ipages[imap.index(p)] for p in range(len(ipages))),
        'MAPPING1.MAP': mapping(19, [(p + 1) % len(dmap) for p in dmap]) + mapping(19, imap, root=2),
        'MAPPING2.MAP': mapping(20, dmap) + mapping(20, imap, root=1) + b'\x00' * 4,
    }
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--archive', required=True, help='zip to write')
    args = ap.parse_args()
    files = build()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(ROOT + name, date_time=(2024, 1, 5, 9, 15, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[name])
    with open(args.archive, 'wb') as f:
        f.write(buf.getvalue())
    print(f'{args.archive}: {", ".join(f"{n} {len(b):,} bytes" for n, b in sorted(files.items()))}')


if __name__ == '__main__':
    main()
