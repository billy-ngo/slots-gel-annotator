@echo off
REM ===============================================================
REM   Slots Gel Annotator — Windows installer
REM   Installs the package from this source tree (editable mode)
REM   and launches the annotator. Re-run any time to update.
REM ===============================================================
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo  ==============================================
echo    Slots Gel Annotator -- installing
echo  ==============================================
echo.

REM Resolve a Python interpreter. py.exe is preferred on Windows;
REM fall back to "python" on PATH if absent.
set "PY="
where py >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY=py -3"
) else (
    where python >NUL 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY=python"
    ) else (
        echo  ERROR: Python 3.10+ not found on PATH.
        echo  Install Python from https://www.python.org/downloads/ then re-run this installer.
        pause
        exit /b 1
    )
)

REM Install / upgrade the package from this directory in editable mode
REM so that pulling new commits (`git pull`) reflects immediately.
echo  Running: %PY% -m pip install -U pip
%PY% -m pip install -U pip
if %ERRORLEVEL% NEQ 0 (
    echo  Pip self-upgrade failed. Continuing anyway.
)

echo.
echo  Running: %PY% -m pip install -e "%~dp0"
%PY% -m pip install -e "%~dp0"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  Install failed. Try:
    echo    %PY% -m pip install -e "%~dp0" --user
    pause
    exit /b 1
)

echo.
echo  Install OK. Launching Slots Gel Annotator...
echo.
%PY% -m gel_annotator
ENDLOCAL
