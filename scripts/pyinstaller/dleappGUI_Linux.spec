# -*- mode: python ; coding: utf-8 -*-

import os
import sys

sys.path.insert(0, SPECPATH)
from unifiedlog_binary import unifiedlog_binaries, unifiedlog_datas
from PyInstaller.utils.hooks import collect_submodules

# PyInstaller resolves pathex against the current working directory, unlike the
# script and datas paths below, which it resolves against the spec file. Anchor
# it to SPECPATH so the build works from any directory.
a = Analysis(
    ['../../dleappGUI.py'],
    pathex=[os.path.join(SPECPATH, '..', 'artifacts')],
    binaries=unifiedlog_binaries(),
    datas=[
        ('../', 'scripts'),
        ('../../assets', 'assets'),
        ('../../leapp_functions', 'leapp_functions')] + unifiedlog_datas(),
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
        # pefile: scripts/windows_messages.py reads Defender's message files with
        # it, and the artifacts load that module from disk, out of the import graph.
        'pefile',
        'PIL._tkinter_finder',
        'pillow_heif',
        'pypdf',
        'Registry',
        'requests',
        'xlrd',
        # python-evtx: the .evtx artifacts import Evtx.Evtx from disk at runtime, so the
        # import graph never sees it, and a build without this entry reads no event log
        # (the run log says python-evtx is not installed).
        *collect_submodules('Evtx'),
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
    name='dleappGUI',
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
)
