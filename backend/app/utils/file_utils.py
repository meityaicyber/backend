import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import magic

from app.config import settings


MIME_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def validate_extension(filename: str) -> Tuple[bool, str]:
    """Validate file extension against allowed list. Returns (is_valid, extension)."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in settings.ALLOWED_EXTENSIONS, ext


def validate_mime_type(file_bytes: bytes, expected_extension: str) -> Tuple[bool, str]:
    """Validate MIME type using python-magic. Returns (is_valid, detected_mime)."""
    detected_mime = magic.from_buffer(file_bytes[:2048], mime=True)

    # For .txt files, python-magic might detect various text subtypes
    if expected_extension == ".txt":
        return detected_mime.startswith("text/"), detected_mime

    expected_mime = MIME_TYPE_MAP.get(expected_extension, "")
    return detected_mime == expected_mime, detected_mime


def compute_sha256(file_bytes: bytes) -> str:
    """Compute SHA256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def get_storage_path(original_filename: str) -> Tuple[str, str]:
    """
    Generate storage path based on current date.
    Returns (directory_path, stored_filename).
    """
    now = datetime.now(timezone.utc)
    dir_path = os.path.join(
        settings.STORAGE_PATH,
        str(now.year),
        f"{now.month:02d}",
    )
    # Create unique stored filename
    import uuid
    unique_id = uuid.uuid4().hex[:12]
    stored_name = f"{unique_id}_{original_filename}"
    return dir_path, stored_name


def save_file_to_disk(file_bytes: bytes, dir_path: str, stored_filename: str) -> str:
    """Save file bytes to disk. Returns full file path."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    full_path = os.path.join(dir_path, stored_filename)
    with open(full_path, "wb") as f:
        f.write(file_bytes)
    return full_path


def delete_file_from_disk(file_path: str) -> bool:
    """Delete a file from disk if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False


def _sanitize_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings for JSONB storage."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        elif value is None:
            sanitized[key] = None
        else:
            sanitized[key] = str(value) if not isinstance(value, (int, float, bool, list, dict)) else value
    return sanitized


def extract_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a PDF file."""
    from PyPDF2 import PdfReader

    metadata: Dict[str, Any] = {}
    try:
        reader = PdfReader(file_path)
        info = reader.metadata
        metadata["page_count"] = len(reader.pages)

        if info:
            metadata["title"] = getattr(info, "title", None) or info.get("/Title")
            metadata["author"] = getattr(info, "author", None) or info.get("/Author")
            metadata["producer"] = getattr(info, "producer", None) or info.get("/Producer")
            metadata["subject"] = getattr(info, "subject", None) or info.get("/Subject")
            metadata["keywords"] = info.get("/Keywords")
            creation = getattr(info, "creation_date", None)
            modification = getattr(info, "modification_date", None)
            metadata["creation_date"] = creation if isinstance(creation, datetime) else _parse_pdf_date(info.get("/CreationDate"))
            metadata["modification_date"] = modification if isinstance(modification, datetime) else _parse_pdf_date(info.get("/ModDate"))
    except Exception:
        metadata["extraction_error"] = "Failed to extract PDF metadata"

    return metadata


def _parse_pdf_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse PDF date string format D:YYYYMMDDHHmmSS."""
    if not date_str:
        return None
    try:
        date_str = str(date_str)
        # Remove D: prefix if present
        if date_str.startswith("D:"):
            date_str = date_str[2:]
        # Take first 14 chars: YYYYMMDDHHmmSS
        date_str = date_str[:14].ljust(14, "0")
        return datetime.strptime(date_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def extract_docx_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a DOCX file."""
    from docx import Document

    metadata: Dict[str, Any] = {}
    try:
        doc = Document(file_path)
        props = doc.core_properties
        metadata["title"] = props.title
        metadata["author"] = props.author
        metadata["subject"] = props.subject
        metadata["keywords"] = props.keywords
        metadata["creation_date"] = props.created
        metadata["modification_date"] = props.modified
        # Count paragraphs as a proxy (no page count in DOCX without rendering)
        metadata["page_count"] = None
    except Exception:
        metadata["extraction_error"] = "Failed to extract DOCX metadata"

    return metadata


def extract_txt_metadata(file_path: str) -> Dict[str, Any]:
    """Extract basic metadata from a TXT file."""
    metadata: Dict[str, Any] = {
        "title": os.path.basename(file_path),
        "page_count": None,
    }
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            line_count = content.count("\n") + 1
            metadata["line_count"] = line_count
    except Exception:
        metadata["extraction_error"] = "Failed to read TXT file"

    return metadata


def extract_metadata(file_path: str, extension: str) -> Dict[str, Any]:
    """Extract metadata based on file type."""
    if extension == ".pdf":
        return extract_pdf_metadata(file_path)
    elif extension == ".docx":
        return extract_docx_metadata(file_path)
    elif extension == ".txt":
        return extract_txt_metadata(file_path)
    return {}

