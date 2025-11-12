"""
Vercel serverless function entry point for Flask application.

This module is the entry point for Vercel's Python runtime.
It creates and exports the Flask app instance.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import create_app

# Create Flask app instance
app = create_app("production")

# Export for Vercel
# Vercel will call this as a WSGI application
handler = app
