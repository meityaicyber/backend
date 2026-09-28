import uuid
import httpx
from typing import Tuple, Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.organisation_matching_service import OrganisationMatchingService


class Objective1Service:
    @staticmethod
    async def extract_and_match_agency(
        db: AsyncSession,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "application/pdf"
    ) -> Tuple[Optional[str], Optional[uuid.UUID], str, List[dict]]:
        """
        Calls the Objective 1 ML pipeline to extract the agency name,
        and then matches it against the master list.
        
        Returns:
            (extracted_name, matched_agency_id, match_status, candidate_matches)
        """
        pipeline_url = f"{settings.AI_PIPELINE_URL}/run"
        
        # We generate a dummy report_id since this might be run before a Report record is created
        dummy_report_id = str(uuid.uuid4())
        
        try:
            # We use a relatively long timeout since ML inference on PDFs can be slow
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    pipeline_url,
                    data={"report_id": dummy_report_id},
                    files={"file": (filename, file_bytes, mime_type)},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException:
            raise RuntimeError("Objective 1 ML Pipeline timed out")
        except httpx.ConnectError:
            raise RuntimeError("Objective 1 ML Pipeline service is unavailable")
        except Exception as e:
            raise RuntimeError(f"Objective 1 ML Pipeline failed: {str(e)}")
            
        metadata = data.get("metadata", {})
        # Depending on the report context, we might want organization_audited or auditing_organization
        # Let's extract auditing_organization as primary for CERT-In
        extracted_name = metadata.get("auditing_organization")
        if not extracted_name:
            extracted_name = metadata.get("organization_audited", "")
            
        if not extracted_name:
            return None, None, 'AGENCY_NOT_IDENTIFIED', []
            
        # Call the matching service
        matched_agency_id, match_status, candidates = await OrganisationMatchingService.match_agency(
            db, extracted_name
        )
        
        return extracted_name, matched_agency_id, match_status, candidates
