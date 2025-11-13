#!/usr/bin/env python3
"""
Complete extraction of Maroonbook content including all subsections, lists, and examples.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def extract_all_content_complete(xml_path):
    """Extract complete content from Maroonbook XML."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract bookmarks for structure
    bookmarks = extract_bookmark_structure(content)
    
    # Find where actual content starts (after bookmark tree)
    content_start = content.find('</bookmark-tree>')
    if content_start == -1:
        print("Could not find end of bookmark tree")
        return [], {}
    
    # Get only the actual document content
    doc_content = content[content_start:]
    
    # Extract all elements with positions
    elements = []
    
    # Extract ALL headers (H1-H4) with their IDs
    for level in [1, 2, 3, 4]:
        pattern = rf'<H{level}(?:[^>]*?)>([^<]+)</H{level}>'
        for match in re.finditer(pattern, doc_content):
            full_tag = match.group(0)
            text = match.group(1).strip()
            
            # Extract ID if present
            id_match = re.search(r'id="([^"]+)"', full_tag)
            elem_id = id_match.group(1) if id_match else ''
            
            if text:  # Only add non-empty headers
                elements.append({
                    'type': f'H{level}',
                    'id': elem_id,
                    'text': text,
                    'position': match.start()
                })
    
    # Extract ALL paragraphs
    p_pattern = r'<P(?:[^>]*?)>([^<]+(?:<[^>]+>[^<]*</[^>]+>[^<]*)*)</P>'
    for match in re.finditer(p_pattern, doc_content):
        text = match.group(1).strip()
        # Clean up inline tags
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        
        if text and len(text) > 2:  # Skip empty or very short paragraphs
            elements.append({
                'type': 'P',
                'id': '',
                'text': text,
                'position': match.start()
            })
    
    # Extract list items
    li_pattern = r'<LI(?:[^>]*?)>([^<]+(?:<[^>]+>[^<]*</[^>]+>[^<]*)*)</LI>'
    for match in re.finditer(li_pattern, doc_content):
        text = match.group(1).strip()
        # Clean up inline tags
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        
        if text:
            elements.append({
                'type': 'LI',
                'id': '',
                'text': text,
                'position': match.start()
            })
    
    # Extract table cells (often contain important content)
    td_pattern = r'<TD(?:[^>]*?)>([^<]+(?:<[^>]+>[^<]*</[^>]+>[^<]*)*)</TD>'
    for match in re.finditer(td_pattern, doc_content):
        text = match.group(1).strip()
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        
        if text and len(text) > 5:
            elements.append({
                'type': 'TD',
                'id': '',
                'text': text,
                'position': match.start()
            })
    
    # Sort by position to maintain document order
    elements.sort(key=lambda x: x['position'])
    
    return elements, bookmarks

def extract_bookmark_structure(content):
    """Extract complete bookmark structure with hierarchy."""
    bookmarks = {}
    bookmark_hierarchy = {}
    
    # Find bookmark section
    bookmark_start = content.find('<bookmark-tree>')
    bookmark_end = content.find('</bookmark-tree>')
    
    if bookmark_start == -1 or bookmark_end == -1:
        return bookmarks
    
    bookmark_content = content[bookmark_start:bookmark_end]
    
    # Extract all bookmarks with their destinations
    pattern = r'<bookmark title="([^"]+)"[^>]*>\s*<destination structID="([^"]+)"'
    for match in re.finditer(pattern, bookmark_content):
        title = match.group(1)
        struct_id = match.group(2)
        bookmarks[struct_id] = title
        
        # Track hierarchy
        if 'Rule ' in title and ':' in title:
            rule_num = re.search(r'Rule (\d+)', title)
            if rule_num:
                bookmark_hierarchy[struct_id] = ('rule', rule_num.group(1))
        elif re.match(r'^\d+\.\d+', title):
            section_num = re.match(r'^(\d+\.\d+)', title).group(1)
            bookmark_hierarchy[struct_id] = ('section', section_num)
        elif re.match(r'^\([a-z]\)', title):
            subsection = re.match(r'^\(([a-z])\)', title).group(1)
            bookmark_hierarchy[struct_id] = ('subsection', subsection)
    
    return bookmarks

