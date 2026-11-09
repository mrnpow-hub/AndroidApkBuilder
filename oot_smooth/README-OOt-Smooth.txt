OOT SMOOTH / RAM-AWARE PIPELINE BUILD (EXPERIMENTAL)
==================================================
Source: PantACRO4life/Lichii PR741 (stacked on PR579), pinned
  b8e4638080c257b8a28bc083d5f2c831f8aea0d4
Retention: port of Lichii PR313, with a conservative Vulkan GPU-memory
  budget in addition to a system-RAM budget. The game only keeps pipelines
  longer when safe under the cap; no unbounded preload.

EXTRACT THE ENTIRE ZIP into its own new folder. Keep the old working
Fritchii and previous shader-warm-up build.

FIRST TIME:
1. Back up %APPDATA%\eden before switching emulator forks. Their
   configurations, shader caches and saves may be shared.
2. Run Run_OOT_Smooth.cmd (or lichii.exe if preferred).
3. Right-click Ocarina of Time -> Prepare shaders (warm-up), if needed.
4. Under Emulation > Configure > Graphics > Advanced:
   - Shader libraries: ENABLE.
   - Prepare shaders before game starts: ALWAYS.
   - Native/ Switch 2 draws with unbuilt pipelines: WAIT.
   - Faster shader compiles (shared functions as calls): ENABLE.
5. Keep resolution at 1x, Vulkan, persistent shader cache ON,
   Vulkan driver pipeline cache ON, and FXAA if those match the
   previous build's acceptable visual quality.
6. Finish the initial warm-up, then test combat and revisiting areas.

The first preparation may take significant CPU time, but completing it
before gameplay avoids competition with the game while exploring.

DO NOT enable EDEN_NX2_PRELOAD_ALL_PIPELINES=1. That can compile tens
of thousands of graphics pipelines and exhaust 8 GiB VRAM.
Do not use Bounded/Skip while testing fidelity: they can drop draws.
Avoid external aggressive texture-cache overrides.

REMAINING LIMITS:
- Lichii PR741 and PR579 are experimental and not fully gameplay-verified
  on RTX 2070 Super.
- Occasional white/bright regions were reported independently of
  this retention change. Retention does not itself fix incorrect shaders.
- Shader preparation only makes known shader states cheaper. New states
  and GPU synchronization waits can still cause stalls.
- Using 64 GiB RAM does NOT turn it into 64 GiB of dedicated GPU memory.

If new visual problems appear, stop the test build and return to the
previous executable. Report the game's location, action and eden_log.txt.
No game files, title keys, firmware, saves or shaders are included.
