# Gacha Life static audit findings

## Source-integrity blocker — incomplete decompilation
The original source pack is not complete original source. Core methods in `GachaLife_fla/MainTimeline.as` and several other generated classes were replaced by decompiler-error `IllegalOperationError` stubs.

Known failed methods include:
- `MainTimeline.updatechar`
- `MainTimeline.presetgo`
- `MainTimeline.colorloop`
- `MainTimeline.updatescenechars`
- `MainTimeline.updatemakerchars`
- `MainTimeline.updatenpcs`
- `MainTimeline.updatequestions`
- `MainTimeline.frame1`
- `MainTimeline.frame5`
- `numbersonopen_4970.frame2`
- `seetocoolor_4915.updatecolor`
- `chatnpc_5373.updatenpcs`
- `chatnpc_5373.updatechar`
- `customizations_4874.randomnamebtx`

These 14 methods are now mapped to concrete bytecode bodies in the supplied Gacha Life PC SWF and tracked in `recovery_manifest.json`. `tools/validate_recovery.py` verifies mapping, instruction count, bytecode length, deterministic generation, and the authoritative SWF hash.

A strong parity signal is `chatnpc`: the source-pack timeout comments report 12,936 instructions for `updatenpcs` and 12,925 for `updatechar`, and the supplied compiled binary decodes to exactly those counts for the corresponding methods.

## Confirmed bug — wrong ENTER_FRAME dispatcher in minigame 2
`onEnterFramex` is registered on `MainTimeline`, while game-over cleanup removes it from `stage`. Because those are different event dispatchers, the cleanup does not unregister the original handler.

**Fix:** remove `onEnterFramex` from the same `MainTimeline` dispatcher that registered it.

Status: fixed in reconstructed source and direct ABC patch pipeline.

## Confirmed bug — minigame 6 movement listener survives game over
`onEnterFramexf` can remain active after the minigame loop itself is removed.

**Fix:** explicitly remove `onEnterFramexf` in the game-over cleanup branch.

Status: fixed in reconstructed source and direct ABC patch pipeline. The direct bytecode patch inserts a 16-byte cleanup call and adjusts the one crossing branch and method `code_length`.

## Confirmed bug — random-string off-by-one
`generateRandomString()` used `chars.length - 1` as the random range, making the final character unreachable.

**Fix:** use the full character count.

Status: fixed in reconstructed source and direct ABC patch pipeline.

## Confirmed bug — `addComma(0)` returns an empty string
The original formatter skips its loop for zero and returns `""`.

**Fix:** return `"0"` for zero.

Status: fixed in reconstructed source and direct ABC patch pipeline.

## Confirmed listener leak — restore panel
`restore_4819.as` registers `stage.addEventListener(Event.ENTER_FRAME, loopfd)` on its active frame. Close/success paths in the decompiled source can return to frame 1 without removing the stage listener, leaving the panel reachable from `stage`.

A conservative source patch was prepared to remove the listener before returning to frame 1. This still needs runtime confirmation once the reconstructed source compiles.

## Runtime risks still requiring parity tests
- `handleDeactivate()` sets `stage.frameRate = 0`, which is not a robust pause mechanism and should be replaced only after frame-loop parity tests exist.
- Several SFX paths may manipulate a stale/null sound channel depending on mute state; startup/channel initialization should be verified at runtime before broad changes.
- Large `SharedObject` save batches call `flush()` with limited failure/quota handling.
- Many timeline frame scripts register listeners dynamically; lifecycle auditing should track dispatcher + event type + handler as a tuple.
- Network/login/redeem paths need explicit IO/security/error-path testing.
- Dynamic-property indexing and large generated state arrays need bounds checks under corrupted save data.

## Reconstruction status
The supplied compiled SWF contains one ABC block with 462 classes and 3,524 method bodies. `binary_reconstructed_source/` now covers all 462 classes. `swf_shell/` preserves all 20,488 original non-code/timeline/library tags around the replaceable DoABC block.

Baseline decompressed-SWF SHA-256:
`0bcc4fee8b89427766bdd4538552e0682b6a4562a8e8a44a022b1e4148bc0032`

Current all-four-fix SWF SHA-256:
`1f9ae154ddd8c12085e68079b15ec52385730c526ae491987c6f9a29c5b59526`

## Tests still required
1. Compile all reconstructed ActionScript with a real AIR/Flex `mxmlc` toolchain.
2. Launch frame 1 and verify no decompilation-error paths remain.
3. Exercise minigames 2 and 6 repeatedly and verify movement handlers are cleaned up immediately.
4. Verify `generateRandomString()` can produce every allowed character.
5. Verify `addComma(0) == "0"` plus thousands/millions formatting.
6. Exercise save/load with normal, missing, corrupted, and quota/error conditions.
7. Test background/resume, audio mute/unmute, Studio, NPC chat, and network failure paths.
