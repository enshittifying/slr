"""Parse citations from the master Google spreadsheet."""

from typing import List, Dict, Any
from web_app.services import GoogleSheetsService
from shared_utils.logger import get_logger
from shared_utils.exceptions import SpreadsheetError

logger = get_logger(__name__)


class SpreadsheetParser:
    """Parse citations from Google Sheets."""

    def __init__(self, spreadsheet_id: str):
        """
        Initialize the spreadsheet parser.

        Args:
            spreadsheet_id: ID of the Google Sheets document
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service = GoogleSheetsService()

    def get_citations_for_article(self, article_id: str) -> List[Dict[str, Any]]:
        """
        Get all citations for a specific article.

        Args:
            article_id: Article identifier (e.g., "79.1.article_name")

        Returns:
            List of citation dictionaries with metadata

        Raises:
            SpreadsheetError: If reading fails
        """
        try:
            # Read from the Sources tab (adjust range as needed)
            # Assuming the spreadsheet has columns:
            # A: Article ID
            # B: Source Number
            # C: Citation Text
            # D: Status
            # E: PDF Link
            # F: Notes

            range_name = "Sources!A2:F1000"  # Adjust as needed
            values = self.sheets_service.read_range(self.spreadsheet_id, range_name)

            citations = []
            for i, row in enumerate(values, start=2):
                if not row:  # Skip empty rows
                    continue

                # Parse row (handle missing columns)
                row_article_id = row[0] if len(row) > 0 else ""
                source_num = row[1] if len(row) > 1 else ""
                citation_text = row[2] if len(row) > 2 else ""
                status = row[3] if len(row) > 3 else "not_started"
                pdf_link = row[4] if len(row) > 4 else ""
                notes = row[5] if len(row) > 5 else ""

                # Filter by article ID
                if row_article_id == article_id:
                    citations.append({
                        "row_index": i,
                        "article_id": row_article_id,
                        "source_number": source_num,
                        "citation_text": citation_text,
                        "status": status,
                        "pdf_link": pdf_link,
                        "notes": notes,
                    })

            logger.info(f"Found {len(citations)} citations for article {article_id}")
            return citations

        except Exception as e:
            logger.error(f"Failed to parse spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to parse spreadsheet: {e}")

    def update_citation_status(
        self, row_index: int, status: str, pdf_link: str = "", notes: str = ""
    ) -> None:
        """
        Update the status of a citation in the spreadsheet.

        Args:
            row_index: Row number in the spreadsheet (1-indexed)
            status: New status value
            pdf_link: Optional PDF link
            notes: Optional notes
        """
        try:
            # Update status column (D), pdf_link (E), and notes (F)
            range_name = f"Sources!D{row_index}:F{row_index}"
            values = [[status, pdf_link, notes]]

            self.sheets_service.write_range(self.spreadsheet_id, range_name, values)
            logger.debug(f"Updated row {row_index} with status: {status}")

        except Exception as e:
            logger.error(f"Failed to update citation status: {e}")
            raise SpreadsheetError(f"Failed to update status: {e}")
