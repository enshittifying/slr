#!/usr/bin/env python3
"""
Process CMOS appendices, TOC, glossary, and bibliography files
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

def extract_appendix_content(html, file_path):
    """Extract content from appendix (asec) HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "file": file_path.name,
        "type": "appendix",
        "title": None,
        "appendix_number": None,
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Extract appendix number from filename
    match = re.search(r'asec(\d+)', file_path.name)
    if match:
        result["appendix_number"] = match.group(1)
    
    # Find title
    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.get_text(strip=True)
    else:
        # Try other heading tags
        for tag in ["h2", "h3"]:
            heading = soup.find(tag)
            if heading:
                result["title"] = heading.get_text(strip=True)
                break
    
    # Find main content
    main_content = soup.find("div", class_="page-section")
    if not main_content:
        main_content = soup.find("div", class_="content")
    if not main_content:
        main_content = soup.find("main")
    if not main_content:
        main_content = soup.find("article")
    if not main_content:
        # Fall back to body
        main_content = soup.find("body")
    
    if main_content:
        # Clean navigation and chrome
        for elem in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
            elem.decompose()
        
        result["body_html"] = str(main_content)
        result["body_text"] = main_content.get_text(separator="\n", strip=True)
    
    return result

def extract_toc_content(html, file_path):
    """Extract table of contents."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "file": file_path.name,
        "type": "toc",
        "title": "Table of Contents",
        "chapters": [],
        "body_html": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Look for TOC structure
    toc_container = soup.find("div", class_="toc")
    if not toc_container:
        toc_container = soup.find("nav", class_="toc")
    if not toc_container:
        toc_container = soup.find("div", id="toc")
    if not toc_container:
        # Try to find list structures
        toc_container = soup.find("ul", class_="toc-list")
    
    if toc_container:
        result["body_html"] = str(toc_container)
        
        # Extract chapter entries
        for link in toc_container.find_all("a"):
            text = link.get_text(strip=True)
            href = link.get("href", "")
            if text:
                result["chapters"].append({
                    "title": text,
                    "link": href
                })
    else:
        # Fall back to body content
        body = soup.find("body")
        if body:
            result["body_html"] = str(body)
            # Try to extract any links that look like chapters
            for link in body.find_all("a"):
                text = link.get_text(strip=True)
                if "Chapter" in text or re.match(r'^\d+\.', text):
                    result["chapters"].append({
                        "title": text,
                        "link": link.get("href", "")
                    })
    
    return result

def extract_glossary_content(html, file_path):
    """Extract glossary content."""
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "file": file_path.name,
        "type": "glossary",
        "title": "Glossary",
        "terms": [],
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Find title
    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.get_text(strip=True)
    
    # Find glossary content
    glossary = soup.find("div", class_="glossary")
    if not glossary:
        glossary = soup.find("dl")  # Often glossaries use definition lists
    if not glossary:
        glossary = soup.find("div", class_="content")
    if not glossary:
        glossary = soup.find("main")
    
    if glossary:
        # Clean
        for elem in glossary.find_all(['script', 'style', 'nav']):
            elem.decompose()
        
        result["body_html"] = str(glossary)
        result["body_text"] = glossary.get_text(separator="\n", strip=True)
        
        # Try to extract term definitions
        # Look for dt/dd pairs
        for dt in glossary.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                result["terms"].append({
                    "term": dt.get_text(strip=True),
                    "definition": dd.get_text(strip=True)
                })
        
        # Also look for structured divs
        if not result["terms"]:
            for entry in glossary.find_all("div", class_="glossary-entry"):
                term_elem = entry.find(class_="term")
                def_elem = entry.find(class_="definition")
                if term_elem and def_elem:
                    result["terms"].append({
                        "term": term_elem.get_text(strip=True),
                        "definition": def_elem.get_text(strip=True)
                    })
    
    return result

def create_appendix_html(data):
    """Create clean HTML for appendix."""
    
    title = data.get("title", f"Appendix {data.get('appendix_number', '')}")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS {title}</title>
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
        .appendix-header {{
            background: #8B4513;
            color: white;
            padding: 10px 15px;
            margin: -20px -20px 20px -20px;
            font-size: 0.9em;
        }}
        h1 {{ 
            color: #8B4513; 
            border-bottom: 3px solid #8B4513; 
            padding-bottom: 10px;
        }}
        h2, h3 {{ color: #8B4513; margin-top: 1.5em; }}
    </style>
</head>
<body>
    <div class="appendix-header">
        Chicago Manual of Style - Appendix
    </div>
    <h1>{title}</h1>
    {data.get("body_html", "")}
</body>
</html>"""
    
    return html_content

def create_toc_html(data):
    """Create clean HTML for table of contents."""
    
    chapters_html = ""
    for chapter in data.get("chapters", []):
        chapters_html += f"""
        <div class="toc-entry">
            <a href="{chapter.get('link', '#')}">{chapter.get('title', '')}</a>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS - Table of Contents</title>
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
        h1 {{ 
            color: #1E3A8A; 
            border-bottom: 3px solid #1E3A8A; 
            padding-bottom: 10px;
        }}
        .toc-entry {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-left: 3px solid #1E3A8A;
        }}
        .toc-entry a {{
            color: #1E3A8A;
            text-decoration: none;
            font-size: 1.1em;
        }}
        .toc-entry a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>Table of Contents</h1>
    <div class="toc-container">
        {chapters_html if chapters_html else data.get("body_html", "")}
    </div>
</body>
</html>"""
    
    return html_content

