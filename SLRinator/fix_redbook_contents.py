#!/usr/bin/env python3
"""
Fix Redbook HTML files to properly extract and display Contents sections
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def fix_redbook_contents():
    """Fix the Contents sections in Redbook HTML files"""
    
    redbook_dir = Path("/Users/ben/app/citation-editor/redbook_processed")
    captures_dir = Path("/Users/ben/app/SLRinator/captures")
    
    # Get all Redbook HTML files
    html_files = sorted(redbook_dir.glob("rb_*.html"))
    
    fixed_count = 0
    
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this file has empty list items in Contents
        if '<ul class="space-y-2"><li></li>' in content:
            print(f"Fixing: {html_file.name}")
            
            # Parse the HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the Contents section
            contents_div = soup.find('div', class_='mt-8 p-6 bg-gray-50 border border-gray-200 rounded-lg')
            
            if contents_div:
                # Find the ul with empty list items
                ul = contents_div.find('ul')
                
                if ul:
                    # Try to find corresponding original capture to get the real content
                    # Extract section number from filename
                    section_match = re.search(r'rb_\d+__(.+)\.html', html_file.name)
                    
                    if section_match:
                        # Look for matching capture file
                        capture_pattern = section_match.group(1).replace('-', '*')
                        
                        # Search for matching capture
                        matching_captures = list(captures_dir.glob(f"*{capture_pattern[:20]}*.html"))
                        
                        if matching_captures:
                            # Read the first matching capture
                            with open(matching_captures[0], 'r', encoding='utf-8') as f:
                                capture_content = f.read()
                            
                            # Extract the Contents list items
                            capture_soup = BeautifulSoup(capture_content, 'html.parser')
                            
                            # Find Contents section
                            contents_section = None
                            for h3 in capture_soup.find_all('h3'):
                                if 'Contents' in h3.get_text():
                                    parent = h3.parent
                                    contents_ul = parent.find('ul')
                                    if contents_ul:
                                        contents_section = contents_ul
                                        break
                            
                            if contents_section:
                                # Extract the button texts
                                items = []
                                for li in contents_section.find_all('li'):
                                    button = li.find('button')
                                    if button:
                                        text = button.get_text(strip=True)
                                        items.append(text)
                                
                                if items:
                                    # Replace the empty list items with real content
                                    ul.clear()
                                    for item_text in items:
                                        new_li = soup.new_tag('li')
                                        new_li.string = item_text
                                        ul.append(new_li)
                                    
                                    # Save the fixed file
                                    with open(html_file, 'w', encoding='utf-8') as f:
                                        f.write(str(soup))
                                    
                                    fixed_count += 1
                                    print(f"  ✓ Fixed with {len(items)} items")
                                else:
                                    print(f"  ✗ No items found in capture")
                            else:
                                # If no Contents section found, remove the empty one
                                contents_div.decompose()
                                
                                with open(html_file, 'w', encoding='utf-8') as f:
                                    f.write(str(soup))
                                
                                print(f"  ✓ Removed empty Contents section")
                                fixed_count += 1
                        else:
                            # No matching capture found - remove the empty Contents section
                            contents_div.decompose()
                            
                            with open(html_file, 'w', encoding='utf-8') as f:
                                f.write(str(soup))
                            
                            print(f"  ✓ Removed empty Contents section (no capture found)")
                            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} files")

if __name__ == "__main__":
    fix_redbook_contents()