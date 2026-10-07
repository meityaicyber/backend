# Task Prioritization: Phase 1 Findings

This document outlines the findings from the repository analysis for the Task Prioritization module (Phase 1). No code or database changes have been made.

## 1. Confirmation of Existing Features (What the team believes)

*   **Backend:** Confirmed. Python/FastAPI is used. Analytics endpoints are in `app/routers/ml_analytics.py` (`/api/ml/forecast`, `/api/ml/severity-assessment`, `/api/ml/clusters`, `/api/ml/anomalies`).
*   **Data access:** Confirmed. `ReportsData`, `Report`, and `Vulnerability` models are used. They are accessed via SQLAlchemy ORM.
*   **Dates:** Confirmed. `ReportsData.report_date` is used for groupings in forecasts.
*   **Severity:** Confirmed. CVSS scores exist (`cvss_score`). "Critical" is defined simply via Enum matching (`Vulnerability.severity == SeverityLevel.CRITICAL`).
*   **Text fields:** Confirmed. `vulnerability_title`, `description`, `impact`, `recommendation`, etc. exist in the `Vulnerability` table.
*   **Agency features:** Confirmed. Aggregations like `total_reports`, `avg_cvss`, and `severity_density` are calculated dynamically via SQLAlchemy `func` and `case` statements in the existing clustering/anomaly endpoints.
*   **Frontend:** Confirmed. `MLAnalyticsDashboardPage.jsx` uses `react-grid-layout`, Recharts, `GlassTooltip`, and global state filters (Time Range, Agency, File/Report) passed dynamically to API calls.

## 2. Important Discoveries (What the team did not know)

1.  **Status:** The `status` field **DOES EXIST** in the `Vulnerability` table. It uses an Enum (`VulnStatus`) with the following values: `OPEN`, `CLOSED`, `ACCEPTED`, `RISK_ACCEPTED`, `IN_PROGRESS`. We can definitively tell which tasks are pending.
2.  **Dates:** 
    *   There is a `created_at` (DateTime of DB insertion) and `updated_at`.
    *   There is **NO** `first_seen`, `due_date`, or `sla` field in the database.
    *   *Result:* Age will be estimated from `created_at` or `ReportsData.report_date`.
3.  **Effort, team, dependencies:** **NONE** of these exist in the current schema. There is no `estimated_effort`, `required_team`, or `depends_on`.
4.  **Other impact inputs:**
    *   `cvss_score` and `severity` exist.
    *   `affected_assets` exists as an `ARRAY(Text)`.
    *   `exploitability`, `asset_criticality`, `data_sensitivity`, and `business_impact` **DO NOT EXIST**.
    *   Audit score does not explicitly exist on the `Agency` model, so we will rely on `avg_cvss` and `severity_density` for agency risk.
5.  **Definition of "Critical":** It is defined explicitly via the `SeverityLevel` Enum, accessed as `Vulnerability.severity == SeverityLevel.CRITICAL`.
6.  **Backend Structure:** 
    *   Routers are in `app/routers/`. Services are in `app/services/`.
    *   DB sessions use `async_session` dependency via `get_db`.
    *   Async offload is handled via `asyncio.to_thread` (as seen in the severity assessment tool).
    *   Migrations use Alembic (`alembic/versions/`).
    *   No standard `tests/` directory (tests currently exist as scripts in `scripts/`).
7.  **Auth:** Protected via JWT (`HTTPBearer`). User is extracted using the `get_current_user` dependency from `app/dependencies.py`.
8.  **Frontend Structure:** Layouts are managed by `react-grid-layout` and cached in `localStorage` (`mlVisibleWidgets`, `mlLayouts`). Global filters trigger a `useEffect` that appends URL parameters (`agency_id`, `time_range`) to `api.get` calls.
9.  **Data Volume:** Unable to query exact volume counts directly due to local database connection block in the test script, but previous implementations cap processing at 500 records to prevent OOM, implying a potentially large dataset. 

## 3. Field Mapping Table

| Concept | Source (table.column) | Exists? | Notes |
|---|---|---|---|
| Severity label | `vulnerabilities.severity` | Yes | Enum (`CRITICAL`, `HIGH`, etc.) |
| CVSS score | `vulnerabilities.cvss_score` | Yes | `Numeric(3, 1)` |
| Exploitability | N/A | No | Will be dropped from weighting |
| Asset criticality | N/A | No | Will be dropped from weighting |
| Affected assets | `vulnerabilities.affected_assets` | Yes | `ARRAY(Text)` - Can use array length |
| Data sensitivity | N/A | No | Will be dropped from weighting |
| First seen / created | `vulnerabilities.created_at` | Yes | DB insertion timestamp |
| Report date | `reports_data.report_date` | Yes | Available via JOIN |
| Due date / SLA | N/A | No | Will fall back to severity targets |
| Status | `vulnerabilities.status` | Yes | Enum (`OPEN`, `IN_PROGRESS`, etc.) |
| Required team / owner | N/A | No | Requires new table/fields |
| Remediation effort | N/A | No | Requires new table/fields |
| Dependencies | N/A | No | Requires new table/fields |

## 4. Proposals & Open Questions for Approval

**Proposal:**
We proceed with Phase 2 (Config, scoring service) using the fields that exist. For the scheduler (Phase 4), since team and effort data do *not* exist, we will create the permitted additive schema extension (a `vulnerability_remediation_info` table holding `estimated_effort`, `required_teams`, and `depends_on`).

**Open Questions for the Project Lead:**
1. Since `first_seen` doesn't exist, we will use `created_at` (DB insertion) or `report_date`. Is it acceptable to prioritize `created_at`?
2. Are the default weights, SLA targets, and bands outlined in the plan acceptable, or does CERT-In have its own timelines?
3. For the missing effort/team/dependencies, we will create the additive table. Who will populate it, or should it remain empty initially (flagged as "READY - resource info missing")?
4. Are team capacities global or per agency?
5. Should the Time Range filter apply to prioritization, or should pending tasks always show regardless of report date?
6. If scores must be stored in the future, how often should they be refreshed (e.g., nightly cron job)?

**Status:** Awaiting human review before proceeding to Phase 2.
