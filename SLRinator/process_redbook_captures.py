#!/usr/bin/env python3
"""
Process Redbook (seegenerally) captures and extract to citation-editor format
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

def extract_redbook_content(html):
    """Extract content from Redbook HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "title": None,
        "section": None,
        "meta": {},
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Try to find the main content area
    main_content = soup.find("div", class_="redbook-content")
    if not main_content:
        # Fallback to finding prose content
        main_content = soup.find("div", class_="prose")
    if not main_content:
        # Last fallback - find any large content div
        main_content = soup.find("main") or soup.find("body")
    
    if not main_content:
        return None
    
    # Extract title - look for h1 or first heading
    title_elem = main_content.find("h1")
    if title_elem:
        result["title"] = title_elem.get_text(strip=True)
    
    # Try to identify section from sidebar or title
    sidebar = soup.find("div", {"data-sidebar": "content"})
    if sidebar:
        active_item = sidebar.find("button", {"class": re.compile(r"bg-red-100.*text-red-900")})
        if active_item:
            section_text = active_item.get_text(strip=True)
            result["section"] = section_text
            
            # Extract section number if present
            section_match = re.match(r'^(\d+):', section_text)
            if section_match:
                result["meta"]["section_number"] = section_match.group(1)
    
    # Clean the HTML content
    if main_content:
        # Remove any script or style tags
        for tag in main_content.find_all(['script', 'style']):
            tag.decompose()
        
        result["body_html"] = str(main_content)
        result["body_text"] = main_content.get_text(separator="\n", strip=True)
    
    return result

def create_redbook_filename(original_file):
    """Create consistent filename for Redbook content."""
    # Extract timestamp
    timestamp_match = re.search(r'_(\d{8}_\d{6})\.html$', original_file)
    
    # Create a hash of the file for uniqueness
    file_hash = hashlib.md5(original_file.encode()).hexdigest()[:8]
    
    # Create filename: redbook_[hash]_[timestamp].html
    if timestamp_match:
        return f"redbook_{file_hash}.html"
    else:
        return f"redbook_{file_hash}.html"

