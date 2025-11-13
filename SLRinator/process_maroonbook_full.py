#!/usr/bin/env python3
"""
Process the complete Maroonbook XML file with all content, not just bookmarks.
Extracts full rule text, examples, and maintains all cross-references.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def clean_xml_content(content):
    """Clean and prepare XML content for parsing."""
    # Remove the bookmark tree and header
    bookmark_end = content.find('</bookmark-tree>')
    if bookmark_end != -1:
        content = content[bookmark_end + len('</bookmark-tree>'):]
    
    # Remove the initial metadata
    if '<?xpacket' in content:
        xpacket_end = content.rfind('?>')
        if xpacket_end != -1:
            content = content[xpacket_end + 2:]
    
    # Wrap in root element if needed
    if not content.strip().startswith('<'):
        return None
    
    # Add a root element to make it valid XML
    content = '<?xml version="1.0" encoding="UTF-8"?>\n<MaroonbookContent>\n' + content + '\n</MaroonbookContent>'
    
    # Fix common XML issues
    content = content.replace('&', '&amp;')
    content = content.replace('<P >', '<P>')
    content = content.replace('< ', '&lt; ')
    
    return content

def parse_maroonbook_content(xml_path):
    """Parse the complete Maroonbook content from XML."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        raw_content = f.read()
    
    # Extract bookmark structure first
    bookmarks = extract_bookmark_structure(raw_content)
    
    # Clean the content for parsing
    cleaned_content = clean_xml_content(raw_content)
    
    if not cleaned_content:
        return None, bookmarks
    
    # Try to parse
    try:
        # Use a more lenient parser
        import xml.etree.ElementTree as ET
        root = ET.fromstring(cleaned_content)
    except ET.ParseError as e:
        print(f"XML Parse error: {e}")
        # Try even more aggressive cleaning
        try:
            # Remove problematic sections
            cleaned_content = re.sub(r'<Figure[^>]*>.*?</Figure>', '', cleaned_content, flags=re.DOTALL)
            cleaned_content = re.sub(r'<ImageData[^>]*/>', '', cleaned_content)
            root = ET.fromstring(cleaned_content)
        except:
            print("Could not parse XML even after cleaning")
            return None, bookmarks
    
    return root, bookmarks

def extract_bookmark_structure(content):
    """Extract the bookmark navigation structure."""
    bookmarks = {}
    
    # Find bookmark section
    bookmark_start = content.find('<bookmark-tree>')
    bookmark_end = content.find('</bookmark-tree>')
    
    if bookmark_start == -1 or bookmark_end == -1:
        return bookmarks
    
    bookmark_xml = content[bookmark_start:bookmark_end + len('</bookmark-tree>')]
    
    # Parse bookmarks to get structure IDs
    try:
        # Clean up bookmark XML
        bookmark_xml = bookmark_xml.replace('&', '&amp;')
        root = ET.fromstring(bookmark_xml)
        
        def process_bookmark(elem, path=""):
            title = elem.get('title', '')
            struct_id = elem.get('structID', '')
            
            if struct_id:
                bookmarks[struct_id] = {
                    'title': title,
                    'path': path,
                    'destination': elem.findtext('.//destination', '')
                }
            
            # Process children
            for child in elem:
                if child.tag == 'bookmark':
                    child_path = f"{path}/{title}" if path else title
                    process_bookmark(child, child_path)
        
        for bookmark in root:
            if bookmark.tag == 'bookmark':
                process_bookmark(bookmark)
    
    except Exception as e:
        print(f"Error parsing bookmarks: {e}")
    
    return bookmarks

