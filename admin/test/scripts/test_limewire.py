"""Pin scripts/java_serialization.py and the LimeWire readers.

admin/test/fixtures/java_serialization/oracle.ser was written by the JDK's own ObjectOutputStream (Temurin
8u472) from KdSerialOracle.java beside it, so the expected values below are what Java put in. The LimeWire
reader tests build object trees in the shapes LimeWire's classes write (wiregit/wirecode 2b22c50): the
UrnSetKey and URN writeObject methods, LibraryFileData's map and the download mementos.
"""
import datetime
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import java_serialization as js
from scripts.artifacts.limewire import (_settings_folder, java_properties, read_downloads, read_library,
                                        read_urn_cache, read_xml_cache)

ORACLE = REPO_ROOT / 'admin' / 'test' / 'fixtures' / 'java_serialization' / 'oracle.ser'
UTC = datetime.timezone.utc


def _obj(classname, fields=None, annotations=None):
    obj = js.JavaObject(classname)
    obj.fields.update(fields or {})
    obj.annotations.update(annotations or {})
    return obj


def _hashmap(pairs):
    items = [b'\x00\x00\x00\x10' + len(pairs).to_bytes(4, 'big')]
    for key, value in pairs:
        items.extend([key, value])
    return _obj('java.util.HashMap', {'loadFactor': 0.75, 'threshold': 12}, {'java.util.HashMap': items})


def _list(values):
    return _obj('java.util.ArrayList', {'size': len(values)},
                {'java.util.ArrayList': [len(values).to_bytes(4, 'big')] + list(values)})


def _integer(value):
    return _obj('java.lang.Integer', {'value': value})


def _urn(text):
    data = text.encode()
    return _obj('com.limegroup.gnutella.URN', {},
                {'com.limegroup.gnutella.URN': [len(data).to_bytes(2, 'big') + data, js.JavaEnum('Type')]})


class OracleStreamTest(unittest.TestCase):
    def setUp(self):
        self.root = js.load_first(ORACLE.read_bytes())

    def test_root_map_decodes_like_java_wrote_it(self):
        values = dict(js.plain(self.root))
        self.assertEqual(values['VERSION'], 'THREE')
        self.assertEqual(sorted(values['FILES']), [('C:\\kd\\a.txt', [0, 2]), ('C:\\kd\\b.txt', [])])
        self.assertEqual(values['NAMES'], [(2, 'kd-list')])
        self.assertEqual(values['SET'], ['urn:sha1:AAAA'])
        self.assertEqual(values['LONG'], 1288051200000)
        self.assertEqual(values['UNMOD'], ['x', 'y'])

    def test_custom_write_object_keeps_its_annotation(self):
        holder = dict(js.plain(self.root))['HOLDER']
        self.assertEqual((holder.fields['count'], holder.fields['when'], holder.fields['label']),
                         (7, 1288051200000, 'kd-holder'))
        self.assertEqual(js.plain(holder.fields['file']), 'C:\\kd\\a.txt')
        self.assertEqual(holder.annotations['KdSerialOracle$Holder'], [b'\x00\x00\x00*', 'kd-extra'])

    def test_bad_streams_are_refused(self):
        with self.assertRaises(js.JavaSerializationError):
            js.loads(b'not a stream')
        with self.assertRaises(js.JavaSerializationError):
            js.loads(ORACLE.read_bytes()[:200])


