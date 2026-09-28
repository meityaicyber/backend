from abc import ABC, abstractmethod
from typing import Optional, Dict, List

class PasswordResolver(ABC):
    """
    Abstract base class for password resolution strategies.
    Different implementations can fetch passwords from a global batch password,
    a mapping file, an external vault, etc.
    """
    @abstractmethod
    async def get_passwords(self, file_path: str) -> List[str]:
        pass


class BatchPasswordResolver(PasswordResolver):
    """
    Resolves passwords using a single global password provided for the entire batch.
    """
    def __init__(self, batch_password: str):
        self.batch_password = batch_password

    async def get_passwords(self, file_path: str) -> List[str]:
        return [self.batch_password] if self.batch_password else []


class MappingPasswordResolver(PasswordResolver):
    """
    Resolves passwords using a pre-defined mapping of filenames to passwords.
    """
    def __init__(self, password_map: Dict[str, str]):
        self.password_map = password_map

    async def get_passwords(self, file_path: str) -> List[str]:
        import os
        pwd = self.password_map.get(os.path.basename(file_path))
        return [pwd] if pwd else []


class EmptyPasswordResolver(PasswordResolver):
    """
    Always returns None, for batches where no passwords are expected.
    """
    async def get_passwords(self, file_path: str) -> List[str]:
        return []


class FolderPasswordResolver(PasswordResolver):
    """
    Resolves passwords by finding .txt files in the job directory and parsing them.
    (This works for both flat structures and subfolders, as long as the .txt is accessible).
    """
    def __init__(self, job_root: str = None):
        self.job_root = job_root
        self._passwords_cache = None

    async def get_passwords(self, file_path: str) -> List[str]:
        import os
        
        # Load from cache if already loaded (for efficiency across multiple PDFs)
        if self._passwords_cache is not None:
            return self._passwords_cache
            
        # Determine the root to search
        search_root = self.job_root
        if not search_root:
            search_root = os.path.dirname(file_path)
            
        passwords = []
        try:
            for root, dirs, files in os.walk(search_root):
                for f in files:
                    if f.lower().endswith('.txt'):
                        txt_path = os.path.join(root, f)
                        with open(txt_path, 'r', encoding='utf-8-sig') as txt_file:
                            for line in txt_file:
                                pwd = line.rstrip("\r\n")
                                if pwd:
                                    passwords.append(pwd)
        except Exception:
            pass
            
        # Deduplicate while preserving order
        self._passwords_cache = list(dict.fromkeys(passwords))
        return self._passwords_cache


async def resolve_and_decrypt(
    file_bytes: bytes,
    file_path: str,
    extension: str,
    resolver: PasswordResolver,
    last_successful_password: str = None
) -> tuple[bytes, str, str]:
    """
    Detects if the file is encrypted. If it is, asks the resolver for a list of passwords
    and attempts to decrypt sequentially until one succeeds.
    
    Returns:
        (decrypted_bytes, status, successful_password)
        status: 'UNENCRYPTED', 'DECRYPTED', 'PASSWORD_NOT_FOUND', 'INVALID_PASSWORD'
    """
    from app.utils.encryption_utils import (
        is_pdf_encrypted, decrypt_pdf,
        is_docx_encrypted, decrypt_docx
    )
    
    is_encrypted = False
    
    if extension == '.pdf':
        is_encrypted = is_pdf_encrypted(file_bytes)
    elif extension == '.docx':
        is_encrypted = is_docx_encrypted(file_bytes)
        
    if not is_encrypted:
        return file_bytes, 'UNENCRYPTED', None
        
    passwords = await resolver.get_passwords(file_path)
    if not passwords:
        return file_bytes, 'PASSWORD_NOT_FOUND', None
        
    # Try the last successful password first!
    if last_successful_password and last_successful_password in passwords:
        passwords.remove(last_successful_password)
        passwords.insert(0, last_successful_password)
        
    for password in passwords:
        try:
            if extension == '.pdf':
                decrypted_bytes = decrypt_pdf(file_bytes, password)
            elif extension == '.docx':
                decrypted_bytes = decrypt_docx(file_bytes, password)
            else:
                return file_bytes, 'UNSUPPORTED_ENCRYPTION', None
                
            return decrypted_bytes, 'DECRYPTED', password
        except Exception:
            continue
            
    return file_bytes, 'INVALID_PASSWORD', None
