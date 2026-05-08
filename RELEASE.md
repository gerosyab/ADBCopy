# Release Guide

## Build Release Packages

### 1. Single File Build (Portable)
```bash
build_onefile.bat
```

**Output:**
- `dist/onefile/ADBCopy.exe` (~100MB)
- `dist/onefile/ADBCopy_v0.1.3_Windows_Portable.zip`

**For:** Users who want single .exe file

---

### 2. Folder Build
```bash
build.bat
```

**Output:**
- `dist/folder/ADBCopy/` (folder with ADBCopy.exe + DLLs)
- `dist/folder/ADBCopy_v0.1.3_Windows.zip`

**For:** Users who prefer faster startup

---

## GitHub Release Steps

### 1. Commit and Tag
```bash
# Ensure all changes are committed
git add .
git commit -m "Release v0.1.3"

# Create tag
git tag -a v0.1.3 -m "Release v0.1.3 - Bug fixes & UX improvements"

# Push to GitHub
git push origin main
git push origin v0.1.3
```

### 2. Create GitHub Release

1. Go to: https://github.com/gerosyab/ADBCopy/releases/new
2. **Tag:** v0.1.3
3. **Title:** ADBCopy v0.1.3
4. **Description:**
   ```markdown
   # 🚀 ADBCopy v0.1.3 - Bug Fixes & UX Improvements

   A simple ADB file explorer with FileZilla-style UI.

   ## 🐛 Bug Fixes

   - **Drive root listing crash** - Loading `D:\`, `E:\` etc. no longer crashes when special files such as `pagefile.sys`, `$Recycle.Bin`, or `System Volume Information` are present. Per-item `WinError 2`/permission errors are now skipped gracefully so the rest of the listing still appears.
   - **Error display overlay** - When a directory fails to load, the error message is shown as a non-interactive overlay instead of a fake table row. Right-click and other actions are blocked while the overlay is visible, eliminating crashes from interacting with bogus rows.
   - **Folder transfer queue tracking** - Pulling/pushing a folder now expands into individual per-file tasks in the transfer queue. Progress, ETA, transfer speed, and elapsed time are now calculated correctly even for deep folder trees. Parent directories on the destination are auto-created (`mkdir -p` for remote, `os.makedirs` for local).
   - **Symlinks & SELinux ACL** - `ls -la` parser now recognizes symlinks (`l` permissions) and SELinux ACL markers, fixing edge cases where some Android entries were silently dropped.

   ## 🆕 What's New in v0.1.3

   - 🖱️ **Unified context menu** on both panels:
     - **Local panel:** PUSH / Open / Make Directory / Rename / Delete
     - **Remote panel:** PULL / Open / Make Directory / Rename / Delete
     - Open on remote panel is disabled when any folder is selected
     - Rename is enabled only for single selections
   - 📂 **Local file/folder operations** - Delete, New Folder, and Rename are now available on the local panel (previously remote-only)
   - 🗑️ **Safe delete dialog** - Local delete asks **Trash vs Permanent** with a red "cannot be undone" warning. Falls back to permanent delete if Trash is unsupported on the platform.
   - 👁️ **Open files cross-platform**:
     - Local files open in the OS default viewer/Explorer
     - Remote files automatically download to `~/.adbcopy/temp/` and then open (uses transfer queue, so progress is visible)
     - Multi-selection opens each item individually
   - 🌐 **Instant language switch** - Switching between English / 한국어 in `File → Language` now updates all UI text immediately. No restart required.
   - 🪟 **Folder tree right-click menu** - Same unified actions are available from the folder tree on either side, including PUSH/PULL of the right-clicked folder.

   ## ⚙️ Internal Improvements

   - i18n system migrated from a one-shot lookup to a weak-ref dispatcher so widgets can register listeners without leaking
   - Folder expansion uses `ls -laR` on the device for fast recursive listing
   - Worker creates missing parent directories before each transfer to keep folder structure intact

   ## Features
   - 📁 Dual-panel file browser (Local ↔ Remote)
   - 🎯 Drag & drop file/folder transfer (recursive, per-file progress)
   - 🪟 Windows Explorer integration (drag from Explorer, copy/paste)
   - 🖱️ Unified right-click context menus on both panels
   - 👁️ Open files in default viewer (remote: download-to-temp then open)
   - 🗑️ Safe delete (Trash vs Permanent for local files)
   - 📊 Transfer queue with real-time progress tracking
   - 🛠️ File management (create, rename, delete) on both panels
   - ◀▶ Navigation history (back/forward buttons)
   - 🌍 Multi-language support (English, 한국어) with instant switching
   - ⚡ Real-time transfer speed, ETA, and file details with date/time

   ## Downloads

   **Portable (Recommended):**
   - Single .exe file, no installation required
   - Slower first startup (~5-10 seconds)

   **Standard:**
   - Folder with multiple files
   - Faster startup (~2-3 seconds)

   ## Requirements
   - Windows 10 or higher (Linux/macOS supported when running from source)
   - Android device with USB debugging enabled
   - ADB (Android Debug Bridge) in system PATH

   ## Usage
   1. Download and extract
   2. Run ADBCopy.exe
   3. Connect your Android device via USB
   4. Start transferring files!

   ## Upgrade Notes
   - No configuration migration required from v0.1.2
   - First "Open" on a remote file creates `~/.adbcopy/temp/` (kept persistent so default-app caches keep working between sessions)

   ---

   **Inspired by:** [AdbExplorer](https://github.com/gregko/AdbExplorer)
   ```

5. **Upload Files:**
   - `dist/onefile/ADBCopy_v0.1.3_Windows_Portable.zip`
   - `dist/folder/ADBCopy_v0.1.3_Windows.zip`

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
│   └── ADBCopy_v0.1.3_Windows_Portable.zip      # Release package
└── folder/
    ├── ADBCopy/                                 # Folder build
    │   ├── ADBCopy.exe
    │   └── ... (DLLs and resources)
    └── ADBCopy_v0.1.3_Windows.zip               # Release package
```

---

## Version Update for Next Release

Before next release, update version in:
1. `adb_copy/__init__.py` - Source of truth
2. `README.md` - Build output examples + Version Management section
3. `VERSION.md` - "현재 버전" section
4. This file (RELEASE.md)
