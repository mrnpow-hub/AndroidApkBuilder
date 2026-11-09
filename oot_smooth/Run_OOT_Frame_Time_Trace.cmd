@echo off
setlocal
rem Normal quality-first configuration with optional frame-interval telemetry.
set "EDEN_NX2_GPL=1"
set "EDEN_NX2_PRELOAD_ALL_PIPELINES=0"
set "EDEN_NX2_HEAVY_SKIP=0"
set "EDEN_NX2_ASYNC_DISCARD=0"
set "EDEN_NX2_STUTTER_LOG=1"
set "EDEN_NX2_FPS_LOG=1"
cd /d "%~dp0"
start "" "%~dp0lichii.exe"
endlocal
