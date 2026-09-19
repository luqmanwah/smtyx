# SMTYX

> **AOA stable language profile:** [SMTYX-AOA/0.1](docs/AOA_LANGUAGE_PROFILE.md) defines the
> stable operational vocabulary used by AOA while SMTYX research continues. See
> [STABILITY.md](STABILITY.md). The SMTYX 0.2 core and frozen byte-matrix 0.2.0 baseline
> remain unchanged.

> **Frozen byte-matrix runtime 0.2.0:** [source, exact reconstruction, and tests](runtimes/byte-matrix-0.2.0/).
> This separately runnable component adds SMALL fingerprints, LARGE hierarchy, and
> lossless `.smtyx` file reconstruction. See the [runtime guide](runtimes/README.md).
> The semantic protocol/reference SDK below remains unchanged.

**Semantic Language and Protocol for Intelligent Systems**

SMTYX is an open, model-agnostic semantic language, protocol, and reference SDK for exchanging **meaning,
state, evidence, permissions, task relationships, and verification status** between
AI models, agents, tools, and local/cloud runtimes.

> Created by **Luqmanwah** · 2026 · Apache-2.0

SMTYX is not a foundation model. It is an interoperability layer: models may
change, but the semantic contract can remain stable.

## Identity

**SMTYX** is a coined project name inspired by **semantics**, **syntax**, and **semiotics**. The project pronunciation is **“semiotics.”** The protocol focuses on machine-readable meaning rather than provider-specific prompt wording.

Project site: **https://smtyx.io**

## Why SMTYX

Natural-language agent-to-agent messaging is flexible but difficult to validate.
SMTYX adds a machine-checkable semantic layer without requiring a specific LLM,
provider, transport, or programming language.

```text
Human / Application
        │
        ▼
 Semantic State / Envelope
        │
 ┌──────┼────────┬──────────┐
 ▼      ▼        ▼          ▼
GPT   Claude   Gemini    Local Models
 │      │        │          │
 └──────┴────────┴─────┬────┘
                       ▼
                 Orchestrator
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Memory       Verifier      Tools
          │                         │
          └──── Experience ─────────┘
                       │
                       ▼
                Learning Ledger
```

## Core principles

1. **State over conversation** — durable semantic state is the coordination unit.
2. **Meaning over vendor syntax** — adapters translate provider-specific formats.
3. **Lineage by default** — every important state can point to its parent and trace.
4. **Evidence is explicit** — claims can carry provenance/evidence references.
5. **Reasoning is separated from execution** — tools require policy evaluation.
6. **Uncertainty is representable** — `AMBIGUOUS`, `CONFLICT`, and confidence are first-class.
7. **Learning is controlled** — experience cannot silently rewrite protocol or policy.
8. **Local and cloud are peers** — both communicate through the same semantic contract.

## Minimal semantic state

```json
{
  "protocol": "SMTYX",
  "protocol_version": "0.2",
  "state_id": "st_01",
  "parent_state_id": null,
  "trace_id": "tr_01",
  "source": {"kind": "human", "id": "user"},
  "destination": {"kind": "agent", "id": "reviewer"},
  "intent": "ANALYZE",
  "object": "DOCUMENT",
  "status": "PROPOSED",
  "confidence": 1.0,
  "payload": {},
  "evidence": [],
  "permissions": [],
  "ack": ["ACK_RECEIVED"]
}
```

## Experimental interchange conventions

```text
Protocol identifier: SMTYX
Package namespace:    smtyx
Project site:         https://smtyx.io
Optional file suffix: .smx
JSON media type:      application/smtyx+json
```

The `.smx` suffix and media type are project conventions in v0.2, not registered
standards. See `docs/IDENTITY.md`.

## Status lifecycle

```text
PROPOSED → PARSED → VERIFIED → FINAL
              │          │
              ├→ AMBIGUOUS
              ├→ CONFLICT
              ├→ DENIED
              ├→ FAILED
              └→ STALE
```

No implementation is required to expose hidden chain-of-thought. SMTYX exchanges
**decisions, state, evidence, confidence, and externally useful rationale**, not private
reasoning traces.

## Quick start

```python
from smtyx import SemanticState, Capability, CapabilityRegistry, SemanticOrchestrator

registry = CapabilityRegistry()
registry.register(Capability(
    agent_id="doc-reviewer",
    intents={"ANALYZE", "VERIFY"},
    objects={"DOCUMENT"},
    reliability=0.92,
))

orchestrator = SemanticOrchestrator(registry=registry)
state = SemanticState.create(
    source={"kind": "human", "id": "user"},
    intent="ANALYZE",
    object_type="DOCUMENT",
)

print(orchestrator.route(state))
```

## Repository map

```text
smtyx/              Python reference SDK
schemas/              Vendor-neutral JSON Schemas
docs/                 Architecture, identity, and protocol documents
benchmarks/            AI interoperability/conformance cases
prompts/               Prompt to test external AI systems
scripts/               Local conformance scoring tools
examples/              Runnable examples
tests/                 Reference implementation tests
legacy/aivocab_v0_1/   Preserved original experiment
```

## Test many AI systems

1. Give an AI the contents of `prompts/AI_CONFORMANCE_PROMPT.md`.
2. Give it cases from `benchmarks/conformance_cases.jsonl`.
3. Save its JSONL answers.
4. Score them:

```bash
python scripts/score_model_outputs.py answers.jsonl
```

This intentionally requires no OpenAI, Anthropic, Google, or other vendor API.

## Scope

SMTYX v0.2 defines:
- semantic state/envelope,
- lifecycle and acknowledgements,
- state lineage and trace IDs,
- task graph primitives,
- capability advertisement and selection,
- memory record types,
- controlled learning lifecycle,
- execution-policy boundary,
- interoperability test format.

SMTYX v0.2 does **not** define:
- a foundation model,
- hidden reasoning representation,
- a universal ontology,
- autonomous permission escalation,
- silent self-modification,
- provider-specific transport.

## License and ownership

Copyright © 2026 **Luqmanwah**.

Licensed under the Apache License, Version 2.0. The license permits open-source use,
modification, and distribution under its terms; it does not transfer ownership of the
original copyright. See `LICENSE`, `NOTICE`, and `AUTHORS.md`.

## Project status

**Alpha / protocol research.** The contract is intentionally small enough to test,
criticize, and evolve through interoperability experiments.
