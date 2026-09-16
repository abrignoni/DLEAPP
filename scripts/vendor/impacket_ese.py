"""ESE (Extensible Storage Engine / .edb) database reader for DLEAPP.

Adapted from Fortra impacket 0.13.1, tag impacket_0_13_1, commit
c456746d7a0f0bb25e8968a59f25aae1ad519935 (2026-05-15), files impacket/structure.py
and impacket/ese.py. Distributed under the Apache Software License, kept beside
this file as LICENSE-impacket. The two modules are folded into this single
self-contained file and their impacket/six/logging dependencies are inlined
below, so nothing outside the Python standard library is required. The import
lines were removed and the shims below added. One behavior change is made on top
of that: a tagged column stored with ESE 7-bit compression, which upstream
returns as None with an "Unsupported tag column" log, is decoded to its string
here (see _ese_decompress_value and the compressed-tag branch); other
compression schemes still return None. The change is additive, so a column that
was never compressed decodes exactly as before.

Not tracked in scripts/vendor/vendored.json, because it is adapted rather than a
verbatim copy: the check_vendored gate requires the body to match upstream byte
for byte. To update, re-adapt from the impacket source at the tag above.
"""

import logging
import re
from struct import pack, unpack, calcsize
from collections import OrderedDict
from binascii import hexlify

LOG = logging.getLogger('dleapp.impacket_ese')
PY3 = True


def b(value):
    """six.b / six.ensure_binary(latin-1): encode str to bytes, pass bytes through."""
    if isinstance(value, str):
        return value.encode('latin-1')
    return bytes(value) if isinstance(value, bytearray) else value


class _Six:
    """Minimal stand-in for the parts of the six module the bodies below use."""
    PY3 = True
    PY2 = False

    @staticmethod
    def ensure_binary(s, encoding='utf-8', errors='strict'):
        if isinstance(s, (bytes, bytearray)):
            return bytes(s)
        if isinstance(s, str):
            return s.encode(encoding, errors)
        raise TypeError("not expecting type '%s'" % type(s))

    @staticmethod
    def ensure_str(s, encoding='utf-8', errors='strict'):
        if isinstance(s, bytes):
            return s.decode(encoding, errors)
        return s


six = _Six()


def _ese_decompress_value(value):
    """Decode an ESE compressed tagged-column value.

    ESE stores some tagged columns (for example the Windows Search property
    store's paths and names) compressed, with a one-byte header. A header of
    0x10-0x17 marks 7-bit compression: the bytes after it pack one 7-bit
    character each, least-significant-bit first. That case is decoded here and
    returned as a str. Any other scheme (an Xpress-compressed value, header
    0x18 and up) is not decoded and returns None rather than a guess.
    """
    if not value:
        return None
    header = value[0]
    if 0x10 <= header <= 0x17:
        chars = []
        acc = 0
        nbits = 0
        for byte in value[1:]:
            acc |= byte << nbits
            nbits += 8
            while nbits >= 7:
                chars.append(acc & 0x7F)
                acc >>= 7
                nbits -= 7
        return "".join(chr(c) for c in chars).rstrip("\x00")
    return None



# --- adapted from impacket/structure.py ---
# Impacket - Collection of Python classes for working with network protocols.
#
# Copyright Fortra, LLC and its affiliated companies 
#
# All rights reserved.
#
# This software is provided under a slightly modified version
# of the Apache Software License. See the accompanying LICENSE file
# for more information.
#


import re
from struct import pack, unpack, calcsize

from binascii import hexlify


