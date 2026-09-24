"""Every PyInstaller spec must bundle the Unified Log parser, its license and its notices.

There are six spec files, one per (CLI, GUI) x (Windows, macOS, Linux). A new spec, or a
spec someone regenerates with `pyi-makespec`, silently goes back to `binaries=[]`, and the
only symptom is that native Apple Unified Log support quietly disappears from that one
platform's build. Nothing else in the test suite would notice.

The specs are plain Python evaluated by PyInstaller, so they are exec'd here with stubbed
PyInstaller globals and the resulting Analysis arguments inspected. Ported from iLEAPP.

The license and notices checks are not decoration. unifiedlog_iterator is Apache-2.0 and
this project is MIT; section 4(a) requires that anyone receiving a redistribution also
receives the license, and the binary statically links Rust crates under their own
licenses, whose texts the notices file carries. A build that ships the binary without
either is a licensing defect, so the helper raises rather than quietly omitting it.
"""
import pathlib
import sys
import tempfile
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / 'scripts' / 'pyinstaller'))

# The specs import collect_submodules from PyInstaller, which CI does not install (it
# only installs requirements.txt). A stub is injected unconditionally, not just when the
# real thing is absent, so the assertions below can look for deterministic sentinels
# instead of whatever set of submodules the local PyInstaller happens to resolve. The
# tests thereby verify that a spec ASKS for a package's submodules, which is the part a
# regenerated spec loses; what PyInstaller does with the request is its own business.
_hooks_stub = types.ModuleType('PyInstaller.utils.hooks')
_hooks_stub.collect_submodules = lambda package: [f'<collect_submodules:{package}>']
_pyinstaller_stub = types.ModuleType('PyInstaller')
_pyinstaller_utils_stub = types.ModuleType('PyInstaller.utils')
_pyinstaller_stub.utils = _pyinstaller_utils_stub
_pyinstaller_utils_stub.hooks = _hooks_stub
sys.modules['PyInstaller'] = _pyinstaller_stub
sys.modules['PyInstaller.utils'] = _pyinstaller_utils_stub
sys.modules['PyInstaller.utils.hooks'] = _hooks_stub

import unifiedlog_binary  # pylint: disable=wrong-import-position

SPEC_DIR = REPO_ROOT / 'scripts' / 'pyinstaller'
EXPECTED_SPECS = {
    'dleapp.spec', 'dleappGUI.spec',
    'dleapp_Linux.spec', 'dleappGUI_Linux.spec',
    'dleapp_macOS.spec', 'dleappGUI_macOS.spec',
}


class _Inert:
    """Stands in for PYZ/EXE/COLLECT/BUNDLE, which the specs only pass around."""

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        pass


class _CapturedAnalysis:
    """Stands in for PyInstaller's Analysis, recording what the spec asked for.

    Only Analysis records itself. The other stubs must not, or the last thing the spec
    constructs (EXE, or COLLECT/BUNDLE in the macOS specs) would be what gets inspected.
    """

    last = None

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        # Positional args are the scripts list; only the keywords matter here.
        self.kwargs = kwargs
        self.pure = self.zipped_data = self.scripts = []
        self.binaries = self.zipfiles = self.datas = []
        _CapturedAnalysis.last = self


def _run_spec(path):
    """Execute one spec with PyInstaller's globals stubbed out, returning Analysis kwargs."""
    _CapturedAnalysis.last = None
    namespace = {
        'Analysis': _CapturedAnalysis, 'PYZ': _Inert, 'EXE': _Inert,
        'COLLECT': _Inert, 'BUNDLE': _Inert,
        'SPECPATH': str(SPEC_DIR), '__file__': str(path),
    }
    # Spec files are Python that PyInstaller exec's; running them is the only way to
    # see what they actually pass to Analysis.
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'),  # pylint: disable=exec-used
         namespace)  # nosec B102
    if _CapturedAnalysis.last is None:
        raise AssertionError(f'{path.name} never called Analysis()')
    return _CapturedAnalysis.last.kwargs


def _bundled(entries, name):
    return any(dest == 'bin' and pathlib.Path(src).name == name for src, dest in entries)


