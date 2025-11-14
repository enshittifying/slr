#!/bin/bash

# SLR Citation Processor - Mac Build Script

set -e

echo "========================================="
echo "SLR Citation Processor - Mac Build"
echo "========================================="

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ __pycache__

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r app/requirements.txt

# Run PyInstaller
echo "Building application..."
cd build
pyinstaller slr.spec --clean
cd ..

# Sign the app (requires Apple Developer ID - optional)
if [ -n "$DEVELOPER_ID" ]; then
    echo "Signing application..."
    codesign --force --deep --sign "$DEVELOPER_ID" \
        "dist/SLR Citation Processor.app"
else
    echo "Skipping code signing (no DEVELOPER_ID set)"
fi

# Create DMG (optional)
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG..."
    create-dmg \
        --volname "SLR Citation Processor" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --app-drop-link 600 185 \
        "dist/SLR-Citation-Processor-Mac.dmg" \
        "dist/SLR Citation Processor.app"
else
    echo "Skipping DMG creation (create-dmg not installed)"
    echo "Install with: brew install create-dmg"
fi

echo ""
echo "========================================="
echo "Build complete!"
echo "========================================="
echo "Application: dist/SLR Citation Processor.app"
if [ -f "dist/SLR-Citation-Processor-Mac.dmg" ]; then
    echo "DMG: dist/SLR-Citation-Processor-Mac.dmg"
fi
echo ""
