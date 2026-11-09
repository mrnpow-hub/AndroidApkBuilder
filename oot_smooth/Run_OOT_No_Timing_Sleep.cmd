@echo off
setlocal
rem A/B fallback launcher: disable only the NEW Windows coarse-sleep timing path.
rem Preserves all rendering and pipeline retention from the standard launcher.
set "EDEN_NX2_GPL=1"
set "EDEN_NX2_PRELOAD_ALL_PIPELINES=0"
set "EDEN_NX2_HEAVY_SKIP=0"
set "EDEN_NX2_ASYNC_DISCARD=0"
set "EDEN_NX2_TIMING_SLEEP=0"
cd /d "%~dp0"
start "" "%~dp0lichii.exe"
endlocal
