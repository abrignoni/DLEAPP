# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# PyInstaller resolves pathex and hookspath against the current working
# directory, unlike the script and datas paths below, which it resolves against
# the spec file. Anchor them to SPECPATH so the build works from any directory.
a = Analysis(['..\\..\\dleapp.py'],
             pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
             binaries=[],
             datas=[('..\\', '.\\scripts')],
             hiddenimports=[
                'bencoding',
                'fitz',
                'ijson',
                'mailbox',
                'mammoth',
                'openpyxl',
                'pillow_heif',
                'pypdf',
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
          name='dleapp',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          version='dleapp-file_version_info.txt',
          console=True )
