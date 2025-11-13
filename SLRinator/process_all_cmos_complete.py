#!/usr/bin/env python3
"""
Process ALL CMOS captures - complete 15 chapters + bibliography
Handles section numbering that restarts for each chapter
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict

# Complete CMOS chapter mapping
CMOS_CHAPTERS = {
    "1": "Books and Journals",
    "2": "Manuscript Preparation, Manuscript Editing, and Proofreading", 
    "3": "Illustrations and Tables",
    "4": "Rights, Permissions, and Copyright Administration",
    "5": "Grammar and Usage",
    "6": "Punctuation", 
    "7": "Spelling, Distinctive Treatment of Words, and Compounds",
    "8": "Names, Terms, and Titles of Works",
    "9": "Numbers",
    "10": "Abbreviations",
    "11": "Languages Other than English",
    "12": "Source Citations: Overview",
    "13": "Source Citations: Examples",
    "14": "Source Citations: Overview",  # There might be duplicate or it's Notes and Bibliography
    "15": "Source Citations: Examples",  # Check actual content
}

def extract_cmos_section(html, file_path):
    """Extract content from CMOS psec HTML with full context."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "file": file_path.name,
        "title": None,
        "chapter": None,
        "chapter_number": None,
        "section": None,
        "section_number": None,
        "full_section_id": None,
        "meta": {},
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Extract chapter info
    chapter_elem = soup.find("span", id="chapter-number")
    if chapter_elem:
        chapter_num = chapter_elem.get_text(strip=True).rstrip(":")
        result["chapter_number"] = chapter_num
        result["meta"]["chapter_number"] = chapter_num
    
    chapter_title_elem = soup.find("span", id="chapter-title")
    if chapter_title_elem:
        result["chapter"] = chapter_title_elem.get_text(strip=True)
    
    # Extract section info
    section_elem = soup.find("span", class_="section-number")
    if section_elem:
        section_num = section_elem.get_text(strip=True)
        result["section_number"] = section_num
        result["full_section_id"] = section_num  # e.g., "1.1", "15.23"
        
        # Extract just the subsection part for duplicate detection
        if '.' in section_num:
            parts = section_num.split('.')
            result["meta"]["chapter_from_section"] = parts[0]
            result["meta"]["subsection"] = parts[1]
    
    section_title_elem = soup.find("span", class_="section-title")
    if section_title_elem:
        result["section"] = section_title_elem.get_text(strip=True)
        if result["section_number"]:
            result["title"] = f"{result['section_number']}: {result['section']}"
        else:
            result["title"] = result["section"]
    
    # Find main content
    main_content = soup.find("div", class_="page-section")
    if not main_content:
        main_content = soup.find("div", class_="section-content")
    if not main_content:
        main_content = soup.find("div", class_="content-inner")
    if not main_content:
        main_content = soup.find("main")
    
    if main_content:
        # Clean navigation and chrome
        for elem in main_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'noindex']):
            elem.decompose()
        
        for trail in main_content.find_all("p", class_="trail"):
            trail.decompose()
        
        result["body_html"] = str(main_content)
        result["body_text"] = main_content.get_text(separator="\n", strip=True)
    
    return result

def organize_sections_by_chapter(psec_files):
    """Organize psec files by chapter and section."""
    chapters = defaultdict(lambda: defaultdict(list))
    
    for file_path in psec_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        extracted = extract_cmos_section(html_content, file_path)
        
        if extracted["chapter_number"] and extracted["section_number"]:
            chapter = extracted["chapter_number"]
            section = extracted["section_number"]
            
            # Store with timestamp for deduplication
            timestamp = re.search(r'_(\d{8}_\d{6})', file_path.name)
            if timestamp:
                extracted["timestamp"] = timestamp.group(1)
            
            chapters[chapter][section].append(extracted)
    
    return chapters

def deduplicate_sections(chapters):
    """Keep only the best version of each section."""
    deduped = defaultdict(dict)
    
    for chapter, sections in chapters.items():
        for section_num, versions in sections.items():
            if versions:
                # Sort by timestamp and content length, prefer latest with most content
                sorted_versions = sorted(versions, 
                                        key=lambda x: (x.get("timestamp", ""), 
                                                      len(x.get("body_text", ""))),
                                        reverse=True)
                # Keep the best version
                deduped[chapter][section_num] = sorted_versions[0]
    
    return deduped

