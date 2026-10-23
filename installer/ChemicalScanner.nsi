; Chemical Scanner Installer
; NSIS Configuration

!include "MUI2.nsh"
!include "x64.nsh"

; Name and file
Name "Chemical Scanner"
OutFile "..\dist\ChemicalScannerSetup.exe"
Icon "..\assets\chemical_chemistry_laboratory_icon_192522.ico"
UninstallIcon "..\assets\chemical_chemistry_laboratory_icon_192522.ico"

; Default installation folder
InstallDir "$PROGRAMFILES\ChemicalScanner"

; Get installation folder from registry if available
InstallDirRegKey HKCU "Software\ChemicalScanner" ""

; Request application privileges for Windows Vista and higher
RequestExecutionLevel admin

;--------------------------------
; MUI Settings
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections
;--------------------------------
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy the main executable
  File "..\dist\ChemicalScanner.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Store installation folder in registry
  WriteRegStr HKCU "Software\ChemicalScanner" "" $INSTDIR
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\ChemicalScanner"
  CreateShortcut "$SMPROGRAMS\ChemicalScanner\Chemical Scanner.lnk" "$INSTDIR\ChemicalScanner.exe"
  CreateShortcut "$SMPROGRAMS\ChemicalScanner\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create Desktop shortcut (optional, commented out by default)
  ; CreateShortcut "$DESKTOP\Chemical Scanner.lnk" "$INSTDIR\ChemicalScanner.exe"
  
  ; Add to Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "DisplayName" "Chemical Scanner"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "DisplayVersion" "1.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "DisplayIcon" "$INSTDIR\ChemicalScanner.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "Publisher" "Chemical Scanner"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "URLInfoAbout" "https://github.com/yourusername/chemical-scanner"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner" "NoRepair" 1
  
SectionEnd

;--------------------------------
; Uninstaller Section
;--------------------------------
Section "Uninstall"
  ; Remove files
  Delete "$INSTDIR\ChemicalScanner.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  
  ; Remove Start Menu shortcuts
  Delete "$SMPROGRAMS\ChemicalScanner\Chemical Scanner.lnk"
  Delete "$SMPROGRAMS\ChemicalScanner\Uninstall.lnk"
  RMDir "$SMPROGRAMS\ChemicalScanner"
  
  ; Remove Desktop shortcut if it exists
  Delete "$DESKTOP\Chemical Scanner.lnk"
  
  ; Remove registry keys
  DeleteRegKey HKCU "Software\ChemicalScanner"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemicalScanner"
  
SectionEnd

;--------------------------------
; Function to run the app after installation
;--------------------------------
Function .onInstSuccess
  MessageBox MB_YESNO "Installation complete. Launch Chemical Scanner now?" IDNO end
    Exec "$INSTDIR\ChemicalScanner.exe"
  end:
FunctionEnd
