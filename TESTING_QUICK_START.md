# Testing Quick Start Guide
## Getting Started with Test Implementation

**Last Updated:** 2025-11-16

This guide helps you quickly implement the testing infrastructure for the SLR Citation Processor.

---

## Prerequisites

Ensure you have the required testing packages installed:

```bash
cd /home/user/slr
pip install pytest pytest-cov pytest-mock pytest-qt pytest-xdist
```

---

## Quick Setup (5 minutes)

### 1. Verify Test Infrastructure

The following files have been created:

```bash
# Check that these files exist:
ls -la pytest.ini               # ✅ Created
ls -la .coveragerc              # ✅ Created
ls -la tests/conftest.py        # ✅ Created
```

### 2. Run Existing Tests

```bash
# Run all current tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov=SLRinator --cov=r2_pipeline

# Generate HTML coverage report
pytest tests/ --cov=app --cov=SLRinator --cov-report=html
open htmlcov/index.html  # View coverage report in browser
```

### 3. Verify Coverage Baseline

```bash
# Run coverage and save baseline
pytest tests/ --cov=app --cov=SLRinator --cov=r2_pipeline --cov-report=term

# Expected output (current state):
# Name                                    Stmts   Miss  Cover
# -----------------------------------------------------------
# app/core/sp_machine.py                    210    120    43%
# app/core/r1_machine.py                    326    195    40%
# app/core/r2_pipeline.py                   430    258    40%
# SLRinator/src/utils/error_handler.py      300    300     0%
# SLRinator/src/utils/cache_manager.py      350    350     0%
# ...
# -----------------------------------------------------------
# TOTAL                                   20000  12000    40%
```

---

## Your First Test (15 minutes)

Let's write your first real test for the cache manager:

### Step 1: Create Test File

```bash
mkdir -p tests/unit/test_utils
touch tests/unit/test_utils/__init__.py
```

### Step 2: Write the Test

Create `tests/unit/test_utils/test_cache_manager.py`:

```python
"""Tests for cache management"""
import pytest
from datetime import timedelta
from SLRinator.src.utils.cache_manager import CacheManager

class TestCacheManager:
    """Test cache manager functionality"""

    def test_cache_set_and_get(self, temp_cache_dir):
        """Test basic cache operations"""
        cache = CacheManager(cache_dir=str(temp_cache_dir), max_size_mb=10)

        # Store data
        cache.set('test_key', {'data': 'test_value'})

        # Retrieve data
        result = cache.get('test_key')

        # Assertions
        assert result == {'data': 'test_value'}
        assert cache.stats['hits'] == 1
        assert cache.stats['misses'] == 0

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss increments stats"""
        cache = CacheManager(cache_dir=str(temp_cache_dir))

        # Try to get non-existent key
        result = cache.get('nonexistent_key')

        # Assertions
        assert result is None
        assert cache.stats['misses'] == 1

    def test_cache_expiration(self, temp_cache_dir):
        """Test cache entries expire after TTL"""
        import time

        cache = CacheManager(cache_dir=str(temp_cache_dir))

        # Set with 1 second TTL
        cache.set('temp_key', 'temp_value', ttl=timedelta(seconds=1))

        # Should exist immediately
        assert cache.get('temp_key') == 'temp_value'

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        assert cache.get('temp_key') is None
```

### Step 3: Run Your Test

```bash
# Run just this test file
pytest tests/unit/test_utils/test_cache_manager.py -v

# Expected output:
# tests/unit/test_utils/test_cache_manager.py::TestCacheManager::test_cache_set_and_get PASSED
# tests/unit/test_utils/test_cache_manager.py::TestCacheManager::test_cache_miss PASSED
# tests/unit/test_utils/test_cache_manager.py::TestCacheManager::test_cache_expiration PASSED
```

### Step 4: Check Coverage

```bash
# Run with coverage
pytest tests/unit/test_utils/test_cache_manager.py --cov=SLRinator.src.utils.cache_manager --cov-report=term-missing

# Shows which lines are covered/missed
```

---

## Testing Patterns & Best Practices

### Pattern 1: Arrange-Act-Assert (AAA)

