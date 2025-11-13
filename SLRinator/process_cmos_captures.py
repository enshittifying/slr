#!/usr/bin/env python3
"""
Process CMOS (Chicago Manual of Style) captures
- psec files (sections 001-267)
- Index files (a-z)
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

def extract_cmos_section(html):
    """Extract content from CMOS psec HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "title": None,
        "chapter": None,
        "section": None,
        "section_number": None,
        "meta": {},
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Extract chapter info
    chapter = soup.find("h1", id="ch01")
    if not chapter:
        chapter = soup.find("h1")
    
    if chapter:
        chapter_num = chapter.find("span", id="chapter-number")
        chapter_title = chapter.find("span", id="chapter-title")
        
        if chapter_num:
            result["meta"]["chapter_number"] = chapter_num.get_text(strip=True).rstrip(":")
        if chapter_title:
            result["chapter"] = chapter_title.get_text(strip=True)
    
    # Extract section info
    section = soup.find("h2", class_="section-heading")
    if section:
        section_num = section.find("span", class_="section-number")
        section_title = section.find("span", class_="section-title")
        
        if section_num:
            result["section_number"] = section_num.get_text(strip=True)
        if section_title:
            result["section"] = section_title.get_text(strip=True)
            result["title"] = f"{result['section_number']}: {result['section']}" if result['section_number'] else result['section']
    
    # Find main content
    main_content = soup.find("div", class_="page-section")
    if not main_content:
        main_content = soup.find("div", class_="content-inner")
    if not main_content:
        main_content = soup.find("main")
    if not main_content:
        main_content = soup.find("body")
    
    if main_content:
        # Remove navigation and chrome elements
        for elem in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
            elem.decompose()
        
        # Remove trail navigation
        for trail in main_content.find_all("p", class_="trail"):
            trail.decompose()
        
        # Remove noindex sections
        for noindex in main_content.find_all("noindex"):
            noindex.decompose()
        
        result["body_html"] = str(main_content)
        result["body_text"] = main_content.get_text(separator="\n", strip=True)
    
    return result

