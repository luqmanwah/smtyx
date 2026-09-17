# SMTYX byte-matrix runtime — frozen 0.2.0

[byte-matrix-0.2.0](byte-matrix-0.2.0/) contains the verified, frozen raw-byte runtime.
This is a separate component from the repository-root semantic reference SDK.
Both expose the Python module name `smtyx`; run from the indicated component directory
or use separate virtual environments. Do not install both distributions into one environment.

## Run locally

Python 3.10+; no third-party runtime dependencies, model, GPU, or network required.

```sh
cd runtimes/byte-matrix-0.2.0
python -m unittest discover -s tests -v
python -m smtyx encode input.zip --exact -o input.exact.smtyx
python -m smtyx write input.exact.smtyx -o restored.zip
python -m smtyx verify input.exact.smtyx input.zip
```

Supply your own readable file and unused output filenames. The decoder reads only
the exact container; it does not copy the original source or resolve a source path.
Output publication requires hardlink support on the destination filesystem.

## Implemented

- SMALL: raw-byte pair reduction, `[N,W]`, histogram of 16 clusters, SHA-256.
- LARGE metadata: MICRO → BLOCK → PAGE → DOC and `[N,P0,P1,P2,P3]` signatures.
- LARGE exact: ordered cluster masks plus ternary pair discriminators, lossless inverse.
- `encode`, `inspect`, `decode`, `write`, `verify`, and manual versioned route registry.
- Strict integrity checks, no overwriting existing outputs, and offline operation.

The prior metadata-only format cannot recover arbitrary raw files. Use `--exact`
when encoding to produce the reversible format. Signatures alone are not universal
lossless encodings. Manual registry descriptors do not execute models, tools, or SOPs.

## Verification and limitations

The frozen runtime passed 44 tests on Windows/Python 3.13.15. A 6,508,349-byte ZIP
was reconstructed byte-for-byte, with matching SHA-256 and valid ZIP CRC, while
original-input access was blocked in the tested Python decoder process.
Its exact container measured 12,042,392 bytes: lossless, but larger than the input.
No universal compression ratio or complete semantic/AI runtime is claimed.

Frozen file contents are listed in `byte-matrix-0.2.0/FROZEN_MANIFEST.json`.
The accompanying `.gitattributes` preserves exact bytes, including fixture line endings.
The 40 baseline files are unchanged from the frozen local snapshot. Public upload
adds only this navigation guide, the manifest, and Git line-ending preservation.

The baseline documents retain historical local Windows example paths and receipt
locations for provenance. Those paths are not dependencies and should be replaced
with local paths when running examples. Local execution logs, user input/output ZIPs,
credentials, caches, and workspace build products are not included here.

Apache-2.0; SMTYX originator / initial designer: **@luqmanwah**.
