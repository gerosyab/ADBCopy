# ADBCopy

A simple ADB file explorer with FileZilla-style UI for managing files on Android devices.

Inspired by [AdbExplorer](https://github.com/gregko/AdbExplorer), this project implements a clean and intuitive interface similar to FileZilla for easy file transfer between your computer and Android devices.

<img width="2104" height="1493" alt="image" src="https://github.com/user-attachments/assets/3026cf4d-7095-4416-ba5e-38decee8355a" />



## Features

- **Dual-panel interface** - Local and remote file systems side-by-side
- **Drag & drop** - Easy file/folder transfers between panels
- **Folder transfer** - Recursive folder synchronization support
- **Windows Explorer integration** - Drag from Explorer or copy/paste files
- **Transfer queue** - Monitor multiple file transfers with real-time progress
- **File management** - Create folders, rename, delete files on Android devices
- **Navigation history** - Back/forward buttons for easy browsing
- **Multi-language support** - English and Korean (한국어)
- **Real-time monitoring** - Transfer speed, ETA, and file details with date/time

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
   pip install PyQt6
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
- **Folder transfer** - Automatically transfers all subfolders and files recursively

### Navigation
- **Back/Forward** - Navigate folder history with ◀ ▶ buttons
- **Double-click** - Enter folders or go up with ".." entry
- **Path bar** - Type path directly and press Enter

### Transfer Queue
- **Real-time progress** - See speed, elapsed time, and ETA
- **Pause/Resume** - Control transfers at any time
- **Retry failed** - Automatically retry failed transfers
- **Sort & filter** - Click column headers to sort

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
- Release package: `dist/onefile/ADBCopy_v0.1.1_Windows_Portable.zip`

**Folder:**
- Executable: `dist/folder/ADBCopy/ADBCopy.exe`
- Release package: `dist/folder/ADBCopy_v0.1.1.zip`

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
__version__ = "0.1.2"
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
│   ├── ui/               # UI components
│   ├── workers/          # Background workers
│   └── resources/        # Icons and resources
├── build.bat             # Build script (folder)
├── build_onefile.bat     # Build script (single file)
├── run_tests.py          # Integrated test suite
└── README.md             # This file
```

## License

MIT License

