# Building ADBCopy

This guide explains how to build ADBCopy into a standalone Windows executable.

## Prerequisites

1. Python 3.10 or higher installed
2. All dependencies installed: `pip install -r requirements.txt`
3. PyInstaller installed: `pip install pyinstaller`

## Build Methods

### Method 1: Folder Build (Recommended) ⭐

**Advantages:**
- Fast startup time
- Smaller individual files
- Easier to debug
- Better for development

**How to build:**
```bash
build.bat
```

**Output:**
```
dist/ADBCopy/
├── ADBCopy.exe          # Main executable
├── *.dll                # Required DLLs
└── adb_copy/           # Resources
    └── resources/
        └── icons/       # Application icons
```

**Distribution:**
- Compress the entire `dist/ADBCopy/` folder to ZIP
- Users extract and run `ADBCopy.exe`

---

### Method 2: Single File Build

**Advantages:**
- Single .exe file
- Easier distribution

**Disadvantages:**
- Slower startup (extracts to temp folder)
- Larger file size

**How to build:**
```bash
build_onefile.bat
```

**Output:**
```
dist/
└── ADBCopy.exe    # Single executable (~100MB)
```

**Distribution:**
- Just distribute the single `ADBCopy.exe` file

---

### Method 3: Manual Build

For advanced users who want custom build options:

```bash
# Using spec file
pyinstaller ADBCopy.spec

# Or custom command
pyinstaller --windowed --icon=adb_copy/resources/icons/favicon.ico adb_copy/main.py
```

## Build Configuration

### ADBCopy.spec

The spec file controls the build process:

- **Included files**: Icons and resources
- **Hidden imports**: PyQt6 modules
- **Excluded modules**: Unnecessary packages (matplotlib, numpy, etc.)
- **UPX compression**: Enabled for smaller file size
- **Console**: Disabled (GUI only)

### Customization

To modify the build:

1. Edit `ADBCopy.spec`
2. Add/remove files in `datas` section
3. Add/remove modules in `excludes` section
4. Run: `pyinstaller ADBCopy.spec`

## Troubleshooting

### Missing modules error
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution:** Add module to `hiddenimports` in `ADBCopy.spec`

### Icon not showing
**Solution:** Ensure `favicon.ico` exists in `adb_copy/resources/icons/`

### Antivirus false positive
**Solution:** This is common with PyInstaller. Add exception to antivirus or submit false positive report

### Build fails
1. Clean previous builds: Delete `build/` and `dist/` folders
2. Reinstall PyInstaller: `pip uninstall pyinstaller && pip install pyinstaller`
3. Check Python version: Must be 3.10+

## File Size Optimization

Current build size: ~100-150MB

To reduce size:
1. Use folder build instead of onefile
2. Enable UPX compression (already enabled)
3. Exclude more unnecessary modules in spec file
4. Consider using Nuitka (advanced)

## Testing the Build

After building:

1. Navigate to output folder
2. Run `ADBCopy.exe`
3. Test main features:
   - Device connection
   - File browsing
   - File transfer
   - Language switching

## Distribution

### Recommended Structure

```
ADBCopy_v0.1.0_Windows.zip
├── ADBCopy/              # Built application folder
│   ├── ADBCopy.exe
│   └── ...
├── README.txt            # Quick start guide
└── LICENSE.txt           # License file
```

### Release Checklist

- [ ] Test on clean Windows machine
- [ ] Verify ADB functionality
- [ ] Check both language modes
- [ ] Test file transfers
- [ ] Create release notes
- [ ] Tag version in git
- [ ] Upload to GitHub Releases

## GitHub Release

```bash
# Tag version
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Create release on GitHub with:
# - Tag: v0.1.0
# - Title: ADBCopy v0.1.0
# - Description: Release notes
# - Attachment: ADBCopy_v0.1.0_Windows.zip
```

