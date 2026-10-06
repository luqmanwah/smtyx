# SMTYX-MC² — Research Status v0.2

## Status

SMTYX-MC² v0.2 has moved from a pure architecture sketch to an executable reconstructive runtime experiment.

The current evidence supports **deterministic exact reconstruction under registered shared context**. It does not support a claim of universal compression.

## Confirmed by the Current Research

- LORENTZ and INVERSE can form an exact round-trip pair.
- MASS can carry a compact residual plus a registered LAW index.
- QUANTUM REALM can resolve deterministic LAW definitions.
- ENTANGLEMENT can represent LAW dependencies.
- REFERENCE FRAME can bind the runtime context required for reconstruction.
- INVARIANT can verify byte-identical reconstruction.
- LORENTZ can select among multiple LAW candidates and fall back to IDENTITY.
- Structured data in the tested set can produce a smaller MASS with TEXT_DICT.
- Already-compressed ZIP inputs correctly avoid false reduction claims and fall back to IDENTITY.

## Not Yet Proven

- universal or general-purpose superiority over mature compressors;
- scalable selection over tens of thousands of LAW nodes;
- streaming reconstruction for very large inputs;
- bounded-memory operation for multi-GB / multi-TB data;
- semantic reconstruction from highly abstract MASS;
- learned/probabilistic LAW generation compatible with exact-mode identity;
- formal proof of optimality for Smart Lorentz selection.

## Current Technical Model

For candidate LAW set `Q_F` in frame `F`:

```text
D* = argmin_D packet_size(D, X)
```

subject to:

```text
INVERSE_D(LORENTZ_D(X)) = X
```

The selected MASS is therefore the smallest valid packet among the evaluated deterministic LAW candidates, not an assertion of globally optimal information coding.

## Next Research Gate

The next architecture problem is LAW selection scalability.

Instead of evaluating every LAW:

```text
RAW -> try all D in QUANTUM REALM -> choose minimum
```

the v0.3 research direction introduces an **OBSERVER**:

```text
RAW -> OBSERVER -> candidate LAW subset -> LORENTZ -> MASS
```

OBSERVER may classify/select candidates, but exact-mode output remains governed by deterministic LAW execution and INVARIANT.
