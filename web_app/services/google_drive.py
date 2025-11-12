"""Google Drive integration service."""

import os
from typing import Optional, List, Dict, Any, BinaryIO
from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

from shared_utils.logger import get_logger
from shared_utils.exceptions import SLRException

logger = get_logger(__name__)


class GoogleDriveService:
    """Service for interacting with Google Drive API."""

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, service_account_file: Optional[str] = None):
        """
        Initialize Google Drive service.

        Args:
            service_account_file: Path to service account JSON file
        """
        self.service_account_file = service_account_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE"
        )
        self._service = None

    def _get_service(self):
        """Get or create Google Drive service."""
        if self._service is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=self.SCOPES
                )
                self._service = build("drive", "v3", credentials=credentials)
                logger.info("Google Drive service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Drive service: {e}")
                raise SLRException(f"Failed to initialize Drive service: {e}")

        return self._service

    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        name: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Path to the file to upload
            folder_id: Optional parent folder ID
            name: Optional name for the file (defaults to filename)
            mime_type: Optional MIME type (will be guessed if not provided)

        Returns:
            File metadata including ID

        Raises:
            SLRException: If upload fails
        """
        try:
            service = self._get_service()

            file_name = name or os.path.basename(file_path)
            file_metadata = {"name": file_name}

            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
                .execute()
            )

            logger.info(f"Uploaded file: {file.get('name')} (ID: {file.get('id')})")
            return file
        except HttpError as e:
            logger.error(f"Failed to upload file: {e}")
            raise SLRException(f"Failed to upload file: {e}")

    def upload_file_from_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        folder_id: Optional[str] = None,
        mime_type: str = "application/pdf",
    ) -> Dict[str, Any]:
        """
        Upload a file from bytes to Google Drive.

        Args:
            file_bytes: File content as bytes
            file_name: Name for the file
            folder_id: Optional parent folder ID
            mime_type: MIME type of the file

        Returns:
            File metadata including ID

        Raises:
            SLRException: If upload fails
        """
        try:
            service = self._get_service()

            file_metadata = {"name": file_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaIoBaseUpload(
                BytesIO(file_bytes), mimetype=mime_type, resumable=True
            )

            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
                .execute()
            )

            logger.info(f"Uploaded file from bytes: {file.get('name')}")
            return file
        except HttpError as e:
            logger.error(f"Failed to upload file from bytes: {e}")
            raise SLRException(f"Failed to upload file: {e}")

    def download_file(self, file_id: str, destination_path: str) -> None:
        """
        Download a file from Google Drive.

        Args:
            file_id: ID of the file to download
            destination_path: Path to save the downloaded file

        Raises:
            SLRException: If download fails
        """
        try:
            service = self._get_service()

            request = service.files().get_media(fileId=file_id)

            with open(destination_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"Downloaded file {file_id} to {destination_path}")
        except HttpError as e:
            logger.error(f"Failed to download file: {e}")
            raise SLRException(f"Failed to download file: {e}")

    def download_file_as_bytes(self, file_id: str) -> bytes:
        """
        Download a file from Google Drive as bytes.

        Args:
            file_id: ID of the file to download

        Returns:
            File content as bytes

        Raises:
            SLRException: If download fails
        """
        try:
            service = self._get_service()
            request = service.files().get_media(fileId=file_id)

            file_bytes = BytesIO()
            downloader = MediaIoBaseDownload(file_bytes, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_bytes.seek(0)
            logger.info(f"Downloaded file {file_id} as bytes")
            return file_bytes.read()
        except HttpError as e:
            logger.error(f"Failed to download file as bytes: {e}")
            raise SLRException(f"Failed to download file: {e}")

    def list_files(
        self, folder_id: Optional[str] = None, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in Google Drive.

        Args:
            folder_id: Optional folder ID to list files from
            query: Optional query string for filtering files

        Returns:
            List of file metadata dictionaries

        Raises:
            SLRException: If listing fails
        """
        try:
            service = self._get_service()

            # Build query
            q = []
            if folder_id:
                q.append(f"'{folder_id}' in parents")
            if query:
                q.append(query)

            query_string = " and ".join(q) if q else None

            results = (
                service.files()
                .list(
                    q=query_string,
                    pageSize=100,
                    fields="files(id, name, mimeType, createdTime, modifiedTime, webViewLink)",
                )
                .execute()
            )

            files = results.get("files", [])
            logger.info(f"Listed {len(files)} files")
            return files
        except HttpError as e:
            logger.error(f"Failed to list files: {e}")
            raise SLRException(f"Failed to list files: {e}")

    def create_folder(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.

        Args:
            folder_name: Name of the folder to create
            parent_id: Optional parent folder ID

        Returns:
            Folder metadata including ID

        Raises:
            SLRException: If creation fails
        """
        try:
            service = self._get_service()

            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            if parent_id:
                file_metadata["parents"] = [parent_id]

            folder = (
                service.files()
                .create(body=file_metadata, fields="id,name,webViewLink")
                .execute()
            )

            logger.info(f"Created folder: {folder.get('name')} (ID: {folder.get('id')})")
            return folder
        except HttpError as e:
            logger.error(f"Failed to create folder: {e}")
            raise SLRException(f"Failed to create folder: {e}")

    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.

        Args:
            file_id: ID of the file to delete

        Raises:
            SLRException: If deletion fails
        """
        try:
            service = self._get_service()
            service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file: {file_id}")
        except HttpError as e:
            logger.error(f"Failed to delete file: {e}")
            raise SLRException(f"Failed to delete file: {e}")

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get metadata for a file.

        Args:
            file_id: ID of the file

        Returns:
            File metadata

        Raises:
            SLRException: If retrieval fails
        """
        try:
            service = self._get_service()
            file = (
                service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink",
                )
                .execute()
            )
            logger.info(f"Retrieved metadata for file: {file.get('name')}")
            return file
        except HttpError as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise SLRException(f"Failed to get file metadata: {e}")
