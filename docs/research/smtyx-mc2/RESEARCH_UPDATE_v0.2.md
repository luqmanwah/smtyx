# SMTYX-MC² — Research Update v0.2

## Executive Status

SMTYX-MC² v0.2 is now an executable reconstructive representation experiment rather than only a conceptual architecture.

The current evidence supports:

```text
Exact reconstruction       PASS
Registered LAW index       PASS
REFERENCE FRAME binding    PASS
Auto LAW selection         PASS
TEXT_DICT reduction        PASS on tested structured inputs
IDENTITY fallback          PASS
Compact MASS packet        PASS
```

Open research:

```text
Large-file streaming       OPEN
LAW selection scalability  OPEN
Measured RAM profiling     OPEN
Measured CPU profiling     OPEN
Observer pre-selection     NEXT
```

## Architecture

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

### D as Registered Index

The current Reference v0.2 profile demonstrates the intended form:

```text
D0 -> IDENTITY
D1 -> RLE8
D2 -> REPEAT_BLOCK
D3 -> TOY_ALPHA2
D4 -> TEXT_DICT
```

The exact map is profile/version specific.

MASS therefore does not need to carry a full implementation when both sides already share a compatible registered LAW.

## Smart Lorentz

Given selectable LAW candidates, v0.2 evaluates valid MASS candidates and chooses the smallest packet:

```text
D* = argmin_D packet_size(D, X)
```

subject to:

```text
INVERSE_D(LORENTZ_D(X)) = X
```

This is local candidate optimization, not a proof of global optimal coding.

## v0.2 Bulk Test

The supplied AntyGravity integration log records 7 files, ~12.44 MB total input, 8984 ms total execution, and exact invariant success for all seven.

LAW choices:

```text
hasil-uji.json            -> TEXT_DICT
kalkulator.exact.smtyx    -> IDENTITY
kalkulator.pulih.html     -> TEXT_DICT
matriks-ringkas.json      -> TEXT_DICT
Input.zip                 -> IDENTITY
SDCardFormatter...zip     -> IDENTITY
Hello World.txt           -> IDENTITY
```

Structured input reductions reported:

```text
hasil-uji.json         2.49 KB -> 2.25 KB
kalkulator.pulih.html  3.79 KB -> 3.42 KB
matriks-ringkas.json   0.67 KB -> 0.66 KB
```

Already-compressed ZIP inputs correctly fell back to IDENTITY instead of forcing a false reduction claim.

## Audit Corrections

### Exhaustive LAW search

The source report calls growth "exponential". For the current implementation, independently evaluating `L` candidates is approximately linear in LAW count:

```text
T(X) ≈ Σ cost(D_i, X)
```

The scalability issue remains serious because cost grows with both input size and the number/complexity of candidate LAW nodes.

### Performance wording

The process report also records approximately 4.66 s and 4.25 s for the two large ZIP files. Therefore statements that LAW selection completes in milliseconds must be scoped to smaller inputs or specific LAW paths.

## Information-Theory Boundary

SMTYX-MC² does not claim that missing information vanishes.

```text
MASS + CODE + CONTEXT -> ENERGY
```

Research accounting must distinguish:

- logical residual size;
- actual packet size;
- registered LAW / shared context cost;
- amortized shared context cost;
- total storage/transmission cost.

## Three Program Lineages

### 1. Codex Version v0.1
Rigorous baseline:
- explicit framing;
- separate manifest;
- fail-closed version/hash checks;
- collision testing;
- cross-process tests;
- cost accounting.

### 2. AntyGravity Version v0.1
Experimental lab:
- simpler implementation;
- rapid conceptual iteration;
- early AI/vision hypotheses;
- useful for exploration, but claims must be separated from tested behavior.

### 3. Reference Runtime v0.2
Current research reference:
- registered D indices;
- compact MASS packet;
- Smart Lorentz auto-selection;
- RLE8 / repeated block / TEXT_DICT experiments;
- honest IDENTITY fallback;
- benchmark and break-even cost analysis.

These are retained as lineage, not as three simultaneous canonical specifications.

## Next Direction — OBSERVER

The next bottleneck is exhaustive LAW selection.

Proposed v0.3:

```text
RAW
 ↓
OBSERVER
 ↓
candidate LAW subset
 ↓
LORENTZ
 ↓
MASS
```

Candidate set:

```text
C = O(X, Q)
C ⊂ Q
|C| << |Q|
```

Then:

```text
D* = argmin_(D in C) |M_D|
```

with exact reconstruction still enforced by INVARIANT.

OBSERVER may be heuristic; exact identity may not be.
