"""
Google Sheets client wrapper - adapts SLRinator integration for desktop app
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
import logging

from ..utils.retry import retry_api_call

logger = logging.getLogger(__name__)


class SheetsClient:
    """Google Sheets API client for SLR Master Control Sheet"""

    def __init__(self, credentials, spreadsheet_id: str):
        """
        Initialize Sheets client

        Args:
            credentials: Google service account credentials
            spreadsheet_id: ID of the master control spreadsheet
        """
        self.spreadsheet_id = spreadsheet_id
        self.service = build('sheets', 'v4', credentials=credentials)

    @retry_api_call
    def get_all_articles(self) -> List[Dict]:
        """
        Get all articles from Master Sheet

        Returns:
            List of article dicts with keys: article_id, volume_issue, author, title, stage, etc.
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Articles!A2:Z'
            ).execute()

            rows = result.get('values', [])
            articles = []

            for row in rows:
                if len(row) < 4:  # Skip incomplete rows
                    continue

                articles.append({
                    'article_id': row[0] if len(row) > 0 else '',
                    'volume_issue': row[1] if len(row) > 1 else '',
                    'author': row[2] if len(row) > 2 else '',
                    'title': row[3] if len(row) > 3 else '',
                    'stage': row[4] if len(row) > 4 else 'not_started',
                    'sources_total': int(row[5]) if len(row) > 5 and row[5] else 0,
                    'sources_completed': int(row[6]) if len(row) > 6 and row[6] else 0,
                    'last_updated': row[7] if len(row) > 7 else ''
                })

            logger.info(f"Retrieved {len(articles)} articles from Master Sheet")
            return articles

        except HttpError as error:
            logger.error(f"Failed to get articles: {error}")
            raise

    @retry_api_call
    def get_sources_for_article(self, article_id: str) -> List[Dict]:
        """
        Get all sources for a specific article

        Args:
            article_id: Article identifier

        Returns:
            List of source dicts
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sources!A2:Z'
            ).execute()

            rows = result.get('values', [])
            sources = []

            for row in rows:
                if len(row) < 2:
                    continue

                # Check if this source belongs to the article
                if row[1] == article_id:
                    sources.append({
                        'source_id': row[0] if len(row) > 0 else '',
                        'article_id': row[1] if len(row) > 1 else '',
                        'footnote_num': row[2] if len(row) > 2 else '',
                        'citation': row[3] if len(row) > 3 else '',
                        'type': row[4] if len(row) > 4 else 'unknown',
                        'status': row[5] if len(row) > 5 else 'pending',
                        'drive_link': row[6] if len(row) > 6 else '',
                        'r1_status': row[7] if len(row) > 7 else '',
                        'r1_drive_link': row[8] if len(row) > 8 else '',
                        'r2_status': row[9] if len(row) > 9 else '',
                        'error_message': row[10] if len(row) > 10 else ''
                    })

            logger.info(f"Retrieved {len(sources)} sources for article {article_id}")
            return sources

        except HttpError as error:
            logger.error(f"Failed to get sources: {error}")
            raise

    @retry_api_call
    def update_source_status(self, source_id: str, status: str = None,
                           drive_link: str = None, error_message: str = None):
        """
        Update source status in Sheet

        Args:
            source_id: Source identifier
            status: New status
            drive_link: Drive link to uploaded PDF
            error_message: Error message if failed
        """
        try:
            # Find row for this source_id
            row_num = self._find_source_row(source_id)
            if not row_num:
                logger.warning(f"Source {source_id} not found in sheet")
                return

            # Update status column (F)
            if status:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!F{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()

            # Update drive_link column (G)
            if drive_link:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!G{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[drive_link]]}
                ).execute()

            # Update error_message column (K)
            if error_message:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!K{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[error_message]]}
                ).execute()

            logger.info(f"Updated source {source_id} status to {status}")

        except HttpError as error:
            logger.error(f"Failed to update source status: {error}")
            raise

    @retry_api_call
    def update_r1_status(self, source_id: str, status: str = None,
                        r1_drive_link: str = None, error_message: str = None):
        """
        Update R1 status in Sheet

        Args:
            source_id: Source identifier
            status: R1 status
            r1_drive_link: Drive link to R1 PDF
            error_message: Error message if failed
        """
        try:
            row_num = self._find_source_row(source_id)
            if not row_num:
                return

            if status:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!H{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[status]]}
                ).execute()

            if r1_drive_link:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!I{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[r1_drive_link]]}
                ).execute()

            if error_message:
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'Sources!K{row_num}',
                    valueInputOption='RAW',
                    body={'values': [[error_message]]}
                ).execute()

            logger.info(f"Updated R1 status for {source_id}")

        except HttpError as error:
            logger.error(f"Failed to update R1 status: {error}")
            raise

    @retry_api_call
    def update_article_stage(self, article_id: str, stage: str, error_message: str = None):
        """
        Update article processing stage

        Args:
            article_id: Article identifier
            stage: New stage (e.g., 'sp_complete', 'r1_in_progress')
            error_message: Error message if applicable
        """
        try:
            row_num = self._find_article_row(article_id)
            if not row_num:
                return

            # Update stage column (E)
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Articles!E{row_num}',
                valueInputOption='RAW',
                body={'values': [[stage]]}
            ).execute()

            # Update timestamp column (H)
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Articles!H{row_num}',
                valueInputOption='RAW',
                body={'values': [[timestamp]]}
            ).execute()

            logger.info(f"Updated article {article_id} stage to {stage}")

        except HttpError as error:
            logger.error(f"Failed to update article stage: {error}")
            raise

    def _find_source_row(self, source_id: str) -> Optional[int]:
        """Find row number for source_id"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Sources!A2:A'
            ).execute()

            rows = result.get('values', [])
            for i, row in enumerate(rows):
                if row and row[0] == source_id:
                    return i + 2  # +2 because of header row and 0-indexing

            return None

        except HttpError as error:
            logger.error(f"Error finding source row: {error}")
            return None

    def _find_article_row(self, article_id: str) -> Optional[int]:
        """Find row number for article_id"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Articles!A2:A'
            ).execute()

            rows = result.get('values', [])
            for i, row in enumerate(rows):
                if row and row[0] == article_id:
                    return i + 2

            return None

        except HttpError as error:
            logger.error(f"Error finding article row: {error}")
            return None

    def batch_update_sources(self, updates: List[Dict]):
        """
        Batch update multiple sources

        Args:
            updates: List of dicts with source_id and fields to update
        """
        for update in updates:
            source_id = update.pop('source_id')
            self.update_source_status(
                source_id,
                status=update.get('status'),
                drive_link=update.get('drive_link'),
                error_message=update.get('error_message')
            )
