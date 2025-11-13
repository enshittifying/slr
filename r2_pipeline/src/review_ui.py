"""
Flask web UI for reviewing items flagged by the R2 pipeline.
"""
from flask import Flask, render_template, send_from_directory
import json
from pathlib import Path
import os

# Determine the absolute path to the project root to resolve paths correctly
# This assumes review_ui.py is in the src directory
project_root = Path(__file__).parent.parent

app = Flask(__name__, template_folder='templates')

# Configuration
# Use absolute paths to avoid issues with the working directory
REPORT_PATH = project_root / "data" / "reports" / "human_review_queue.html"
LOG_PATH = project_root / "data" / "logs" / "full_pipeline_log.json"
R2_PDF_DIR = project_root / "data" / "output" / "r2_pdfs"

@app.route('/')
def review_queue():
    """Display the human review queue."""
    try:
        with open(LOG_PATH, 'r') as f:
            # We load the JSON log to get structured data for the template
            all_items = json.load(f)
            review_items = [item for item in all_items if item.get("recommendation") != "approve"]
    except (FileNotFoundError, json.JSONDecodeError):
        review_items = []
        
    return render_template('review.html', items=review_items)

@app.route('/pdfs/<path:filename>')
def serve_r2_pdf(filename):
    """Serve generated R2 PDFs."""
    return send_from_directory(R2_PDF_DIR, filename)

if __name__ == '__main__':
    print(f"Starting Flask server...")
    print(f"Serving review UI from: http://127.0.0.1:5001")
    print(f"Make sure your log file is at: {LOG_PATH}")
    app.run(debug=True, port=5001)
