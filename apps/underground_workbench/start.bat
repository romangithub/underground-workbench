@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "BIN=%ROOT%bin"
set "MF6_VERSION=6.7.0"
set "MF6_ASSET=mf6.7.0_win64.zip"
set "MF6_URL=https://github.com/MODFLOW-ORG/modflow6/releases/download/6.7.0/mf6.7.0_win64.zip"
set "MF6_TARGET=%BIN%\mf6.windows-x86_64.exe"

if not exist "%BIN%" mkdir "%BIN%"

if defined MF6_BIN (
  if not exist "%MF6_BIN%" (
    echo ERROR: MF6_BIN is set but does not exist: "%MF6_BIN%" 1>&2
    exit /b 44
  )
  set "MF6=%MF6_BIN%"
  goto :verify_mf6
)

set "NATIVE_ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "NATIVE_ARCH=%PROCESSOR_ARCHITEW6432%"
if /I not "%NATIVE_ARCH%"=="AMD64" (
  echo ERROR: Unsupported Windows architecture: %NATIVE_ARCH%. Need win64. 1>&2
  exit /b 44
)

if not exist "%MF6_TARGET%" (
  where powershell.exe >nul 2>nul
  if errorlevel 1 (
    echo ERROR: powershell.exe required for first MODFLOW download. 1>&2
    exit /b 44
  )

  echo Downloading USGS MODFLOW %MF6_VERSION%: %MF6_ASSET% 1>&2
  echo URL: %MF6_URL% 1>&2

  set "MF6_TMP=%TEMP%\uw_mf6_%RANDOM%"

  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$tmp=$env:MF6_TMP; $url=$env:MF6_URL; $target=$env:MF6_TARGET;" ^
    "try {" ^
    "  New-Item -ItemType Directory -Force -Path $tmp | Out-Null;" ^
    "  $zip=Join-Path $tmp 'mf6.zip'; $out=Join-Path $tmp 'out';" ^
    "  Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $zip;" ^
    "  Expand-Archive -LiteralPath $zip -DestinationPath $out -Force;" ^
    "  $found=Get-ChildItem -LiteralPath $out -Filter 'mf6.exe' -File -Recurse | Select-Object -First 1;" ^
    "  if (-not $found) { throw 'mf6.exe not found in downloaded archive' };" ^
    "  Copy-Item -LiteralPath $found.FullName -Destination $target -Force;" ^
    "} finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue } }"

  if errorlevel 1 (
    echo ERROR: Failed to download or extract MODFLOW %MF6_VERSION%. 1>&2
    exit /b 44
  )
)

set "MF6=%MF6_TARGET%"

:verify_mf6
"%MF6%" -v >nul 2>nul
if errorlevel 1 (
  echo ERROR: MODFLOW executable failed version check: "%MF6%" 1>&2
  exit /b 44
)

set "MF6_BIN=%MF6%"
if not defined PORT set "PORT=18888"

echo UNDERGROUND Workbench -^> http://127.0.0.1:%PORT% 1>&2
echo MF6: %MF6_BIN% 1>&2

cd /d "%ROOT%"
where py.exe >nul 2>nul
if not errorlevel 1 goto :run_py

where python.exe >nul 2>nul
if not errorlevel 1 goto :run_python

echo ERROR: Python 3 not found (need py.exe or python.exe in PATH). 1>&2
exit /b 44

:run_py
py -3 "%ROOT%api_server.py"
exit /b %ERRORLEVEL%

:run_python
python "%ROOT%api_server.py"
exit /b %ERRORLEVEL%
