# SMTYX Protocol Specification v0.2

## 1. Purpose
SMTYX defines a vendor-neutral semantic language and protocol for exchanging meaning-bearing state between AI models, agents, tools, and runtimes.

## 2. Conformance language
The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

## 3. Required envelope fields
A conforming semantic state MUST include:
- `protocol`: `SMTYX`
- `protocol_version`
- `state_id`
- `trace_id`
- `source`
- `intent`
- `object`
- `status`
- `confidence`
- `payload`
- `evidence`
- `permissions`
- `ack`

`parent_state_id` and `destination` MAY be null.

## 4. Statuses
Normative statuses:
- `PROPOSED`
- `PARSED`
- `AMBIGUOUS`
- `VERIFIED`
- `FINAL`
- `CONFLICT`
- `DENIED`
- `FAILED`
- `STALE`

Terminal statuses are `FINAL`, `DENIED`, and `FAILED`. Implementations MAY create a new child state after a terminal state, but MUST NOT mutate historical state silently.

## 5. Acknowledgements
Normative ACK values:
- `ACK_RECEIVED`
- `ACK_PARSED`
- `ACK_SEMANTIC`
- `ACK_VERIFIED`
- `ACK_FINAL`

ACKs indicate processing milestones, not truth by themselves.

## 6. Confidence
`confidence` MUST be numeric in `[0.0, 1.0]`. Confidence is the sender's calibrated estimate, not a substitute for evidence or verification.

## 7. Lineage
Each derived state SHOULD include `parent_state_id`. Related states across one operation SHOULD share a `trace_id`.

## 8. Evidence and provenance
Evidence entries SHOULD identify a source using a URI, digest, reference ID, or equivalent stable locator when available. Implementations MUST NOT represent unsupported claims as verified evidence.

## 9. Permissions
Execution-affecting operations SHOULD declare required permissions before execution. A receiver MUST NOT infer permission merely from an AI-generated instruction.

## 10. Task graphs
A task graph is a directed acyclic graph. Nodes MAY depend on prior nodes. Cyclic task graphs are invalid.

## 11. Capability registry
Agents MAY advertise supported intents, object classes, tools, locality, latency, cost, and reliability. Selection algorithms are implementation-defined but SHOULD be observable.

## 12. Memory
SMTYX recognizes three portable memory classes:
- `EPISODIC`: what happened,
- `SEMANTIC`: what is known,
- `PROCEDURAL`: how a task is performed.

Memory assertions SHOULD record source states and verification status.

## 13. Learning lifecycle
A learning item MUST progress through explicit stages rather than silently altering core behavior:

`OBSERVATION → CANDIDATE → VERIFIED → ADOPTED | REJECTED`

Adoption into policy or procedure SHOULD require explicit approval unless a deployment has a documented auto-adoption policy.

## 14. Reasoning privacy
SMTYX does not require or standardize private chain-of-thought. Conforming systems SHOULD exchange concise rationale, evidence, state, and decisions sufficient for interoperability without exposing hidden reasoning traces.

## 15. Execution boundary
The semantic protocol is not an execution authorization system. Tool execution MUST be mediated by a runtime policy layer.

## 16. Versioning
Breaking semantic changes require a new protocol version. Historical state MUST retain its original version identifier.
