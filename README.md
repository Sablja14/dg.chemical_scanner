# Chemical Scanner

A Windows desktop application for screening German-language product datasheets (SDS/PDF files) against regulated chemical keywords. Designed for compliance screening and product safety analysis.

## 🎯 Features

- **German Chemical Keywords** - 200+ German chemical keywords for EU/German product compliance
- **Batch Processing** - Scan entire CSV/Excel files with one click
- **PDF Download** - Automatically downloads and processes PDF files from URLs
- **Keyword Counting** - Shows how many times each keyword appears in each document
- **Professional User-Interface** - Clean, intuitive desktop interface
- **CSV Export** - Detailed reports with all findings
- **No Setup Required** - Self-contained executable, no Python installation needed
- **Multi-threaded** - Scans multiple PDFs in parallel for speed

## 📥 Download

### Latest Release

Choose your preferred format (Both versions requires you to unblock them from SmartScreen warnings -> Right Click -> And on attributes click "UNBLOCK") :

1. **ChemicalScanner_Portable.zip** (121 MB) - **Recommended**
   - Extract and run immediately
   - No installation needed
   - Everything included

2. **ChemicalScanner.exe** (127 MB)
   - Single file download
   - Double-click to launch
   - Direct execution

Get the latest version from [Releases](https://github.com/yourusername/chemical-scanner/releases)

## 🚀 Quick Start

### Step 1: Download
- Get **ChemicalScanner_Portable.zip** from Releases

### Step 2: Extract
- Extract the ZIP to any folder
- You'll get: ChemicalScanner.exe, README.txt, Launch.bat

### Step 3: Run
- Double-click **ChemicalScanner.exe**

### Step 4: Scan
1. Click **"Browse"** and select your CSV/Excel file
2. Map columns:
   - Select which column has Product IDs
   - Select which column has PDF URLs
3. Click **"Select Output Folder"** and choose where to save results
4. Click **"Scan"** and wait for completion
5. Results open automatically in CSV format

## 📋 Input File Format

Your CSV or Excel file should have these columns:

| ProductId | ProductName | Url |
|-----------|------------|-----|
| CHEM-001 | Cleaner Pro | https://example.com/chem001.pdf |
| CHEM-002 | Polish XYZ | https://example.com/chem002.pdf |

**The app will:**
1. Download each PDF from the URL
2. Extract text from it
3. Search for German chemical keywords
4. Generate a detailed report

## 📊 Output Report

The app generates a CSV with these columns:

| Column | Description |
|--------|-------------|
| ProductId | Your product identifier |
| chemical_keywords_found | "Yes" or "No" |
| chemicals_found | List of keywords found |
| keyword_occurrences | Count per keyword (e.g., "Isopropanol:5; Nagellack:2") |
| pdf_url | Original URL processed |
| keywords_phrases | Text snippets containing keywords |
| status | Processing status |

## ✨ Chemical Keywords

Searches for 200+ German chemical terms including:

**Sprays & Solvents:**
- Isopropanol, Kontaktspray, Frostspray, Druckluftspray

**Soldering Materials:**
- Lötfett, Lötpaste, Lötwasser, Flussmittel

**Acids & Bases:**
- Salzsäure, Natronlauge, Ammoniak, Ätzmittel

**Specialty Chemicals:**
- Blondierpulver, Nagellack, Duftöl, Motoröl

See complete list in [pdf_chemical_scan.py](./chemical_scanner/scripts/pdf_chemical_scan.py#L36)

To modify the app:

### Requirements
- Python 3.8 or higher
- Windows 7 or later

### Setup

`ash
cd chemical_scanner

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
`

### Run GUI (Development)

`ash
python app.py
`

### Build Standalone EXE

`ash
.\build_installer.ps1
`

Creates dist\ChemicalScanner.exe (~127 MB)

### Build Portable ZIP

`ash
cd installer
.\build_portable.ps1
`

Creates dist\ChemicalScanner_Portable.zip (~121 MB)

## 📁 Project Structure

`
chemical_scanner/
├── app.py                      # Main GUI application (Tkinter)
├── scripts/
│   └── pdf_chemical_scan.py    # Core scanning logic
├── build_installer.ps1         # Build EXE script
├── requirements.txt            # Python dependencies
├── installer/
│   ├── ChemicalScanner.nsi    # NSIS installer config
│   ├── build_installer.ps1    # NSIS build script
│   └── build_portable.ps1     # Portable ZIP builder
└── dist/
    ├── ChemicalScanner.exe            # Standalone executable
    └── ChemicalScanner_Portable.zip   # Portable version
`

## 🔧 Dependencies

- **pymupdf** - PDF text extraction
- **pypdf** - Alternative PDF extraction
- **pandas** - CSV/Excel file handling
- **requests** - HTTP PDF downloads
- **tkinter** - GUI framework (built-in with Python)
- **openpyxl** - Excel file support
- **tqdm** - Progress bars

## 🐛 Troubleshooting

### "Windows Defender SmartScreen" Warning
UNBLOCK the app in properties when right clicking the .exe

The warning appears because the EXE isn't code-signed (Code signing costs 300 EUR). 

### App Takes 5-10 Seconds to Start
**Normal on first run** - PyInstaller extracts bundled files. Subsequent launches are much faster.

### PDF Downloads Fail
- Check your internet connection
- Verify the URL works in your browser
- Try increasing timeout in code (change 	imeout=30 to 	imeout=60)
- Some PDFs may be behind authentication or firewall-blocked
- Contact Scraping Manager Team

### Excel Files Won't Load
- Use .xlsx or .xls extension
- Ensure headers are in the first row
- Try converting to CSV and importing

### No Keywords Found in German PDFs
- Verify the PDF contains searchable text (not scanned images)
- Check that it's actually in German
- Try a different PDF to test

### Column Mapping Error
- Make sure your CSV has the columns you're trying to select
- Column names are case-sensitive
- Try re-saving the file as CSV if using Excel

## 📄 License

[Add your license: MIT, GPL, Apache 2.0, etc.]

## 🤝 Contributing

Contributions welcome!

- **Bug reports:** Open an issue with error details and CSV format
- **Feature requests:** Suggest new keywords or functionality
- **Code:** Fork, modify, and submit a pull request
- **Documentation:** Help improve guides and README

## 📧 Support & Issues

**For help:**

1. Check [Troubleshooting](#-troubleshooting) section above
2. Search existing [GitHub Issues](https://github.com/yourusername/chemical-scanner/issues)
3. Create a new issue with:
   - Windows version
   - Error message/screenshot
   - Steps to reproduce
   - Sample CSV format

## 🎓 How It Works Behind the Scenes

1. **Load Data** - Reads CSV/Excel with pandas
2. **Validate** - Checks for required columns
3. **Download PDFs** - Fetches files from URLs using requests + curl
4. **Extract Text** - Uses pymupdf/pypdf for text extraction
5. **Search Keywords** - Regex search against 200+ German terms
6. **Count Occurrences** - Tallies each keyword instance
7. **Generate Report** - Creates comprehensive CSV results
8. **Display Results** - Shows preview table and exports file

All processing is multi-threaded for speed and keeps the UI responsive.

---

**Version:** 1.0.0  
**Release Date:** October 2026  
**Compatible With:** Windows 7, 8, 10, 11 (64-bit)  
**License:** [Your License]  
**Author:** [Your Name/Organization]
