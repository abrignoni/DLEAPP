"""Pin the rows, locations and file times of scripts/artifacts/windowsClrUsageLogs.py."""
import datetime
import pathlib
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsClrUsageLogs as clr  # pylint: disable=wrong-import-position
from scripts.search_files import FileInfo  # pylint: disable=wrong-import-position

_UTC = datetime.timezone.utc
_LOG = (b'1,"fusion","GAC",0\r\n1,"WinRT","NotApp",1\r\n'
        b'3,"System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089",'
        b'"C:\\Windows\\assembly\\NativeImages_v4.0.30319_64\\System\\1\\System.ni.dll",0\r\n')


class LocationTest(unittest.TestCase):
    def test_profile_clr_folder_and_package(self):
        cases = {
            'vol/Users/IEUser/AppData/Local/Microsoft/CLR_v4.0/UsageLogs/mmc.exe.log':
                ('IEUser', 'CLR_v4.0', ''),
            'vol/Windows/System32/config/systemprofile/AppData/Local/Microsoft/CLR_v4.0_32/'
            'UsageLogs/NGenTask.exe.log': ('systemprofile', 'CLR_v4.0_32', ''),
            'vol/Windows/SysWOW64/config/systemprofile/AppData/Local/Microsoft/CLR_v4.0_32/'
            'UsageLogs/a.exe.log': ('systemprofile', 'CLR_v4.0_32', ''),
            'vol/Windows/ServiceProfiles/NetworkService/AppData/Local/Microsoft/CLR_v4.0/'
            'UsageLogs/b.exe.log': ('NetworkService', 'CLR_v4.0', ''),
            'vol/Users/borch/AppData/Local/Packages/Microsoft.MicrosoftOfficeHub_8wekyb3d8bbwe/'
            'LocalCache/Local/Microsoft/CLR_v4.0/UsageLogs/LocalBridge.exe.log':
                ('borch', 'CLR_v4.0', 'Microsoft.MicrosoftOfficeHub_8wekyb3d8bbwe'),
            'vol\\Users\\u\\AppData\\Local\\Microsoft\\CLR_v2.0\\UsageLogs\\c.exe.log':
                ('u', 'CLR_v2.0', ''),
            'vol/Users/Packages/AppData/Local/Microsoft/CLR_v4.0/UsageLogs/d.exe.log':
                ('Packages', 'CLR_v4.0', ''),
        }
        for relative, expected in cases.items():
            self.assertEqual(clr.location(relative), expected, relative)

    def test_log_text_keeps_the_lines_as_stored(self):
        self.assertEqual(clr.log_text(_LOG).split('\n'), [
            '1,"fusion","GAC",0', '1,"WinRT","NotApp",1',
            '3,"System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089",'
            '"C:\\Windows\\assembly\\NativeImages_v4.0.30319_64\\System\\1\\System.ni.dll",0'])
        self.assertEqual(clr.log_text(b'a\xffb'), 'a\ufffdb')


class ImageSeeker:
    """A raw image seeker: it lists streams, and its file times are the evidence's."""

    stream_list = ()

    def __init__(self, file_infos):
        self.file_infos = file_infos


class FolderSeeker:
    def __init__(self, file_infos):
        self.file_infos = file_infos


class FakeContext:
    def __init__(self, root, files, seeker):
        self.root = root
        self.files = files
        self.seeker = seeker

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return str(pathlib.Path(path).relative_to(self.root))

    def get_seeker(self):
        return self.seeker


class ProcessorTest(unittest.TestCase):
    def run_on(self, seeker_class):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp, 'vol', 'Users', 'u', 'AppData', 'Local', 'Microsoft',
                                  'CLR_v4.0', 'UsageLogs')
            folder.mkdir(parents=True)
            log = folder / 'powershell.exe.log'
            log.write_bytes(_LOG)
            other = folder / 'notes.txt'
            other.write_bytes(b'x')
            infos = {str(log): FileInfo('vol/Users/u/.../powershell.exe.log',
                                        1676935750.5, 1677098865.25)}
            context = FakeContext(tmp, [str(folder), str(other), str(log)],
                                  seeker_class(infos))
            headers, rows, source = clr.clrUsageLogs.__wrapped__(context)
            return headers, rows, source, str(log)

    def test_an_image_gives_the_file_times(self):
        headers, rows, source, log = self.run_on(ImageSeeker)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(headers), len(rows[0]))
        row = rows[0]
        self.assertEqual(row[0], datetime.datetime.fromtimestamp(1676935750.5, _UTC))
        self.assertEqual(row[1], datetime.datetime.fromtimestamp(1677098865.25, _UTC))
        self.assertEqual(row[2:6], ('powershell.exe', 'u', 'CLR_v4.0', ''))
        self.assertTrue(row[6].startswith('1,"fusion","GAC",0\n'))
        self.assertEqual(source, log)

    def test_a_folder_or_archive_leaves_the_times_blank(self):
        _headers, rows, _source, _log = self.run_on(FolderSeeker)
        self.assertEqual(rows[0][:3], ('', '', 'powershell.exe'))


if __name__ == '__main__':
    unittest.main()
