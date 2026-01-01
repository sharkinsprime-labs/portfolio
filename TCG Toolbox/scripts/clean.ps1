if (Test-Path ".\build") { Remove-Item ".\build" -Recurse -Force }
if (Test-Path ".\dist")  { Remove-Item ".\dist"  -Recurse -Force }
if (Test-Path ".\__pycache__") { Remove-Item ".\__pycache__" -Recurse -Force }

Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue