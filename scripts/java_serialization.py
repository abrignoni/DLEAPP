"""Read Java Object Serialization streams (the format ObjectOutputStream writes).

The stream protocol is Oracle's "Java Object Serialization Specification", chapter 6
(https://docs.oracle.com/javase/8/docs/platform/serialization/spec/protocol.html). A stream
names every class and field before the values, so it reads without the program's classes.

What a class writes in its own writeObject method follows its default fields as an
annotation: block data for primitives and objects in between. Every object keeps those
annotations here, per class in its hierarchy, so callers can read collections. `plain()`
turns the JDK collections and boxes into Python values, following what each JDK 8 class
writes (openjdk/jdk8u at the jdk8u472-b08 tag, jdk/src/share/classes/java/):
  util/HashMap.java lines 1357 to 1365 and 1811 to 1821: default fields, then block data
      holding the bucket count and size, then each key and value.
  util/HashSet.java lines 274 to 288: capacity, load factor and size, then each element.
  util/TreeMap.java lines 2426 to 2438: size, then each key and value.
  util/Hashtable.java lines 1131 to 1158: table length and count, then each key and value.
  util/ArrayList.java lines 757 to 768: the size field, the size again, then each element.
  io/File.java lines 2191 to 2195: the path field, then the separator character.
LinkedHashMap and LinkedHashSet write as their superclass does, so they read the same way.
"""

import struct

_TC_NULL = 0x70
_TC_REFERENCE = 0x71
_TC_CLASSDESC = 0x72
_TC_OBJECT = 0x73
_TC_STRING = 0x74
_TC_ARRAY = 0x75
_TC_CLASS = 0x76
_TC_BLOCKDATA = 0x77
_TC_ENDBLOCKDATA = 0x78
_TC_RESET = 0x79
_TC_BLOCKDATALONG = 0x7A
_TC_EXCEPTION = 0x7B
_TC_LONGSTRING = 0x7C
_TC_PROXYCLASSDESC = 0x7D
_TC_ENUM = 0x7E
_BASE_HANDLE = 0x7E0000
_SC_WRITE_METHOD = 0x01
_SC_SERIALIZABLE = 0x02
_SC_EXTERNALIZABLE = 0x04
_SC_BLOCK_DATA = 0x08

_PRIMITIVES = {'B': ('>b', 1), 'C': ('>H', 2), 'D': ('>d', 8), 'F': ('>f', 4),
               'I': ('>i', 4), 'J': ('>q', 8), 'S': ('>h', 2), 'Z': ('>?', 1)}


class JavaObject:
    """One serialized object: its class name, its fields, and what each class's writeObject wrote."""

    def __init__(self, classname):
        self.classname = classname
        self.fields = {}
        self.annotations = {}  # class name -> list of objects and bytes, in stream order

    def __repr__(self):
        return f'JavaObject({self.classname})'


class JavaEnum:
    """One serialized enum constant."""

    def __init__(self, classname):
        self.classname = classname
        self.name = ''

    def __repr__(self):
        return f'JavaEnum({self.classname}.{self.name})'


class JavaClassDesc:
    """A class descriptor: name, serialVersionUID, flags, fields and superclass."""

    def __init__(self):
        self.name = ''
        self.uid = 0
        self.flags = 0
        self.fields = []
        self.superclass = None


class JavaSerializationError(ValueError):
    """The bytes are not a stream this reader can read."""


