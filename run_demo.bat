@echo off
setlocal
set "BASEDIR=%~dp0"

:: Try to locate python
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Python found, installing requirements and running demo.py…
    python -m pip install -r "%BASEDIR%requirements.txt"
    python "%BASEDIR%demo.py"
) else (
    echo Python not found, running bundled EXE…
    "%BASEDIR%dist\demo.exe"
)