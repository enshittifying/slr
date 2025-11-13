#!/usr/bin/env python3
"""
Extract Maroonbook with URL replacement - replace chicagomanualofstyle.com links with relative links.
Keep images unchanged, only fix actual content links.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def fix_internal_links(text):
    """Replace chicagomanualofstyle.com links with relative links, but keep images/media unchanged."""
    if not text:
        return text
    
    # Don't modify any URLs that are images/media files
    # This includes /dam paths, image extensions, etc.
    
    # Pattern for href attributes (content links only, not media)
    href_pattern = r'href="https?://(?:www\.)?chicagomanualofstyle\.org(/(?!dam/)[^"]*)"'
    text = re.sub(href_pattern, r'href="thisurl\1"', text)
    
    # Pattern for bare URLs in text content (not media paths)
    bare_url_pattern = r'https?://(?:www\.)?chicagomanualofstyle\.org(/(?!dam/)(?![^"\s]*\.(jpg|jpeg|png|gif|pdf|css|js))[^"\s]*)'
    text = re.sub(bare_url_pattern, r'thisurl\1', text)
    
    # Pattern for domain references without protocol (not media paths)
    domain_pattern = r'(?<![\w./])chicagomanualofstyle\.org(/(?!dam/)(?![^"\s]*\.(jpg|jpeg|png|gif|pdf|css|js))[^"\s]*)'
    text = re.sub(domain_pattern, r'thisurl\1', text)
    
    return text

def extract_all_content_with_url_fix(xml_path):
    """Extract content with URL fixing applied."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Separate bookmark tree from actual content
    bookmark_end = content.find('</bookmark-tree>')
    if bookmark_end == -1:
        print("Error: Could not find end of bookmark tree")
        return [], {}, []
    
    bookmark_section = content[:bookmark_end + len('</bookmark-tree>')]
    bookmarks = extract_bookmark_structure(bookmark_section)
    
    doc_content = content[bookmark_end + len('</bookmark-tree>'):]
    
    # Find appendix start
    appendix_start_pos = find_appendix_start_position(doc_content, bookmarks)
    
    rules_content = doc_content[:appendix_start_pos] if appendix_start_pos != -1 else doc_content
    appendices_content = doc_content[appendix_start_pos:] if appendix_start_pos != -1 else ""
    
    # Extract elements
    rules_elements = extract_elements_from_content(rules_content, bookmarks, 0)
    appendices_elements = extract_elements_from_content(appendices_content, bookmarks, appendix_start_pos) if appendices_content else []
    
    return rules_elements, appendices_elements, bookmarks

def find_appendix_start_position(doc_content, bookmarks):
    """Find where appendices start."""
    appendix_ids = [id for id, title in bookmarks.items() if 'Appendix 1:' in title and 'General Rules' in title]
    
    if appendix_ids:
        for app_id in appendix_ids:
            pos = doc_content.find(f'id="{app_id}"')
            if pos != -1:
                return pos
    
    h1_appendix = re.search(r'<H1[^>]*>Appendix 1:', doc_content)
    if h1_appendix:
        return h1_appendix.start()
    
    return -1

def extract_bookmark_structure(bookmark_content):
    """Extract bookmark structure."""
    bookmarks = {}
    pattern = r'<bookmark title="([^"]+)"[^>]*>\s*<destination structID="([^"]+)"'
    for match in re.finditer(pattern, bookmark_content):
        title = match.group(1)
        struct_id = match.group(2)
        bookmarks[struct_id] = title
    return bookmarks

