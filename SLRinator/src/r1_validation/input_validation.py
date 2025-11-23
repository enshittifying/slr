"""
Input Validation Framework for R1 Validation
Provides comprehensive input validation and sanitization
"""
import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity."""
    ERROR = "error"  # Invalid input, cannot proceed
    WARNING = "warning"  # Potentially problematic input
    INFO = "info"  # Informational message


@dataclass
class ValidationError:
    """Input validation error."""
    field: str
    message: str
    severity: ValidationSeverity
    current_value: Any = None
    suggested_value: Any = None


class ValidationResult:
    """Result of input validation."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []

    def add_error(self, field: str, message: str, current: Any = None, suggested: Any = None):
        """Add validation error."""
        self.errors.append(ValidationError(
            field=field,
            message=message,
            severity=ValidationSeverity.ERROR,
            current_value=current,
            suggested_value=suggested
        ))

    def add_warning(self, field: str, message: str, current: Any = None, suggested: Any = None):
        """Add validation warning."""
        self.warnings.append(ValidationError(
            field=field,
            message=message,
            severity=ValidationSeverity.WARNING,
            current_value=current,
            suggested_value=suggested
        ))

    def add_info(self, field: str, message: str):
        """Add informational message."""
        self.info.append(ValidationError(
            field=field,
            message=message,
            severity=ValidationSeverity.INFO
        ))

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0

    def get_summary(self) -> str:
        """Get validation summary."""
        if self.is_valid and not self.has_warnings:
            return "Validation passed"

        lines = []
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  - {err.field}: {err.message}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                lines.append(f"  - {warn.field}: {warn.message}")

        return "\n".join(lines)


