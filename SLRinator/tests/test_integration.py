#!/usr/bin/env python3
"""
Integration Test for Enhanced SLRinator System
Tests all components working together with improvements
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stage1.citation_parser import CitationParser
from utils import (
    PerformanceMonitor, 
    ErrorHandler, 
    CacheManager,
    APIClient,
    BatchProcessor,
    InputValidator,
    ValidationError
)


def test_enhanced_citation_parsing():
    """Test citation parsing with error handling and performance monitoring"""
    print("\n" + "="*60)
    print("Testing Enhanced Citation Parsing")
    print("="*60)
    
    # Initialize components
    parser = CitationParser()
    monitor = PerformanceMonitor()
    error_handler = ErrorHandler()
    validator = InputValidator()
    
    # Test citations including edge cases
    test_citations = [
        # Valid citations
        ("Smith v. Jones, 123 U.S. 456 (2020)", "001", "Smith"),
        ("42 U.S.C. § 1983 (2018)", "002", "USC"),
        
        # Edge cases
        ("", "003", "Empty"),  # Empty citation
        ("DROP TABLE citations;", "004", "SQL"),  # SQL injection attempt
        ("<script>alert('xss')</script>", "005", "XSS"),  # XSS attempt
        ("A" * 10000, "006", "Long"),  # Very long citation
        ("Müller v. Société Générale, 123 F.3d 456 (2d Cir. 2020)", "007", "Unicode"),
        (None, "008", "None"),  # None input
    ]
    
    results = []
    
    for raw_text, source_id, short_name in test_citations:
        op_id = monitor.start_operation("parse_citation", {"source_id": source_id})
        
        try:
            # Validate input
            if raw_text is not None:
                validated_text = validator.validate_citation(raw_text)
            else:
                validated_text = ""
            
            # Parse citation
            citation = parser.parse_citation(validated_text, source_id, short_name)
            results.append({
                'source_id': source_id,
                'success': True,
                'type': citation.type.value if citation else 'unknown'
            })
            
            monitor.end_operation(op_id, success=True)
            print(f"✅ Parsed {source_id}: {citation.type.value if citation else 'failed'}")
            
        except ValidationError as e:
            error_context = error_handler.handle_error(e, f"parse_{source_id}")
            results.append({
                'source_id': source_id,
                'success': False,
                'error': str(e)
            })
            monitor.end_operation(op_id, success=False, error=str(e))
            print(f"⚠️  Validation failed for {source_id}: {e}")
            
        except Exception as e:
            error_context = error_handler.handle_error(e, f"parse_{source_id}")
            results.append({
                'source_id': source_id,
                'success': False,
                'error': str(e)
            })
            monitor.end_operation(op_id, success=False, error=str(e))
            print(f"❌ Failed {source_id}: {e}")
    
    # Print statistics
    stats = monitor.get_statistics()
    print(f"\nPerformance Stats:")
    print(f"  Total: {stats['total_operations']}")
    print(f"  Success: {stats['successful_operations']}")
    print(f"  Failed: {stats['failed_operations']}")
    print(f"  Avg Time: {stats['average_duration']:.3f}s")
    
    error_summary = error_handler.get_error_summary()
    if error_summary['total_errors'] > 0:
        print(f"\nError Summary:")
        print(f"  Total Errors: {error_summary['total_errors']}")
        print(f"  Recovery Attempts: {error_summary['recovery_stats']['attempted']}")
    
    return len([r for r in results if r['success']]) >= 5


def test_caching_system():
    """Test enhanced caching with validation"""
    print("\n" + "="*60)
    print("Testing Enhanced Caching System")
    print("="*60)
    
    cache = CacheManager(cache_dir="./test_cache", max_size_mb=10)
    
    # Test basic caching
    test_data = {
        'key1': {'data': 'test', 'size': 100},
        'key2': {'data': [1, 2, 3], 'array': True},
        'key3': {'large': 'x' * 1000},
    }
    
    # Store items
    for key, value in test_data.items():
        success = cache.set(key, value, ttl=timedelta(minutes=5))
        print(f"  Stored {key}: {'✅' if success else '❌'}")
    
    # Retrieve items
    hits = 0
    for key in test_data.keys():
        value = cache.get(key)
        if value == test_data[key]:
            hits += 1
            print(f"  Retrieved {key}: ✅")
        else:
            print(f"  Retrieved {key}: ❌")
    
    # Test cache statistics
    stats = cache.get_statistics()
    print(f"\nCache Stats:")
    print(f"  Entries: {stats['total_entries']}")
    print(f"  Size: {stats['total_size_mb']:.2f} MB")
    print(f"  Hit Rate: {stats['hit_rate']:.1%}")
    
    # Test expiration
    expired_key = 'expired'
    cache.set(expired_key, 'data', ttl=timedelta(seconds=1))
    time.sleep(2)
    expired_value = cache.get(expired_key)
    print(f"  Expiration test: {'✅' if expired_value is None else '❌'}")
    
    # Cleanup
    cache.clear()
    
    return hits == len(test_data)


def test_batch_processing():
    """Test batch processing with resource management"""
    print("\n" + "="*60)
    print("Testing Batch Processing")
    print("="*60)
    
    processor = BatchProcessor(batch_size=50, max_workers=4)
    
    # Create test items
    items = [f"Citation {i}" for i in range(200)]
    
    # Process function
    def process_item(item):
        # Simulate processing
        time.sleep(0.01)
        return f"Processed: {item}"
    
    print(f"  Processing {len(items)} items in batches...")
    start_time = time.time()
    
    results = processor.process_batch(items, process_item, "Test Processing")
    
    elapsed = time.time() - start_time
    rate = len(items) / elapsed
    
    print(f"  Completed in {elapsed:.2f}s")
    print(f"  Rate: {rate:.0f} items/second")
    print(f"  Results: {len(results)} items processed")
    
    # Check statistics
    stats = processor.monitor.get_statistics()
    print(f"\nBatch Stats:")
    print(f"  Total Operations: {stats['total_operations']}")
    print(f"  Success Rate: {stats['successful_operations']}/{stats['total_operations']}")
    
    return len(results) == len(items)


def test_api_connection_pooling():
    """Test API connection pooling and rate limiting"""
    print("\n" + "="*60)
    print("Testing API Connection Pooling")
    print("="*60)
    
    # Note: This test doesn't make real API calls to avoid requiring API keys
    client = APIClient()
    
    print("  Connection pools registered:")
    for endpoint in client.pool.endpoints.keys():
        print(f"    - {endpoint}")
    
    # Test rate limiting
    print("\n  Testing rate limiting...")
    
    # Simulate rapid requests (would be rate limited)
    from utils.connection_pool import RateLimiter, RateLimitConfig
    
    config = RateLimitConfig(
        calls_per_second=2,
        calls_per_minute=10,
        burst_size=3
    )
    limiter = RateLimiter(config)
    
    acquired = []
    start = time.time()
    
    # Try to acquire 5 tokens rapidly
    for i in range(5):
        if limiter.acquire(timeout=0.1):
            acquired.append(time.time() - start)
            print(f"    Request {i+1}: Acquired at {acquired[-1]:.2f}s")
        else:
            print(f"    Request {i+1}: Rate limited")
    
    # Should get burst_size immediately, then rate limited
    print(f"  Acquired {len(acquired)} out of 5 requests")
    
    client.close()
    
    return len(acquired) >= 3


def test_error_recovery():
    """Test error recovery mechanisms"""
    print("\n" + "="*60)
    print("Testing Error Recovery")
    print("="*60)
    
    handler = ErrorHandler(max_retries=3)
    
    # Test retry mechanism
    attempt_count = 0
    
    def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Network error")
        return "Success"
    
    try:
        # This should fail twice then succeed
        context = handler.handle_error(
            ConnectionError("Initial error"),
            "flaky_operation"
        )
        
        result = handler.recover(
            context,
            retry_func=flaky_operation
        )
        
        print(f"  Retry test: ✅ (succeeded after {attempt_count} attempts)")
    except:
        print(f"  Retry test: ❌")
    
    # Test fallback mechanism
    def primary_operation():
        raise ValueError("Primary failed")
    
    def fallback_operation():
        return "Fallback success"
    
    try:
        context = handler.handle_error(
            ValueError("Test error"),
            "test_operation"
        )
        
        result = handler.recover(
            context,
            fallback_func=fallback_operation
        )
        
        print(f"  Fallback test: {'✅' if result == 'Fallback success' else '❌'}")
    except:
        print(f"  Fallback test: ❌")
    
    # Generate error report
    handler.save_error_report("test_error_report.json")
    print(f"  Error report saved: ✅")
    
    return attempt_count == 3


def test_input_validation():
    """Test input validation and sanitization"""
    print("\n" + "="*60)
    print("Testing Input Validation")
    print("="*60)
    
    validator = InputValidator()
    
    test_cases = [
        # Citations
        ("Normal citation", "Smith v. Jones, 123 U.S. 456 (2020)", True),
        ("SQL injection", "'; DROP TABLE users; --", True),  # Should be sanitized
        ("XSS attempt", "<script>alert('xss')</script>", True),  # Should be sanitized
        
        # Filenames
        ("Normal filename", "document.pdf", True),
        ("Path traversal", "../../../etc/passwd", True),  # Should be sanitized
        ("Reserved name", "CON.pdf", True),  # Should be sanitized
        
        # URLs
        ("Valid URL", "https://example.com/page", True),
        ("Invalid URL", "not-a-url", False),
        ("Javascript", "javascript:alert(1)", False),
    ]
    
    passed = 0
    
    for test_name, input_val, should_pass in test_cases:
        try:
            if "citation" in test_name.lower() or "sql" in test_name.lower() or "xss" in test_name.lower():
                result = validator.validate_citation(input_val)
            elif "filename" in test_name.lower() or "path" in test_name.lower() or "reserved" in test_name.lower():
                result = validator.validate_filename(input_val)
            else:
                result = validator.validate_url(input_val)
            
            if should_pass:
                passed += 1
                print(f"  {test_name}: ✅ -> {result[:50]}")
            else:
                print(f"  {test_name}: ❌ (should have failed)")
        
        except ValidationError as e:
            if not should_pass:
                passed += 1
                print(f"  {test_name}: ✅ (correctly rejected)")
            else:
                print(f"  {test_name}: ❌ (incorrectly rejected)")
    
    print(f"\nValidation: {passed}/{len(test_cases)} tests passed")
    
    return passed >= len(test_cases) - 1


def main():
    """Run all integration tests"""
    print("="*80)
    print("SLRINATOR ENHANCED INTEGRATION TEST")
    print("="*80)
    
    tests = [
        ("Enhanced Citation Parsing", test_enhanced_citation_parsing),
        ("Caching System", test_caching_system),
        ("Batch Processing", test_batch_processing),
        ("API Connection Pooling", test_api_connection_pooling),
        ("Error Recovery", test_error_recovery),
        ("Input Validation", test_input_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n{test_name}: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The enhanced SLRinator system is ready for production use.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())