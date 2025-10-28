# Release Guide

## Build Release Packages

### 1. Single File Build (Portable)
```bash
build_onefile.bat
```

**Output:**
- `dist/onefile/ADBCopy.exe` (~100MB)
- `dist/onefile/ADBCopy_v0.1.0_Windows_Portable.zip`

**For:** Users who want single .exe file

---

### 2. Folder Build
```bash
build.bat
```

**Output:**
- `dist/folder/ADBCopy/` (folder with ADBCopy.exe + DLLs)
- `dist/folder/ADBCopy_v0.1.0_Windows.zip`

**For:** Users who prefer faster startup

---

## GitHub Release Steps

### 1. Commit and Tag
```bash
# Ensure all changes are committed
git add .
git commit -m "Release v0.1.0"

# Create tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial release"

# Push to GitHub
git push origin main
git push origin v0.1.0
```

### 2. Create GitHub Release

1. Go to: https://github.com/gerosyab/ADBCopy/releases/new
2. **Tag:** v0.1.0
3. **Title:** ADBCopy v0.1.0
4. **Description:**
   ```markdown
   # ADBCopy v0.1.0 - Initial Release
   
   A simple ADB file explorer with FileZilla-style UI.
   
   ## Features
   - Dual-panel file browser (Local ↔ Remote)
   - Drag & drop file transfer
   - Transfer queue with progress tracking
   - File management (create, rename, delete)
   - Multi-language support (English, 한국어)
   - Real-time transfer speed monitoring
   
   ## Downloads
   
   **Portable (Recommended):**
   - Single .exe file, no installation required
   - Slower first startup (~5-10 seconds)
   
   **Standard:**
   - Folder with multiple files
   - Faster startup (~2-3 seconds)
   
   ## Requirements
   - Windows 10 or higher
   - Android device with USB debugging enabled
   - ADB (Android Debug Bridge) in system PATH
   
   ## Usage
   1. Download and extract
   2. Run ADBCopy.exe
   3. Connect your Android device via USB
   4. Start transferring files!
   
   ---
   
   **Inspired by:** [AdbExplorer](https://github.com/gregko/AdbExplorer)
   ```

5. **Upload Files:**
   - `dist/onefile/ADBCopy_v0.1.0_Windows_Portable.zip`
   - `dist/folder/ADBCopy_v0.1.0_Windows.zip`

6. Click **Publish release**

---

## Pre-Release Checklist

- [ ] All features tested
- [ ] Both language modes tested (English, 한국어)
- [ ] Icons display correctly
- [ ] File transfer works (push/pull)
- [ ] Drag & drop works
- [ ] File management works (create, rename, delete)
- [ ] No console errors
- [ ] Tested on clean Windows machine (without Python)
- [ ] Release notes written
- [ ] Version number updated in code
- [ ] Git tag created

---

## File Structure

```
dist/
├── onefile/
│   ├── ADBCopy.exe                              # Single file
│   └── ADBCopy_v0.1.0_Windows_Portable.zip      # Release package
└── folder/
    ├── ADBCopy/                                 # Folder build
    │   ├── ADBCopy.exe
    │   └── ... (DLLs and resources)
    └── ADBCopy_v0.1.0_Windows.zip               # Release package
```

---

## Version Update for Next Release

Before next release, update version in:
1. `adb_copy/main_window.py` - About dialog
2. `build.bat` - Header comment
3. `build_onefile.bat` - Header comment
4. This file (RELEASE.md)

