"""
Google Drive client for file operations
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
import logging

from ..utils.retry import retry_api_call, APIRetryConfig
from ..utils.edge_cases import PDFValidator

logger = logging.getLogger(__name__)


class DriveClient:
    """Google Drive API client"""

    def __init__(self, credentials, root_folder_id: str = None):
        """
        Initialize Drive client

        Args:
            credentials: Google service account credentials
            root_folder_id: Root folder ID for file operations
        """
        self.credentials = credentials
        self.root_folder_id = root_folder_id
        self.service = build('drive', 'v3', credentials=credentials)

    @retry_api_call
    def upload_file(self, local_path: str, filename: str = None, folder_id: str = None,
                   mime_type: str = None) -> str:
        """
        Upload file to Drive (with automatic retry on failures)

        Args:
            local_path: Path to local file
            filename: Filename in Drive (defaults to local filename)
            folder_id: Parent folder ID (defaults to root_folder_id)
            mime_type: MIME type (auto-detected if None)

        Returns:
            File ID of uploaded file
        """
        # Validate PDF if it's a PDF file
        if local_path.endswith('.pdf'):
            is_valid, error = PDFValidator.validate_pdf(local_path)
            if not is_valid:
                logger.warning(f"Uploading potentially corrupted PDF: {error}")


        if filename is None:
            filename = Path(local_path).name

        if folder_id is None:
            folder_id = self.root_folder_id

        if mime_type is None:
            # Auto-detect based on extension
            ext = Path(local_path).suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.json': 'application/json'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')

        file_metadata = {'name': filename}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)

        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            logger.info(f"Uploaded {filename} to Drive: {file.get('id')}")
            return file.get('id')

        except HttpError as error:
            logger.error(f"Failed to upload {filename}: {error}")
            raise

    def download_file(self, file_id: str = None, file_link: str = None,
                     output_path: str = None) -> str:
        """
        Download file from Drive

        Args:
            file_id: File ID (provide either file_id or file_link)
            file_link: Drive link (provide either file_id or file_link)
            output_path: Where to save file (temp file if None)

        Returns:
            Path to downloaded file
        """
        # Extract file ID from link if needed
        if file_link and not file_id:
            file_id = self._extract_file_id(file_link)

        if not file_id:
            raise ValueError("Must provide either file_id or file_link")

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")

        # Save to file
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.pdf')

        with open(output_path, 'wb') as f:
            f.write(fh.getvalue())

        logger.info(f"Downloaded file {file_id} to {output_path}")
        return output_path

    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Get folder ID or create if doesn't exist

        Args:
            folder_name: Name of folder
            parent_id: Parent folder ID (defaults to root_folder_id)

        Returns:
            Folder ID
        """
        if parent_id is None:
            parent_id = self.root_folder_id

        # Search for existing folder
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        files = results.get('files', [])

        if files:
            logger.info(f"Found existing folder: {folder_name}")
            return files[0]['id']

        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        logger.info(f"Created folder: {folder_name} ({folder.get('id')})")
        return folder.get('id')

    def list_files(self, folder_id: str = None, query: str = None) -> List[Dict]:
        """
        List files in folder

        Args:
            folder_id: Folder ID (defaults to root_folder_id)
            query: Custom query string

        Returns:
            List of file metadata dicts
        """
        if folder_id is None:
            folder_id = self.root_folder_id

        if query is None:
            query = f"'{folder_id}' in parents and trashed=false"

        results = self.service.files().list(
            q=query,
            fields='files(id, name, mimeType, modifiedTime, size)'
        ).execute()

        return results.get('files', [])

    def delete_file(self, file_id: str):
        """
        Delete file from Drive

        Args:
            file_id: File ID to delete
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file: {file_id}")
        except HttpError as error:
            logger.error(f"Failed to delete file {file_id}: {error}")
            raise

    def get_file_link(self, file_id: str) -> str:
        """
        Get shareable link for file

        Args:
            file_id: File ID

        Returns:
            Drive link URL
        """
        return f"https://drive.google.com/file/d/{file_id}/view"

    @staticmethod
    def _extract_file_id(drive_link: str) -> str:
        """
        Extract file ID from Drive link

        Args:
            drive_link: Google Drive link

        Returns:
            File ID
        """
        # Handle various Drive link formats
        if '/d/' in drive_link:
            return drive_link.split('/d/')[1].split('/')[0]
        elif 'id=' in drive_link:
            return drive_link.split('id=')[1].split('&')[0]
        else:
            # Assume it's already a file ID
            return drive_link

    def upload_source_pdf(self, local_path: str, source_id: str, article_id: str) -> str:
        """
        Upload source PDF to Drive in organized structure

        Args:
            local_path: Path to PDF
            source_id: Source identifier
            article_id: Article identifier

        Returns:
            File ID
        """
        # Create/get article folder
        article_folder_id = self.get_or_create_folder(article_id, self.root_folder_id)

        # Create/get SP subfolder
        sp_folder_id = self.get_or_create_folder('SP', article_folder_id)

        # Upload file
        return self.upload_file(
            local_path,
            filename=f'{source_id}.pdf',
            folder_id=sp_folder_id,
            mime_type='application/pdf'
        )

    def upload_r1_pdf(self, local_path: str, source_id: str, article_id: str) -> str:
        """
        Upload R1 PDF to Drive

        Args:
            local_path: Path to PDF
            source_id: Source identifier
            article_id: Article identifier

        Returns:
            File ID
        """
        article_folder_id = self.get_or_create_folder(article_id, self.root_folder_id)
        r1_folder_id = self.get_or_create_folder('R1', article_folder_id)

        return self.upload_file(
            local_path,
            filename=f'{source_id}_R1.pdf',
            folder_id=r1_folder_id,
            mime_type='application/pdf'
        )

    def upload_r2_package(self, article_id: str, pdf_files: List[str],
                         word_doc: str, html_report: str) -> Dict[str, str]:
        """
        Upload complete R2 package

        Args:
            article_id: Article identifier
            pdf_files: List of R2 PDF paths
            word_doc: Path to Word doc with changes
            html_report: Path to HTML review queue

        Returns:
            Dict of file types to file IDs
        """
        article_folder_id = self.get_or_create_folder(article_id, self.root_folder_id)
        r2_folder_id = self.get_or_create_folder('R2', article_folder_id)

        results = {}

        # Upload PDFs
        for pdf_path in pdf_files:
            file_id = self.upload_file(pdf_path, folder_id=r2_folder_id)
            results[Path(pdf_path).name] = file_id

        # Upload Word doc
        word_id = self.upload_file(word_doc, folder_id=r2_folder_id)
        results['word_doc'] = word_id

        # Upload HTML report
        html_id = self.upload_file(html_report, folder_id=r2_folder_id)
        results['html_report'] = html_id

        return results
