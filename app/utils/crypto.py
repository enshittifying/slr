"""
Credential encryption and decryption utilities
"""
from cryptography.fernet import Fernet
import base64
from pathlib import Path


def generate_key() -> bytes:
    """Generate encryption key - run once during setup"""
    return Fernet.generate_key()


def encrypt_credentials(credentials_json: str, key: bytes) -> bytes:
    """Encrypt service account JSON"""
    f = Fernet(key)
    return f.encrypt(credentials_json.encode())


def decrypt_credentials(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt service account JSON"""
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()


def save_encrypted_credentials(credentials_path: str, output_path: str, key: bytes):
    """
    Encrypt and save service account credentials

    Args:
        credentials_path: Path to credentials.json
        output_path: Where to save encrypted file
        key: Encryption key
    """
    with open(credentials_path, 'r') as f:
        creds_json = f.read()

    encrypted = encrypt_credentials(creds_json, key)

    Path(output_path).write_bytes(encrypted)


def load_encrypted_credentials(encrypted_path: str, key: bytes) -> str:
    """
    Load and decrypt service account credentials

    Args:
        encrypted_path: Path to encrypted credentials file
        key: Encryption key

    Returns:
        Decrypted JSON string
    """
    encrypted_data = Path(encrypted_path).read_bytes()
    return decrypt_credentials(encrypted_data, key)
