# Exact continuation prompt

Resume Gacha Life reconstruction from the recovery workspace branch `audit/gacha-life-1.1.4`, current clean head `441db6a` or later.

1. Read `CODEX_PROGRESS.md`, `RECONSTRUCTION_STATUS.md`, `AUDIT_FINDINGS.md`, `HARDWARE_TESTS.md`, `recovery_manifest.json`, and recent Git history before edits.
2. Update `CODEX_PROGRESS.md` while working, not only at the end. Make a checkpoint commit before broad emitter/parser/compiler work and small milestone commits afterward.
3. Restore the authoritative SWF from the supplied `GachaLife.zip` if the extracted recovery SWF is absent. Expected SHA-256: `d9d5c98f1f30b0fd872cd5ad0f2ca115673e4ff1ee31ee0ab92c58de45192863`.
4. First validation commands:
   - `python tools/validate_recovery.py`
   - `python tools/test_apply_recovery_overlay.py`
   - `python tools/validate_binary_source_tree.py`
   - `python tools/rebuild_swf_shell.py`
   - `python tools/patch_abc_safe_fixes.py`
   - `python tools/rebuild_swf_shell.py --abc build/patched-safe.abc -o build/GachaLifePC-safe-patched-all4.swf`
   - `python tools/validate_patched_abc.py build/GachaLifePC-safe-patched-all4.swf`
5. Current recovered source: `binary_reconstructed_source/`, 462/462 ABC classes, zero generator failures. Known source-pack decompiler failures: 14/14 recovered and validated.
6. Lossless assets/timelines are preserved in `swf_shell/` (20,488 tags; one replaceable DoABC). Baseline decompressed SWF SHA-256 must remain `0bcc4fee8b89427766bdd4538552e0682b6a4562a8e8a44a022b1e4148bc0032`.
7. The direct bytecode pipeline patches **all four** verified fixes. Patched SWF expected SHA-256: `1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`. Do not regress this to the old two-fix patcher.
8. Highest priority: obtain/use an AIR/Flex SDK containing `bin/mxmlc`, set `AIR_SDK_HOME` or `FLEX_HOME`, and run `./air_project/build_reconstructed_swf.sh`.
9. Capture actual compiler diagnostics and fix the emitter/generated source iteratively. Do not claim source compilation until `mxmlc` really succeeds.
10. After a successful compile, inject the compiler-produced ABC with `tools/rebuild_swf_shell.py --abc ...`, validate structure, then smoke-test on Windows/captive AIR and record results in `HARDWARE_TESTS.md`.
11. Current Windows candidate SHA-256: `49c14d64c1c5098e70c7293b4a36640677ffd2187475a1675b2ffbf2134257ab`. It includes all four binary fixes but has not been runtime-tested.
12. Continue the listener lifecycle, save/load safety, network/error handling, dynamic-property bounds, and null/stage audits after the compiler milestone.
13. If interrupted, update this file to the exact current state rather than rerunning the original prompt.
