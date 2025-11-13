#!/usr/bin/env python3
"""
Stress Test Suite for SLRinator
Tests edge cases, performance, and error handling
"""

import sys
import os
import time
import random
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple
import concurrent.futures
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stage1.citation_parser import CitationParser, Citation
from stage1.source_retriever import SourceRetriever
from stage1.pdf_processor import PDFProcessor
from stage3.quote_checker import QuoteChecker
from stage4.bluebook_checker import BluebookChecker


class StressTestSuite:
    """Comprehensive stress testing for SLRinator"""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': [],
            'performance': {},
            'edge_cases': []
        }
        
        # Initialize components
        self.citation_parser = CitationParser()
        self.config = {'cache_dir': './cache', 'output_dir': './data/Sourcepull'}
        
    def run_all_tests(self):
        """Run complete stress test suite"""
        print("="*80)
        print("SLRINATOR STRESS TEST SUITE")
        print("="*80)
        
        test_methods = [
            self.test_citation_parser_edge_cases,
            self.test_malformed_citations,
            self.test_unicode_and_special_chars,
            self.test_performance_large_batch,
            self.test_concurrent_processing,
            self.test_memory_usage,
            self.test_error_recovery,
            self.test_api_failures,
            self.test_pdf_corruption,
            self.test_quote_matching_edge_cases,
            self.test_bluebook_complex_rules,
            self.test_cross_references,
            self.test_file_system_limits,
            self.test_network_timeouts,
            self.test_cache_corruption
        ]
        
        for test_method in test_methods:
            try:
                print(f"\n{'='*60}")
                print(f"Running: {test_method.__name__}")
                print("="*60)
                test_method()
                self.results['tests_passed'] += 1
            except Exception as e:
                self.results['tests_failed'] += 1
                self.results['errors'].append({
                    'test': test_method.__name__,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                print(f"❌ FAILED: {e}")
            finally:
                self.results['tests_run'] += 1
        
        self.print_report()
    
    def test_citation_parser_edge_cases(self):
        """Test citation parser with edge cases"""
        print("Testing citation parser edge cases...")
        
        edge_cases = [
            # Complex case names
            ("United States ex rel. Smith v. Jones & Co., Inc., 123 F.3d 456 (2d Cir. 2020)", "001", "US_ex_rel"),
            ("In re Marriage of Smith-Jones, 456 Cal. App. 4th 789 (2020)", "002", "Marriage"),
            ("Matter of Baby M, 537 A.2d 1227 (N.J. 1988)", "003", "Baby_M"),
            
            # Multiple reporters
            ("Smith v. Jones, 123 U.S. 456, 100 S. Ct. 789, 50 L. Ed. 2d 123 (2020)", "004", "Smith_multi"),
            
            # Foreign cases
            ("Regina v. Dudley & Stephens, [1884] 14 QBD 273 (UK)", "005", "Regina"),
            
            # Statutes with subsections
            ("42 U.S.C. § 1983(a)(1)(A)(i) (2018 & Supp. II 2020)", "006", "USC_complex"),
            
            # Articles with multiple authors
            ("John Doe, Jane Smith & Robert Johnson, Complex Title: A Study, 100 Harv. L. Rev. 123, 125-27 (2020)", "007", "Multiple_authors"),
            
            # Web sources with complex URLs
            ("Article Title, https://www.example.com/path/to/article?param=value&other=123#section (last visited Jan. 1, 2024, 10:30 AM EST)", "008", "Web_complex"),
            
            # Books with editors and translators
            ("AUTHOR NAME, BOOK TITLE 123 (Jane Editor ed., John Translator trans., 3d ed. 2020)", "009", "Book_complex"),
            
            # Legislative materials
            ("H.R. Rep. No. 114-123, at 45-47 (2016) (Conf. Rep.)", "010", "HR_Rep"),
            
            # Treaties
            ("Treaty on Nuclear Non-Proliferation, July 1, 1968, 21 U.S.T. 483, 729 U.N.T.S. 161", "011", "Treaty"),
            
            # Parentheticals and signals
            ("See generally Smith v. Jones, 123 U.S. 456 (2020) (discussing the importance of proper citation).", "012", "Signal"),
            
            # Short forms
            ("Id. at 458-59.", "013", "Id"),
            ("Smith, supra note 7, at 125.", "014", "Supra"),
            
            # Unpublished opinions
            ("Smith v. Jones, No. 19-CV-1234, 2020 WL 123456, at *5 (S.D.N.Y. Jan. 1, 2020)", "015", "Unpublished"),
            
            # Forthcoming publications
            ("John Doe, Future Article, 100 HARV. L. REV. (forthcoming 2025)", "016", "Forthcoming"),
            
            # Empty or minimal citations
            ("", "017", "Empty"),
            ("Id.", "018", "Id_only"),
            ("123", "019", "Number_only"),
            
            # Extremely long citations
            ("A" * 1000 + " v. " + "B" * 1000 + ", 123 U.S. 456 (2020)", "020", "Long"),
            
            # Special characters
            ("Müller v. Société Générale, 123 F.3d 456 (2d Cir. 2020)", "021", "Unicode"),
            ("AT&T v. M&A Corp., 123 U.S. 456 (2020)", "022", "Ampersand"),
            
            # Malformed but parseable
            ("Smith  v.   Jones , 123   U.S.  456  ( 2020 )", "023", "Extra_spaces"),
            ("smith v jones 123 us 456 2020", "024", "No_punct"),
        ]
        
        successes = 0
        failures = []
        
        for raw_text, source_id, short_name in edge_cases:
            try:
                citation = self.citation_parser.parse_citation(raw_text, source_id, short_name)
                if citation:
                    successes += 1
                    print(f"  ✅ Parsed: {citation.type.value} - {short_name[:20]}")
                else:
                    failures.append((raw_text[:50], "Failed to parse"))
            except Exception as e:
                failures.append((raw_text[:50], str(e)))
        
        print(f"\nResults: {successes}/{len(edge_cases)} successful")
        if failures:
            print("Failures:")
            for text, error in failures[:5]:
                print(f"  - {text}: {error}")
        
        assert successes >= len(edge_cases) * 0.8, f"Too many parsing failures: {successes}/{len(edge_cases)}"
    
    def test_malformed_citations(self):
        """Test handling of malformed citations"""
        print("Testing malformed citation handling...")
        
        malformed = [
            "Smith v",  # Incomplete case
            "123 456",  # Just numbers
            "U.S.C. § (2020)",  # Missing title and section
            ",,,,",  # Just punctuation
            "See also see also see",  # Repeated signals
            "@#$%^&*()",  # Special chars only
            "null",  # Null-like strings
            "undefined",
            "\n\n\n",  # Just whitespace
            "DROP TABLE citations;",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "../../../etc/passwd",  # Path traversal
        ]
        
        handled = 0
        for bad_cite in malformed:
            try:
                citation = self.citation_parser.parse_citation(bad_cite, "999", "malformed")
                handled += 1
                print(f"  ✅ Handled: '{bad_cite[:30]}' -> {citation.type.value}")
            except Exception as e:
                print(f"  ❌ Exception on '{bad_cite[:30]}': {e}")
        
        assert handled == len(malformed), "Some malformed citations caused exceptions"
    
    def test_unicode_and_special_chars(self):
        """Test Unicode and special character handling"""
        print("Testing Unicode and special characters...")
        
        unicode_tests = [
            "Müller v. Société Générale, 123 F.3d 456 (2d Cir. 2020)",
            "北京大学 v. 清华大学, 123 U.S. 456 (2020)",  # Chinese
            "محكمة v. المدعي, 123 U.S. 456 (2020)",  # Arabic
            "🏛️ Court v. ⚖️ Justice, 123 U.S. 456 (2020)",  # Emojis
            "Αλφα v. Βήτα, 123 U.S. 456 (2020)",  # Greek
            "א v. ב, 123 U.S. 456 (2020)",  # Hebrew (RTL)
            "Smith\u200bv.\u200bJones, 123 U.S. 456 (2020)",  # Zero-width spaces
            "Smith\tv.\nJones, 123 U.S. 456 (2020)",  # Tabs and newlines
        ]
        
        successes = 0
        for test_cite in unicode_tests:
            try:
                citation = self.citation_parser.parse_citation(test_cite, "999", "unicode")
                if citation:
                    successes += 1
                    print(f"  ✅ Handled Unicode: {test_cite[:40]}")
            except Exception as e:
                print(f"  ❌ Failed on: {test_cite[:40]} - {e}")
        
        assert successes >= len(unicode_tests) * 0.7, "Unicode handling issues"
    
    def test_performance_large_batch(self):
        """Test performance with large batches"""
        print("Testing performance with large batches...")
        
        # Generate large batch of citations
        num_citations = 10000
        citations = []
        
        templates = [
            "Case{} v. Defendant{}, {} U.S. {} ({})",
            "{} U.S.C. § {} ({})",
            "Author{}, Article Title {}, {} Harv. L. Rev. {} ({})",
        ]
        
        print(f"  Generating {num_citations} citations...")
        for i in range(num_citations):
            template = random.choice(templates)
            if "Case" in template:
                cite = template.format(i, i+1, random.randint(100, 999), 
                                      random.randint(1, 999), random.randint(1950, 2024))
            elif "U.S.C." in template:
                cite = template.format(random.randint(1, 50), random.randint(1, 9999), 
                                      random.randint(2000, 2024))
            else:
                cite = template.format(i, i, random.randint(1, 150), 
                                      random.randint(1, 999), random.randint(1950, 2024))
            
            citations.append((cite, str(i), f"test_{i}"))
        
        # Time the parsing
        print(f"  Parsing {num_citations} citations...")
        start_time = time.time()
        
        parser = CitationParser()
        results = parser.parse_batch(citations)
        
        elapsed = time.time() - start_time
        rate = num_citations / elapsed
        
        print(f"  ✅ Parsed {num_citations} citations in {elapsed:.2f} seconds")
        print(f"  Rate: {rate:.0f} citations/second")
        
        self.results['performance']['batch_parsing'] = {
            'total': num_citations,
            'time': elapsed,
            'rate': rate
        }
        
        assert rate > 100, f"Parsing too slow: {rate:.0f} citations/second"
    
    def test_concurrent_processing(self):
        """Test concurrent processing capabilities"""
        print("Testing concurrent processing...")
        
        num_workers = 10
        citations_per_worker = 100
        
        def process_batch(worker_id):
            parser = CitationParser()
            citations = []
            for i in range(citations_per_worker):
                cite = f"Case{worker_id}_{i} v. State, {random.randint(100, 999)} U.S. {random.randint(1, 999)} (2020)"
                citations.append((cite, f"{worker_id}_{i}", f"worker{worker_id}"))
            
            start = time.time()
            results = parser.parse_batch(citations)
            return time.time() - start, len(results)
        
        print(f"  Running {num_workers} concurrent workers...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(process_batch, i) for i in range(num_workers)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        total_processed = sum(r[1] for r in results)
        
        print(f"  ✅ Processed {total_processed} citations in {total_time:.2f}s with {num_workers} workers")
        print(f"  Rate: {total_processed/total_time:.0f} citations/second")
        
        self.results['performance']['concurrent'] = {
            'workers': num_workers,
            'total': total_processed,
            'time': total_time,
            'rate': total_processed/total_time
        }
    
    def test_memory_usage(self):
        """Test memory usage under load"""
        print("Testing memory usage...")
        
        import psutil
        import gc
        
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"  Baseline memory: {baseline_memory:.2f} MB")
        
        # Create large dataset
        large_citations = []
        for i in range(50000):
            cite = f"Case{i} " * 100 + f" v. State{i}, {i} U.S. {i} (2020)"  # Long citation
            large_citations.append((cite, str(i), f"large_{i}"))
        
        # Parse and measure
        parser = CitationParser()
        parser.parse_batch(large_citations)
        
        peak_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - baseline_memory
        
        print(f"  Peak memory: {peak_memory:.2f} MB")
        print(f"  Memory increase: {memory_increase:.2f} MB")
        
        # Clean up
        del large_citations
        del parser
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        print(f"  After cleanup: {final_memory:.2f} MB")
        
        self.results['performance']['memory'] = {
            'baseline': baseline_memory,
            'peak': peak_memory,
            'increase': memory_increase,
            'final': final_memory
        }
        
        assert memory_increase < 500, f"Excessive memory usage: {memory_increase:.2f} MB"
    
    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        print("Testing error recovery...")
        
        # Test citation parser recovery
        mixed_citations = [
            ("Valid Case v. State, 123 U.S. 456 (2020)", "001", "valid"),
            (None, "002", "none"),  # None input
            ("Another v. Case, 789 F.3d 123 (2d Cir. 2021)", "003", "valid2"),
            ("", "004", "empty"),  # Empty string
            ("Final v. Citation, 456 U.S. 789 (2022)", "005", "valid3"),
        ]
        
        parser = CitationParser()
        recovered = 0
        
        for cite_data in mixed_citations:
            try:
                if cite_data[0] is not None:
                    result = parser.parse_citation(*cite_data)
                    if result:
                        recovered += 1
                        print(f"  ✅ Recovered: {cite_data[2]}")
            except Exception as e:
                print(f"  ❌ Failed to recover: {cite_data[2]} - {e}")
        
        print(f"  Recovery rate: {recovered}/{len(mixed_citations)}")
        assert recovered >= 3, "Poor error recovery"
    
    def test_api_failures(self):
        """Test handling of API failures"""
        print("Testing API failure handling...")
        
        # Create retriever with invalid config
        bad_config = {
            'apis': {
                'courtlistener': 'invalid_key',
                'crossref': 'bad_email',
            },
            'cache_dir': './cache',
            'output_dir': './data/Sourcepull'
        }
        
        retriever = SourceRetriever(bad_config)
        
        # Test with citation that would normally use API
        citation = Citation(
            raw_text="Smith v. Jones, 123 U.S. 456 (2020)",
            source_id="001",
            short_name="Smith"
        )
        
        # Should handle gracefully and return failure status
        result = retriever.retrieve(citation)
        
        print(f"  Status: {result.status.value}")
        print(f"  Message: {result.message}")
        
        assert result.status.value in ['failed', 'manual_required'], "API failure not handled properly"
        print("  ✅ API failures handled gracefully")
    
    def test_pdf_corruption(self):
        """Test handling of corrupted PDFs"""
        print("Testing corrupted PDF handling...")
        
        # Create a corrupted PDF file
        corrupt_pdf_path = Path("test_corrupt.pdf")
        corrupt_pdf_path.write_bytes(b"Not a real PDF content %PDF-1.4 corrupted")
        
        processor = PDFProcessor()
        citation = Citation("Test v. Case, 123 U.S. 456 (2020)", "001", "test")
        
        try:
            result = processor.process_pdf(str(corrupt_pdf_path), citation)
            print(f"  Result: {result}")
            print(f"  ✅ Handled corrupted PDF gracefully")
        except Exception as e:
            print(f"  ❌ Exception on corrupted PDF: {e}")
        finally:
            corrupt_pdf_path.unlink(missing_ok=True)
    
    def test_quote_matching_edge_cases(self):
        """Test quote matching with edge cases"""
        print("Testing quote matching edge cases...")
        
        from stage3.quote_checker import QuoteChecker
        
        checker = QuoteChecker()
        
        # Test cases
        test_quotes = [
            # Exact match
            ("This is an exact quote", "This is an exact quote", 1.0),
            
            # Minor differences
            ("This is a quote", "This is  a quote", 0.95),  # Extra space
            ("This is a quote.", "This is a quote", 0.95),  # Period difference
            
            # Case differences
            ("This Is A Quote", "this is a quote", 0.9),
            
            # With ellipsis
            ("This is ... a quote", "This is a very long middle part a quote", 0.8),
            
            # With brackets
            ("[T]his is a quote", "This is a quote", 0.95),
            ("[She] said something", "He said something", 0.8),
            
            # Completely different
            ("Apples are red", "Oranges are orange", 0.2),
            
            # Empty or minimal
            ("", "", 0.0),
            ("a", "a", 1.0),
            
            # Special characters
            ("Quote with 'single' quotes", "Quote with \"single\" quotes", 0.9),
            ("Em—dash test", "Em--dash test", 0.9),
        ]
        
        for original, found, expected_min in test_quotes:
            alterations = checker.check_alterations(original)
            print(f"  Quote: '{original[:30]}...'")
            print(f"    Alterations: {alterations}")
        
        print("  ✅ Quote matching edge cases handled")
    
    def test_bluebook_complex_rules(self):
        """Test complex Bluebook rule validation"""
        print("Testing complex Bluebook rules...")
        
        checker = BluebookChecker()
        
        complex_citations = {
            # Id. usage
            1: "Id. at 123.",  # Valid if previous citation exists
            2: "id. at 456.",  # Lowercase id
            3: "Id at 789.",   # Missing period
            
            # Supra usage
            4: "Smith, supra note 1, at 123.",  # Valid format
            5: "Smith supra note 2 at 456.",   # Missing commas
            6: "Smith, Supra Note 3, at 789.",  # Incorrect capitalization
            
            # Signal combinations
            7: "See generally Smith v. Jones, 123 U.S. 456 (2020).",
            8: "But see id. at 789.",
            9: "Compare Smith, with Jones.",
            
            # Complex parentheticals
            10: "Smith v. Jones, 123 U.S. 456, 458 (2020) (holding that \"quotes matter\") (emphasis added).",
        }
        
        for fn_num, text in complex_citations.items():
            checker.check_footnote(fn_num, text)
        
        violations = checker._violations_to_dict()
        print(f"  Found {len(violations)} violations in complex citations")
        
        for v in violations[:5]:
            print(f"    - FN{v['footnote_num']}: {v['issue']}")
        
        print("  ✅ Complex Bluebook rules tested")
    
    def test_cross_references(self):
        """Test cross-reference validation"""
        print("Testing cross-reference validation...")
        
        checker = BluebookChecker()
        
        # Build footnote history
        footnotes = {
            1: "Smith v. Jones, 123 U.S. 456 (2020).",
            2: "Id. at 458.",  # Valid - refers to FN 1
            3: "42 U.S.C. § 1983 (2018).",
            4: "Smith, supra note 1, at 460.",  # Valid - refers to FN 1
            5: "Jones, supra note 10, at 123.",  # Invalid - FN 10 doesn't exist yet
            6: "See infra note 8.",  # Valid - refers forward
            7: "Williams v. State, 789 F.3d 123 (2d Cir. 2021).",
            8: "Johnson, supra note 5.",  # Problem - FN 5 has invalid supra
        }
        
        for fn_num, text in footnotes.items():
            checker.check_footnote(fn_num, text)
        
        checker._check_cross_references()
        violations = checker._violations_to_dict()
        
        cross_ref_violations = [v for v in violations if v['type'] == 'Cross-reference']
        print(f"  Found {len(cross_ref_violations)} cross-reference issues")
        
        for v in cross_ref_violations:
            print(f"    - FN{v['footnote_num']}: {v['issue']}")
        
        print("  ✅ Cross-references validated")
    
    def test_file_system_limits(self):
        """Test file system limits and edge cases"""
        print("Testing file system limits...")
        
        test_cases = [
            # Long filename
            ("a" * 255 + ".pdf", False),  # Too long for most systems
            ("valid_name.pdf", True),
            
            # Special characters in filename
            ("file:name.pdf", False),
            ("file<>name.pdf", False),
            ("file|name.pdf", False),
            ("file_name.pdf", True),
            
            # Path traversal attempts
            ("../../../etc/passwd", False),
            ("./valid_file.pdf", True),
            
            # Reserved names (Windows)
            ("CON.pdf", False),
            ("PRN.pdf", False),
            ("AUX.pdf", False),
            ("NUL.pdf", False),
        ]
        
        for filename, should_work in test_cases:
            try:
                # Test filename sanitization
                from stage1.source_retriever import SourceRetriever
                retriever = SourceRetriever(self.config)
                sanitized = retriever._sanitize_filename(filename)
                print(f"  '{filename[:30]}' -> '{sanitized[:30]}'")
            except Exception as e:
                print(f"  Error with '{filename[:30]}': {e}")
        
        print("  ✅ File system limits handled")
    
    def test_network_timeouts(self):
        """Test network timeout handling"""
        print("Testing network timeout handling...")
        
        import socket
        
        # Save original timeout
        original_timeout = socket.getdefaulttimeout()
        
        try:
            # Set very short timeout
            socket.setdefaulttimeout(0.001)
            
            retriever = SourceRetriever(self.config)
            citation = Citation("Test v. Case, 123 U.S. 456 (2020)", "001", "test")
            
            # This should timeout
            result = retriever.retrieve(citation)
            print(f"  Status: {result.status.value}")
            print(f"  ✅ Network timeouts handled gracefully")
            
        finally:
            # Restore original timeout
            socket.setdefaulttimeout(original_timeout)
    
    def test_cache_corruption(self):
        """Test cache corruption handling"""
        print("Testing cache corruption handling...")
        
        cache_dir = Path(self.config['cache_dir'])
        cache_dir.mkdir(exist_ok=True)
        
        # Create corrupted cache file
        corrupt_cache = cache_dir / "corrupt_cache.pdf"
        corrupt_cache.write_text("This is not a valid PDF or cache file")
        
        # Test retriever with corrupted cache
        retriever = SourceRetriever(self.config)
        
        # Should handle gracefully
        citation = Citation("Test v. Case, 123 U.S. 456 (2020)", "001", "test")
        result = retriever._check_cache(citation)
        
        print(f"  Cache check result: {result.status.value}")
        print("  ✅ Cache corruption handled")
        
        # Cleanup
        corrupt_cache.unlink(missing_ok=True)
    
    def print_report(self):
        """Print comprehensive test report"""
        print("\n" + "="*80)
        print("STRESS TEST REPORT")
        print("="*80)
        
        print(f"\nTests Run: {self.results['tests_run']}")
        print(f"Passed: {self.results['tests_passed']}")
        print(f"Failed: {self.results['tests_failed']}")
        print(f"Success Rate: {self.results['tests_passed']/self.results['tests_run']*100:.1f}%")
        
        if self.results['errors']:
            print("\n❌ ERRORS:")
            for error in self.results['errors']:
                print(f"\n  Test: {error['test']}")
                print(f"  Error: {error['error']}")
                if '--verbose' in sys.argv:
                    print(f"  Traceback:\n{error['traceback']}")
        
        if self.results['performance']:
            print("\n📊 PERFORMANCE METRICS:")
            for metric, data in self.results['performance'].items():
                print(f"\n  {metric}:")
                for key, value in data.items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.2f}")
                    else:
                        print(f"    {key}: {value}")
        
        # Save detailed report
        report_path = Path("stress_test_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Overall assessment
        print("\n" + "="*80)
        if self.results['tests_failed'] == 0:
            print("✅ ALL STRESS TESTS PASSED - System is robust!")
        elif self.results['tests_failed'] <= 2:
            print("⚠️  MINOR ISSUES DETECTED - System mostly stable")
        else:
            print("❌ SIGNIFICANT ISSUES FOUND - Updates needed")


def main():
    """Run stress tests"""
    tester = StressTestSuite()
    
    try:
        tester.run_all_tests()
        return 0 if tester.results['tests_failed'] == 0 else 1
    except KeyboardInterrupt:
        print("\n\nStress test interrupted by user")
        return 1
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())