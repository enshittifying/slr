#!/usr/bin/env python3
"""
Bluebook HTML Content Extractor
Extracts useful content from captured Bluebook HTML files
"""

import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

def extract_bluebook(html):
    """
    Extract content from Bluebook HTML following the specified patterns.
    Returns a dictionary with title, metadata, and cleaned content.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Find main content area
    main = soup.select_one("main#main-content")
    if not main:
        # Fallback to body if main not found
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
    
    # Initialize result structure
    result = {
        "title": None,
        "meta": {},
        "body_html": "",
        "body_text": "",
        "extracted_at": datetime.now().isoformat()
    }
    
    # Check for dynamic content (rules/tables/whitepages detail pages)
    dyn = main.select_one("div.dynamic-content")
    content_root = None
    
    if dyn:
        # Capture metadata from dynamic-content attributes
        for attr in ("version", "section", "parent", "slug", "element"):
            if dyn.has_attr(attr):
                result["meta"][attr] = dyn.get(attr)
        
        # Find the readable content column
        content_root = main.select_one("div.dynamic-content section div.m-auto.max-w-72ch")
        if not content_root:
            # Try alternative selectors
            content_root = main.select_one("div.dynamic-content section div.leading-0")
            if not content_root:
                content_root = dyn
    else:
        # Check for Index pages pattern
        index_section = main.select_one("section.w-screen.block.bg-white-400")
        if index_section:
            content_root = index_section
            # Remove index pager if present (keep terms only)
            for pager in content_root.select(".indexPager"):
                pager.decompose()
        else:
            # Fallback: look for any content wrapper
            content_root = main.select_one("div.pt-42") or main.select_one("section") or main
    
    if not content_root:
        content_root = main
    
    # Extract title from h1
    h1 = content_root.find("h1")
    if h1:
        result["title"] = h1.get_text(" ", strip=True)
    else:
        # Fallback to page title
        page_title = soup.find("title")
        if page_title:
            result["title"] = page_title.get_text(" ", strip=True)
    
    # Clean noise: scripts, styles, svg, hidden elements
    for tag in content_root(["script", "style", "svg", "noscript"]):
        tag.decompose()
    
    # Remove hidden elements
    for hidden in content_root.select('[style*="display:none"], [style*="display: none"], .hidden'):
        hidden.decompose()
    
    # Extract structured content
    result["body_html"] = str(content_root).strip()
    result["body_text"] = content_root.get_text("\n", strip=True)
    
    # Additional metadata from head
    meta_description = soup.find("meta", {"name": "description"})
    if meta_description:
        result["meta"]["description"] = meta_description.get("content", "")
    
    canonical_link = soup.find("link", {"rel": "canonical"})
    if canonical_link:
        result["meta"]["canonical_url"] = canonical_link.get("href", "")
    
    return result

def process_captures_folder():
    """
    Process all HTML files in the captures folder and extract content.
    """
    base_dir = Path("/Users/ben/app/SLRinator")
    captures_dir = base_dir / "captures"
    extracts_dir = base_dir / "captures_extracts"
    
    # Ensure directories exist
    extracts_dir.mkdir(exist_ok=True)
    
    # Track processing stats
    stats = {
        "total_files": 0,
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "files": []
    }
    
    # Get all HTML files in captures folder
    html_files = list(captures_dir.glob("*.html"))
    stats["total_files"] = len(html_files)
    
    print(f"Found {len(html_files)} HTML files to process")
    print("=" * 60)
    
    for html_file in html_files:
        print(f"\nProcessing: {html_file.name}")
        
        try:
            # Read HTML content
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Extract content
            extracted = extract_bluebook(html_content)
            
            if extracted and (extracted["body_text"] or extracted["body_html"]):
                # Create output filenames
                base_name = html_file.stem
                json_file = extracts_dir / f"{base_name}.json"
                text_file = extracts_dir / f"{base_name}.txt"
                html_file_clean = extracts_dir / f"{base_name}_clean.html"
                
                # Save JSON with all data
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(extracted, f, indent=2, ensure_ascii=False)
                
                # Save plain text version
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
                
                print(f"  ✓ Extracted: {len(extracted['body_text'])} chars")
                print(f"  ✓ Saved: {json_file.name}, {text_file.name}, {html_file_clean.name}")
                
                stats["processed"] += 1
                stats["files"].append({
                    "source": html_file.name,
                    "title": extracted["title"],
                    "size": len(extracted["body_text"])
                })
            else:
                print(f"  ⚠ No content found to extract")
                stats["skipped"] += 1
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            stats["failed"] += 1
    
    # Save processing stats
    stats_file = extracts_dir / "extraction_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total files:     {stats['total_files']}")
    print(f"Processed:       {stats['processed']}")
    print(f"Skipped:         {stats['skipped']}")
    print(f"Failed:          {stats['failed']}")
    print(f"\nResults saved to: {extracts_dir}")
    print(f"Stats saved to:   {stats_file.name}")
    
    return stats

def main():
    """Main entry point"""
    print("Bluebook HTML Content Extractor")
    print("================================\n")
    
    # Check if beautifulsoup4 is installed
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing beautifulsoup4...")
        os.system("pip3 install --user --break-system-packages beautifulsoup4")
        from bs4 import BeautifulSoup
    
    process_captures_folder()

if __name__ == "__main__":
    main()