def deduplicate_captures(captures_list):
    """Deduplicate captures based on content similarity."""
    unique_captures = []
    seen_content = set()
    
    for capture_path in captures_list:
        with open(capture_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create content hash (ignoring timestamps and minor differences)
        soup = BeautifulSoup(content, 'html.parser')
        main_text = soup.get_text(separator=" ", strip=True)
        # Normalize text for comparison
        normalized = re.sub(r'\s+', ' ', main_text)[:5000]  # First 5000 chars
        content_hash = hashlib.md5(normalized.encode()).hexdigest()
        
        if content_hash not in seen_content:
            seen_content.add(content_hash)
            unique_captures.append(capture_path)
    
    return unique_captures

def process_redbook_captures():
    """Process all Redbook captures"""
    
    # Setup paths
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    # Create Redbook-specific directories
    redbook_extracts = citation_editor / "redbook_extracts"
    redbook_processed = citation_editor / "redbook_processed"
    
    for dir_path in [redbook_extracts, redbook_processed]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Processing Redbook captures")
    print("=" * 60)
    
    # Find all seegenerally files
    seegenerally_files = sorted(captures_dir.glob("seegenerallyid_wtf_*.html"))
    print(f"Found {len(seegenerally_files)} seegenerally captures")
    
    # Deduplicate captures
    unique_files = deduplicate_captures(seegenerally_files)
    print(f"After deduplication: {len(unique_files)} unique captures")
    print()
    
    # Track processed sections
    sections_found = {}
    
    for idx, file_path in enumerate(unique_files, 1):
        print(f"Processing {idx}/{len(unique_files)}: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        extracted = extract_redbook_content(html_content)
        
        if extracted:
            # Determine section for naming
            section_id = extracted.get("section", f"section_{idx}")
            if extracted.get("title"):
                section_id = extracted["title"]
            
            # Clean section_id for filename
            clean_section = re.sub(r'[^\w\s-]', '', section_id)
            clean_section = re.sub(r'[-\s]+', '-', clean_section).lower()[:50]
            
            # Track sections
            if section_id not in sections_found:
                sections_found[section_id] = {
                    "file": f"rb_{idx:02d}__{clean_section}.html",
                    "title": extracted.get("title", section_id),
                    "section": extracted.get("section"),
                    "extracted": extracted
                }
                
                # Save JSON extract
                json_filename = f"rb_{idx:02d}__{clean_section}.json"
                json_path = redbook_extracts / json_filename
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(extracted, f, indent=2)
                print(f"  ✓ Saved extract: {json_filename}")
                
                # Create simplified HTML
                html_content = create_simplified_redbook_html(extracted, idx, clean_section)
                html_filename = f"rb_{idx:02d}__{clean_section}.html"
                html_path = redbook_processed / html_filename
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"  ✓ Saved HTML: {html_filename}")
        else:
            print(f"  ✗ Failed to extract content")
    
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Found {len(sections_found)} unique sections:")
    for section_id, info in sections_found.items():
        print(f"  - {info['file']}: {info['title']}")
    
    # Create index
    create_redbook_index(sections_found, redbook_processed)
    
    return sections_found

def create_simplified_redbook_html(extracted_data, idx, section_slug):
    """Create simplified HTML for Redbook section."""
    title = extracted_data.get("title", f"Section {idx}")
    section = extracted_data.get("section", "")
    
    # Parse the body HTML to clean it up
    soup = BeautifulSoup(extracted_data.get("body_html", ""), "html.parser")
    
    # Keep only essential elements
    for tag in soup.find_all(['button', 'svg', 'script', 'style']):
        tag.decompose()
    
    body_content = str(soup)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Redbook: {title}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #8B0000; border-bottom: 2px solid #8B0000; padding-bottom: 10px; }}
        h2, h3 {{ color: #8B0000; margin-top: 1.5em; }}
        .section-info {{ 
            background: #FFF5F5; 
            padding: 10px; 
            border-left: 4px solid #8B0000;
            margin-bottom: 20px;
        }}
        .example {{ 
            background: #F9F9F9; 
            padding: 10px; 
            border-left: 3px solid #DDD;
            margin: 10px 0;
            font-style: italic;
        }}
        .editor-note {{ 
            background: #FFFFCC; 
            padding: 2px 4px;
            border-radius: 3px;
        }}
        em {{ font-style: italic; }}
        strong {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="section-info">
        <strong>Redbook Section:</strong> {section if section else 'General'}
    </div>
    {body_content}
</body>
</html>"""
    
    return html_content

def create_redbook_index(sections_data, output_dir):
    """Create an index.html for Redbook sections."""
    
    index_html = """<!DOCTYPE html>
<html>
<head>
    <title>Stanford Law Review Redbook Index</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            background: #F5F5F5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #8B0000;
            border-bottom: 3px solid #8B0000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .subtitle {
            color: #666;
            font-style: italic;
            margin-bottom: 30px;
        }
        .sections-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .section-card {
            background: #FFF9F9;
            border: 1px solid #E0E0E0;
            border-left: 4px solid #8B0000;
            border-radius: 5px;
            padding: 15px;
            transition: all 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        .section-card:hover {
            background: #FFF;
            box-shadow: 0 4px 12px rgba(139,0,0,0.1);
            transform: translateY(-2px);
        }
        .section-number {
            background: #8B0000;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        .section-title {
            color: #333;
            font-weight: 500;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        .section-subtitle {
            color: #666;
            font-size: 0.9em;
        }
        .metadata {
            background: #F0F0F0;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📕 Stanford Law Review Redbook</h1>
        <p class="subtitle">The SLR guide to citation style and conventions</p>
        
        <div class="metadata">
            <strong>Generated:</strong> """ + datetime.now().strftime("%B %d, %Y at %I:%M %p") + """<br>
            <strong>Total Sections:</strong> """ + str(len(sections_data)) + """
        </div>
        
        <div class="sections-grid">
"""
    
    # Add section cards
    for section_id, info in sorted(sections_data.items(), key=lambda x: x[1]['file']):
        file_name = info['file']
        title = info['title']
        section = info.get('section', '')
        
        # Extract section number if available
        section_num = ""
        if section:
            num_match = re.match(r'^(\d+)', section)
            if num_match:
                section_num = num_match.group(1)
        
        index_html += f"""
            <a href="{file_name}" class="section-card">
                {f'<span class="section-number">Section {section_num}</span>' if section_num else ''}
                <div class="section-title">{title}</div>
                {f'<div class="section-subtitle">{section}</div>' if section and section != title else ''}
            </a>
"""
    
    index_html += """
        </div>
    </div>
</body>
</html>"""
    
    # Save index
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"\n✅ Created index.html with {len(sections_data)} sections")
    
    # Also create index.json
    index_data = {
        "generated_at": datetime.now().isoformat(),
        "count": len(sections_data),
        "sections": [
            {
                "file": info['file'],
                "title": info['title'],
                "section": info.get('section', ''),
                "section_number": info['extracted'].get('meta', {}).get('section_number')
            }
            for section_id, info in sections_data.items()
        ]
    }
    
    json_path = output_dir / "index.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    print(f"✅ Created index.json")

if __name__ == "__main__":
    process_redbook_captures()