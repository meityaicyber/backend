import asyncio
import time
import uuid
import os
import sys

# Add backend to path so we can import from app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import AsyncSessionLocal
from app.models.report import Report
from app.services.agency_detection_service import AgencyDetectionService
from app.services.organisation_matching_service import OrganisationMatchingService
from app.utils.simhash_utils import extract_pages_from_bytes

async def run_benchmark():
    file_path = "test_reports_v2/Audit_Report_0017_KPMG_India_Pvt_Ltd.pdf"
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    print("Measuring First-page extraction time...")
    t0 = time.time()
    pages_text = extract_pages_from_bytes(file_bytes, ".pdf")
    t1 = time.time()
    print(f"Extraction Time: {(t1 - t0)*1000:.2f} ms")

    print("Measuring Lightweight Agency Detection time...")
    t0 = time.time()
    detection = AgencyDetectionService.extract_agency(pages_text)
    t1 = time.time()
    print(f"Detection Time: {(t1 - t0)*1000:.2f} ms")
    print(f"Detection Result: {detection}")

    print("Measuring In-memory organisation matching time...")
    async with AsyncSessionLocal() as db:
        await OrganisationMatchingService.load_orgs(db)
        
        t0 = time.time()
        res = await OrganisationMatchingService.match_agency(db, "KPMG", "HIGH")
        t1 = time.time()
        print(f"Matching Time: {(t1 - t0)*1000:.2f} ms")
        print(f"Matching Result: {res}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
