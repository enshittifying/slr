"""
Global pytest configuration and fixtures for SLR Citation Processor tests

This module provides reusable test fixtures and configuration for all tests.
"""

import pytest
import tempfile
import shutil
import json
import fitz  # PyMuPDF
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from datetime import datetime


# ============================================================================
# Session-scoped fixtures (created once per test session)
# ============================================================================

@pytest.fixture(scope='session')
def qapp():
    """
    Create QApplication instance for GUI testing

    This fixture is session-scoped so the QApplication is only created once
    for all GUI tests in the session.
    """
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    except ImportError:
        pytest.skip("PyQt6 not installed, skipping GUI tests")


# ============================================================================
# Function-scoped fixtures (created fresh for each test)
# ============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """
    Provide a temporary directory that is cleaned up after the test

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path: Path to temporary directory
    """
    yield tmp_path
    # Cleanup is automatic with tmp_path


@pytest.fixture
def temp_cache_dir(tmp_path):
    """
    Provide a temporary cache directory

    Returns:
        Path: Path to cache directory
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    yield cache_dir


@pytest.fixture
def temp_logs_dir(tmp_path):
    """
    Provide a temporary logs directory

    Returns:
        Path: Path to logs directory
    """
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    yield logs_dir


# ============================================================================
# Mock API clients
# ============================================================================

@pytest.fixture
def mock_sheets_client():
    """
    Mock Google Sheets client with realistic data

    Returns:
        Mock: Mocked SheetsClient instance
    """
    client = Mock()

    # Mock get_all_articles
    client.get_all_articles.return_value = [
        {
            'article_id': 'test-001',
            'volume_issue': '78.6',
            'author': 'John Doe',
            'title': 'Test Article on Patent Law',
            'stage': 'not_started',
            'sources_total': 10,
            'sources_completed': 0,
            'last_updated': datetime.now().isoformat()
        },
        {
            'article_id': 'test-002',
            'volume_issue': '78.6',
            'author': 'Jane Smith',
            'title': 'Another Legal Article',
            'stage': 'sp_complete',
            'sources_total': 5,
            'sources_completed': 5,
            'last_updated': datetime.now().isoformat()
        }
    ]

    # Mock get_sources_for_article
    client.get_sources_for_article.return_value = [
        {
            'source_id': f'SP-{i:03d}',
            'article_id': 'test-001',
            'footnote_num': str(i),
            'citation': f'Test Citation {i}, 123 U.S. {100+i} (2020)',
            'type': 'case',
            'status': 'pending',
            'drive_link': '',
            'r1_status': '',
            'r1_drive_link': ''
        }
        for i in range(1, 11)
    ]

    # Mock update methods
    client.update_source_status.return_value = True
    client.update_r1_status.return_value = True
    client.update_article_stage.return_value = True

    return client


@pytest.fixture
def mock_drive_client():
    """
    Mock Google Drive client

    Returns:
        Mock: Mocked DriveClient instance
    """
    client = Mock()

    # Mock upload methods
    client.upload_file.return_value = 'file-123-abc'
    client.upload_source_pdf.return_value = 'source-file-456'
    client.upload_r1_pdf.return_value = 'r1-file-789'

    # Mock download methods
    client.download_file.return_value = '/tmp/downloaded_file.pdf'

    # Mock utility methods
    client.get_file_link.return_value = 'https://drive.google.com/file/d/file-123-abc'
    client.create_folder.return_value = 'folder-123'
    client.list_files.return_value = []

    return client


@pytest.fixture
def mock_llm_client():
    """
    Mock LLM client (OpenAI/Anthropic)

    Returns:
        Mock: Mocked LLM client instance
    """
    client = Mock()

    # Mock format checking
    client.check_format.return_value = {
        'issues': [],
        'suggestion': '',
        'confidence': 95,
        'is_valid': True
    }

    # Mock support checking
    client.check_support.return_value = {
        'supported': True,
        'confidence': 90,
        'explanation': 'The source adequately supports the proposition cited.',
        'requires_review': False
    }

    return client


# ============================================================================
# Sample test data
# ============================================================================

@pytest.fixture
def sample_citations():
    """
    Sample citation data for testing

    Returns:
        Dict[str, str]: Dictionary of citation types and examples
    """
    return {
        'valid_case': 'Alice Corp. v. CLS Bank International, 573 U.S. 208 (2014)',
        'valid_statute': '35 U.S.C. § 101 (2018)',
        'valid_article': 'Mark A. Lemley, Software Patents, 2013 Wis. L. Rev. 905',
        'valid_book': 'Donald S. Chisum, Chisum on Patents § 1.01 (2020)',
        'malformed': 'Bad Citation;;;',
        'empty': '',
        'unicode': 'Müller v. Société Générale, 123 F.3d 456 (2d Cir. 2020)',
        'sql_injection': "'; DROP TABLE citations; --",
        'xss': '<script>alert("xss")</script>',
        'path_traversal': '../../../etc/passwd',
        'very_long': 'A' * 10000,
    }


