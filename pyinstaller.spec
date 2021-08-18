# -*- mode: python ; coding: utf-8 -*-

import os
import diode_measurement

version = diode_measurement.__version__
console = True
block_cipher = None

with open('_app.py', 'w') as fp:
    fp.write('from diode_measurement.__main__ import main; main()')

a = Analysis(
    ['_app.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[],
    hiddenimports=[
      'pyvisa',
      'pyvisa_py',
      'pyserial',
      'pyusb'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'diode-measurement-{version}.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console
)
