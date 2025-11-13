#!/usr/bin/env python3
"""
Fix ALL CMOS capture files - both original captures and processed files
Fixes image paths, links, and other references
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def fix_paths_in_content(content):
    """Fix all paths in HTML content."""
    
    soup = BeautifulSoup(content, 'html.parser')
    modified = False
    
    # Fix img tags
    for img in soup.find_all('img'):
        src = img.get('src', '')
        new_src = None
        
        # Convert various path patterns
        if src.startswith('/dam/'):
            new_src = f"https://www.chicagomanualofstyle.org{src}"
        elif src.startswith('/.resources/'):
            new_src = f"https://www.chicagomanualofstyle.org{src}"
        elif src.startswith('/book/'):
            new_src = f"https://www.chicagomanualofstyle.org{src}"
        elif 'file:///' in src:
            # Remove file:/// and add domain
            path = src.replace('file:///', '/')
            new_src = f"https://www.chicagomanualofstyle.org{path}"
        
        if new_src and new_src != src:
            img['src'] = new_src
            modified = True
    
    # Fix link tags (CSS)
    for link in soup.find_all('link'):
        href = link.get('href', '')
        new_href = None
        
        if href.startswith('/.resources/'):
            new_href = f"https://www.chicagomanualofstyle.org{href}"
        elif href.startswith('/dam/'):
            new_href = f"https://www.chicagomanualofstyle.org{href}"
        
        if new_href and new_href != href:
            link['href'] = new_href
            modified = True
    
    # Fix script tags
    for script in soup.find_all('script'):
        src = script.get('src', '')
        if src:
            new_src = None
            
            if src.startswith('/.resources/'):
                new_src = f"https://www.chicagomanualofstyle.org{src}"
            elif src.startswith('/docroot/'):
                new_src = f"https://www.chicagomanualofstyle.org{src}"
            elif not src.startswith(('http://', 'https://', '//')):
                # Relative path
                new_src = f"https://www.chicagomanualofstyle.org/{src.lstrip('/')}"
            
            if new_src and new_src != src:
                script['src'] = new_src
                modified = True
    
    # Fix anchor tags with local references
    for a in soup.find_all('a'):
        href = a.get('href', '')
        new_href = None
        
        if href.startswith('/book/'):
            new_href = f"https://www.chicagomanualofstyle.org{href}"
        elif href.startswith('/dam/'):
            new_href = f"https://www.chicagomanualofstyle.org{href}"
        elif 'psec' in href and not href.startswith('http'):
            # Convert relative psec links
            if href.startswith('/'):
                new_href = f"https://www.chicagomanualofstyle.org{href}"
            else:
                new_href = f"https://www.chicagomanualofstyle.org/book/ed18/{href}"
        
        if new_href and new_href != href:
            a['href'] = new_href
            modified = True
    
    # Fix any style attributes with URLs
    for elem in soup.find_all(style=True):
        style = elem.get('style', '')
        if 'url(' in style:
            new_style = style
            
            # Fix background images and other URL references
            patterns = [
                (r'url\(["\']?(/.resources/[^"\')]+)["\']?\)', r'url(https://www.chicagomanualofstyle.org\1)'),
                (r'url\(["\']?(/dam/[^"\')]+)["\']?\)', r'url(https://www.chicagomanualofstyle.org\1)'),
                (r'url\(["\']?(/book/[^"\')]+)["\']?\)', r'url(https://www.chicagomanualofstyle.org\1)'),
            ]
            
            for pattern, replacement in patterns:
                new_style = re.sub(pattern, replacement, new_style)
            
            if new_style != style:
                elem['style'] = new_style
                modified = True
    
    # Fix meta tags with URLs
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if content.startswith('/dam/'):
            meta['content'] = f"https://www.chicagomanualofstyle.org{content}"
            modified = True
    
    return str(soup) if modified else None

def process_file(file_path, stats):
    """Process a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_content = fix_paths_in_content(content)
        
        if fixed_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            stats['fixed'] += 1
            return True
        else:
            stats['unchanged'] += 1
            return False
    except Exception as e:
        print(f"  ✗ Error processing {file_path.name}: {e}")
        stats['errors'] += 1
        return False

