#!/usr/bin/env python3
"""
Fix Redbook index.json - extract section numbers and clean titles
"""

import json
import re
from pathlib import Path

def fix_redbook_index():
    """Fix the Redbook index.json file"""
    
    index_path = Path("/Users/ben/app/citation-editor/redbook_processed/index.json")
    
    # Load the current index
    with open(index_path, 'r') as f:
        index_data = json.load(f)
    
    print(f"Fixing {len(index_data['sections'])} sections...")
    
    for section in index_data['sections']:
        # Get the section text (might be in 'section' or 'title')
        section_text = section.get('section', '') or section.get('title', '')
        
        # Try to extract section number pattern like "1.1:" or "10.15:" or "22.11:"
        # Also handle single numbers like "2:" or "10:"
        section_match = re.match(r'^(\d+(?:\.\d+)?):?\s*(.*)$', section_text)
        
        if section_match:
            # Extract section number and clean title
            section_num = section_match.group(1)
            clean_title = section_match.group(2).strip()
            
            # Update the section data
            section['section_number'] = section_num
            
            # If title was null, use the cleaned title
            if section['title'] is None:
                section['title'] = clean_title
            
            # Update section field with cleaned title
            section['section'] = clean_title
            
            print(f"  Fixed: {section_num} -> {clean_title}")
        else:
            # No section number found, keep as is
            if section['title'] is None and section['section']:
                section['title'] = section['section']
            print(f"  Kept as is: {section.get('title', section.get('section', 'Unknown'))}")
    
    # Save the fixed index
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n✅ Fixed index.json saved to {index_path}")
    
    # Also update the HTML files if needed
    update_html_files(index_data['sections'])
    
    return index_data

def update_html_files(sections):
    """Update HTML files with corrected section information"""
    
    html_dir = Path("/Users/ben/app/citation-editor/redbook_processed")
    
    for section in sections:
        html_path = html_dir / section['file']
        
        if html_path.exists() and section.get('section_number'):
            # Read the HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Update the section info if it contains the old format
            old_pattern = f"<strong>Redbook Section:</strong> {section.get('section_number', '')}:"
            new_pattern = f"<strong>Redbook Section {section['section_number']}:</strong>"
            
            if old_pattern in html_content:
                html_content = html_content.replace(old_pattern, new_pattern)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"  Updated HTML: {section['file']}")

if __name__ == "__main__":
    fix_redbook_index()