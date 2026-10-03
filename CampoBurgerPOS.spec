# -*- mode: python ; coding: utf-8 -*-


# ================================================================
# CAMPO BURGER POS
# CONFIGURACION DE PYINSTALLER
# ================================================================


a = Analysis(
    ['main.py'],

    pathex=[],

    binaries=[],

    datas=[
        ('campo_burger.ico', '.'),
    ],

    hiddenimports=[
        'win32print',
        'pywintypes',
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],

    noarchive=False,
    optimize=0,
)


# ================================================================
# PAQUETE PYTHON
# ================================================================

pyz = PYZ(a.pure)


# ================================================================
# EJECUTABLE PRINCIPAL
# ================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],

    exclude_binaries=True,

    name='CampoBurgerPOS',

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

    icon=['campo_burger.ico'],
)


# ================================================================
# CARPETA FINAL DEL PROGRAMA
# ================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,

    strip=False,
    upx=True,
    upx_exclude=[],

    name='CampoBurgerPOS',
)