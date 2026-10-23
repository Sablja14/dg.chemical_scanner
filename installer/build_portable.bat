@echo off
REM Chemical Scanner - Create Portable ZIP
REM This script creates a portable ZIP distribution of the app

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%") do set "SCRIPT_DIR=%%~fI"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"
set "DIST_DIR=%ROOT_DIR%\dist"
set "EXE_PATH=%DIST_DIR%\ChemicalScanner.exe"
set "TEMP_DIR=%SCRIPT_DIR%ChemicalScanner_Portable"
set "ZIP_PATH=%DIST_DIR%\ChemicalScanner_Portable.zip"

cd /d "%SCRIPT_DIR%"

if not exist "%EXE_PATH%" (
    echo Error: ChemicalScanner.exe not found in %DIST_DIR%
    exit /b 1
)

echo Creating portable ZIP distribution...

REM Create a temporary folder
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

REM Copy the executable
copy "%EXE_PATH%" "%TEMP_DIR%\ChemicalScanner.exe" >nul
if errorlevel 1 (
    echo Error: Failed to copy ChemicalScanner.exe
    exit /b 1
)

REM Create a README
(
    echo Chemical Scanner - Portable Version
    echo ====================================
    echo.
    echo To use:
    echo 1. Extract this ZIP to any folder
    echo 2. Double-click ChemicalScanner.exe
    echo 3. Select your CSV/Excel file
    echo 4. Map columns and run scan
    echo.
    echo Requirements:
    echo - Windows 7 or later
    echo - No Python installation needed
    echo - No other software required
    echo.
    echo For updates and more info:
    echo https://github.com/yourusername/chemical-scanner
) > "%TEMP_DIR%\README.txt"

REM Create a batch file to launch the app
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo ChemicalScanner.exe
) > "%TEMP_DIR%\Launch.bat"

REM Create ZIP using PowerShell
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
tar -a -c -f "%ZIP_PATH%" "ChemicalScanner_Portable"

if errorlevel 1 (
    echo Error: Failed to create ZIP file
    rmdir /s /q "%TEMP_DIR%"
    exit /b 1
)

REM Clean up temporary folder
rmdir /s /q "%TEMP_DIR%"

REM Check file size
for %%A in ("%ZIP_PATH%") do set size=%%~zA
set /a size_mb=!size! / 1048576

echo.
echo ✓ Portable ZIP created successfully!
echo   Output: %ZIP_PATH%
echo   Size: !size_mb! MB
echo.
