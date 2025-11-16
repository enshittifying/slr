"""
Edge case handlers for robust citation processing
Handles malformed citations, corrupted PDFs, network failures, and other edge cases
"""
import logging
import re
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import PyMuPDF as fitz

logger = logging.getLogger(__name__)


class MalformedCitationHandler:
    """Handles malformed and edge case citations"""

    @staticmethod
    def clean_citation(citation: str) -> str:
        """
        Clean up common citation formatting issues

        Args:
            citation: Raw citation text

        Returns:
            Cleaned citation
        """
        if not citation or not citation.strip():
            return ""

        # Remove excessive whitespace
        cleaned = ' '.join(citation.split())

        # Fix common typos
        replacements = {
            '  ': ' ',
            ' ,': ',',
            ' .': '.',
            '..': '.',
            'v .': 'v.',
            'U. S.': 'U.S.',
            'F. 3d': 'F.3d',
            'F. 2d': 'F.2d',
        }

        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        return cleaned.strip()

    @staticmethod
    def extract_case_name(citation: str) -> Optional[str]:
        """
        Extract case name from malformed citation

        Args:
            citation: Citation text

        Returns:
            Case name or None
        """
        # Try to find "X v. Y" pattern
        patterns = [
            r'([A-Z][^,]+?)\s+v\.?\s+([A-Z][^,]+?)[,\s]',  # Standard
            r'([A-Z][^,]+?)\s+vs\.?\s+([A-Z][^,]+?)[,\s]',  # vs instead of v.
            r'([A-Z][^,]+?)\s+versus\s+([A-Z][^,]+?)[,\s]',  # versus
        ]

        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                party1 = match.group(1).strip()
                party2 = match.group(2).strip()
                return f"{party1} v. {party2}"

        return None

    @staticmethod
    def extract_year(citation: str) -> Optional[str]:
        """
        Extract year from citation

        Args:
            citation: Citation text

        Returns:
            Year or None
        """
        # Look for 4-digit year in parentheses or standalone
        year_patterns = [
            r'\((\d{4})\)',  # (2020)
            r'\b(\d{4})\b',  # 2020
        ]

        for pattern in year_patterns:
            match = re.search(pattern, citation)
            if match:
                year = match.group(1)
                # Validate year is reasonable (1800-2100)
                if 1800 <= int(year) <= 2100:
                    return year

        return None

    @staticmethod
    def validate_citation_structure(citation: str) -> Tuple[bool, List[str]]:
        """
        Validate basic citation structure and return issues

        Args:
            citation: Citation text

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        if not citation or len(citation) < 5:
            issues.append("Citation too short")
            return False, issues

        # Check for basic components
        has_case_name = bool(re.search(r'v\.', citation, re.IGNORECASE))
        has_reporter = bool(re.search(r'\d+\s+[A-Z][A-Za-z.]+\s+\d+', citation))
        has_year = bool(re.search(r'\d{4}', citation))

        if not has_case_name and not has_reporter:
            issues.append("Missing both case name and reporter")

        if not has_year:
            issues.append("Missing year")

        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s.,();\-\']', citation))
        if special_chars > 10:
            issues.append(f"Excessive special characters ({special_chars})")

        return len(issues) == 0, issues

    @staticmethod
    def attempt_repair(citation: str) -> Tuple[str, bool]:
        """
        Attempt to repair a malformed citation

        Args:
            citation: Malformed citation

        Returns:
            (repaired_citation, was_repaired)
        """
        original = citation
        repaired = MalformedCitationHandler.clean_citation(citation)

        # Try to fix common issues
        # Fix missing spaces after periods
        repaired = re.sub(r'\.([A-Za-z])', r'. \1', repaired)

        # Fix missing commas
        if ' v. ' in repaired and ',' not in repaired:
            # Add comma after case name
            repaired = re.sub(r'(v\.\s+[^,]+?)(\s+\d+)', r'\1,\2', repaired)

        was_repaired = repaired != original
        if was_repaired:
            logger.info(f"Repaired citation: '{original}' -> '{repaired}'")

        return repaired, was_repaired


class PDFValidator:
    """Validates and handles corrupted/invalid PDFs"""

    @staticmethod
    def validate_pdf(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a file is a valid PDF

        Args:
            file_path: Path to PDF file

        Returns:
            (is_valid, error_message)
        """
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return False, f"File not found: {file_path}"

        # Check file size
        if path.stat().st_size == 0:
            return False, "PDF file is empty"

        if path.stat().st_size < 100:  # Minimum PDF size
            return False, "PDF file too small (possibly corrupted)"

        # Check PDF header
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False, "Invalid PDF header (not a PDF file)"
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"

        # Try to open with PyMuPDF
        try:
            doc = fitz.open(file_path)

            # Check page count
            if len(doc) == 0:
                doc.close()
                return False, "PDF has no pages"

            # Check if encrypted
            if doc.is_encrypted:
                doc.close()
                return False, "PDF is encrypted/password protected"

            # Try to read first page
            try:
                page = doc[0]
                text = page.get_text()
                # PDF is valid
            except Exception as e:
                doc.close()
                return False, f"Cannot read PDF pages: {str(e)}"

            doc.close()
            return True, None

        except Exception as e:
            return False, f"PyMuPDF error: {str(e)}"

    @staticmethod
    def attempt_repair(file_path: str, output_path: str = None) -> Tuple[bool, Optional[str]]:
        """
        Attempt to repair a corrupted PDF

        Args:
            file_path: Path to corrupted PDF
            output_path: Where to save repaired PDF (defaults to file_path + ".repaired.pdf")

        Returns:
            (success, output_path_or_error)
        """
        if output_path is None:
            output_path = str(Path(file_path).with_suffix('.repaired.pdf'))

        try:
            # Try to open and re-save (PyMuPDF can often fix minor corruption)
            doc = fitz.open(file_path)

            # Create new document
            new_doc = fitz.open()

            # Copy pages
            for page_num in range(len(doc)):
                try:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                except Exception as e:
                    logger.warning(f"Skipping corrupted page {page_num}: {e}")
                    continue

            # Save repaired document
            new_doc.save(output_path, garbage=4, deflate=True, clean=True)
            new_doc.close()
            doc.close()

            # Validate repaired file
            is_valid, error = PDFValidator.validate_pdf(output_path)

            if is_valid:
                logger.info(f"Successfully repaired PDF: {output_path}")
                return True, output_path
            else:
                return False, f"Repair failed validation: {error}"

        except Exception as e:
            return False, f"Repair failed: {str(e)}"

    @staticmethod
    def extract_text_safe(file_path: str, max_pages: int = 10) -> Tuple[str, List[str]]:
        """
        Safely extract text from PDF, handling corrupted pages

        Args:
            file_path: Path to PDF
            max_pages: Maximum pages to extract

        Returns:
            (extracted_text, list_of_errors)
        """
        text_parts = []
        errors = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(min(len(doc), max_pages)):
                try:
                    page = doc[page_num]
                    text = page.get_text()
                    text_parts.append(text)
                except Exception as e:
                    errors.append(f"Page {page_num}: {str(e)}")
                    continue

            doc.close()

            return '\n'.join(text_parts), errors

        except Exception as e:
            errors.append(f"Document error: {str(e)}")
            return "", errors


