# Quick Start Guide

**Get Chemical Scanner running in 2 minutes**

## Step 1: Download (30 seconds)

Go to [Releases](https://github.com/yourusername/chemical-scanner/releases)

Click **ChemicalScanner_Portable.zip** to download (~121 MB)

## Step 2: Extract (30 seconds)

- Right-click **ChemicalScanner_Portable.zip**
- Choose **Extract All...**
- Select a folder (e.g., Desktop, Documents)
- Click **Extract**

You'll get:
- ✓ ChemicalScanner.exe (the app)
- ✓ README.txt (instructions)
- ✓ Launch.bat (quick launcher)

## Step 3: Run (5 seconds)

**Option A:**
- Double-click **ChemicalScanner.exe**

**Option B:**
- Double-click **Launch.bat**

**First run:** Takes 5-10 seconds (normal). Subsequent runs are faster.

## Step 4: Use the App (60 seconds)

### 4a. Load Your File
1. Click **Browse** button
2. Select your CSV or Excel file
3. Wait for "File loaded" message

**Your file must have:**
- Column with Product IDs (e.g., "ProductId")
- Column with PDF URLs (e.g., "Url")

### 4b. Map Columns
1. **Product ID Column** - Pick from dropdown (e.g., "ProductId")
2. **PDF URL Column** - Pick from dropdown (e.g., "Url")
3. See the mapping display at bottom

### 4c. Choose Output Location
1. Click **Select Output Folder**
2. Pick where to save results (e.g., Desktop)

### 4d. Scan
1. Click **Scan** button
2. Wait for "Scan complete" message
3. Results CSV opens automatically

## That's It! 🎉

Your results are saved as CSV file ready to open in Excel.

---

## Example CSV File

Create a file named `products.csv`:

```
ProductId,Url
CHEM-001,https://www.example.com/datasheet1.pdf
CHEM-002,https://www.example.com/datasheet2.pdf
CHEM-003,https://www.example.com/datasheet3.pdf
```

Then load it into Chemical Scanner.

---

## Output File

You'll get a CSV with columns:

| ProductId | chemical_keywords_found | chemicals_found | keyword_occurrences |
|-----------|----------------------|-----------------|-------------------|
| CHEM-001 | Yes | Isopropanol | Isopropanol:5 |
| CHEM-002 | No | | |
| CHEM-003 | Yes | Nagellack | Nagellack:3 |

Open it with Excel or any spreadsheet program.

---

## Troubleshooting

### Q: App won't start
**A:** Try double-clicking `Launch.bat` instead

### Q: "Windows Defender" warning appears
**A:** Click "More info" → "Run anyway" (normal for unsigned apps)

### Q: App takes forever
**A:** Check internet connection (PDFs are downloaded from URLs)

### Q: "File could not be read"
**A:** Make sure it's a CSV or Excel file (.csv, .xlsx, .xls)

### Q: No keywords found
**A:** PDF might be in English or an image. Try a German datasheet.

### Q: Can't find my column
**A:** Column names must match exactly. Check spelling and spacing.

---

## Need Help?

1. Check [README.md](./README.md) for more details
2. See [DISTRIBUTION.md](./DISTRIBUTION.md) for technical info
3. Open a GitHub Issue with error details

---

**That's all!** Happy scanning! 🔬