```python
def test_something(self):
    """Test description"""
    # ARRANGE - Set up test data
    cache = CacheManager(cache_dir="/tmp/test")
    test_data = {'key': 'value'}

    # ACT - Perform the action
    cache.set('key1', test_data)
    result = cache.get('key1')

    # ASSERT - Verify the result
    assert result == test_data
```

### Pattern 2: Fixtures for Reusable Test Data

```python
@pytest.fixture
def sample_cache(temp_cache_dir):
    """Pre-populated cache for testing"""
    cache = CacheManager(cache_dir=str(temp_cache_dir))
    cache.set('key1', 'value1')
    cache.set('key2', 'value2')
    return cache

def test_with_fixture(sample_cache):
    """Use the fixture"""
    assert sample_cache.get('key1') == 'value1'
```

### Pattern 3: Parametrized Tests

```python
@pytest.mark.parametrize("input_val,expected", [
    ('valid', True),
    ('invalid', False),
    ('', False),
    (None, False),
])
def test_validation(input_val, expected):
    """Test multiple inputs efficiently"""
    result = validate(input_val)
    assert result == expected
```

### Pattern 4: Exception Testing

```python
def test_raises_exception():
    """Test that exception is raised"""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_input)
```

### Pattern 5: Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock(mock_sheets_client):
    """Use mocked Google Sheets client"""
    # The fixture provides a mock
    mock_sheets_client.get_all_articles.return_value = [...]

    # Your code uses the mock
    processor = ArticleProcessor(mock_sheets_client)
    result = processor.process()

    # Verify mock was called
    assert mock_sheets_client.get_all_articles.called
```

---

## Common Testing Scenarios

### Testing Async/Background Operations

```python
import time

def test_background_operation():
    """Test operation that runs in background"""
    worker = BackgroundWorker()

    # Start operation
    worker.start()

    # Wait briefly
    time.sleep(0.5)

    # Check progress
    assert worker.is_running()

    # Wait for completion
    worker.wait()
    assert worker.is_complete()
```

### Testing File Operations

```python
def test_file_processing(temp_dir):
    """Test file is created correctly"""
    processor = FileProcessor(output_dir=str(temp_dir))

    # Process file
    output_path = processor.process('input.txt')

    # Verify file exists
    assert output_path.exists()

    # Verify content
    content = output_path.read_text()
    assert 'expected content' in content
```

### Testing Error Handling

```python
def test_error_recovery():
    """Test system recovers from errors"""
    processor = DataProcessor()

    # Simulate error condition
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Network error")

        # Should handle gracefully
        result = processor.fetch_data()

        # Should return cached or default data
        assert result is not None
```

---

## Test Organization

Organize tests to mirror your source code structure:

```
/home/user/slr/
├── SLRinator/src/
│   ├── utils/
│   │   ├── cache_manager.py
│   │   └── error_handler.py
│   └── core/
│       └── pdf_retriever.py
│
└── tests/
    └── unit/
        ├── test_utils/
        │   ├── test_cache_manager.py      # ← Tests for cache_manager.py
        │   └── test_error_handler.py      # ← Tests for error_handler.py
        └── test_core/
            └── test_pdf_retriever.py      # ← Tests for pdf_retriever.py
```

---

## Running Tests Efficiently

### During Development (Fast Feedback)

```bash
# Run only fast tests
pytest -m fast

# Run tests for specific module
pytest tests/unit/test_utils/test_cache_manager.py

# Run tests matching a pattern
pytest -k "cache"

# Stop at first failure
pytest --maxfail=1

# Show print statements
pytest -s
```

### Before Commit (Comprehensive)

```bash
# Run all unit tests with coverage
pytest tests/unit/ --cov=app --cov=SLRinator

# Run linting and formatting
black app/ SLRinator/
flake8 app/ SLRinator/
```

### Before Release (Full Suite)

```bash
# Run everything including slow tests
pytest tests/ --cov=app --cov=SLRinator --cov=r2_pipeline --cov-report=html

# Run verification scripts
python verify_modules.py
python verify_integration.py
```

---

## Next Steps

### Week 1: Foundation Tests

Focus on utility modules (highest ROI):

```bash
# Priority order:
1. tests/unit/test_utils/test_error_handler.py      # 15 tests
2. tests/unit/test_utils/test_cache_manager.py      # 12 tests
3. tests/unit/test_utils/test_retry_handler.py      # 10 tests
4. tests/unit/test_utils/test_connection_pool.py    # 8 tests
5. tests/unit/test_utils/test_performance_monitor.py # 6 tests