class InputValidator:
    """
    Comprehensive input validator for R1 system.
    """

    @staticmethod
    def validate_document_path(path: Union[str, Path]) -> ValidationResult:
        """
        Validate document path.

        Args:
            path: Path to document

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not path:
            result.add_error("document_path", "Document path is required")
            return result

        path = Path(path)

        # Check existence
        if not path.exists():
            result.add_error("document_path", f"File does not exist: {path}")
            return result

        # Check file extension
        valid_extensions = [".docx", ".doc"]
        if path.suffix.lower() not in valid_extensions:
            result.add_error(
                "document_path",
                f"Invalid file type: {path.suffix}. Expected: {', '.join(valid_extensions)}",
                current=path.suffix,
                suggested=".docx"
            )

        # Check file size (warn if > 50MB)
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            result.add_warning(
                "document_path",
                f"Large file size: {file_size_mb:.1f} MB. Processing may be slow."
            )

        # Check read permissions
        if not path.is_file():
            result.add_error("document_path", f"Path is not a file: {path}")
        elif not path.stat().st_mode & 0o400:  # Check read permission
            result.add_error("document_path", f"No read permission for file: {path}")

        return result

    @staticmethod
    def validate_footnote_range(footnote_range: str, max_footnotes: int = 1000) -> ValidationResult:
        """
        Validate footnote range specification.

        Args:
            footnote_range: Footnote range (e.g., "1-50", "1-50,100-150")
            max_footnotes: Maximum reasonable footnote number

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not footnote_range:
            # Empty means all footnotes - valid
            return result

        # Parse ranges
        ranges = []
        for part in footnote_range.split(','):
            part = part.strip()

            if '-' in part:
                # Range format: "1-50"
                try:
                    start, end = part.split('-')
                    start_num = int(start.strip())
                    end_num = int(end.strip())

                    if start_num < 1:
                        result.add_error("footnote_range", f"Invalid start: {start_num}. Must be >= 1")
                    if end_num < start_num:
                        result.add_error("footnote_range", f"Invalid range: {start_num}-{end_num}. End must be >= start")
                    if end_num > max_footnotes:
                        result.add_warning("footnote_range", f"Large footnote number: {end_num}")

                    ranges.append((start_num, end_num))

                except ValueError:
                    result.add_error("footnote_range", f"Invalid range format: {part}. Expected: N-M")

            else:
                # Single number
                try:
                    num = int(part)
                    if num < 1:
                        result.add_error("footnote_range", f"Invalid footnote number: {num}. Must be >= 1")
                    if num > max_footnotes:
                        result.add_warning("footnote_range", f"Large footnote number: {num}")

                    ranges.append((num, num))

                except ValueError:
                    result.add_error("footnote_range", f"Invalid number: {part}")

        # Check for overlapping ranges
        if len(ranges) > 1:
            sorted_ranges = sorted(ranges)
            for i in range(len(sorted_ranges) - 1):
                if sorted_ranges[i][1] >= sorted_ranges[i + 1][0]:
                    result.add_warning(
                        "footnote_range",
                        f"Overlapping ranges: {sorted_ranges[i]} and {sorted_ranges[i + 1]}"
                    )

        return result

    @staticmethod
    def validate_citation_text(citation_text: str, max_length: int = 5000) -> ValidationResult:
        """
        Validate citation text.

        Args:
            citation_text: Citation text
            max_length: Maximum citation length

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not citation_text or not citation_text.strip():
            result.add_error("citation_text", "Citation text is empty")
            return result

        citation_text = citation_text.strip()

        # Check length
        if len(citation_text) > max_length:
            result.add_error(
                "citation_text",
                f"Citation too long: {len(citation_text)} chars. Max: {max_length}"
            )

        # Check for minimum length (very short citations are suspicious)
        if len(citation_text) < 10:
            result.add_warning(
                "citation_text",
                f"Very short citation: {len(citation_text)} chars"
            )

        # Check for common issues
        if citation_text.count('(') != citation_text.count(')'):
            result.add_warning("citation_text", "Unmatched parentheses")

        if citation_text.count('[') != citation_text.count(']'):
            result.add_warning("citation_text", "Unmatched brackets")

        # Check for control characters
        if re.search(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', citation_text):
            result.add_warning("citation_text", "Contains control characters")

        return result

    @staticmethod
    def validate_api_key(api_key: str) -> ValidationResult:
        """
        Validate OpenAI API key format.

        Args:
            api_key: API key

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not api_key or not api_key.strip():
            result.add_error("api_key", "API key is empty")
            return result

        api_key = api_key.strip()

        # Check format (OpenAI keys start with "sk-")
        if not api_key.startswith("sk-"):
            result.add_error(
                "api_key",
                "Invalid API key format. OpenAI keys start with 'sk-'",
                current=api_key[:10] + "..."
            )

        # Check length (OpenAI keys are ~51 characters)
        if len(api_key) < 40:
            result.add_error("api_key", f"API key too short: {len(api_key)} chars")

        # Check for placeholder values
        placeholder_values = ["your-api-key-here", "sk-your-key-here", "INSERT_KEY_HERE"]
        if api_key in placeholder_values:
            result.add_error("api_key", "API key is a placeholder. Replace with real key.")

        return result

    @staticmethod
    def validate_output_directory(output_dir: Union[str, Path]) -> ValidationResult:
        """
        Validate output directory.

        Args:
            output_dir: Output directory path

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        if not output_dir:
            result.add_error("output_dir", "Output directory path is required")
            return result

        output_dir = Path(output_dir)

        # Check if exists
        if output_dir.exists():
            # Check if it's a directory
            if not output_dir.is_dir():
                result.add_error("output_dir", f"Path is not a directory: {output_dir}")
                return result

            # Check write permissions
            if not os.access(output_dir, os.W_OK):
                result.add_error("output_dir", f"No write permission: {output_dir}")

        else:
            # Check if parent exists and is writable
            parent = output_dir.parent
            if not parent.exists():
                result.add_warning("output_dir", f"Parent directory does not exist: {parent}")
            elif not os.access(parent, os.W_OK):
                result.add_error("output_dir", f"Cannot create directory. No write permission in parent: {parent}")

        return result

    @staticmethod
    def validate_workflow_config(config: Dict) -> ValidationResult:
        """
        Validate workflow configuration.

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Required fields
        required_fields = ["document_path"]
        for field in required_fields:
            if field not in config:
                result.add_error("config", f"Missing required field: {field}")

        # Validate document_path if present
        if "document_path" in config:
            doc_result = InputValidator.validate_document_path(config["document_path"])
            result.errors.extend(doc_result.errors)
            result.warnings.extend(doc_result.warnings)

        # Validate footnote_range if present
        if "footnote_range" in config and config["footnote_range"]:
            range_result = InputValidator.validate_footnote_range(config["footnote_range"])
            result.errors.extend(range_result.errors)
            result.warnings.extend(range_result.warnings)

        # Validate output_dir if present
        if "output_dir" in config:
            dir_result = InputValidator.validate_output_directory(config["output_dir"])
            result.errors.extend(dir_result.errors)
            result.warnings.extend(dir_result.warnings)

        # Validate boolean flags
        boolean_flags = [
            "enable_validation",
            "enable_quote_check",
            "enable_support_check"
        ]
        for flag in boolean_flags:
            if flag in config and not isinstance(config[flag], bool):
                result.add_warning("config", f"Field {flag} should be boolean, got {type(config[flag])}")

        return result

    @staticmethod
    def sanitize_citation_text(citation_text: str) -> str:
        """
        Sanitize citation text by removing problematic characters.

        Args:
            citation_text: Raw citation text

        Returns:
            Sanitized citation text
        """
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', citation_text)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Trim
        sanitized = sanitized.strip()

        return sanitized

    @staticmethod
    def sanitize_file_path(file_path: Union[str, Path]) -> Path:
        """
        Sanitize file path.

        Args:
            file_path: Raw file path

        Returns:
            Sanitized Path object
        """
        # Convert to Path
        path = Path(file_path)

        # Resolve to absolute path
        path = path.resolve()

        return path


# Import os for permission checks
import os
