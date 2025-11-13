"""
Test citation splitting on specific footnotes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_parser import CitationParser
from src.word_extractor import extract_footnotes

# Extract footnotes from Word doc
word_doc_path = "/Users/ben/app/slrapp/78 SLR V2 R2 F/References/Bersh_PreR2.docx"
footnotes = extract_footnotes(word_doc_path)

# Expected counts
expected_counts = {
    78: 3,
    79: 2,
    86: 2,
    93: 3,
    108: 8,
    111: 4,
    113: 7,
}

print("="*80)
print("CITATION SPLITTING TEST - SPECIFIC FOOTNOTES")
print("="*80)

passing = 0
total = len(expected_counts)

for fn_num in sorted(expected_counts.keys()):
    if fn_num not in footnotes:
        print(f"\n❌ FN{fn_num}: NOT FOUND in document")
        continue

    fn_text = footnotes[fn_num]
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

    if not passed:
        print(f"   Text preview: {fn_text[:100]}...")
        print(f"   Citations found:")
        for i, cit in enumerate(citations, 1):
            preview = cit.full_text[:80].replace('\n', ' ')
            print(f"      [{i}] {preview}...")

print("\n" + "="*80)
print(f"RESULTS: {passing}/{total} passing ({passing*100//total}%)")
print("="*80)
