# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analysis: Find all dependencies
a = Analysis(
    ['adb_copy/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('adb_copy/resources/icons/*.ico', 'adb_copy/resources/icons'),
        ('adb_copy/resources/icons/*.png', 'adb_copy/resources/icons'),
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
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Create archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: Create executable (FOLDER build - fast!)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Important: Keep files separate
    name='ADBCopy',
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
    icon='adb_copy/resources/icons/favicon.ico',
)

# COLLECT: Collect all files into dist folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADBCopy',
)

