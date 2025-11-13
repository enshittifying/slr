#!/usr/bin/env python3
"""
Update index.json and create index.html for relabeled_extracts
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
        
        return id_part, title
    return name, name

def update_indexes():
    """Update index.json and create index.html"""
    
    relabeled_dir = Path("/Users/ben/app/citation-editor/relabeled_extracts")
    
    # Load existing index.json
    index_json_path = relabeled_dir / "index.json"
    if index_json_path.exists():
        with open(index_json_path, 'r') as f:
            index_data = json.load(f)
    else:
        index_data = {
            "generated_at": datetime.now().isoformat(),
            "count": 0,
            "items": []
        }
    
    # Get all HTML files
    html_files = sorted([f.name for f in relabeled_dir.glob("*.html") if f.name != "index.html"])
    
    # Create a set of existing files for quick lookup
    existing_files = {item['relabeled'] for item in index_data['items']}
    
    # New files to add
    new_files = [
        "b5__quotations.html",
        "b12__statutes-rules-and-restatements.html",
        "b16__periodical-materials.html",
        "b18__the-internet.html",
        "bt2__jurisdiction-specific-citation-rules-and-style-guides.html",
        "t4__3-unofficial-treaty-sources.html"
    ]
    
    # Add new files to index if not already present
    for filename in new_files:
        if filename not in existing_files and filename in html_files:
            id_part, title = extract_title_from_filename(filename)
            
            # Special handling for t4.3
            if id_part == "t4__3":
                id_part = "t4.3"
                
            index_data['items'].append({
                "original": filename.replace('.html', '_clean.html'),
                "relabeled": filename,
                "id": id_part,
                "title": title
            })
            print(f"Added to index: {filename}")
    
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
            # Handle decimal numbers like "1.1", "10.2"
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
    index_data['generated_at'] = datetime.now().isoformat()
    
    # Save updated index.json
    with open(index_json_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    print(f"Updated index.json with {index_data['count']} items")
    
    # Create index.html
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bluebook Rules Index</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        .metadata {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 30px;
            font-style: italic;
        }
        
        .search-box {
            margin-bottom: 30px;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            transition: border-color 0.3s;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .rules-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .rule-card {
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .rule-card:hover {
            background: #fff;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .rule-id {
            background: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        
        .rule-title {
            color: #2c3e50;
            font-weight: 500;
            font-size: 1.1em;
        }
        
        .new-badge {
            background: #27ae60;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 5px;
            vertical-align: middle;
        }
        
        .section-header {
            grid-column: 1 / -1;
            background: #34495e;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        
        .stats {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
            padding: 10px;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #3498db;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Bluebook Citation Rules Index</h1>
        <div class="metadata">Last updated: """ + datetime.now().strftime("%B %d, %Y at %I:%M %p") + """</div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">""" + str(index_data['count']) + """</div>
                <div class="stat-label">Total Rules</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">6</div>
                <div class="stat-label">New Rules Added</div>
            </div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Search rules by ID or title..." onkeyup="filterRules()">
        </div>
        
        <div class="rules-grid" id="rulesGrid">
"""
    
    # Group rules by major section
    current_section = None
    for item in index_data['items']:
        # Determine section
        id_parts = item['id'].split('.')
        section = id_parts[0] if id_parts else item['id']
        
        # Add section header if new section
        if section != current_section:
            current_section = section
            section_name = get_section_name(section)
            html_content += f'            <div class="section-header">{section_name}</div>\n'
        
        # Check if this is a new file
        is_new = item['relabeled'] in new_files
        new_badge = '<span class="new-badge">NEW</span>' if is_new else ''
        
        # Add rule card
        html_content += f"""            <a href="{item['relabeled']}" class="rule-card">
                <span class="rule-id">{item['id']}</span>{new_badge}
                <div class="rule-title">{item['title']}</div>
            </a>
"""
    
    html_content += """        </div>
    </div>
    
    <script>
        function filterRules() {
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const cards = document.getElementsByClassName('rule-card');
            const headers = document.getElementsByClassName('section-header');
            
            // Hide all section headers first
            for (let header of headers) {
                header.style.display = 'none';
            }
            
            let lastVisibleSection = null;
            
            for (let card of cards) {
                const text = card.textContent.toLowerCase();
                if (text.includes(filter)) {
                    card.style.display = 'block';
                    
                    // Show the section header for visible cards
                    const prevHeader = card.previousElementSibling;
                    if (prevHeader && prevHeader.classList.contains('section-header')) {
                        prevHeader.style.display = 'block';
                    }
                } else {
                    card.style.display = 'none';
                }
            }
        }
    </script>
</body>
</html>"""
    
    # Save index.html
    index_html_path = relabeled_dir / "index.html"
    with open(index_html_path, 'w') as f:
        f.write(html_content)
    print(f"Created index.html with {index_data['count']} rules")
    
    return index_data['count']

def get_section_name(section_id):
    """Get human-readable section name"""
    section_names = {
        '1': 'Section 1: Structure and Use of Citations',
        '2': 'Section 2: Typefaces',
        '3': 'Section 3: Subdivisions',
        '4': 'Section 4: Short Citation Forms',
        '5': 'Section 5: Quotations',
        '6': 'Section 6: Abbreviations',
        '7': 'Section 7: Italicization',
        '8': 'Section 8: Capitalization',
        '9': 'Section 9: Titles',
        '10': 'Section 10: Cases',
        '11': 'Section 11: Constitutions',
        '12': 'Section 12: Statutes',
        '13': 'Section 13: Legislative Materials',
        '14': 'Section 14: Administrative Materials',
        '15': 'Section 15: Books',
        '16': 'Section 16: Periodicals',
        '17': 'Section 17: Unpublished Materials',
        '18': 'Section 18: Internet Sources',
        '19': 'Section 19: Services',
        '20': 'Section 20: Foreign Materials',
        '21': 'Section 21: International Materials',
        '22': 'Section 22: Tribal Nations',
        '23': 'Section 23: Other Authorities',
        'b': 'Bluepages',
        'bt': 'Bluepages Tables',
        't': 'Tables',
    }
    
    # Check for special prefixes
    if section_id.startswith('b'):
        if section_id.startswith('bt'):
            return section_names.get('bt', f'Bluepages Table {section_id[2:]}')
        return section_names.get('b', f'Bluepages Rule {section_id[1:]}')
    elif section_id.startswith('t'):
        return section_names.get('t', f'Table {section_id[1:]}')
    
    return section_names.get(section_id, f'Section {section_id}')

if __name__ == "__main__":
    count = update_indexes()
    print(f"\n✅ Successfully updated indexes with {count} total rules")