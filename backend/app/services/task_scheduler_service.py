def schedule_tasks(tasks: list, capacity: dict, in_progress: dict):
    # tasks: list of dicts with 'vuln_id', 'priority_score', 'priority_level', 'required_teams', 'depends_on'
    
    # Calculate free capacity
    free = {team: max(0, cap - in_progress.get(team, 0)) for team, cap in capacity.items()}
    
    # Simple dependency tracking: assume open dependencies mean blocked
    # In a real system, we'd check if dependent tasks are also open. 
    # For now, if depends_on has items, we'll assume they are open.
    
    for task in tasks:
        if task.get('depends_on'):
            task['state'] = "BLOCKED"
            task['state_reason'] = "waiting on dependency"
        elif not task.get('required_teams'):
            task['state'] = "READY"
            task['state_reason'] = "resource info missing"
        elif all(free.get(t, 0) >= 1 for t in task['required_teams']):
            for t in task['required_teams']:
                free[t] -= 1
            task['state'] = "READY"
            task['state_reason'] = "ready to start"
        else:
            task['state'] = "WAITING_FOR_RESOURCE"
            short_teams = [t for t in task['required_teams'] if free.get(t, 0) < 1]
            task['state_reason'] = f"{short_teams[0]} has no free slot"
            
    # Assign queue positions (tasks are already sorted by priority)
    q_pos = 1
    for task in tasks:
        if task['state'] == 'WAITING_FOR_RESOURCE':
            task['queue_position'] = q_pos
            q_pos += 1
        else:
            task['queue_position'] = None
            
    return tasks
