# ADBCopy

A simple ADB file explorer with FileZilla-style UI for managing files on Android devices.

Inspired by [AdbExplorer](https://github.com/gregko/AdbExplorer), this project implements a clean and intuitive interface similar to FileZilla for easy file transfer between your computer and Android devices.

## Features

- **Dual-panel interface** - Local and remote file systems side-by-side
- **Drag & drop** - Easy file transfers between panels
- **Transfer queue** - Monitor multiple file transfers with progress tracking
- **File management** - Create folders, rename, delete files on Android devices
- **Multi-language support** - English and Korean (한국어)
- **Real-time speed monitoring** - Transfer speed and estimated time display

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
- Release package: `dist/onefile/ADBCopy_v0.1.0_Windows_Portable.zip`

**Folder:**
- Executable: `dist/folder/ADBCopy/ADBCopy.exe`
- Release package: `dist/folder/ADBCopy_v0.1.0_Windows.zip`

See [RELEASE.md](RELEASE.md) for detailed release instructions.

## Interface

- **Top**: Console log showing transfer activity
- **Middle**: Dual file panels (Local ↔ Remote)
- **Bottom**: Transfer queue with progress tracking

## License

MIT License

