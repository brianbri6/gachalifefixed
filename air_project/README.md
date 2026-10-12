# AIR rebuild target

This directory contains the recovered AIR application descriptor from the user-provided `GachaLife.zip`. The authoritative PC movie is an AIR 32 application (`com.lunime.gachalife`, version label 1.1.3) with an 850x500, 24 fps, 56-frame SWF.

The rebuild path intentionally keeps the original SWF timeline/library shell and replaces only its single `DoABC` code payload:

```bash
export AIR_SDK_HOME=/path/to/air-sdk
./air_project/build_reconstructed_swf.sh
```

The script compiles `binary_reconstructed_source/GachaLifePC_fla/MainTimeline.as`, extracts the compiler-produced ABC payload, and injects it into `swf_shell/`. This avoids losing the original timeline placements, shapes, sprites, bitmaps, sounds, fonts, labels, and SymbolClass linkage.

Current limitation: no AIR/Flex compiler was installed in the recovery execution environment, so the compile step has not yet been executed there. The shell baseline rebuild itself was verified byte-identical after decompression.

The original icon PNGs are tracked in the local recovery workspace but are not duplicated through this connector-only GitHub write because they are binary; recover them from the supplied app archive when packaging.