def extract_rules_content(root, bookmarks):
    """Extract actual rule content from the XML."""
    
    rules = {}
    current_rule = None
    current_section = None
    content_buffer = []
    
    # Process all elements
    for elem in root.iter():
        # Check for headers that match bookmark IDs
        elem_id = elem.get('id', '')
        
        if elem_id and elem_id.startswith('LinkTarget_'):
            # This is a linked section
            bookmark_info = bookmarks.get(elem_id, {})
            title = bookmark_info.get('title', elem.text or '')
            
            # Check if this is a rule
            rule_match = re.match(r'^Rule (\d+):?\s*(.*)', title)
            if rule_match:
                # Save previous rule if exists
                if current_rule and content_buffer:
                    if current_section:
                        current_rule['sections'][current_section]['content'] = '\n'.join(content_buffer)
                    else:
                        current_rule['content'] = '\n'.join(content_buffer)
                
                # Start new rule
                rule_num = rule_match.group(1)
                rule_title = rule_match.group(2).strip()
                
                current_rule = {
                    'number': rule_num,
                    'title': rule_title,
                    'full_title': title,
                    'id': elem_id,
                    'content': '',
                    'sections': {}
                }
                rules[rule_num] = current_rule
                current_section = None
                content_buffer = []
            
            # Check if this is a section
            elif current_rule:
                section_match = re.match(r'^(\d+\.\d+)\s*(.*)', title)
                if section_match:
                    # Save previous section
                    if current_section and content_buffer:
                        current_rule['sections'][current_section]['content'] = '\n'.join(content_buffer)
                    
                    # Start new section
                    section_num = section_match.group(1)
                    section_title = section_match.group(2).strip()
                    
                    current_section = section_num
                    current_rule['sections'][section_num] = {
                        'number': section_num,
                        'title': section_title,
                        'full_title': title,
                        'id': elem_id,
                        'content': ''
                    }
                    content_buffer = []
        
        # Collect content
        if elem.tag in ['P', 'H1', 'H2', 'H3', 'H4', 'LI', 'Caption']:
            text = elem.text or ''
            # Also get text from children
            for child in elem:
                if child.text:
                    text += ' ' + child.text
                if child.tail:
                    text += ' ' + child.tail
            
            text = text.strip()
            if text and current_rule:
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)
                text = html.unescape(text)
                
                # Add to buffer
                if elem.tag in ['H1', 'H2', 'H3', 'H4']:
                    content_buffer.append(f"\n### {text}\n")
                elif elem.tag == 'LI':
                    content_buffer.append(f"• {text}")
                else:
                    content_buffer.append(text)
    
    # Save last rule/section
    if current_rule and content_buffer:
        if current_section:
            current_rule['sections'][current_section]['content'] = '\n'.join(content_buffer)
        else:
            current_rule['content'] = '\n'.join(content_buffer)
    
    return rules

