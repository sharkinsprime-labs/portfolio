# TCG_Toolbox.spec
from PyInstaller.utils.hooks import collect_all

APP_NAME = "TCGToolbox"  # folder/exe name (no spaces recommended)

datas, binaries, hiddenimports = [], [], []

d, b, h = collect_all("PySide6")
datas += d
binaries += b
hiddenimports += h

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    strip=False,
    upx=True,
    console=False,  # GUI app
    # icon="assets/icon.ico",  # uncomment if you add an ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name=APP_NAME,
)
