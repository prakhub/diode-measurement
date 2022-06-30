import os
import diode_measurement

version = diode_measurement.__version__
name = "diode-measurement"
filename = f"{name}-{version}.exe"
organization = "HEPHY"
license = "GPLv3"
console = True
block_cipher = None

package_root = os.path.join(os.path.dirname(diode_measurement.__file__))
package_icon = os.path.join(package_root, "assets", "icons", "diode-measurement.ico")

# Windows version info template
version_info = """
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=({version[0]}, {version[1]}, {version[2]}, 0),
        prodvers=({version[0]}, {version[1]}, {version[2]}, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
            StringTable(
                u'000004b0',
                [StringStruct(u'CompanyName', u'{organization}'),
                StringStruct(u'FileDescription', u'{name}'),
                StringStruct(u'FileVersion', u'{version[0]}.{version[1]}.{version[2]}.0'),
                StringStruct(u'InternalName', u'{name}'),
                StringStruct(u'LegalCopyright', u'{license}'),
                StringStruct(u'OriginalFilename', u'{name}.exe'),
                StringStruct(u'ProductName', u'{name}'),
                StringStruct(u'ProductVersion', u'{version[0]}.{version[1]}.{version[2]}.0'),
                ])
            ]),
        VarFileInfo([VarStruct(u'Translation', [0, 1200])])
    ]
)
"""

# Create entry point
with open("entry_point.py", "wt") as fp:
    fp.write("from diode_measurement.__main__ import main; main()")

# Create windows version info
with open("version_info.txt", "wt") as fp:
    fp.write(version_info.format(
        name=name,
        organization=organization,
        version=version.split("."),
        license=license
    ))

a = Analysis(
    ["entry_point.py"],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        (os.path.join(package_root, "assets", "icons", "*.svg"), os.path.join("diode_measurement", "assets", "icons")),
        (os.path.join(package_root, "assets", "icons", "*.ico"), os.path.join("diode_measurement", "assets", "icons")),
    ],
    hiddenimports=[
        "pyvisa",
        "pyvisa_py",
        "pyserial",
        "pyusb"
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
    name=filename,
    version="version_info.txt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    icon=package_icon
)
