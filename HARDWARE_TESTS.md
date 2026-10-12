# Hardware Tests

_Last updated: 2026-10-12._

## Scope
Gacha Life is an Adobe AIR/ActionScript project. This ledger records desktop/mobile/device-specific tests when they become possible.

## Current environment
- No physical Android/iOS device attached.
- No GPU/input/audio hardware validation performed.
- No Windows/captive-AIR runtime execution capability exposed in the reconstruction container.

## Results
| Test | Target | Result | Notes |
|---|---|---|---|
| Physical device smoke test | Android/iOS | NOT RUN | No device/toolchain exposed in this environment. |
| Desktop captive-AIR launch | Windows | NOT RUN | Patched package exists but needs a Windows/Wine/AIR-capable environment. |
| Touch input | Mobile | NOT RUN | Requires device/emulator. |
| Audio playback | Desktop/mobile | NOT RUN | Requires runtime execution. |
| Save persistence | Desktop/mobile | NOT RUN | Requires runtime execution and writable SharedObject storage. |

## Structural test results

### 2026-10-11 — baseline reconstruction
- Structural SWF rebuild: **PASS** — baseline lossless shell is byte-identical to the authoritative game after decompression.
- ABC parse: **PASS** — ABC 46.16, 462 classes, 3,524 method bodies.
- Runtime smoke testing: **NOT RUN**.

### 2026-10-12 — all-four-fix SWF
- Artifact: `build/GachaLifePC-safe-patched-all4.swf`
- SHA-256: `1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`
- Static SWF/ABC test: **PASS** — one DoABC, 462 classes, 3,524 method bodies.
- Bytecode verification: **PASS** for all four verified fixes, including the length-changing minigame-6 cleanup.
- Independent validation: `python tools/validate_patched_abc.py` — **PASS** against both patched SWF and raw patched ABC.
- Captive-runtime package SHA-256: `49c14d64c1c5098e70c7293b4a36640677ffd2187475a1675b2ffbf2134257ab`.
- Windows/captive-AIR runtime test: **NOT RUN**.

## Required runtime smoke tests
1. Application/title-screen startup.
2. Character editor/customization.
3. Random code/string generation; verify final allowed alphabet character can occur.
4. Minigame 2 movement and repeated game-over/exit cycles; verify no stale movement handler behavior.
5. Minigame 6 game over; verify movement handler stops immediately.
6. `addComma(0)` display paths and large-number formatting.
7. Save/load persistence and corrupted/missing SharedObject handling.
8. Studio mode and NPC chat.
9. Audio mute/unmute and channel lifecycle.
10. Background/resume behavior.

## Procedure when runtime hardware is available
Document exact package, OS/runtime version, launch steps, logs, reproduction steps, and PASS/FAIL outcome here while testing. Do not replace failed results with assumptions.