class LimeWireReadersTest(unittest.TestCase):
    def test_library_map(self):
        library = _hashmap([
            ('FILE_DATA', _hashmap([('C:\\a.mp3', _list([_integer(0)])), ('C:\\b.wav', _list([_integer(1)]))])),
            ('COLLECTION_NAMES', _obj('java.util.TreeMap', {}, {'java.util.TreeMap': [b'\x00\x00\x00\x01',
                                                                                     _integer(1), 'Untitled']})),
            ('SAFE_URNS', _obj('java.util.HashSet', {}, {'java.util.HashSet': [b'\x00' * 12, 'urn:sha1:A']})),
            ('CURRENT_VERSION', js.JavaEnum('Version')),
        ])
        files, names, safe = read_library(library)
        self.assertEqual(files, {'C:\\a.mp3': [0], 'C:\\b.wav': [1]})
        self.assertEqual(names, {1: 'Untitled'})
        self.assertEqual(safe, {'urn:sha1:A'})

    def test_urn_cache_key_gives_path_time_and_sha1(self):
        key = _obj('com.limegroup.gnutella.library.UrnCache$UrnSetKey', {},
                   {'com.limegroup.gnutella.library.UrnCache$UrnSetKey':
                    [(1794188342114).to_bytes(8, 'big'), 'C:\\a.mp3']})
        value = _obj('com.limegroup.gnutella.UrnSet$UnmodifiableUrnSet', {'sha1': _urn('urn:sha1:A'),
                                                                          'nms1': None, 'ttroot': None})
        self.assertEqual(read_urn_cache(_hashmap([(key, value)])), {'C:\\a.mp3': (1794188342114, 'urn:sha1:A')})

    def test_xml_cache_reads_attributes_despite_undeclared_prefix(self):
        key = _obj('com.limegroup.gnutella.xml.LimeXMLReplyCollection$FileAndUrn',
                   {'file': _obj('java.io.File', {'path': 'C:\\a.mp3'}), 'urn': _urn('urn:sha1:A')})
        xml = ('<?xml version="1.0"?><audios xsi:noNamespaceSchemaLocation="http://x/audio.xsd">'
               '<audio title="T" artist="A" seconds="6"/></audios>')
        self.assertEqual(read_xml_cache(_hashmap([(key, xml)])), {'C:\\a.mp3': 'title=T; artist=A; seconds=6'})

    def test_download_memento(self):
        date = _obj('java.util.Date', {}, {'java.util.Date': [(1794191534287).to_bytes(8, 'big')]})
        serial = _hashmap([('name', 'w.mp3'), ('sha1Urn', _urn('urn:sha1:W')), ('saveFile', None),
                           ('trackers', _list([])), ('attributes', _hashmap([('limewire.download.startDate', date),
                                                                             ('other', 'x')]))])
        memento = _obj('com.limegroup.gnutella.downloader.serial.LibTorrentBTDownloadMementoImpl',
                       {'serialObjects': serial})
        rows = read_downloads(_list([memento]))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row['type'], row['name'], row['sha1Urn'], row['saveFile'], row['trackers']),
                         ('LibTorrentBT', 'w.mp3', 'urn:sha1:W', '', ''))
        self.assertEqual(row['start'], datetime.datetime(2026, 11, 9, 2, 32, 14, 287000, tzinfo=UTC))
        self.assertEqual(row['other'], 'other=x')

    def test_properties_take_the_later_value_and_unescape(self):
        values = java_properties('#c\nA=1\nDIR=C\\:\\\\x\nA=2\nLONG=a\\\n  b\n')
        self.assertEqual(values, {'A': '2', 'DIR': 'C:\\x', 'LONG': 'ab'})

    def test_settings_folders(self):
        self.assertEqual(_settings_folder('Users/u/AppData/Roaming/LimeWire/library5.dat'),
                         ('Users/u/AppData/Roaming/LimeWire', 'u', 'library5.dat'))
        self.assertEqual(_settings_folder('Documents and Settings/v/Application Data/LimeWire/xml/data/a.sxml3'),
                         ('Documents and Settings/v/Application Data/LimeWire', 'v', 'xml/data/a.sxml3'))
        self.assertEqual(_settings_folder('home/w/.limewire/limewire.props')[1], 'w')
        self.assertIsNone(_settings_folder('Users/u/AppData/Roaming/NotLimeWire/library5.dat'))


if __name__ == '__main__':
    unittest.main()
