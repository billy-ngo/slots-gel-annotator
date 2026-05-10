@echo off
REM ─────────────────────────────────────────────────────────────────
REM   Slots Gel Annotator — release wrapper for Windows.
REM   Lets you type:
REM     release 1.0.1
REM     release --patch
REM     release --minor -m "fix something"
REM   instead of `python scripts/release.py ...`. All args are
REM   forwarded verbatim to the Python script.
REM ─────────────────────────────────────────────────────────────────
SETLOCAL
SET "PY="
where py >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
    SET "PY=py -3"
) ELSE (
    where python >NUL 2>&1
    IF %ERRORLEVEL% EQU 0 (
        SET "PY=python"
    ) ELSE (
        echo ERROR: Python not found on PATH.
        EXIT /B 1
    )
)
%PY% "%~dp0scripts\release.py" %*
ENDLOCAL
EXIT /B %ERRORLEVEL%
