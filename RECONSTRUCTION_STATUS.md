# Gacha Life reconstruction status

## What is recovered

The user-provided `GachaLife.zip` contains the Gacha Life PC Adobe AIR application and its authoritative `GachaLifePC.swf` (SHA-256 `d9d5c98f1f30b0fd872cd5ad0f2ca115673e4ff1ee31ee0ab92c58de45192863`). The SWF contains one AVM2 ABC block with 462 classes and 3,524 method bodies.

`binary_reconstructed_source/` is a generated ActionScript tree from that ABC. The current generator emits all 462/462 classes with zero generator failures. It uses control-flow-preserving state-machine ActionScript for difficult bytecode plus explicit high-level overrides where intact source semantics are safer than approximating AVM2 enumeration/`with` behavior.

For the 1.1.4-named source pack, `recovery_manifest.json` separately tracks the 14 method bodies that were replaced by decompiler-error stubs. `tools/validate_recovery.py` verifies those bodies against the attached SWF hash, method mappings, bytecode lengths, instruction counts, and deterministic generation.

The non-code SWF content is also preserved. `swf_shell/` losslessly stores everything around the game's single DoABC tag. A baseline rebuild reproduces the authoritative **decompressed SWF bytes exactly**, preserving all 20,488 original tags including timelines, placements, shapes, bitmaps, sounds, fonts, frame labels, linkage metadata, and other library data. This means rebuilt code can be inserted without reauthoring the original visual/timeline assets.

## Verified fixes

The reconstructed AS3 tree contains four bugs independently confirmed in the compiled PC SWF:

1. `generateRandomString` can select the final character in the allowed character set.
2. Minigame 2 removes `onEnterFramex` from the same dispatcher that registered it.
3. `MainTimeline.addComma(0)` returns `"0"` rather than an empty string.
4. Minigame 6 removes `onEnterFramexf` when the game ends.

`tools/patch_abc_safe_fixes.py` now applies all four directly to the authoritative ABC. Three are same-length edits; minigame 6 inserts a 16-byte cleanup call and adjusts the one branch that crosses the insertion plus the method body's `code_length` field. `tools/validate_patched_abc.py` independently verifies all four patch sites and the expected 462-class / 3,524-method-body structure.

Current patched SWF: `build/GachaLifePC-safe-patched-all4.swf`

SHA-256: `1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`

A captive-runtime Windows package has also been rebuilt as `GachaLifePC-safe-patched-all4.zip`. Runtime smoke testing still needs Windows/Wine/AIR execution.

## Current validation

Run from the Git workspace:

```bash
python tools/validate_recovery.py
python tools/test_apply_recovery_overlay.py
python tools/validate_binary_source_tree.py
python tools/rebuild_swf_shell.py
python tools/patch_abc_safe_fixes.py
python tools/rebuild_swf_shell.py --abc build/patched-safe.abc -o build/GachaLifePC-safe-patched-all4.swf
python tools/validate_patched_abc.py build/GachaLifePC-safe-patched-all4.swf
```

Expected results:

- 14/14 known source-pack decompiler failures validate against the authoritative SWF.
- Recovery-overlay tests pass.
- 462/462 classes generate with zero report failures.
- Static source validation passes, including lexical balance, package/QName paths, unique/non-reserved parameters, constructor sanity, and state-machine control-flow targets.
- Baseline lossless SWF shell rebuild matches the authoritative decompressed SWF exactly.
- All four binary fixes validate independently.

## Remaining blocker

A real AIR/Flex `mxmlc` compile has not yet been run because no compiler SDK is installed in the active reconstruction container. Apache Flex 4.16.1 is publicly available, but that container could not resolve the external download host, so repeated network retries were avoided.

`air_project/build_reconstructed_swf.sh` is ready to consume an installed AIR/Flex SDK via `AIR_SDK_HOME` or `FLEX_HOME`. A successful compiler run is still required before calling the reconstructed ActionScript tree compile-verified.

## Next technical layer

1. Provide or connect an AIR/Flex SDK containing `bin/mxmlc`; run `air_project/build_reconstructed_swf.sh` and fix real compiler diagnostics iteratively.
2. After compiler success, extract the compiler-produced ABC, insert it into the lossless shell, and compare behavior against the patched authoritative-binary candidate.
3. Smoke-test the captive-runtime package on Windows, especially character creation/save/load, studio, NPC chat, and minigames 2 and 6; record exact results in `HARDWARE_TESTS.md`.
4. Continue targeted audits for lifecycle leaks, network/error handling, save-data bounds, and null/stage assumptions. Keep every broad run behind a checkpoint commit and update `CODEX_PROGRESS.md` during work.
