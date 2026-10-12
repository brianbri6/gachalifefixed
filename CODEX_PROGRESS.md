# Codex Progress

_Last updated: 2026-10-12. Posted from the active reconstruction workspace._

## Current project goal
Recover Gacha Life into a working, maintainable ActionScript/AIR source project from the incomplete decompiled source pack plus the compiled `GachaLifePC.swf`, while preserving the original SWF timeline/library assets losslessly and keeping every milestone recoverable in Git.

## Working rules
- Update this file while work is in progress, not only at the end.
- Checkpoint before broad recovery/compiler work.
- Make small milestone commits.
- Do not blindly rerun a failed long prompt; resume from `NEXT_TASK.md`.
- Record exact build/test commands and failures.
- Keep runtime/device results in `HARDWARE_TESTS.md`.

## What is already working
- Authoritative recovery binary identified from the supplied `GachaLife.zip` as `GachaLifePC.app/GachaLifePC.swf`.
- SWF SHA-256: `d9d5c98f1f30b0fd872cd5ad0f2ca115673e4ff1ee31ee0ab92c58de45192863`.
- Dependency-free SWF/ABC tooling inventories one DoABC block containing 462 classes and 3,524 method bodies.
- All 14 known source-pack decompiler failures have binary-derived recovery bodies and deterministic validation.
- `binary_reconstructed_source/` generates 462/462 ABC classes with zero generator failures.
- Static source validation passes for lexical balance, package/QName alignment, parameter sanity, constructor sanity, and generated state-machine control-flow targets.
- `swf_shell/` preserves the original non-code SWF content losslessly around the single replaceable DoABC tag. Baseline reconstruction matches the authoritative decompressed SWF exactly.
- Four gameplay defects are fixed in both the reconstructed source path and the direct bytecode patch path:
  1. random-string final-character off-by-one
  2. minigame-2 ENTER_FRAME cleanup on the wrong dispatcher
  3. `addComma(0)` returning an empty string
  4. minigame-6 `onEnterFramexf` cleanup at game over
- Patched SWF SHA-256: `1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`.
- Patched captive-runtime Windows package SHA-256: `49c14d64c1c5098e70c7293b4a36640677ffd2187475a1675b2ffbf2134257ab`.

## Current local Git checkpoint
Source/recovery workspace branch: `audit/gacha-life-1.1.4`

Current clean head: `441db6a` (`docs: clean reconstruction status formatting`).

Recent milestones:
- `a1ab7df` — strengthen reconstructed source validity checks
- `5fedbc9` — independently validate all patched AVM2 fixes
- `d3c3905` — patch all four verified gameplay defects in ABC
- `adfcad9` — continuation checkpoint before compiler work
- `a45cc5b` — harden AIR rebuild handoff
- `d97f823` — preserve class QNames in constructors
- `4dfe55a` — sanitize parameters and qualify static traits
- `4ad1acd` — verified AVM2 patch pipeline
- `2526b23` — preserve lossless SWF timeline/asset shell

## Main files/directories changed
- `binary_reconstructed_source/` — generated AS3 tree covering all 462 ABC classes.
- `recovery_manifest.json` — mapping for all known failed decompilations.
- `recovered_methods/` — deterministic recovered method bodies.
- `manual_overrides/` — high-level semantic overrides where intact source is preferable to low-level emission.
- `swf_shell/` — lossless pre/post-DoABC shell preserving timeline/library assets.
- `air_project/` — AIR descriptor/build scaffold and reconstructed-SWF build script.
- `tools/` — SWF parser, ABC indexer/disassembler, AVM2-to-AS3 emitter, validators, overlay tool, SWF rebuild tool, and direct safe-fix ABC patcher.
- `AUDIT_FINDINGS.md`, `HARDWARE_TESTS.md`, `NEXT_TASK.md`, `RECONSTRUCTION_STATUS.md` — live project state and handoff documentation.

## Known bugs / open issues
- A real AIR/Flex `mxmlc` compilation has not yet succeeded because no AIR/Flex compiler SDK is installed in the active container.
- The original source pack references MilkmanGames native-extension classes/events; exact ANE/library dependencies still need to be recovered or stubbed appropriately for compilation/testing.
- Windows/captive-AIR runtime smoke testing has not yet been executed here.
- Broader audits remain for listener lifecycle, save/load failure handling, dynamic-property bounds, network error handling, and background/pause behavior.
- `handleDeactivate()` setting `stage.frameRate = 0` remains a runtime-risk candidate and should be changed only after parity/runtime testing.

## Hardware / test results
See `HARDWARE_TESTS.md`.

Current static/structural results:
- 14/14 known decompiler failures: PASS
- recovery overlay tests: PASS
- 462/462 reconstructed classes: PASS
- baseline lossless SWF shell rebuild: PASS
- patched ABC structural parse: PASS, 462 classes / 3,524 method bodies
- all four direct binary fixes: PASS by independent validator
- Windows runtime smoke test: NOT RUN
- Android/iOS physical-device test: NOT RUN

## Anything attempted that failed
- Direct shell DNS/network access to GitHub and external download hosts failed in the execution container.
- External FFDec acquisition was therefore not repeatedly retried; local dependency-free AVM2 tooling was written instead.
- Apache Flex 4.16.1 was located publicly, but the container could not resolve the download host, so a real `mxmlc` run is still pending.
- Earlier inspection of `GachaLife2.zip` was correctly rejected because it is Gacha Life 2 and not authoritative for the Gacha Life 1 source pack.

## Exact validation commands
Run from the reconstruction workspace root:

```bash
python tools/validate_recovery.py
python tools/test_apply_recovery_overlay.py
python tools/validate_binary_source_tree.py
python tools/rebuild_swf_shell.py
python tools/patch_abc_safe_fixes.py
python tools/rebuild_swf_shell.py --abc build/patched-safe.abc -o build/GachaLifePC-safe-patched-all4.swf
python tools/validate_patched_abc.py build/GachaLifePC-safe-patched-all4.swf
```

Expected baseline decompressed-SWF SHA-256:

`0bcc4fee8b89427766bdd4538552e0682b6a4562a8e8a44a022b1e4148bc0032`

Expected patched SWF SHA-256:

`1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`

## Exact build command once an AIR/Flex SDK is available

```bash
export AIR_SDK_HOME=/path/to/air-or-flex-sdk
./air_project/build_reconstructed_swf.sh
```

`FLEX_HOME` may be used instead if that SDK layout provides `bin/mxmlc`.

Do not call the reconstructed source compile-verified until `mxmlc` actually succeeds.

## Next steps
1. Install/provide an AIR/Flex SDK containing `bin/mxmlc` and run `./air_project/build_reconstructed_swf.sh`.
2. Fix real compiler diagnostics iteratively, keeping `CODEX_PROGRESS.md` updated during the run.
3. Insert compiler-produced ABC into the lossless SWF shell and re-run structural validation.
4. Smoke-test the all-four-fix captive-runtime build on Windows: startup, character editing, save/load, studio, NPC chat, minigames 2 and 6, audio/input.
5. Record exact runtime results in `HARDWARE_TESTS.md`.
6. Continue lifecycle/save/network/null-stage audits behind small Git checkpoints.
