@echo off
setlocal
set "BASEDIR=%~dp0"

:: Try to locate python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found, running bundled EXE...
    goto :RunExe
)

echo Python found. Identifying python version.
:: grab the full version string into PY_VERSION
for /f "tokens=2 delims= " %%A in ('python --version 2^>^&1') do set "PY_VERSION=%%A"

:: split into major & minor
for /f "tokens=1,2 delims=." %%M in ("%PY_VERSION%") do (
    set "PY_MAJOR=%%M"
    set "PY_MINOR=%%N"
)

echo Major version: %PY_MAJOR%
echo Minor version: %PY_MINOR%

:: Require at least Python 3.11
if "%PY_MAJOR%"=="3" (
    if %PY_MINOR% GEQ 11 (
        echo Detected compatible Python version: %PY_MAJOR%.%PY_MINOR%
        goto :RunPython
    ) else (
        echo Detected incompatible Python version: %PY_MAJOR%.%PY_MINOR% — too old (needs ≥ 3.11)
        goto :RunExe
    )
) else (
    echo Detected incompatible Python version: %PY_MAJOR%.%PY_MINOR% — too old (needs ≥ 3.11)
    goto :RunExe
)

::goto for running the app with python
:RunPython
python -m pip install -r "%BASEDIR%requirements.txt"
python "%BASEDIR%demo.py"

goto :End

::goto for running the app through the exe
:RunExe
"%BASEDIR%dist\demo.exe"
goto :End

:End
pause
