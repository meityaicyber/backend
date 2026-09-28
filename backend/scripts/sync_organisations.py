import asyncio
import json
import os
import sys
import argparse
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.agency import Agency
from app.services.organisation_matching_service import normalize_org_name
from sqlalchemy import select

async def sync_organisations(file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        print("Expected a JSON list of organisations.")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Agency))
        existing_agencies = result.scalars().all()
        
        existing_map = {a.agency_name: a for a in existing_agencies}
        existing_serial_map = {a.empanelment_number: a for a in existing_agencies if a.empanelment_number}
        
        seen_serials = set()
        
        for item in data:
            serial_no = str(item.get('certin_serial_no', ''))
            official_name = item.get('official_name', '')
            aliases = item.get('aliases', [])
            
            if not official_name:
                continue
                
            seen_serials.add(serial_no)
            
            agency = existing_serial_map.get(serial_no)
            if not agency:
                agency = existing_map.get(official_name)
                
            norm_name = normalize_org_name(official_name)
            
            if agency:
                # Update existing
                if agency.agency_name != official_name:
                    print(f"INFO: Renaming '{agency.agency_name}' to '{official_name}' (Serial: {serial_no})")
                    agency.agency_name = official_name
                
                agency.normalized_name = norm_name
                agency.aliases = aliases
                agency.empanelment_number = serial_no
                if agency.status != 'ACTIVE':
                    print(f"INFO: Reactivating '{official_name}'")
                    agency.status = 'ACTIVE'
            else:
                # Add new
                print(f"INFO: Adding new Agency '{official_name}'")
                new_agency = Agency(
                    agency_code=f"CERT-IN-{serial_no}",
                    agency_name=official_name,
                    agency_type='CERT_IN_EMPANELLED',
                    cert_in_empanelled=True,
                    empanelment_number=serial_no,
                    normalized_name=norm_name,
                    aliases=aliases,
                    status='ACTIVE',
                    contact_person="Auto Generated",
                    contact_email="auto@generated.com"
                )
                db.add(new_agency)
                
        # Handle removed (set to inactive)
        for agency in existing_agencies:
            if agency.agency_type == 'CERT_IN_EMPANELLED' and agency.empanelment_number and agency.empanelment_number not in seen_serials:
                if agency.status == 'ACTIVE':
                    print(f"INFO: Marking '{agency.agency_name}' as inactive (Removed from master)")
                    agency.status = 'INACTIVE'
                    
        await db.commit()
        print("Sync complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync CERT-In Agencies Master List")
    parser.add_argument("--file", required=True, help="Path to JSON file containing the master list")
    args = parser.parse_args()
    
    asyncio.run(sync_organisations(args.file))
