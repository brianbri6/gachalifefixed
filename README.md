# Gacha Life Fixed — reconstruction workspace

This branch is the active recovery handoff for the Gacha Life PC ActionScript/SWF reconstruction. It contains the actual progress ledger, recovery tooling/build scaffold, source/recovery manifests, patches and CI bootstrap workflows—not a placeholder branch.

## Current state

- 462/462 ABC classes represented in the locally reconstructed source tree.
- 3,524 AVM2 method bodies inventoried.
- 14/14 known source-pack decompiler failures recovered from the supplied compiled SWF.
- Lossless SWF-shell reconstruction validated against the authoritative binary.
- All four confirmed binary fixes independently validated in the patched SWF pipeline.
- Remaining major source-side blocker: run a real AIR/Flex `mxmlc` compilation and resolve compiler diagnostics.

## Key files

- `CODEX_PROGRESS.md` — live reconstruction ledger and exact validation/build commands.
- `RECONSTRUCTION_STATUS.md` — source/binary recovery status.
- `AUDIT_FINDINGS.md` — confirmed bugs and decompiler failures.
- `HARDWARE_TESTS.md` — structural/runtime test ledger.
- `NEXT_TASK.md` — exact continuation state.
- `recovery_manifest.json` — exact mapping of source decompiler failures to recovered binary method IDs.
- `tools/` — AVM2, SWF-shell, source-generation, patch and validation utilities.
- `air_project/` — AIR build scaffold.
- `manual_overrides/` — hand-corrected recovered methods.
- `patches/` — conservative source patches.
- `.github/workflows/` — FFDec/Flex SDK bootstrap workflows.

## Large generated source

The local recovery workspace also contains a 464-file `binary_reconstructed_source/` tree and 14 large recovered method bodies. Several generated files are multi-megabyte (the reconstructed `MainTimeline.as` alone is about 11.5 MB). The GitHub connector used by this run has a much smaller per-write text payload than GitHub itself, so those large generated files cannot be transferred faithfully through one connector write. They remain fully reproducible from the supplied SWF with the checked-in tooling and are individually accounted for by the recovery/source manifests and progress documents.

Generated/local-heavy artifacts (`build/`, local `.git/` objects, patched SWFs, and the ~93 MB lossless `swf_shell/` cache) are deliberately not duplicated in Git history. Exact hashes and regeneration commands are in the progress/status files.
