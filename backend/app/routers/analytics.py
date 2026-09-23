from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import analytics_service
from app.schemas.analytics import (
    AnalyticsSummary,
    SeverityDistribution,
    SeverityItem,
    StatusDistribution,
    StatusItem,
    CvssDistribution,
    CvssBucket,
    CategoryBreakdown,
    CategoryItem,
    VulnTrend,
    TrendItem,
    TopCwe,
    CweItem,
    TopCve,
    CveItem,
    AffectedAssets,
    AssetItem,
    NewVsRepeat,
    NewVsRepeatItem,
    RecentVulns,
    RecentVuln,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level vulnerability analytics summary."""
    data = await analytics_service.get_summary(db, agency_id, report_id)
    return AnalyticsSummary(**data)


@router.get("/severity-distribution", response_model=SeverityDistribution)
async def get_severity_distribution(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vulnerability count per severity level."""
    items = await analytics_service.get_severity_distribution(db, agency_id, report_id)
    return SeverityDistribution(data=[SeverityItem(**i) for i in items])


@router.get("/status-distribution", response_model=StatusDistribution)
async def get_status_distribution(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vulnerability count per status."""
    items = await analytics_service.get_status_distribution(db, agency_id, report_id)
    return StatusDistribution(data=[StatusItem(**i) for i in items])


@router.get("/cvss-distribution", response_model=CvssDistribution)
async def get_cvss_distribution(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get CVSS score histogram buckets."""
    items = await analytics_service.get_cvss_distribution(db, agency_id, report_id)
    return CvssDistribution(data=[CvssBucket(**i) for i in items])


@router.get("/category-breakdown", response_model=CategoryBreakdown)
async def get_category_breakdown(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top vulnerability categories by count."""
    items = await analytics_service.get_category_breakdown(db, agency_id, report_id)
    return CategoryBreakdown(data=[CategoryItem(**i) for i in items])


@router.get("/trend", response_model=VulnTrend)
async def get_trend(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vulnerability count by month (last 12 months)."""
    items = await analytics_service.get_trend(db, agency_id, report_id)
    return VulnTrend(data=[TrendItem(**i) for i in items])


@router.get("/top-cwe", response_model=TopCwe)
async def get_top_cwe(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top 10 CWE IDs by frequency."""
    items = await analytics_service.get_top_cwe(db, agency_id, report_id)
    return TopCwe(data=[CweItem(**i) for i in items])


@router.get("/top-cve", response_model=TopCve)
async def get_top_cve(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top 10 CVE IDs by frequency."""
    items = await analytics_service.get_top_cve(db, agency_id, report_id)
    return TopCve(data=[CveItem(**i) for i in items])


@router.get("/affected-assets", response_model=AffectedAssets)
async def get_affected_assets(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top most-attacked assets."""
    items = await analytics_service.get_affected_assets(db, agency_id, report_id)
    return AffectedAssets(data=[AssetItem(**i) for i in items])


@router.get("/new-vs-repeat", response_model=NewVsRepeat)
async def get_new_vs_repeat(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of New vs Repeat findings."""
    items = await analytics_service.get_new_vs_repeat(db, agency_id, report_id)
    return NewVsRepeat(data=[NewVsRepeatItem(**i) for i in items])


@router.get("/recent-vulns", response_model=RecentVulns)
async def get_recent_vulns(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest 10 vulnerabilities."""
    items = await analytics_service.get_recent_vulns(db, agency_id, report_id)
    return RecentVulns(data=[RecentVuln(**i) for i in items])
@router.get("/vulnerabilities-raw")
async def get_all_vulnerabilities_raw(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.report import Vulnerability, Report

    query = select(Vulnerability, Report.agency_id).join(Report, Vulnerability.report_id == Report.report_id)
    if report_id:
        query = query.where(Vulnerability.report_id == report_id)
    if agency_id:
        query = query.where(Report.agency_id == agency_id)
        
    result = await db.execute(query)
    rows = result.all()
    
    data = []
    for vuln, ag_id in rows:
        data.append({
            "id": str(vuln.vuln_id),
            "title": vuln.vulnerability_title,
            "severity": vuln.severity.value if vuln.severity else None,
            "status": vuln.status.value if vuln.status else None,
            "cvss": float(vuln.cvss_score) if vuln.cvss_score is not None else None,
            "date": vuln.created_at.isoformat(),
            "category": vuln.category,
            "cwe": vuln.cwe_ids[0] if vuln.cwe_ids and len(vuln.cwe_ids) > 0 else None,
            "cve": vuln.cve_ids[0] if vuln.cve_ids and len(vuln.cve_ids) > 0 else None,
            "asset": vuln.affected_assets[0] if vuln.affected_assets and len(vuln.affected_assets) > 0 else None,
            "new_or_repeat": vuln.new_or_repeat,
            "reportId": str(vuln.report_id),
            "agencyId": str(ag_id) if ag_id else None
        })
    return data