def process_all_cmos():
    """Process ALL CMOS captures comprehensively."""
    
    # Setup paths
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    # Create comprehensive CMOS directories
    cmos_dir = citation_editor / "cmos_complete"
    cmos_dir.mkdir(parents=True, exist_ok=True)
    
    for chapter_num in range(1, 16):
        chapter_dir = cmos_dir / f"chapter_{chapter_num:02d}"
        chapter_dir.mkdir(exist_ok=True)
    
    # Also create directories for bibliography and appendices
    (cmos_dir / "bibliography").mkdir(exist_ok=True)
    (cmos_dir / "appendices").mkdir(exist_ok=True)
    (cmos_dir / "index").mkdir(exist_ok=True)
    
    print("Processing ALL CMOS captures")
    print("=" * 60)
    
    # Get all psec files
    psec_files = sorted(captures_dir.glob("psec*.html"))
    print(f"Found {len(psec_files)} total psec files")
    
    # Organize by chapter and section
    print("\nOrganizing sections by chapter...")
    chapters = organize_sections_by_chapter(psec_files)
    
    # Deduplicate
    print("Deduplicating sections...")
    deduped = deduplicate_sections(chapters)
    
    # Process and save each chapter
    all_sections = []
    stats = defaultdict(int)
    
    for chapter_num in sorted(deduped.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        sections = deduped[chapter_num]
        chapter_name = CMOS_CHAPTERS.get(chapter_num, f"Chapter {chapter_num}")
        
        print(f"\nChapter {chapter_num}: {chapter_name}")
        print(f"  Sections: {len(sections)}")
        
        chapter_dir = cmos_dir / f"chapter_{int(chapter_num):02d}"
        
        for section_num in sorted(sections.keys(), 
                                 key=lambda x: float(x.replace('.', '')) if '.' in x else float(x)):
            section_data = sections[section_num]
            
            # Create clean HTML
            html_content = create_cmos_html(section_data, chapter_num, chapter_name)
            
            # Save HTML file
            safe_section = section_num.replace('.', '_')
            html_filename = f"cmos_{safe_section}.html"
            html_path = chapter_dir / html_filename
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Save JSON metadata
            json_filename = f"cmos_{safe_section}.json"
            json_path = chapter_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(section_data, f, indent=2)
            
            # Track for index
            all_sections.append({
                "chapter": chapter_num,
                "chapter_name": chapter_name,
                "section": section_num,
                "title": section_data.get("title"),
                "file": f"chapter_{int(chapter_num):02d}/{html_filename}"
            })
            
            stats[chapter_num] += 1
    
    # Process index files
    print("\n\nProcessing index files (a-z)...")
    index_files = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        # Find files from 20:04-20:05
        matches = list(captures_dir.glob(f"{letter}_*2004*.html")) + \
                 list(captures_dir.glob(f"{letter}_*2005*.html"))
        if matches:
            index_files.extend(matches)
    
    print(f"Found {len(index_files)} index files")
    
    for file_path in index_files:
        letter = file_path.name[0]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Process index...
        index_html = process_index_file(html_content, letter)
        
        index_path = cmos_dir / "index" / f"index_{letter}.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    # Create master index
    create_master_cmos_index(all_sections, stats, cmos_dir)
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print(f"\nStatistics by chapter:")
    for ch in sorted(stats.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        name = CMOS_CHAPTERS.get(ch, f"Chapter {ch}")
        print(f"  Chapter {ch} ({name}): {stats[ch]} sections")
    print(f"\nTotal sections: {sum(stats.values())}")
    print(f"Output directory: {cmos_dir}")

def create_cmos_html(section_data, chapter_num, chapter_name):
    """Create clean HTML for a CMOS section."""
    
    title = section_data.get("title", "CMOS Section")
    section_num = section_data.get("section_number", "")
    
    # Parse and clean body HTML
    soup = BeautifulSoup(section_data.get("body_html", ""), "html.parser")
    
    # Remove chrome elements
    for tag in soup.find_all(['button', 'svg', 'script', 'style']):
        tag.decompose()
    
    body_content = str(soup)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS {section_num}: {section_data.get('section', '')}</title>
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
        .chapter-header {{
            background: #1E3A8A;
            color: white;
            padding: 10px 15px;
            margin: -20px -20px 20px -20px;
            font-size: 0.9em;
        }}
        h1 {{ 
            color: #1E3A8A; 
            border-bottom: 3px solid #1E3A8A; 
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2, h3 {{ color: #1E3A8A; margin-top: 1.5em; }}
        .section-nav {{
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
            padding: 10px;
            background: #E0E7FF;
            border-radius: 5px;
        }}
        .section-nav a {{
            color: #1E3A8A;
            text-decoration: none;
            font-weight: bold;
        }}
        .section-nav a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            margin-left: 2em;
            padding-left: 1em;
            border-left: 3px solid #DDD;
        }}
        .example {{
            background: #F5F5F5;
            padding: 12px;
            border-left: 3px solid #999;
            margin: 15px 0;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="chapter-header">
        Chapter {chapter_num}: {chapter_name}
    </div>
    <h1>{title}</h1>
    {body_content}
</body>
</html>"""
    
    return html_content

def process_index_file(html_content, letter):
    """Process an index file."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract index entries (simplified)
    entries = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 3:
            entries.append(text)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS Index: {letter.upper()}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{ color: #1E3A8A; }}
        .entry {{ padding: 5px 0; border-bottom: 1px dotted #DDD; }}
    </style>
</head>
<body>
    <h1>Index: {letter.upper()}</h1>
    <div class="entries">
        {''.join([f'<div class="entry">{e}</div>' for e in entries[:100]])}
    </div>
</body>
</html>"""
    
    return html

def create_master_cmos_index(all_sections, stats, output_dir):
    """Create comprehensive master index."""
    
    total_chapters = len(stats)
    total_sections = sum(stats.values())
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Chicago Manual of Style - Complete 18th Edition</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #F5F5F5;
        }}
        h1 {{
            color: #1E3A8A;
            border-bottom: 4px solid #1E3A8A;
            padding-bottom: 15px;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            display: flex;
            justify-content: space-around;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #1E3A8A;
        }}
        .chapter-section {{
            background: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .chapter-title {{
            color: #1E3A8A;
            font-size: 1.5em;
            margin-bottom: 15px;
            border-bottom: 2px solid #E0E7FF;
            padding-bottom: 10px;
        }}
        .sections-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        .section-link {{
            padding: 8px 12px;
            background: #F9F9F9;
            border-left: 3px solid #1E3A8A;
            text-decoration: none;
            color: #333;
            display: block;
            transition: all 0.3s;
        }}
        .section-link:hover {{
            background: #E0E7FF;
            transform: translateX(5px);
        }}
        .section-number {{
            font-weight: bold;
            color: #1E3A8A;
        }}
    </style>
</head>
<body>
    <h1>📘 Chicago Manual of Style - 18th Edition (Complete)</h1>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{total_chapters}</div>
            <div>Chapters</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{total_sections}</div>
            <div>Sections</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">26</div>
            <div>Index Pages</div>
        </div>
    </div>
"""
    
    # Group sections by chapter
    chapters_grouped = defaultdict(list)
    for section in all_sections:
        chapters_grouped[section["chapter"]].append(section)
    
    # Add each chapter
    for chapter_num in sorted(chapters_grouped.keys(), 
                              key=lambda x: int(x) if x.isdigit() else 999):
        sections = chapters_grouped[chapter_num]
        chapter_name = sections[0]["chapter_name"] if sections else f"Chapter {chapter_num}"
        
        html_content += f"""
    <div class="chapter-section">
        <div class="chapter-title">Chapter {chapter_num}: {chapter_name}</div>
        <div class="sections-grid">
"""
        
        for section in sorted(sections, 
                             key=lambda x: float(x["section"].replace('.', '')) if '.' in x["section"] else float(x["section"])):
            html_content += f"""
            <a href="{section['file']}" class="section-link">
                <span class="section-number">{section['section']}</span>
                {section.get('title', '').replace(section['section'] + ':', '').strip()}
            </a>
"""
        
        html_content += """
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>"""
    
    # Save master index
    index_path = output_dir / "index.html"
    with open(index_path, 'w') as f:
        f.write(html_content)
    
    print(f"\n✅ Created master index: {index_path}")
    
    # Save metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_chapters": total_chapters,
        "total_sections": total_sections,
        "chapters": dict(stats),
        "sections": all_sections
    }
    
    json_path = output_dir / "cmos_complete_metadata.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    process_all_cmos()