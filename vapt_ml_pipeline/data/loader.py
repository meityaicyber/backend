import os
import json
import glob
import pandas as pd
from datetime import datetime

def load_reports(dir_path: str) -> list[dict]:
    """Load all JSON reports in the given directory (from report_to_json outputs)."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        return []

    reports = []
    skipped_log = []
    
    for fp in glob.glob(os.path.join(dir_path, "*.json")):
        # Skip meta or schema files
        if fp.endswith(".meta.json") or fp.endswith("master_schema.json"):
            continue
            
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Check for standard report_to_json root keys
            if "report_meta" not in data or "executive_summary" not in data:
                skipped_log.append(f"{fp}: Missing 'report_meta' or 'executive_summary' keys.")
                continue
                
            reports.append(data)
        except Exception as e:
            skipped_log.append(f"{fp}: Error reading file: {e}")
            
    if skipped_log:
        output_dir = os.path.join(os.path.dirname(dir_path), "..", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "skipped_reports.log"), "w") as f:
            f.write("\n".join(skipped_log))
            
    return reports

def build_dataframes(reports: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flatten standardized reports into reports_df and findings_df for the ML pipeline."""
    reports_data = []
    findings_data = []
    
    def parse_date(date_str):
        if not date_str: return None
        try: return pd.to_datetime(date_str)
        except: return None
        
    for r in reports:
        meta = r.get("report_meta", {})
        doc_control = r.get("document_control", {})
        exec_sum = r.get("executive_summary", {})
        scope = r.get("engagement_scope", {})
        timeline = r.get("audit_timeline", {})
        methodology = r.get("methodology", {})
        
        # In master_schema, detailed_observations holds the findings
        vulns = r.get("detailed_observations", [])
        
        report_id = meta.get("report_id") or doc_control.get("document_id") or f"report_{hash(json.dumps(r))}"
        
        test_start = parse_date(timeline.get("assessment_start_date"))
        test_end = parse_date(timeline.get("assessment_end_date"))
        testing_duration_days = (test_end - test_start).days if pd.notnull(test_start) and pd.notnull(test_end) else 1
        
        assets = scope.get("assets", [])
        assets_tested_count = max(1, len(assets)) # Prevent div by zero
        
        # Build mapping for finding level criticality joining
        asset_crit_map = {}
        for a in assets:
            crit = a.get("criticality", "Medium")
            if a.get("asset_description"): asset_crit_map[str(a.get("asset_description")).lower()] = crit
            if a.get("url"): asset_crit_map[str(a.get("url")).lower()] = crit
            if a.get("public_ip"): asset_crit_map[str(a.get("public_ip")).lower()] = crit
            if a.get("internal_ip"): asset_crit_map[str(a.get("internal_ip")).lower()] = crit
            
        repeat_count = sum(1 for v in vulns if str(v.get("new_or_repeat")).lower() == "repeat")
        repeat_ratio = repeat_count / max(1, len(vulns))
        
        total_vulns = int(exec_sum.get("total_findings") or len(vulns))
        
        sev_counts = exec_sum.get("severity_count", {})
        crit_count = int(sev_counts.get("critical") or 0)
        
        reports_data.append({
            "report_id": report_id,
            "org": "Unknown", # Organization is not explicitly in master_schema unless inferred
            "audit_type": meta.get("audit_type", "Unknown"),
            "report_type": meta.get("report_type", "Unknown"),
            "release_date": parse_date(meta.get("report_release_date") or doc_control.get("release_date")),
            "test_start": test_start,
            "test_end": test_end,
            "testing_duration_days": testing_duration_days,
            "auditing_organization": "Unknown",
            "standards_referenced_count": len(methodology.get("standards_referred", [])),
            "tools_used_count": len(r.get("tools_used", [])),
            "assets_tested_count": assets_tested_count,
            "total_vulns": total_vulns,
            "critical_count": crit_count,
            "high_count": int(sev_counts.get("high") or 0),
            "medium_count": int(sev_counts.get("medium") or 0),
            "low_count": int(sev_counts.get("low") or 0),
            "info_count": 0, # master schema does not have informational severity
            "summary_text": exec_sum.get("narrative", ""),
            "repeat_ratio": repeat_ratio,
            "total_vulns_per_asset": total_vulns / assets_tested_count,
            "critical_count_per_asset": crit_count / assets_tested_count
        })
        
        for v in vulns:
            cvss_raw = v.get("cvss_score")
            try: cvss_float = float(cvss_raw) if cvss_raw is not None else None
            except ValueError: cvss_float = None
                
            affected = v.get("affected_asset", [])
            if not isinstance(affected, list):
                affected = [affected] if affected else []
                
            # Map structured criticality from scope.assets_tested
            finding_crit = "Medium"
            for a in affected:
                c = asset_crit_map.get(str(a).lower())
                if c:
                    finding_crit = c
                    if str(c).lower() == "high": break # Highest takes precedence
                        
            findings_data.append({
                "report_id": report_id,
                "finding_id": v.get("finding_id", ""),
                "title": v.get("title", ""),
                "category": v.get("cwe", [""])[0] if v.get("cwe") else "Unknown",
                "severity": v.get("severity"),
                "cvss_score": cvss_float,
                "cvss_raw": cvss_raw,
                "cve_ids": v.get("cve_id", []),
                "cwe_ids": v.get("cwe", []),
                "affected_assets": affected,
                "asset_criticality": finding_crit,
                "status": v.get("status"),
                "new_or_repeat": v.get("new_or_repeat"),
                "description": v.get("observation_description", ""),
                "detailed_observation": v.get("observation_description", ""),
                "impact": v.get("impact", ""),
                "recommendation": v.get("recommendation", ""),
                "proof_of_concept": v.get("proof_of_concept"),
                "revalidation_status": "Unknown",
                "report_type": meta.get("report_type", "Unknown")
            })
            
    return pd.DataFrame(reports_data) if reports_data else pd.DataFrame(), pd.DataFrame(findings_data) if findings_data else pd.DataFrame()
