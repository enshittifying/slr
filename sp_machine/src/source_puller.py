"""Pull source files from various databases and websites."""

import os
import requests
from pathlib import Path
from typing import Dict, Any
from urllib.parse import quote

from web_app.services import GoogleDriveService
from shared_utils.logger import get_logger
from shared_utils.exceptions import SourceNotFoundError

logger = get_logger(__name__)


class SourcePuller:
    """Pull source files based on citation data."""

    def __init__(self, output_dir: str):
        """
        Initialize the source puller.

        Args:
            output_dir: Directory to save downloaded PDFs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.drive_service = GoogleDriveService()

        # API keys (if available)
        self.westlaw_api_key = os.getenv("WESTLAW_API_KEY")
        self.lexis_api_key = os.getenv("LEXIS_API_KEY")
        self.jstor_api_key = os.getenv("JSTOR_API_KEY")

    def pull_source(
        self, citation_data: Dict[str, Any], citation_row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pull a source file based on citation data.

        Args:
            citation_data: Parsed citation metadata
            citation_row: Original row data from spreadsheet

        Returns:
            Dictionary with 'success', 'file_path', and 'error' keys
        """
        source_type = citation_data.get("type", "unknown")
        source_num = citation_row.get("source_number", "unknown")

        logger.info(f"Pulling source type: {source_type}")

        try:
            # Route to appropriate puller based on type
            if source_type == "case":
                return self._pull_case(citation_data, source_num)
            elif source_type == "article":
                return self._pull_article(citation_data, source_num)
            elif source_type == "statute":
                return self._pull_statute(citation_data, source_num)
            elif source_type == "book":
                return self._pull_book(citation_data, source_num)
            elif source_type == "website":
                return self._pull_website(citation_data, source_num)
            else:
                return {
                    "success": False,
                    "file_path": None,
                    "error": f"Unknown source type: {source_type}",
                }

        except Exception as e:
            logger.error(f"Error pulling source: {e}")
            return {"success": False, "file_path": None, "error": str(e)}

    def _pull_case(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Pull a case from legal databases."""
        # Priority: HeinOnline > Westlaw > Lexis > Google Scholar

        # Try HeinOnline (free for academic institutions)
        result = self._try_heinonline(citation_data, source_num)
        if result["success"]:
            return result

        # Try Westlaw (if API key available)
        if self.westlaw_api_key:
            result = self._try_westlaw(citation_data, source_num)
            if result["success"]:
                return result

        # Try Google Scholar as fallback
        result = self._try_google_scholar(citation_data, source_num)
        if result["success"]:
            return result

        return {
            "success": False,
            "file_path": None,
            "error": "Could not retrieve case from any source",
        }

    def _pull_article(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Pull a law review article."""
        # Try HeinOnline, then JSTOR, then general search

        result = self._try_heinonline(citation_data, source_num)
        if result["success"]:
            return result

        if self.jstor_api_key:
            result = self._try_jstor(citation_data, source_num)
            if result["success"]:
                return result

        return {
            "success": False,
            "file_path": None,
            "error": "Could not retrieve article - may require manual download",
        }

    def _pull_statute(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Pull a statute."""
        # Statutes typically available on government websites
        return {
            "success": False,
            "file_path": None,
            "error": "Statute retrieval not yet implemented - check regulations.gov or govinfo.gov",
        }

    def _pull_book(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Pull a book excerpt."""
        # Books typically require library access or purchase
        return {
            "success": False,
            "file_path": None,
            "error": "Book retrieval requires manual download - check Stanford library",
        }

    def _pull_website(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Pull content from a website."""
        # For websites, we'll attempt to archive or screenshot
        return {
            "success": False,
            "file_path": None,
            "error": "Website archiving not yet implemented - use Wayback Machine manually",
        }

    # Database-specific methods

    def _try_heinonline(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Try to retrieve from HeinOnline."""
        # HeinOnline URL pattern (example - actual pattern may vary)
        # This is a placeholder - actual implementation would require HeinOnline API access

        logger.debug("Attempting HeinOnline retrieval (placeholder)")
        return {"success": False, "file_path": None, "error": "HeinOnline API not configured"}

    def _try_westlaw(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Try to retrieve from Westlaw."""
        logger.debug("Attempting Westlaw retrieval (placeholder)")
        return {"success": False, "file_path": None, "error": "Westlaw API not configured"}

    def _try_google_scholar(
        self, citation_data: Dict[str, Any], source_num: str
    ) -> Dict[str, Any]:
        """Try to retrieve from Google Scholar."""
        logger.debug("Attempting Google Scholar retrieval (placeholder)")
        return {"success": False, "file_path": None, "error": "Google Scholar scraping not implemented"}

    def _try_jstor(self, citation_data: Dict[str, Any], source_num: str) -> Dict[str, Any]:
        """Try to retrieve from JSTOR."""
        logger.debug("Attempting JSTOR retrieval (placeholder)")
        return {"success": False, "file_path": None, "error": "JSTOR API not configured"}

    def _save_pdf(self, pdf_content: bytes, filename: str) -> str:
        """
        Save PDF content to file and upload to Google Drive.

        Args:
            pdf_content: Binary PDF content
            filename: Name for the file

        Returns:
            Local file path
        """
        file_path = self.output_dir / filename
        with open(file_path, "wb") as f:
            f.write(pdf_content)

        logger.info(f"Saved PDF: {file_path}")

        # Optionally upload to Google Drive
        try:
            folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
            if folder_id:
                drive_file = self.drive_service.upload_file(str(file_path), folder_id=folder_id)
                logger.info(f"Uploaded to Drive: {drive_file.get('webViewLink')}")
        except Exception as e:
            logger.warning(f"Failed to upload to Drive: {e}")

        return str(file_path)
