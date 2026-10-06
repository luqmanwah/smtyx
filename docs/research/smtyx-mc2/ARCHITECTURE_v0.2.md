# SMTYX-MC² Architecture v0.2

## 1. Runtime Topology

```text
SPACETIME
└── REFERENCE FRAME
    ├── QUANTUM REALM
    │   ├── LAW D0
    │   ├── LAW D1
    │   ├── LAW D2
    │   └── ENTANGLEMENT
    ├── LORENTZ
    ├── MASS
    ├── INVERSE
    └── INVARIANT
```

## 2. D as Registered Index

v0.2 sharpens the original D concept:

```text
D0 -> IDENTITY
D1 -> RLE8
D2 -> REPEAT_BLOCK
D3 -> TOY_ALPHA2
D4 -> TEXT_DICT
...
```

The exact mapping is runtime/profile specific and must be versioned/fingerprinted.

> MASS does not need to carry the implementation of a LAW when the same LAW is already registered in the receiver's compatible QUANTUM REALM.

## 3. MASS

MASS is a reconstructible packet, not merely "compressed bytes".

A practical packet may contain:

```text
MAGIC
VERSION
FRAME fingerprint
LAW index (D)
raw length
payload bit length
raw hash
residual payload
packet integrity data
```

Meaning is contextual:

```text
MASS | REFERENCE FRAME | QUANTUM REALM -> ENERGY
```

## 4. LORENTZ — Smart Selection

For each selectable LAW `D_i`, produce a valid candidate MASS `M_i`.

Then select:

```text
D* = argmin_i |M_i|
```

subject to exact reconstruction:

```text
INVERSE_Di(M_i) = X
```

If no specialized LAW beats the safe representation, IDENTITY remains valid.

## 5. INVERSE

INVERSE reads the packet, resolves the exact LAW by D index under the active REFERENCE FRAME, reconstructs ENERGY, and verifies the expected invariant.

## 6. INVARIANT

Exact mode requires:

```text
ENERGY === RAW
```

byte-for-byte.

## 7. ENTANGLEMENT

ENTANGLEMENT is the dependency graph among LAW nodes.

For the current research profile:
- cycles are rejected;
- dependencies are explicit;
- traversal is deterministic;
- recursion must terminate at a registered primitive/root LAW.

## 8. Cost Model

Research accounting should distinguish:

```text
logical_mass_bits
packet_bits
law_reference_bits
shared_realm_cost
frame_cost
amortized_shared_cost
```

A useful amortized expression is:

```text
C_avg(N) = packet_cost + shared_context_cost / N
```

## 9. Boundary

SMTYX-MC² is currently a reconstructive representation/runtime experiment.

It is not yet:
- a universal semantic language;
- a proof of post-Shannon compression;
- encryption;
- quantum computation;
- a replacement for PYXIS global addressing/topology.
