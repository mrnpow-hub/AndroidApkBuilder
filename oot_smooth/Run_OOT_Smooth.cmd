@echo off
setlocal
rem Experimental Vulkan shader-library build with conservative, quality-first rendering.
rem Do not enable unbounded pipeline preload: the RTX 2070 Super has 8 GiB VRAM.
set "EDEN_NX2_GPL=1"
set "EDEN_NX2_PRELOAD_ALL_PIPELINES=0"
set "EDEN_NX2_HEAVY_SKIP=0"
set "EDEN_NX2_ASYNC_DISCARD=0"
cd /d "%~dp0"
start "" "%~dp0lichii.exe"
endlocal