@pytest.fixture
def sample_article_data():
    """
    Sample article data with footnotes

    Returns:
        Dict[str, Any]: Article metadata and footnotes
    """
    return {
        'article_id': 'test-001',
        'title': 'Patent Eligibility After Alice',
        'author': 'John Doe',
        'volume_issue': '78.6',
        'footnotes': [
            {
                'number': 1,
                'text': 'See Alice Corp. v. CLS Bank Int\'l, 573 U.S. 208, 215 (2014) (holding that abstract ideas are not patentable).',
                'citation': 'Alice Corp. v. CLS Bank Int\'l, 573 U.S. 208 (2014)',
                'page': '215',
                'quote': 'abstract ideas are not patentable'
            },
            {
                'number': 2,
                'text': 'See 35 U.S.C. § 101 (2018).',
                'citation': '35 U.S.C. § 101 (2018)',
                'page': None,
                'quote': None
            },
            {
                'number': 3,
                'text': 'Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905, 910.',
                'citation': 'Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905',
                'page': '910',
                'quote': None
            }
        ]
    }


@pytest.fixture
def sample_pdf(temp_cache_dir):
    """
    Create a sample PDF file for testing

    Args:
        temp_cache_dir: Temporary cache directory fixture

    Returns:
        Path: Path to created PDF file
    """
    doc = fitz.open()

    # Add a few pages with sample content
    for i in range(3):
        page = doc.new_page()
        page.insert_text(
            (72, 72 + i*100),
            f"This is page {i+1} of a test PDF document.\n"
            f"Alice Corp. v. CLS Bank International\n"
            f"573 U.S. 208 (2014)\n"
            f"Some sample legal text for testing."
        )

    pdf_path = temp_cache_dir / "sample_test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    return pdf_path


@pytest.fixture
def sample_corrupted_pdf(temp_cache_dir):
    """
    Create a corrupted PDF file for testing error handling

    Args:
        temp_cache_dir: Temporary cache directory fixture

    Returns:
        Path: Path to corrupted PDF file
    """
    pdf_path = temp_cache_dir / "corrupted.pdf"
    pdf_path.write_bytes(b"This is not a valid PDF file!")
    return pdf_path


@pytest.fixture
def sample_config():
    """
    Sample configuration for testing

    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    return {
        'google': {
            'spreadsheet_id': 'test-spreadsheet-123',
            'drive_folder_id': 'test-folder-456',
            'credentials_path': '/tmp/test-credentials.json'
        },
        'llm': {
            'provider': 'openai',
            'model': 'gpt-4o-mini',
            'api_key': 'test-api-key-789',
            'max_tokens': 1000,
            'temperature': 0.3
        },
        'paths': {
            'cache_dir': '/tmp/test-cache',
            'logs_dir': '/tmp/test-logs',
            'output_dir': '/tmp/test-output'
        },
        'processing': {
            'max_retries': 3,
            'timeout_seconds': 30,
            'batch_size': 10
        }
    }


# ============================================================================
# Mock credentials
# ============================================================================

@pytest.fixture
def mock_google_credentials(temp_dir):
    """
    Create mock Google service account credentials file

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Path to credentials JSON file
    """
    creds_data = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    creds_file = temp_dir / "test_credentials.json"
    creds_file.write_text(json.dumps(creds_data, indent=2))

    return creds_file


# ============================================================================
# Utility fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances between tests

    This ensures test isolation by clearing any singleton state.
    """
    # Add any singleton reset logic here
    yield
    # Cleanup code here


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing logging calls

    Returns:
        Mock: Mocked logger instance
    """
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


# ============================================================================
# Performance testing fixtures
# ============================================================================

@pytest.fixture
def performance_monitor():
    """
    Simple performance monitoring for tests

    Usage:
        with performance_monitor() as timer:
            # code to measure
            pass
        assert timer.elapsed_ms < 1000  # Should take less than 1 second
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def timer():
        class Timer:
            def __init__(self):
                self.start = time.time()
                self.elapsed_ms = 0

        t = Timer()
        yield t
        t.elapsed_ms = (time.time() - t.start) * 1000

    return timer


# ============================================================================
# Test markers and configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (> 1s execution)"
    )
    config.addinivalue_line(
        "markers", "fast: marks tests as fast (< 100ms execution)"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "gui: GUI tests requiring display"
    )
    config.addinivalue_line(
        "markers", "network: tests requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically
    """
    for item in items:
        # Auto-mark GUI tests
        if "gui" in str(item.fspath):
            item.add_marker(pytest.mark.gui)

        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Auto-mark E2E tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
