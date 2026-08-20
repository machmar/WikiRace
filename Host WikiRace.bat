@echo off
REM Host a game for people who haven't installed anything.
REM They just open the printed link in a browser.
setlocal
cd /d "%~dp0"
call "%~dp0Play WikiRace.bat" --host %*
endlocal
