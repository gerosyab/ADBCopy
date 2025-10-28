@echo off
echo ========================================
echo  Building ADBCopy v0.1.0
echo ========================================
echo.

REM Check if pyinstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Please run: pip install pyinstaller
    pause
    exit /b 1
)

REM Clean previous build
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist\folder rmdir /s /q dist\folder

echo.
echo Building executable...
echo.

REM Build with PyInstaller using folder spec file
pyinstaller --distpath dist/folder ADBCopy_folder.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Creating release package...
cd dist\folder
powershell -Command "Compress-Archive -Path ADBCopy -DestinationPath ADBCopy_v0.1.0_Windows.zip -Force"
cd ..\..

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output location: dist\folder\ADBCopy\
echo Executable: dist\folder\ADBCopy\ADBCopy.exe
echo Release package: dist\folder\ADBCopy_v0.1.0_Windows.zip
echo.
echo You can now run: dist\folder\ADBCopy\ADBCopy.exe
echo.
pause

