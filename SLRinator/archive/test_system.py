#!/usr/bin/env python3
"""
Test script to verify SLRinator system components
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    
    try:
        from stage1.citation_parser import CitationParser, Citation
        print("✅ Citation Parser imported")
    except ImportError as e:
        print(f"❌ Citation Parser import failed: {e}")
        return False
    
    try:
        from stage1.source_retriever import SourceRetriever
        print("✅ Source Retriever imported")
    except ImportError as e:
        print(f"❌ Source Retriever import failed: {e}")
        return False
    
    try:
        from stage1.pdf_processor import PDFProcessor
        print("✅ PDF Processor imported")
    except ImportError as e:
        print(f"❌ PDF Processor import failed: {e}")
        return False
    
    try:
        from stage1.spreadsheet_manager import SpreadsheetManager
        print("✅ Spreadsheet Manager imported")
    except ImportError as e:
        print(f"❌ Spreadsheet Manager import failed: {e}")
        return False
    
    try:
        from stage3.footnote_processor import FootnoteProcessor
        print("✅ Footnote Processor imported")
    except ImportError as e:
        print(f"❌ Footnote Processor import failed: {e}")
        return False
    
    try:
        from stage3.quote_checker import QuoteChecker
        print("✅ Quote Checker imported")
    except ImportError as e:
        print(f"❌ Quote Checker import failed: {e}")
        return False
    
    try:
        from stage4.bluebook_checker import BluebookChecker
        print("✅ Bluebook Checker imported")
    except ImportError as e:
        print(f"❌ Bluebook Checker import failed: {e}")
        return False
    
    return True


def test_citation_parser():
    """Test citation parsing functionality"""
    print("\nTesting Citation Parser...")
    
    from stage1.citation_parser import CitationParser
    
    parser = CitationParser()
    
    test_citations = [
        ("Smith v. Jones, 123 U.S. 456 (2020)", "001", "Smith"),
        ("42 U.S.C. § 1983 (2018)", "002", "USC"),
        ("John Doe, Article Title, 100 Harv. L. Rev. 123 (2020)", "003", "Doe"),
        ("https://www.example.com/article (last visited Jan. 1, 2024)", "004", "Web"),
    ]
    
    for raw_text, source_id, short_name in test_citations:
        citation = parser.parse_citation(raw_text, source_id, short_name)
        print(f"  Parsed: {citation.type.value} - {citation.short_name}")
    
    stats = parser.get_statistics()
    print(f"✅ Parsed {stats['total_citations']} citations")
    print(f"   Types: {stats['types']}")
    
    return True


def test_bluebook_checker():
    """Test Bluebook compliance checking"""
    print("\nTesting Bluebook Checker...")
    
    from stage4.bluebook_checker import BluebookChecker
    
    checker = BluebookChecker()
    
    test_footnotes = {
        1: "Smith V. Jones, 123 US 456 (2020).",  # Intentional errors
        2: "42 U.S.C. 1983 (2018).",  # Missing section symbol
        3: "John Doe, Article Title, 100 Harvard Law Review 123 (2020).",  # Unabbreviated
    }
    
    for fn_num, text in test_footnotes.items():
        checker.check_footnote(fn_num, text)
    
    violations = checker._violations_to_dict()
    print(f"✅ Found {len(violations)} Bluebook violations")
    
    for v in violations[:3]:
        print(f"   - {v['issue']}: {v['suggestion']}")
    
    return True


def test_directories():
    """Test that all required directories exist"""
    print("\nTesting directory structure...")
    
    required_dirs = [
        "data/Sourcepull",
        "data/Round1",
        "data/Round2",
        "cache",
        "logs",
        "reports",
        "config",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            all_exist = False
    
    return all_exist


def main():
    """Run all tests"""
    print("="*60)
    print("SLRinator System Test")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_imports()))
    results.append(("Citation Parser Test", test_citation_parser()))
    results.append(("Bluebook Checker Test", test_bluebook_checker()))
    results.append(("Directory Test", test_directories()))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the setup.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())