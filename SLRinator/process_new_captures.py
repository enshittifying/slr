#!/usr/bin/env python3
"""
Process new Bluebook captures and extract to citation-editor format
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
    
    # Check for dynamic content
    dyn = main.select_one("div.dynamic-content")
    content_root = None
    
    if dyn:
        for attr in ("version", "section", "parent", "slug", "element"):
            if dyn.has_attr(attr):
                result["meta"][attr] = dyn.get(attr)
        
        content_root = main.select_one("div.dynamic-content section div.m-auto.max-w-72ch")
        if not content_root:
            content_root = main.select_one("div.dynamic-content section div.leading-0")
            if not content_root:
                content_root = dyn
    else:
        index_section = main.select_one("section.w-screen.block.bg-white-400")
        if index_section:
            content_root = index_section
            for pager in content_root.select(".indexPager"):
                pager.decompose()
        else:
            content_root = main.select_one("div.pt-42") or main.select_one("section") or main
    
    if not content_root:
        content_root = main
    
    # Extract title
    h1 = content_root.find("h1")
    if h1:
        result["title"] = h1.get_text(" ", strip=True)
    else:
        page_title = soup.find("title")
        if page_title:
            result["title"] = page_title.get_text(" ", strip=True)
    
    # Clean noise
    for tag in content_root(["script", "style", "svg", "noscript"]):
        tag.decompose()
    
    for hidden in content_root.select('[style*="display:none"], [style*="display: none"], .hidden'):
        hidden.decompose()
    
    result["body_html"] = str(content_root).strip()
    result["body_text"] = content_root.get_text("\n", strip=True)
    
    # Additional metadata
    meta_description = soup.find("meta", {"name": "description"})
    if meta_description:
        result["meta"]["description"] = meta_description.get("content", "")
    
    canonical_link = soup.find("link", {"rel": "canonical"})
    if canonical_link:
        result["meta"]["canonical_url"] = canonical_link.get("href", "")
    
    return result

def create_relabeled_filename(original_filename):
    """Convert filename to relabeled format: b18-the-internet -> b18__the-internet"""
    # Remove timestamp
    base = re.sub(r'_\d{8}_\d{6}\.html$', '', original_filename)
    
    # Replace first hyphen with double underscore
    parts = base.split('-', 1)
    if len(parts) == 2:
        return f"{parts[0]}__{parts[1]}.html"
    return f"{base}.html"

def process_new_captures():
    """Process the new capture files"""
    
    # New capture files to process
    new_files = [
        "b18-the-internet_20250820_052112.html",
        "b16-periodical-materials_20250820_052105.html",
        "b12-statutes-rules-and-restatements_20250820_052054.html",
        "b5-quotations_20250820_052035.html",
        "t4-3-unofficial-treaty-sources_20250820_051922.html"
    ]
    
    # Directories
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    
    # Output directories
    captures_extracts_dir = Path("/Users/ben/app/citation-editor/captures_extracts")
    relabeled_extracts_dir = Path("/Users/ben/app/citation-editor/relabeled_extracts")
    lightbluebook_dir = Path("/Users/ben/app/citation-editor/lightbluebook2")
    
    # Ensure directories exist
    captures_extracts_dir.mkdir(exist_ok=True, parents=True)
    relabeled_extracts_dir.mkdir(exist_ok=True, parents=True)
    lightbluebook_dir.mkdir(exist_ok=True, parents=True)
    
    print("Processing new Bluebook captures")
    print("=" * 60)
    
    for html_file in new_files:
        html_path = captures_dir / html_file
        
        if not html_path.exists():
            print(f"✗ File not found: {html_file}")
            continue
            
        print(f"\nProcessing: {html_file}")
        
        try:
            # Read HTML content
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Extract content
            extracted = extract_bluebook(html_content)
            
            if extracted and (extracted["body_text"] or extracted["body_html"]):
                # Create base name without timestamp
                base_name = html_file.replace('.html', '')
                
                # Save to captures_extracts (with original naming)
                json_file = captures_extracts_dir / f"{base_name}.json"
                text_file = captures_extracts_dir / f"{base_name}.txt"
                html_file_clean = captures_extracts_dir / f"{base_name}_clean.html"
                
                # Save JSON
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(extracted, f, indent=2, ensure_ascii=False)
                
                # Save plain text
                with open(text_file, "w", encoding="utf-8") as f:
                    if extracted["title"]:
                        f.write(f"TITLE: {extracted['title']}\n")
                        f.write("=" * 60 + "\n\n")
                    if extracted["meta"]:
                        f.write("METADATA:\n")
                        for key, value in extracted["meta"].items():
                            f.write(f"  {key}: {value}\n")
                        f.write("\n" + "-" * 60 + "\n\n")
                    f.write("CONTENT:\n")
                    f.write(extracted["body_text"])
                
                # Save cleaned HTML
                with open(html_file_clean, "w", encoding="utf-8") as f:
                    f.write(extracted["body_html"])
                
                print(f"  ✓ Saved to captures_extracts: {json_file.name}")
                
                # Save to relabeled_extracts with new naming
                relabeled_name = create_relabeled_filename(html_file)
                relabeled_file = relabeled_extracts_dir / relabeled_name
                
                # Create simplified HTML for relabeled version
                simplified_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{extracted.get('title', 'Bluebook Rule')}</title>
    <meta charset="utf-8">
</head>
<body>
    {extracted["body_html"]}
</body>
</html>"""
                
                with open(relabeled_file, "w", encoding="utf-8") as f:
                    f.write(simplified_html)
                
                print(f"  ✓ Saved to relabeled_extracts: {relabeled_name}")
                
                # Also save to lightbluebook2
                lb_file = lightbluebook_dir / relabeled_name
                with open(lb_file, "w", encoding="utf-8") as f:
                    f.write(simplified_html)
                
                print(f"  ✓ Saved to lightbluebook2: {relabeled_name}")
                
            else:
                print(f"  ⚠ No content found to extract")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"Files saved to:")
    print(f"  - {captures_extracts_dir}")
    print(f"  - {relabeled_extracts_dir}")
    print(f"  - {lightbluebook_dir}")

if __name__ == "__main__":
    process_new_captures()