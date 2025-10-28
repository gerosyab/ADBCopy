# -*- mode: python ; coding: utf-8 -*-
# ADBCopy - Single File Build (Optimized)

block_cipher = None

a = Analysis(
    ['adb_copy/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('adb_copy/resources/icons/favicon.ico', 'adb_copy/resources/icons'),
        ('adb_copy/resources/icons/ADBCopy.png', 'adb_copy/resources/icons'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
        'scipy',
        'IPython',
        'notebook',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ADBCopy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='adb_copy/resources/icons/favicon.ico',
)
