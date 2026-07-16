
15 — UI/UX Design
Version: 1.0
Document Type: UI/UX Wireframe Specification
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This document describes, screen by screen, the layout and content of IA TeamPilot's key interfaces — detailed enough to build from directly, without needing a separate Figma file for the MVP. Each screen maps back to a persona (Chapter 3) and the components defined in Chapter 12.

2. Design Principles (Applied From Chapter 1 §9)

Transparency first: every AI-driven number (workload %, risk score) is always shown alongside its plain-language explanation — never a bare number with no context.
One primary action per screen: e.g., the Recommendation Inbox's main action is Accept/Reject — nothing competes with it visually.
Color consistency: workload/risk color bands (Chapter 5, Chapter 12 §7) are used identically across every screen — orange always means "Overloaded," never reused for anything else.


3. Screen: PM Dashboard (/dashboard)
Primary persona: Alice (Project Manager)
┌──────────────────────────────────────────────────────────┐
│  TeamPilot AI          [🔔 3]  [Alice Kamana ▾]            │
├──────────────────────────────────────────────────────────┤
│  My Projects (3)                                            │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ │
│  │ CRM Redesign     │ │ Mobile App v2    │ │ API Gateway      │ │
│  │ 🔴 CRITICAL 82%  │ │ 🟢 LOW 18%       │ │ 🟠 HIGH 64%      │ │
│  └────────────────┘ └────────────────┘ └────────────────┘ │
│                                                                │
│  Team Workload                     Pending Recommendations   │
│  ┌───────────────────────────┐    ┌───────────────────────┐ │
│  │ David N.   ████████████ 135%│    │ 🟢 HIGH confidence      │ │
│  │ Marie T.   █████ 55%        │    │ Reassign "API Payment" │ │
│  │ Jean P.    ███████ 72%      │    │ David → Marie            │ │
│  └───────────────────────────┘    │ [Accept] [Reject]        │ │
│                                     └───────────────────────┘ │
└──────────────────────────────────────────────────────────┘
Content requirements:

Project cards sorted by descending risk score (highest risk first — surfaces what needs attention).
Workload bars use BR-1.3 color bands exactly.
Recommendation preview shows justification on hover/click (not truncated to the point of losing meaning, per NFR-USE-002).


4. Screen: Recommendation Inbox (/recommendations)
Primary persona: Alice (Project Manager) — this is the centerpiece screen for the demo (Chapter 12 §8).
┌──────────────────────────────────────────────────────────┐
│  Recommendations                                             │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐   │
│  │ Confidence: HIGH                                        │   │
│  │                                                            │   │
│  │ Task: API Payment Integration (12h, due Aug 2)           │   │
│  │ Currently: David N. (135% capacity)                      │   │
│  │ Suggested: Marie T. (55% capacity, matches: Django, PostgreSQL) │   │
│  │                                                            │   │
│  │ "David is currently at 135% capacity while Marie has      │   │
│  │  both matching Django/PostgreSQL skills and only 55%      │   │
│  │  capacity, making her the clear candidate..."             │   │
│  │                                                            │   │
│  │           [ ✓ Accept ]      [ ✗ Reject ]                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                                │
│  Skill Gap Alert (no valid candidate found):                  │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ⚠ "Frontend Polish" task has no assignee with          │   │
│  │   matching React skills currently available.            │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
Interaction detail: Accept triggers an inline confirmation state ("Reassigned to Marie T. ✓") before the card disappears from the list — this avoids the jarring "recommendation just vanished" feeling and gives the PM a moment to see the result of their decision (relevant since a live demo needs this visible feedback loop).

5. Screen: Task Board (/projects/{id}/tasks)
Primary personas: David (Team Member), Alice (PM)
┌──────────────────────────────────────────────────────────┐
│  CRM Redesign — Task Board                                   │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  To Do        │  In Progress  │  Blocked      │  Done             │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│ [Task card]   │ [Task card]   │ [Task card 🔴]│ [Task card ✓]     │
│ [Task card]   │ [Task card]   │  Blocked 26h  │                     │
│               │               │  "Waiting on  │                     │
│               │               │   API creds"  │                     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
Content requirements:

Blocked column cards show elapsed blocked time; cards blocked >24h get a distinct red border (matches BR-3.2 escalation logic).
Team Member view is filtered to their own tasks by default; PM view shows the full board.
Status change is drag-and-drop or a dropdown — either is acceptable for MVP; drag-and-drop is nicer for the demo video but not a hard requirement.


6. Screen: Executive Dashboard (/dashboard/executive)
Primary persona: Grace (Executive Manager)
┌──────────────────────────────────────────────────────────┐
│  Portfolio Overview                     [Filter: Team ▾] [Risk ▾]│
├──────────────────────────────────────────────────────────┤
│  Projects Ranked by Risk                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🔴 CRITICAL 82%   CRM Redesign         Backend Squad     │   │
│  │ 🟠 HIGH     64%   API Gateway          Backend Squad     │   │
│  │ 🟢 LOW      18%   Mobile App v2        Mobile Squad       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                                │
│  Workload Balance Trend (last 4 weeks)                        │
│  [ line chart: avg team workload % over time ]                │
└──────────────────────────────────────────────────────────┘
Content requirement: clicking a project row expands the risk explanation inline (reuses RiskExplanation.jsx from Chapter 12), so Grace never needs to navigate away to understand why a project is flagged.

7. Screen: Chat Panel (/chat)
Primary personas: Alice, Grace
┌──────────────────────────────────────────────────────────┐
│  Ask TeamPilot AI                                             │
├──────────────────────────────────────────────────────────┤
│  You: Who is overloaded this week?                            │
│                                                                │
│  TeamPilot: David N. is currently overloaded at 135%          │
│  capacity; no one else on this project exceeds 80%.           │
│                                                                │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Type a question about your project...      [Send]  │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
Content requirement: a "Suggested questions" row above the input (e.g., "Who is overloaded?", "What's at risk?") reduces blank-page friction for a first-time judge trying the feature live.

8. Screen: Team/Skill Management (/admin/teams)
Primary persona: Samuel (Administrator)
┌──────────────────────────────────────────────────────────┐
│  Team: Backend Squad                    Data completeness: 87%│
├──────────────────────────────────────────────────────────┤
│  Member          Skills                        Capacity      │
│  David N.        Django, PostgreSQL             40h/week      │
│  Marie T.        Django, PostgreSQL, React      40h/week      │
│  Jean P.         DevOps                         [⚠ no skills] │
│                                                                │
│  [+ Add Member]                                                │
└──────────────────────────────────────────────────────────┘
Content requirement: the data-completeness indicator (FR-TEAM-005) is visible at the top of the screen, not buried, since incomplete skill data directly degrades recommendation quality (BR-5.2) — this screen is where Samuel is meant to notice and fix that.

9. Responsive Behavior
Per NFR-USE-003, layouts collapse to a single column below ~1024px (tablet breakpoint); the task board's four columns become horizontally scrollable rather than stacked, to preserve the Kanban mental model.

10. Screen-to-Chapter Traceability
ScreenPersonasRelated ChaptersPM DashboardAlice7, 9, 12Recommendation InboxAlice6, 13Task BoardDavid, Alice5, 6Executive DashboardGrace6, 9Chat PanelAlice, Grace8, 13Team/Skill ManagementSamuel2, 4

End of Chapter 15