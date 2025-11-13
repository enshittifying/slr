"""
Test citation splitting on specific footnotes with hard-coded text.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_parser import CitationParser

# Test data - simplified versions
test_cases = {
    78: {
        "text": "*See* Abernathy v. SellPoolSuppliesOnline.com, Inc., No. 24-CV-00754, 2024 WL 3642634 (N.D. Cal. July 1, 2024); *id.* at *9-10; Yoxen v. Snap Inc., No. 24-CV-01077-JSC, 2024 WL 3259865, at *7 n.11 (N.D. Cal. June 28, 2024).",
        "expected": 3
    },
    79: {
        "text": "Abernathy, 2024 WL 3642634, at *10; Yoxen, 2024 WL 3259865, at *7 n.11.",
        "expected": 2
    },
    86: {
        "text": "Jason Rantanen, *The Malleability of Patent Rights*, 2015 Mich. St. L. Rev. 895, 904-05 (\"[T]here is always a human actor involved at various points in the interpretation process . . . .\"); *supra* note 25.",
        "expected": 2
    },
    93: {
        "text": "*See* Yoxen, 2024 WL 3259865, at *7 n.11; *see also* Doe 1 v. GitHub, Inc., WL 235217, at *6 (N.D. Cal. Jan. 22, 2024); *cf.* Kirk Kara Corp. v. W. Stone & Metal Corp., No. CV 20-1931-DMG (EX), 2020 WL 5991503, at *6 (C.D. Cal. Aug. 14, 2020).",
        "expected": 3
    },
    111: {
        "text": "Real World Media LLC v. Daily Caller, Inc., 744 F. Supp. 3d 24, 40 (D.D.C. 2024); Doe 1 v. GitHub, Inc., No. 22-CV-06823-JST, 2024 WL 4336532, at *2 (N.D. Cal. Sept. 27, 2024); *compare *Nimmer On Copyright, *supra* note 25 § 12A.10(C)(1) (\"[T]o be actionable...'\" (quoting O'Neal v.Sideshow, 583 F.Supp. 3d. 1282, 1287 (C.D. Cal. 2022)))*, with* Goldstein On Copyright at § 7.18 (\"As a rule, the works must be identical...\").",
        "expected": 4
    },
    108: {
        "text": "*See* Doe 1, 2024 WL 235217, at *8; Advanta-STAR Auto. Rsch. Corp. of Am. v. Search Optics, LLC, 672 F. Supp. 3d 1035, 1057 (S.D. Cal. 2023); O'Neal v. Sideshow, Inc., 583 F. Supp. 3d 1282, 1287 (C.D. Cal. 2022); Kirk Kara Corp., 2020 WL 5991503, at *6; *see also* Schneider v. YouTube, LLC, 674 F. Supp. 3d 704, 723-24 (N.D. Cal. 2023); *cf.* Doe 1 v. GitHub, Inc., 784 F. Supp. 3d 1245, 1253 (N.D. Cal. 2024); *contra* Munro v. Fairchild Tropical Botanic Garden, Inc., WL 452257, at *11 (S.D. Fla. Jan 13, 2022).",
        "expected": 8
    },
    113: {
        "text": "A smattering of courts has considered copyrightability in an unsystematic and ungeneralizable fashion. One court focused on the copyrightability inquiry within the context of class certification. See Schneider v. YouTube, LLC, 674 F. Supp. 3d 704, 723-24 (N.D. Cal. 2023). Another court positioned the inquiry within the scienter requirement. See Munro v. Fairchild Tropical Botanic Garden, Inc., WL 452257, at *11 (S.D. Fla. Jan 13, 2022). Another court similarly focused on ownership. Sanborn Libr. LLC v. ERIS Info, Inc., WL 1744630, at *20 (S.D.N.Y. Mar. 25, 2024). Yet another court imported a copyrightability requirement seemingly by mistake. Say It Visually, Inc. v. Real Est. Educ. Co., Inc., 2025 WL 933951, at *8 (N.D. Ill. Mar. 27, 2025) (quoting Design Basics, LLC v. Signature Contr. Inc., 994 F.3d 879, 886 (7th Cir. 2021)). In support of this contention, the court cited a case that is entirely about copyright infringement. Say It Visually, 2025 WL 933951, at *8 (citing Design Basics, 994 F.3d at 886). The closest a court has come to a proper acknowledgement was this statement. Raw Story Media, Inc. v. OpenAI, Inc., 756 F. Supp. 3d 1, 7 (S.D.N.Y. 2024). This is distinct from an inquiry into the copyrightability of the training data itself. Id.",
        "expected": 7
    },
}

print("="*80)
print("CITATION SPLITTING TEST")
print("="*80)

passing = 0
total = len(test_cases)

for fn_num in sorted(test_cases.keys()):
    test = test_cases[fn_num]
    fn_text = test["text"]
    expected = test["expected"]

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

    # Always show citations for debugging
    for i, cit in enumerate(citations, 1):
        preview = cit.full_text[:100].replace('\n', ' ')
        print(f"      [{i}] {preview}...")

print("\n" + "="*80)
print(f"RESULTS: {passing}/{total} passing ({passing*100//total}%)")
print("="*80)
