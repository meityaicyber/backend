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


from app.schemas.analytics import VulnerabilityList, VulnerabilityItem

@router.get("/vulnerabilities", response_model=VulnerabilityList)
async def get_all_vulnerabilities(
    agency_id: Optional[UUID] = None,
    report_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all vulnerabilities for frontend filtering."""
    items = await analytics_service.get_all_vulnerabilities(db, agency_id, report_id)
    return VulnerabilityList(data=[VulnerabilityItem(**i) for i in items])
