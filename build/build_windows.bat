@echo off
REM SLR Citation Processor - Windows Build Script

echo =========================================
echo SLR Citation Processor - Windows Build
echo =========================================

REM Clean previous builds
echo Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r app\requirements.txt

REM Run PyInstaller
echo Building application...
cd build
pyinstaller slr.spec --clean
cd ..

echo.
echo =========================================
echo Build complete!
echo =========================================
echo Application: dist\SLR Citation Processor\SLR Citation Processor.exe
echo.
echo To create installer, run Inno Setup with installer.iss
echo.

pause