# Goal: 51 new tests, ~20% coverage increase
```

### Week 2: Data Layer Tests

Test API clients:

```bash
# Priority order:
1. tests/unit/test_data/test_sheets_client.py   # 15 tests
2. tests/unit/test_data/test_drive_client.py    # 10 tests
3. tests/unit/test_data/test_llm_client.py      # 16 tests

# Goal: 41 new tests, data layer at 70%+ coverage
```

### Week 3-4: Core & Integration

Test business logic and integration:

```bash
1. Core module tests                            # 57 tests
2. Integration tests                            # 34 tests

# Goal: Core functionality fully tested
```

---

## Useful Commands Reference

### Test Execution

```bash
# Basic
pytest                                  # Run all tests
pytest tests/unit/                      # Run unit tests only
pytest tests/integration/               # Run integration tests only
pytest -v                              # Verbose output
pytest -s                              # Show print statements
pytest --tb=short                      # Short traceback format

# Filtering
pytest -k "cache"                      # Run tests matching "cache"
pytest -m "not slow"                   # Skip slow tests
pytest --maxfail=3                     # Stop after 3 failures
pytest --lf                            # Run last failed tests
pytest --ff                            # Run failed first, then others

# Coverage
pytest --cov=app                       # Coverage for app/
pytest --cov-report=html               # HTML coverage report
pytest --cov-report=term-missing       # Show missing lines
pytest --cov-fail-under=80             # Fail if coverage < 80%

# Parallel Execution
pytest -n 4                            # Run with 4 workers
pytest -n auto                         # Auto-detect CPU count

# Other
pytest --collect-only                  # List all tests without running
pytest --markers                       # List all markers
pytest --fixtures                      # List all fixtures
```

### Coverage Commands

```bash
# Generate reports
coverage run -m pytest tests/
coverage report                        # Terminal report
coverage html                          # HTML report
coverage xml                           # XML report (for CI)

# Open HTML report
open htmlcov/index.html               # Mac
xdg-open htmlcov/index.html           # Linux
start htmlcov/index.html              # Windows
```

---

## Troubleshooting

### "ModuleNotFoundError"

```bash
# Add paths to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/user/slr:/home/user/slr/app:/home/user/slr/SLRinator"

# Or install in development mode
pip install -e .
```

### "No tests found"

```bash
# Check test discovery patterns in pytest.ini
# Ensure files/functions start with "test_"

# List what pytest will collect
pytest --collect-only
```

### "Fixture not found"

```bash
# Ensure conftest.py is in the right location
# Fixtures should be in tests/conftest.py or local conftest.py

# List available fixtures
pytest --fixtures
```

### "Import errors in tests"

```bash
# Check imports are correct
# Use absolute imports from project root

# Good:
from app.core.sp_machine import SPMachine

# Avoid relative imports in tests
```

---

## Resources

### Documentation
- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)

### Example Test Files
- `/home/user/slr/tests/unit/test_utils/test_error_handler_EXAMPLE.py`
- `/home/user/slr/tests/test_core_pipeline.py`
- `/home/user/slr/tests/test_integration.py`

### Your Project Files
- `/home/user/slr/QA_TESTING_ANALYSIS.md` - Comprehensive analysis
- `/home/user/slr/pytest.ini` - Test configuration
- `/home/user/slr/.coveragerc` - Coverage configuration
- `/home/user/slr/tests/conftest.py` - Global fixtures

---

## Success Checklist

After your first week of testing, you should have:

- [ ] pytest.ini configured and working
- [ ] conftest.py with reusable fixtures
- [ ] 50+ utility tests written
- [ ] Coverage reports generated
- [ ] Coverage increased from 40% to 55%+
- [ ] All tests passing consistently
- [ ] Pre-commit hook running tests

---

**Happy Testing! 🧪**

Remember:
- Write tests for new code first (TDD when possible)
- Keep tests simple and focused
- Use descriptive test names
- Mock external dependencies
- Aim for 80%+ coverage on critical paths

For questions or issues, refer to:
- QA_TESTING_ANALYSIS.md for comprehensive strategy
- tests/conftest.py for available fixtures
- test_error_handler_EXAMPLE.py for test patterns
