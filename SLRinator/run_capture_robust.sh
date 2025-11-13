#!/bin/bash

echo "Browser HTML Capture Tool (Robust Version)"
echo "=========================================="
echo ""
echo "This tool will:"
echo "1. Launch a Chrome browser window"
echo "2. Capture HTML when you press CMD+SHIFT+0 (zero)"
echo "3. Save files to: /Users/ben/app/SLRinator/captures/"
echo ""
echo "Files are saved as: {page_name}_{timestamp}.html"
echo ""
echo "Note: You need to grant Terminal accessibility permissions"
echo "Go to System Settings > Privacy & Security > Accessibility"
echo "And add Terminal.app if not already added"
echo ""
echo "Press Enter to start..."
read

python3 /Users/ben/app/SLRinator/browser_capture_robust.py