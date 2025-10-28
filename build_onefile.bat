@echo off
echo ========================================
echo  Building ADBCopy v0.1.0 (Single File)
echo ========================================
echo.
echo Single file build: One .exe file (easy to distribute)
echo.
pause

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
if exist dist\onefile rmdir /s /q dist\onefile

echo.
echo Building single executable (this may take a while)...
echo.

REM Build single file using spec file
pyinstaller --distpath dist/onefile ADBCopy.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Creating release package...
cd dist\onefile
powershell -Command "Compress-Archive -Path ADBCopy.exe -DestinationPath ADBCopy_v0.1.0_Windows_Portable.zip -Force"
cd ..\..

echo.
echo ========================================
echo  Build Complete!
echo ========================================
echo.
echo Output location: dist\onefile\
echo Executable: dist\onefile\ADBCopy.exe
echo Release package: dist\onefile\ADBCopy_v0.1.0_Windows_Portable.zip
echo.
pause

