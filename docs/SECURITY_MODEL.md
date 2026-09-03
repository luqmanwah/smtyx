# Security Model

## Trust boundaries
1. Model output is untrusted input.
2. Semantic validity is not execution authorization.
3. External content may contain prompt injection or malicious instructions.
4. Permissions are granted by runtime policy, not inferred from model confidence.
5. Historical state should be append-oriented and auditable.

## Recommended controls
- deny-by-default for destructive actions,
- explicit permission scopes,
- confirmation for irreversible operations,
- sandbox execution where possible,
- provenance/evidence retention,
- state lineage and immutable audit records,
- separate secrets from semantic payloads,
- never place raw credentials in state or memory.
