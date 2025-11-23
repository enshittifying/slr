"""Google Sheets integration service."""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared_utils.logger import get_logger
from shared_utils.exceptions import SpreadsheetError

logger = get_logger(__name__)


class GoogleSheetsService:
    """Service for interacting with Google Sheets API."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, service_account_file: Optional[str] = None):
        """
        Initialize Google Sheets service.

        Args:
            service_account_file: Path to service account JSON file
        """
        self.service_account_file = service_account_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE"
        )
        self._service = None

    def _get_service(self):
        """Get or create Google Sheets service."""
        if self._service is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=self.SCOPES
                )
                self._service = build("sheets", "v4", credentials=credentials)
                logger.info("Google Sheets service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets service: {e}")
                raise SpreadsheetError(f"Failed to initialize Sheets service: {e}")

        return self._service

    def read_range(
        self, spreadsheet_id: str, range_name: str
    ) -> List[List[Any]]:
        """
        Read data from a spreadsheet range.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The A1 notation of the range to read

        Returns:
            List of rows, where each row is a list of cell values

        Raises:
            SpreadsheetError: If the read operation fails
        """
        try:
            service = self._get_service()
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheet_id=spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])
            logger.info(
                f"Read {len(values)} rows from {spreadsheet_id}!{range_name}"
            )
            return values
        except HttpError as e:
            logger.error(f"Failed to read from spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to read spreadsheet: {e}")

    def write_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """
        Write data to a spreadsheet range.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The A1 notation of the range to write
            values: List of rows to write
            value_input_option: How to interpret input data (USER_ENTERED or RAW)

        Returns:
            Response from the API

        Raises:
            SpreadsheetError: If the write operation fails
        """
        try:
            service = self._get_service()
            body = {"values": values}

            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )

            logger.info(
                f"Updated {result.get('updatedCells')} cells in {spreadsheet_id}!{range_name}"
            )
            return result
        except HttpError as e:
            logger.error(f"Failed to write to spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to write to spreadsheet: {e}")

    def append_rows(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """
        Append rows to a spreadsheet.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The A1 notation of the range to append to
            values: List of rows to append
            value_input_option: How to interpret input data

        Returns:
            Response from the API

        Raises:
            SpreadsheetError: If the append operation fails
        """
        try:
            service = self._get_service()
            body = {"values": values}

            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )

            logger.info(
                f"Appended {len(values)} rows to {spreadsheet_id}!{range_name}"
            )
            return result
        except HttpError as e:
            logger.error(f"Failed to append to spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to append to spreadsheet: {e}")

    def batch_update(
        self, spreadsheet_id: str, requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform batch update operations on a spreadsheet.

        Args:
            spreadsheet_id: The ID of the spreadsheet
            requests: List of update requests

        Returns:
            Response from the API

        Raises:
            SpreadsheetError: If the batch update fails
        """
        try:
            service = self._get_service()
            body = {"requests": requests}

            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            logger.info(f"Batch updated spreadsheet {spreadsheet_id}")
            return result
        except HttpError as e:
            logger.error(f"Failed to batch update spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to batch update spreadsheet: {e}")

    def create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """
        Create a new spreadsheet.

        Args:
            title: Title for the new spreadsheet

        Returns:
            Spreadsheet metadata including ID

        Raises:
            SpreadsheetError: If creation fails
        """
        try:
            service = self._get_service()
            spreadsheet = {"properties": {"title": title}}

            result = service.spreadsheets().create(body=spreadsheet).execute()

            logger.info(f"Created spreadsheet: {result.get('spreadsheetId')}")
            return result
        except HttpError as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            raise SpreadsheetError(f"Failed to create spreadsheet: {e}")
