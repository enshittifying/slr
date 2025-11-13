#!/usr/bin/env python3
"""
Final complete extraction of Maroonbook content handling all edge cases.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import html

def extract_all_content_final(xml_path):
    """Extract complete content from Maroonbook XML, handling all edge cases."""
    
    with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # CRITICAL: Separate bookmark tree from actual content
    bookmark_end = content.find('</bookmark-tree>')
    if bookmark_end == -1:
        print("Error: Could not find end of bookmark tree")
        return [], {}
    
    # Extract bookmarks for structure (from beginning)
    bookmark_section = content[:bookmark_end + len('</bookmark-tree>')]
    bookmarks = extract_bookmark_structure(bookmark_section)
    
    # Get ONLY the actual document content (after bookmarks)
    doc_content = content[bookmark_end + len('</bookmark-tree>'):]
    
    # Extract all elements with positions
    elements = []
    
    # Extract ALL headers (H1-H4) with their IDs from ACTUAL CONTENT
    for level in [1, 2, 3, 4]:
        pattern = rf'<H{level}(?:[^>]*?)>([^<]+)</H{level}>'
        for match in re.finditer(pattern, doc_content):
            full_tag = match.group(0)
            text = match.group(1).strip()
            
            # Extract ID if present
            id_match = re.search(r'id="([^"]+)"', full_tag)
            elem_id = id_match.group(1) if id_match else ''
            
            if text and len(text) > 1:  # Only add non-empty headers
                elements.append({
                    'type': f'H{level}',
                    'id': elem_id,
                    'text': text,
                    'position': match.start()
                })
    
    # Extract paragraphs including those with inline content
    # More comprehensive pattern to capture inline tags
    p_pattern = r'<P(?:[^>]*?)>((?:[^<]|<(?!/?P>))*)</P>'
    for match in re.finditer(p_pattern, doc_content):
        raw_text = match.group(1)
        
        # Process inline tags (Link, Reference, etc)
        text = process_inline_content(raw_text)
        
        # Skip empty or whitespace-only paragraphs
        if text and len(text.strip()) > 2:
            elements.append({
                'type': 'P',
                'id': '',
                'text': text.strip(),
                'position': match.start()
            })
    
    # Extract list items from L structures
    l_pattern = r'<L>(.*?)</L>'
    for l_match in re.finditer(l_pattern, doc_content, re.DOTALL):
        list_content = l_match.group(1)
        
        # Extract LI items within this list
        li_pattern = r'<LI>.*?<LBody[^>]*>(.*?)</LBody>.*?</LI>'
        for li_match in re.finditer(li_pattern, list_content, re.DOTALL):
            text = li_match.group(1).strip()
            text = process_inline_content(text)
            
            if text:
                elements.append({
                    'type': 'LI',
                    'id': '',
                    'text': text,
                    'position': l_match.start() + li_match.start()
                })
    
    # Extract table content properly
    table_pattern = r'<Table>(.*?)</Table>'
    for table_match in re.finditer(table_pattern, doc_content, re.DOTALL):
        table_content = table_match.group(1)
        table_position = table_match.start()
        
        # Extract each row
        tr_pattern = r'<TR>(.*?)</TR>'
        for tr_match in re.finditer(tr_pattern, table_content, re.DOTALL):
            row_content = tr_match.group(1)
            row_data = []
            
            # Extract TH cells
            th_pattern = r'<TH>.*?<P[^>]*>(.*?)</P>.*?</TH>'
            for th_match in re.finditer(th_pattern, row_content, re.DOTALL):
                cell_text = th_match.group(1).strip()
                cell_text = process_inline_content(cell_text)
                if cell_text:
                    row_data.append(cell_text)
            
            # Extract TD cells
            td_pattern = r'<TD>.*?<P[^>]*>(.*?)</P>.*?</TD>'
            for td_match in re.finditer(td_pattern, row_content, re.DOTALL):
                cell_text = td_match.group(1).strip()
                cell_text = process_inline_content(cell_text)
                if cell_text:
                    row_data.append(cell_text)
            
            # Add as table row if we got data
            if row_data:
                elements.append({
                    'type': 'TABLE_ROW',
                    'id': '',
                    'text': ' | '.join(row_data),  # Join cells with separator
                    'position': table_position + tr_match.start()
                })
    
    # Sort by position to maintain document order
    elements.sort(key=lambda x: x['position'])
    
    return elements, bookmarks

def process_inline_content(text):
    """Process inline tags within text content."""
    # Handle Link tags
    text = re.sub(r'<Link[^>]*>([^<]+)</Link>', r'\1', text)
    
    # Handle Reference tags
    text = re.sub(r'<Reference[^>]*>([^<]+)</Reference>', r'\1', text)
    
    # Remove any other tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up HTML entities
    text = html.unescape(text)
    
    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_bookmark_structure(bookmark_content):
    """Extract complete bookmark structure."""
    bookmarks = {}
    
    # Find all bookmarks with their destinations
    pattern = r'<bookmark title="([^"]+)"[^>]*>\s*<destination structID="([^"]+)"'
    for match in re.finditer(pattern, bookmark_content):
        title = match.group(1)
        struct_id = match.group(2)
        bookmarks[struct_id] = title
    
    return bookmarks

def organize_content_final(elements, bookmarks):
    """Organize all content into complete rule structure."""
    
    rules = {}
    current_rule = None
    current_section = None
    current_subsection = None
    
    for elem in elements:
        elem_type = elem['type']
        elem_id = elem['id']
        text = elem['text']
        
        # Skip table of contents entries
        if 'Table of Contents' in text or re.match(r'^Rule \d+:.*\.{5,}', text):
            continue
        
        # Skip volume/edition headers
        if 'Volume 91' in text or 'Edited by' in text:
            continue
        
        # Check if this element has a bookmark ID
        bookmark_title = bookmarks.get(elem_id, '')
        
        # Determine what this element is
        is_rule = False
        is_section = False
        is_subsection = False
        
        # Check bookmark title first
        if bookmark_title:
            if bookmark_title.startswith('Rule ') and ':' in bookmark_title:
                is_rule = True
            elif re.match(r'^\d+\.\d+', bookmark_title):
                is_section = True
            elif re.match(r'^\([a-z]\)', bookmark_title):
                is_subsection = True
        
        # Also check text content as fallback
        if not (is_rule or is_section or is_subsection):
            if text.startswith('Rule ') and ':' in text:
                is_rule = True
            elif re.match(r'^\d+\.\d+\s+', text):
                is_section = True
            elif re.match(r'^\([a-z]\)\s+', text):
                is_subsection = True
        
        # Process based on type
        if is_rule:
            # Extract rule number and title
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
            # Extract section number and title
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
            # Extract subsection letter and title
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
                    # Direct subsection of rule
                    current_subsection = {
                        'letter': subsection_letter,
                        'title': subsection_title,
                        'content': []
                    }
                    if 'direct_subsections' not in current_rule:
                        current_rule['direct_subsections'] = {}
                    current_rule['direct_subsections'][subsection_letter] = current_subsection
        
        else:
            # This is content - add to appropriate location
            if not current_rule:
                continue  # Skip content before first rule
            
            # Check for numbered list items
            if re.match(r'^\(\d+\)\s+', text):
                content_item = {
                    'type': 'numbered_item',
                    'text': text
                }
            elif elem_type == 'TABLE_ROW':
                content_item = {
                    'type': 'table_row',
                    'text': text
                }
            else:
                content_item = {
                    'type': elem_type,
                    'text': text
                }
            
            # Add to appropriate location
            if current_subsection:
                current_subsection['content'].append(content_item)
            elif current_section:
                current_section['content'].append(content_item)
            elif current_rule:
                current_rule['content'].append(content_item)
    
    # Handle appendices separately
    appendices = extract_appendices_from_elements(elements, bookmarks)
    
    return rules, appendices

def extract_appendices_from_elements(elements, bookmarks):
    """Extract appendix content from elements."""
    appendices = {}
    current_appendix = None
    in_appendix = False
    
    for elem in elements:
        text = elem['text']
        elem_id = elem['id']
        
        # Check if this starts an appendix
        if elem_id in bookmarks and 'Appendix' in bookmarks[elem_id]:
            in_appendix = True
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
        
        # Also check text
        if re.match(r'^Appendix [0-9.]+', text):
            in_appendix = True
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
        
        # Stop if we hit a rule
        if text.startswith('Rule ') and ':' in text:
            in_appendix = False
            current_appendix = None
            continue
        
        # Add content to current appendix
        if in_appendix and current_appendix:
            if elem['type'] == 'TABLE_ROW':
                content_item = {
                    'type': 'table_row',
                    'text': text
                }
            else:
                content_item = {
                    'type': elem['type'],
                    'text': text
                }
            current_appendix['content'].append(content_item)
    
    return appendices

# Import HTML creation functions from previous script
from extract_maroonbook_complete import (
    create_complete_rule_html,
    format_content_items,
    get_navigation_links,
    create_appendix_html,
    create_complete_index_with_appendices
)

def main():
    """Main processing function."""
    
    xml_path = Path("/Users/ben/app/SLRinator/v91 The Maroonbook.xml")
    output_dir = Path("/Users/ben/app/citation-editor/maroonbook_final")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("FINAL Maroonbook Extraction")
    print("=" * 60)
    
    # Extract all content with edge case handling
    print("Extracting all content from XML...")
    elements, bookmarks = extract_all_content_final(xml_path)
    print(f"  Found {len(elements)} total elements")
    print(f"  Found {len(bookmarks)} bookmarked sections")
    
    # Count element types
    from collections import Counter
    type_counts = Counter(elem['type'] for elem in elements)
    print("\nElement types found:")
    for elem_type, count in type_counts.most_common():
        print(f"  {elem_type}: {count}")
    
    # Organize into complete structure
    print("\nOrganizing content into rules and appendices...")
    rules, appendices = organize_content_final(elements, bookmarks)
    print(f"  Organized into {len(rules)} rules")
    print(f"  Found {len(appendices)} appendices")
    
    # Process each rule
    total_content = 0
    for rule_num in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[rule_num]
        
        # Count all content
        rule_content = len(rule.get('content', []))
        for section in rule.get('sections', {}).values():
            rule_content += len(section.get('content', []))
            for subsection in section.get('subsections', {}).values():
                rule_content += len(subsection.get('content', []))
        for subsection in rule.get('direct_subsections', {}).values():
            rule_content += len(subsection.get('content', []))
        
        total_content += rule_content
        
        print(f"\nRule {rule_num}: {rule['title']}")
        print(f"  Total content items: {rule_content}")
        print(f"  Sections: {len(rule.get('sections', {}))}")
        
        # Create HTML
        html_content = create_complete_rule_html(rule)
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
        print(f"\nAppendix {app_num}: {app['title']} ({len(app['content'])} items)")
        
        html_content = create_appendix_html(app)
        html_path = output_dir / f"appendix_{app_num.replace('.', '_')}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    # Create index
    print("\nCreating final index...")
    index_html = create_complete_index_with_appendices(rules, appendices)
    index_path = output_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Save metadata
    metadata = {
        "source": "The Maroonbook - 91st Edition",
        "publisher": "University of Chicago Law Review",
        "extracted_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "total_appendices": len(appendices),
        "total_content_items": total_content,
        "extraction_method": "Final complete extraction with all edge cases handled"
    }
    
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ FINAL extraction complete!")
    print(f"Output: {output_dir}")
    print(f"Total content items: {total_content}")

if __name__ == "__main__":
    main()