class Structure:
    """ sublcasses can define commonHdr and/or structure.
        each of them is an tuple of either two: (fieldName, format) or three: (fieldName, ':', class) fields.
        [it can't be a dictionary, because order is important]
        
        where format specifies how the data in the field will be converted to/from bytes (string)
        class is the class to use when unpacking ':' fields.

        each field can only contain one value (or an array of values for *)
           i.e. struct.pack('Hl',1,2) is valid, but format specifier 'Hl' is not (you must use 2 dfferent fields)

        format specifiers:
          specifiers from module pack can be used with the same format 
          see struct.__doc__ (pack/unpack is finally called)
            x       [padding byte]
            c       [character]
            b       [signed byte]
            B       [unsigned byte]
            h       [signed short]
            H       [unsigned short]
            l       [signed long]
            L       [unsigned long]
            i       [signed integer]
            I       [unsigned integer]
            q       [signed long long (quad)]
            Q       [unsigned long long (quad)]
            s       [string (array of chars), must be preceded with length in format specifier, padded with zeros]
            p       [pascal string (includes byte count), must be preceded with length in format specifier, padded with zeros]
            f       [float]
            d       [double]
            =       [native byte ordering, size and alignment]
            @       [native byte ordering, standard size and alignment]
            !       [network byte ordering]
            <       [little endian]
            >       [big endian]

          usual printf like specifiers can be used (if started with %) 
          [not recommended, there is no way to unpack this]

            %08x    will output an 8 bytes hex
            %s      will output a string
            %s\\x00  will output a NUL terminated string
            %d%d    will output 2 decimal digits (against the very same specification of Structure)
            ...

          some additional format specifiers:
            :       just copy the bytes from the field into the output string (input may be string, other structure, or anything responding to __str__()) (for unpacking, all what's left is returned)
            z       same as :, but adds a NUL byte at the end (asciiz) (for unpacking the first NUL byte is used as terminator)  [asciiz string]
            u       same as z, but adds two NUL bytes at the end (after padding to an even size with NULs). (same for unpacking) [UTF16-le encoded bytes]
            w       DCE-RPC/NDR string (it's a macro for [  '<L=(len(field)+1)/2','"\\x00\\x00\\x00\\x00','<L=(len(field)+1)/2',':' ]
            ?-field length of field named 'field', formatted as specified with ? ('?' may be '!H' for example). The input value overrides the real length
            ?1*?2   array of elements. Each formatted as '?2', the number of elements in the array is stored as specified by '?1' (?1 is optional, or can also be a constant (number), for unpacking)
            'xxxx   literal xxxx (field's value doesn't change the output. quotes must not be closed or escaped)
            "xxxx   literal xxxx (field's value doesn't change the output. quotes must not be closed or escaped)
            _       will not pack the field. Accepts a third argument, which is an unpack code. See _Test_UnpackCode for an example
            ?=packcode  will evaluate packcode in the context of the structure, and pack the result as specified by ?. Unpacking is made plain
            ?&fieldname "Address of field fieldname".
                        For packing it will simply pack the id() of fieldname. Or use 0 if fieldname doesn't exists.
                        For unpacking, it's used to know weather fieldname has to be unpacked or not, i.e. by adding a & field you turn another field (fieldname) in an optional field.
            
    """
    # REGEX: Positive lookahead to find overlapping NUL-NUL terminators (something like \x00\x00\x00 has 1 overlap)
    NULL_NULL_TERMINATOR_REGEX = re.compile(b'(?=(\x00\x00))')

    commonHdr = ()
    structure = ()
    debug = 0
    # Encoding defaults to latin-1 which already was the de facto encoding for structures and works for most use cases.
    # Now it can be configured to another encoding if needed.
    ENCODING = 'latin-1'   # https://github.com/fortra/impacket/pull/1958

    def __init__(self, data = None, alignment = 0):
        if not hasattr(self, 'alignment'):
            self.alignment = alignment

        self.fields    = {}
        self.rawData   = data

        self.b = lambda x: six.ensure_binary(x, encoding=self.ENCODING)

        if data is not None:
            self.fromString(data)
        else:
            self.data = None

    @classmethod
    def fromFile(self, file):
        answer = self()
        answer.fromString(file.read(len(answer)))
        return answer

    def setAlignment(self, alignment):
        self.alignment = alignment

    def setData(self, data):
        self.data = data

    def packField(self, fieldName, format = None):
        if self.debug:
            print("packField( %s | %s )" % (fieldName, format))

        if format is None:
            format = self.formatForField(fieldName)

        if fieldName in self.fields:
            ans = self.pack(format, self.fields[fieldName], field = fieldName)
        else:
            ans = self.pack(format, None, field = fieldName)

        if self.debug:
            print("\tanswer %r" % ans)

        return ans

    def getData(self):
        if self.data is not None:
            return self.data
        data = bytes()
        for field in self.commonHdr+self.structure:
            try:
                data += self.packField(field[0], field[1])
            except Exception as e:
                if field[0] in self.fields:
                    e.args += ("When packing field '%s | %s | %r' in %s" % (field[0], field[1], self[field[0]], self.__class__),)
                else:
                    e.args += ("When packing field '%s | %s' in %s" % (field[0], field[1], self.__class__),)
                raise
            if self.alignment:
                if len(data) % self.alignment:
                    data += (b'\x00'*self.alignment)[:-(len(data) % self.alignment)]
            
        #if len(data) % self.alignment: data += ('\x00'*self.alignment)[:-(len(data) % self.alignment)]
        return data

    def fromString(self, data):
        self.rawData = data
        for field in self.commonHdr+self.structure:
            if self.debug:
                print("fromString( %s | %s | %r )" % (field[0], field[1], data))
            size = self.calcUnpackSize(field[1], data, field[0])
            if self.debug:
                print("  size = %d" % size)
            dataClassOrCode = b
            if len(field) > 2:
                dataClassOrCode = field[2]
            try:
                self[field[0]] = self.unpack(field[1], data[:size], dataClassOrCode = dataClassOrCode, field = field[0])
            except Exception as e:
                e.args += ("When unpacking field '%s | %s | %r[:%d]'" % (field[0], field[1], data, size),)
                raise

            size = self.calcPackSize(field[1], self[field[0]], field[0])
            if self.alignment and size % self.alignment:
                size += self.alignment - (size % self.alignment)
            data = data[size:]

        return self

    def __setitem__(self, key, value):
        self.fields[key] = value
        self.data = None        # force recompute

    def __getitem__(self, key):
        return self.fields[key]

    def __delitem__(self, key):
        del self.fields[key]

    def __str__(self):
        return str(hexlify(self.getData()).decode("ascii"))

    def __len__(self):
        # XXX: improve
        return len(self.getData())

    def pack(self, format, data, field = None):
        if self.debug:
            print("  pack( %s | %r | %s)" %  (format, data, field))

        if field:
            addressField = self.findAddressFieldFor(field)
            if (addressField is not None) and (data is None):
                return b''

        # void specifier
        if format[:1] == '_':
            return b''

        # quote specifier
        if format[:1] == "'" or format[:1] == '"':
            return self.b(format[1:])

        # code specifier
        two = format.split('=')
        if len(two) >= 2:
            try:
                return self.pack(two[0], data)
            except:
                fields = {'self':self}
                fields.update(self.fields)
                return self.pack(two[0], eval(two[1], {}, fields))

        # address specifier
        two = format.split('&')
        if len(two) == 2:
            try:
                return self.pack(two[0], data)
            except:
                if (two[1] in self.fields) and (self[two[1]] is not None):
                    return self.pack(two[0], id(self[two[1]]) & ((1<<(calcsize(two[0])*8))-1) )
                else:
                    return self.pack(two[0], 0)

        # length specifier
        two = format.split('-')
        if len(two) == 2:
            try:
                return self.pack(two[0],data)
            except:
                return self.pack(two[0], self.calcPackFieldSize(two[1]))

        # array specifier
        two = format.split('*')
        if len(two) == 2:
            answer = bytes()
            for each in data:
                answer += self.pack(two[1], each)
            if two[0]:
                if two[0].isdigit():
                    if int(two[0]) != len(data):
                        raise Exception("Array field has a constant size, and it doesn't match the actual value")
                else:
                    return self.pack(two[0], len(data))+answer
            return answer

        # "printf" string specifier
        if format[:1] == '%':
            # format string like specifier
            return self.b(format % data)

        # asciiz specifier
        if format[:1] == 'z':
            if isinstance(data,bytes):
                return data + self.b('\0')
            return bytes(self.b(data)+self.b('\0'))

        # unicode specifier
        if format[:1] == 'u':
            return bytes(data+self.b('\0\0') + (len(data) & 1 and self.b('\0') or b''))

        # DCE-RPC/NDR string specifier
        if format[:1] == 'w':
            if len(data) == 0:
                data = self.b('\0\0')
            elif len(data) % 2:
                data = self.b(data) + self.b('\0')
            l = pack('<L', len(data)//2)
            return b''.join([l, l, self.b('\0\0\0\0'), data])

        if data is None:
            raise Exception("Trying to pack None")
        
        # literal specifier
        if format[:1] == ':':
            if isinstance(data, Structure):
                return data.getData()
            # If we have an object that can serialize itself, go ahead
            elif hasattr(data, "getData"):
                return data.getData()
            elif isinstance(data, int):
                return bytes(data)
            elif isinstance(data, bytes) is not True:
                return bytes(self.b(data))
            else:
                return data

        if format[-1:] == 's':
            # Let's be sure we send the right type
            if isinstance(data, bytes) or isinstance(data, bytearray):
                return pack(format, data)
            else:
                return pack(format, self.b(data))

        # struct like specifier
        return pack(format, data)

    def unpack(self, format, data, dataClassOrCode = b, field = None):
        if self.debug:
            print("  unpack( %s | %r )" %  (format, data))

        if field:
            addressField = self.findAddressFieldFor(field)
            if addressField is not None:
                if not self[addressField]:
                    return

        # void specifier
        if format[:1] == '_':
            if dataClassOrCode != b:
                fields = {'self':self, 'inputDataLeft':data}
                fields.update(self.fields)
                return eval(dataClassOrCode, {}, fields)
            else:
                return None

        # quote specifier
        if format[:1] == "'" or format[:1] == '"':
            answer = format[1:]
            if self.b(answer) != data:
                raise Exception("Unpacked data doesn't match constant value '%r' should be '%r'" % (data, answer))
            return answer

        # address specifier
        two = format.split('&')
        if len(two) == 2:
            return self.unpack(two[0],data)

        # code specifier
        two = format.split('=')
        if len(two) >= 2:
            return self.unpack(two[0],data)

        # length specifier
        two = format.split('-')
        if len(two) == 2:
            return self.unpack(two[0],data)

        # array specifier
        two = format.split('*')
        if len(two) == 2:
            answer = []
            sofar = 0
            if two[0].isdigit():
                number = int(two[0])
            elif two[0]:
                sofar += self.calcUnpackSize(two[0], data)
                number = self.unpack(two[0], data[:sofar])
            else:
                number = -1

            while number and sofar < len(data):
                nsofar = sofar + self.calcUnpackSize(two[1],data[sofar:])
                answer.append(self.unpack(two[1], data[sofar:nsofar], dataClassOrCode))
                number -= 1
                sofar = nsofar
            return answer

        # "printf" string specifier
        if format[:1] == '%':
            # format string like specifier
            return format % data

        # asciiz specifier
        if format == 'z':
            if data[-1:] != self.b('\x00'):
                raise Exception("%s 'z' field is not NUL terminated: %r" % (field, data))
            if PY3:
                return data[:-1].decode('latin-1')
            else:
                return data[:-1]

        # unicode specifier
        if format == 'u':
            if data[-2:] != self.b('\x00\x00'):
                raise Exception("%s 'u' field is not NUL-NUL terminated: %r" % (field, data))
            return data[:-2] # remove trailing NUL

        # DCE-RPC/NDR string specifier
        if format == 'w':
            l = unpack('<L', data[:4])[0]
            return data[12:12+l*2]

        # literal specifier
        if format == ':':
            if isinstance(data, bytes) and dataClassOrCode is b:
                return data
            return dataClassOrCode(data)

        # struct like specifier
        return unpack(format, data)[0]

    def calcPackSize(self, format, data, field = None):
#        # print "  calcPackSize  %s:%r" %  (format, data)
        if field:
            addressField = self.findAddressFieldFor(field)
            if addressField is not None:
                if not self[addressField]:
                    return 0

        # void specifier
        if format[:1] == '_':
            return 0

        # quote specifier
        if format[:1] == "'" or format[:1] == '"':
            return len(format)-1

        # address specifier
        two = format.split('&')
        if len(two) == 2:
            return self.calcPackSize(two[0], data)

        # code specifier
        two = format.split('=')
        if len(two) >= 2:
            return self.calcPackSize(two[0], data)

        # length specifier
        two = format.split('-')
        if len(two) == 2:
            return self.calcPackSize(two[0], data)

        # array specifier
        two = format.split('*')
        if len(two) == 2:
            answer = 0
            if two[0].isdigit():
                    if int(two[0]) != len(data):
                        raise Exception("Array field has a constant size, and it doesn't match the actual value")
            elif two[0]:
                answer += self.calcPackSize(two[0], len(data))

            for each in data:
                answer += self.calcPackSize(two[1], each)
            return answer

        # "printf" string specifier
        if format[:1] == '%':
            # format string like specifier
            return len(format % data)

        # asciiz specifier
        if format[:1] == 'z':
            return len(data)+1

        # asciiz specifier
        if format[:1] == 'u':
            l = len(data)
            return l + (l & 1 and 3 or 2)

        # DCE-RPC/NDR string specifier
        if format[:1] == 'w':
            l = len(data)
            return 12+l+l % 2

        # literal specifier
        if format[:1] == ':':
            return len(data)

        # struct like specifier
        return calcsize(format)

    def calcUnpackSize(self, format, data, field = None):
        if self.debug:
            print("  calcUnpackSize( %s | %s | %r)" %  (field, format, data))

        # void specifier
        if format[:1] == '_':
            return 0

        addressField = self.findAddressFieldFor(field)
        if addressField is not None:
            if not self[addressField]:
                return 0

        try:
            lengthField = self.findLengthFieldFor(field)
            return int(self[lengthField])
        except Exception:
            pass

        # XXX: Try to match to actual values, raise if no match
        
        # quote specifier
        if format[:1] == "'" or format[:1] == '"':
            return len(format)-1

        # address specifier
        two = format.split('&')
        if len(two) == 2:
            return self.calcUnpackSize(two[0], data)

        # code specifier
        two = format.split('=')
        if len(two) >= 2:
            return self.calcUnpackSize(two[0], data, field)

        # length specifier
        two = format.split('-')
        if len(two) == 2:
            return self.calcUnpackSize(two[0], data)

        # array specifier
        two = format.split('*')
        if len(two) == 2:
            answer = 0
            if two[0]:
                if two[0].isdigit():
                    number = int(two[0])
                else:
                    answer += self.calcUnpackSize(two[0], data)
                    number = self.unpack(two[0], data[:answer])

                while number:
                    number -= 1
                    answer += self.calcUnpackSize(two[1], data[answer:])
            else:
                while answer < len(data):
                    answer += self.calcUnpackSize(two[1], data[answer:])
            return answer

        # "printf" string specifier
        if format[:1] == '%':
            raise Exception("Can't guess the size of a printf like specifier for unpacking")

        # asciiz specifier
        if format[:1] == 'z':
            try:
                return data.index(self.b('\x00'))+1
            except ValueError:
                raise ValueError("Can't find NUL terminator in field '%s'" % (field or 'unknown'))

        # asciiz specifier
        if format[:1] == 'u':
            # Positive lookahead to find overlapping NUL-NUL terminators (something like \x00\x00\x00 has 1 overlap)
            matches = self.NULL_NULL_TERMINATOR_REGEX.finditer(data)
            for a_match in matches:
                if a_match.start() % 2 == 0:    # \x00\x00 at an even index
                    return a_match.start() + 2

            # NUL-NUL terminator not found
            hex_data = str(hexlify(data).decode('ascii'))
            utf16_chunks = [hex_data[i:i + 4] for i in range(0, len(hex_data), 4)]
            raise ValueError("Can't find NUL-NUL terminator in UTF-16le string '%s'" % ' '.join(utf16_chunks))

        # DCE-RPC/NDR string specifier
        if format[:1] == 'w':
            l = unpack('<L', data[:4])[0]
            return 12+l*2

        # literal specifier
        if format[:1] == ':':
            return len(data)

        # struct like specifier
        return calcsize(format)

    def calcPackFieldSize(self, fieldName, format = None):
        if format is None:
            format = self.formatForField(fieldName)

        return self.calcPackSize(format, self[fieldName])

    def formatForField(self, fieldName):
        for field in self.commonHdr+self.structure:
            if field[0] == fieldName:
                return field[1]
        raise Exception("Field %s not found" % fieldName)

    def findAddressFieldFor(self, fieldName):
        descriptor = '&%s' % fieldName
        l = len(descriptor)
        for field in self.commonHdr+self.structure:
            if field[1][-l:] == descriptor:
                return field[0]
        return None
        
    def findLengthFieldFor(self, fieldName):
        descriptor = '-%s' % fieldName
        l = len(descriptor)
        for field in self.commonHdr+self.structure:
            if field[1][-l:] == descriptor:
                return field[0]
        return None
        
    def zeroValue(self, format):
        two = format.split('*')
        if len(two) == 2:
            if two[0].isdigit():
                return (self.zeroValue(two[1]),)*int(two[0])
                        
        if not format.find('*') == -1:
            return ()
        if 's' in format:
            return b''
        if format in ['z',':','u']:
            return b''
        if format == 'w':
            return self.b('\x00\x00')

        return 0

    def clear(self):
        for field in self.commonHdr + self.structure:
            self[field[0]] = self.zeroValue(field[1])

    def dump(self, msg = None, indent = 0):
        if msg is None:
            msg = self.__class__.__name__
        ind = ' '*indent
        print("\n%s" % msg)
        fixedFields = []
        for field in self.commonHdr+self.structure:
            i = field[0] 
            if i in self.fields:
                fixedFields.append(i)
                if isinstance(self[i], Structure):
                    self[i].dump('%s%s:{' % (ind,i), indent = indent + 4)
                    print("%s}" % ind)
                else:
                    print("%s%s: {%r}" % (ind,i,self[i]))
        # Do we have remaining fields not defined in the structures? let's 
        # print them
        remainingFields = list(set(self.fields) - set(fixedFields))
        for i in remainingFields:
            if isinstance(self[i], Structure):
                self[i].dump('%s%s:{' % (ind,i), indent = indent + 4)
                print("%s}" % ind)
            else:
                print("%s%s: {%r}" % (ind,i,self[i]))

def pretty_print(x):
    if chr(x) in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ':
       return chr(x)
    else:
       return u'.'

def hexdump(data, indent = ''):
    if data is None:
        return
    if isinstance(data, int):
        data = str(data).encode('utf-8')
    x=bytearray(data)
    strLen = len(x)
    i = 0
    while i < strLen:
        line = " %s%04x   " % (indent, i)
        for j in range(16):
            if i+j < strLen:
                line += "%02X " % x[i+j]
            else:
                line += u"   "
            if j%16 == 7:
                line += " "
        line += "  "
        line += ''.join(pretty_print(x) for x in x[i:i+16] )
        print (line)
        i += 16

def parse_bitmask(dict, value):
    ret = ''
    
    for i in range(0, 31):
        flag = 1 << i

        if value & flag == 0:
            continue

        if flag in dict:
            ret += '%s | ' % dict[flag]
        else:
            ret += "0x%.8X | " % flag

    if len(ret) == 0:
        return '0'
    else:
        return ret[:-3]

# --- adapted from impacket/ese.py ---
# Impacket - Collection of Python classes for working with network protocols.
#
# Copyright Fortra, LLC and its affiliated companies 
#
# All rights reserved.
#
# This software is provided under a slightly modified version
# of the Apache Software License. See the accompanying LICENSE file
# for more information.
#
# Description:
#   Microsoft Extensive Storage Engine parser, just focused on trying
#   to parse NTDS.dit files (not meant as a full parser, although it might work)
#
# Author:
#   Alberto Solino (@agsolino)
#
# Reference for:
#   Structure
# 
#   Excellent reference done by Joachim Metz
#   - http://forensic-proof.com/wp-content/uploads/2011/07/Extensible-Storage-Engine-ESE-Database-File-EDB-format.pdf
#
# ToDo: 
#   [ ] Parse multi-values properly
#   [ ] Support long values properly
#

from collections import OrderedDict
from struct import unpack
from binascii import hexlify

# Constants

FILE_TYPE_DATABASE       = 0
FILE_TYPE_STREAMING_FILE = 1

# Database state
JET_dbstateJustCreated    = 1
JET_dbstateDirtyShutdown  = 2
JET_dbstateCleanShutdown  = 3
JET_dbstateBeingConverted = 4
JET_dbstateForceDetach    = 5

# Page Flags
FLAGS_ROOT         = 1
FLAGS_LEAF         = 2
FLAGS_PARENT       = 4
FLAGS_EMPTY        = 8
FLAGS_SPACE_TREE   = 0x20
FLAGS_INDEX        = 0x40
FLAGS_LONG_VALUE   = 0x80
FLAGS_NEW_FORMAT   = 0x2000
FLAGS_NEW_CHECKSUM = 0x2000

# On 16 KiB and 32 KiB pages, the raw 16-bit tag state appears to store the total
# tag count in the lower 12 bits. The upper 4 bits seem to represent a reserved tag count.
FIRST_AVAILABLE_PAGE_TAG_MASK = 0x0fff
FIRST_AVAILABLE_PAGE_TAG_RESERVED_SHIFT = 12

# Tag Flags
TAG_UNKNOWN = 0x1
TAG_DEFUNCT = 0x2
TAG_COMMON  = 0x4

# Fixed Page Numbers
DATABASE_PAGE_NUMBER           = 1
CATALOG_PAGE_NUMBER            = 4
CATALOG_BACKUP_PAGE_NUMBER     = 24

# Fixed FatherDataPages
DATABASE_FDP         = 1
CATALOG_FDP          = 2
CATALOG_BACKUP_FDP   = 3

# Catalog Types
CATALOG_TYPE_TABLE        = 1
CATALOG_TYPE_COLUMN       = 2
CATALOG_TYPE_INDEX        = 3
CATALOG_TYPE_LONG_VALUE   = 4
CATALOG_TYPE_CALLBACK     = 5

# Column Types
JET_coltypNil          = 0
JET_coltypBit          = 1
JET_coltypUnsignedByte = 2
JET_coltypShort        = 3
JET_coltypLong         = 4
JET_coltypCurrency     = 5
JET_coltypIEEESingle   = 6
JET_coltypIEEEDouble   = 7
JET_coltypDateTime     = 8
JET_coltypBinary       = 9
JET_coltypText         = 10
JET_coltypLongBinary   = 11
JET_coltypLongText     = 12
JET_coltypSLV          = 13
JET_coltypUnsignedLong = 14
JET_coltypLongLong     = 15
JET_coltypGUID         = 16
JET_coltypUnsignedShort= 17
JET_coltypMax          = 18

ColumnTypeToName = {
    JET_coltypNil          : 'NULL',
    JET_coltypBit          : 'Boolean',
    JET_coltypUnsignedByte : 'Signed byte',
    JET_coltypShort        : 'Signed short',
    JET_coltypLong         : 'Signed long',
    JET_coltypCurrency     : 'Currency',
    JET_coltypIEEESingle   : 'Single precision FP',
    JET_coltypIEEEDouble   : 'Double precision FP',
    JET_coltypDateTime     : 'DateTime',
    JET_coltypBinary       : 'Binary',
    JET_coltypText         : 'Text',
    JET_coltypLongBinary   : 'Long Binary',
    JET_coltypLongText     : 'Long Text',
    JET_coltypSLV          : 'Obsolete',
    JET_coltypUnsignedLong : 'Unsigned long',
    JET_coltypLongLong     : 'Long long',
    JET_coltypGUID         : 'GUID',
    JET_coltypUnsignedShort: 'Unsigned short',
    JET_coltypMax          : 'Max',
}

ColumnTypeSize = {
    JET_coltypNil          : None,
    JET_coltypBit          : (1,'B'),
    JET_coltypUnsignedByte : (1,'B'),
    JET_coltypShort        : (2,'<h'),
    JET_coltypLong         : (4,'<l'),
    JET_coltypCurrency     : (8,'<Q'),
    JET_coltypIEEESingle   : (4,'<f'),
    JET_coltypIEEEDouble   : (8,'<d'),
    JET_coltypDateTime     : (8,'<Q'),
    JET_coltypBinary       : None,
    JET_coltypText         : None, 
    JET_coltypLongBinary   : None,
    JET_coltypLongText     : None,
    JET_coltypSLV          : None,
    JET_coltypUnsignedLong : (4,'<L'),
    JET_coltypLongLong     : (8,'<Q'),
    JET_coltypGUID         : (16,'16s'),
    JET_coltypUnsignedShort: (2,'<H'),
    JET_coltypMax          : None,
}

# Tagged Data Type Flags
TAGGED_DATA_TYPE_VARIABLE_SIZE = 1
TAGGED_DATA_TYPE_COMPRESSED    = 2
TAGGED_DATA_TYPE_STORED        = 4
TAGGED_DATA_TYPE_MULTI_VALUE   = 8
TAGGED_DATA_TYPE_WHO_KNOWS     = 10

# Code pages
CODEPAGE_UNICODE = 1200
CODEPAGE_ASCII   = 20127
CODEPAGE_WESTERN = 1252

StringCodePages = {
    CODEPAGE_UNICODE : 'utf-16le', 
    CODEPAGE_ASCII   : 'ascii',
    CODEPAGE_WESTERN : 'cp1252',
}

# Structures

TABLE_CURSOR = {
    'TableData' : b'',
    'FatherDataPageNumber': 0,
    'CurrentPageData' : b'',
    'CurrentTag' : 0,
}

class ESENT_JET_SIGNATURE(Structure):
    structure = (
        ('Random','<L=0'),
        ('CreationTime','<Q=0'),
        ('NetBiosName','16s=b""'),
    )

class ESENT_DB_HEADER(Structure):
    structure = (
        ('CheckSum','<L=0'),
        ('Signature','"\xef\xcd\xab\x89'),
        ('Version','<L=0'),
        ('FileType','<L=0'),
        ('DBTime','<Q=0'),
        ('DBSignature',':',ESENT_JET_SIGNATURE),
        ('DBState','<L=0'),
        ('ConsistentPosition','<Q=0'),
        ('ConsistentTime','<Q=0'),
        ('AttachTime','<Q=0'),
        ('AttachPosition','<Q=0'),
        ('DetachTime','<Q=0'),
        ('DetachPosition','<Q=0'),
        ('LogSignature',':',ESENT_JET_SIGNATURE),
        ('Unknown','<L=0'),
        ('PreviousBackup','24s=b""'),
        ('PreviousIncBackup','24s=b""'),
        ('CurrentFullBackup','24s=b""'),
        ('ShadowingDisables','<L=0'),
        ('LastObjectID','<L=0'),
        ('WindowsMajorVersion','<L=0'),
        ('WindowsMinorVersion','<L=0'),
        ('WindowsBuildNumber','<L=0'),
        ('WindowsServicePackNumber','<L=0'),
        ('FileFormatRevision','<L=0'),
        ('PageSize','<L=0'),
        ('RepairCount','<L=0'),
        ('RepairTime','<Q=0'),
        ('Unknown2','28s=b""'),
        ('ScrubTime','<Q=0'),
        ('RequiredLog','<Q=0'),
        ('UpgradeExchangeFormat','<L=0'),
        ('UpgradeFreePages','<L=0'),
        ('UpgradeSpaceMapPages','<L=0'),
        ('CurrentShadowBackup','24s=b""'),
        ('CreationFileFormatVersion','<L=0'),
        ('CreationFileFormatRevision','<L=0'),
        ('Unknown3','16s=b""'),
        ('OldRepairCount','<L=0'),
        ('ECCCount','<L=0'),
        ('LastECCTime','<Q=0'),
        ('OldECCFixSuccessCount','<L=0'),
        ('ECCFixErrorCount','<L=0'),
        ('LastECCFixErrorTime','<Q=0'),
        ('OldECCFixErrorCount','<L=0'),
        ('BadCheckSumErrorCount','<L=0'),
        ('LastBadCheckSumTime','<Q=0'),
        ('OldCheckSumErrorCount','<L=0'),
        ('CommittedLog','<L=0'),
        ('PreviousShadowCopy','24s=b""'),
        ('PreviousDifferentialBackup','24s=b""'),
        ('Unknown4','40s=b""'),
        ('NLSMajorVersion','<L=0'),
        ('NLSMinorVersion','<L=0'),
        ('Unknown5','148s=b""'),
        ('UnknownFlags','<L=0'),
    )

class ESENT_PAGE_HEADER(Structure):
    structure_2003_SP0 = (
        ('CheckSum','<L=0'),
        ('PageNumber','<L=0'),
    )
    structure_0x620_0x0b = (
        ('CheckSum','<L=0'),
        ('ECCCheckSum','<L=0'),
    )
    structure_win7 = (
        ('CheckSum','<Q=0'),
    )
    common = (
        ('LastModificationTime','<Q=0'),
        ('PreviousPageNumber','<L=0'),
        ('NextPageNumber','<L=0'),
        ('FatherDataPage','<L=0'),
        ('AvailableDataSize','<H=0'),
        ('AvailableUncommittedDataSize','<H=0'),
        ('FirstAvailableDataOffset','<H=0'),
        ('FirstAvailablePageTag','<H=0'),
        ('PageFlags','<L=0'),
    )
    extended_win7 = (
        ('ExtendedCheckSum1','<Q=0'),
        ('ExtendedCheckSum2','<Q=0'),
        ('ExtendedCheckSum3','<Q=0'),
        ('PageNumber','<Q=0'),
        ('Unknown','<Q=0'),
    )
    def __init__(self, version, revision, pageSize=8192, data=None):
        if (version < 0x620) or (version == 0x620 and revision < 0x0b):
            # For sure the old format
            self.structure = self.structure_2003_SP0 + self.common
        elif version == 0x620 and revision < 0x11:
            # Exchange 2003 SP1 and Windows Vista and later
            self.structure = self.structure_0x620_0x0b + self.common
        else:
            # Windows 7 and later
            self.structure = self.structure_win7 + self.common
            if pageSize > 8192:
                self.structure += self.extended_win7

        Structure.__init__(self,data)

class ESENT_ROOT_HEADER(Structure):
    structure = (
        ('InitialNumberOfPages','<L=0'),
        ('ParentFatherDataPage','<L=0'),
        ('ExtentSpace','<L=0'),
        ('SpaceTreePageNumber','<L=0'),
    )

class ESENT_BRANCH_HEADER(Structure):
    structure = (
        ('CommonPageKey',':'),
    )

class ESENT_BRANCH_ENTRY(Structure):
    common = (
        ('CommonPageKeySize','<H=0'),
    )
    structure = (
        ('LocalPageKeySize','<H=0'),
        ('_LocalPageKey','_-LocalPageKey','self["LocalPageKeySize"]'),
        ('LocalPageKey',':'),
        ('ChildPageNumber','<L=0'),
    )
    def __init__(self, flags, data=None):
        if flags & TAG_COMMON > 0:
            # Include the common header
            self.structure = self.common + self.structure
        Structure.__init__(self,data)

class ESENT_LEAF_HEADER(Structure):
    structure = (
        ('CommonPageKey',':'),
    )

class ESENT_LEAF_ENTRY(Structure):
    common = (
        ('CommonPageKeySize','<H=0'),
    )
    structure = (
        ('LocalPageKeySize','<H=0'),
        ('_LocalPageKey','_-LocalPageKey','self["LocalPageKeySize"]'),
        ('LocalPageKey',':'),
        ('EntryData',':'),
    )
    def __init__(self, flags, data=None):
        if flags & TAG_COMMON > 0:
            # Include the common header
            self.structure = self.common + self.structure
        Structure.__init__(self,data)

class ESENT_SPACE_TREE_HEADER(Structure):
    structure = (
        ('Unknown','<Q=0'),
    )

class ESENT_SPACE_TREE_ENTRY(Structure):
    structure = (
        ('PageKeySize','<H=0'),
        ('LastPageNumber','<L=0'),
        ('NumberOfPages','<L=0'),
    )

class ESENT_INDEX_ENTRY(Structure):
    structure = (
        ('RecordPageKey',':'),
    )

class ESENT_DATA_DEFINITION_HEADER(Structure):
    structure = (
        ('LastFixedSize','<B=0'),
        ('LastVariableDataType','<B=0'),
        ('VariableSizeOffset','<H=0'),
    )

class ESENT_CATALOG_DATA_DEFINITION_ENTRY(Structure):
    fixed = (
        ('FatherDataPageID','<L=0'),
        ('Type','<H=0'),
        ('Identifier','<L=0'),
    )

    column_stuff = (
        ('ColumnType','<L=0'),
        ('SpaceUsage','<L=0'),
        ('ColumnFlags','<L=0'),
        ('CodePage','<L=0'),
    )

    other = (
        ('FatherDataPageNumber','<L=0'),
    )

    table_stuff = (
        ('SpaceUsage','<L=0'),
#        ('TableFlags','<L=0'),
#        ('InitialNumberOfPages','<L=0'),
    )

    index_stuff = (
        ('SpaceUsage','<L=0'),
        ('IndexFlags','<L=0'),
        ('Locale','<L=0'),
    )

    lv_stuff = (
        ('SpaceUsage','<L=0'),
#        ('LVFlags','<L=0'),
#        ('InitialNumberOfPages','<L=0'),
    )
    common = (
#        ('RootFlag','<B=0'),
#        ('RecordOffset','<H=0'),
#        ('LCMapFlags','<L=0'),
#        ('KeyMost','<H=0'),
        ('Trailing',':'),
    )

    def __init__(self,data):
        # Depending on the type of data we'll end up building a different struct
        dataType = unpack('<H', data[4:][:2])[0]
        self.structure = self.fixed

        if dataType == CATALOG_TYPE_TABLE:
            self.structure += self.other + self.table_stuff
        elif dataType == CATALOG_TYPE_COLUMN:
            self.structure += self.column_stuff
        elif dataType == CATALOG_TYPE_INDEX:
            self.structure += self.other + self.index_stuff
        elif dataType == CATALOG_TYPE_LONG_VALUE:
            self.structure += self.other + self.lv_stuff
        elif dataType == CATALOG_TYPE_CALLBACK:
            raise Exception('CallBack types not supported!')
        else:
            LOG.error('Unknown catalog type 0x%x' % dataType)
            self.structure = ()
            Structure.__init__(self,data)

        self.structure += self.common

        Structure.__init__(self,data)


def getUnixTime(t):
    t -= 116444736000000000
    t //= 10000000
    return t

class ESENT_PAGE:
    def __init__(self, db, data=None):
        self.__DBHeader = db
        self.data = data
        self.record = None
        self.tagCount = 0
        self.tagReserved = 1
        self.firstDataTag = 1
        if data is not None:
            self.record = ESENT_PAGE_HEADER(self.__DBHeader['Version'], self.__DBHeader['FileFormatRevision'], self.__DBHeader['PageSize'], data)
            self.tagCount = self.record['FirstAvailablePageTag']
            if self.__DBHeader['Version'] == 0x620 and self.__DBHeader['FileFormatRevision'] >= 0x11 and self.__DBHeader['PageSize'] > 8192:
                self.tagReserved = (self.record['FirstAvailablePageTag'] >> FIRST_AVAILABLE_PAGE_TAG_RESERVED_SHIFT) or 1
                self.tagCount = self.record['FirstAvailablePageTag'] & FIRST_AVAILABLE_PAGE_TAG_MASK
            self.firstDataTag = min(self.tagReserved, self.tagCount)

    def iterDataTagNums(self):
        return range(self.firstDataTag, self.tagCount)

    def printFlags(self):
        flags = self.record['PageFlags']
        if flags & FLAGS_EMPTY:
            print("\tEmpty")
        if flags & FLAGS_INDEX:
            print("\tIndex")
        if flags & FLAGS_LEAF:
            print("\tLeaf")
        else:
            print("\tBranch")
        if flags & FLAGS_LONG_VALUE:
            print("\tLong Value")
        if flags & FLAGS_NEW_CHECKSUM:
            print("\tNew Checksum")
        if flags & FLAGS_NEW_FORMAT:
            print("\tNew Format")
        if flags & FLAGS_PARENT:
            print("\tParent")
        if flags & FLAGS_ROOT:
            print("\tRoot")
        if flags & FLAGS_SPACE_TREE:
            print("\tSpace Tree")

    def dump(self):
        baseOffset = len(self.record)
        self.record.dump()
        tags = self.data[-4*self.tagCount:]

        print("FLAGS: ")
        self.printFlags()

        print()

        for i in range(self.tagCount):
            tag = tags[-4:]
            if self.__DBHeader['Version'] == 0x620 and self.__DBHeader['FileFormatRevision'] > 11 and self.__DBHeader['PageSize'] > 8192:
                valueSize = unpack('<H', tag[:2])[0] & 0x7fff
                valueOffset = unpack('<H',tag[2:])[0] & 0x7fff
                hexdump((self.data[baseOffset+valueOffset:][:6]))
                pageFlags = ord(self.data[baseOffset+valueOffset:][1]) >> 5
                #print "TAG FLAG: 0x%x " % (unpack('<L', self.data[baseOffset+valueOffset:][:4]) ) >> 5
                #print "TAG FLAG: 0x " , ord(self.data[baseOffset+valueOffset:][0])
            else:
                valueSize = unpack('<H', tag[:2])[0] & 0x1fff
                pageFlags = (unpack('<H', tag[2:])[0] & 0xe000) >> 13
                valueOffset = unpack('<H',tag[2:])[0] & 0x1fff
                
            print("TAG %-8d offset:0x%-6x flags:0x%-4x valueSize:0x%x" % (i,valueOffset,pageFlags,valueSize))
            #hexdump(self.getTag(i)[1])
            tags = tags[:-4]

        if self.record['PageFlags'] & FLAGS_ROOT > 0:
            rootHeader = ESENT_ROOT_HEADER(self.getTag(0)[1])
            rootHeader.dump()
        elif self.record['PageFlags'] & FLAGS_LEAF == 0:
            # Branch Header
            flags, data = self.getTag(0)
            branchHeader = ESENT_BRANCH_HEADER(data)
            branchHeader.dump()
        else:
            # Leaf Header
            flags, data = self.getTag(0)
            if self.record['PageFlags'] & FLAGS_SPACE_TREE > 0:
                # Space Tree
                spaceTreeHeader = ESENT_SPACE_TREE_HEADER(data)
                spaceTreeHeader.dump()
            else:
                leafHeader = ESENT_LEAF_HEADER(data)
                leafHeader.dump()

        # Print the leaf/branch tags
        for tagNum in self.iterDataTagNums():
            flags, data = self.getTag(tagNum)
            if self.record['PageFlags'] & FLAGS_LEAF == 0:
                # Branch page
                branchEntry = ESENT_BRANCH_ENTRY(flags, data)
                branchEntry.dump()
            elif self.record['PageFlags'] & FLAGS_LEAF > 0:
                # Leaf page
                if self.record['PageFlags'] & FLAGS_SPACE_TREE > 0:
                    # Space Tree
                    spaceTreeEntry = ESENT_SPACE_TREE_ENTRY(data)
                    #spaceTreeEntry.dump()

                elif self.record['PageFlags'] & FLAGS_INDEX > 0:
                    # Index Entry
                    indexEntry = ESENT_INDEX_ENTRY(data)
                    #indexEntry.dump()
                elif self.record['PageFlags'] & FLAGS_LONG_VALUE > 0:
                    # Long Page Value
                    raise Exception('Long value still not supported')
                else:
                    # Table Value
                    leafEntry = ESENT_LEAF_ENTRY(flags, data)
                    dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(leafEntry['EntryData'])
                    dataDefinitionHeader.dump()
                    catalogEntry = ESENT_CATALOG_DATA_DEFINITION_ENTRY(leafEntry['EntryData'][len(dataDefinitionHeader):])
                    catalogEntry.dump()
                    hexdump(leafEntry['EntryData'])

    def getTag(self, tagNum):
        if self.tagCount <= tagNum:
            raise Exception('Trying to grab an unknown tag 0x%x' % tagNum)

        tags = self.data[-4*self.tagCount:]
        baseOffset = len(self.record)
        for i in range(tagNum):
            tags = tags[:-4]

        tag = tags[-4:]

        if self.__DBHeader['Version'] == 0x620 and self.__DBHeader['FileFormatRevision'] >= 17 and self.__DBHeader['PageSize'] > 8192:
            valueSize = unpack('<H', tag[:2])[0] & 0x7fff
            valueOffset = unpack('<H',tag[2:])[0] & 0x7fff
            tmpData = bytearray(self.data[baseOffset+valueOffset:][:valueSize])
            pageFlags = tmpData[1] >> 5
            tmpData[1] = tmpData[1:2][0] & 0x1f
            tmpData = bytes(tmpData)
            tagData = tmpData
        else:
            valueSize = unpack('<H', tag[:2])[0] & 0x1fff
            pageFlags = (unpack('<H', tag[2:])[0] & 0xe000) >> 13
            valueOffset = unpack('<H',tag[2:])[0] & 0x1fff
            tagData = self.data[baseOffset+valueOffset:][:valueSize]

        #return pageFlags, self.data[baseOffset+valueOffset:][:valueSize]
        return pageFlags, tagData

class ESENT_DB:
    def __init__(self, fileName, pageSize = 8192, isRemote = False):
        self.__fileName = fileName
        self.__pageSize = pageSize
        self.__DB = None
        self.__DBHeader = None
        self.__totalPages = None
        self.__tables = OrderedDict()
        self.__currentTable = None
        self.__isRemote = isRemote
        self.mountDB()

    def mountDB(self):
        LOG.debug("Mounting DB...")
        if self.__isRemote is True:
            self.__DB = self.__fileName
            self.__DB.open()
        else:
            self.__DB = open(self.__fileName,"rb")
        mainHeader = self.getPage(-1)
        self.__DBHeader = ESENT_DB_HEADER(mainHeader)
        self.__pageSize = self.__DBHeader['PageSize']
        self.__DB.seek(0,2)
        self.__totalPages = (self.__DB.tell() // self.__pageSize) -2
        LOG.debug("Database Version:0x%x, Revision:0x%x"% (self.__DBHeader['Version'], self.__DBHeader['FileFormatRevision']))
        LOG.debug("Page Size: %d" % self.__pageSize)
        LOG.debug("Total Pages in file: %d" % self.__totalPages)
        self.parseCatalog(CATALOG_PAGE_NUMBER)

    def printCatalog(self):
        indent = '    '

        print("Database version: 0x%x, 0x%x" % (self.__DBHeader['Version'], self.__DBHeader['FileFormatRevision'] ))
        print("Page size: %d " % self.__pageSize)
        print("Number of pages: %d" % self.__totalPages)
        print() 
        print("Catalog for %s" % self.__fileName)
        for table in list(self.__tables.keys()):
            print("[%s]" % table.decode('utf8'))
            print("%sColumns " % indent)
            for column in list(self.__tables[table]['Columns'].keys()):
                record = self.__tables[table]['Columns'][column]['Record']
                print("%s%-5d%-30s%s" % (indent*2, record['Identifier'], column.decode('utf-8'),ColumnTypeToName[record['ColumnType']]))
            print("%sIndexes"% indent)
            for index in list(self.__tables[table]['Indexes'].keys()):
                print("%s%s" % (indent*2, index.decode('utf-8')))
            print("")

    def __addItem(self, entry):
        dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])
        catalogEntry = ESENT_CATALOG_DATA_DEFINITION_ENTRY(entry['EntryData'][len(dataDefinitionHeader):])
        itemName = self.__parseItemName(entry)

        if catalogEntry['Type'] == CATALOG_TYPE_TABLE:
            self.__tables[itemName] = OrderedDict()
            self.__tables[itemName]['TableEntry'] = entry
            self.__tables[itemName]['Columns']    = OrderedDict()
            self.__tables[itemName]['Indexes']    = OrderedDict()
            self.__tables[itemName]['LongValues'] = OrderedDict()
            self.__currentTable = itemName
        elif catalogEntry['Type'] == CATALOG_TYPE_COLUMN:
            self.__tables[self.__currentTable]['Columns'][itemName] = entry
            self.__tables[self.__currentTable]['Columns'][itemName]['Header'] = dataDefinitionHeader
            self.__tables[self.__currentTable]['Columns'][itemName]['Record'] = catalogEntry
        elif catalogEntry['Type'] == CATALOG_TYPE_INDEX:
            self.__tables[self.__currentTable]['Indexes'][itemName] = entry
        elif catalogEntry['Type'] == CATALOG_TYPE_LONG_VALUE:
            self.__addLongValue(entry)
        else:
            raise Exception('Unknown type 0x%x' % catalogEntry['Type'])

    def __parseItemName(self,entry):
        dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])

        if dataDefinitionHeader['LastVariableDataType'] > 127:
            numEntries =  dataDefinitionHeader['LastVariableDataType'] - 127
        else:
            numEntries =  dataDefinitionHeader['LastVariableDataType']

        itemLen = unpack('<H',entry['EntryData'][dataDefinitionHeader['VariableSizeOffset']:][:2])[0]
        itemName = entry['EntryData'][dataDefinitionHeader['VariableSizeOffset']:][2*numEntries:][:itemLen]
        return itemName

    def __addLongValue(self, entry):
        dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])
        lvLen = unpack('<H',entry['EntryData'][dataDefinitionHeader['VariableSizeOffset']:][:2])[0]
        lvName = entry['EntryData'][dataDefinitionHeader['VariableSizeOffset']:][7:][:lvLen]
        self.__tables[self.__currentTable]['LongValues'][lvName] = entry

    def parsePage(self, page):
        # Print the leaf/branch tags
        for tagNum in page.iterDataTagNums():
            flags, data = page.getTag(tagNum)
            if page.record['PageFlags'] & FLAGS_LEAF > 0:
                # Leaf page
                if page.record['PageFlags'] & FLAGS_SPACE_TREE > 0:
                    pass
                elif page.record['PageFlags'] & FLAGS_INDEX > 0:
                    pass
                elif page.record['PageFlags'] & FLAGS_LONG_VALUE > 0:
                    pass
                else:
                    # Table Value
                    leafEntry = ESENT_LEAF_ENTRY(flags, data)
                    self.__addItem(leafEntry)

    def parseCatalog(self, pageNum):
        # Parse all the pages starting at pageNum and commit table data
        page = self.getPage(pageNum)
        self.parsePage(page)

        for i in page.iterDataTagNums():
            flags, data = page.getTag(i)
            if page.record['PageFlags'] & FLAGS_LEAF == 0:
                # Branch page
                branchEntry = ESENT_BRANCH_ENTRY(flags, data)
                self.parseCatalog(branchEntry['ChildPageNumber'])


    def readHeader(self):
        LOG.debug("Reading Boot Sector for %s" % self.__volumeName)

    def getPage(self, pageNum):
        LOG.debug("Trying to fetch page %d (0x%x)" % (pageNum, (pageNum+1)*self.__pageSize))
        self.__DB.seek((pageNum+1)*self.__pageSize, 0)
        data = self.__DB.read(self.__pageSize)
        while len(data) < self.__pageSize:
            remaining = self.__pageSize - len(data)
            data += self.__DB.read(remaining)
        # Special case for the first page
        if pageNum <= 0:
            return data
        else:
            return ESENT_PAGE(self.__DBHeader, data)

    def close(self):
        self.__DB.close()

    def openTable(self, tableName):
        # Returns a cursos for later use

        if isinstance(tableName, bytes) is not True:
            tableName = b(tableName)

        if tableName in self.__tables:
            entry = self.__tables[tableName]['TableEntry']
            dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(entry['EntryData'])
            catalogEntry = ESENT_CATALOG_DATA_DEFINITION_ENTRY(entry['EntryData'][len(dataDefinitionHeader):])
            
            # Let's position the cursor at the leaf levels for fast reading
            pageNum = catalogEntry['FatherDataPageNumber']
            done = False
            while done is False:
                page = self.getPage(pageNum)
                if page.tagCount <= page.firstDataTag:
                    # There are no records
                    done = True
                for i in page.iterDataTagNums():
                    flags, data = page.getTag(i)
                    if page.record['PageFlags'] & FLAGS_LEAF == 0:
                        # Branch page, move on to the next page
                        branchEntry = ESENT_BRANCH_ENTRY(flags, data)
                        pageNum = branchEntry['ChildPageNumber']
                        break
                    else:
                        done = True
                        break
                
            cursor = TABLE_CURSOR
            cursor['TableData'] = self.__tables[tableName]
            cursor['FatherDataPageNumber'] = catalogEntry['FatherDataPageNumber']
            cursor['CurrentPageData'] = page
            cursor['CurrentTag']  = page.firstDataTag - 1
            return cursor
        else:
            return None

    def __getNextTag(self, cursor):
        page = cursor['CurrentPageData']

        if cursor['CurrentTag'] >= page.tagCount:
            # No more data in this page, chau
            return None

        flags, data = page.getTag(cursor['CurrentTag'])
        if page.record['PageFlags'] & FLAGS_LEAF > 0:
            # Leaf page
            if page.record['PageFlags'] & FLAGS_SPACE_TREE > 0:
                raise Exception('FLAGS_SPACE_TREE > 0')
            elif page.record['PageFlags'] & FLAGS_INDEX > 0:
                raise Exception('FLAGS_INDEX > 0')
            elif page.record['PageFlags'] & FLAGS_LONG_VALUE > 0:
                raise Exception('FLAGS_LONG_VALUE > 0')
            else:
                # Table Value
                leafEntry = ESENT_LEAF_ENTRY(flags, data)
                return leafEntry

        return None

    def getNextRow(self, cursor, filter_tables = None):
        cursor['CurrentTag'] += 1

        tag = self.__getNextTag(cursor)
        #hexdump(tag)

        if tag is None:
            # No more tags in this page, search for the next one on the right
            page = cursor['CurrentPageData']
            if page.record['NextPageNumber'] == 0:
                # No more pages, chau
                return None
            else:
                cursor['CurrentPageData'] = self.getPage(page.record['NextPageNumber'])
                cursor['CurrentTag'] = cursor['CurrentPageData'].firstDataTag - 1
                return self.getNextRow(cursor, filter_tables = filter_tables)
        else:
            return self.__tagToRecord(cursor, tag['EntryData'], filter_tables = filter_tables)

    def __tagToRecord(self, cursor, tag, filter_tables = None):
        # So my brain doesn't forget, the data record is composed of:
        # Header
        # Fixed Size Data (ID < 127)
        #     The easiest to parse. Their size is fixed in the record. You can get its size
        #     from the Column Record, field SpaceUsage
        # Variable Size Data (127 < ID < 255)
        #     At VariableSizeOffset you get an array of two bytes per variable entry, pointing
        #     to the length of the value. Values start at:
        #                numEntries = LastVariableDataType - 127
        #                VariableSizeOffset + numEntries * 2 (bytes)
        # Tagged Data ( > 255 )
        #     After the Variable Size Value, there's more data for the tagged values.
        #     Right at the beginning there's another array (taggedItems), pointing to the
        #     values, size.
        #
        # The interesting thing about this DB records is there's no need for all the columns to be there, hence
        # saving space. That's why I got over all the columns, and if I find data (of any type), i assign it. If 
        # not, the column's empty.
        #
        # There are a lot of caveats in the code, so take your time to explore it. 
        #
        # ToDo: Better complete this description
        #

        record = OrderedDict()
        taggedItems = OrderedDict()
        taggedItemsParsed = False

        dataDefinitionHeader = ESENT_DATA_DEFINITION_HEADER(tag)
        #dataDefinitionHeader.dump()
        variableDataBytesProcessed = (dataDefinitionHeader['LastVariableDataType'] - 127) * 2
        prevItemLen = 0
        tagLen = len(tag)
        fixedSizeOffset = len(dataDefinitionHeader)
        variableSizeOffset = dataDefinitionHeader['VariableSizeOffset'] 
 
        columns = cursor['TableData']['Columns'] 
        
        for column in list(columns.keys()):
            if filter_tables is not None:
                if column not in filter_tables:
                    continue
            columnRecord = columns[column]['Record']
            #columnRecord.dump()
            if columnRecord['Identifier'] <= dataDefinitionHeader['LastFixedSize']:
                # Fixed Size column data type, still available data
                record[column] = tag[fixedSizeOffset:][:columnRecord['SpaceUsage']]
                fixedSizeOffset += columnRecord['SpaceUsage']

            elif 127 < columnRecord['Identifier'] <= dataDefinitionHeader['LastVariableDataType']:
                # Variable data type
                index = columnRecord['Identifier'] - 127 - 1
                itemLen = unpack('<H',tag[variableSizeOffset+index*2:][:2])[0]

                if itemLen & 0x8000:
                    # Empty item
                    itemLen = prevItemLen
                    record[column] = None
                else:
                    itemValue = tag[variableSizeOffset+variableDataBytesProcessed:][:itemLen-prevItemLen]
                    record[column] = itemValue

                #if columnRecord['Identifier'] <= dataDefinitionHeader['LastVariableDataType']:
                variableDataBytesProcessed +=itemLen-prevItemLen

                prevItemLen = itemLen

            elif columnRecord['Identifier'] > 255:
                # Have we parsed the tagged items already?
                if taggedItemsParsed is False and (variableDataBytesProcessed+variableSizeOffset) < tagLen:
                    index = variableDataBytesProcessed+variableSizeOffset
                    #hexdump(tag[index:])
                    endOfVS = self.__pageSize
                    firstOffsetTag = (unpack('<H', tag[index+2:][:2])[0] & 0x3fff) + variableDataBytesProcessed+variableSizeOffset
                    while True:
                        taggedIdentifier = unpack('<H', tag[index:][:2])[0]
                        index += 2
                        taggedOffset = (unpack('<H', tag[index:][:2])[0] & 0x3fff) 
                        # As of Windows 7 and later ( version 0x620 revision 0x11) the 
                        # tagged data type flags are always present
                        if self.__DBHeader['Version'] == 0x620 and self.__DBHeader['FileFormatRevision'] >= 17 and self.__DBHeader['PageSize'] > 8192: 
                            flagsPresent = 1
                        else:
                            flagsPresent = (unpack('<H', tag[index:][:2])[0] & 0x4000)
                        index += 2
                        if taggedOffset < endOfVS:
                            endOfVS = taggedOffset
                        taggedItems[taggedIdentifier] = (taggedOffset, tagLen, flagsPresent)
                        #print "ID: %d, Offset:%d, firstOffset:%d, index:%d, flag: 0x%x" % (taggedIdentifier, taggedOffset,firstOffsetTag,index, flagsPresent)
                        if index >= firstOffsetTag:
                            # We reached the end of the variable size array
                            break
                
                    # Calculate length of variable items
                    # Ugly.. should be redone
                    prevKey = list(taggedItems.keys())[0]
                    for i in range(1,len(taggedItems)):
                        offset0, length, flags = taggedItems[prevKey]
                        offset, _, _ = list(taggedItems.items())[i][1]
                        taggedItems[prevKey] = (offset0, offset-offset0, flags)
                        #print "ID: %d, Offset: %d, Len: %d, flags: %d" % (prevKey, offset0, offset-offset0, flags)
                        prevKey = list(taggedItems.keys())[i]
                    taggedItemsParsed = True
 
                # Tagged data type
                if columnRecord['Identifier'] in taggedItems:
                    offsetItem = variableDataBytesProcessed + variableSizeOffset + taggedItems[columnRecord['Identifier']][0] 
                    itemSize = taggedItems[columnRecord['Identifier']][1]
                    # If item have flags, we should skip them
                    if taggedItems[columnRecord['Identifier']][2] > 0:
                        itemFlag = ord(tag[offsetItem:offsetItem+1])
                        offsetItem += 1
                        itemSize -= 1
                    else:
                        itemFlag = 0

                    #print "ID: %d, itemFlag: 0x%x" %( columnRecord['Identifier'], itemFlag)
                    if itemFlag & (TAGGED_DATA_TYPE_COMPRESSED ):
                        record[column] = _ese_decompress_value(tag[offsetItem:][:itemSize])
                    elif itemFlag & TAGGED_DATA_TYPE_MULTI_VALUE:
                        # ToDo: Parse multi-values properly
                        LOG.debug('Multivalue detected in column %s, returning raw results' % (column))
                        record[column] = (hexlify(tag[offsetItem:][:itemSize]),)
                    else:
                        record[column] = tag[offsetItem:][:itemSize]

                else:
                    record[column] = None
            else:
                record[column] = None

            # If we understand the data type, we unpack it and cast it accordingly
            # otherwise, we just encode it in hex
            if isinstance(record[column], str):
                # Already decoded (a 7-bit-decompressed tagged column); leave as is.
                pass
            elif type(record[column]) is tuple:
                # A multi value data, we won't decode it, just leave it this way
                record[column] = record[column][0]
            elif columnRecord['ColumnType'] == JET_coltypText or columnRecord['ColumnType'] == JET_coltypLongText: 
                # Let's handle strings
                if record[column] is not None:
                    if columnRecord['CodePage'] not in StringCodePages:
                        raise Exception('Unknown codepage 0x%x'% columnRecord['CodePage'])
                    stringDecoder = StringCodePages[columnRecord['CodePage']]

                    try:
                        record[column] = record[column].decode(stringDecoder)
                    except Exception:
                        LOG.debug("Exception:", exc_info=True)
                        LOG.debug('Fixing Record[%r][%d]: %r' % (column, columnRecord['ColumnType'], record[column]))
                        record[column] = record[column].decode(stringDecoder, "replace")
                        pass
            else:
                unpackData = ColumnTypeSize[columnRecord['ColumnType']]
                if record[column] is not None:
                    if unpackData is None:
                        record[column] = hexlify(record[column])
                    else:
                        unpackStr = unpackData[1]
                        record[column] = unpack(unpackStr, record[column])[0]

        return record
