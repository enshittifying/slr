"""
Service account authentication utilities
"""
from google.oauth2 import service_account
from pathlib import Path
import json
import logging
import keyring
from .crypto import decrypt_credentials

logger = logging.getLogger(__name__)


class ServiceAccountAuth:
    """Manages service account authentication"""

    def __init__(self, encrypted_creds_path: str = None):
        """
        Initialize authentication manager

        Args:
            encrypted_creds_path: Path to encrypted credentials file
        """
        self.encrypted_creds_path = encrypted_creds_path
        self.credentials = None

    def get_credentials(self, scopes: list):
        """
        Get service account credentials

        Args:
            scopes: List of OAuth scopes

        Returns:
            google.oauth2.service_account.Credentials
        """
        try:
            if self.credentials:
                logger.debug("Returning cached credentials")
                return self.credentials

            # Get encryption key from system keyring
            encryption_key = keyring.get_password("slr-citation-processor", "encryption_key")
            if not encryption_key:
                logger.error("Encryption key not found in system keyring")
                raise ValueError("Encryption key not found in system keyring. Please run setup.")

            # Decrypt credentials
            if not Path(self.encrypted_creds_path).exists():
                logger.error(f"Encrypted credentials file not found: {self.encrypted_creds_path}")
                raise FileNotFoundError(f"Encrypted credentials not found: {self.encrypted_creds_path}")

            encrypted_data = Path(self.encrypted_creds_path).read_bytes()
            decrypted_json = decrypt_credentials(encrypted_data, encryption_key.encode())

            creds_dict = json.loads(decrypted_json)

            self.credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=scopes
            )

            logger.info("Successfully loaded service account credentials")
            return self.credentials

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in decrypted credentials: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error getting credentials: {e}", exc_info=True)
            raise

    def get_credentials_from_file(self, creds_path: str, scopes: list):
        """
        Get credentials directly from unencrypted file (for setup/testing)

        Args:
            creds_path: Path to credentials.json
            scopes: List of OAuth scopes

        Returns:
            google.oauth2.service_account.Credentials
        """
        try:
            if not Path(creds_path).exists():
                logger.error(f"Credentials file not found: {creds_path}")
                raise FileNotFoundError(f"Credentials file not found: {creds_path}")

            self.credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=scopes
            )
            logger.info(f"Loaded credentials from file: {creds_path}")
            return self.credentials
        except Exception as e:
            logger.error(f"Error loading credentials from file: {e}", exc_info=True)
            raise

    @staticmethod
    def setup_encrypted_credentials(creds_path: str, output_path: str) -> str:
        """
        Set up encrypted credentials for first time use

        Args:
            creds_path: Path to credentials.json
            output_path: Where to save encrypted credentials

        Returns:
            Success message
        """
        try:
            from .crypto import generate_key, encrypt_credentials

            if not Path(creds_path).exists():
                logger.error(f"Credentials file not found: {creds_path}")
                raise FileNotFoundError(f"Credentials file not found: {creds_path}")

            # Generate encryption key
            key = generate_key()
            logger.debug("Generated encryption key")

            # Encrypt credentials
            with open(creds_path, 'r') as f:
                creds_json = f.read()

            encrypted = encrypt_credentials(creds_json, key)

            # Save encrypted credentials
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(encrypted)

            # Save key to system keyring
            keyring.set_password("slr-citation-processor", "encryption_key", key.decode())

            logger.info(f"Credentials encrypted and saved to {output_path}")
            return f"Credentials encrypted and saved to {output_path}"

        except Exception as e:
            logger.error(f"Error setting up encrypted credentials: {e}", exc_info=True)
            raise
