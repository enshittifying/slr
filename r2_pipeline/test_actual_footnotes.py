"""
Test citation splitting on ACTUAL footnotes from Word doc with REAL expected counts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_parser import CitationParser
from docx import Document
from lxml import etree

# Extract footnotes from Word doc
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

# Real expected counts from R1 files (excluding "A" supplemental files)
expected_counts = {
    78: 3,
    79: 1,
    86: 2,
    93: 3,
    108: 8,  # 10 total files, but 2 are "A" supplemental
    111: 4,  # 5 total files, but 1 is "A" supplemental
    113: 7,  # 8 total files, but 1 is "A" supplemental
    114: 4,
}

print("="*80)
print("CITATION SPLITTING TEST - ACTUAL FOOTNOTES")
print("="*80)

passing = 0
total = len(expected_counts)

for fn_num in sorted(expected_counts.keys()):
    if fn_num not in footnotes_text:
        print(f"\n❌ FN{fn_num}: NOT FOUND in document")
        continue

    fn_text = footnotes_text[fn_num]
    expected = expected_counts[fn_num]

    parser = CitationParser(fn_text, fn_num)
    citations = parser.parse()
    got = len(citations)

    passed = (got == expected)
    if passed:
        passing += 1

    status = "✓" if passed else "❌"
    diff = got - expected
    diff_str = f"({diff:+d})" if diff != 0 else ""

    print(f"\n{status} FN{fn_num}: Expected {expected}, Got {got} {diff_str}")
    print(f"   Text length: {len(fn_text)} chars, {fn_text.count(';')} semicolons")

    if not passed:
        print(f"   First 100 chars: {fn_text[:100]}...")
        print(f"   Citations found:")
        for i, cit in enumerate(citations, 1):
            preview = cit.full_text[:80].replace('\n', ' ')
            print(f"      [{i}] {preview}...")

print("\n" + "="*80)
print(f"RESULTS: {passing}/{total} passing ({passing*100//total}%)")
print("="*80)
