# ADBCopy

A simple ADB file explorer with FileZilla-style UI for managing files on Android devices.

Inspired by [AdbExplorer](https://github.com/gregko/AdbExplorer), this project implements a clean and intuitive interface similar to FileZilla for easy file transfer between your computer and Android devices.

<img width="2793" height="1841" alt="image" src="https://github.com/user-attachments/assets/7bd96a7f-3eb3-42bb-b473-38f165c9748d" />


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
   ```bash
   python -m adb_copy.main
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

## License

MIT License

