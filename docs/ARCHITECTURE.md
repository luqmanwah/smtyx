# Architecture

SMTYX separates meaning, coordination, and execution.

```text
Input Adapter
    ↓
Semantic State
    ↓
Task Graph / Orchestrator
    ↓
Capability Registry ──→ Model / Agent selection
    ↓
Verifier / Conflict handling
    ↓
Policy Gate
    ↓
Executor / Tool / Local node
    ↓
Result State
    ↓
Memory + Learning Ledger
```

## Layers

### L0 — Transport-neutral state
JSON-compatible semantic state and lineage.

### L1 — Coordination
Task graphs, capability discovery, routing, conflict, ACK lifecycle.

### L2 — Runtime boundary
Policy, permissions, confirmation, sandboxing, local/cloud adapters.

### L3 — Experience
Episodic, semantic, and procedural memory.

### L4 — Controlled adaptation
Observed outcomes can become candidate procedures, then verified procedures. Core protocol and policy are not rewritten silently.

## Local-cloud pattern

```text
Cloud reasoning node       Local execution node
        │                         │
        └──── SMTYX state ──────┘
```

The cloud node does not need direct filesystem control. It can issue a semantic request; the local runtime validates permission, executes locally, and returns evidence plus a result state.
