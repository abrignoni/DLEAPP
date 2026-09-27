"""DLEAPP profile files: saved as .dlprofile, and .rlprofile files from earlier releases still load.

Releases up to v2026.4.1 saved profiles with RLEAPP's extension. What makes a file
a DLEAPP profile is its "leapp": "dleapp" value, so an RLEAPP profile is refused
whatever it is called, and a DLEAPP profile loads whatever it is called.

The GUI cannot be imported without a display, so its two file dialogs are checked
by reading dleappGUI.py: the open dialog must offer both extensions, the save
dialog must default to .dlprofile, and both must use the shared helpers in
dleapp.py rather than their own copies.
"""
import ast
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import dleapp  # noqa: E402  pylint: disable=wrong-import-position


def _write_json(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


class TestProfileFileName(unittest.TestCase):

    def test_adds_the_dleapp_extension(self):
        self.assertEqual(dleapp.profile_file_name('case'), 'case.dlprofile')

    def test_does_not_add_it_twice(self):
        self.assertEqual(dleapp.profile_file_name('case.dlprofile'), 'case.dlprofile')
        self.assertEqual(dleapp.profile_file_name('case.DLPROFILE'), 'case.DLPROFILE')

    def test_open_dialog_patterns_cover_both_extensions(self):
        self.assertEqual(dleapp.PROFILE_OPEN_PATTERNS, ('*.dlprofile', '*.rlprofile'))


class TestSaveAndLoad(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_cli_wizard_saves_a_dlprofile_that_loads(self):
        plugins = [SimpleNamespace(category='Browsers', name='firefoxHistory'),
                   SimpleNamespace(category='Windows', name='windowsPrefetch')]
        # Add module 2 (sorted by category then name), save, name it 'case'.
        answers = iter(['a', '2', 'q', 'case'])
        with mock.patch('builtins.input', lambda prompt='': next(answers)), \
                mock.patch('builtins.print'):
            dleapp.create_profile(plugins, str(self.folder))

        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), ['case.dlprofile'])
        saved = self.folder / 'case.dlprofile'
        self.assertEqual(json.loads(saved.read_text(encoding='utf-8')),
                         {'leapp': 'dleapp', 'format_version': 1, 'plugins': ['windowsPrefetch']})
        self.assertEqual(dleapp.read_profile(str(saved)), ({'windowsPrefetch'}, None))

    def test_write_profile_round_trips(self):
        path = self.folder / 'gui.dlprofile'
        dleapp.write_profile(str(path), ['a', 'b'])
        self.assertEqual(dleapp.read_profile(str(path)), ({'a', 'b'}, None))

    def test_legacy_rlprofile_from_dleapp_loads(self):
        path = self.folder / 'old.rlprofile'
        _write_json(path, {'leapp': 'dleapp', 'format_version': 1, 'plugins': ['wireMessages']})
        self.assertEqual(dleapp.read_profile(str(path)), ({'wireMessages'}, None))

    def test_rleapp_profile_is_refused(self):
        path = self.folder / 'rleapp.rlprofile'
        _write_json(path, {'leapp': 'rleapp', 'format_version': 1, 'plugins': ['x']})
        plugins, error = dleapp.read_profile(str(path))
        self.assertIsNone(plugins)
        self.assertIn('incorrect LEAPP or version', error)

    def test_extension_does_not_make_a_file_a_dleapp_profile(self):
        path = self.folder / 'renamed.dlprofile'
        _write_json(path, {'leapp': 'rleapp', 'format_version': 1, 'plugins': ['x']})
        self.assertIsNone(dleapp.read_profile(str(path))[0])

    def test_unsupported_format_version_is_refused(self):
        path = self.folder / 'future.dlprofile'
        _write_json(path, {'leapp': 'dleapp', 'format_version': 2, 'plugins': ['x']})
        self.assertIsNone(dleapp.read_profile(str(path))[0])

    def test_invalid_files_are_refused(self):
        for name, content in (('broken.dlprofile', b'{not json'),
                              ('list.dlprofile', b'["x"]'),
                              ('binary.dlprofile', b'\xff\xfe\x00junk')):
            path = self.folder / name
            path.write_bytes(content)
            plugins, error = dleapp.read_profile(str(path))
            self.assertIsNone(plugins, name)
            self.assertIn('invalid format', error, name)

    def test_profiles_shipped_in_the_repo_load(self):
        shipped = sorted(REPO_ROOT.glob('*.dlprofile'))
        self.assertTrue(shipped, 'no .dlprofile files at the repository root')
        for path in shipped:
            plugins, error = dleapp.read_profile(str(path))
            self.assertIsNone(error, path.name)
            self.assertTrue(plugins, path.name)


def _function(tree, name):
    """The top-level function named name."""
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(found) == 1, (name, len(found))
    return found[0]


def _call(tree, attribute):
    """The one call under tree to <something>.<attribute>(...)."""
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == attribute]
    assert len(calls) == 1, (attribute, len(calls))
    return calls[0]


class TestGuiDialogs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = (REPO_ROOT / 'dleappGUI.py').read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)

    def _keyword(self, call, name):
        return ast.unparse(next(k.value for k in call.keywords if k.arg == name))

    def test_open_dialog_offers_both_extensions(self):
        call = _call(_function(self.tree, 'load_profile'), 'askopenfilename')
        self.assertEqual(self._keyword(call, 'filetypes'),
                         "(('DLEAPP Profile', dleapp.PROFILE_OPEN_PATTERNS),)")

    def test_save_dialog_defaults_to_dlprofile(self):
        call = _call(_function(self.tree, 'save_profile'), 'asksaveasfilename')
        self.assertEqual(self._keyword(call, 'defaultextension'), 'dleapp.PROFILE_EXTENSION')

    def test_gui_uses_the_shared_reader_and_writer(self):
        _call(_function(self.tree, 'load_profile'), 'read_profile')
        _call(_function(self.tree, 'save_profile'), 'write_profile')
        self.assertNotIn('rlprofile', self.source)


if __name__ == '__main__':
    unittest.main()
