#!/usr/bin/env python3
"""
Extract complete Maroonbook content using regex due to malformed XML.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def extract_all_content(xml_path):
    """Extract all content from Maroonbook XML using regex."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract bookmarks for structure
    bookmarks = extract_bookmarks(content)
    
    # Extract all headers and paragraphs with their IDs
    elements = []
    
    # Find H1, H2, H3, H4 headers with better ID extraction
    for level in [1, 2, 3, 4]:
        pattern = rf'<H{level}[^>]*>([^<]+)</H{level}>'
        matches = re.finditer(pattern, content)
        for match in matches:
            full_tag = match.group(0)
            text = match.group(1).strip()
            
            # Extract ID if present
            id_match = re.search(r'id="([^"]+)"', full_tag)
            elem_id = id_match.group(1) if id_match else ''
            
            elements.append({
                'type': f'H{level}',
                'id': elem_id,
                'text': text,
                'position': match.start()
            })
    
    # Find paragraphs
    p_pattern = r'<P[^>]*>([^<]+)</P>'
    p_matches = re.findall(p_pattern, content)
    
    # Find positions for ordering
    for p_text in p_matches:
        if p_text.strip() and len(p_text.strip()) > 5:
            pos = content.find(f'>{p_text}<')
            elements.append({
                'type': 'P',
                'id': '',
                'text': p_text.strip(),
                'position': pos
            })
    
    # Find list items
    li_pattern = r'<LI[^>]*>([^<]+)</LI>'
    li_matches = re.findall(li_pattern, content)
    for li_text in li_matches:
        if li_text.strip():
            pos = content.find(f'>{li_text}<')
            elements.append({
                'type': 'LI',
                'id': '',
                'text': li_text.strip(),
                'position': pos
            })
    
    # Sort by position to maintain document order
    elements.sort(key=lambda x: x['position'])
    
    return elements, bookmarks

def extract_bookmarks(content):
    """Extract bookmark structure."""
    bookmarks = {}
    
    # Find all bookmarks - handle both destination and structID
    bookmark_pattern = r'<bookmark title="([^"]+)"[^>]*>'
    matches = re.finditer(bookmark_pattern, content)
    
    for match in matches:
        title = match.group(1)
        # Look for destination structID right after
        full_match = match.group(0)
        dest_match = re.search(r'<destination structID="([^"]+)"', content[match.end():match.end()+100])
        if dest_match:
            struct_id = dest_match.group(1)
            bookmarks[struct_id] = title
    
    return bookmarks

def organize_into_rules(elements, bookmarks):
    """Organize elements into rules based on headers."""
    
    rules = {}
    current_rule = None
    current_section = None
    current_subsection = None
    
    # First pass - identify rule boundaries using bookmarks
    rule_starts = {}
    for elem_id, title in bookmarks.items():
        rule_match = re.match(r'^Rule (\d+):?\s*(.*)', title)
        if rule_match:
            rule_num = rule_match.group(1)
            rule_title = rule_match.group(2).strip()
            rule_starts[elem_id] = (rule_num, rule_title)
    
    for elem in elements:
        text = elem['text']
        elem_type = elem['type']
        elem_id = elem['id']
        
        # Skip empty or very short content
        if not text or len(text) < 2:
            continue
        
        # Check if this starts a new rule
        if elem_id in rule_starts:
            rule_num, rule_title = rule_starts[elem_id]
            current_rule = {
                'number': rule_num,
                'title': rule_title,
                'content': [],
                'sections': {}
            }
            rules[rule_num] = current_rule
            current_section = None
            current_subsection = None
            continue
        
        # Check if this is a rule header by text (fallback)
        if elem_type in ['H1', 'H2'] and not elem_id:
            rule_match = re.match(r'^Rule (\d+):?\s*(.*)', text)
            if rule_match:
                rule_num = rule_match.group(1)
                rule_title = rule_match.group(2).strip()
                
                current_rule = {
                    'number': rule_num,
                    'title': rule_title,
                    'content': [],
                    'sections': {}
                }
                rules[rule_num] = current_rule
                current_section = None
                current_subsection = None
                continue
        
        # Check if this is any bookmarked header (could be section)
        if elem_id in bookmarks:
            bookmark_title = bookmarks[elem_id]
            
            # Section (e.g., "1.1", "10.2")
            section_match = re.match(r'^(\d+\.\d+)\s*(.*)', bookmark_title)
            if section_match and current_rule:
                section_num = section_match.group(1)
                section_title = section_match.group(2).strip()
                
                current_section = {
                    'number': section_num,
                    'title': section_title,
                    'content': []
                }
                current_rule['sections'][section_num] = current_section
                current_subsection = None
                continue
            
            # Subsection (e.g., "(a)", "(b)")
            subsection_match = re.match(r'^\(([a-z])\)\s*(.*)', bookmark_title)
            if subsection_match:
                if current_section:
                    current_subsection = subsection_match.group(1)
                    # Add subsection marker
                    current_section['content'].append({
                        'type': 'subsection',
                        'text': bookmark_title
                    })
                elif current_rule:
                    current_rule['content'].append({
                        'type': 'subsection', 
                        'text': bookmark_title
                    })
                continue
        
        # Add content to appropriate location if we have a current rule
        if current_rule:
            content_item = {
                'type': elem_type,
                'text': text
            }
            
            if current_section:
                current_section['content'].append(content_item)
            else:
                current_rule['content'].append(content_item)
    
    return rules