def extract_cmos_index(html, letter):
    """Extract content from CMOS index HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "title": f"Index: {letter.upper()}",
        "letter": letter.upper(),
        "type": "index",
        "meta": {},
        "entries": [],
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Find index content
    index_content = soup.find("div", class_="index-content")
    if not index_content:
        index_content = soup.find("div", class_="content-inner")
    if not index_content:
        # Look for index list items
        index_content = soup.find("ul", class_="index-list")
    
    if index_content:
        # Extract index entries
        for item in index_content.find_all("li"):
            entry_text = item.get_text(strip=True)
            if entry_text:
                result["entries"].append(entry_text)
        
        # Clean HTML
        for elem in index_content.find_all(['script', 'style']):
            elem.decompose()
        
        result["body_html"] = str(index_content)
        result["body_text"] = "\n".join(result["entries"])
    
    return result

def deduplicate_cmos_captures(captures_list):
    """Deduplicate CMOS captures based on content."""
    unique_captures = {}
    
    for capture_path in captures_list:
        # Extract identifier from filename
        filename = capture_path.name
        
        # For psec files, extract the section number
        if filename.startswith("psec"):
            match = re.match(r'psec(\d+)_', filename)
            if match:
                section_num = match.group(1)
                
                # Keep the earliest timestamp for each section
                if section_num not in unique_captures:
                    unique_captures[section_num] = capture_path
                else:
                    # Compare timestamps and keep earlier one
                    existing_time = re.search(r'_(\d{8}_\d{6})', unique_captures[section_num].name)
                    new_time = re.search(r'_(\d{8}_\d{6})', filename)
                    
                    if existing_time and new_time:
                        if new_time.group(1) < existing_time.group(1):
                            unique_captures[section_num] = capture_path
        
        # For index files, just use the letter
        elif re.match(r'^[a-z]_', filename):
            letter = filename[0]
            # Only process files from 20:04-20:05
            if "_2004" in filename or "_2005" in filename:
                if letter not in unique_captures:
                    unique_captures[letter] = capture_path
    
    return list(unique_captures.values())

def process_cmos_captures():
    """Process all CMOS captures"""
    
    # Setup paths
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    # Create CMOS-specific directories
    cmos_extracts = citation_editor / "cmos_extracts"
    cmos_sections = citation_editor / "cmos_sections"
    cmos_index = citation_editor / "cmos_index"
    
    for dir_path in [cmos_extracts, cmos_sections, cmos_index]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("Processing CMOS captures")
    print("=" * 60)
    
    # Process psec files
    print("\nProcessing section files (psec)...")
    psec_files = sorted(captures_dir.glob("psec*.html"))
    unique_psec = deduplicate_cmos_captures(psec_files)
    print(f"Found {len(psec_files)} psec files, {len(unique_psec)} unique sections")
    
    sections_data = {}
    
    for idx, file_path in enumerate(unique_psec, 1):
        if idx % 50 == 0:
            print(f"  Processing section {idx}/{len(unique_psec)}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        extracted = extract_cmos_section(html_content)
        
        if extracted and extracted.get("section_number"):
            section_num = extracted["section_number"]
            
            # Save JSON extract
            json_filename = f"cmos_{section_num.replace('.', '_')}.json"
            json_path = cmos_extracts / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(extracted, f, indent=2)
            
            # Create simplified HTML
            html_filename = f"cmos_{section_num.replace('.', '_')}.html"
            html_content = create_simplified_cmos_html(extracted)
            html_path = cmos_sections / html_filename
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            sections_data[section_num] = {
                "file": html_filename,
                "title": extracted.get("title"),
                "section": extracted.get("section"),
                "chapter": extracted.get("chapter"),
                "section_number": section_num
            }
    
    print(f"✓ Processed {len(sections_data)} unique sections")
    
    # Process index files
    print("\nProcessing index files (a-z)...")
    index_files = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        # Look for files from 20:04-20:05
        pattern = f"{letter}_20250821_200*.html"
        matches = list(captures_dir.glob(pattern))
        for match in matches:
            if "_2004" in str(match) or "_2005" in str(match):
                index_files.append(match)
                break
    
    print(f"Found {len(index_files)} index files")
    
    index_data = {}
    
    for file_path in index_files:
        letter = file_path.name[0]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        extracted = extract_cmos_index(html_content, letter)
        
        if extracted:
            # Save JSON extract
            json_filename = f"index_{letter}.json"
            json_path = cmos_extracts / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(extracted, f, indent=2)
            
            # Create simplified HTML
            html_filename = f"index_{letter}.html"
            html_content = create_simplified_index_html(extracted)
            html_path = cmos_index / html_filename
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            index_data[letter] = {
                "file": html_filename,
                "letter": letter.upper(),
                "entries_count": len(extracted.get("entries", []))
            }
            
            print(f"  ✓ Index {letter.upper()}: {len(extracted.get('entries', []))} entries")
    
    # Create master index
    create_cmos_master_index(sections_data, index_data, citation_editor)
    
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Processed:")
    print(f"  - {len(sections_data)} sections")
    print(f"  - {len(index_data)} index pages")
    print(f"\nFiles saved to:")
    print(f"  - {cmos_extracts}")
    print(f"  - {cmos_sections}")
    print(f"  - {cmos_index}")

def create_simplified_cmos_html(extracted_data):
    """Create simplified HTML for CMOS section."""
    title = extracted_data.get("title", "CMOS Section")
    section_num = extracted_data.get("section_number", "")
    chapter = extracted_data.get("chapter", "")
    
    # Parse and clean the body HTML
    soup = BeautifulSoup(extracted_data.get("body_html", ""), "html.parser")
    
    # Remove any remaining chrome
    for tag in soup.find_all(['button', 'svg', 'script', 'style']):
        tag.decompose()
    
    body_content = str(soup)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS {section_num}: {title}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #FAFAFA;
        }}
        h1 {{ color: #1E3A8A; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; }}
        h2, h3 {{ color: #1E3A8A; margin-top: 1.5em; }}
        .section-info {{ 
            background: #E0E7FF; 
            padding: 12px; 
            border-left: 4px solid #1E3A8A;
            margin-bottom: 20px;
            font-size: 0.95em;
        }}
        .example {{ 
            background: #F5F5F5; 
            padding: 12px; 
            border-left: 3px solid #999;
            margin: 15px 0;
            font-style: italic;
        }}
        blockquote {{
            margin-left: 2em;
            padding-left: 1em;
            border-left: 3px solid #DDD;
        }}
        .section-number {{ 
            font-weight: bold; 
            color: #1E3A8A; 
        }}
    </style>
</head>
<body>
    <div class="section-info">
        <strong>CMOS Section {section_num}</strong>
        {f'<br>Chapter: {chapter}' if chapter else ''}
    </div>
    <h1>{title}</h1>
    {body_content}
</body>
</html>"""
    
    return html_content