class _Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0
        self.handles = []

    def _take(self, size):
        if self.offset + size > len(self.data):
            raise JavaSerializationError(f'stream ends at {len(self.data)}, needed {self.offset + size}')
        value = self.data[self.offset:self.offset + size]
        self.offset += size
        return value

    def _u1(self):
        return self._take(1)[0]

    def _unpack(self, fmt, size):
        return struct.unpack(fmt, self._take(size))[0]

    def _utf(self, long_form=False):
        length = self._unpack('>Q', 8) if long_form else self._unpack('>H', 2)
        return _modified_utf8(self._take(length))

    def _handle(self, obj):
        self.handles.append(obj)
        return obj

    def read_stream(self):
        if self._unpack('>H', 2) != 0xACED:
            raise JavaSerializationError('not a Java serialization stream')
        version = self._unpack('>H', 2)
        if version != 5:
            raise JavaSerializationError(f'unsupported stream version {version}')
        contents = []
        while self.offset < len(self.data):
            contents.append(self._content())
        return contents

    def _content(self):
        marker = self._u1()
        if marker == _TC_NULL:
            return None
        if marker == _TC_REFERENCE:
            return self._reference()
        if marker == _TC_STRING:
            return self._handle(self._utf())
        if marker == _TC_LONGSTRING:
            return self._handle(self._utf(long_form=True))
        if marker in (_TC_CLASSDESC, _TC_PROXYCLASSDESC):
            self.offset -= 1
            return self._classdesc()
        if marker == _TC_CLASS:
            return self._handle(self._classdesc())
        if marker == _TC_OBJECT:
            return self._object()
        if marker == _TC_ARRAY:
            return self._array()
        if marker == _TC_ENUM:
            return self._enum()
        if marker == _TC_BLOCKDATA:
            return bytes(self._take(self._u1()))
        if marker == _TC_BLOCKDATALONG:
            return bytes(self._take(self._unpack('>I', 4)))
        if marker == _TC_RESET:
            self.handles = []
            return self._content()
        raise JavaSerializationError(f'unsupported stream marker {marker:#x} at {self.offset - 1}')

    def _reference(self):
        index = self._unpack('>i', 4) - _BASE_HANDLE
        if not 0 <= index < len(self.handles):
            raise JavaSerializationError(f'reference to unknown handle {index}')
        return self.handles[index]

    def _classdesc(self):
        marker = self._u1()
        if marker == _TC_NULL:
            return None
        if marker == _TC_REFERENCE:
            return self._reference()
        descriptor = JavaClassDesc()
        if marker == _TC_PROXYCLASSDESC:
            self._handle(descriptor)
            for _ in range(self._unpack('>i', 4)):
                self._utf()
            self._annotation()
            descriptor.superclass = self._classdesc()
            return descriptor
        if marker != _TC_CLASSDESC:
            raise JavaSerializationError(f'expected a class descriptor, got {marker:#x}')
        descriptor.name = self._utf()
        descriptor.uid = self._unpack('>q', 8)
        descriptor.flags = self._u1()
        self._handle(descriptor)
        for _ in range(self._unpack('>H', 2)):
            code = chr(self._u1())
            name = self._utf()
            if code in 'L[':
                self._content()  # the field's class name, a string or a reference
            elif code not in _PRIMITIVES:
                raise JavaSerializationError(f'unknown field type {code!r}')
            descriptor.fields.append((code, name))
        self._annotation()
        descriptor.superclass = self._classdesc()
        return descriptor

    def _annotation(self):
        items = []
        while True:
            if self.offset >= len(self.data):
                raise JavaSerializationError('stream ends inside an annotation')
            if self.data[self.offset] == _TC_ENDBLOCKDATA:
                self.offset += 1
                return items
            items.append(self._content())

    def _value(self, code):
        if code in 'L[':
            return self._content()
        fmt, size = _PRIMITIVES[code]
        value = self._unpack(fmt, size)
        return chr(value) if code == 'C' else value

    def _object(self):
        descriptor = self._classdesc()
        obj = JavaObject(descriptor.name if descriptor else '')
        self._handle(obj)
        chain = []
        current = descriptor
        while current:
            chain.append(current)
            current = current.superclass
        for level in reversed(chain):
            if level.flags & _SC_EXTERNALIZABLE:
                if not level.flags & _SC_BLOCK_DATA:
                    raise JavaSerializationError(f'{level.name}: externalizable data without block mode')
                obj.annotations[level.name] = self._annotation()
                continue
            for code, name in level.fields:
                obj.fields[name] = self._value(code)
            if level.flags & _SC_WRITE_METHOD:
                obj.annotations[level.name] = self._annotation()
        return obj

    def _array(self):
        descriptor = self._classdesc()
        values = []
        self._handle(values)
        count = self._unpack('>i', 4)
        code = descriptor.name[1] if descriptor and len(descriptor.name) > 1 else 'L'
        if code == 'B':
            values.extend(self._take(count))
            return values
        for _ in range(count):
            values.append(self._value(code))
        return values

    def _enum(self):
        descriptor = self._classdesc()
        constant = JavaEnum(descriptor.name if descriptor else '')
        self._handle(constant)
        constant.name = self._content()
        return constant


