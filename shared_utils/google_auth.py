"""Google API authentication utilities."""

import os
from typing import Any, List, Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .exceptions import AuthenticationError
from .logger import get_logger

logger = get_logger(__name__)


class GoogleAuthManager:
    """Manages authentication for Google APIs."""

    # OAuth 2.0 scopes required for the application
    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/forms",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(
        self,
        service_account_file: Optional[str] = None,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
    ):
        """
        Initialize the Google Auth Manager.

        Args:
            service_account_file: Path to service account JSON file
            credentials_file: Path to OAuth credentials JSON file
            token_file: Path to save/load user token
        """
        self.service_account_file = service_account_file
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._credentials: Optional[Credentials] = None

    def get_credentials(self) -> Credentials:
        """
        Get valid Google API credentials.

        Returns:
            Valid credentials object

        Raises:
            AuthenticationError: If authentication fails
        """
        # Use service account if provided
        if self.service_account_file and os.path.exists(self.service_account_file):
            logger.info("Authenticating with service account")
            return self._get_service_account_credentials()

        # Otherwise use OAuth 2.0 flow
        logger.info("Authenticating with OAuth 2.0")
        return self._get_oauth_credentials()

    def _get_service_account_credentials(self) -> Credentials:
        """Get credentials from service account file."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=self.SCOPES
            )
            logger.info("Successfully authenticated with service account")
            return credentials
        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            raise AuthenticationError(f"Service account authentication failed: {e}")

    def _get_oauth_credentials(self) -> Credentials:
        """Get credentials using OAuth 2.0 flow."""
        creds = None

        # Try to load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Could not load token file: {e}")

        # If credentials are invalid or don't exist, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Could not refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise AuthenticationError(
                        f"Credentials file not found: {self.credentials_file}"
                    )

                logger.info("Starting OAuth 2.0 flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            try:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token file")
            except Exception as e:
                logger.warning(f"Could not save token file: {e}")

        self._credentials = creds
        return creds

    def get_service(self, service_name: str, version: str) -> Any:
        """
        Build and return a Google API service.

        Args:
            service_name: Name of the service (e.g., 'sheets', 'calendar')
            version: API version (e.g., 'v4', 'v3')

        Returns:
            Google API service object
        """
        try:
            creds = self.get_credentials()
            service = build(service_name, version, credentials=creds)
            logger.info(f"Built {service_name} {version} service")
            return service
        except Exception as e:
            logger.error(f"Failed to build service {service_name}: {e}")
            raise AuthenticationError(f"Failed to build service: {e}")

    def verify_domain_access(self, email: str, allowed_domain: str = "stanford.edu") -> bool:
        """
        Verify that the email belongs to the allowed domain.

        Args:
            email: Email address to verify
            allowed_domain: Required email domain

        Returns:
            True if email is from allowed domain, False otherwise
        """
        if not email:
            return False

        domain = email.split("@")[-1].lower()
        is_valid = domain == allowed_domain.lower()

        if is_valid:
            logger.info(f"Domain verification passed for {email}")
        else:
            logger.warning(f"Domain verification failed for {email}: expected {allowed_domain}")

        return is_valid
