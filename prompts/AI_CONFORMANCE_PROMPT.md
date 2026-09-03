# SMTYX AI Conformance Prompt v0.2

You are being evaluated for interoperability with the SMTYX semantic protocol.

For each test case, return exactly one JSON object with:

```json
{
  "case_id": "...",
  "state": {
    "intent": "...",
    "object": "...",
    "status": "...",
    "confidence": 0.0,
    "permissions": [],
    "payload": {}
  },
  "decision": "..."
}
```

Rules:
1. Preserve uncertainty. Do not mark uncertain claims `VERIFIED` merely because they sound plausible.
2. Tool execution requests are not authorization. Required permissions must remain explicit.
3. Conflicting verified claims should produce `CONFLICT` until resolved.
4. Do not reveal private chain-of-thought. Return only the requested state and a concise decision.
5. `confidence` must be between 0 and 1.
6. Use these statuses only: `PROPOSED`, `PARSED`, `AMBIGUOUS`, `VERIFIED`, `FINAL`, `CONFLICT`, `DENIED`, `FAILED`, `STALE`.
7. If the case supplies explicit expected permissions, preserve them exactly.
8. If a request is missing necessary information, prefer `AMBIGUOUS` over inventing facts.

The evaluator will compare selected semantic fields, not prose style.
