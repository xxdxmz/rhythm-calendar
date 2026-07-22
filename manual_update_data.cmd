@echo off
setlocal
cd /d "%~dp0"
title Rhythm Calendar - Manual Data Update

echo Closing Codex before running this command is recommended.
echo Collecting Arcaea data and uploading it to GitHub...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update_public_data.ps1"
set "update_exit=%ERRORLEVEL%"

echo.
if "%update_exit%"=="0" (
    echo SUCCESS: Website data was updated and uploaded.
) else (
    echo FAILED: The update was not completed.
    echo Check data\logs\local-updater.log for details, then run this file again.
)
echo.
pause
exit /b %update_exit%