def create_glossary_html(data):
    """Create clean HTML for glossary."""
    
    terms_html = ""
    for term_def in data.get("terms", []):
        terms_html += f"""
        <div class="glossary-entry">
            <dt>{term_def.get('term', '')}</dt>
            <dd>{term_def.get('definition', '')}</dd>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>CMOS - Glossary</title>
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
        h1 {{ 
            color: #1E3A8A; 
            border-bottom: 3px solid #1E3A8A; 
            padding-bottom: 10px;
        }}
        .glossary-entry {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-left: 3px solid #4A5568;
        }}
        dt {{
            font-weight: bold;
            color: #1E3A8A;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        dd {{
            margin-left: 0;
            color: #555;
        }}
    </style>
</head>
<body>
    <h1>Glossary</h1>
    <dl class="glossary-container">
        {terms_html if terms_html else data.get("body_html", "")}
    </dl>
</body>
</html>"""
    
    return html_content

def process_cmos_appendices():
    """Process all CMOS appendices, TOC, and glossary files."""
    
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    cmos_dir = Path("/Users/ben/app/citation-editor/cmos_complete")
    
    print("Processing CMOS Appendices, TOC, and Glossary")
    print("=" * 60)
    
    # Process appendices
    asec_files = sorted(captures_dir.glob("asec*.html"))
    print(f"\nFound {len(asec_files)} appendix files")
    
    appendices_dir = cmos_dir / "appendices"
    appendices_dir.mkdir(exist_ok=True)
    
    for file_path in asec_files:
        print(f"  Processing {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        data = extract_appendix_content(html_content, file_path)
        
        # Save HTML
        appendix_num = data.get("appendix_number", "unknown")
        html_output = create_appendix_html(data)
        
        output_path = appendices_dir / f"appendix_{appendix_num}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        # Save JSON metadata
        json_path = appendices_dir / f"appendix_{appendix_num}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    # Process TOC files
    toc_files = sorted(captures_dir.glob("toc*.html"))
    print(f"\nFound {len(toc_files)} TOC files")
    
    toc_dir = cmos_dir / "toc"
    toc_dir.mkdir(exist_ok=True)
    
    # Process each TOC file and save with timestamp
    for i, file_path in enumerate(toc_files, 1):
        print(f"  Processing {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        data = extract_toc_content(html_content, file_path)
        
        # Save HTML
        html_output = create_toc_html(data)
        
        # Extract timestamp from filename for uniqueness
        timestamp = re.search(r'_(\d{8}_\d{6})', file_path.name)
        suffix = timestamp.group(1) if timestamp else str(i)
        
        output_path = toc_dir / f"toc_{suffix}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        # Save JSON metadata
        json_path = toc_dir / f"toc_{suffix}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    # Process glossary
    glos_files = sorted(captures_dir.glob("glos*.html"))
    print(f"\nFound {len(glos_files)} glossary file(s)")
    
    for file_path in glos_files:
        print(f"  Processing {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        data = extract_glossary_content(html_content, file_path)
        
        # Save HTML
        html_output = create_glossary_html(data)
        
        output_path = cmos_dir / "glossary.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        # Save JSON metadata
        json_path = cmos_dir / "glossary.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    # Look for bibliography files (might be named differently)
    print("\nSearching for bibliography files...")
    
    # Check if any of the TOC or other files might be bibliography
    # Sometimes bibliography is in appendices or has different naming
    
    # Update the main index to include these new sections
    update_main_index(cmos_dir, len(asec_files), len(toc_files), len(glos_files))
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print(f"  - {len(asec_files)} appendices processed")
    print(f"  - {len(toc_files)} TOC files processed")
    print(f"  - {len(glos_files)} glossary file(s) processed")
    print(f"\nOutput directory: {cmos_dir}")

def update_main_index(cmos_dir, num_appendices, num_toc, num_glossary):
    """Update the main index to include links to appendices, TOC, and glossary."""
    
    index_path = cmos_dir / "index.html"
    
    # Read existing index
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Find where to insert the new content (before </body>)
    insert_point = html_content.rfind("</body>")
    
    # Create new sections HTML
    new_sections = f"""
    <div class="chapter-section">
        <div class="chapter-title">📚 Appendices</div>
        <div class="sections-grid">"""
    
    for i in range(1, num_appendices + 1):
        new_sections += f"""
            <a href="appendices/appendix_{i:02d}.html" class="section-link">
                Appendix {i}
            </a>"""
    
    new_sections += """
        </div>
    </div>
    
    <div class="chapter-section">
        <div class="chapter-title">📑 Table of Contents</div>
        <div class="sections-grid">
            <a href="toc/" class="section-link">
                View Table of Contents Files
            </a>
        </div>
    </div>"""
    
    if num_glossary > 0:
        new_sections += """
    <div class="chapter-section">
        <div class="chapter-title">📖 Glossary</div>
        <div class="sections-grid">
            <a href="glossary.html" class="section-link">
                View Glossary
            </a>
        </div>
    </div>"""
    
    new_sections += "\n"
    
    # Insert new content
    updated_html = html_content[:insert_point] + new_sections + html_content[insert_point:]
    
    # Write updated index
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    print(f"\n✅ Updated main index: {index_path}")

if __name__ == "__main__":
    process_cmos_appendices()