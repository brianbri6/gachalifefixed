# Manual high-level method overrides

These four methods are intentionally taken from intact source-pack decompilation instead of the generic AVM2 state-machine emitter:

- method 9: `p.setTextField` — contains `with` / `pushwith` scope semantics.
- method 19: `fl.motion.Color.fromXML` — static AVM2 `call` sequence is clearer and safer in the intact source-pack form.
- method 31: `fl.motion.Color.parseXML` — contains AVM2 enumeration (`nextvalue` / `hasnext2`).
- method 432: `GachaLifePC_fla.MainTimeline.depthgo` — contains AVM2 enumeration (`nextname` / `hasnext2`).

Using the intact high-level source avoids introducing guessed enumeration/scope semantics. The binary instruction stream remains the authority for all recovered decompiler-error methods tracked in `recovery_manifest.json`.