class NetworkErrorHandler:
    """Handles network-related errors and edge cases"""

    @staticmethod
    def is_retryable_error(exception: Exception) -> bool:
        """
        Determine if an error should be retried

        Args:
            exception: Exception that occurred

        Returns:
            True if error is retryable
        """
        retryable_types = [
            'ConnectionError',
            'Timeout',
            'HTTPError',
            'APIError',
            'RateLimitError',
            'APIConnectionError',
            'ServiceUnavailable',
            'GatewayTimeout',
        ]

        exception_type = type(exception).__name__

        if exception_type in retryable_types:
            return True

        # Check error message for retryable indicators
        error_msg = str(exception).lower()
        retryable_messages = [
            'timeout',
            'connection',
            'rate limit',
            'service unavailable',
            'gateway',
            'temporary',
            '429',  # Too Many Requests
            '502',  # Bad Gateway
            '503',  # Service Unavailable
            '504',  # Gateway Timeout
        ]

        return any(msg in error_msg for msg in retryable_messages)

    @staticmethod
    def get_error_category(exception: Exception) -> str:
        """
        Categorize error for logging/reporting

        Args:
            exception: Exception

        Returns:
            Error category
        """
        exception_type = type(exception).__name__
        error_msg = str(exception).lower()

        if 'timeout' in error_msg or 'Timeout' in exception_type:
            return 'timeout'
        elif 'connection' in error_msg or 'Connection' in exception_type:
            return 'connection'
        elif 'rate limit' in error_msg or 'RateLimit' in exception_type:
            return 'rate_limit'
        elif 'authentication' in error_msg or 'auth' in error_msg:
            return 'authentication'
        elif 'permission' in error_msg:
            return 'permission'
        elif 'not found' in error_msg or '404' in error_msg:
            return 'not_found'
        else:
            return 'unknown'


class APIKeyValidator:
    """Validates API keys and provides helpful error messages"""

    @staticmethod
    def validate_openai_key(api_key: str) -> Tuple[bool, str]:
        """
        Validate OpenAI API key format

        Args:
            api_key: API key to validate

        Returns:
            (is_valid, message)
        """
        if not api_key:
            return False, "API key is empty"

        if not api_key.startswith('sk-'):
            return False, "OpenAI API key should start with 'sk-'"

        if len(api_key) < 40:
            return False, "OpenAI API key too short (minimum 40 characters)"

        # Basic format check
        if not re.match(r'^sk-[A-Za-z0-9\-_]+$', api_key):
            return False, "Invalid API key format"

        return True, "API key format valid"

    @staticmethod
    def validate_anthropic_key(api_key: str) -> Tuple[bool, str]:
        """
        Validate Anthropic API key format

        Args:
            api_key: API key to validate

        Returns:
            (is_valid, message)
        """
        if not api_key:
            return False, "API key is empty"

        if not api_key.startswith('sk-ant-'):
            return False, "Anthropic API key should start with 'sk-ant-'"

        if len(api_key) < 50:
            return False, "Anthropic API key too short"

        return True, "API key format valid"

    @staticmethod
    def validate_google_credentials(creds_path: str) -> Tuple[bool, str]:
        """
        Validate Google service account credentials file

        Args:
            creds_path: Path to credentials JSON

        Returns:
            (is_valid, message)
        """
        path = Path(creds_path)

        if not path.exists():
            return False, f"Credentials file not found: {creds_path}"

        if path.stat().st_size == 0:
            return False, "Credentials file is empty"

        try:
            import json
            with open(creds_path, 'r') as f:
                creds = json.load(f)

            required_fields = [
                'type',
                'project_id',
                'private_key_id',
                'private_key',
                'client_email',
                'client_id'
            ]

            missing = [field for field in required_fields if field not in creds]

            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"

            if creds.get('type') != 'service_account':
                return False, "Not a service account credentials file"

            return True, "Credentials file valid"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Error reading credentials: {str(e)}"
