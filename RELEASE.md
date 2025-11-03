# Release Guide

## Build Release Packages

### 1. Single File Build (Portable)
```bash
build_onefile.bat
```

**Output:**
- `dist/onefile/ADBCopy.exe` (~100MB)
- `dist/onefile/ADBCopy_v0.1.1_Windows_Portable.zip`

**For:** Users who want single .exe file

---

### 2. Folder Build
```bash
build.bat
```

**Output:**
- `dist/folder/ADBCopy/` (folder with ADBCopy.exe + DLLs)
- `dist/folder/ADBCopy_v0.1.1_Windows.zip`

**For:** Users who prefer faster startup

---

## GitHub Release Steps

### 1. Commit and Tag
```bash
# Ensure all changes are committed
git add .
git commit -m "Release v0.1.1"

# Create tag
git tag -a v0.1.1 -m "Release v0.1.1 - Update release"

# Push to GitHub
git push origin main
git push origin v0.1.1
```

### 2. Create GitHub Release

1. Go to: https://github.com/gerosyab/ADBCopy/releases/new
2. **Tag:** v0.1.1
3. **Title:** ADBCopy v0.1.1
4. **Description:**
   ```markdown
   # 🚀 ADBCopy v0.1.1 - Feature Update
   
   A simple ADB file explorer with FileZilla-style UI.
   
   ## 🆕 What's New in v0.1.1
   
   - 📅 **Date column** - File modification date/time now displayed
   - 📁 **Folder transfer** - Drag & drop folders with recursive copy
   - ◀▶ **Navigation history** - Back/forward buttons for easy browsing  
   - 🪟 **Windows Explorer integration:**
     - Drag files from Windows Explorer to remote panel
     - Copy (Ctrl+C) files from local panel, paste in Explorer
     - Paste (Ctrl+V) files from Explorer to remote panel
   - ⚡ **Performance boost** - 5-10x faster file operations
   - 🐛 **Bug fixes** - Folder tree refresh, path navigation improvements
   
   ## Features
   - 📁 Dual-panel file browser (Local ↔ Remote)
   - 🎯 Drag & drop file/folder transfer (recursive)
   - 🪟 Windows Explorer integration (drag from Explorer, copy/paste)
   - 📊 Transfer queue with real-time progress tracking
   - 🛠️ File management (create, rename, delete)
   - ◀▶ Navigation history (back/forward buttons)
   - 🌍 Multi-language support (English, 한국어)
   - ⚡ Real-time transfer speed, ETA, and file details with date/time
   
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
   
   ## Key Features Explained
   
   **File Transfer:**
   - Drag & drop files/folders between panels
   - Drag files from Windows Explorer to remote panel
   - Copy (Ctrl+C) and paste (Ctrl+V) files
   
   **Navigation:**
   - Back (◀) and Forward (▶) buttons to navigate folder history
   - Double-click folders to enter
   - ".." entry to go to parent folder
   
   **Transfer Queue:**
   - Real-time progress with speed and ETA
   - Pause/Resume transfers
   - Retry failed transfers
   - Sort by any column
   
   ---
   
   **Inspired by:** [AdbExplorer](https://github.com/gregko/AdbExplorer)
   ```

5. **Upload Files:**
   - `dist/onefile/ADBCopy_v0.1.1_Windows_Portable.zip`
   - `dist/folder/ADBCopy_v0.1.1_Windows.zip`

6. Click **Publish release**

---

## Pre-Release Checklist

### Core Features
- [ ] File transfer works (push/pull)
- [ ] Folder transfer works (recursive)
- [ ] Drag & drop works (internal)
- [ ] Windows Explorer drag & drop works
- [ ] Copy/paste works (Ctrl+C, Ctrl+V)
- [ ] File management works (create, rename, delete)

### UI/UX
- [ ] Date column displays correctly
- [ ] Back/forward navigation works
- [ ] Both language modes tested (English, 한국어)
- [ ] Icons display correctly (window + taskbar)
- [ ] Transfer queue updates in real-time
- [ ] No console errors or warnings

### Testing
- [ ] Tested on clean Windows machine (without Python)
- [ ] Large file transfer (100MB+) tested
- [ ] Multiple file transfer (100+ files) tested
- [ ] Folder with subfolders tested

### Release
- [ ] Release notes written
- [ ] Version number updated in code
- [ ] Git tag created
- [ ] ZIP files generated

---

## File Structure

```
dist/
├── onefile/
│   ├── ADBCopy.exe                              # Single file
│   └── ADBCopy_v0.1.1_Windows_Portable.zip      # Release package
└── folder/
    ├── ADBCopy/                                 # Folder build
    │   ├── ADBCopy.exe
    │   └── ... (DLLs and resources)
    └── ADBCopy_v0.1.1_Windows.zip               # Release package
```

---

## Version Update for Next Release

Before next release, update version in:
1. `adb_copy/main_window.py` - About dialog
2. `build.bat` - Header comment
3. `build_onefile.bat` - Header comment
4. This file (RELEASE.md)