def create_comprehensive_rule_html(rule_data):
    """Create HTML with full content for a rule."""
    
    rule_num = rule_data['number']
    rule_title = rule_data['title']
    
    # Build content HTML
    content_html = ""
    
    # Add main rule content if exists
    if rule_data.get('content'):
        content_html += f"""
        <div class="rule-content">
            {format_content_as_html(rule_data['content'])}
        </div>"""
    
    # Add sections
    for section_num in sorted(rule_data.get('sections', {}).keys()):
        section = rule_data['sections'][section_num]
        content_html += f"""
        <div class="section" id="{section.get('id', '')}">
            <h3>{section['full_title']}</h3>
            <div class="section-content">
                {format_content_as_html(section.get('content', ''))}
            </div>
        </div>"""
    
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
            background: #800020;
            color: white;
            padding: 15px 20px;
            margin: -20px -20px 30px -20px;
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
        .rule-content, .section-content {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .section {{
            margin: 30px 0;
            padding-left: 20px;
            border-left: 3px solid #800020;
        }}
        .example {{
            background: #F5F5F5;
            padding: 15px;
            border-left: 3px solid #999;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        .note {{
            background: #FFF3CD;
            padding: 10px;
            border-left: 3px solid #FFC107;
            margin: 15px 0;
            font-style: italic;
        }}
        p {{
            margin: 10px 0;
        }}
        .subsection {{
            margin-left: 20px;
            margin-top: 15px;
        }}
        .citation-example {{
            font-style: italic;
            color: #555;
            margin: 10px 20px;
        }}
    </style>
</head>
<body>
    <div class="rule-header">
        The Maroonbook - University of Chicago Law Review Citation Manual (91st Edition)
    </div>
    <h1>Rule {rule_num}: {rule_title}</h1>
    
    {content_html}
    
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #DDD;">
        <a href="index.html" style="color: #800020;">← Back to Index</a>
        {get_navigation_links(rule_num)}
    </div>
</body>
</html>"""
    
    return html_content

def format_content_as_html(content):
    """Convert plain text content to formatted HTML."""
    if not content:
        return ""
    
    lines = content.split('\n')
    html_parts = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue
        
        # Handle headers
        if line.startswith('###'):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h4>{line[3:].strip()}</h4>')
        
        # Handle list items
        elif line.startswith('•'):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{line[1:].strip()}</li>')
        
        # Handle numbered items
        elif re.match(r'^\d+\.', line):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p><strong>{line}</strong></p>')
        
        # Handle subsections like (a), (b), etc
        elif re.match(r'^\([a-z]\)', line):
            html_parts.append(f'<div class="subsection"><strong>{line}</strong></div>')
        
        # Regular paragraphs
        else:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            
            # Check for examples
            if 'e.g.,' in line or 'See' in line or line.startswith('Example:'):
                html_parts.append(f'<div class="example">{line}</div>')
            # Check for citations
            elif re.search(r'\d+\s+[A-Z]', line) or 'v.' in line:
                html_parts.append(f'<div class="citation-example">{line}</div>')
            else:
                html_parts.append(f'<p>{line}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts)

def get_navigation_links(current_rule_num):
    """Generate previous/next navigation links."""
    current = int(current_rule_num)
    nav_html = ' | '
    
    if current > 1:
        nav_html += f'<a href="rule_{current-1:02d}.html" style="color: #800020;">← Previous Rule</a>'
    
    if current < 21:  # Assuming 21 rules total
        if current > 1:
            nav_html += ' | '
        nav_html += f'<a href="rule_{current+1:02d}.html" style="color: #800020;">Next Rule →</a>'
    
    return nav_html

def process_maroonbook_complete():
    """Main function to process the complete Maroonbook."""
    
    # Setup paths
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Processing the Complete Maroonbook")
    print("=" * 60)
    
    # Parse the XML with content
    print(f"Reading and parsing XML from: {xml_path}")
    root, bookmarks = parse_maroonbook_content(xml_path)
    
    if root is None:
        print("Failed to parse XML content")
        return
    
    print(f"Found {len(bookmarks)} bookmarked sections")
    
    # Extract rules with content
    print("Extracting rules with full content...")
    rules = extract_rules_content(root, bookmarks)
    
    print(f"Extracted {len(rules)} rules with content")
    
    # Process each rule
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule_data = rules[rule_num]
        sections_count = len(rule_data.get('sections', {}))
        content_length = len(rule_data.get('content', ''))
        
        print(f"  Processing Rule {rule_num}: {rule_data['title']}")
        print(f"    - {sections_count} sections")
        print(f"    - {content_length} characters of content")
        
        # Create comprehensive HTML
        html_content = create_comprehensive_rule_html(rule_data)
        
        # Save HTML file
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save JSON with full content
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rule_data, f, indent=2, ensure_ascii=False)
    
    # Create comprehensive index
    print("\nCreating comprehensive index...")
    index_html = create_comprehensive_index(rules)
    
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Save complete metadata
    metadata = {
        "source": "The Maroonbook - 91st Edition",
        "publisher": "University of Chicago Law Review",
        "processed_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "total_content_chars": sum(len(r.get('content', '')) for r in rules.values()),
        "rules_summary": {
            rule_num: {
                "title": rule_data['title'],
                "sections": len(rule_data.get('sections', {})),
                "content_length": len(rule_data.get('content', ''))
            }
            for rule_num, rule_data in rules.items()
        }
    }
    
    metadata_path = output_dir / "maroonbook_complete_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Complete processing finished!")
    print(f"Output directory: {output_dir}")
    print(f"Total rules processed: {len(rules)}")
    print(f"Total content extracted: {metadata['total_content_chars']} characters")

def create_comprehensive_index(rules):
    """Create a comprehensive index with content previews."""
    
    total_rules = len(rules)
    total_sections = sum(len(r.get('sections', {})) for r in rules.values())
    
    # Build rules cards
    rules_html = ""
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        num_sections = len(rule.get('sections', {}))
        content_preview = (rule.get('content', '')[:200] + '...') if rule.get('content') else 'No preview available'
        
        rules_html += f"""
        <div class="rule-card">
            <a href="rule_{int(rule_num):02d}.html" class="rule-link">
                <div class="rule-header-info">
                    <span class="rule-number">Rule {rule_num}</span>
                    <span class="section-count">{num_sections} sections</span>
                </div>
                <div class="rule-title">{rule['title']}</div>
                <div class="rule-preview">{content_preview}</div>
            </a>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>The Maroonbook - Complete Citation Manual</title>
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
        .rules-container {{
            margin-top: 30px;
        }}
        .rule-card {{
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s;
            border-left: 4px solid #800020;
        }}
        .rule-card:hover {{
            transform: translateX(10px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .rule-link {{
            text-decoration: none;
            color: #333;
            display: block;
        }}
        .rule-header-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .rule-number {{
            font-weight: bold;
            color: #800020;
            font-size: 1.3em;
        }}
        .section-count {{
            font-size: 0.9em;
            color: #999;
            background: #F0F0F0;
            padding: 3px 10px;
            border-radius: 15px;
        }}
        .rule-title {{
            color: #555;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        .rule-preview {{
            font-size: 0.9em;
            color: #777;
            line-height: 1.4;
            font-style: italic;
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
    <h1>📕 The Maroonbook - Complete Edition</h1>
    <div class="subtitle">University of Chicago Law Review Citation Manual - 91st Edition</div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-value">{total_rules}</div>
            <div>Rules</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{total_sections}</div>
            <div>Sections</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">91st</div>
            <div>Edition</div>
        </div>
    </div>
    
    <div class="info-box">
        <strong>About the Maroonbook:</strong> The Maroonbook is the citation manual used by the 
        University of Chicago Law Review. This complete digital edition includes all rules, 
        sections, examples, and explanatory content extracted from the official 91st edition.
    </div>
    
    <h2 style="color: #800020; margin-top: 30px;">Complete Citation Rules</h2>
    <div class="rules-container">
        {rules_html}
    </div>
</body>
</html>"""
    
    return html_content

if __name__ == "__main__":
    process_maroonbook_complete()