def _modified_utf8(raw):
    """Java's modified UTF-8: NUL is C0 80 and characters above U+FFFF are surrogate pairs."""
    text = bytes(raw).replace(b'\xc0\x80', b'\x00').decode('utf-8', 'surrogatepass')
    return text.encode('utf-16', 'surrogatepass').decode('utf-16', 'replace')


def loads(data):
    """Every top-level content item of a serialization stream, in order."""
    return _Reader(data).read_stream()


def load_first(data):
    """The first top-level object of a stream, the usual shape of one writeObject() call."""
    contents = loads(data)
    if not contents:
        raise JavaSerializationError('empty stream')
    return contents[0]


_MAPS = {'java.util.HashMap', 'java.util.LinkedHashMap', 'java.util.TreeMap', 'java.util.Hashtable'}
_SETS = {'java.util.HashSet', 'java.util.LinkedHashSet'}
_LISTS = {'java.util.ArrayList'}
_BOXES = {'java.lang.Integer', 'java.lang.Long', 'java.lang.Short', 'java.lang.Byte',
          'java.lang.Boolean', 'java.lang.Double', 'java.lang.Float', 'java.lang.Character'}
_EMPTY = {'java.util.Collections$EmptyList': list, 'java.util.Collections$EmptySet': list,
          'java.util.Collections$EmptyMap': list}
_WRAPPERS = ('java.util.Collections$Unmodifiable', 'java.util.Collections$Synchronized',
             'java.util.Collections$Checked', 'java.util.Collections$Singleton')


def _objects(obj, level):
    """The objects (not block data) a class's writeObject wrote, in order."""
    return [item for item in obj.annotations.get(level, []) if not isinstance(item, bytes)]


def _block_ints(obj, level, count):
    """The first `count` big-endian ints of the block data a class wrote ahead of its objects."""
    for item in obj.annotations.get(level, []):
        if isinstance(item, bytes) and len(item) >= 4 * count:
            return struct.unpack_from(f'>{count}i', item)
    return None


def map_items(obj):
    """(key, value) pairs of a serialized JDK map, as stored, or None when `obj` is not one."""
    if not isinstance(obj, JavaObject):
        return None
    for level in (obj.classname, 'java.util.HashMap', 'java.util.TreeMap', 'java.util.Hashtable'):
        if level in obj.annotations and (obj.classname in _MAPS or level in _MAPS):
            items = _objects(obj, level)
            if len(items) % 2:
                raise JavaSerializationError(f'{obj.classname}: odd number of key and value objects')
            return list(zip(items[0::2], items[1::2]))
    return None


def collection_items(obj):
    """Members of a serialized JDK list or set, as stored, or None when `obj` is not one."""
    if not isinstance(obj, JavaObject):
        return None
    for level in (obj.classname, 'java.util.HashSet', 'java.util.ArrayList'):
        if level in obj.annotations and (obj.classname in _SETS | _LISTS or level in _SETS | _LISTS):
            return _objects(obj, level)
    return None


def plain(value):
    """A Python value for a decoded JDK box, string, enum, file, list, set or map.

    Maps become lists of (key, value) pairs, since Java keys need not be hashable here.
    Objects of other classes are returned unchanged.
    """
    if isinstance(value, JavaEnum):
        return value.name
    if isinstance(value, list):
        return [plain(item) for item in value]
    if not isinstance(value, JavaObject):
        return value
    name = value.classname
    if name in _BOXES:
        return value.fields.get('value')
    if name == 'java.io.File':
        return value.fields.get('path')
    if name in _EMPTY:
        return _EMPTY[name]()
    if name.startswith(_WRAPPERS):
        for field in ('c', 'list', 's', 'm', 'element', 'k', 'v'):
            if field in value.fields:
                inner = plain(value.fields[field])
                return inner if field not in ('element', 'k') else [inner]
    pairs = map_items(value)
    if pairs is not None:
        return [(plain(k), plain(v)) for k, v in pairs]
    members = collection_items(value)
    if members is not None:
        return [plain(item) for item in members]
    return value
