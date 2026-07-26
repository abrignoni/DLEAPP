# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../../dleappGUI.py'],
    pathex=['scripts/artifacts'],
    binaries=[],
    datas=[('../', 'scripts'), ('../../assets', 'assets')],
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
    version='2.2.0',
)
