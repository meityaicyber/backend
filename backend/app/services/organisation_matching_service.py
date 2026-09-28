import re
import uuid
from typing import List, Tuple, Optional
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

class OrganisationMatchingService:
    @staticmethod
    async def match_agency(
        db: AsyncSession, extracted_name: str
    ) -> Tuple[Optional[uuid.UUID], str, List[dict]]:
        """
        Attempts to match the extracted ML name against the Agency master table.
        Returns:
            (matched_org_id, match_status, candidate_matches)
            
        match_status can be:
            'MATCHED' -> score >= 0.95 or exact/alias match
            'AGENCY_REVIEW_REQUIRED' -> score < 0.95
            
        candidate_matches: [{'org_id': uuid, 'name': str, 'score': float}] (top 3)
        """
        if not extracted_name:
            return None, 'AGENCY_REVIEW_REQUIRED', []

        norm_extracted = normalize_org_name(extracted_name)
        if not norm_extracted:
            return None, 'AGENCY_REVIEW_REQUIRED', []
            
        # Fetch all active empanelled agencies
        result = await db.execute(
            select(Agency).where(Agency.status == 'ACTIVE')
        )
        all_orgs = result.scalars().all()
        
        candidates = []
        
        for org in all_orgs:
            # We want to match against the agency_name or its normalized form
            org_norm_name = org.normalized_name or normalize_org_name(org.agency_name)
            
            # 1. Exact normalized match
            if norm_extracted == org_norm_name:
                candidates.append({
                    'agency_id': str(org.agency_id),
                    'name': org.agency_name,
                    'score': 1.0
                })
                continue
                
            # 2. Alias match
            alias_matched = False
            for alias in (org.aliases or []):
                if norm_extracted == normalize_org_name(alias):
                    candidates.append({
                        'agency_id': str(org.agency_id),
                        'name': org.agency_name,
                        'score': 1.0
                    })
                    alias_matched = True
                    break
            if alias_matched:
                continue
                
            # 3. Controlled fuzzy match
            score = calculate_similarity(norm_extracted, org_norm_name)
            candidates.append({
                'agency_id': str(org.agency_id),
                'name': org.agency_name,
                'score': score
            })
            
        # Sort candidates by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:3]
        
        if top_candidates and top_candidates[0]['score'] >= 0.95:
            return uuid.UUID(top_candidates[0]['agency_id']), 'MATCHED', top_candidates
            
        return None, 'AGENCY_REVIEW_REQUIRED', top_candidates
