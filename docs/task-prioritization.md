# Task Prioritization and Scheduling

This module highlights pending vulnerabilities demanding immediate attention using a rule-based prioritization algorithm and a resource-aware scheduler. It optimizes task scheduling by considering urgency, potential impact, and resource constraints.

## How a score is made
Each open vulnerability receives a final priority score from 0 to 100 based on three components:
1. **Impact (50%)**: Derived from the base severity (CVSS score) and affected assets.
2. **Urgency (35%)**: Derived from the age of the vulnerability compared against target SLAs for its severity level.
3. **Resource (15%)**: Based on the estimated remediation effort (LOW, MEDIUM, HIGH).

Missing data gracefully degrades the calculation. For example, if no effort data is available, the resource component is excluded, and the weights for impact and urgency scale up proportionally.

### Safety Floor
Regardless of age or effort, an open vulnerability mapped as "CRITICAL" severity will never drop below a "HIGH" priority score.

## How the scheduler decides
The scheduler evaluates tasks in descending priority order. It allocates available team slots (defined in configuration) to tasks.
- If a task's dependencies are open, it is marked `BLOCKED`.
- If the required teams have free capacity, it is marked `READY` and consumes a slot.
- If teams are busy, it is marked `WAITING_FOR_RESOURCE`.

## Configuration
Settings are located in `app/services/prioritization_config.py`.
- **Weights & Thresholds:** Determine the balance between urgency, impact, and effort, as well as level boundaries (e.g. `> 80` is CRITICAL).
- **Resources:** Defines team capacities (e.g., `{"security_team": 2}`).

*Note: The weights, SLA targets, and effort scores currently implemented are engineering defaults and need sign-off/calibration from CERT-In or project leads. Team capacities are placeholders.*

## Missing Data & Assumptions
Currently, the database lacks historical status tracking (`first_seen`), exact due dates, and effort/team mappings. 
- Age is estimated using the database `created_at` timestamp.
- A new table `VulnerabilityRemediationInfo` has been created to store effort and team data, but currently has no data. Therefore, the scheduler will mark tasks as `READY` but flag them as "resource info missing."

## Running the module locally
**Backend:**
```bash
# In the backend directory
pip install -r requirements.txt
python -m pytest scripts/test_prioritization.py
uvicorn app.main:app --reload
```

**Frontend:**
```bash
# In the frontend directory
npm install
npm start
```

*The module is accessible via the "Task Prioritization" widget on the ML Analytics Dashboard.*
