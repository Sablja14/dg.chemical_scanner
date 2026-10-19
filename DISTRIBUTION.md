# Chemical Scanner - Distribution Guide

## Quick Start

There are two ways to distribute the Chemical Scanner app:

### **Option 1: Standalone EXE (Simplest)**
- File: `dist/ChemicalScanner.exe` (~127 MB)
- Share directly with users
- No installation needed
- Just double-click to run

### **Option 2: Portable ZIP (For GitHub Releases)**
- File: `dist/ChemicalScanner_Portable.zip`
- Includes the EXE + README + Launch script
- User unzips and runs immediately
- Professional presentation

### **Option 3: Windows Installer (Requires NSIS)**
- File: `dist/ChemicalScannerSetup.exe`
- Traditional installation experience
- Creates Start Menu shortcuts
- Adds to Add/Remove Programs
- Requires NSIS to build (see below)

---

## Building the Portable ZIP

```powershell
cd C:\pdfscanner\chemical_scanner\installer
.\build_portable.ps1
```

Or run the batch file:
```cmd
cd C:\pdfscanner\chemical_scanner\installer
build_portable.bat
```

Output: `dist/ChemicalScanner_Portable.zip` (~127 MB)

---

## Building the Windows Installer (Optional)

To create a professional Windows installer (.exe setup file):

### Step 1: Install NSIS

**Option A: Using Chocolatey (Recommended)**
```powershell
choco install nsis
```

**Option B: Manual Download**
Download from: https://nsis.sourceforge.io/Download

### Step 2: Build the Installer

```powershell
cd C:\pdfscanner\chemical_scanner\installer
.\build_installer.ps1
```

Output: `dist/ChemicalScannerSetup.exe` (~2-3 MB)

---

## GitHub Release Setup

### Recommended Files to Upload:

1. **ChemicalScanner_Portable.zip** ← Easy for users
   - Unzip and run
   - No installation needed
   - Best for casual users

2. **ChemicalScanner.exe** ← Direct download
   - Single file
   - Minimalist approach
   - Works immediately

3. **ChemicalScannerSetup.exe** (if you build it)
   - Traditional Windows installer
   - Creates shortcuts
   - Professional feel

### GitHub Release Instructions:

1. Create a new Release on GitHub
2. Tag: `v1.0.0` (or your version)
3. Upload the ZIP and EXE files
4. Add release notes with:
   ```markdown
   ## Chemical Scanner v1.0.0

   ### Downloads:
   - **ChemicalScanner_Portable.zip** - Portable version (extract and run)
   - **ChemicalScanner.exe** - Standalone executable

   ### System Requirements:
   - Windows 7 or later
   - No Python installation needed
   - No additional software required

   ### Quick Start:
   1. Download the ZIP or EXE
   2. Extract (if ZIP) or just double-click (if EXE)
   3. Select your CSV/Excel file with PDF links
   4. Map your columns
   5. Click Scan

   ### Features:
   - Scans German SDS/product datasheets for chemical keywords
   - Supports CSV and Excel files
   - Generates CSV report with findings
   - Counts keyword occurrences
   - Professional GUI interface
   ```

---

## Version Updates

To create updated releases:

1. Update code as needed
2. Rebuild the EXE:
   ```powershell
   cd C:\pdfscanner\chemical_scanner
   & .\build_installer.ps1
   ```
3. Rebuild portable ZIP:
   ```powershell
   cd C:\pdfscanner\chemical_scanner\installer
   .\build_portable.ps1
   ```
4. Upload new files to GitHub Release

---

## Troubleshooting

### Users see "Windows Defender SmartScreen" warning
This is normal for unsigned executables. Users can click "More info" → "Run anyway"

To remove this warning, you would need to:
- Get a code-signing certificate (~$200-400/year)
- Sign the EXE with the certificate

### File size is large (~127 MB)
This is expected - it includes:
- Python runtime
- All dependencies (pandas, pymupdf, etc.)
- PyInstaller bundler overhead

The ZIP compresses it to ~30-40 MB.

### EXE takes time to start on first run
PyInstaller extracts bundled files on first launch. Subsequent runs are faster.

---

## System Requirements

- **OS:** Windows 7, 8, 10, 11
- **Architecture:** 64-bit
- **RAM:** 512 MB minimum (1 GB recommended)
- **Disk Space:** 200 MB for extraction + space for PDFs
- **Internet:** Required for downloading PDFs from URLs

---

## Support

For issues, questions, or feature requests:
- Create an issue on GitHub
- Include the error message and CSV file format you're using
