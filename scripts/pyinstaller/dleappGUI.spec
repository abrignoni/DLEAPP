# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# PyInstaller resolves pathex and hookspath against the current working
# directory, unlike the script and datas paths below, which it resolves against
# the spec file. Anchor them to SPECPATH so the build works from any directory.
a = Analysis(['..\\..\\dleappGUI.py'],
             pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
             binaries=[],
             datas=[('..\\', '.\\scripts'), ('..\\..\\assets', '.\\assets')],
             hiddenimports=[
                'bencoding',
                'fitz',
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
          upx=True,
          console=True,
		    hide_console='hide-early',
		    disable_windowed_traceback=False,
          upx_exclude=[],
          version='dleappGUI-file_version_info.txt',
          runtime_tmpdir=None )
