13 — AI Architecture
Version: 1.0
Document Type: AI System Architecture & Prompt Design
Challenge: IBM AI Builders Challenge 2026 – Wildcard Challenge: Build Intelligent Systems for the Future of Work
Status: Draft

1. Purpose of This Document
This is the most judging-critical chapter. It defines exactly how IA TeamPilot uses IBM Granite (via watsonx) and LangChain: the chain design, the prompt templates, the input/output contracts, and the guardrails that keep the AI explainable and human-controlled — the core promise of Chapter 1's vision.

2. AI Design Philosophy (Recap and Operationalization)
As established in Chapter 10 (§2), the AI layer is deliberately narrow in scope:
The AI DOESThe AI DOES NOTGenerate natural-language justifications for scores computed by business rulesCompute the risk score or workload % itself (BR-4.1, BR-1.2 stay in Python)Reason over a pre-filtered, ranked list of candidates to pick/refine the final suggestionQuery the database directly or search the full user baseAnswer chat questions grounded in data explicitly passed to itApply any change to data automatically (BR-5.5)
This split exists specifically so that a failure or hallucination in the AI layer degrades the explanation quality, never the correctness of the underlying numbers — directly satisfying NFR-EXP-001 and NFR-REL-001.

3. Three AI Chains
IA TeamPilot implements exactly three LangChain chains, each with a single responsibility.
3.1 Chain 1 — Recommendation Justification Chain
Triggered by: RecommendationService (Chapter 11 §3) when BR-5.1 trigger conditions are met and at least one candidate passes BR-5.2/5.3 ranking.
Input contract (structured dict passed to the chain):
json{
  "overloaded_user": { "name": "David N.", "workload_pct": 135, "role": "Backend Developer" },
  "candidate": { "name": "Marie T.", "workload_pct": 55, "matching_skills": ["Django", "PostgreSQL"] },
  "task": { "title": "API Payment Integration", "estimated_hours": 12, "deadline": "2026-08-02" },
  "rule_context": {
    "candidate_rank_reason": "highest skill match, lowest workload",
    "confidence_tier": "HIGH"
  }
}
Prompt template (recommendation_prompt.txt):
You are an assistant explaining a project management recommendation.
You do NOT decide anything — the decision has already been made
by business rules. Your job is ONLY to explain it clearly in 2-3
sentences, in plain language a project manager can trust and verify.

Overloaded team member: {overloaded_user.name} ({overloaded_user.workload_pct}% capacity)
Candidate: {candidate.name} ({candidate.workload_pct}% capacity)
Matching skills: {candidate.matching_skills}
Task: {task.title} ({task.estimated_hours}h, due {task.deadline})
Why this candidate was ranked first: {rule_context.candidate_rank_reason}

Write a short, specific justification. Do not invent any data not
provided above. Do not suggest anything beyond this single reassignment.
Output contract (parsed, validated before saving to Recommendation.justification_text):
json{ "justification": "David is currently at 135% capacity while Marie has both matching Django/PostgreSQL skills and only 55% capacity, making her the clear candidate to take on the API Payment Integration task without becoming overloaded herself." }
Guardrail: if the response references a name, number, or skill not present in the input, the service layer rejects it and falls back to a rule-based template string (Section 6).

3.2 Chain 2 — Risk Explanation Chain
Triggered by: RiskScoreService whenever a new RiskScore is computed (BR-4.3).
Input contract:
json{
  "project_name": "CRM Redesign",
  "score": 82,
  "level": "CRITICAL",
  "factors": {
    "overload_factor": 0.6,
    "blocked_task_factor": 0.75,
    "deadline_proximity_factor": 0.4,
    "historical_velocity_factor": 0.3
  },
  "top_contributors": [
    "2 of 5 team members overloaded",
    "1 task blocked for 4 days (API integration)",
    "deadline in 6 days with 40h of work remaining"
  ]
}
Prompt template (risk_explanation_prompt.txt):
You are explaining WHY a project's risk score was calculated as it was.
The score itself is already computed — you must not change or
re-derive it. Explain the top contributing factors in plain
language, in priority order, in 2-4 sentences.

Project: {project_name}
Risk score: {score}% ({level})
Top contributing factors: {top_contributors}

Be concrete. Reference the specific factors above. Do not add
speculative causes not listed.
Output: saved directly to RiskScore.explanation_text (Chapter 9 §10), surfaced by RiskExplanation.jsx (Chapter 12 §2).

