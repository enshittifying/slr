#!/usr/bin/env python3
"""
Process the Maroonbook XML file into organized HTML format similar to other citation guides.
The Maroonbook is the University of Chicago Law Review's citation manual.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_maroonbook_xml(xml_path):
    """Parse the Maroonbook XML bookmark structure."""
    
    # Read the XML file
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the bookmark tree section
    bookmark_start = content.find('<bookmark-tree>')
    bookmark_end = content.find('</bookmark-tree>') + len('</bookmark-tree>')
    
    if bookmark_start == -1 or bookmark_end == -1:
        print("Could not find bookmark tree in XML")
        return None
    
    bookmark_xml = content[bookmark_start:bookmark_end]
    
    # Parse the bookmark tree
    try:
        root = ET.fromstring(bookmark_xml)
    except ET.ParseError as e:
        print(f"Error parsing bookmark XML: {e}")
        # Try to fix common issues
        bookmark_xml = bookmark_xml.replace('&', '&amp;')
        try:
            root = ET.fromstring(bookmark_xml)
        except:
            return None
    
    return root

def extract_rules_from_bookmarks(root):
    """Extract rules and their subsections from bookmark tree."""
    
    rules = {}
    
    def process_bookmark(elem, parent_rule=None, parent_section=None, level=0):
        """Recursively process bookmark elements."""
        
        title = elem.get('title', '')
        struct_id = elem.get('structID', '')
        
        # Check if this is a main rule
        rule_match = re.match(r'^Rule (\d+):?\s*(.*)', title)
        if rule_match:
            rule_num = rule_match.group(1)
            rule_title = rule_match.group(2).strip()
            
            rules[rule_num] = {
                'number': rule_num,
                'title': rule_title,
                'full_title': title,
                'struct_id': struct_id,
                'sections': [],
                'subsections': defaultdict(list)
            }
            
            # Process child bookmarks
            for child in elem:
                if child.tag == 'bookmark':
                    process_bookmark(child, parent_rule=rule_num, level=level+1)
        
        # Check if this is a section (e.g., "1.1", "10.2")
        elif parent_rule:
            section_match = re.match(r'^(\d+\.\d+)\s*(.*)', title)
            if section_match:
                section_num = section_match.group(1)
                section_title = section_match.group(2).strip()
                
                rules[parent_rule]['sections'].append({
                    'number': section_num,
                    'title': section_title,
                    'full_title': title,
                    'struct_id': struct_id,
                    'subsections': []
                })
                
                # Process subsections
                for child in elem:
                    if child.tag == 'bookmark':
                        process_bookmark(child, parent_rule=parent_rule, 
                                       parent_section=section_num, level=level+1)
            
            # Check if this is a subsection (e.g., "(a)", "(1)")
            elif parent_section or level > 1:
                subsection_info = {
                    'title': title,
                    'struct_id': struct_id,
                    'level': level
                }
                
                if parent_section:
                    # Add to the last section added
                    if rules[parent_rule]['sections']:
                        rules[parent_rule]['sections'][-1]['subsections'].append(subsection_info)
                else:
                    # Direct subsection of rule
                    rules[parent_rule]['subsections']['direct'].append(subsection_info)
                
                # Process any children
                for child in elem:
                    if child.tag == 'bookmark':
                        process_bookmark(child, parent_rule=parent_rule, 
                                       parent_section=parent_section, level=level+1)
    
    # Process all top-level bookmarks
    for bookmark in root:
        if bookmark.tag == 'bookmark':
            process_bookmark(bookmark)
    
    return rules

def create_rule_html(rule_data):
    """Create HTML for a single rule."""
    
    rule_num = rule_data['number']
    rule_title = rule_data['title']
    
    # Build sections HTML
    sections_html = ""
    for section in rule_data.get('sections', []):
        sections_html += f"""
        <div class="section">
            <h3 id="{section['struct_id']}">{section['full_title']}</h3>"""
        
        if section.get('subsections'):
            sections_html += '<ul class="subsections">'
            for subsec in section['subsections']:
                sections_html += f"""
                <li id="{subsec['struct_id']}">{subsec['title']}</li>"""
            sections_html += '</ul>'
        
        sections_html += '</div>'
    
    # Add direct subsections if any
    if 'direct' in rule_data.get('subsections', {}):
        sections_html += '<ul class="direct-subsections">'
        for subsec in rule_data['subsections']['direct']:
            sections_html += f"""
            <li id="{subsec['struct_id']}">{subsec['title']}</li>"""
        sections_html += '</ul>'
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Maroonbook Rule {rule_num}: {rule_title}</title>
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
        .rule-header {{
            background: #800020;  /* Maroon color */
            color: white;
            padding: 10px 15px;
            margin: -20px -20px 20px -20px;
            font-size: 0.9em;
        }}
        h1 {{ 
            color: #800020; 
            border-bottom: 3px solid #800020; 
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2, h3 {{ 
            color: #800020; 
            margin-top: 1.5em; 
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-left: 3px solid #800020;
        }}
        .subsections, .direct-subsections {{
            margin-top: 10px;
            padding-left: 20px;
        }}
        .subsections li, .direct-subsections li {{
            margin: 8px 0;
            color: #555;
        }}
        .note {{
            background: #FFF3CD;
            padding: 10px;
            border-left: 3px solid #FFC107;
            margin: 15px 0;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="rule-header">
        The Maroonbook - University of Chicago Law Review Citation Manual (91st Edition)
    </div>
    <h1>Rule {rule_num}: {rule_title}</h1>
    
    <div class="note">
        Note: This is extracted from the Maroonbook bookmark structure. 
        For complete rule text and examples, please refer to the full Maroonbook manual.
    </div>
    
    {sections_html}
</body>
</html>"""
    
    return html_content

