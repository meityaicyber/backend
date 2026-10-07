import re

with open(r'C:\Main Project\Module\backend\backend\app\routers\ml_analytics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add timedelta
content = content.replace('from datetime import datetime, timezone', 'from datetime import datetime, timezone, timedelta')

helper_code = """
def get_time_threshold(time_range: str):
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
"""

content = content.replace('router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])', 'router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])\n' + helper_code)

# 1. Update forecast_trends
forecast_sig = """async def forecast_trends(
    months: int = Query(6, ge=1, le=12),
    agency_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    time_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):"""
content = re.sub(r'async def forecast_trends\([^)]+\):', forecast_sig, content)

forecast_query = """    query = select(ReportsData.report_date, func.count(Vulnerability.vuln_id).label("count")).select_from(ReportsData).join(Vulnerability, ReportsData.report_id == Vulnerability.report_id)
    if agency_id:
        query = query.join(Report, ReportsData.report_id == Report.report_id).where(Report.agency_id == agency_id)
    if report_id:
        query = query.where(ReportsData.report_id == report_id)
    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)
    query = query.group_by(ReportsData.report_date).order_by(ReportsData.report_date)"""
content = re.sub(r'    query = select\(ReportsData\.report_date.*?order_by\(ReportsData\.report_date\)', forecast_query, content)

# 2. Update clusters
clusters_sig = """async def regional_clusters(
    agency_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    time_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):"""
content = re.sub(r'async def regional_clusters\([^)]+\):', clusters_sig, content)

clusters_query = """    query = select(
        Agency.agency_id,
        Agency.agency_name,
        func.count(Report.report_id).label("total_reports"),
        func.avg(Vulnerability.cvss_score).label("avg_cvss"),
        func.count(Vulnerability.vuln_id).label("total_vulns"),
        func.sum(
            case(
                (Vulnerability.severity == SeverityLevel.CRITICAL, 1.0),
                else_=0.0
            )
        ).label("critical_vulns")
    ).select_from(Agency).outerjoin(Report, Agency.agency_id == Report.agency_id).outerjoin(Vulnerability, Report.report_id == Vulnerability.report_id)
    
    if agency_id:
        query = query.where(Agency.agency_id == agency_id)
    if report_id:
        query = query.where(Report.report_id == report_id)
    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)
        
    query = query.group_by(Agency.agency_id, Agency.agency_name)"""
content = re.sub(r'    query = select\(.*?\.group_by\(Agency\.agency_id, Agency\.agency_name\)', clusters_query, content, flags=re.DOTALL)


# 3. Update anomalies
anomalies_sig = """async def audit_score_anomalies(
    agency_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    time_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):"""
content = re.sub(r'async def audit_score_anomalies\([^)]+\):', anomalies_sig, content)

anomalies_query = """    query = select(Agency.agency_id, Agency.agency_name, Report.report_id, Vulnerability.cvss_score).select_from(Agency).outerjoin(Report, Agency.agency_id == Report.agency_id).outerjoin(Vulnerability, Report.report_id == Vulnerability.report_id)
    
    if agency_id:
        query = query.where(Agency.agency_id == agency_id)
    if report_id:
        query = query.where(Report.report_id == report_id)
    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)"""
content = re.sub(r'    query = select\(Agency\.agency_id.*?== Vulnerability\.report_id\)', anomalies_query, content)


# 4. Update prioritize
prioritize_sig = """async def task_prioritization(
    agency_id: Optional[uuid.UUID] = None,
    report_id: Optional[uuid.UUID] = None,
    time_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):"""
content = re.sub(r'async def task_prioritization\([^)]+\):', prioritize_sig, content)

prioritize_query = """    query = select(Vulnerability).where(Vulnerability.status == VulnStatus.OPEN)
    
    if agency_id or report_id:
        query = query.join(Report, Vulnerability.report_id == Report.report_id)
        if agency_id:
            query = query.where(Report.agency_id == agency_id)
        if report_id:
            query = query.where(Vulnerability.report_id == report_id)
            
    threshold = get_time_threshold(time_range)
    if threshold:
        query = query.where(Vulnerability.created_at >= threshold)
        
    query = query.order_by(Vulnerability.cvss_score.desc()).limit(1000)"""
content = re.sub(r'    query = \(\s*select\(Vulnerability\)\s*\.where\(Vulnerability\.status == VulnStatus\.OPEN\)\s*\.order_by\(Vulnerability\.cvss_score\.desc\(\)\)\s*\.limit\(1000\)\s*\)', prioritize_query, content, flags=re.DOTALL)


with open(r'C:\Main Project\Module\backend\backend\app\routers\ml_analytics.py', 'w', encoding='utf-8') as f:
    f.write(content)
