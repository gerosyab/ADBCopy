# Release Guide

## Build Release Packages

### 1. Single File Build (Portable)
```bash
build_onefile.bat
```

**Output:**
- `dist/onefile/ADBCopy.exe` (~100MB)
- `dist/onefile/ADBCopy_v0.1.4_Windows_Portable.zip`

**For:** Users who want single .exe file

---

### 2. Folder Build
```bash
build.bat
```

**Output:**
- `dist/folder/ADBCopy/` (folder with ADBCopy.exe + DLLs)
- `dist/folder/ADBCopy_v0.1.4_Windows.zip`

**For:** Users who prefer faster startup

---

## GitHub Release Steps

### 1. Commit and Tag
```bash
# Ensure all changes are committed
git add .
git commit -m "Release v0.1.4"

# Create tag
git tag -a v0.1.4 -m "Release v0.1.4 - Navigation, queue UX & tree sync"

# Push to GitHub
git push origin main
git push origin v0.1.4
```

### 2. Create GitHub Release

1. Go to: https://github.com/gerosyab/ADBCopy/releases/new
2. **Tag:** v0.1.4
3. **Title:** ADBCopy v0.1.4
4. **Description:**
   ```markdown
   # 🚀 ADBCopy v0.1.4 — Navigation, queue cleanup & tree sync

   A simple ADB file explorer with FileZilla-style UI.

   ## 🆕 What's new in v0.1.4

   - **Folder tree sync** — Create / rename / delete from the file list refreshes the matching branch in the folder tree so you do not need a manual tree refresh.
   - **My PC view** — Select **My PC** in the local tree to show special folders (Desktop, Documents, …) and drive letters in the file panel; open entries as usual.
   - **Transfer queue: Remove** — Toolbar **Remove ▼** and table right-click: remove selected, completed, failed, waiting, finished (completed+failed), or all. In-progress rows are never removed; pending tasks are dropped from the worker queue in sync (`tasks_removed` + thread-safe queue lock).
   - **History navigation** — **Alt+Left / Alt+Right**, **Backspace**, and mouse **Back / Forward** (XButton) when the local or remote panel has focus, in addition to the ◀ ▶ toolbar buttons.

   ## 🐛 Reliability (recent releases)

   - Windows drive roots (`C:\`, `D:\`, …) skip per-item permission / `WinError 2` issues instead of failing the whole listing.
   - Directory load errors use a blocking overlay instead of fake table rows.
   - Folder PUSH/PULL expands to per-file queue rows with correct progress, ETA, and auto-created parent dirs on the destination.
   - `ls -la` parsing handles symlinks and SELinux ACL markers.

   ## ✨ Other capabilities (summary)

   - Dual local ↔ remote panels, drag-drop, Explorer integration, unified context menus on panels and tree
   - Open remote files via `~/.adbcopy/temp/`; local delete with Trash vs permanent choice
   - English / 한국어 instant language switch (weak-ref i18n listeners)

   ## Downloads

   **Portable (recommended):** single `.exe`, slower cold start (~5–10 s).  
   **Standard:** folder build, faster start (~2–3 s).

   ## Requirements

   - Windows 10+ for the prebuilt binaries (Linux/macOS from source)
   - USB debugging enabled on the device; `adb` on PATH

   ## Usage

   1. Download and extract  
   2. Run `ADBCopy.exe`  
   3. Connect the device via USB  
   4. Transfer files

   ## Upgrade notes

   - No config migration needed from **v0.1.3**.
   - First remote **Open** still uses persistent `~/.adbcopy/temp/` for default-app caching.

   ---

   **Inspired by:** [AdbExplorer](https://github.com/gregko/AdbExplorer)
   ```

5. **Upload Files:**
   - `dist/onefile/ADBCopy_v0.1.4_Windows_Portable.zip`
   - `dist/folder/ADBCopy_v0.1.4_Windows.zip`

6. Click **Publish release**

---

## Pre-Release Checklist

### Core Features
- [ ] File transfer works (push/pull)
- [ ] Folder transfer works (recursive, each file shows its own queue row)
- [ ] Drag & drop works (internal)
- [ ] Windows Explorer drag & drop works
- [ ] Copy/paste works (Ctrl+C, Ctrl+V)
- [ ] File management works (create, rename, delete on **both** panels)

### Context Menu
- [ ] Local folder tree right-click: PUSH / Open / Make Directory / Rename / Delete
- [ ] Local file list right-click: PUSH / Open / Make Directory / Rename / Delete
- [ ] Remote folder tree right-click: PULL / Make Directory / Rename / Delete
- [ ] Remote file list right-click: PULL / Open / Make Directory / Rename / Delete
- [ ] Open is disabled when any folder is selected on remote panel
- [ ] Rename is disabled with multi-selection
- [ ] Local delete shows Trash/Permanent dialog with red warning

### Bug Regressions
- [ ] `D:\`, `E:\` and other drive roots load without crashing
- [ ] Error overlay appears (not interactive) when a path cannot be listed
- [ ] Folder pull/push expands into individual per-file queue rows

### UI/UX
- [ ] Date column displays correctly
- [ ] Back/forward navigation works
- [ ] Language switch (English ↔ 한국어) updates UI **without restart**
- [ ] Icons display correctly (window + taskbar)
- [ ] Transfer queue updates in real-time
- [ ] Open remote file: downloads to `~/.adbcopy/temp/` and launches default app
- [ ] No console errors or warnings

### Testing
- [ ] Tested on clean Windows machine (without Python)
- [ ] Large file transfer (100MB+) tested
- [ ] Multiple file transfer (100+ files) tested
- [ ] Folder with subfolders tested (verify per-file progress)

### Release
- [ ] Release notes written
- [ ] Version number updated in `adb_copy/__init__.py`
- [ ] Git tag created
- [ ] ZIP files generated

---

## File Structure

```
dist/
├── onefile/
│   ├── ADBCopy.exe                              # Single file
│   └── ADBCopy_v0.1.4_Windows_Portable.zip      # Release package
└── folder/
    ├── ADBCopy/                                 # Folder build
    │   ├── ADBCopy.exe
    │   └── ... (DLLs and resources)
    └── ADBCopy_v0.1.4_Windows.zip               # Release package
```

---

## Version Update for Next Release

Before next release, update version in:
1. `adb_copy/__init__.py` - Source of truth
2. `README.md` - Build output examples + Version Management section
3. `VERSION.md` - "현재 버전" section
4. This file (RELEASE.md)
