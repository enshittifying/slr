"""
Credential encryption and decryption utilities
"""
from cryptography.fernet import Fernet
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_key() -> bytes:
    """Generate encryption key - run once during setup"""
    return Fernet.generate_key()


def encrypt_credentials(credentials_json: str, key: bytes) -> bytes:
    """Encrypt service account JSON"""
    try:
        f = Fernet(key)
        encrypted = f.encrypt(credentials_json.encode())
        logger.debug("Successfully encrypted credentials")
        return encrypted
    except Exception as e:
        logger.error(f"Error encrypting credentials: {e}", exc_info=True)
        raise


def decrypt_credentials(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt service account JSON"""
    try:
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_data).decode()
        logger.debug("Successfully decrypted credentials")
        return decrypted
    except Exception as e:
        logger.error(f"Error decrypting credentials: {e}", exc_info=True)
        raise


def save_encrypted_credentials(credentials_path: str, output_path: str, key: bytes):
    """
    Encrypt and save service account credentials

    Args:
        credentials_path: Path to credentials.json
        output_path: Where to save encrypted file
        key: Encryption key
    """
    try:
        with open(credentials_path, 'r') as f:
            creds_json = f.read()

        encrypted = encrypt_credentials(creds_json, key)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(encrypted)

        logger.info(f"Saved encrypted credentials to {output_path}")
    except FileNotFoundError:
        logger.error(f"Credentials file not found: {credentials_path}")
        raise
    except Exception as e:
        logger.error(f"Error saving encrypted credentials: {e}", exc_info=True)
        raise


def load_encrypted_credentials(encrypted_path: str, key: bytes) -> str:
    """
    Load and decrypt service account credentials

    Args:
        encrypted_path: Path to encrypted credentials file
        key: Encryption key

    Returns:
        Decrypted JSON string
    """
    try:
        if not Path(encrypted_path).exists():
            raise FileNotFoundError(f"Encrypted credentials not found: {encrypted_path}")

        encrypted_data = Path(encrypted_path).read_bytes()
        decrypted = decrypt_credentials(encrypted_data, key)

        logger.info(f"Loaded encrypted credentials from {encrypted_path}")
        return decrypted
    except Exception as e:
        logger.error(f"Error loading encrypted credentials: {e}", exc_info=True)
        raise
