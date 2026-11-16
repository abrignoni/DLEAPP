"""Every artifact declares the operating systems its files come from.

The `platforms` key of an artifact block is a tuple of names from PLATFORMS. It lists the
systems the artifact's files come from. The category decides when it names a system
("Wire (Windows)", "Biome (macOS)"). Otherwise the module's docstring and notes decide when
they name the systems the application keeps these files on (Dropbox "for Windows", sudo's
Linux syslog). Otherwise the paths decide: a path under AppData or the registry hives is
Windows, one under Library is macOS, one under .config, /home or the systemd journal is
Linux, and a glob that names no system root (*/.bash_history, *.pst, */discord*/) is valued
for all three. Device is for stores read from the firmware of a device that is not a
computer (a TV, a camera, a doorbell, a bootloader), and is never combined with a system.

The value says where the files are found, not where the artifact was tested. The sample_data
block records that.

leapps.org/artifacts is meant to filter DLEAPP artifacts by this key, so a missing or
misspelled value would leave the artifact out of that filter.

Two passes, because each misses what the other catches: the AST pass reads every literal
block, including a module the loader would skip, and the PluginLoader pass sees blocks built
by a helper (robloxWindows.py), which are not literals.
"""
import ast
import pathlib
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parents[3]
ARTIFACTS = REPO / 'scripts' / 'artifacts'
PLATFORMS = ('Windows', 'macOS', 'Linux', 'Device')


def problem(value):
    """Why a platforms value is wrong, or None when it is right."""
    if not isinstance(value, tuple) or not value:
        return f'not a non-empty tuple: {value!r}'
    unknown = [v for v in value if v not in PLATFORMS]
    if unknown:
        return f'not in {PLATFORMS}: {unknown!r}'
    if len(set(value)) != len(value):
        return f'repeats a value: {value!r}'
    if 'Device' in value and len(value) > 1:
        return f'Device combined with an operating system: {value!r}'
    return None


def literal_blocks():
    for path in sorted(ARTIFACTS.glob('*.py')):
        for node in ast.parse(path.read_text(encoding='utf-8')).body:
            if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == '__artifacts_v2__'):
                try:
                    block = ast.literal_eval(node.value)
                except ValueError:
                    continue
                yield path.name, block


class ArtifactPlatformsTest(unittest.TestCase):

    def test_every_literal_block_declares_platforms(self):
        checked = 0
        wrong = []
        for name, block in literal_blocks():
            for artifact, info in block.items():
                checked += 1
                why = problem(info.get('platforms'))
                if why:
                    wrong.append((name, artifact, why))
        self.assertGreater(checked, 900)
        self.assertEqual(wrong, [])

    def test_every_loaded_plugin_declares_platforms(self):
        sys.path.insert(0, str(REPO))
        try:
            from scripts.plugin_loader import PluginLoader  # pylint: disable=import-outside-toplevel
        finally:
            sys.path.remove(str(REPO))
        loader = PluginLoader()
        wrong = [(p.name, problem(p.artifact_info.get('platforms')))
                 for p in loader.plugins if problem(p.artifact_info.get('platforms'))]
        self.assertGreater(len(loader), 900)
        self.assertEqual(wrong, [])


if __name__ == '__main__':
    unittest.main()
