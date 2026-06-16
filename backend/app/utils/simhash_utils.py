import io
import re
from typing import Optional
from simhash import Simhash

def extract_text_from_bytes(file_bytes: bytes, extension: str) -> str:
    """Extract raw text from file bytes based on the extension."""
    text = ""
    try:
        if extension == ".txt":
            text = file_bytes.decode("utf-8", errors="ignore")
        elif extension == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            text = " ".join(pages_text)
        elif extension == ".docx":
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            text = " ".join([p.text for p in doc.paragraphs])
    except Exception as e:
        # If extraction fails, we just return empty text, which will result in a generic hash
        print(f"Error extracting text for simhash: {e}")
        pass

    # Normalize text: lowercase, remove punctuation, keep only alphanumeric
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return text.strip()


def calculate_simhash(file_bytes: bytes, extension: str) -> Optional[str]:
    """Calculate the Simhash of the file content. Returns string representation of the 64-bit integer."""
    text = extract_text_from_bytes(file_bytes, extension)
    if not text:
        return None
    # simhash module automatically tokenizes strings into words if passed a string
    return str(Simhash(text).value)


def is_partial_duplicate(new_hash_str: str, existing_hash_str: str, threshold: int = 3) -> bool:
    """Compare two Simhashes. Returns True if Hamming distance is <= threshold."""
    if not new_hash_str or not existing_hash_str:
        return False
    try:
        new_val = int(new_hash_str)
        existing_val = int(existing_hash_str)
        
        # Calculate Hamming distance
        x = (new_val ^ existing_val) & ((1 << 64) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x - 1
        return ans <= threshold
    except ValueError:
        return False