def organize_content_complete(elements, bookmarks):
    """Organize all content into complete rule structure."""
    
    rules = {}
    current_rule = None
    current_section = None
    current_subsection = None
    
    # Create reverse lookup for bookmarks
    bookmark_positions = {}
    for elem in elements:
        if elem['id'] and elem['id'] in bookmarks:
            bookmark_positions[elem['position']] = elem['id']
    
    for i, elem in enumerate(elements):
        elem_type = elem['type']
        elem_id = elem['id']
        text = elem['text']
        
        # Skip table of contents entries
        if 'Table of Contents' in text or re.match(r'^Rule \d+:.*\.{5,}', text):
            continue
        
        # Check if this is a rule start
        if elem_id in bookmarks:
            title = bookmarks[elem_id]
            
            # Main rule
            if title.startswith('Rule ') and ':' in title:
                rule_match = re.match(r'^Rule (\d+):?\s*(.*)', title)
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
            
            # Section (e.g., "10.2 Case Names")
            elif re.match(r'^\d+\.\d+', title) and current_rule:
                section_match = re.match(r'^(\d+\.\d+)\s*(.*)', title)
                if section_match:
                    section_num = section_match.group(1)
                    section_title = section_match.group(2).strip()
                    
                    current_section = {
                        'number': section_num,
                        'title': section_title,
                        'content': [],
                        'subsections': {}
                    }
                    current_rule['sections'][section_num] = current_section
                    current_subsection = None
                    continue
            
            # Subsection (e.g., "(a) Actions and parties cited")
            elif re.match(r'^\([a-z]\)', title):
                subsection_match = re.match(r'^\(([a-z])\)\s*(.*)', title)
                if subsection_match:
                    subsection_letter = subsection_match.group(1)
                    subsection_title = subsection_match.group(2).strip()
                    
                    if current_section:
                        current_subsection = {
                            'letter': subsection_letter,
                            'title': subsection_title,
                            'content': []
                        }
                        current_section['subsections'][subsection_letter] = current_subsection
                    elif current_rule:
                        # Direct subsection of rule
                        current_subsection = {
                            'letter': subsection_letter,
                            'title': subsection_title,
                            'content': []
                        }
                        if 'direct_subsections' not in current_rule:
                            current_rule['direct_subsections'] = {}
                        current_rule['direct_subsections'][subsection_letter] = current_subsection
                    continue
        
        # Also check text patterns for headers without IDs
        if elem_type in ['H1', 'H2', 'H3'] and not elem_id:
            # Check for rule pattern in text
            if text.startswith('Rule ') and ':' in text:
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
            
            # Check for section pattern
            elif re.match(r'^\d+\.\d+\s+', text) and current_rule:
                section_match = re.match(r'^(\d+\.\d+)\s+(.*)', text)
                if section_match:
                    section_num = section_match.group(1)
                    section_title = section_match.group(2).strip()
                    
                    current_section = {
                        'number': section_num,
                        'title': section_title,
                        'content': [],
                        'subsections': {}
                    }
                    current_rule['sections'][section_num] = current_section
                    current_subsection = None
                    continue
            
            # Check for subsection pattern
            elif re.match(r'^\([a-z]\)\s+', text):
                subsection_match = re.match(r'^\(([a-z])\)\s+(.*)', text)
                if subsection_match:
                    subsection_letter = subsection_match.group(1)
                    subsection_title = subsection_match.group(2).strip()
                    
                    if current_section:
                        current_subsection = {
                            'letter': subsection_letter,
                            'title': subsection_title,
                            'content': []
                        }
                        current_section['subsections'][subsection_letter] = current_subsection
                    elif current_rule:
                        current_subsection = {
                            'letter': subsection_letter,
                            'title': subsection_title,
                            'content': []
                        }
                        if 'direct_subsections' not in current_rule:
                            current_rule['direct_subsections'] = {}
                        current_rule['direct_subsections'][subsection_letter] = current_subsection
                    continue
        
        # Check for numbered list items like "(1)", "(2)" etc.
        if re.match(r'^\(\d+\)\s+', text):
            # This is a numbered sub-item
            content_item = {
                'type': 'numbered_item',
                'text': text
            }
        else:
            content_item = {
                'type': elem_type,
                'text': text
            }
        
        # Add content to appropriate location
        if current_subsection:
            current_subsection['content'].append(content_item)
        elif current_section:
            current_section['content'].append(content_item)
        elif current_rule:
            current_rule['content'].append(content_item)
    
    return rules

