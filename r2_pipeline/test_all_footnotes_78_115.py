"""
Test citation splitting on ALL footnotes from 78-115.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_parser import CitationParser
from docx import Document
from lxml import etree
import os

# Extract all footnotes from Word doc
doc_path = "/Users/ben/app/slrapp/78 SLR V2 R2 F/References/Bersh_PreR2.docx"
doc = Document(doc_path)

# Get footnotes part
footnotes_part = None
for rel in doc.part.rels.values():
    if "footnotes" in rel.target_ref:
        footnotes_part = rel.target_part
        break

footnotes_text = {}
if footnotes_part:
    footnotes_xml = footnotes_part.blob
    root = etree.fromstring(footnotes_xml)
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    for footnote in root.findall('.//w:footnote', namespaces):
        xml_id = footnote.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
        if xml_id:
            text_parts = []
            for t in footnote.findall('.//w:t', namespaces):
                if t.text:
                    text_parts.append(t.text)
            # XML IDs are +1 ahead of actual footnote numbers
            actual_fn_num = int(xml_id) - 1
            footnotes_text[actual_fn_num] = ''.join(text_parts)

# Count R1 files for all footnotes 78-115 (excluding "A" supplemental)
r1_dir = '/Users/ben/app/slrapp/78 SLR V2 R2 F/78 SLR V2 R1'
r1_files = os.listdir(r1_dir)

expected_counts = {}
for fn_num in range(78, 116):
    fn_str = f"{fn_num:03d}"
    all_fn_files = [f for f in r1_files if f.startswith(f'R1-{fn_str}-')]
    # Exclude "A" supplemental files
    main_citations = [f for f in all_fn_files if not f.split('-')[2].endswith('A')]
    if main_citations:
        expected_counts[fn_num] = len(main_citations)

print("="*80)
print("CITATION SPLITTING TEST - ALL FOOTNOTES 78-115")
print("="*80)

passing = 0
failing = 0
missing = 0

for fn_num in range(78, 116):
    if fn_num not in footnotes_text:
        if fn_num in expected_counts:
            print(f"\n❌ FN{fn_num}: NOT FOUND in document (but {expected_counts[fn_num]} R1 files exist)")
            missing += 1
        continue

    if fn_num not in expected_counts:
        # No R1 files for this footnote
        continue

    fn_text = footnotes_text[fn_num]
    expected = expected_counts[fn_num]

    parser = CitationParser(fn_text, fn_num)
    citations = parser.parse()
    got = len(citations)

    passed = (got == expected)
    if passed:
        passing += 1
    else:
        failing += 1

    status = "✓" if passed else "❌"
    diff = got - expected
    diff_str = f"({diff:+d})" if diff != 0 else ""

    if not passed:
        print(f"\n{status} FN{fn_num}: Expected {expected}, Got {got} {diff_str}")
        print(f"   Text: {len(fn_text)} chars, {fn_text.count(';')} semicolons")
        print(f"   Preview: {fn_text[:100]}...")

total = passing + failing
accuracy = (passing * 100 // total) if total > 0 else 0

print("\n" + "="*80)
print(f"RESULTS:")
print(f"  Passing: {passing}")
print(f"  Failing: {failing}")
print(f"  Missing: {missing}")
print(f"  Total Tested: {total}")
print(f"  Accuracy: {accuracy}%")
print("="*80)

# Summary of all results
print("\n" + "="*80)
print("DETAILED SUMMARY")
print("="*80)
for fn_num in range(78, 116):
    if fn_num not in expected_counts:
        continue
    if fn_num not in footnotes_text:
        print(f"FN{fn_num}: MISSING from document")
        continue

    expected = expected_counts[fn_num]
    parser = CitationParser(footnotes_text[fn_num], fn_num)
    got = len(parser.parse())
    status = "✓" if got == expected else "❌"
    print(f"{status} FN{fn_num}: {got}/{expected}")