def create_rule_html_with_content(rule_data):
    """Create HTML for a rule with all its content."""
    
    rule_num = rule_data['number']
    rule_title = rule_data['title']
    
    # Format main content
    main_content_html = format_content_items(rule_data.get('content', []))
    
    # Format sections
    sections_html = ""
    for section_num in sorted(rule_data.get('sections', {}).keys()):
        section = rule_data['sections'][section_num]
        section_content = format_content_items(section.get('content', []))
        
        sections_html += f"""
        <div class="section">
            <h3>{section_num} {section['title']}</h3>
            <div class="section-content">
                {section_content}
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
        .header {{
            background: #800020;
            color: white;
            padding: 15px 20px;
            margin: -20px -20px 30px -20px;
        }}
        h1 {{ 
            color: #800020; 
            border-bottom: 3px solid #800020; 
            padding-bottom: 10px;
        }}
        h2, h3 {{ 
            color: #800020; 
            margin-top: 1.5em; 
        }}
        .section {{
            margin: 30px 0;
            padding-left: 20px;
            border-left: 3px solid #800020;
        }}
        .section-content {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .subsection {{
            font-weight: bold;
            color: #800020;
            margin: 20px 0 10px 0;
        }}
        .example {{
            background: #F5F5F5;
            padding: 12px;
            border-left: 3px solid #999;
            margin: 15px 0;
            font-style: italic;
        }}
        ul {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        p {{
            margin: 10px 0;
        }}
        .citation {{
            font-style: italic;
            color: #555;
            margin-left: 20px;
        }}
        .navigation {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #DDD;
            display: flex;
            justify-content: space-between;
        }}
        .navigation a {{
            color: #800020;
            text-decoration: none;
        }}
        .navigation a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>The Maroonbook - University of Chicago Law Review Citation Manual</div>
        <div style="font-size: 0.9em; margin-top: 5px;">91st Edition</div>
    </div>
    
    <h1>Rule {rule_num}: {rule_title}</h1>
    
    <div class="main-content">
        {main_content_html}
    </div>
    
    {sections_html}
    
    <div class="navigation">
        <a href="index.html">← Back to Index</a>
        <div>
            {get_nav_links(rule_num)}
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def format_content_items(content_items):
    """Format a list of content items as HTML."""
    html_parts = []
    in_list = False
    
    for item in content_items:
        item_type = item.get('type', 'P')
        text = item.get('text', '').strip()
        
        if not text:
            continue
        
        # Clean text
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        
        # Handle different types
        if item_type == 'subsection':
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<div class="subsection">{text}</div>')
        
        elif item_type == 'LI':
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{text}</li>')
        
        elif item_type in ['H1', 'H2', 'H3', 'H4']:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            level = item_type[1]
            html_parts.append(f'<h{level}>{text}</h{level}>')
        
        else:  # Paragraph
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            
            # Check for special content
            if any(word in text for word in ['e.g.', 'See', 'But see', 'Cf.', 'Example:']):
                html_parts.append(f'<div class="example">{text}</div>')
            elif re.search(r'\d+\s+[A-Z].*\d{4}', text) or ' v. ' in text or ' v ' in text:
                html_parts.append(f'<div class="citation">{text}</div>')
            else:
                html_parts.append(f'<p>{text}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts)

def get_nav_links(current_rule):
    """Generate navigation links."""
    current = int(current_rule)
    links = []
    
    if current > 1:
        links.append(f'<a href="rule_{current-1:02d}.html">← Rule {current-1}</a>')
    
    if current < 21:
        links.append(f'<a href="rule_{current+1:02d}.html">Rule {current+1} →</a>')
    
    return ' | '.join(links)

def create_complete_index(rules):
    """Create index page with all rules."""
    
    rules_html = ""
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        sections_count = len(rule.get('sections', {}))
        content_count = len(rule.get('content', []))
        
        # Get preview text
        preview = ""
        for item in rule.get('content', [])[:3]:
            if item.get('type') == 'P' and len(item.get('text', '')) > 20:
                preview = item['text'][:150] + '...'
                break
        
        rules_html += f"""
        <div class="rule-card">
            <a href="rule_{int(rule_num):02d}.html">
                <div class="rule-header">
                    <span class="rule-number">Rule {rule_num}</span>
                    <span class="stats">{sections_count} sections • {content_count} items</span>
                </div>
                <div class="rule-title">{rule['title']}</div>
                <div class="rule-preview">{preview}</div>
            </a>
        </div>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>The Maroonbook - Complete Digital Edition</title>
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
        .header {{
            background: #800020;
            color: white;
            padding: 30px;
            margin: -20px -20px 30px -20px;
            text-align: center;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .subtitle {{
            margin-top: 10px;
            font-style: italic;
            opacity: 0.9;
        }}
        .stats-bar {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            display: flex;
            justify-content: space-around;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #800020;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .rules-grid {{
            margin-top: 30px;
        }}
        .rule-card {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #800020;
            transition: all 0.3s;
        }}
        .rule-card:hover {{
            transform: translateX(10px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .rule-card a {{
            text-decoration: none;
            color: inherit;
        }}
        .rule-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .rule-number {{
            font-weight: bold;
            color: #800020;
            font-size: 1.2em;
        }}
        .stats {{
            font-size: 0.85em;
            color: #999;
        }}
        .rule-title {{
            font-size: 1.1em;
            color: #333;
            margin-bottom: 8px;
        }}
        .rule-preview {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.4;
        }}
        .info {{
            background: #FFF3CD;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #FFC107;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📕 The Maroonbook</h1>
        <div class="subtitle">The University of Chicago Manual of Legal Citation • 91st Edition</div>
    </div>
    
    <div class="stats-bar">
        <div class="stat">
            <div class="stat-value">{len(rules)}</div>
            <div class="stat-label">Rules</div>
        </div>
        <div class="stat">
            <div class="stat-value">{sum(len(r.get('sections', {})) for r in rules.values())}</div>
            <div class="stat-label">Sections</div>
        </div>
        <div class="stat">
            <div class="stat-value">91st</div>
            <div class="stat-label">Edition</div>
        </div>
    </div>
    
    <div class="info">
        <strong>Complete Digital Edition:</strong> This digital version contains all rules, sections, 
        examples, and explanatory content from the University of Chicago Law Review's official 
        citation manual. Each rule includes full text, examples, and cross-references.
    </div>
    
    <div class="rules-grid">
        {rules_html}
    </div>
</body>
</html>"""
    
    return html_content

def main():
    """Main processing function."""
    
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_full")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Extracting Complete Maroonbook Content")
    print("=" * 60)
    
    # Extract all content
    print("Extracting elements from XML...")
    elements, bookmarks = extract_all_content(xml_path)
    print(f"  Found {len(elements)} elements")
    print(f"  Found {len(bookmarks)} bookmarked sections")
    
    # Organize into rules
    print("\nOrganizing content into rules...")
    rules = organize_into_rules(elements, bookmarks)
    print(f"  Organized into {len(rules)} rules")
    
    # Process each rule
    total_content = 0
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule_data = rules[rule_num]
        content_items = len(rule_data.get('content', []))
        sections = len(rule_data.get('sections', {}))
        
        print(f"\nRule {rule_num}: {rule_data['title']}")
        print(f"  Content items: {content_items}")
        print(f"  Sections: {sections}")
        
        total_content += content_items
        for section in rule_data.get('sections', {}).values():
            total_content += len(section.get('content', []))
        
        # Create HTML
        html_content = create_rule_html_with_content(rule_data)
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save JSON
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            # Convert content to serializable format
            json_data = {
                'number': rule_data['number'],
                'title': rule_data['title'],
                'content': [{'type': c['type'], 'text': c['text']} for c in rule_data.get('content', [])],
                'sections': {
                    k: {
                        'number': v['number'],
                        'title': v['title'],
                        'content': [{'type': c['type'], 'text': c['text']} for c in v.get('content', [])]
                    }
                    for k, v in rule_data.get('sections', {}).items()
                }
            }
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Create index
    print("\nCreating index...")
    index_html = create_complete_index(rules)
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Save metadata
    metadata = {
        "source": "The Maroonbook - 91st Edition",
        "extracted_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "total_content_items": total_content,
        "total_sections": sum(len(r.get('sections', {})) for r in rules.values())
    }
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Extraction complete!")
    print(f"Output: {output_dir}")
    print(f"Total content items: {total_content}")

if __name__ == "__main__":
    main()