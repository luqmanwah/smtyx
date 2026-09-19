# SMTYX-AOA Language Profile 0.1

**Status:** Stable operational profile for AOA interoperability  
**Base protocol:** SMTYX 0.2  
**Profile identifier:** `AOA/0.1`  
**Originator:** @luqmanwah  
**License:** Apache-2.0

## 1. Purpose

SMTYX-AOA/0.1 defines the stable semantic vocabulary used by AOA components to
exchange state, tasks, evidence, routing requests, results, tuning candidates,
session-control messages, and project context.

It is a profile of SMTYX 0.2, not a replacement protocol. The SMTYX core remains
vendor-neutral and may be used outside AOA.

This profile deliberately separates:

- **identity/state continuity** from model/account/runtime,
- **semantic messages** from transport,
- **routing decisions** from execution,
- **candidate learning/tuning** from canonical adoption,
- **historical evidence** from current operational state.

## 2. Stability boundary

The following are stable for AOA/0.1:

1. the SMTYX 0.2 required envelope fields;
2. the SMTYX 0.2 lifecycle/status and ACK semantics;
3. the AOA intent vocabulary in this document;
4. the AOA object vocabulary in this document;
5. the `metadata.aoa_profile = "AOA/0.1"` marker;
6. the AOA metadata field meanings defined below;
7. the rule that conflicting states are preserved rather than silently overwritten;
8. the rule that model/account/runtime identity is not canonical AOA identity;
9. the rule that execution remains permission/policy gated;
10. the rule that tuning and learning candidates do not silently become canonical state.

Breaking changes require a new AOA profile version.

## 3. Normative AOA intents

A conforming AOA/0.1 state MUST use one of these intents:

- `READ` — obtain information or a resource.
- `WRITE` — request creation or modification through a permission-gated runtime.
- `ANALYZE` — inspect and derive findings without implying execution.
- `VERIFY` — test a claim, artifact, state, or result.
- `ROUTE` — select a capable destination, model, tool, or workflow.
- `EXECUTE` — request bounded execution through a runtime/policy boundary.
- `REPORT` — return findings, evidence, progress, or outcome.
- `SYNC` — synchronize state or context between projections/nodes.
- `OBSERVE` — observe runtime/session/task state without changing it.
- `CONTROL` — control a live task/session through an authorized adapter.
- `PROPOSE` — submit a candidate state/delta/decision.
- `TUNE` — submit or inspect a state-tuning candidate.
- `HYDRATE` — obtain the minimum relevant shared context before work.
- `RESOLVE` — resolve a reference, capability, route, conflict, or dependency.

## 4. Normative AOA objects

A conforming AOA/0.1 state MUST use one of these objects:

- `STATE`
- `DELTA`
- `TASK`
- `SESSION`
- `PROJECTION`
- `TOOL`
- `DOCUMENT`
- `FILE`
- `PROJECT`
- `MEMORY`
- `CAPABILITY`
- `SOURCE`
- `REPORT`
- `TUNING`
- `RESULT`
- `CONTEXT`
- `POLICY`
- `CHECKPOINT`

Applications may carry domain-specific detail inside `payload`; they SHOULD NOT
invent new top-level object names when one of these stable objects is sufficient.

## 5. AOA metadata contract

The SMTYX core `metadata` object remains extensible. AOA/0.1 requires:

```json
{
  "metadata": {
    "aoa_profile": "AOA/0.1"
  }
}
```

The following fields are optional but stable when present:

| Field | Meaning |
|---|---|
| `domain` | Domain/work area used for context isolation and routing. |
| `project` | Stable project key, not a temporary display title. |
| `persona` | Operational persona/role hint; it does not redefine identity. |
| `projection_id` | Runtime/session projection that produced or consumes the state. |
| `authority` | Authority/source class for protected decisions. |
| `memory_scopes` | Memory namespaces requested for hydration. |
| `source_priority` | Ordered source classes preferred for verification. |
| `client_key` | Adapter/client identity for provenance, not canonical AI identity. |

