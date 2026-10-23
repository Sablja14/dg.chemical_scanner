$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvDir = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvDir
}

$pythonExe = Join-Path $venvDir "Scripts\python.exe"
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
& $pythonExe -m pip install pyinstaller

$distDir = Join-Path $PSScriptRoot "dist"
$buildDir = Join-Path $PSScriptRoot "build"

$running = Get-CimInstance Win32_Process -Filter "Name='ChemicalScanner.exe'" -ErrorAction SilentlyContinue
if ($running) {
    foreach ($process in $running) {
        Stop-Process -Id $process.ProcessId -Force
    }
    Start-Sleep -Seconds 1
}

if (Test-Path $distDir) { Remove-Item -Recurse -Force $distDir }
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }

Write-Host "Building Chemical Scanner executable..."
$iconPath = Join-Path $PSScriptRoot "assets\chemical_chemistry_laboratory_icon_192522.ico"
& $pythonExe -m PyInstaller `
    --windowed `
    --onefile `
    --clean `
    --name "ChemicalScanner" `
    --icon $iconPath `
    --distpath $distDir `
    --workpath $buildDir `
    --paths $PSScriptRoot `
    --collect-submodules scripts `
    --collect-all pandas `
    --collect-all pymupdf `
    --collect-all pypdf `
    --collect-all requests `
    --collect-all openpyxl `
    --hidden-import pandas `
    --hidden-import pandas._libs `
    --hidden-import numpy `
    --hidden-import pymupdf `
    --hidden-import pypdf `
    --hidden-import requests `
    --hidden-import openpyxl `
    --hidden-import tqdm `
    --add-data "scripts;scripts" `
    --add-data "assets;assets" `
    app.py

Write-Host "Build complete. Executable: $distDir\ChemicalScanner.exe"