3.3 Chain 3 — Chat Assistant Chain
Triggered by: chat app (Chapter 11 §3) on a PM/Executive query (UC-06, UC-07 partially).
Input contract: the user's question plus a scoped data snapshot assembled server-side (never raw DB access by the chain itself):
json{
  "question": "Who is overloaded this week?",
  "scope": "project_id=uuid-1234",
  "data_snapshot": {
    "team_workloads": [
      { "name": "David N.", "workload_pct": 135 },
      { "name": "Marie T.", "workload_pct": 55 }
    ],
    "at_risk_projects": []
  }
}
Prompt template (chat_prompt.txt):
You are a project data assistant. Answer the user's question using
ONLY the data provided below. If the data doesn't contain the
answer, say so explicitly rather than guessing.

Data snapshot: {data_snapshot}

User question: {question}

Answer in 1-3 sentences, plain language, no markdown tables.
Guardrail (directly enforcing FR-CHAT-002 and UC-06's alternate flow): data_snapshot is assembled by the chat service using the same role-scoped queries as the dashboard (BR-7.1) — so even if a PM tried to ask about a project they don't manage, the snapshot passed to the chain simply would not contain that project's data. The AI cannot leak what it never received.

4. Why Granite + watsonx + LangChain (Not a Single Direct API Call)

LangChain's role here is intentionally modest: prompt templating, structured input/output handling, and keeping the three chains independently swappable/testable — not complex multi-agent orchestration, which would be over-engineering for three well-defined, single-purpose chains at this scope.
Granite via watsonx is used because it is the IBM-native model path required for the challenge's technology fit criterion (NFR-COMP-002), and its instruction-following on constrained, template-based prompts is well suited to this narrow "explain, don't decide" role.


5. Output Validation Layer
Every chain's raw response passes through a validation function before being persisted or shown to a user:
python# ai_engine/validators.py

def validate_recommendation_output(response: dict, input_context: dict) -> dict:
    # 1. Check required keys present (justification)
    # 2. Check no names/numbers appear that aren't in input_context
    # 3. Check length is within expected bounds (reject empty or runaway output)
    # Raise AIValidationError if any check fails
    ...
If validation fails, the calling service (Chapter 11 §3–4) uses the fallback path below rather than surfacing a broken or hallucinated response to the user.

6. Fallback Templates (NFR-REL-001 in Practice)
When the AI service is unavailable or a response fails validation, each chain has a deterministic fallback string, built directly from the same structured input (no AI needed):
ChainFallback ExampleRecommendation"{candidate.name} has matching skills and lower current workload ({candidate.workload_pct}%) than {overloaded_user.name} ({overloaded_user.workload_pct}%)."Risk Explanation"Risk level {level} ({score}%), driven primarily by: {top_contributors joined as a list}."Chat"AI assistant temporarily unavailable. Here is the raw data: {data_snapshot}."
This guarantees the UI never shows a blank state or an error where a judge expects to see the AI value proposition — a degraded-but-functional explanation is always available.

7. Prompt Versioning
Per NFR-MAINT-003, prompt files (ai_engine/prompts/*.txt) are plain text files under version control, not inline Python strings. Any prompt iteration during development is a single commit touching only that file — never mixed with logic changes — which also makes it easy to show prompt evolution in the GitHub history for the judges.

8. Cost & Latency Considerations

Chains are only invoked when trigger conditions are actually met (BR-5.1, BR-4.3 schedule) — not on every page load, keeping watsonx call volume proportional to actual events rather than UI traffic (also serves NFR-PERF-003's 8-second budget by avoiding chain calls on the hot dashboard-load path wherever a cached/last-known value is acceptable).
Chat (Chain 3) is the one on-demand, user-triggered chain, and is the most latency-sensitive from a UX perspective — hence the explicit loading-state requirement in NFR-PERF-003.


9. Traceability
ChainRelated FRRelated BRRelated NFRRecommendation JustificationFR-RECO-001–002BR-5.1–5.4NFR-EXP-001, NFR-SEC-004Risk ExplanationFR-RISK-003BR-4.1–4.2NFR-EXP-001Chat AssistantFR-CHAT-001–003BR-7.1NFR-SEC-004, NFR-PERF-003

End of Chapter 13