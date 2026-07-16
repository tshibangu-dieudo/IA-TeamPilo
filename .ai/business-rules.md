# Business Rules (Condensed): IA TeamPilot

Full formulas and rationale: `docs/05_Business_Rules.md`. This file
is a quick-reference summary — always verify against the full
chapter before implementing.

## Workload
- Capacity default: 40h/week per user (configurable).
- Workload % = (sum of estimated effort of open tasks in sprint
  window) / (weekly capacity × sprint weeks) × 100.
- Bands: 0–60% Underloaded · 61–99% Balanced · 100–120% Overloaded ·
  >120% Critically Overloaded.
- Overload alert: triggers on entering Overloaded/Critically
  Overloaded; not retriggered within 24h unless workload rises
  another 15 percentage points.

## Task Rules
- Priority levels: Critical, High, Medium, Low.
- Auto-escalate priority by one level if due within 48h and not Done.
- Blocked status requires a reason field.
- Blocked >24h → flagged as a risk contributor, PM notified.
- Dependency not Done → dependent task flagged "Waiting on Dependency"
  (distinct from manually-set "Blocked").

## Project Risk Score (0–100%)
- Weighted composite: Overload (35%) + Blocked Tasks (30%) +
  Deadline Proximity (20%) + Historical Velocity (15%).
- Bands: 0–29 Low · 30–59 Moderate · 60–79 High · 80–100 Critical.
- Recalculated on relevant data change, or every 6 hours minimum.

## Recommendations
- Trigger requires: an overloaded member + an available teammate +
  a skill match on a reassignable task.
- Candidates ranked by: skill match → lowest workload → fewest
  blocked tasks.
- Confidence: High (exact skill match, resulting workload <80%) ·
  Medium (partial match, <100%) · Low (no ideal candidate).
- **Never applied automatically — requires explicit PM approval.**
  This is the single most important rule in the entire system.
- Rejected recommendations are not reissued for the same task/candidate
  pair within the same sprint.

## Access Control
| Role | Sees |
|---|---|
| Administrator | All org config data |
| Project Manager | Projects they own/manage |
| Team Member | Own tasks, team aggregate workload (not individuals) |
| Executive Manager | Read-only, all projects |

Scope violations return 404, not 403 (avoid leaking existence of
data the user shouldn't know about).