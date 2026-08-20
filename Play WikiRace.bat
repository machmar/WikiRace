@echo off
setlocal
title WikiRace
cd /d "%~dp0"

call :findpython
if not "%PYCMD%"=="" goto :play

echo.
echo   Python isn't set up on this machine yet - doing that first.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 goto :failed

call :findpython
if "%PYCMD%"=="" goto :failed

:play
%PYCMD% wikirace.py %*
goto :done

:failed
echo.
echo   Couldn't start the game. Run 'Setup.bat' and read what it reports.
echo.
pause
goto :done

REM Pick the first interpreter that is really Python 3.8+. The bare "python"
REM on a clean Windows install is a Microsoft Store stub that answers nothing,
REM so each candidate has to prove its version before we trust it.
:findpython
set "PYCMD="
for %%C in ("py -3" "python" "python3") do (
    if "%PYCMD%"=="" (
        %%~C -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
        if not errorlevel 1 set "PYCMD=%%~C"
    )
)
exit /b 0

:done
endlocal
