$ErrorActionPreference = "Stop"

# Check if NSIS is installed
$nsis_path = "C:\Program Files (x86)\NSIS\makensis.exe"
if (-not (Test-Path $nsis_path)) {
    Write-Host "NSIS not found at $nsis_path"
    Write-Host ""
    Write-Host "To build the installer, install NSIS from:"
    Write-Host "  https://nsis.sourceforge.io/Download"
    Write-Host ""
    Write-Host "Or install via Chocolatey:"
    Write-Host "  choco install nsis"
    Write-Host ""
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$nsiFile = Join-Path $scriptDir "ChemicalScanner.nsi"

if (-not (Test-Path $nsiFile)) {
    Write-Host "ChemicalScanner.nsi not found"
    exit 1
}

Write-Host "Building installer with NSIS..."
& $nsis_path $nsiFile

if ($LASTEXITCODE -eq 0) {
    $setupExe = "C:\pdfscanner\chemical_scanner\dist\ChemicalScannerSetup.exe"
    if (Test-Path $setupExe) {
        $size = (Get-Item $setupExe).Length / 1MB
        Write-Host "✓ Installer created successfully!"
        Write-Host "  Output: $setupExe"
        Write-Host "  Size: $([math]::Round($size, 2)) MB"
    } else {
        Write-Host "✗ Installer output not found"
        exit 1
    }
} else {
    Write-Host "✗ NSIS compilation failed"
    exit 1
}
