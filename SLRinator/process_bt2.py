#!/usr/bin/env python3
"""
Process bt2 Bluebook capture and extract to citation-editor format
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

def extract_bluebook(html):
    """Extract content from Bluebook HTML following the specified patterns."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Find main content area
    main = soup.select_one("main#main-content")
    if not main:
        main = soup.find("body")
        if not main:
            return None
    
    # Remove common chrome/UI elements inside main
    chrome_selectors = [
        'nav[aria-label="Breadcrumb"]',
        '.ql-container',
        '.ql-button',
        '#dismissible-banner',
        'header.fixed',
        'nav[aria-label="Main Section"]',
        '.mobile-nav-container',
        '.menu-section',
        '.pins-overlay',
        '.toc-button',
        'button.hamburger'
    ]
    
    for selector in chrome_selectors:
        for node in main.select(selector):
            node.decompose()
    
    result = {
        "title": None,
        "meta": {},
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Try to find title (h1 or h2)
    title = main.find("h1")
    if not title:
        title = main.find("h2")
    
    if title:
        result["title"] = title.get_text(strip=True)
        title_parts = result["title"].split()
        if title_parts and (title_parts[0].startswith('B') or title_parts[0].startswith('T')):
            result["meta"]["rule_id"] = title_parts[0]
    
    # Clean the HTML (preserve structure)
    content = main.prettify()
    
    # Store both HTML and text versions
    result["body_html"] = content
    result["body_text"] = main.get_text(separator="\n", strip=True)
    
    return result

def create_simplified_html(extracted_data):
    """Create simplified HTML from extracted data."""
    # Get rule ID and title
    rule_id = extracted_data.get("meta", {}).get("rule_id", "Unknown")
    title = extracted_data.get("title", "Untitled")
    
    # Parse the body HTML
    soup = BeautifulSoup(extracted_data["body_html"], "html.parser")
    
    # Keep only the main content div
    main_div = soup.find("div")
    if main_div:
        body_content = str(main_div)
    else:
        body_content = extracted_data["body_html"]
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
</head>
<body>
    {body_content}
</body>
</html>"""
    
    return html_content

def create_relabeled_filename(original_filename):
    """Convert filename format: bt2-jurisdiction-specific -> bt2__jurisdiction-specific"""
    # Remove timestamp and extension
    base = original_filename.replace('.html', '')
    base = re.sub(r'_\d{8}_\d{6}$', '', base)
    
    # Split on first hyphen after rule ID
    parts = base.split('-', 1)
    if len(parts) == 2:
        return f"{parts[0]}__{parts[1]}.html"
    return f"{base}.html"

def process_bt2():
    """Process bt2 capture file"""
    
    # Setup paths
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    captures_extracts = citation_editor / "captures_extracts"
    relabeled_extracts = citation_editor / "relabeled_extracts"
    lightbluebook2 = citation_editor / "lightbluebook2"
    
    # Create directories if needed
    for dir_path in [captures_extracts, relabeled_extracts, lightbluebook2]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Processing bt2 Bluebook capture")
    print("=" * 60)
    
    # Find the bt2 file
    bt2_file = captures_dir / "bt2-jurisdiction-specific-citation-rules-and-style-guides_20250820_053658.html"
    
    if not bt2_file.exists():
        print(f"File not found: {bt2_file}")
        return
    
    filename = bt2_file.name
    print(f"\nProcessing: {filename}")
    
    # Read and extract content
    with open(bt2_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    extracted = extract_bluebook(html_content)
    
    if extracted:
        # Save JSON extract
        json_path = captures_extracts / filename.replace('.html', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(extracted, f, indent=2)
        print(f"  ✓ Saved to captures_extracts: {json_path.name}")
        
        # Create simplified HTML
        simplified_html = create_simplified_html(extracted)
        
        # Save to relabeled_extracts with new naming
        relabeled_name = create_relabeled_filename(filename)
        relabeled_path = relabeled_extracts / relabeled_name
        with open(relabeled_path, 'w', encoding='utf-8') as f:
            f.write(simplified_html)
        print(f"  ✓ Saved to relabeled_extracts: {relabeled_name}")
        
        # Also save to lightbluebook2
        lightblue_path = lightbluebook2 / relabeled_name
        with open(lightblue_path, 'w', encoding='utf-8') as f:
            f.write(simplified_html)
        print(f"  ✓ Saved to lightbluebook2: {relabeled_name}")
    else:
        print(f"  ✗ Failed to extract content")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Files saved to:")
    print(f"  - {captures_extracts}")
    print(f"  - {relabeled_extracts}")
    print(f"  - {lightbluebook2}")

if __name__ == "__main__":
    process_bt2()