# GitHub Setup Guide for Chemical Scanner

## Step-by-Step: Publishing Chemical Scanner on GitHub

### Prerequisites
- GitHub account created
- Git installed on your PC
- Chemical Scanner files ready (this folder)

---

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click **+** icon (top right) → **New repository**
3. Fill in:
   - **Repository name:** `chemical-scanner` (or your choice)
   - **Description:** `Professional desktop app for scanning German chemical datasheets`
   - **Visibility:** Public (for sharing) or Private (for internal use)
4. **Do NOT** check "Initialize with README" (you already have one)
5. Click **Create repository**

---

## Step 2: Copy Repository URL

After creating repository:
1. Click **Code** button (green)
2. Copy the HTTPS URL (e.g., `https://github.com/yourusername/chemical-scanner.git`)
3. Save it somewhere - you'll need it in the next step

---

## Step 3: Push Code to GitHub

### On Windows (Using Command Prompt):

1. Open **Command Prompt** or **PowerShell**
2. Navigate to the project folder:
   ```
   cd C:\pdfscanner\chemical_scanner
   ```

3. Initialize Git (if not already done):
   ```
   git init
   ```

4. Add all files:
   ```
   git add .
   ```

5. Create initial commit:
   ```
   git commit -m "Initial commit: Chemical Scanner v1.0.0 - Professional desktop app for German chemical screening"
   ```

6. Add remote repository (replace URL with your own):
   ```
   git remote add origin https://github.com/yourusername/chemical-scanner.git
   ```

7. Push to GitHub:
   ```
   git branch -M main
   git push -u origin main
   ```

8. **Enter your GitHub credentials** when prompted

---

## Step 4: Create Release

### Via GitHub Website:

1. Go to your repository on GitHub
2. Click **Releases** (on the right sidebar)
3. Click **Create a new release** or **Draft a new release**
4. Fill in:

   **Tag version:** `v1.0.0`

   **Release title:** `Chemical Scanner v1.0.0 - Initial Release`

   **Description:** Copy from [RELEASE_TEMPLATE.md](RELEASE_TEMPLATE.md)

   **Attach binaries:**
   - Click "Attach binaries"
   - Select and upload:
     - `ChemicalScanner.exe` (121.7 MB)
     - `ChemicalScanner_Portable.zip` (120.9 MB)

5. Click **Publish release**

---

## Step 5: Share with Users

Once published, users can access your app via:
```
https://github.com/yourusername/chemical-scanner/releases/tag/v1.0.0
```

They can download either:
- **ChemicalScanner.exe** - Single file, double-click to run
- **ChemicalScanner_Portable.zip** - Extract and run

---

## What Gets Pushed to GitHub

✅ **These files are pushed:**
- app.py
- scripts/pdf_chemical_scan.py
- build_installer.ps1
- requirements.txt
- README.md
- QUICKSTART.md
- INSTALL.txt
- DISTRIBUTION.md
- RELEASE_TEMPLATE.md
- .gitignore

❌ **These are excluded (per .gitignore):**
- dist/ (binaries)
- .venv/ (Python environment)
- __pycache__/ (Python cache)
- *.pyc files
- results/ folder
- Any test data files

---

## After First Release

### For Updates (v1.0.1, v2.0.0, etc.):

1. Make code changes locally
2. Rebuild:
   ```
   cd C:\pdfscanner\chemical_scanner
   .\build_installer.ps1
   ```
3. Commit changes:
   ```
   git add .
   git commit -m "Update: Fix issue XYZ"
   git push origin main
   ```
4. Create new release on GitHub with updated binaries

---

## Optional: Enable GitHub Pages (Documentation)

To host documentation at `yourusername.github.io/chemical-scanner`:

1. On GitHub, go to **Settings** → **Pages**
2. Select **Source:** `main` branch, `/root` folder
3. Your README.md will be displayed as the homepage

---

## Optional: Add License

To add an open-source license:

1. On GitHub, click **Add file** → **Create new file**
2. Name it: `LICENSE`
3. Click **Choose a license template**
4. Select one:
   - **MIT License** (popular, permissive)
   - **Apache 2.0** (includes patent protection)
   - **GPL v3** (requires derivative works to be open-source)
5. Commit with message: `Add MIT License`

---

## Troubleshooting

### Git not found?
- Install Git from [git-scm.com](https://git-scm.com)
- Restart Command Prompt after installing

### "fatal: not a git repository"?
- Make sure you ran `git init` in the correct folder
- Check you're in `C:\pdfscanner\chemical_scanner`

### "Authentication failed"?
- GitHub may require Personal Access Token (PAT) instead of password
- Create one: GitHub Settings → Developer settings → Personal access tokens
- Use token instead of password when prompted

### Files not showing on GitHub?
- Check `.gitignore` - some files might be excluded
- Run `git status` to see what's staged
- Make sure you ran `git push`

### Need to update release files?
- Can't edit already-uploaded binaries
- Instead: Delete old release, create new one with v1.0.1 tag

---

## File Size Reference

- **ChemicalScanner.exe:** 121.7 MB (includes Python runtime + all dependencies)
- **ChemicalScanner_Portable.zip:** 120.9 MB (EXE + README + launcher)
- **Total source code:** ~40 KB (compressed)

GitHub allows releases up to several GB, so size is not a concern.

---

## Support & Feedback

After publishing, you can:

1. **Track issues:** GitHub Issues tab for bug reports
2. **Accept pull requests:** For community contributions
3. **Add wiki:** GitHub Wiki for detailed guides
4. **Monitor releases:** Track download counts and user feedback

---

## Example GitHub URLs

Once published, your app will be at:

- **Repository:** `https://github.com/yourusername/chemical-scanner`
- **Release v1.0.0:** `https://github.com/yourusername/chemical-scanner/releases/tag/v1.0.0`
- **Download EXE:** `https://github.com/yourusername/chemical-scanner/releases/download/v1.0.0/ChemicalScanner.exe`
- **Download ZIP:** `https://github.com/yourusername/chemical-scanner/releases/download/v1.0.0/ChemicalScanner_Portable.zip`

---

## Next Steps

1. ✅ Follow steps 1-5 above
2. ✅ Test that users can download and run the app
3. ✅ Share GitHub link with team/users
4. ✅ Monitor feedback via Issues
5. ✅ Plan updates based on user feedback

---

**Your Chemical Scanner is ready for the world! 🚀**
