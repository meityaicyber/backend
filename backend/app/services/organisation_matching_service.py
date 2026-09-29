import re
import uuid
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agency import Agency

def normalize_org_name(name: str) -> str:
    """
    Normalizes organisation names to improve matching.
    Removes common suffixes, prefixes, punctuation, and extra spaces.
    """
    if not name:
        return ""
    
    name = name.lower()
    
    # Remove punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Remove common prefixes/suffixes
    # M/s, Pvt Ltd, Private Limited, Ltd, LLP, INC, LLC
    stop_words = [
        r'\bm\s*s\b', r'\bpvt\b', r'\bltd\b', r'\bprivate\b', r'\blimited\b', 
        r'\bllp\b', r'\binc\b', r'\bllc\b', r'\bcompany\b', r'\bcorporation\b'
    ]
    for stop_word in stop_words:
        name = re.sub(stop_word, ' ', name)
        
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def calculate_similarity(name1: str, name2: str) -> float:
    """Calculates a string similarity score between 0.0 and 1.0"""
    return SequenceMatcher(None, name1, name2).ratio()

from rapidfuzz import process, fuzz

class OrganisationMatchingService:
    _org_cache: List[Dict] = []
    _is_loaded: bool = False

    @classmethod
    async def load_orgs(cls, db: AsyncSession):
        """Loads agencies into memory."""
        result = await db.execute(select(Agency).where(Agency.status == 'ACTIVE'))
        orgs = result.scalars().all()
        
        cls._org_cache = []
        for org in orgs:
            norm_name = org.normalized_name or normalize_org_name(org.agency_name)
            aliases = [normalize_org_name(a) for a in (org.aliases or [])]
            cls._org_cache.append({
                'agency_id': str(org.agency_id),
                'name': org.agency_name,
                'norm_name': norm_name,
                'aliases': aliases
            })
        cls._is_loaded = True

    @classmethod
    async def match_agency(
        cls, db: AsyncSession, extracted_name: str, signal_confidence: str = "HIGH"
    ) -> Tuple[Optional[uuid.UUID], str, List[dict]]:
        """
        Attempts to match the extracted ML name against the Agency master table.
        """
        if not cls._is_loaded:
            await cls.load_orgs(db)
            
        if not extracted_name:
            return None, 'AGENCY_NOT_FOUND', []

        norm_extracted = normalize_org_name(extracted_name)
        if not norm_extracted:
            return None, 'AGENCY_NOT_FOUND', []
            
        candidates = []
        
        for org in cls._org_cache:
            # 1. Exact normalized match
            if norm_extracted == org['norm_name']:
                candidates.append({
                    'agency_id': org['agency_id'],
                    'name': org['name'],
                    'score': 1.0,
                    'match_method': 'NORMALIZED_EXACT'
                })
                break # Exact match found
                
            # 2. Alias match
            if norm_extracted in org['aliases']:
                candidates.append({
                    'agency_id': org['agency_id'],
                    'name': org['name'],
                    'score': 1.0,
                    'match_method': 'ALIAS_EXACT'
                })
                break
                
        # If we have an exact match, return it (but consider signal confidence)
        if candidates and candidates[0]['score'] == 1.0:
            if signal_confidence == "LOW":
                # Low confidence signal + Exact match = Corroborated
                pass
            return uuid.UUID(candidates[0]['agency_id']), 'AGENCY_MATCHED', candidates

        # 3. Controlled fuzzy match
        # Extract names for RapidFuzz
        choices = {idx: org['norm_name'] for idx, org in enumerate(cls._org_cache)}
        # We also want to include aliases in fuzzy matching? The plan says "fuzz against the same in-memory list"
        
        fuzzy_results = process.extract(
            norm_extracted, choices, scorer=fuzz.WRatio, limit=3
        )
        
        for match_str, score, idx in fuzzy_results:
            # RapidFuzz returns score 0-100
            score_normalized = score / 100.0
            candidates.append({
                'agency_id': cls._org_cache[idx]['agency_id'],
                'name': cls._org_cache[idx]['name'],
                'score': score_normalized,
                'match_method': 'FUZZY'
            })
            
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:3]
        
        if not top_candidates:
            return None, 'AGENCY_NOT_FOUND', []
            
        if top_candidates[0]['score'] >= 0.90: # Slightly lower threshold for rapidfuzz WRatio
            if signal_confidence == "LOW":
                # Low confidence + Fuzzy match = Needs review
                return None, 'AGENCY_REVIEW_REQUIRED', top_candidates
            return uuid.UUID(top_candidates[0]['agency_id']), 'AGENCY_MATCHED', top_candidates
            
        return None, 'AGENCY_REVIEW_REQUIRED', top_candidates
