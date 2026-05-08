# ADBCopy

A simple ADB file explorer with FileZilla-style UI for managing files on Android devices.

Inspired by [AdbExplorer](https://github.com/gregko/AdbExplorer), this project implements a clean and intuitive interface similar to FileZilla for easy file transfer between your computer and Android devices.

<img width="2104" height="1493" alt="image" src="https://github.com/user-attachments/assets/3026cf4d-7095-4416-ba5e-38decee8355a" />



## Features

- **Dual-panel interface** - Local and remote file systems side-by-side
- **Drag & drop** - Easy file/folder transfers between panels
- **Folder transfer** - Recursive folder synchronization with per-file progress
- **Windows Explorer integration** - Drag from Explorer or copy/paste files
- **Unified context menu** - Same actions on both panels (PUSH/PULL, Open, New Folder, Delete, Rename)
- **Open files** - Launch local files in default viewer; remote files auto-download to temp and open
- **Safe delete** - Choose between Trash (local) or Permanent delete with red warning
- **Transfer queue** - Monitor multiple file transfers with real-time progress
- **File management** - Create folders, rename, delete files on both panels
- **Navigation history** - Back/forward toolbar buttons, **Alt+Left/Right**, **Backspace**, and mouse **Back/Forward** (per panel when focused)
- **My PC view** - Click **My PC** in the local tree to list special folders and drives in the file panel
- **Transfer queue cleanup** - **Remove** menu (dropdown + right-click): selected / completed / failed / waiting / finished / all (in-progress rows are always kept; worker queue stays in sync)
- **Tree sync** - File list changes (new folder, rename, delete) refresh the matching folder tree branch automatically
- **Multi-language support** - English and Korean (한국어), switch instantly without restart
- **Real-time monitoring** - Transfer speed, ETA, and file details with date/time
- **Robust drive listing** - Handles Windows drive roots (C:\, D:\) gracefully even when special files (pagefile.sys, $Recycle.Bin) are present

## Requirements

- Python 3.10 or higher
- PyQt6
- ADB (Android Debug Bridge)
- Android device with Developer Mode enabled

## Installation

1. **Install ADB**
   - Windows: Download [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
   - Add ADB to system PATH

2. **Clone repository**
   ```bash
   git clone https://github.com/gerosyab/ADBCopy.git
   cd ADBCopy
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or manually:
   ```bash
   pip install PyQt6 send2trash
   ```

## Usage

1. **Enable Developer Mode on Android**
   - Go to `Settings` → `About phone`
   - Tap `Build number` 7 times
   - Go back to `Settings` → `Developer options`
   - Enable `USB debugging`

2. **Connect device**
   - Connect your Android device via USB
   - Accept USB debugging permission on device

3. **Run application**
   
   **Option A: Run from source (개발/테스트용)**
   ```bash
   python -m adb_copy.main
   ```
   
   **Option B: Run built executable (배포용)**
   ```bash
   # After building
   dist\folder\ADBCopy\ADBCopy.exe
   ```

## Key Features

### File Transfer
- **Drag & drop** - Drag files/folders between panels for instant transfer
- **Windows Explorer** - Drag files from Explorer directly to remote panel
- **Copy/Paste** - Use Ctrl+C/Ctrl+V to copy files between panels or from Explorer
- **Folder transfer** - Recursively expands folders into individual file tasks so each file shows its own progress, ETA, and size in the queue

### Context Menu (right-click)
Both panels share a unified menu, with panel-specific actions:

- **Local panel:** PUSH, Open (default viewer/explorer), Make Directory, Rename, Delete
- **Remote panel:** PULL, Open (download to `~/.adbcopy/temp` then launch), Make Directory, Rename, Delete

Behavior:
- Open on remote panel is disabled if any folder is selected
- Rename is enabled only with a single selection
- Delete on local panel asks Trash vs Permanent (with red "cannot be undone" warning)
- Delete on remote panel is permanent only (Android `rm -rf`)

### Navigation
- **Back/Forward** - ◀ ▶ buttons plus **Alt+Left / Alt+Right**, **Backspace**, and mouse **Back / Forward** (XButton) when a panel has focus
- **My PC** - Local tree root opens a virtual list of special folders and drive letters in the file panel
- **Double-click** - Enter folders or go up with ".." entry
- **Path bar** - Type path directly and press Enter

### Transfer Queue
- **Real-time progress** - See speed, elapsed time, and ETA
- **Pause/Resume** - Control transfers at any time
- **Retry failed** - Automatically retry failed transfers
- **Remove** - Toolbar **Remove ▼** and table right-click: clear selected, completed, failed, waiting, finished, or all (rows in progress are never removed; pending worker tasks are dropped when rows are removed)
- **Sort & filter** - Click column headers to sort

### Language
- Switch between English and 한국어 from `File → Language` - applies instantly, no restart needed
- Choice is persisted across runs

## Building Executable

### Quick Start
```bash
pip install pyinstaller

# Single file (recommended for distribution)
build_onefile.bat

# Or folder build (faster startup)
build.bat
```

### Build Output

**Single File:**
- Executable: `dist/onefile/ADBCopy.exe`
- Release package: `dist/onefile/ADBCopy_v0.1.4_Windows_Portable.zip`

**Folder:**
- Executable: `dist/folder/ADBCopy/ADBCopy.exe`
- Release package: `dist/folder/ADBCopy_v0.1.4_Windows.zip`

See [RELEASE.md](RELEASE.md) for detailed release instructions.

## Interface

- **Top**: Console log showing transfer activity
- **Middle**: Dual file panels (Local ↔ Remote)
- **Bottom**: Transfer queue with progress tracking

## Development

### Running Tests

Run integrated tests before building:

```bash
python run_tests.py
```

Tests include:
- ADB connection and command execution
- File list parsing (including setuid/setgid permissions)
- Local drive loading (C:, D:, E: etc.)
- Path handling and validation
- UI component initialization
- Version management

### Version Management

Version is centrally managed in `adb_copy/__init__.py`:

```python
__version__ = "0.1.4"
```

When you update the version, it automatically reflects in:
- Build scripts output
- About dialog
- Release package filenames

See [VERSION.md](VERSION.md) for details.

### Project Structure

```
ADBCopy/
├── adb_copy/              # Main application package
│   ├── core/             # Core functionality (ADB manager)
│   ├── ui/               # UI components (panels, dialogs)
│   ├── workers/          # Background workers (transfer, file list, device watch)
│   ├── utils/            # Cross-platform helpers (open, temp dir)
│   └── resources/        # Icons and resources
├── build.bat             # Build script (folder)
├── build_onefile.bat     # Build script (single file)
├── run_tests.py          # Integrated test suite
├── requirements.txt      # Runtime dependencies
└── README.md             # This file
```

## License

MIT License

