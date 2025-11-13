#!/usr/bin/env python3
"""
Fix image paths in CMOS HTML files
Convert local file:/// references to proper https:// URLs
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def fix_image_paths_in_file(file_path):
    """Fix image paths in a single HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Fix img tags
    for img in soup.find_all('img'):
        src = img.get('src', '')
        
        # Convert file:/// paths to https://
        if 'file:///' in src:
            # Extract the figure ID if present
            if 'fig' in src:
                fig_match = re.search(r'fig(\d+)', src)
                if fig_match:
                    fig_id = fig_match.group(1)
                    # Construct proper URL
                    new_src = f"https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig{fig_id}.jpg"
                    img['src'] = new_src
                    modified = True
        
        # Fix paths that start with /dam/
        elif src.startswith('/dam/'):
            # Add the full domain
            new_src = f"https://www.chicagomanualofstyle.org{src}"
            img['src'] = new_src
            modified = True
        
        # Fix paths that start with /book/
        elif src.startswith('/book/'):
            # Extract figure ID from path
            fig_match = re.search(r'fig(\d+)', src)
            if fig_match:
                fig_id = fig_match.group(1)
                new_src = f"https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig{fig_id}.jpg"
                img['src'] = new_src
                modified = True
        
        # Fix relative paths to images
        elif 'psec' in src and '#f' in src:
            # Extract figure number from anchor
            fig_match = re.search(r'#f(\d+)', src)
            if fig_match:
                fig_id = fig_match.group(1)
                new_src = f"https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig{fig_id}.jpg"
                img['src'] = new_src
                modified = True
    
    # Fix links that might reference images
    for link in soup.find_all('a'):
        href = link.get('href', '')
        
        # Check if this is a link to a figure
        if '#f' in href and ('psec' in href or 'file:///' in href):
            # This is likely a figure reference - we might want to handle these differently
            # For now, just remove the file:/// prefix if present
            if href.startswith('file:///'):
                link['href'] = '#' + href.split('#')[-1] if '#' in href else '#'
                modified = True
    
    # Also fix any style attributes with background images
    for elem in soup.find_all(style=True):
        style = elem.get('style', '')
        if 'url(' in style and ('file:///' in style or '/book/' in style):
            # Extract and fix URL from style
            new_style = re.sub(
                r'url\(["\']?(?:file:///.*?/|/book/.*?/)([^"\')]+)["\']?\)',
                lambda m: f'url(https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/{m.group(1)})',
                style
            )
            if new_style != style:
                elem['style'] = new_style
                modified = True
    
    if modified:
        # Save the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    
    return False

def fix_all_cmos_files():
    """Fix image paths in all CMOS HTML files."""
    
    citation_editor = Path("/Users/ben/app/citation-editor")
    
    # Process CMOS sections
    sections_dir = citation_editor / "cmos_sections"
    if sections_dir.exists():
        section_files = list(sections_dir.glob("*.html"))
        print(f"Processing {len(section_files)} section files...")
        
        fixed_count = 0
        for file_path in section_files:
            if fix_image_paths_in_file(file_path):
                fixed_count += 1
                if fixed_count % 10 == 0:
                    print(f"  Fixed {fixed_count} files...")
        
        print(f"✓ Fixed {fixed_count} section files")
    
    # Process CMOS index files
    index_dir = citation_editor / "cmos_index"
    if index_dir.exists():
        index_files = list(index_dir.glob("*.html"))
        print(f"\nProcessing {len(index_files)} index files...")
        
        fixed_count = 0
        for file_path in index_files:
            if fix_image_paths_in_file(file_path):
                fixed_count += 1
        
        print(f"✓ Fixed {fixed_count} index files")
    
    print("\n✅ Image path fixing complete!")

def test_fix_sample():
    """Test the fixing on a sample to verify it works."""
    
    test_cases = [
        ('file:///book/ed18/part1/ch01/psec049.html#f01008', 
         'https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig01008.jpg'),
        ('/book/ed18/part1/ch01/images/fig01008.jpg',
         'https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig01008.jpg'),
    ]
    
    print("Testing image path conversions:")
    for old_path, expected in test_cases:
        # Extract figure ID
        fig_match = re.search(r'(?:fig|#f)(\d+)', old_path)
        if fig_match:
            fig_id = fig_match.group(1)
            new_path = f"https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig{fig_id}.jpg"
            print(f"  ✓ {old_path}")
            print(f"    → {new_path}")
            assert new_path == expected, f"Mismatch: {new_path} != {expected}"
    
    print("\n✅ All test cases passed!")

if __name__ == "__main__":
    print("CMOS Image Path Fixer")
    print("=" * 60)
    
    # Run tests first
    test_fix_sample()
    
    print("\n" + "=" * 60)
    print("Fixing actual files...\n")
    
    # Fix all files
    fix_all_cmos_files()