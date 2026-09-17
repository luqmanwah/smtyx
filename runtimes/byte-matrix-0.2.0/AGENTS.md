# SMTYX release discipline

The user froze SMTYX design and runtime 0.2.0 on 2026-09-17.
Read DESIGN_FREEZE_0.2.0.md before changing this project.

- Preserve releases/0.2.0 as the reference snapshot; never replace its artifacts.
- Treat a later explicit user change request as work for a new version. Preserve
  the frozen baseline and document any changes to mathematics, payload, or behavior.
- Distinguish SMALL fingerprints, v1 hierarchy metadata, and v2 exact representation.
  Never claim raw recovery from signatures alone or from an unverified file copy.
- Keep source inputs read-only; outputs must not overwrite existing files.
- Preserve Apache-2.0 and the design attribution @luqmanwah.
- Keep evidence of actual commands, return codes, hashes, tests, and limitations.
