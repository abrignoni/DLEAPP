# -*- mode: python ; coding: utf-8 -*-

import os
import sys

sys.path.insert(0, SPECPATH)
from unifiedlog_binary import unifiedlog_binaries, unifiedlog_datas
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# PyInstaller resolves pathex and hookspath against the current working
# directory, unlike the script and datas paths below, which it resolves against
# the spec file. Anchor them to SPECPATH so the build works from any directory.
a = Analysis(['..\\..\\dleappGUI.py'],
             pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
             binaries=unifiedlog_binaries(windows=True),
             datas=[('..\\', '.\\scripts'), ('..\\..\\assets', '.\\assets')] + unifiedlog_datas(windows=True),
             hiddenimports=[
                # Stdlib that only artifacts import. Artifacts are bundled as data
                # files and imported from disk at runtime, so PyInstaller's
                # import-graph analysis never sees these, and it prunes stdlib it
                # cannot see used (mailbox below is the same case, added earlier).
                'base64',
                'email.utils',
                'plistlib',
                'struct',
                'xml.etree.ElementTree',
                'bencoding',
                'ijson',
                'mailbox',
                'mammoth',
                'openpyxl',
                'pillow_heif',
                'pypdf',
                'Registry',
                'requests',
                'simplekml',
                'xlrd',
                # python-evtx: the .evtx artifacts import Evtx.Evtx from disk at runtime, so the
                # import graph never sees it, and a build without this entry reads no event log
                # (the run log says python-evtx is not installed).
                *collect_submodules('Evtx'),
                ],
             hookspath=[SPECPATH],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='dleappGUI',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True,
		    hide_console='hide-early',
		    disable_windowed_traceback=False,
          upx_exclude=[],
          version='dleappGUI-file_version_info.txt',
          runtime_tmpdir=None )
