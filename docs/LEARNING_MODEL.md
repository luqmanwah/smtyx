# Controlled Learning Model

SMTYX treats learning as auditable state change, not hidden self-modification.

```text
Experience
   ↓
Observation
   ↓
Candidate Rule / Procedure
   ↓
Verification
   ↓
Adoption decision
   ├─ ADOPTED
   └─ REJECTED
```

A candidate should include:
- evidence/source state IDs,
- measured outcome,
- scope,
- confidence,
- rollback information when applicable.

Default reference behavior requires explicit approval for adoption. Deployments may define stricter rules.
