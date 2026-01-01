$ErrorActionPreference = "Stop"

# 1) Create / activate venv
if (!(Test-Path ".\.venv")) {
  py -m venv .venv
}
.\.venv\Scripts\Activate.ps1

# 2) Install deps
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 3) Clean old outputs
if (Test-Path ".\build") { Remove-Item ".\build" -Recurse -Force }
if (Test-Path ".\dist")  { Remove-Item ".\dist"  -Recurse -Force }

# 4) Build from spec
$ErrorActionPreference = "Stop"
pyinstaller --clean .\TCG_Toolbox.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\TCG_Toolbox\TCG_Toolbox.exe"

