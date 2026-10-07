import pandas as pd
from datetime import datetime, timezone, timedelta
from app.services.task_prioritization_service import calculate_priority

def test_prioritization():
    now = datetime.now(timezone.utc)
    
    # Task A: Critical, open 40 days, effort HIGH
    # Task B: Low, open 10 days, effort LOW
    # Task C: High, open 15 days, no effort
    
    data = [
        {
            'vuln_id': '1',
            'severity': 'CRITICAL',
            'created_at': now - timedelta(days=40),
            'estimated_effort': 'HIGH',
            'status': 'OPEN'
        },
        {
            'vuln_id': '2',
            'severity': 'LOW',
            'created_at': now - timedelta(days=10),
            'estimated_effort': 'LOW',
            'status': 'OPEN'
        },
        {
            'vuln_id': '3',
            'severity': 'HIGH',
            'created_at': now - timedelta(days=15),
            'estimated_effort': None,
            'status': 'OPEN'
        }
    ]
    df = pd.DataFrame(data)
    result = calculate_priority(df, current_date=now)
    
    res_a = result.iloc[0]
    res_b = result.iloc[1]
    res_c = result.iloc[2]
    
    print(f"Task A Score: {res_a['priority_score']} - {res_a['priority_level']}")
    print(f"Task B Score: {res_b['priority_score']} - {res_b['priority_level']}")
    print(f"Task C Score: {res_c['priority_score']} - {res_c['priority_level']}")
    
    # Check levels and floor
    assert res_a['priority_level'] == 'CRITICAL', "Task A should be CRITICAL"
    assert res_b['priority_level'] == 'LOW' or res_b['priority_level'] == 'INFORMATIONAL', "Task B should be LOW"
    assert res_c['priority_level'] == 'HIGH', "Task C should be HIGH"
    
if __name__ == '__main__':
    test_prioritization()
    print('All prioritization tests passed.')
