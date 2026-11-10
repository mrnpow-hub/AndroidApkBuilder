LICHII BUILD 130 - RETAINED / WOLF - EXPERIMENTAL (NOVEMBER 9, 2026)
====================================================================
This build starts from official zortos293/Lichii build 130 (3dae119aeac255a9334386cdf10ca707ef96867d).
It retains all upstream Shader Cache v2, PGO, GPU readback, sync, and renderer crash fixes.

ADDED FROM OUR PREVIOUS WINDOWS BUILDS
1) Conservative Switch 2 graphics pipeline retention based on PR #313:
   - Only eligible idle pipelines are evicted once over the RAM/VRAM-derived cap.
   - Cap is 2,200-4,800 pipelines, estimated at about 450 KiB per pipeline,
     limited to one-eighth of physical RAM and one-quarter of Vulkan memory budget.
   - Original protection for up to 2,000 never-used prebuilt pipelines remains.
   - Switch 1 titles retain original behaviour.
2) Previous Arcolade red-eye wolf EXE and Qt window icon, checksummed.

COMPARE THE TWO LAUNCHERS
  Run_Lichii130_Retained.cmd      - retention enabled.
  Run_Lichii130_StockEviction.cmd - exact original build-130 eviction policy.
Use identical game configuration for each test. Do not run both simultaneously.

FIRST RUN
- Back up %APPDATA%\\eden (configs, caches and saves) before switching emulator forks.
- Per official build-130 release notes: right-click the game, Remove >
  Remove All Pipeline Caches. Old caches can cause compatibility/stutter problems.
  Back up the folder first if you need to roll back. New cache builds on first use.
- Keep Vulkan, image quality, resolution, and other graphics options unchanged.
- Do not force EDEN_NX2_PRELOAD_ALL_PIPELINES=1 or EDEN_NX2_ASYNC_DISCARD=1.
- Record behavior in Kokiri/Kakariko, one new region, combat and a return visit.
- If you see missing geometry, a crash or VRAM pressure, use the StockEviction
  launcher or official 130 PGO as a fallback and preserve eden_log.txt.

This is an experimental code port, not validated gameplay on RTX 2070 Super.
No game, content, keys, firmware or proprietary shader assets included.
Upstream: https://github.com/zortos293/Lichii/releases/tag/build-130
PR: https://github.com/zortos293/Lichii/pull/313
