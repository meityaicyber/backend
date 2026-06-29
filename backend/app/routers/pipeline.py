"""
Pipeline Router
---------------
Proxy endpoint that downloads a report from storage,
forwards it to the AI Pipeline service, and returns the results.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from datetime import datetime, timezone
import httpx

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.report import ReportsData, Vulnerability, SeverityLevel, VulnStatus
from app.services import report_service
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Pipeline"])


@router.post("/{report_id}/run-pipeline")
async def run_pipeline(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run the AI pipeline on a report.
    Downloads the report file from SeaweedFS, forwards it to the
    AI Pipeline microservice, and returns the analysis results.
    """
    from app.utils.seaweedfs_utils import get_file_bytes

    # 1. Fetch the report record
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.storage or not report.storage.encrypted_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File storage record not found",
        )

    # 2. Download file from SeaweedFS
    object_name = report.storage.encrypted_file_path
    try:
        encrypted_data = get_file_bytes(object_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found in storage: {e}",
        )

    # 3. Decrypt if needed
    if report.storage.encryption_algorithm == "Fernet":
        from app.utils.encryption_utils import decrypt_file
        file_data = decrypt_file(encrypted_data)
    else:
        file_data = encrypted_data

    # 4. Forward to AI Pipeline service
    pipeline_url = f"{settings.AI_PIPELINE_URL}/run"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                pipeline_url,
                data={"report_id": str(report_id)},
                files={"file": (report.original_filename, file_data, report.mime_type)},
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract vulnerabilities to store them ONLY in the vulnerabilities table
            vulns = data.pop("vulnerabilities", [])
            
            # 5. Save results to DB
            # Upsert ReportsData (store everything EXCEPT vulnerabilities)
            existing_rd_res = await db.execute(select(ReportsData).where(ReportsData.report_id == report_id))
            rd = existing_rd_res.scalar_one_or_none()
            if rd:
                rd.data = data
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(rd, "data")
                rd.updated_at = datetime.now(timezone.utc)
            else:
                rd = ReportsData(
                    report_id=report_id,
                    data=data
                )
                db.add(rd)
            
            # Clear existing vulnerabilities
            await db.execute(delete(Vulnerability).where(Vulnerability.report_id == report_id))
            
            # Insert new vulnerabilities
            for v in vulns:
                severity_str = str(v.get("severity", "")).upper()
                severity_enum = None
                if severity_str == "CRITICAL": severity_enum = SeverityLevel.CRITICAL
                elif severity_str == "HIGH": severity_enum = SeverityLevel.HIGH
                elif severity_str == "MEDIUM": severity_enum = SeverityLevel.MEDIUM
                elif severity_str == "LOW": severity_enum = SeverityLevel.LOW
                elif severity_str == "INFORMATIONAL": severity_enum = SeverityLevel.INFORMATIONAL
                
                status_str = str(v.get("status", "")).upper()
                status_enum = VulnStatus.OPEN
                if status_str == "CLOSED": status_enum = VulnStatus.CLOSED
                elif status_str == "ACCEPTED": status_enum = VulnStatus.ACCEPTED
                elif status_str == "RISK ACCEPTED": status_enum = VulnStatus.RISK_ACCEPTED
                elif status_str == "IN PROGRESS": status_enum = VulnStatus.IN_PROGRESS
                
                vuln = Vulnerability(
                    report_id=report_id,
                    vulnerability_title=v.get("vulnerability_title", "Unknown Vulnerability"),
                    category=v.get("category"),
                    severity=severity_enum,
                    cvss_score=v.get("cvss_score"),
                    cve_ids=v.get("cve_ids", []),
                    cwe_ids=v.get("cwe_ids", []),
                    affected_assets=v.get("affected_assets", []),
                    status=status_enum,
                    new_or_repeat=v.get("new_or_repeat"),
                    revalidation_status=v.get("revalidation_status"),
                    detailed_observation=v.get("detailed_observation"),
                    description=v.get("description"),
                    impact=v.get("impact"),
                    recommendation=v.get("recommendation"),
                    proof_of_concept=v.get("proof_of_concept"),
                    reproduction_steps=v.get("reproduction_steps"),
                    reference=v.get("reference"),
                    meta_data=v.get("additional meta", {})
                )
                db.add(vuln)
                
            await db.commit()
            
            return data
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI Pipeline service timed out",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Pipeline service is not available",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Pipeline service returned an error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to communicate with AI Pipeline service: {str(e)}",
        )

@router.get("/{report_id}/results")
async def get_pipeline_results(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the AI pipeline results for a specific report from the database.
    """
    import os
    import json
    
    # 1. Fetch the report record to check authorization/existence
    report = await report_service.get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # 2. Fetch main results from ReportsData
    existing_rd_res = await db.execute(select(ReportsData).where(ReportsData.report_id == report_id))
    rd = existing_rd_res.scalar_one_or_none()
    
    if not rd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pipeline results found for this report",
        )
        
    data = dict(rd.data)
    
    # 3. Stitch vulnerabilities back in for the frontend API response
    vuln_res = await db.execute(select(Vulnerability).where(Vulnerability.report_id == report_id))
    vulns_db = vuln_res.scalars().all()
    
    vuln_list = []
    for v in vulns_db:
        vuln_list.append({
            "report id": str(v.report_id),
            "id": v.meta_data.get("ai_id", "") if isinstance(v.meta_data, dict) else "",
            "vulnerability_title": v.vulnerability_title,
            "category": v.category or "",
            "severity": v.severity.value if v.severity else "",
            "cvss_score": float(v.cvss_score) if v.cvss_score is not None else None,
            "cve_ids": v.cve_ids or [""],
            "cwe_ids": v.cwe_ids or [""],
            "affected_assets": v.affected_assets or [""],
            "status": v.status.value if v.status else "",
            "detailed_observation": v.detailed_observation or "",
            "description": v.description or "",
            "impact": v.impact or "",
            "recommendation": v.recommendation or "",
            "proof_of_concept": v.proof_of_concept or "",
            "reproduction_steps": v.reproduction_steps,
            "reference": v.reference or "",
            "new_or_repeat": v.new_or_repeat or "",
            "revalidation_status": v.revalidation_status,
            "additional meta": v.meta_data or {}
        })
    data["vulnerabilities"] = vuln_list
    
    # 4. Re-order keys exactly as masterjson structure
    master_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../masterjson strcture.json"))
    try:
        with open(master_path, 'r', encoding='utf-8') as f:
            master_json = json.load(f)
            
        def order_dict(data_dict, template_dict):
            ordered = {}
            for k in template_dict.keys():
                if k in data_dict:
                    if isinstance(data_dict[k], dict) and isinstance(template_dict[k], dict):
                        ordered[k] = order_dict(data_dict[k], template_dict[k])
                    elif isinstance(data_dict[k], list) and isinstance(template_dict[k], list) and len(template_dict[k]) > 0 and isinstance(template_dict[k][0], dict):
                        ordered_list = []
                        for item in data_dict[k]:
                            if isinstance(item, dict):
                                ordered_list.append(order_dict(item, template_dict[k][0]))
                            else:
                                ordered_list.append(item)
                        ordered[k] = ordered_list
                    else:
                        ordered[k] = data_dict[k]
            for k in data_dict.keys():
                if k not in ordered:
                    ordered[k] = data_dict[k]
            return ordered
            
        final_data = order_dict(data, master_json)
    except Exception as e:
        final_data = data

    return JSONResponse(content=final_data)
