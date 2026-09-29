"""Pin the Belkin WeMo device description and manufacture data artifacts
(scripts/artifacts/belkinWemo.py: belkinWemoDevice and belkinWemoManufactureData).

Every file here is made up. setup.xml follows the shape a WeMo serves at /setup.xml, as
recorded in pywemo's test data (pywemo 6dea7394, tests/vcr/tests.ouimeaux_device.test_switch):
a root element in the urn:Belkin:device-1-0 namespace holding a device element.
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import belkinWemo as bw
# pylint: enable=wrong-import-position


class FileInfo:
    def __init__(self, modified):
        self.modification_date = modified


class Seeker:
    def __init__(self):
        self.file_infos = {}


class FakeContext:
    def __init__(self, paths, root, seeker):
        self.paths, self.root, self.seeker = paths, root, seeker

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, '/')

    def get_seeker(self):
        return self.seeker


def setup_xml(serial, icon_url='/icon.jpg', namespace='urn:Belkin:device-1-0', bom=False):
    body = (f'<?xml version="1.0"?>\n<root xmlns="{namespace}">\n<specVersion><major>1</major><minor>0</minor>'
            f'</specVersion>\n<device>\n<deviceType>urn:Belkin:device:example:1</deviceType>\n'
            f'<friendlyName>Example Plug</friendlyName>\n<manufacturer>Example Maker</manufacturer>\n'
            f'<modelName>Example</modelName>\n<modelNumber>1.0</modelNumber>\n'
            f'<modelDescription>Example description</modelDescription>\n<hwVersion>v9</hwVersion>\n'
            f'<serialNumber>{serial}</serialNumber>\n<UDN>uuid:Example-1_0-{serial}</UDN>\n'
            f'<UPC>000000000</UPC>\n<macAddress>0200000000AA</macAddress>\n'
            f'<firmwareVersion>Example_FW_1.0</firmwareVersion>\n<iconVersion>0|49153</iconVersion>\n'
            f'<binaryState>1</binaryState>\n<iconList><icon><mimetype>jpg</mimetype><width>100</width>'
            f'<height>100</height><depth>100</depth><url>{icon_url}</url></icon></iconList>\n'
            f'<extraGroup>text<sub>1</sub></extraGroup>\n<serviceList><service><serviceType>urn:Belkin:service:basicevent:1</serviceType></service>'
            f'</serviceList>\n<presentationURL>/pluginpres.html</presentationURL>\n</device>\n</root>\n')
    return (b'\xef\xbb\xbf' if bom else b'') + body.encode()


PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32


class WemoSettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)
        self.seeker = Seeker()
        self.paths = []
        self.logged = []
        self.media = []
        for name, value in (('logfunc', self.logged.append), ('check_in_media', self.fake_media)):
            patcher = mock.patch.object(bw, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_media(self, path, name=''):
        self.media.append((os.path.relpath(path, self.root).replace(os.sep, '/'), name))
        return f'media-{len(self.media)}'

    def add(self, relative, data, modified=None):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as handle:
            handle.write(data)
        self.paths.append(path)
        if modified is not None:
            self.seeker.file_infos[path] = FileInfo(modified)
        return path

    def run_artifact(self, func):
        return func.__wrapped__(FakeContext(self.paths, self.root, self.seeker))

    def test_device_description_row_and_icon(self):
        setup = self.add('lba900/setup.xml', setup_xml('000EXAMPLE001', bom=True), 1500000000)
        icon = self.add('lba900/icon.jpg', PNG, 1500000001)
        self.add('lba800/icon.jpg', PNG)                     # another folder's icon, not this file's
        headers, rows, source = self.run_artifact(bw.belkinWemoDevice)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(datetime.fromtimestamp(1500000000, timezone.utc), 'Example Plug', 'Example', '1.0',
                                 'Example description', '000EXAMPLE001', '0200000000AA',
                                 'uuid:Example-1_0-000EXAMPLE001', 'Example_FW_1.0', 'v9', '1', '0|49153',
                                 'urn:Belkin:device:example:1', 'media-1',
                                 json.dumps({'UPC': '000000000', 'manufacturer': 'Example Maker',
                                             'presentationURL': '/pluginpres.html'}, sort_keys=True),
                                 'lba900')])
        self.assertEqual(self.media, [('lba900/icon.jpg', 'icon.jpg')])
        self.assertEqual(source.split('\n'), [icon, setup])
        self.assertEqual(self.logged, [])

    def test_firmware_copies_and_other_devices_are_not_read(self):
        self.add('lba55/sbin/web/setup.xml', setup_xml('000FIRMWARE00'))
        self.add('lba900/setup.xml', setup_xml('000OTHER0000', namespace='urn:schemas-upnp-org:device-1-0'))
        self.add('lba901/setup.xml', b'<not xml')
        _headers, rows, source = self.run_artifact(bw.belkinWemoDevice)
        self.assertEqual((rows, source), ([], ''))
        self.assertEqual(self.logged, ["Belkin WeMo Device Description: 1 setup.xml files inside a firmware image's "
                                       "sbin/web folder, not read, 2 setup.xml files that are not a Belkin device "
                                       "description, not read"])

    def test_missing_icon_leaves_the_column_blank(self):
        self.add('lba900/setup.xml', setup_xml('000EXAMPLE002'))
        self.add('lba901/setup.xml', setup_xml('000EXAMPLE003', icon_url=''))
        self.add('lba902/setup.xml', setup_xml('000EXAMPLE004', icon_url='/other.png'))
        self.add('lba902/icon.jpg', PNG)                     # present, but not the file the url names
        _headers, rows, _source = self.run_artifact(bw.belkinWemoDevice)
        self.assertEqual([(r[5], r[13], r[0]) for r in rows],
                         [('000EXAMPLE002', '', ''), ('000EXAMPLE003', '', ''), ('000EXAMPLE004', '', '')])
        self.assertEqual(self.media, [])
        self.assertEqual(self.logged, ['Belkin WeMo Device Description: 2 icons named by setup.xml and not found '
                                       'in its folder'])

    def test_manufacture_data(self):
        self.add('lba900/ManufactureData.xml',
                 b'<?xml version="1.0"?>\n<ManufactureData>\n<CountryCode></CountryCode>\n'
                 b'<FirmwareVersion>Example_FW_1.0</FirmwareVersion>\n<APMacAddress></APMacAddress>\n'
                 b'<STAMacAddress>02:00:00:00:00:AB</STAMacAddress>\n<SSID>Example.Setup</SSID>\n'
                 b'<TargetCountry>ZZ</TargetCountry>\n<SerialNumber>000EXAMPLE001</SerialNumber>\n'
                 b'<ExtraField>x</ExtraField>\n</ManufactureData>\n', 1500000002)
        self.add('lba901/ManufactureData.xml', b'<?xml version="1.0"?>\n<Other/>\n')
        headers, rows, _source = self.run_artifact(bw.belkinWemoManufactureData)
        self.assertEqual(len(headers), len(rows[0]))
        self.assertEqual(rows, [(datetime.fromtimestamp(1500000002, timezone.utc), '000EXAMPLE001',
                                 '02:00:00:00:00:AB', '', 'Example.Setup', 'Example_FW_1.0', '', 'ZZ',
                                 json.dumps({'ExtraField': 'x'}), 'lba900')])
        self.assertEqual(self.logged, ['Belkin WeMo Manufacture Data: 1 files that are not a ManufactureData '
                                       'element, not read'])


if __name__ == '__main__':
    unittest.main()
