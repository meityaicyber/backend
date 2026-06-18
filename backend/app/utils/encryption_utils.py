from cryptography.fernet import Fernet
from app.config import settings

def get_fernet() -> Fernet:
    """Returns a Fernet instance using the configured encryption key."""
    # Ensure the key is bytes
    key = settings.FILE_ENCRYPTION_KEY.encode('utf-8')
    return Fernet(key)

def encrypt_file(data: bytes) -> bytes:
    """Encrypts raw bytes using Fernet."""
    f = get_fernet()
    return f.encrypt(data)

def decrypt_file(data: bytes) -> bytes:
    """Decrypts Fernet-encrypted bytes."""
    f = get_fernet()
    return f.decrypt(data)
