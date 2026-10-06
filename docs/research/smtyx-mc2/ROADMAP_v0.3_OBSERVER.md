# SMTYX-MC² v0.3 Research Roadmap — OBSERVER

## Problem

Smart Lorentz v0.2 evaluates every selectable LAW candidate.

With a small QUANTUM REALM this is acceptable. With thousands or tens of thousands of LAW nodes it becomes wasteful.

## Proposed Component

# OBSERVER

OBSERVER performs a cheap pre-screen and returns a deterministic candidate subset.

```text
RAW
 ↓
OBSERVER
 ├─ size
 ├─ sampled byte distribution
 ├─ text/binary likelihood
 ├─ repetition signature
 ├─ magic/type hint
 └─ lightweight entropy indicators
 ↓
candidate LAW set C
 ↓
LORENTZ evaluates only C
 ↓
MASS
```

Mathematically:

```text
C = O(X, Q)
```

with:

```text
C ⊂ Q
|C| << |Q|
```

then:

```text
D* = argmin_(D in C) |M_D|
```

subject to:

```text
INVERSE_D(M_D) = X
```

## Critical Boundary

OBSERVER is allowed to be heuristic.

The final exact result is not.

A false-negative candidate selection may reduce efficiency, but it must not corrupt identity. IDENTITY or another safe LAW must always remain available.

## v0.3 Engineering Targets

1. streaming I/O instead of whole-file `readFileSync`;
2. bounded-memory chunks;
3. Observer candidate pre-selection;
4. measured CPU time per LAW;
5. measured peak RSS / heap;
6. selectable LAW cost budget;
7. packet-size threshold before expensive LAW execution;
8. repeatable benchmark corpus;
9. preserve exact INVARIANT in every path.

## Research Question

Can QUANTUM REALM grow large while the average evaluated candidate set remains small enough that Smart Lorentz stays practical?

That is the central v0.3 question.
