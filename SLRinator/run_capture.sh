#!/bin/bash

# Run the browser capture script with sudo
echo "Browser HTML Capture Tool"
echo "========================="
echo ""
echo "This tool will:"
echo "1. Launch a Chrome browser window"
echo "2. Capture HTML when you press F5"
echo "3. Save files to: ./captures/ (in your current directory)"
echo ""
echo "Files are saved as: {page_name}_{timestamp}.html"
echo "Example: about_20250819_143045.html"
echo ""
echo "Please enter your password to run with keyboard access:"
echo ""

sudo python3 /Users/ben/app/SLRinator/browser_capture.py