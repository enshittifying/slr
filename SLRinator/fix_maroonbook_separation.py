#!/usr/bin/env python3
"""
Fix the Maroonbook extraction to properly separate rules from appendices.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def extract_content_with_proper_separation(xml_path):
    """Extract content with proper rule/appendix separation."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Get bookmark structure first
    bookmark_end = content.find('</bookmark-tree>')
    bookmark_section = content[:bookmark_end + len('</bookmark-tree>')]
    bookmarks = extract_bookmark_structure(bookmark_section)
    
    # Get actual document content
    doc_content = content[bookmark_end + len('</bookmark-tree>'):]
    
    # Find the position where appendices start
    appendix_start_pos = find_appendix_start_position(doc_content, bookmarks)
    
    # Split content into rules section and appendices section
    rules_content = doc_content[:appendix_start_pos] if appendix_start_pos != -1 else doc_content
    appendices_content = doc_content[appendix_start_pos:] if appendix_start_pos != -1 else ""
    
    print(f"Rules content: {len(rules_content)} chars")
    print(f"Appendices content: {len(appendices_content)} chars")
    
    # Extract elements from each section separately
    rules_elements = extract_elements_from_content(rules_content, bookmarks, 0)
    appendices_elements = extract_elements_from_content(appendices_content, bookmarks, appendix_start_pos) if appendices_content else []
    
    return rules_elements, appendices_elements, bookmarks

def find_appendix_start_position(doc_content, bookmarks):
    """Find where appendices start in the document."""
    
    # Look for the first H1 with "Appendix" in its ID
    appendix_ids = [id for id, title in bookmarks.items() if 'Appendix 1:' in title and 'General Rules' in title]
    
    if appendix_ids:
        # Find this ID in the document content
        for app_id in appendix_ids:
            pos = doc_content.find(f'id="{app_id}"')
            if pos != -1:
                print(f"Found appendix start at position {pos} (ID: {app_id})")
                return pos
    
    # Fallback: look for first occurrence of "Appendix 1:" as H1 text
    h1_appendix = re.search(r'<H1[^>]*>Appendix 1:', doc_content)
    if h1_appendix:
        print(f"Found appendix start by H1 text at position {h1_appendix.start()}")
        return h1_appendix.start()
    
    print("No appendix start found")
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
    """Extract elements from a specific content section."""
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
                    row_data.append(cell_text)
            
            # TD cells
            td_pattern = r'<TD>.*?<P[^>]*>(.*?)</P>.*?</TD>'
            for td_match in re.finditer(td_pattern, row_content, re.DOTALL):
                cell_text = td_match.group(1).strip()
                cell_text = process_inline_content(cell_text)
                if cell_text:
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
    text = re.sub(r'<Link[^>]*>([^<]+)</Link>', r'\1', text)
    text = re.sub(r'<Reference[^>]*>([^<]+)</Reference>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def organize_rules_only(elements, bookmarks):
    """Organize only rule content (not appendices)."""
    
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
        
        # Stop if we hit appendix content
        if 'Appendix' in text and elem_type in ['H1', 'H2']:
            print(f"Stopping at appendix: {text}")
            break
        
        bookmark_title = bookmarks.get(elem_id, '')
        
        # Check for rule
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

# Import HTML functions
from extract_maroonbook_complete import (
    create_complete_rule_html,
    create_appendix_html,
    create_complete_index_with_appendices
)

def main():
    """Main function to fix the separation."""
    
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_fixed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("FIXING Maroonbook Rule/Appendix Separation")
    print("=" * 60)
    
    # Extract with proper separation
    rules_elements, appendices_elements, bookmarks = extract_content_with_proper_separation(xml_path)
    print(f"Rules elements: {len(rules_elements)}")
    print(f"Appendices elements: {len(appendices_elements)}")
    
    # Organize separately
    rules = organize_rules_only(rules_elements, bookmarks)
    appendices = organize_appendices_only(appendices_elements, bookmarks)
    
    print(f"\nOrganized: {len(rules)} rules, {len(appendices)} appendices")
    
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
        print(f"Rule {rule_num}: {rule_content} items")
        
        # Create files
        html_content = create_complete_rule_html(rule)
        html_path = output_dir / f"rule_{int(rule_num):02d}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        json_path = output_dir / f"rule_{int(rule_num):02d}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rule, f, indent=2, ensure_ascii=False)
    
    # Process appendices
    for app_num in sorted(appendices.keys()):
        app = appendices[app_num]
        print(f"Appendix {app_num}: {len(app['content'])} items")
        
        html_content = create_appendix_html(app)
        html_path = output_dir / f"appendix_{app_num.replace('.', '_')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    # Create index
    index_html = create_complete_index_with_appendices(rules, appendices)
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"\n✅ Fixed extraction complete!")
    print(f"Output: {output_dir}")
    print(f"Total rule content: {total_content}")

if __name__ == "__main__":
    main()