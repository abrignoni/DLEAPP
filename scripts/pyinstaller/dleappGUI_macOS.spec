# -*- mode: python ; coding: utf-8 -*-

import os

# PyInstaller resolves pathex against the current working directory, unlike the
# script and datas paths below, which it resolves against the spec file. Anchor
# it to SPECPATH so the build works from any directory.
a = Analysis(
    ['../../dleappGUI.py'],
    pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
    binaries=[],
    datas=[
        ('../', 'scripts'),
        ('../../assets', 'assets'),
        ('../../leapp_functions', 'leapp_functions')],
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
    [],
    exclude_binaries=True,
    name='dleappGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dleappGUI',
)
app = BUNDLE(
    coll,
    name='dleappGUI.app',
    icon='../../assets/icon.icns',
    bundle_identifier='4n6.brigs.DLEAPP',
    version='2026.3.0',
)
