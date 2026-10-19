# GitHub Release Template

Use this template when creating a new release on GitHub.

## Release Information

- **Tag:** `v1.0.0`
- **Title:** `Chemical Scanner v1.0.0`

## Release Notes

```markdown
## Chemical Scanner v1.0.0 - Production Release

### 🎉 What's New

First production release of Chemical Scanner - a professional Windows desktop application for screening German-language product datasheets.

### ✨ Features

- **Batch Processing** - Scan entire CSV/Excel files with one click
- **German Keywords** - 200+ chemical keywords for EU compliance
- **Automatic PDF Download** - Downloads datasheets from URLs automatically
- **Keyword Counting** - Shows occurrence count for each chemical
- **Professional GUI** - Clean, intuitive Windows desktop interface
- **CSV Reports** - Detailed export with all findings
- **Multi-threaded** - Fast parallel processing for speed
- **No Installation Required** - Standalone executable, no dependencies

### 📥 Downloads

Choose your preferred format:

1. **ChemicalScanner_Portable.zip** (121 MB) ← **RECOMMENDED**
   - Extract and run immediately
   - No installation needed
   - Best for most users

2. **ChemicalScanner.exe** (127 MB)
   - Single file download
   - Same as ZIP, without extraction
   - Alternative for direct download preference

### 🚀 Quick Start

1. Download the ZIP or EXE
2. Extract (if ZIP) or skip (if EXE)
3. Double-click **ChemicalScanner.exe**
4. Load your CSV/Excel file with product data
5. Map columns (Product ID and PDF URL)
6. Click **Scan** and wait for completion
7. Results open automatically in CSV format

### 💻 System Requirements

- **OS:** Windows 7, 8, 10, or 11 (64-bit)
- **RAM:** 512 MB minimum (1 GB recommended)
- **Disk:** 200 MB + space for downloaded PDFs
- **Internet:** Required for downloading PDFs
- **Python:** NOT required (included in the app)

### 📊 Input & Output

**Input Format (CSV/Excel):**
```
ProductId,Url
CHEM-001,https://example.com/datasheet.pdf
CHEM-002,https://example.com/datasheet2.pdf
```

**Output Report (CSV):**
```
ProductId,chemical_keywords_found,chemicals_found,keyword_occurrences
CHEM-001,Yes,Isopropanol; Nagellack,Isopropanol:5; Nagellack:2
CHEM-002,No,,
```

### 🔍 Chemical Keywords

Searches for 200+ German chemical terms:
- Solvents: Isopropanol, Salzsäure, Ammoniak
- Sprays: Kontaktspray, Frostspray, Insektenspray
- Adhesives: Sekundenkleber, Epoxidharz, Lötpaste
- Specialty: Nagellack, Blondierpulver, Motoröl
- And many more...

### 📋 Key Features

- ✅ Automatic PDF download from URLs
- ✅ German text extraction and analysis
- ✅ Keyword occurrence counting
- ✅ Batch processing (test 10 or scan 1000+)
- ✅ Professional GUI with progress feedback
- ✅ Detailed CSV reports with all findings
- ✅ Multi-threaded scanning for speed
- ✅ Responsive interface - no freezing

### 🛠️ Technical Details

- Built with Python + Tkinter GUI
- Bundled with PyInstaller for standalone distribution
- Uses pymupdf/pypdf for PDF extraction
- Parallel processing with ThreadPoolExecutor
- No Python installation needed on user machines

### 🐛 Known Issues & Workarounds

**Windows Defender SmartScreen Warning**
- Normal for unsigned executables
- Click "More info" → "Run anyway"
- To remove: Would require code-signing certificate (~$300/year)

**First Run Takes 5-10 Seconds**
- PyInstaller extracts bundled files on first launch
- Subsequent runs are much faster

**Some PDFs Fail to Download**
- Check internet connection
- Verify URLs are accessible in browser
- Some PDFs may be behind authentication
- Try increasing timeout in settings (advanced)

**No Keywords Found in PDF**
- PDF might be English or image-based (scanned)
- Check that PDF has selectable text
- Try with a different German datasheet

### 📚 Documentation

- **[README.md](https://github.com/yourusername/chemical-scanner/blob/main/README.md)** - Full documentation and features
- **[QUICKSTART.md](https://github.com/yourusername/chemical-scanner/blob/main/QUICKSTART.md)** - 2-minute quick start guide
- **[DISTRIBUTION.md](https://github.com/yourusername/chemical-scanner/blob/main/DISTRIBUTION.md)** - Technical deployment info

### 🤝 Support

For issues, questions, or suggestions:
1. Read [README.md](./README.md) troubleshooting section
2. Check existing [Issues](https://github.com/yourusername/chemical-scanner/issues)
3. Open a new Issue with:
   - Windows version
   - Error message (if any)
   - Steps to reproduce
   - Sample CSV format

### 📝 Changelog

**v1.0.0** (First Release)
- Initial production release
- Professional GUI interface
- 200+ German chemical keywords
- Batch CSV/Excel processing
- PDF automatic download and extraction
- Detailed CSV reporting
- Multi-threaded scanning
- Standalone Windows distribution

### 🎯 What's Next?

Potential future improvements:
- Add more specialized keywords
- Windows installer (.msi) package
- OCR support for scanned PDFs
- Multi-language support
- Advanced report filtering

### 📄 License

[Your License Here - MIT, GPL, Apache 2.0, etc.]

### ✍️ Author

[Your Name/Organization]

---

**Download Now:** Get [ChemicalScanner_Portable.zip](https://github.com/yourusername/chemical-scanner/releases/download/v1.0.0/ChemicalScanner_Portable.zip) and start scanning!

**File Size:** ~121 MB (ZIP), ~127 MB (EXE)  
**Release Date:** October 19, 2026  
**Compatibility:** Windows 7 / 8 / 10 / 11 (64-bit)
```

---

## Steps to Create Release

1. Go to your GitHub repository
2. Click **Releases** (top right area)
3. Click **Create a new release** (or "Draft a new release")
4. Fill in:
   - **Tag:** `v1.0.0`
   - **Title:** `Chemical Scanner v1.0.0`
   - **Description:** Copy the markdown above
5. Click **Attach binaries** and upload:
   - `ChemicalScanner_Portable.zip`
   - `ChemicalScanner.exe`
6. Review everything
7. Click **Publish release**

## Alternative: Release Without Pre-release Tag

If you want to mark it as pre-release during testing:
- Check "This is a pre-release" before publishing
- Later uncheck it when ready for production

## Updating the README

After publishing, add this link to your main README:

```markdown
## Download

Get the latest version: [Chemical Scanner v1.0.0](https://github.com/yourusername/chemical-scanner/releases/tag/v1.0.0)

### Download Files:
- **ChemicalScanner_Portable.zip** (121 MB) - Extract and run
- **ChemicalScanner.exe** (127 MB) - Single executable

See [Releases](https://github.com/yourusername/chemical-scanner/releases) for all versions.
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- `v1.0.0` - First stable release
- `v1.0.1` - Bug fix (patch)
- `v1.1.0` - New feature (minor)
- `v2.0.0` - Breaking change (major)

## Release Checklist

- [ ] Code is complete and tested
- [ ] All documentation updated
- [ ] EXE rebuilt with latest code
- [ ] ZIP package created
- [ ] Release notes written
- [ ] GitHub Release created
- [ ] README links updated
- [ ] Announced to users/team

---

**That's all!** Your first GitHub release is ready! 🚀
