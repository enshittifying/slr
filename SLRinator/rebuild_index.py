#!/usr/bin/env python3
"""
Rebuild index.json from scratch based on actual files in relabeled_extracts
"""

import json
from pathlib import Path
from datetime import datetime
import re

def extract_title_from_filename(filename):
    """Extract human-readable title from filename"""
    # Remove .html extension
    name = filename.replace('.html', '')
    
    # Split by double underscore
    parts = name.split('__')
    if len(parts) == 2:
        id_part = parts[0]
        title_part = parts[1]
        
        # Convert hyphens to spaces and capitalize
        title = title_part.replace('-', ' ').title()
        
        # Special handling for t4.3
        if id_part == "t4" and title.startswith("3 "):
            id_part = "t4.3"
            title = title[2:]  # Remove the "3 " prefix
            
        return id_part, title
    return name, name

def rebuild_index():
    """Rebuild index.json from actual files"""
    
    relabeled_dir = Path("/Users/ben/app/citation-editor/relabeled_extracts")
    
    # Get all HTML files (excluding index.html)
    html_files = sorted([
        f.name for f in relabeled_dir.glob("*.html") 
        if f.name != "index.html"
    ])
    
    print(f"Found {len(html_files)} HTML files in {relabeled_dir}")
    
    # Build index data
    index_data = {
        "generated_at": datetime.now().isoformat(),
        "count": 0,
        "items": []
    }
    
    for filename in html_files:
        id_part, title = extract_title_from_filename(filename)
        
        index_data['items'].append({
            "original": filename.replace('.html', '_clean.html'),
            "relabeled": filename,
            "id": id_part,
            "title": title
        })
    
    # Sort items by ID (custom sort for mixed alphanumeric)
    def sort_key(item):
        id_val = str(item['id'])
        
        # Handle special prefixes
        prefix_order = {'': 0, 'b': 100, 'bt': 200, 't': 300}
        
        # Extract prefix and number
        if id_val.startswith('bt'):
            prefix = 'bt'
            rest = id_val[2:]
        elif id_val.startswith('b'):
            prefix = 'b'
            rest = id_val[1:]
        elif id_val.startswith('t'):
            prefix = 't'
            rest = id_val[1:]
        else:
            prefix = ''
            rest = id_val
        
        # Parse the numeric part
        try:
            # Handle decimal numbers like "1.1", "10.2", "4.3"
            if '.' in rest:
                parts = rest.split('.')
                main = float(parts[0]) if parts[0] else 0
                sub = float(parts[1]) if len(parts) > 1 and parts[1] else 0
                numeric_val = main + sub / 1000  # Ensure subsections sort after main
            else:
                numeric_val = float(rest) if rest else 0
        except (ValueError, IndexError):
            numeric_val = 999  # Put non-numeric at end
        
        return (prefix_order.get(prefix, 500), numeric_val, rest)
    
    index_data['items'].sort(key=sort_key)
    index_data['count'] = len(index_data['items'])
    
    # Save index.json
    index_json_path = relabeled_dir / "index.json"
    with open(index_json_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n✅ Rebuilt index.json with {index_data['count']} items")
    
    # Show some stats
    prefixes = {}
    for item in index_data['items']:
        id_val = item['id']
        if id_val.startswith('bt'):
            prefix = 'bt'
        elif id_val.startswith('b'):
            prefix = 'b'
        elif id_val.startswith('t'):
            prefix = 't'
        else:
            prefix = 'main'
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    print("\nBreakdown by section:")
    for prefix, count in sorted(prefixes.items()):
        print(f"  {prefix}: {count} items")
    
    # Check for bt2 specifically
    bt2_items = [item for item in index_data['items'] if item['id'] == 'bt2']
    if bt2_items:
        print(f"\n✓ bt2 found in index: {bt2_items[0]['title']}")
    else:
        print("\n✗ bt2 NOT found in index")
    
    return index_data

if __name__ == "__main__":
    rebuild_index()