class TestSpecsBundleTheParser(unittest.TestCase):
    """All six specs must pick up the binary, its license and its notices."""

    @classmethod
    def setUpClass(cls):
        # Point the helper at a throwaway bin/ so the result does not depend on whether
        # the developer has run the fetch script.
        cls.tmpdir = tempfile.mkdtemp()
        cls.original_bin_dir = unifiedlog_binary.BIN_DIR
        unifiedlog_binary.BIN_DIR = cls.tmpdir
        for name in ('unifiedlog_iterator', 'unifiedlog_iterator.exe'):
            path = pathlib.Path(cls.tmpdir) / name
            path.write_bytes(b'not a real binary')
            path.chmod(0o755)
        (pathlib.Path(cls.tmpdir) / unifiedlog_binary.LICENSE_NAME).write_text('Apache-2.0')
        (pathlib.Path(cls.tmpdir) / unifiedlog_binary.NOTICES_NAME).write_text('notices')

    @classmethod
    def tearDownClass(cls):
        unifiedlog_binary.BIN_DIR = cls.original_bin_dir

    def test_the_expected_specs_exist(self):
        # A spec added without being added here would not be covered by the checks below.
        self.assertEqual({p.name for p in SPEC_DIR.glob('*.spec')}, EXPECTED_SPECS)

    def test_every_spec_bundles_binary_license_and_notices(self):
        for name in sorted(EXPECTED_SPECS):
            with self.subTest(spec=name):
                kwargs = _run_spec(SPEC_DIR / name)
                binary = 'unifiedlog_iterator.exe' if '_' not in name else 'unifiedlog_iterator'
                self.assertTrue(_bundled(kwargs['binaries'], binary),
                                f'{name} does not bundle {binary}: {kwargs["binaries"]}')
                self.assertTrue(_bundled(kwargs['datas'], unifiedlog_binary.LICENSE_NAME),
                                f'{name} bundles the parser without its Apache-2.0 license')
                self.assertTrue(_bundled(kwargs['datas'], unifiedlog_binary.NOTICES_NAME),
                                f'{name} bundles the parser without its third-party notices')

    def test_specs_keep_their_own_datas(self):
        # The license and notices are appended to each spec's existing datas; dropping the
        # originals would ship a build with no scripts or assets.
        for name in sorted(EXPECTED_SPECS):
            with self.subTest(spec=name):
                datas = _run_spec(SPEC_DIR / name)['datas']
                destinations = [str(dest).replace('.\\', '') for _, dest in datas]
                self.assertIn('scripts', destinations, f'{name} lost its scripts entry')
                self.assertIn('assets', destinations, f'{name} lost its assets entry')


class TestFrozenBuildsCollectPythonEvtx(unittest.TestCase):
    """Every spec must collect python-evtx.

    The .evtx artifacts import Evtx.Evtx from disk at runtime, so PyInstaller's import
    graph never sees it. A macOS build from the specs without this entry carried no Evtx
    module at all, and its run of the Defender scan artifact on a Windows 11 Defender
    Operational log reported that python-evtx is not installed and returned no rows.
    """

    def test_every_spec_collects_evtx(self):
        for name in sorted(EXPECTED_SPECS):
            with self.subTest(spec=name):
                hidden = _run_spec(SPEC_DIR / name)['hiddenimports']
                self.assertIn('<collect_submodules:Evtx>', hidden,
                              f'{name} no longer collects python-evtx')


class TestFrozenBuildsImportPefile(unittest.TestCase):
    """Every spec must list pefile, which the Defender artifacts reach only from disk."""

    def test_every_spec_imports_pefile(self):
        for name in sorted(EXPECTED_SPECS):
            with self.subTest(spec=name):
                self.assertIn('pefile', _run_spec(SPEC_DIR / name)['hiddenimports'],
                              f'{name} no longer lists pefile')


class TestBuildsWithoutTheBinary(unittest.TestCase):
    """A checkout that has not run the fetch script must still build."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_bin_dir = unifiedlog_binary.BIN_DIR
        unifiedlog_binary.BIN_DIR = self.tmpdir
        self.addCleanup(setattr, unifiedlog_binary, 'BIN_DIR', self.original_bin_dir)

    def _binary(self):
        path = pathlib.Path(self.tmpdir) / 'unifiedlog_iterator'
        path.write_bytes(b'x')
        path.chmod(0o755)

    def test_absent_binary_yields_empty_lists(self):
        self.assertEqual(unifiedlog_binary.unifiedlog_binaries(), [])
        self.assertEqual(unifiedlog_binary.unifiedlog_datas(), [])

    def test_every_spec_still_evaluates(self):
        for name in sorted(EXPECTED_SPECS):
            with self.subTest(spec=name):
                self.assertEqual(_run_spec(SPEC_DIR / name)['binaries'], [])

    def test_binary_without_license_is_refused(self):
        self._binary()
        (pathlib.Path(self.tmpdir) / unifiedlog_binary.NOTICES_NAME).write_text('notices')
        with self.assertRaises(SystemExit):
            unifiedlog_binary.unifiedlog_datas()

    def test_binary_without_notices_is_refused(self):
        self._binary()
        (pathlib.Path(self.tmpdir) / unifiedlog_binary.LICENSE_NAME).write_text('Apache-2.0')
        with self.assertRaises(SystemExit):
            unifiedlog_binary.unifiedlog_datas()

    def test_the_committed_notices_file_is_where_the_helper_looks(self):
        # The notices file is committed, not fetched, so a checkout always has it.
        self.assertTrue((REPO_ROOT / 'bin' / unifiedlog_binary.NOTICES_NAME).is_file())
        self.assertEqual(pathlib.Path(self.original_bin_dir), REPO_ROOT / 'bin')


class TestRuntimeAndBuildAgreeOnLocation(unittest.TestCase):
    """The specs put the binary in 'bin'; scripts/unifiedlogs.py has to look there."""

    def test_bundle_destination_matches_runtime_search_path(self):
        from scripts import unifiedlogs  # pylint: disable=import-outside-toplevel
        searched = [pathlib.Path(d).name for d in unifiedlogs._bundled_binary_dirs()]  # pylint: disable=protected-access
        self.assertIn('bin', searched)

    def test_repo_bin_directory_is_searched_in_a_source_checkout(self):
        from scripts import unifiedlogs  # pylint: disable=import-outside-toplevel
        searched = [pathlib.Path(d) for d in unifiedlogs._bundled_binary_dirs()]  # pylint: disable=protected-access
        self.assertIn(REPO_ROOT / 'bin', searched)


if __name__ == '__main__':
    unittest.main()