def fix_all_cmos_files():
    """Fix all CMOS files - captures and processed."""
    
    print("CMOS Comprehensive Path Fixer")
    print("=" * 60)
    
    stats = {
        'fixed': 0,
        'unchanged': 0,
        'errors': 0,
        'total': 0
    }
    
    # Process original capture files
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    
    # Process psec files
    print("\nProcessing original psec capture files...")
    psec_files = sorted(captures_dir.glob("psec*.html"))
    print(f"Found {len(psec_files)} psec files")
    
    for idx, file_path in enumerate(psec_files, 1):
        if idx % 100 == 0:
            print(f"  Processing {idx}/{len(psec_files)}... (Fixed: {stats['fixed']}, Unchanged: {stats['unchanged']})")
        process_file(file_path, stats)
        stats['total'] += 1
    
    # Process index files (a-z from 20:04-20:05)
    print("\nProcessing original index capture files...")
    index_files = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        for file in captures_dir.glob(f"{letter}_*2004*.html"):
            index_files.append(file)
        for file in captures_dir.glob(f"{letter}_*2005*.html"):
            index_files.append(file)
    
    print(f"Found {len(index_files)} index files")
    
    for file_path in index_files:
        process_file(file_path, stats)
        stats['total'] += 1
    
    # Process already extracted files
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    # Process CMOS sections
    sections_dir = citation_editor / "cmos_sections"
    if sections_dir.exists():
        print("\nProcessing extracted section files...")
        section_files = list(sections_dir.glob("*.html"))
        print(f"Found {len(section_files)} section files")
        
        for idx, file_path in enumerate(section_files, 1):
            if idx % 50 == 0:
                print(f"  Processing {idx}/{len(section_files)}...")
            process_file(file_path, stats)
            stats['total'] += 1
    
    # Process CMOS index files
    index_dir = citation_editor / "cmos_index"
    if index_dir.exists():
        print("\nProcessing extracted index files...")
        index_files = list(index_dir.glob("*.html"))
        print(f"Found {len(index_files)} index files")
        
        for file_path in index_files:
            process_file(file_path, stats)
            stats['total'] += 1
    
    # Process other CMOS-related HTML files
    for pattern in ["*.html"]:
        for file_path in citation_editor.glob(pattern):
            if 'cmos' in file_path.name.lower():
                process_file(file_path, stats)
                stats['total'] += 1
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print(f"\nStatistics:")
    print(f"  Total files processed: {stats['total']}")
    print(f"  Files fixed: {stats['fixed']}")
    print(f"  Files unchanged: {stats['unchanged']}")
    print(f"  Errors: {stats['errors']}")
    
    return stats

def verify_fixes():
    """Verify that fixes were applied correctly."""
    print("\nVerifying fixes...")
    
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    
    # Check a sample psec file
    sample_files = list(captures_dir.glob("psec001*.html"))[:1]
    
    for file_path in sample_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for problematic patterns
        problems = []
        if '/.resources/' in content and 'https://www.chicagomanualofstyle.org' not in content:
            problems.append("Still has local .resources paths")
        if '/dam/' in content and not 'https://www.chicagomanualofstyle.org/dam/' in content:
            problems.append("Still has local /dam/ paths")
        if 'href="/book/' in content:
            problems.append("Still has local /book/ links")
        
        if problems:
            print(f"  ✗ {file_path.name}: {', '.join(problems)}")
        else:
            # Check that fixes were applied
            if 'https://www.chicagomanualofstyle.org' in content:
                print(f"  ✓ {file_path.name}: Properly fixed")
            else:
                print(f"  ? {file_path.name}: No URLs found (might not need fixing)")

if __name__ == "__main__":
    stats = fix_all_cmos_files()
    
    if stats['fixed'] > 0:
        verify_fixes()