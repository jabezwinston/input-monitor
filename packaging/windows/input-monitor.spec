# PyInstaller spec for input-monitor. Use this if you need more control than the helper scripts.

# One-file, windowed app (no console)
# Adjust datas to include icon and other files if needed.

block_cipher = None

a = Analysis(
    ['packaging/windows/entry_point.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Example: add icon or other resources if provided
        # ('assets/icon.ico', '.'),
    ],
    hiddenimports=['pynput', 'keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='input-monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='input-monitor',
)
