import uuid
import asyncio
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import pandas as pd

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.report import Report, Vulnerability, ReportsData, VulnerabilityRemediationInfo
from app.models.agency import Agency
from app.services.task_prioritization_service import calculate_priority
from app.services.task_scheduler_service import schedule_tasks
from app.services.prioritization_config import PRIORITY_CONFIG

router = APIRouter(prefix="/api/ml/prioritization", tags=["Task Prioritization"])

def get_time_threshold(time_range: str):
    from datetime import datetime, timezone, timedelta
    if not time_range or time_range == "ALL":
        return None
    now = datetime.now(timezone.utc)
    if time_range == "30_DAYS":
        return now - timedelta(days=30)
    elif time_range == "6_MONTHS":
        return now - timedelta(days=180)
    elif time_range == "1_YEAR":
        return now - timedelta(days=365)
    return None

# Simple in-memory cache
_CACHE = {}

def apply_filters(query, agency_id, report_id, time_range):
    if agency_id or report_id:
        query = query.join(Report, Vulnerability.report_id == Report.report_id)
        if agency_id:
            query = query.where(Report.agency_id == agency_id)
        if report_id:
            query = query.where(Report.report_id == report_id)
            
    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)
    return query

@router.get("")
async def get_prioritized_tasks(
    agency_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    time_range: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(
            Vulnerability.vuln_id,
            Vulnerability.vulnerability_title,
            Vulnerability.severity,
            Vulnerability.cvss_score,
            Vulnerability.status,
            Vulnerability.created_at,
            Vulnerability.affected_assets,
            Report.agency_id,
            Agency.agency_name,
            ReportsData.report_date,
            VulnerabilityRemediationInfo.estimated_effort,
            VulnerabilityRemediationInfo.required_teams,
            VulnerabilityRemediationInfo.depends_on
        )
        .select_from(Vulnerability)
        .outerjoin(Report, Vulnerability.report_id == Report.report_id)
        .outerjoin(Agency, Report.agency_id == Agency.agency_id)
        .outerjoin(ReportsData, Report.report_id == ReportsData.report_id)
        .outerjoin(VulnerabilityRemediationInfo, Vulnerability.vuln_id == VulnerabilityRemediationInfo.vuln_id)
        .where(Vulnerability.status.in_(['OPEN', 'IN_PROGRESS']))
    )

    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)
    if agency_id:
        query = query.where(Report.agency_id == agency_id)
    if report_id:
        query = query.where(Report.report_id == report_id)

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return {"data": [], "meta": {"total": 0, "strategy": "rule_based_v1"}}

    # Convert to Pandas
    data = []
    for r in rows:
        # Calculate agency avg cvss approximation if needed, or query it separately
        # Here we use 5.0 as a fallback if not calculated per agency
        agency_avg_cvss = 5.0
        
        data.append({
            'vuln_id': str(r.vuln_id),
            'title': r.vulnerability_title,
            'severity': r.severity.value if r.severity else None,
            'cvss_score': r.cvss_score,
            'status': r.status.value if r.status else None,
            'created_at': r.created_at,
            'affected_assets_count': len(r.affected_assets) if r.affected_assets else 0,
            'agency_id': str(r.agency_id) if r.agency_id else None,
            'agency_name': r.agency_name,
            'report_date': r.report_date,
            'estimated_effort': r.estimated_effort,
            'required_teams': r.required_teams,
            'depends_on': r.depends_on,
            'agency_avg_cvss': agency_avg_cvss
        })

    df = pd.DataFrame(data)
    
    # Calculate scores in background thread
    df = await asyncio.to_thread(calculate_priority, df)
    
    # Sort by priority desc
    df = df.sort_values(by=['priority_score', 'severity', 'created_at'], ascending=[False, False, True])
    
    tasks = df.to_dict(orient='records')
    
    # Schedule
    capacity = PRIORITY_CONFIG.get("resources", {})
    in_progress = {} # we could aggregate tasks where status=IN_PROGRESS and count teams
    
    tasks = await asyncio.to_thread(schedule_tasks, tasks, capacity, in_progress)
    
    # Paging
    total = len(tasks)
    start = (page - 1) * page_size
    end = start + page_size
    paged_tasks = tasks[start:end]
    
    # Coverage
    cov_due = 0 # No due dates
    cov_team = sum(1 for t in tasks if t.get('required_teams')) / max(total, 1)
    
    return {
        "data": paged_tasks,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "strategy": "rule_based_v1",
            "data_coverage": f"Due dates for 0% of tasks; team data for {int(cov_team*100)}%"
        }
    }
