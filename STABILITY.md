# SMTYX stability status

## Current decision

SMTYX 0.2 remains the vendor-neutral core protocol.

**SMTYX-AOA/0.1** is the stable operational language profile for AOA while broader
SMTYX research continues.

This avoids falsely declaring every experimental SMTYX branch or byte representation
stable.

## Audited baseline

Repository audit on 19 September 2026 found:

- protocol specification v0.2 with normative envelope, lifecycle, lineage, evidence,
  permissions, memory, learning, execution boundary, and versioning rules;
- JSON Schema for semantic state v0.2;
- Python reference SDK with protocol/state tests;
- frozen raw-byte runtime 0.2.0 with its own design freeze and manifest;
- repository history preserving the initial semantic release and later frozen
  byte-matrix runtime as separate components;
- no GitHub Actions workflow/status on `main` at the time of audit.

The latest published byte-matrix commit records 44 runtime tests plus 10 existing
semantic SDK tests passing. Those are documented release results, not continuous CI.

## Stable surface for AOA

AOA may rely on:

- SMTYX 0.2 envelope fields;
- status/ACK lifecycle;
- lineage and trace IDs;
- evidence/provenance fields;
- permission declarations;
- conflict preservation;
- canonical JSON/digest behavior in the reference SDK;
- SMTYX-AOA/0.1 vocabulary and metadata contract.

## Experimental / not stable by this decision

The following remain separately versioned or experimental:

- byte-matrix compression efficiency;
- HLYX/STREAM/SMALL derivative formats outside the frozen repository baseline;
- future binary/wire encoding for semantic AOA states;
- adaptive vocabulary learning;
- automatic macro/grammar induction;
- automatic policy/tuning adoption;
- Pyxis implementation details;
- Spectator implementation details;
- model/tool adapters;
- physical transports and encryption profiles.

## Compatibility policy

- SMTYX protocol breaking semantics require a new SMTYX protocol version.
- AOA profile breaking semantics require a new AOA profile version.
- Additive AOA metadata MAY be introduced without changing `AOA/0.1` when old
  receivers can safely ignore it.
- Frozen byte-matrix 0.2.0 files are never rewritten in place.
- Historical states retain their original protocol/profile identifiers.

## Stability verification

GitHub CI should run:

1. root semantic SDK tests across supported Python versions;
2. AOA profile conformance tests;
3. frozen byte-matrix tests in its own working directory.

A release should not be described as verified merely because documentation says it
passed locally; CI and/or reproducible signed/hashed receipts should support the claim.