def create_complete_rule_html(rule_data):
    """Create comprehensive HTML for a rule with all content."""
    
    rule_num = rule_data['number']
    rule_title = rule_data['title']
    
    # Format main rule content
    main_content_html = ""
    if rule_data.get('content'):
        main_content_html = "<div class='rule-main-content'>"
        main_content_html += format_content_items(rule_data['content'])
        main_content_html += "</div>"
    
    # Format direct subsections
    if rule_data.get('direct_subsections'):
        main_content_html += "<div class='direct-subsections'>"
        for letter in sorted(rule_data['direct_subsections'].keys()):
            subsection = rule_data['direct_subsections'][letter]
            main_content_html += f"""
            <div class='subsection'>
                <h4>({letter}) {subsection['title']}</h4>
                <div class='subsection-content'>
                    {format_content_items(subsection['content'])}
                </div>
            </div>"""
        main_content_html += "</div>"
    
    # Format sections
    sections_html = ""
    for section_num in sorted(rule_data.get('sections', {}).keys()):
        section = rule_data['sections'][section_num]
        
        sections_html += f"""
        <div class="section" id="section_{section_num.replace('.', '_')}">
            <h3>{section_num} {section['title']}</h3>
            <div class="section-content">
                {format_content_items(section['content'])}
            </div>"""
        
        # Add subsections
        if section.get('subsections'):
            sections_html += "<div class='subsections'>"
            for letter in sorted(section['subsections'].keys()):
                subsection = section['subsections'][letter]
                sections_html += f"""
                <div class='subsection'>
                    <h4>({letter}) {subsection['title']}</h4>
                    <div class='subsection-content'>
                        {format_content_items(subsection['content'])}
                    </div>
                </div>"""
            sections_html += "</div>"
        
        sections_html += "</div>"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Maroonbook Rule {rule_num}: {rule_title}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.8;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #FAFAFA;
        }}
        .header {{
            background: #800020;
            color: white;
            padding: 20px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 10px 10px;
        }}
        h1 {{ 
            color: #800020; 
            border-bottom: 3px solid #800020; 
            padding-bottom: 15px;
            margin-top: 0;
        }}
        h2, h3 {{ 
            color: #800020; 
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        h4 {{
            color: #800020;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            font-size: 1.1em;
        }}
        .section {{
            margin: 40px 0;
            padding: 25px;
            background: white;
            border-left: 4px solid #800020;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .section-content {{
            margin-top: 15px;
        }}
        .subsection {{
            margin: 25px 0;
            padding-left: 20px;
            border-left: 2px solid #DDD;
        }}
        .subsection-content {{
            margin-top: 10px;
        }}
        .numbered_item {{
            margin: 10px 0 10px 20px;
            padding-left: 10px;
        }}
        .example {{
            background: #F5F5F5;
            padding: 15px;
            border-left: 3px solid #999;
            margin: 20px 0;
            font-style: italic;
            border-radius: 3px;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        p {{
            margin: 12px 0;
        }}
        .citation {{
            font-style: italic;
            color: #555;
            margin: 15px 20px;
            padding: 10px;
            background: #F9F9F9;
            border-left: 2px solid #CCC;
        }}
        .navigation {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #DDD;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .navigation a {{
            color: #800020;
            text-decoration: none;
            padding: 10px 20px;
            background: white;
            border: 1px solid #800020;
            border-radius: 5px;
            transition: all 0.3s;
        }}
        .navigation a:hover {{
            background: #800020;
            color: white;
        }}
        .rule-main-content {{
            margin: 20px 0;
        }}
        .direct-subsections {{
            margin: 30px 0;
        }}
        code {{
            background: #F0F0F0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 1.5em; font-weight: bold;">The Maroonbook</div>
        <div style="margin-top: 5px;">University of Chicago Law Review Citation Manual • 91st Edition</div>
    </div>
    
    <h1>Rule {rule_num}: {rule_title}</h1>
    
    {main_content_html}
    
    {sections_html}
    
    <div class="navigation">
        <a href="index.html">← Back to Index</a>
        <div>
            {get_navigation_links(rule_num)}
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def format_content_items(content_items):
    """Format content items as HTML with proper styling."""
    if not content_items:
        return ""
    
    html_parts = []
    in_list = False
    
    for item in content_items:
        item_type = item.get('type', 'P')
        text = item.get('text', '').strip()
        
        if not text:
            continue
        
        # Clean and format text
        text = html.unescape(text)
        
        # Close list if needed
        if in_list and item_type not in ['LI', 'numbered_item']:
            html_parts.append('</ul>')
            in_list = False
        
        # Handle different content types
        if item_type == 'numbered_item':
            html_parts.append(f'<div class="numbered_item">{text}</div>')
        
        elif item_type == 'LI':
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            html_parts.append(f'<li>{text}</li>')
        
        elif item_type in ['H1', 'H2', 'H3', 'H4']:
            level = item_type[1]
            html_parts.append(f'<h{level}>{text}</h{level}>')
        
        elif item_type == 'TD':
            # Table data often contains examples
            html_parts.append(f'<div class="example">{text}</div>')
        
        else:  # Paragraph
            # Check for special content patterns
            if any(signal in text for signal in ['e.g.', 'See', 'But see', 'Cf.', 'Compare', 'Example:']):
                html_parts.append(f'<div class="example">{text}</div>')
            elif re.search(r'\d+\s+[A-Z].*\d{4}', text) or ' v. ' in text or ' v ' in text:
                html_parts.append(f'<div class="citation">{text}</div>')
            elif text.startswith('Not:') or text.startswith('Correct:') or text.startswith('Incorrect:'):
                html_parts.append(f'<div class="example"><strong>{text[:text.index(':')+1]}</strong>{text[text.index(':')+1:]}</div>')
            else:
                html_parts.append(f'<p>{text}</p>')
    
    if in_list:
        html_parts.append('</ul>')
    
    return '\n'.join(html_parts)

def get_navigation_links(current_rule):
    """Generate navigation links."""
    current = int(current_rule)
    links = []
    
    if current > 1:
        links.append(f'<a href="rule_{current-1:02d}.html">← Previous Rule</a>')
    
    if current < 21:  # Assuming 21 rules
        links.append(f'<a href="rule_{current+1:02d}.html">Next Rule →</a>')
    
    return ' '.join(links)

def extract_appendices(elements, bookmarks):
    """Extract appendix content from elements."""
    appendices = {}
    current_appendix = None
    
    for elem in elements:
        text = elem['text']
        elem_id = elem['id']
        
        # Check bookmarks for appendix
        if elem_id in bookmarks:
            title = bookmarks[elem_id]
            if 'Appendix' in title:
                # Extract appendix number and title
                app_match = re.match(r'Appendix ([0-9.]+):?\s*(.*)', title)
                if app_match:
                    app_num = app_match.group(1)
                    app_title = app_match.group(2).strip()
                    
                    current_appendix = {
                        'number': app_num,
                        'title': app_title,
                        'content': []
                    }
                    appendices[app_num] = current_appendix
                    continue
        
        # Also check text for appendix headers
        if re.match(r'^Appendix [0-9.]+', text):
            app_match = re.match(r'^Appendix ([0-9.]+):?\s*(.*)', text)
            if app_match:
                app_num = app_match.group(1)
                app_title = app_match.group(2).strip()
                
                current_appendix = {
                    'number': app_num,
                    'title': app_title,
                    'content': []
                }
                appendices[app_num] = current_appendix
                continue
        
        # Add content to current appendix
        if current_appendix and text and len(text) > 2:
            # Skip if this is start of a rule (appendices end when rules start)
            if text.startswith('Rule ') and ':' in text:
                current_appendix = None
                continue
            
            current_appendix['content'].append({
                'type': elem['type'],
                'text': text
            })
    
    return appendices

def create_appendix_html(app_data):
    """Create HTML for an appendix."""
    app_num = app_data['number']
    app_title = app_data['title']
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Maroonbook Appendix {app_num}: {app_title}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.8;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #FAFAFA;
        }}
        .header {{
            background: #800020;
            color: white;
            padding: 20px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 10px 10px;
        }}
        h1 {{ 
            color: #800020; 
            border-bottom: 3px solid #800020; 
            padding-bottom: 15px;
        }}
        .content {{
            background: white;
            padding: 25px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .navigation {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #DDD;
        }}
        .navigation a {{
            color: #800020;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div style="font-size: 1.5em; font-weight: bold;">The Maroonbook - Appendices</div>
        <div style="margin-top: 5px;">University of Chicago Law Review Citation Manual</div>
    </div>
    
    <h1>Appendix {app_num}: {app_title}</h1>
    
    <div class="content">
        {format_content_items(app_data.get('content', []))}
    </div>
    
    <div class="navigation">
        <a href="index.html">← Back to Index</a>
    </div>
</body>
</html>"""
    
    return html_content

def create_complete_index_with_appendices(rules, appendices):
    """Create index including appendices."""
    
    rules_html = ""
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        sections_count = len(rule.get('sections', {}))
        
        rules_html += f"""
        <div class="rule-card">
            <a href="rule_{int(rule_num):02d}.html">
                <div class="rule-header">
                    <span class="rule-number">Rule {rule_num}</span>
                    <span class="stats">{sections_count} sections</span>
                </div>
                <div class="rule-title">{rule['title']}</div>
            </a>
        </div>"""
    
    # Add appendices section
    appendices_html = ""
    if appendices:
        appendices_html = "<h2 style='color: #800020; margin-top: 40px;'>Appendices</h2><div class='appendices-grid'>"
        for app_num in sorted(appendices.keys()):
            app = appendices[app_num]
            appendices_html += f"""
            <div class="appendix-card">
                <a href="appendix_{app_num.replace('.', '_')}.html">
                    <span class="appendix-number">Appendix {app_num}</span>
                    <span class="appendix-title">{app['title']}</span>
                </a>
            </div>"""
        appendices_html += "</div>"
    
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
        .rules-grid {{
            margin-top: 30px;
        }}
        .rule-card, .appendix-card {{
            background: white;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #800020;
            transition: all 0.3s;
        }}
        .rule-card:hover, .appendix-card:hover {{
            transform: translateX(10px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .rule-card a, .appendix-card a {{
            text-decoration: none;
            color: inherit;
        }}
        .rule-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        .rule-number, .appendix-number {{
            font-weight: bold;
            color: #800020;
            font-size: 1.2em;
        }}
        .appendix-title {{
            color: #555;
            margin-left: 10px;
        }}
        .appendices-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
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
            <div>Rules</div>
        </div>
        <div class="stat">
            <div class="stat-value">{sum(len(r.get('sections', {})) for r in rules.values())}</div>
            <div>Sections</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(appendices)}</div>
            <div>Appendices</div>
        </div>
    </div>
    
    <h2 style="color: #800020;">Citation Rules</h2>
    <div class="rules-grid">
        {rules_html}
    </div>
    
    {appendices_html}
</body>
</html>"""
    
    return html_content

def main():
    """Main processing function."""
    
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_complete")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Extracting Complete Maroonbook Content")
    print("=" * 60)
    
    # Extract all content
    print("Extracting all elements from XML...")
    elements, bookmarks = extract_all_content_complete(xml_path)
    print(f"  Found {len(elements)} total elements")
    print(f"  Found {len(bookmarks)} bookmarked sections")
    
    # Organize into complete structure
    print("\nOrganizing content into complete rule structure...")
    rules = organize_content_complete(elements, bookmarks)
    print(f"  Organized into {len(rules)} rules")
    
    # Calculate statistics
    total_content = 0
    total_sections = 0
    total_subsections = 0
    
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        
        # Count content
        rule_content = len(rule.get('content', []))
        sections = rule.get('sections', {})
        
        for section in sections.values():
            total_sections += 1
            rule_content += len(section.get('content', []))
            
            for subsection in section.get('subsections', {}).values():
                total_subsections += 1
                rule_content += len(subsection.get('content', []))
        
        # Count direct subsections
        for subsection in rule.get('direct_subsections', {}).values():
            total_subsections += 1
            rule_content += len(subsection.get('content', []))
        
        total_content += rule_content
        
        print(f"\nRule {rule_num}: {rule['title']}")
        print(f"  Total content items: {rule_content}")
        print(f"  Sections: {len(sections)}")
        print(f"  Subsections: {len(rule.get('direct_subsections', {})) + sum(len(s.get('subsections', {})) for s in sections.values())}")
        
        # Create HTML
        html_content = create_complete_rule_html(rule)
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save complete JSON
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rule, f, indent=2, ensure_ascii=False)
    
    # Extract and process appendices
    print("\nExtracting appendices...")
    appendices = extract_appendices(elements, bookmarks)
    
    for app_num in sorted(appendices.keys()):
        app_data = appendices[app_num]
        print(f"  Appendix {app_num}: {app_data['title']} ({len(app_data.get('content', []))} items)")
        
        # Create appendix HTML
        html_content = create_appendix_html(app_data)
        html_path = output_dir / f"appendix_{app_num.replace('.', '_')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    # Create comprehensive index with appendices
    print("\nCreating comprehensive index...")
    index_html = create_complete_index_with_appendices(rules, appendices)
    
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Save complete metadata
    metadata = {
        "source": "The Maroonbook - 91st Edition",
        "publisher": "University of Chicago Law Review",
        "extracted_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "total_sections": total_sections,
        "total_subsections": total_subsections,
        "total_content_items": total_content,
        "extraction_method": "Complete XML parsing with subsection preservation"
    }
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ Complete extraction finished!")
    print(f"Output: {output_dir}")
    print(f"Total content items: {total_content}")
    print(f"Total sections: {total_sections}")
    print(f"Total subsections: {total_subsections}")

if __name__ == "__main__":
    main()