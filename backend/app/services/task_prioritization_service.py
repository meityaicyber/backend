import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.services.prioritization_config import PRIORITY_CONFIG

def calculate_priority(df: pd.DataFrame, current_date=None) -> pd.DataFrame:
    if current_date is None:
        current_date = datetime.now(timezone.utc)
        
    config = PRIORITY_CONFIG
    
    # Exclude non-actionable statuses
    # We filter before calling this function, but just in case
    non_actionable = ['CLOSED', 'RESOLVED', 'CANCELLED']
    mask = ~df['status'].isin(non_actionable)
    df = df[mask].copy()
    
    if df.empty:
        return df

    def compute_row(row):
        factors = []
        
        # 1. IMPACT
        impact_components = []
        
        # base severity
        if pd.notnull(row.get('cvss_score')):
            base = float(row['cvss_score']) * 10
            impact_components.append(('base_severity', base, config['impact_weights']['base_severity'], 'cvss_score', False))
        elif pd.notnull(row.get('severity')):
            sev = str(row['severity'])
            base = config['severity_scores'].get(sev, 0)
            impact_components.append(('base_severity', base, config['impact_weights']['base_severity'], 'severity', True))
            
        # affected assets
        if pd.notnull(row.get('affected_assets_count')):
            count = float(row['affected_assets_count'])
            asset_score = min(count / 20.0 * 100, 100)
            impact_components.append(('affected_assets', asset_score, config['impact_weights']['affected_assets'], 'affected_assets', False))
            
        # agency risk (using avg_cvss)
        if pd.notnull(row.get('agency_avg_cvss')):
            arisk = min(float(row['agency_avg_cvss']) * 10, 100)
            impact_components.append(('agency_risk', arisk, config['impact_weights']['agency_risk'], 'agency_avg_cvss', False))
            
        if not impact_components:
            impact_score = 0
            impact_factors = []
        else:
            total_i_w = sum(w for _, _, w, _, _ in impact_components)
            impact_score = sum(val * (w / total_i_w) for _, val, w, _, _ in impact_components)
            impact_factors = [{"name": n, "raw_value": v, "contribution": round(v * (w / total_i_w), 1), "source": src, "estimated": est} for n, v, w, src, est in impact_components]

        # 2. URGENCY
        urgency_components = []
        
        # We don't have due dates in the DB.
        # Fallback: Urgency entirely based on age vs SLA
        sev_label = str(row.get('severity', 'MEDIUM'))
        sla_target = config['sla_target_days'].get(sev_label, 60)
        
        # age in days
        created_at = row.get('created_at')
        if pd.isnull(created_at):
            created_at = row.get('report_date')
            
        if pd.notnull(created_at):
            try:
                # ensure tz-aware
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                days_open = (current_date - created_at).days
            except:
                days_open = 0
            age_score = min((days_open / sla_target) * 100, 100)
            urgency_components.append(('age', age_score, config['urgency_weights']['age'], 'created_at/report_date', True))
            
        if not urgency_components:
            urgency_score = 0
            urgency_factors = []
        else:
            total_u_w = sum(w for _, _, w, _, _ in urgency_components)
            raw_urgency = sum(val * (w / total_u_w) for _, val, w, _, _ in urgency_components)
            
            # Status multiplier
            status = str(row.get('status', 'OPEN'))
            multiplier = config['status_multipliers'].get(status, 1.0)
            urgency_score = min(raw_urgency * multiplier, 100.0)
            
            urgency_factors = [{"name": n, "raw_value": v, "contribution": round(v * (w / total_u_w) * multiplier, 1), "source": src, "estimated": est} for n, v, w, src, est in urgency_components]

        # 3. RESOURCE
        effort_label = str(row.get('estimated_effort')) if pd.notnull(row.get('estimated_effort')) else None
        resource_score = None
        resource_factors = []
        if effort_label and effort_label in config['effort_scores']:
            resource_score = config['effort_scores'][effort_label]
            resource_factors = [{"name": "ease", "raw_value": resource_score, "contribution": resource_score, "source": "estimated_effort", "estimated": False}]

        # 4. FINAL SCORE
        available = {}
        if impact_score > 0:
            available['impact'] = (impact_score, config['weights']['impact'])
        if urgency_score > 0:
            available['urgency'] = (urgency_score, config['weights']['urgency'])
        if resource_score is not None:
            available['resource'] = (resource_score, config['weights']['resource'])
            
        if not available:
            final_score = 0.0
        else:
            total_main_w = sum(w for _, w in available.values())
            final_score = sum(s * (w / total_main_w) for s, w in available.values())

        # 5. LEVELS AND FLOOR
        level = "INFORMATIONAL"
        for l, thresh in config['thresholds'].items():
            if final_score >= thresh:
                level = l
                break
                
        notes = []
        if resource_score is None:
            notes.append("Resource component excluded: no effort data.")
            
        if sev_label == 'CRITICAL':
            floor_level = config['critical_floor_level']
            floor_thresh = config['thresholds'][floor_level]
            if final_score < floor_thresh:
                final_score = float(floor_thresh)
                level = floor_level
                notes.append(f"Raised to {floor_level} by the critical-severity rule.")

        return pd.Series({
            'impact_score': round(impact_score, 1),
            'urgency_score': round(urgency_score, 1),
            'resource_score': round(resource_score, 1) if resource_score is not None else None,
            'priority_score': round(final_score, 1),
            'priority_level': level,
            'explanation': {
                'impact_factors': impact_factors,
                'urgency_factors': urgency_factors,
                'resource_factors': resource_factors,
                'notes': notes
            }
        })

    results = df.apply(compute_row, axis=1)
    df = pd.concat([df, results], axis=1)
    return df
