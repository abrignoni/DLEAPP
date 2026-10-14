"""dleapp.py must load modules from --custom_artifacts_path.

The option builds its loader path with pathlib, and dleapp.py once used pathlib
there without importing it, so every run that passed the option stopped with a
NameError before loading anything. The test runs the real command line with a
folder holding one module and checks that module's search pattern reaches the
--artifact_paths list, which is written from every loaded module.
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
CLI_ENTRY_POINT = REPO_ROOT / 'dleapp.py'

SEARCH_PATTERN = '*/custom_artifacts_path_check.txt'

MODULE_SOURCE = textwrap.dedent(f'''\
    __artifacts_v2__ = {{
        "customArtifactsPathCheck": {{
            "name": "Custom Artifacts Path Check",
            "description": "Test module loaded from --custom_artifacts_path.",
            "author": "@AlexisBrignoni, Claude",
            "creation_date": "2026-10-14",
            "last_update_date": "2026-10-14",
            "requirements": "none",
            "category": "Test",
            "notes": "",
            "paths": ("{SEARCH_PATTERN}",),
            "output_types": "none",
        }}
    }}

    from scripts.ilapfuncs import artifact_processor


    @artifact_processor
    def customArtifactsPathCheck(context):
        return ("Value",), [], ""
''')


class TestCustomArtifactsPath(unittest.TestCase):

    def test_custom_module_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            custom = tmp / 'custom'
            custom.mkdir()
            (custom / 'customArtifactsPathCheck.py').write_text(MODULE_SOURCE, encoding='utf-8')
            work = tmp / 'work'
            work.mkdir()
            env = dict(os.environ, HOME=str(tmp / 'home'))
            result = subprocess.run(
                [sys.executable, str(CLI_ENTRY_POINT), '-p',
                 '--custom_artifacts_path', str(custom)],
                cwd=work, env=env, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=300, check=False)
            self.assertEqual(result.returncode, 0,
                             f'dleapp.py failed:\n{result.stdout}\n{result.stderr}')
            path_list = (work / 'path_list.txt').read_text(encoding='utf-8').splitlines()
            self.assertIn(SEARCH_PATTERN, path_list)


if __name__ == '__main__':
    unittest.main()
