# SMTYX-MC² Program Matrix

The research currently preserves three implementation snapshots.

| Program | Role | Main Strength | Main Limitation |
|---|---|---|---|
| **Codex Version v0.1** | rigorous baseline | fail-closed checks, framing, manifests, version/hash validation, cost accounting | manifest/envelope overhead is large |
| **AntyGravity Version v0.1** | rapid research lab | compact implementation, fast iteration, architectural exploration | several conceptual claims exceed what the code proves |
| **Reference Runtime v0.2** | current research reference | D index, compact packet, Smart Lorentz, TEXT_DICT/RLE/repeat experiments | exhaustive LAW evaluation does not scale |

## Codex Version v0.1

Use when studying:
- deterministic protocol boundaries;
- manifest semantics;
- fail-closed behavior;
- cross-process reproducibility;
- collision/version/hash tests;
- explicit cost accounting.

Snapshot: [SMTYX_MC2_Codex_Version_v0.1.zip](./programs/SMTYX_MC2_Codex_Version_v0.1.zip)

## AntyGravity Version v0.1

Use as:
- experimental branch;
- rapid LAW prototyping;
- conceptual testbed.

Treat `VISION_AND_AI_SYNERGY.md` as brainstorming/research direction, not verified runtime behavior.

Snapshot: [SMTYX_MC2_AntyGravity_Version_v0.1.zip](./programs/SMTYX_MC2_AntyGravity_Version_v0.1.zip)

## Reference Runtime v0.2

Current research reference for:
- registered LAW indices;
- compact MASS packet;
- Smart Lorentz selection;
- TEXT_DICT;
- RLE8;
- repeated-block LAW;
- honest fallback to IDENTITY;
- benchmark/cost experiments.

Snapshot: [SMTYX_MC2_Reference_v0.2.zip](./programs/SMTYX_MC2_Reference_v0.2.zip)

## Relationship

```text
Codex v0.1 ──┐
             ├── research findings ──► Reference v0.2
AntyGravity ─┘
```

A higher version number alone does not make a finding correct. Runtime evidence and reproducibility remain the deciding criteria.
