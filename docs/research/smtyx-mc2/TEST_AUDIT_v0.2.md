# SMTYX-MC² v0.2 Test Audit

## Source

This audit accompanies the AntyGravity bulk integration report dated 7 Oct 2026 and the Reference v0.2 runtime.

## Observed Result

The report records 7 processed files, approximately 12.44 MB total input, and 8984 ms total script execution time.

All seven report entries record:

```text
Status Invariant: LULUS (100% Match)
```

LAW selection in the report:

```text
hasil-uji.json            -> TEXT_DICT
kalkulator.exact.smtyx    -> IDENTITY
kalkulator.pulih.html     -> TEXT_DICT
matriks-ringkas.json      -> TEXT_DICT
Input.zip                 -> IDENTITY
SDCardFormatter...zip     -> IDENTITY
Hello World.txt           -> IDENTITY
```

This is the desired behavior for a selector that refuses to force a specialized LAW when it does not reduce the packet.

## Reduction Observed on Structured Inputs

Approximate raw -> MASS sizes from the report:

```text
hasil-uji.json         2.49 KB -> 2.25 KB
kalkulator.pulih.html  3.79 KB -> 3.42 KB
matriks-ringkas.json   0.67 KB -> 0.66 KB
```

This is evidence of reduction under the tested TEXT_DICT context, not proof of general-purpose compression superiority.

## Corrections to the Source Report

### LAW search complexity

The source report describes exhaustive LAW evaluation as becoming "exponential" as LAW count grows.

For the current implementation, if all `L` candidate LAW nodes are independently evaluated, candidate-count growth is approximately linear in `L`:

```text
T(X) ≈ Σ cost(D_i, X)
```

The serious issue is still real: exhaustive evaluation becomes expensive as both input size and LAW count grow. The correction is terminology, not dismissal of the bottleneck.

### CPU wording

The report states candidate evaluation is completed in milliseconds, but the same report records approximately 4.66 s and 4.25 s for the two large ZIP inputs.

Therefore performance claims must be scoped by input size and LAW behavior.

## Conclusion

v0.2 materially strengthens the research:
- exact reconstruction remains intact;
- actual specialized LAW reduction appears on structured inputs;
- unsuitable/already-compressed data falls back to IDENTITY;
- the next bottleneck is candidate selection and streaming rather than basic reversibility.
