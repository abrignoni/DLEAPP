# -*- mode: python ; coding: utf-8 -*-

import os

# PyInstaller resolves pathex against the current working directory, unlike the
# script and datas paths below, which it resolves against the spec file. Anchor
# it to SPECPATH so the build works from any directory.
a = Analysis(
    ['../../dleapp.py'],
    pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
    binaries=[],
    datas=[('../', 'scripts')],
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
        'xlrd',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dleapp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