def create_simplified_index_html(extracted_data):
    """Create simplified HTML for CMOS index."""
    letter = extracted_data.get("letter", "")
    entries = extracted_data.get("entries", [])
    
    # Group entries by first word for better organization
    grouped = {}
    for entry in entries:
        first_word = entry.split()[0] if entry else ""
        if first_word:
            if first_word not in grouped:
                grouped[first_word] = []
            grouped[first_word].append(entry)
    
    # Build entries HTML
    entries_html = ""
    for group, items in sorted(grouped.items()):
        entries_html += f"<h3>{group}</h3>\n<ul>\n"
        for item in items:
            entries_html += f"  <li>{item}</li>\n"
        entries_html += "</ul>\n"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS Index: {letter}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ 
            color: #1E3A8A; 
            border-bottom: 3px solid #1E3A8A; 
            padding-bottom: 10px;
            font-size: 2.5em;
        }}
        h3 {{
            color: #1E3A8A;
            margin-top: 1.5em;
            border-bottom: 1px solid #DDD;
            padding-bottom: 5px;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            padding: 5px 0;
            border-bottom: 1px dotted #EEE;
        }}
        .letter-nav {{
            background: #E0E7FF;
            padding: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .letter-nav a {{
            margin: 0 5px;
            text-decoration: none;
            color: #1E3A8A;
            font-weight: bold;
        }}
        .letter-nav a:hover {{
            text-decoration: underline;
        }}
        .current-letter {{
            background: #1E3A8A;
            color: white !important;
            padding: 2px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="letter-nav">
        {"".join([f'<a href="index_{l}.html" {"class='current-letter'" if l == letter.lower() else ""}>{l.upper()}</a>' for l in "abcdefghijklmnopqrstuvwxyz"])}
    </div>
    <h1>Index: {letter}</h1>
    <p>Total entries: {len(entries)}</p>
    {entries_html if entries_html else "<p>No entries found.</p>"}
</body>
</html>"""
    
    return html_content

def create_cmos_master_index(sections_data, index_data, output_dir):
    """Create master index for CMOS."""
    
    # Group sections by chapter
    chapters = {}
    for section_num, section_info in sections_data.items():
        chapter = section_info.get("chapter", "Unknown")
        if chapter not in chapters:
            chapters[chapter] = []
        chapters[chapter].append(section_info)
    
    index_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Chicago Manual of Style - Complete Index</title>
    <meta charset="utf-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            background: #F5F5F5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #1E3A8A;
            border-bottom: 4px solid #1E3A8A;
            padding-bottom: 15px;
            margin-bottom: 20px;
            font-size: 2.5em;
        }}
        h2 {{
            color: #1E3A8A;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #E0E7FF;
            padding-bottom: 8px;
        }}
        .stats {{
            background: #E0E7FF;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-around;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1E3A8A;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .sections-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .section-card {{
            background: #FAFAFA;
            border: 1px solid #E0E0E0;
            border-left: 3px solid #1E3A8A;
            padding: 12px;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s;
        }}
        .section-card:hover {{
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .section-number {{
            font-weight: bold;
            color: #1E3A8A;
        }}
        .index-nav {{
            background: #333;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-top: 30px;
        }}
        .index-nav a {{
            color: white;
            text-decoration: none;
            margin: 0 8px;
            padding: 5px 10px;
            background: #555;
            border-radius: 4px;
            display: inline-block;
        }}
        .index-nav a:hover {{
            background: #1E3A8A;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📘 Chicago Manual of Style - 18th Edition</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{len(sections_data)}</div>
                <div class="stat-label">Sections</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(chapters)}</div>
                <div class="stat-label">Chapters</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(index_data)}</div>
                <div class="stat-label">Index Pages</div>
            </div>
        </div>
"""
    
    # Add sections by chapter
    for chapter_name in sorted(chapters.keys()):
        if chapter_name and chapter_name != "Unknown":
            index_html += f'        <h2>{chapter_name}</h2>\n'
            index_html += '        <div class="sections-grid">\n'
            
            for section in sorted(chapters[chapter_name], key=lambda x: x.get("section_number", "")):
                index_html += f"""            <a href="cmos_sections/{section['file']}" class="section-card">
                <span class="section-number">{section.get('section_number', '')}</span>
                {section.get('section', section.get('title', 'Untitled'))}
            </a>
"""
            
            index_html += '        </div>\n'
    
    # Add index navigation
    index_html += """
        <h2>Alphabetical Index</h2>
        <div class="index-nav">
"""
    
    for letter in "abcdefghijklmnopqrstuvwxyz":
        if letter in index_data:
            index_html += f'            <a href="cmos_index/index_{letter}.html">{letter.upper()}</a>\n'
    
    index_html += """        </div>
    </div>
</body>
</html>"""
    
    # Save master index
    index_path = output_dir / "cmos_index.html"
    with open(index_path, 'w') as f:
        f.write(index_html)
    print(f"\n✅ Created master index: {index_path}")
    
    # Save JSON metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "sections_count": len(sections_data),
        "chapters_count": len(chapters),
        "index_pages_count": len(index_data),
        "sections": sections_data,
        "index_pages": index_data
    }
    
    json_path = output_dir / "cmos_metadata.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Created metadata: {json_path}")

if __name__ == "__main__":
    process_cmos_captures()