def extract_elements_from_content(content, bookmarks, offset):
    """Extract elements from content with URL fixing."""
    elements = []
    
    # Extract headers
    for level in [1, 2, 3, 4]:
        pattern = rf'<H{level}(?:[^>]*?)>([^<]+)</H{level}>'
        for match in re.finditer(pattern, content):
            full_tag = match.group(0)
            text = match.group(1).strip()
            
            id_match = re.search(r'id="([^"]+)"', full_tag)
            elem_id = id_match.group(1) if id_match else ''
            
            if text and len(text) > 1:
                # Apply URL fixing to header text
                text = fix_internal_links(text)
                elements.append({
                    'type': f'H{level}',
                    'id': elem_id,
                    'text': text,
                    'position': offset + match.start()
                })
    
    # Extract paragraphs
    p_pattern = r'<P(?:[^>]*?)>((?:[^<]|<(?!/?P>))*)</P>'
    for match in re.finditer(p_pattern, content):
        raw_text = match.group(1)
        text = process_inline_content(raw_text)
        
        if text and len(text.strip()) > 2:
            # Apply URL fixing to paragraph text
            text = fix_internal_links(text)
            elements.append({
                'type': 'P',
                'id': '',
                'text': text.strip(),
                'position': offset + match.start()
            })
    
    # Extract list items
    l_pattern = r'<L>(.*?)</L>'
    for l_match in re.finditer(l_pattern, content, re.DOTALL):
        list_content = l_match.group(1)
        li_pattern = r'<LI>.*?<LBody[^>]*>(.*?)</LBody>.*?</LI>'
        for li_match in re.finditer(li_pattern, list_content, re.DOTALL):
            text = li_match.group(1).strip()
            text = process_inline_content(text)
            
            if text:
                # Apply URL fixing to list item text
                text = fix_internal_links(text)
                elements.append({
                    'type': 'LI',
                    'id': '',
                    'text': text,
                    'position': offset + l_match.start() + li_match.start()
                })
    
    # Extract table content
    table_pattern = r'<Table>(.*?)</Table>'
    for table_match in re.finditer(table_pattern, content, re.DOTALL):
        table_content = table_match.group(1)
        table_position = offset + table_match.start()
        
        tr_pattern = r'<TR>(.*?)</TR>'
        for tr_match in re.finditer(tr_pattern, table_content, re.DOTALL):
            row_content = tr_match.group(1)
            row_data = []
            
            # TH cells
            th_pattern = r'<TH>.*?<P[^>]*>(.*?)</P>.*?</TH>'
            for th_match in re.finditer(th_pattern, row_content, re.DOTALL):
                cell_text = th_match.group(1).strip()
                cell_text = process_inline_content(cell_text)
                if cell_text:
                    # Apply URL fixing to table cell text
                    cell_text = fix_internal_links(cell_text)
                    row_data.append(cell_text)
            
            # TD cells
            td_pattern = r'<TD>.*?<P[^>]*>(.*?)</P>.*?</TD>'
            for td_match in re.finditer(td_pattern, row_content, re.DOTALL):
                cell_text = td_match.group(1).strip()
                cell_text = process_inline_content(cell_text)
                if cell_text:
                    # Apply URL fixing to table cell text
                    cell_text = fix_internal_links(cell_text)
                    row_data.append(cell_text)
            
            if row_data:
                elements.append({
                    'type': 'TABLE_ROW',
                    'id': '',
                    'text': ' | '.join(row_data),
                    'position': table_position + tr_match.start()
                })
    
    elements.sort(key=lambda x: x['position'])
    return elements

