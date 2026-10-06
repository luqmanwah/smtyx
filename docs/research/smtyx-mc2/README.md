# SMTYX-MC²

> ## **Small Mass. Massive Meaning.**
> **Encode less. Reconstruct more.**

**Status:** Research  
**Current research baseline:** v0.2  
**License:** Apache-2.0  
**Primary tag:** Research  
**Runtime family:** Node.js / ESM

SMTYX-MC² is an experimental reconstructive representation runtime built around deterministic registered laws, compact residual state, shared context, and exact reconstruction.

The physics vocabulary is architecture branding inspired by relativity and quantum mechanics. It is **not** a claim that SMTYX implements physical relativity, quantum mechanics, or quantum computation.

## E = MC² — Branding Model

```text
E  = ENERGY
M  = MASS
C² = CODE × CONTEXT
```

In SMTYX-MC²:

- **MASS** is the compact reconstructible residual carried by a packet.
- **CODE** is the registered deterministic LAW / D index.
- **CONTEXT** is the active REFERENCE FRAME + QUANTUM REALM.
- **ENERGY** is the realized reconstructed state.

The technical invariant remains:

```text
INVERSE(LORENTZ(X)) = X
```

or:

```text
Λ_F⁻¹(Λ_F(X)) = X
```

## Locked Vocabulary

| Runtime role | SMTYX-MC² term |
|---|---|
| Base runtime domain | **SPACETIME** |
| Active interpretation context | **REFERENCE FRAME** |
| Encode / collapse transform | **LORENTZ** |
| Decode / reconstruction transform | **INVERSE** |
| Compact residual state | **MASS** |
| Registered deterministic rule | **LAW / D** |
| Registry of registered LAW nodes | **QUANTUM REALM** |
| Dependency relations among LAW nodes | **ENTANGLEMENT** |
| Reconstructed full state | **ENERGY** |
| Exact preservation condition | **INVARIANT** |

## v0.2 Architecture

```text
                    SPACETIME
                        │
                 REFERENCE FRAME
                        │
                 QUANTUM REALM
                  ├─ LAW D0
                  ├─ LAW D1
                  ├─ LAW D2
                  ├─ LAW D3
                  └─ ENTANGLEMENT
                        │
RAW X ───── LORENTZ ──► MASS
                        │
                    D index
                        │
                        ▼
                     INVERSE
                        │
                        ▼
                      ENERGY
                        │
                     INVARIANT
```

A LAW is registered by stable identity/index and exact version semantics. A MASS packet obtains meaning relative to the selected LAW and REFERENCE FRAME.

## Current Research Result

The v0.2 integration test processed 7 files (~12.44 MB total) with exact invariant success for all 7. Structured JSON/HTML samples selected `TEXT_DICT`; already-compressed ZIP files and unsuitable small inputs correctly fell back to `IDENTITY`.

Current status:

```text
Exact reconstruction       PASS
Registered LAW index       PASS
REFERENCE FRAME binding    PASS
Auto LAW selection         PASS
TEXT_DICT reduction        PASS on tested structured inputs
IDENTITY fallback          PASS
Compact MASS packet        PASS
Large-file streaming       OPEN
LAW selection scalability  OPEN
Measured memory profiling  OPEN
Observer pre-selection     NEXT RESEARCH
```

## Three Research Implementations

Three implementation snapshots are preserved under [programs/](./programs/):

1. **Codex Version v0.1** — rigorous baseline with framing, manifests, fail-closed checks, and cost accounting.
2. **AntyGravity Version v0.1** — rapid experimental implementation and conceptual lab.
3. **Reference Runtime v0.2** — indexed LAW architecture, Smart Lorentz auto-selection, compact MASS packet, and benchmark suite.

They are research snapshots, not three competing canonical specifications.

## Research Documents

- [Research Status v0.2](./RESEARCH_STATUS_v0.2.md)
- [Architecture v0.2](./ARCHITECTURE_v0.2.md)
- [Program Matrix](./PROGRAM_MATRIX.md)
- [v0.2 Test Audit](./TEST_AUDIT_v0.2.md)
- [Observer Roadmap v0.3](./ROADMAP_v0.3_OBSERVER.md)
- [AntyGravity v0.2 process report](./reports/antigravity-v0.2-process-report.md)

## Information-Theory Guardrail

A small MASS does not make missing information disappear.

A valid reduction may rely on shared deterministic side information:

```text
MASS + CODE + CONTEXT -> ENERGY
```

Therefore research must distinguish:

- logical MASS payload;
- packet/framing overhead;
- shared LAW/realm cost;
- amortized shared context cost;
- actual end-to-end storage/transmission cost.

No claim of universal compression is made.

## License

The public research snapshot and program archives in this directory are published under the repository's **Apache License 2.0** unless a nested file explicitly states otherwise.