Unknown metadata fields MAY be carried for forward compatibility.

## 6. Identity and projection rules

AOA/0.1 adopts these invariants:

```text
Account != Identity
Model   != Identity
Runtime != Identity
Projection != Canonical State
```

A projection MAY contribute observations, events, candidate deltas, reports, and
tuning proposals. A projection MUST NOT silently overwrite protected identity,
authority, root lineage, trusted checkpoints, or canonical protocol semantics.

## 7. Conflict and evidence

If two valid sources disagree:

1. preserve both states/claims;
2. keep source and evidence references;
3. create or report a `CONFLICT` state;
4. design verification when possible;
5. resolve by evidence and authority policy;
6. never erase disagreement merely to produce one answer.

`VERIFIED` means verification occurred under the declared procedure/evidence. It
does not mean universal truth.

## 8. Execution boundary

SMTYX-AOA is a semantic language, not an execution permission system.

`EXECUTE`, `WRITE`, and `CONTROL` requests MUST be evaluated by the receiving
runtime's permissions, policy, sandbox, or approval gate before external effects.

Generated instructions never imply authorization.

## 9. AOA Sync mapping

AOA-SYNC/0.1 can be represented with the stable profile as follows:

| AOA Sync operation | SMTYX intent | SMTYX object |
|---|---|---|
| hydrate | `HYDRATE` | `CONTEXT` |
| open projection | `CONTROL` | `PROJECTION` |
| development event | `REPORT` | `RESULT` |
| propose delta | `PROPOSE` | `DELTA` |
| propose tuning | `TUNE` | `TUNING` |
| tuning queue | `READ` | `TUNING` |
| lab report | `REPORT` | `REPORT` |
| close projection | `CONTROL` | `PROJECTION` |

This mapping is semantic. HTTP, MCP, database RPC, files, queues, or another
transport may carry the same SMTYX-AOA state.

## 10. Pyxis and Spectator

Pyxis may route tasks, capabilities, tools, and live-session operations.

Spectator is an operational Pyxis tool/control surface for session observation and
session control. Spectator is not an SMTYX protocol primitive and not an identity.

AOA/0.1 uses the ordinary stable objects `SESSION`, `PROJECTION`, `TASK`, and
`RESULT` for such interactions.

## 11. Byte-matrix runtime relationship

The frozen byte-matrix runtime under `runtimes/byte-matrix-0.2.0/` is a separate
representation/runtime component.

AOA/0.1 does not require byte-matrix encoding. AOA semantic conformance MUST NOT
depend on SMALL/LARGE compression claims, file-extension semantics, or a particular
binary transport.

A future binary/wire profile may encode AOA semantic states without changing their
meaning.

## 12. Minimal example

```json
{
  "protocol": "SMTYX",
  "protocol_version": "0.2",
  "state_id": "st_aoa_01",
  "parent_state_id": null,
  "trace_id": "tr_aoa_01",
  "source": {"kind": "human", "id": "luqman"},
  "destination": {"kind": "orchestrator", "id": "pyxis"},
  "intent": "ROUTE",
  "object": "TASK",
  "status": "PROPOSED",
  "confidence": 1.0,
  "payload": {
    "goal": "continue project work using the minimum relevant context"
  },
  "evidence": [],
  "permissions": [],
  "ack": ["ACK_RECEIVED"],
  "metadata": {
    "aoa_profile": "AOA/0.1",
    "domain": "professional",
    "project": "example-project",
    "persona": "notch"
  }
}
```

## 13. Conformance

A state conforms to SMTYX-AOA/0.1 when:

1. it conforms to SMTYX 0.2;
2. `metadata.aoa_profile` is exactly `AOA/0.1`;
3. its intent is in the AOA/0.1 intent set;
4. its object is in the AOA/0.1 object set;
5. optional AOA metadata fields, when present, use the types defined by the schema.

Reference validation is provided by `smtyx.validate_aoa_state`.