def process_inline_content(text):
    """Process inline tags within text."""
    # Process inline tags but preserve any URLs for later fixing
    text = re.sub(r'<Link[^>]*>([^<]+)</Link>', r'\1', text)
    text = re.sub(r'<Reference[^>]*>([^<]+)</Reference>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def organize_rules_only(elements, bookmarks):
    """Organize only rule content."""
    rules = {}
    current_rule = None
    current_section = None
    current_subsection = None
    
    for elem in elements:
        elem_type = elem['type']
        elem_id = elem['id']
        text = elem['text']
        
        # Skip TOC and metadata
        if 'Table of Contents' in text or 'Volume 91' in text or 'Edited by' in text:
            continue
        
        # Stop at appendix content
        if 'Appendix' in text and elem_type in ['H1', 'H2']:
            break
        
        bookmark_title = bookmarks.get(elem_id, '')
        
        # Determine element type
        is_rule = False
        is_section = False
        is_subsection = False
        
        if bookmark_title:
            if bookmark_title.startswith('Rule ') and ':' in bookmark_title:
                is_rule = True
            elif re.match(r'^\d+\.\d+', bookmark_title):
                is_section = True
            elif re.match(r'^\([a-z]\)', bookmark_title):
                is_subsection = True
        
        if not (is_rule or is_section or is_subsection):
            if text.startswith('Rule ') and ':' in text:
                is_rule = True
            elif re.match(r'^\d+\.\d+\s+', text):
                is_section = True
            elif re.match(r'^\([a-z]\)\s+', text):
                is_subsection = True
        
        if is_rule:
            rule_text = bookmark_title if bookmark_title else text
            rule_match = re.match(r'^Rule (\d+):?\s*(.*)', rule_text)
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
        
        elif is_section and current_rule:
            section_text = bookmark_title if bookmark_title else text
            section_match = re.match(r'^(\d+\.\d+)\s*(.*)', section_text)
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
        
        elif is_subsection:
            subsection_text = bookmark_title if bookmark_title else text
            subsection_match = re.match(r'^\(([a-z])\)\s*(.*)', subsection_text)
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
        
        else:
            # Content
            if not current_rule:
                continue
            
            if re.match(r'^\(\d+\)\s+', text):
                content_item = {'type': 'numbered_item', 'text': text}
            elif elem_type == 'TABLE_ROW':
                content_item = {'type': 'table_row', 'text': text}
            else:
                content_item = {'type': elem_type, 'text': text}
            
            if current_subsection:
                current_subsection['content'].append(content_item)
            elif current_section:
                current_section['content'].append(content_item)
            elif current_rule:
                current_rule['content'].append(content_item)
    
    return rules

def organize_appendices_only(elements, bookmarks):
    """Organize only appendix content."""
    appendices = {}
    current_appendix = None
    
    for elem in elements:
        text = elem['text']
        elem_id = elem['id']
        
        # Check for appendix start
        if elem_id in bookmarks and 'Appendix' in bookmarks[elem_id]:
            app_match = re.match(r'Appendix ([0-9.]+):?\s*(.*)', bookmarks[elem_id])
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
        
        # Check text for appendix
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
        if current_appendix:
            if elem['type'] == 'TABLE_ROW':
                content_item = {'type': 'table_row', 'text': text}
            else:
                content_item = {'type': elem['type'], 'text': text}
            current_appendix['content'].append(content_item)
    
    return appendices

def create_rule_html_with_url_fix(rule_data):
    """Create HTML for rule with URL fixes applied."""
    
    rule_num = rule_data['number']
    rule_title = rule_data['title']
    
    # Format main content
    main_content_html = ""
    if rule_data.get('content'):
        main_content_html = "<div class='rule-main-content'>"
        main_content_html += format_content_items_with_url_fix(rule_data['content'])
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
                    {format_content_items_with_url_fix(subsection['content'])}
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
                {format_content_items_with_url_fix(section['content'])}
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
                        {format_content_items_with_url_fix(subsection['content'])}
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
        a {{
            color: #800020;
            text-decoration: underline;
        }}
        a:hover {{
            color: #600015;
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

def format_content_items_with_url_fix(content_items):
    """Format content items with URL fixes applied."""
    if not content_items:
        return ""
    
    html_parts = []
    in_list = False
    
    for item in content_items:
        item_type = item.get('type', 'P')
        text = item.get('text', '').strip()
        
        if not text:
            continue
        
        # Apply URL fixing to the text content
        text = fix_internal_links(text)
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
        
        elif item_type == 'TABLE_ROW' or item_type == 'table_row':
            html_parts.append(f'<div class="table-row" style="margin: 8px 0; padding: 5px; background: #F9F9F9; border-left: 2px solid #DDD;">{text}</div>')
        
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
    
    if current < 21:
        links.append(f'<a href="rule_{current+1:02d}.html">Next Rule →</a>')
    
    return ' '.join(links)

def create_appendix_html_with_url_fix(app_data):
    """Create appendix HTML with URL fixes."""
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
        a {{
            color: #800020;
            text-decoration: underline;
        }}
        .table-row {{
            margin: 8px 0;
            padding: 5px;
            background: #F9F9F9;
            border-left: 2px solid #DDD;
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
        {format_content_items_with_url_fix(app_data.get('content', []))}
    </div>
    
    <div class="navigation">
        <a href="index.html">← Back to Index</a>
    </div>
</body>
</html>"""
    
    return html_content

def main():
    """Main function with URL fixing."""
    
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_with_url_fix")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Extracting Maroonbook with URL fixes")
    print("=" * 60)
    
    # Extract with URL fixing
    rules_elements, appendices_elements, bookmarks = extract_all_content_with_url_fix(xml_path)
    print(f"Rules elements: {len(rules_elements)}")
    print(f"Appendices elements: {len(appendices_elements)}")
    
    # Organize
    rules = organize_rules_only(rules_elements, bookmarks)
    appendices = organize_appendices_only(appendices_elements, bookmarks)
    
    print(f"\nOrganized: {len(rules)} rules, {len(appendices)} appendices")
    
    # Test URL fixing on some content
    print("\n🔗 URL Fixing Examples:")
    sample_texts = [
        "See https://www.chicagomanualofstyle.org/tools_citationguide.html for more info",
        "Visit chicagomanualofstyle.org/questions for help",
        '<img src="https://www.chicagomanualofstyle.org/dam/cmos18/figures/images/chi-cmos18-fig01008.jpg" alt="test">',
        'Link to <a href="https://chicagomanualofstyle.org/section">section</a> here'
    ]
    
    for text in sample_texts:
        fixed = fix_internal_links(text)
        print(f"  Original: {text}")
        print(f"  Fixed:    {fixed}")
        print()
    
    # Process rules
    total_content = 0
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        
        # Count content
        rule_content = len(rule.get('content', []))
        for section in rule.get('sections', {}).values():
            rule_content += len(section.get('content', []))
            for subsection in section.get('subsections', {}).values():
                rule_content += len(subsection.get('content', []))
        for subsection in rule.get('direct_subsections', {}).values():
            rule_content += len(subsection.get('content', []))
        
        total_content += rule_content
        
        # Create HTML with URL fixes
        html_content = create_rule_html_with_url_fix(rule)
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Save JSON
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rule, f, indent=2, ensure_ascii=False)
    
    # Process appendices
    for app_num in sorted(appendices.keys()):
        app = appendices[app_num]
        
        html_content = create_appendix_html_with_url_fix(app)
        html_path = output_dir / f"appendix_{app_num.replace('.', '_')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    # Create index (reuse from previous)
    from fix_maroonbook_separation import create_complete_index_with_appendices
    index_html = create_complete_index_with_appendices(rules, appendices)
    
    # Apply URL fixes to index too
    index_html = fix_internal_links(index_html)
    
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"\n✅ Extraction with URL fixes complete!")
    print(f"Output: {output_dir}")
    print(f"Total content: {total_content}")
    print("\n🔗 URL fixes applied:")
    print("  - chicagomanualofstyle.org links → thisurl/ (relative)")
    print("  - Image URLs preserved unchanged")
    print("  - Ready for slug mapping implementation")

if __name__ == "__main__":
    main()