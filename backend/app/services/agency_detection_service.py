import re
from typing import Dict, List, Optional

class AgencyDetectionService:
    AUDITOR_PHRASES = [
        r'audited\s+by\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)',
        r'auditing\s+organisation\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)',
        r'information\s+security\s+auditor\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)',
        r'audited\s+and\s+certified\s+by\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)',
        r'empanelled\s+by\s+cert\-in\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)'
    ]
    GENERIC_PHRASES = [
        r'prepared\s+by\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)',
        r'submitted\s+by\s*[:\-]?\s*([a-zA-Z0-9\s\,\.\&\-]+)'
    ]
    
    @classmethod
    def extract_agency(cls, pages_text: List[str]) -> Dict:
        """
        Lightweight agency extraction from text using phrase rules.
        """
        # Check up to first 3 pages
        for idx, page_text in enumerate(pages_text[:3]):
            if not page_text:
                continue
                
            page_text_clean = re.sub(r'\s+', ' ', page_text)
            
            # 1. Search for high-confidence auditor phrases
            for pattern in cls.AUDITOR_PHRASES:
                match = re.search(pattern, page_text_clean, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    extracted = re.split(r'  |\n', extracted)[0].strip()
                    if len(extracted) > 3:
                        return {
                            "extracted_name": extracted,
                            "source_page": idx + 1,
                            "extraction_method": "TEXT_RULES",
                            "signal_confidence": "HIGH",
                            "status": "NAME_FOUND"
                        }
                            
            # 2. Search for generic phrases (low confidence)
            for pattern in cls.GENERIC_PHRASES:
                match = re.search(pattern, page_text_clean, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    extracted = re.split(r'  |\n', extracted)[0].strip()
                    if len(extracted) > 3:
                        return {
                            "extracted_name": extracted,
                            "source_page": idx + 1,
                            "extraction_method": "TEXT_RULES",
                            "signal_confidence": "LOW",
                            "status": "NAME_FOUND"
                        }
                            
        return {
            "extracted_name": None,
            "source_page": None,
            "extraction_method": "TEXT_RULES",
            "signal_confidence": "NONE",
            "status": "NAME_NOT_FOUND"
        }
