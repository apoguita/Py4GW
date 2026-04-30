@echo off
setlocal

set "ROOT=%~dp0"

echo Cleaning Python cache files under:
echo %ROOT%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "$root = '%ROOT%';" ^
  "$items = Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'pyache|pycache|__pycache__' -or $_.Extension -in '.pyc', '.pyo' };" ^
  "$count = @($items).Count;" ^
  "if ($count -eq 0) { Write-Host 'No Python cache files found.'; exit 0 }" ^
  "$items | Sort-Object FullName -Descending | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction Stop };" ^
  "Write-Host ('Deleted {0} Python cache item(s).' -f $count)"

echo.
if /i not "%~1"=="/nopause" pause
