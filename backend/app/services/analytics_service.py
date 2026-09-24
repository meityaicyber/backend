from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, case, literal_column, text, cast, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Vulnerability, ReportsData, SeverityLevel, VulnStatus, Report


def apply_orm_filters(query, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None):
    from datetime import datetime, timedelta, timezone
    if report_id:
        query = query.where(Vulnerability.report_id == report_id)
    elif agency_id:
        query = query.join(Report, Vulnerability.report_id == Report.report_id).where(Report.agency_id == agency_id)
        
    if time_range and time_range != 'ALL':
        days = 0
        if time_range == '30_DAYS': days = 30
        elif time_range == '6_MONTHS': days = 180
        elif time_range == '1_YEAR': days = 365
        if days > 0:
            threshold = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(Vulnerability.created_at >= threshold)
            
    if severities:
        query = query.where(Vulnerability.severity.in_([SeverityLevel(s) for s in severities]))
        
    if statuses:
        query = query.where(Vulnerability.status.in_([VulnStatus(s) for s in statuses]))
        
    return query


async def get_summary(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> dict:
    """Get high-level vulnerability analytics summary."""
    # Total vulnerabilities
    total_query = select(func.count(Vulnerability.vuln_id))
    total_query = apply_orm_filters(total_query, agency_id, report_id, time_range, severities, statuses)
    total_result = await db.execute(total_query)
    total_vulnerabilities = total_result.scalar() or 0

    # Open vulnerabilities
    open_query = select(func.count(Vulnerability.vuln_id)).where(Vulnerability.status == VulnStatus.OPEN)
    open_query = apply_orm_filters(open_query, agency_id, report_id, time_range, severities, statuses)
    open_result = await db.execute(open_query)
    open_vulnerabilities = open_result.scalar() or 0

    # Closed vulnerabilities
    closed_query = select(func.count(Vulnerability.vuln_id)).where(Vulnerability.status == VulnStatus.CLOSED)
    closed_query = apply_orm_filters(closed_query, agency_id, report_id, time_range, severities, statuses)
    closed_result = await db.execute(closed_query)
    closed_vulnerabilities = closed_result.scalar() or 0

    # Average CVSS score
    avg_query = select(func.avg(Vulnerability.cvss_score)).where(Vulnerability.cvss_score.isnot(None))
    avg_query = apply_orm_filters(avg_query, agency_id, report_id, time_range, severities, statuses)
    avg_result = await db.execute(avg_query)
    avg_cvss = avg_result.scalar()
    avg_cvss_score = round(float(avg_cvss), 1) if avg_cvss is not None else None

    # Severity counts
    severity_counts = {}
    for level in SeverityLevel:
        count_query = select(func.count(Vulnerability.vuln_id)).where(Vulnerability.severity == level)
        count_query = apply_orm_filters(count_query, agency_id, report_id, time_range, severities, statuses)
        count_result = await db.execute(count_query)
        severity_counts[level.value] = count_result.scalar() or 0

    # Reports with vulnerabilities
    reports_query = select(func.count(func.distinct(Vulnerability.report_id)))
    reports_query = apply_orm_filters(reports_query, agency_id, report_id, time_range, severities, statuses)
    reports_result = await db.execute(reports_query)
    reports_with_vulns = reports_result.scalar() or 0

    return {
        "total_vulnerabilities": total_vulnerabilities,
        "open_vulnerabilities": open_vulnerabilities,
        "closed_vulnerabilities": closed_vulnerabilities,
        "avg_cvss_score": avg_cvss_score,
        "critical_count": severity_counts.get("CRITICAL", 0),
        "high_count": severity_counts.get("HIGH", 0),
        "medium_count": severity_counts.get("MEDIUM", 0),
        "low_count": severity_counts.get("LOW", 0),
        "informational_count": severity_counts.get("INFORMATIONAL", 0),
        "reports_with_vulns": reports_with_vulns,
    }


async def get_severity_distribution(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get vulnerability count per severity level."""
    query = select(
        cast(Vulnerability.severity, String).label("severity"),
        func.count(Vulnerability.vuln_id).label("count"),
    ).where(Vulnerability.severity.isnot(None))
    
    query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
    query = query.group_by(Vulnerability.severity).order_by(func.count(Vulnerability.vuln_id).desc())
    
    result = await db.execute(query)
    rows = result.all()

    # Ensure all severity levels appear, even with 0 count
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
    counts_map = {}
    for row in rows:
        val = getattr(row.severity, 'value', str(row.severity)).split('.')[-1].upper()
        counts_map[val] = row.count
    return [
        {"severity": s, "count": counts_map.get(s, 0)}
        for s in severity_order
    ]


async def get_status_distribution(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get vulnerability count per status."""
    query = select(
        cast(Vulnerability.status, String).label("status"),
        func.count(Vulnerability.vuln_id).label("count"),
    ).where(Vulnerability.status.isnot(None))

    query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
    query = query.group_by(Vulnerability.status).order_by(func.count(Vulnerability.vuln_id).desc())

    result = await db.execute(query)
    rows = result.all()

    # Ensure all statuses appear
    status_order = ["OPEN", "CLOSED", "ACCEPTED", "RISK_ACCEPTED", "IN_PROGRESS"]
    counts_map = {}
    for row in rows:
        val = getattr(row.status, 'value', str(row.status)).split('.')[-1].upper()
        counts_map[val] = row.count
    return [
        {"status": s, "count": counts_map.get(s, 0)}
        for s in status_order
    ]


async def get_cvss_distribution(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get CVSS score histogram buckets."""
    buckets = []
    ranges = [
        ("0-1", 0.0, 1.0),
        ("1-2", 1.0, 2.0),
        ("2-3", 2.0, 3.0),
        ("3-4", 3.0, 4.0),
        ("4-5", 4.0, 5.0),
        ("5-6", 5.0, 6.0),
        ("6-7", 6.0, 7.0),
        ("7-8", 7.0, 8.0),
        ("8-9", 8.0, 9.0),
        ("9-10", 9.0, 10.1),  # inclusive of 10.0
    ]

    for label, low, high in ranges:
        query = select(func.count(Vulnerability.vuln_id)).where(
            Vulnerability.cvss_score.isnot(None),
            Vulnerability.cvss_score >= low,
            Vulnerability.cvss_score < high,
        )
        query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
        result = await db.execute(query)
        count = result.scalar() or 0
        buckets.append({"range": label, "count": count})

    return buckets


async def get_category_breakdown(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get top 15 vulnerability categories by count."""
    query = select(
        Vulnerability.category,
        func.count(Vulnerability.vuln_id).label("count"),
    ).where(Vulnerability.category.isnot(None), Vulnerability.category != "")
    
    query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
    query = query.group_by(Vulnerability.category).order_by(func.count(Vulnerability.vuln_id).desc()).limit(15)

    result = await db.execute(query)
    rows = result.all()
    return [{"category": row.category, "count": row.count} for row in rows]


async def get_trend(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get vulnerability count by month (last 12 months) based on reports_data.report_date."""
    # Use raw SQL for date_trunc which is PostgreSQL specific
    base_sql = """
        SELECT
            to_char(date_trunc('month', rd.report_date), 'YYYY-MM') AS month,
            COUNT(v.vuln_id) AS count
        FROM vulnerabilities v
        JOIN reports_data rd ON v.report_id = rd.report_id
    """
    
    where_clauses = [
        "rd.report_date >= (CURRENT_DATE - INTERVAL '12 months')",
        "rd.report_date IS NOT NULL"
    ]
    params = {}
    
    if report_id:
        where_clauses.append("v.report_id = :report_id")
        params["report_id"] = str(report_id)
    elif agency_id:
        base_sql += " JOIN reports r ON v.report_id = r.report_id "
        where_clauses.append("r.agency_id = :agency_id")
        params["agency_id"] = str(agency_id)
        
    sql_query = base_sql + " WHERE " + " AND ".join(where_clauses) + """
        GROUP BY date_trunc('month', rd.report_date)
        ORDER BY date_trunc('month', rd.report_date)
    """

    result = await db.execute(text(sql_query), params)
    rows = result.all()
    return [{"month": row.month, "count": row.count} for row in rows]


async def get_top_cwe(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get top 10 CWE IDs by frequency (unnest the cwe_ids array)."""
    base_sql = """
        SELECT cwe, COUNT(*) AS count
        FROM vulnerabilities v, unnest(v.cwe_ids) AS cwe
    """
    
    where_clauses = ["v.cwe_ids IS NOT NULL"]
    params = {}
    
    if report_id:
        where_clauses.append("v.report_id = :report_id")
        params["report_id"] = str(report_id)
    elif agency_id:
        base_sql += " JOIN reports r ON v.report_id = r.report_id "
        where_clauses.append("r.agency_id = :agency_id")
        params["agency_id"] = str(agency_id)
        
    sql_query = base_sql + " WHERE " + " AND ".join(where_clauses) + """
        GROUP BY cwe
        ORDER BY count DESC
        LIMIT 10
    """
    
    result = await db.execute(text(sql_query), params)
    rows = result.all()
    return [{"cwe_id": row.cwe, "count": row.count} for row in rows]


async def get_top_cve(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get top 10 CVE IDs by frequency (unnest the cve_ids array)."""
    base_sql = """
        SELECT cve, COUNT(*) AS count
        FROM vulnerabilities v, unnest(v.cve_ids) AS cve
    """
    
    where_clauses = ["v.cve_ids IS NOT NULL"]
    params = {}
    
    if report_id:
        where_clauses.append("v.report_id = :report_id")
        params["report_id"] = str(report_id)
    elif agency_id:
        base_sql += " JOIN reports r ON v.report_id = r.report_id "
        where_clauses.append("r.agency_id = :agency_id")
        params["agency_id"] = str(agency_id)
        
    sql_query = base_sql + " WHERE " + " AND ".join(where_clauses) + """
        GROUP BY cve
        ORDER BY count DESC
        LIMIT 10
    """

    result = await db.execute(text(sql_query), params)
    rows = result.all()
    return [{"cve_id": row.cve, "count": row.count} for row in rows]


async def get_affected_assets(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get top 15 most-attacked assets (unnest the affected_assets array)."""
    base_sql = """
        SELECT asset, COUNT(*) AS count
        FROM vulnerabilities v, unnest(v.affected_assets) AS asset
    """
    
    where_clauses = ["v.affected_assets IS NOT NULL"]
    params = {}
    
    if report_id:
        where_clauses.append("v.report_id = :report_id")
        params["report_id"] = str(report_id)
    elif agency_id:
        base_sql += " JOIN reports r ON v.report_id = r.report_id "
        where_clauses.append("r.agency_id = :agency_id")
        params["agency_id"] = str(agency_id)
        
    sql_query = base_sql + " WHERE " + " AND ".join(where_clauses) + """
        GROUP BY asset
        ORDER BY count DESC
        LIMIT 15
    """

    result = await db.execute(text(sql_query), params)
    rows = result.all()
    return [{"asset": row.asset, "count": row.count} for row in rows]


async def get_new_vs_repeat(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get count of New vs Repeat findings."""
    query = select(
        Vulnerability.new_or_repeat,
        func.count(Vulnerability.vuln_id).label("count"),
    ).where(
        Vulnerability.new_or_repeat.isnot(None),
        Vulnerability.new_or_repeat != "",
    )

    query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
    query = query.group_by(Vulnerability.new_or_repeat).order_by(func.count(Vulnerability.vuln_id).desc())

    result = await db.execute(query)
    rows = result.all()
    return [{"type": row.new_or_repeat, "count": row.count} for row in rows]


async def get_recent_vulns(db: AsyncSession, agency_id: Optional[UUID] = None, report_id: Optional[UUID] = None, time_range: Optional[str] = None, severities: Optional[list] = None, statuses: Optional[list] = None) -> list:
    """Get the latest 10 vulnerabilities."""
    query = select(Vulnerability)
    query = apply_orm_filters(query, agency_id, report_id, time_range, severities, statuses)
    query = query.order_by(Vulnerability.created_at.desc()).limit(10)

    result = await db.execute(query)
    vulns = result.scalars().all()
    return [
        {
            "vuln_id": str(v.vuln_id),
            "report_id": str(v.report_id),
            "vulnerability_title": v.vulnerability_title,
            "severity": v.severity.value if v.severity else None,
            "status": v.status.value if v.status else None,
            "cvss_score": float(v.cvss_score) if v.cvss_score is not None else None,
            "category": v.category,
            "created_at": v.created_at.isoformat(),
        }
        for v in vulns
    ]
