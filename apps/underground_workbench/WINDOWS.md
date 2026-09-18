# UNDERGROUND Workbench on Windows

## Requirements

- Windows x64
- Python 3 as `py -3` or `python`
- PowerShell (first MODFLOW download only)
- Internet for the first run

## Start

In `apps\underground_workbench`:

```bat
start.bat
```

First run downloads:

https://github.com/MODFLOW-ORG/modflow6/releases/download/6.7.0/mf6.7.0_win64.zip

Then opens http://127.0.0.1:18888

## Overrides

```bat
set "MF6_BIN=C:\path\to\mf6.exe"
start.bat
```

```bat
set "PORT=19000"
start.bat
```

## Notes

Automatic download is **x64 only**. `mf6.exe` is not bundled. Not runtime-tested on a physical Windows PC in this delivery.
