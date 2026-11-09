OOT SMOOTH - WINDOWS FRAME PACING EXPERIMENT
=============================================
Source base: PantACRO4life/Lichii b8e4638080c257b8a28bc083d5f2c831f8aea0d4
Existing RenderGuard fixes are preserved.
Windows add-ons: seven source files from zortos293/Lichii PR #1002 at
  7a3b8657e51877753ba98b98e44d7087c86cc508 (unmerged research PR).
The patcher checks source blob hashes and aborts if upstream or base differ.

NEW BEHAVIOR
- Windows high-resolution coarse sleep for long HostTiming waits (enabled by
  default). Final ~300 us still uses the previous precise wait.
  Set EDEN_NX2_TIMING_SLEEP=0 to disable.
- Background shader compilation / texture worker CPU placement improved WHEN
  the existing experimental 'Pin GPU threads' emulator option is enabled.
  It is not forcibly enabled: processor models vary.
- EDEN_NX2_TARGET_FPS=<number> optionally selects a Vulkan pacing target.
  NO FPS override is set in the included launchers: default frame pacing
  stays whatever you previously chose in the emulator.
- EDEN_NX2_STUTTER_LOG=1 prints frame-interval p50/p95/p99 and long-frame
  counts to logs periodically.
- EDEN_NX2_FPS_LOG=1 prints live frontend FPS readings to logs.
  Both diagnostics are OFF unless the trace launcher is used.

LAUNCHERS
1) Run_OOT_Smooth.cmd : normal launcher, with improved Windows host timing.
2) Run_OOT_Frame_Time_Trace.cmd : same, with frame-time logs enabled.
3) Run_OOT_No_Timing_Sleep.cmd : same graphics and RAM/VRAM retention, but
   disables the new coarse-sleep path for immediate A/B comparison.

INSTALL / SAFETY
- Extract the WHOLE zip into a separate directory; do not replace your
  working RenderGuard installation.
- Back up %APPDATA%\eden (or the active fork's actual user-data folder)
  before switching forks or editing settings. Saves, caches and config can
  be shared between emulator forks.
- Prefer Vulkan, 1x internal resolution, shader library preparation and
  WAIT for unbuilt pipelines for quality-first testing if those settings
  match your known-good configuration.
- Do not enable EDEN_NX2_PRELOAD_ALL_PIPELINES=1 on an 8 GB VRAM GPU;
  this can exhaust GPU memory.
- Do not force EDEN_NX2_TARGET_FPS to 36, 48 or any arbitrary number without
  checking your display refresh, game-speed behaviour and any dynamic-FPS mod.
  A target may harm smoothness rather than improve it.
- No games, keys, firmware, saves, cache databases or copyrighted assets
  are included in the build.
- If timing causes regressions, use Run_OOT_No_Timing_Sleep.cmd.
  If both builds regress, return to the previous RenderGuard build.

EXPECTED SCOPE
This is not a promise of higher FPS. It may help 1% lows and reduce busy
waiting / CPU contention on some Windows CPU configurations. Its upstream
test platform was not the exact Intel i7 + RTX 2070 Super test system.
No shader math, texture filtering, game rendering quality, or GPU emulation
synchronization was changed by this Windows-specific port.
The known localized white-region shader glitch still requires gameplay testing.
