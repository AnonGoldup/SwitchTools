@echo off
rem Build a standalone SwitchTools.exe with PyInstaller (output in dist\)
cd /d "%~dp0"

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller not found - installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

pyinstaller --noconfirm --clean --onefile --windowed --name SwitchTools app.py

if errorlevel 1 (
    echo Build FAILED.
) else (
    echo.
    echo Build complete: dist\SwitchTools.exe
)
pause