def create_maroonbook_index(rules):
    """Create master index for all Maroonbook rules."""
    
    total_rules = len(rules)
    
    # Build rules list HTML
    rules_html = ""
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        num_sections = len(rule.get('sections', []))
        
        rules_html += f"""
        <div class="rule-card">
            <a href="rule_{int(rule_num):02d}.html" class="rule-link">
                <span class="rule-number">Rule {rule_num}</span>
                <span class="rule-title">{rule['title']}</span>
                <span class="section-count">{num_sections} sections</span>
            </a>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>The Maroonbook - Citation Manual Index</title>
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
            color: #800020;
            border-bottom: 4px solid #800020;
            padding-bottom: 15px;
            text-align: center;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-top: -10px;
            margin-bottom: 30px;
            font-style: italic;
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
            color: #800020;
        }}
        .rules-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .rule-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        .rule-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .rule-link {{
            text-decoration: none;
            color: #333;
            display: flex;
            flex-direction: column;
        }}
        .rule-number {{
            font-weight: bold;
            color: #800020;
            font-size: 1.2em;
            margin-bottom: 5px;
        }}
        .rule-title {{
            color: #555;
            margin-bottom: 5px;
        }}
        .section-count {{
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }}
        .info-box {{
            background: #FFF3CD;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #FFC107;
        }}
    </style>
</head>
<body>
    <h1>📕 The Maroonbook</h1>
    <div class="subtitle">University of Chicago Law Review Citation Manual - 91st Edition</div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{total_rules}</div>
            <div>Rules</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">91st</div>
            <div>Edition</div>
        </div>
    </div>
    
    <div class="info-box">
        <strong>About the Maroonbook:</strong> The Maroonbook is the citation manual used by the 
        University of Chicago Law Review. It provides comprehensive guidance on legal citation 
        format for law review articles, following the distinctive style preferences of the 
        University of Chicago.
    </div>
    
    <h2 style="color: #800020; margin-top: 30px;">Citation Rules</h2>
    <div class="rules-grid">
        {rules_html}
    </div>
    
    <div class="info-box" style="margin-top: 40px;">
        <strong>Note:</strong> This digital version is extracted from the Maroonbook XML structure. 
        For complete rule text, examples, and detailed explanations, please refer to the full 
        Maroonbook manual.
    </div>
</body>
</html>"""
    
    return html_content

def process_maroonbook():
    """Main function to process the Maroonbook XML."""
    
    # Setup paths
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Processing the Maroonbook")
    print("=" * 60)
    
    # Parse the XML
    print(f"Reading XML from: {xml_path}")
    root = parse_maroonbook_xml(xml_path)
    
    if root is None:
        print("Failed to parse XML")
        return
    
    # Extract rules
    print("Extracting rules from bookmark structure...")
    rules = extract_rules_from_bookmarks(root)
    
    print(f"Found {len(rules)} rules")
    
    # Process each rule
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule_data = rules[rule_num]
        print(f"  Processing Rule {rule_num}: {rule_data['title']}")
        
        # Create HTML
        html_content = create_rule_html(rule_data)
        
        # Save HTML file
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save JSON metadata
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rule_data, f, indent=2)
    
    # Create master index
    print("\nCreating master index...")
    index_html = create_maroonbook_index(rules)
    
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Save complete metadata
    metadata = {
        "source": "The Maroonbook - 91st Edition",
        "publisher": "University of Chicago Law Review",
        "processed_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "rules": list(rules.keys())
    }
    
    metadata_path = output_dir / "maroonbook_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Processing complete!")
    print(f"Output directory: {output_dir}")
    print(f"Total rules processed: {len(rules)}")
    
    # Print rule summary
    print("\nRule Summary:")
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        num_sections = len(rule.get('sections', []))
        print(f"  Rule {rule_num}: {rule['title']} ({num_sections} sections)")

if __name__ == "__main__":
    process_maroonbook()