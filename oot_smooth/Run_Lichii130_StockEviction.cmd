@echo off
setlocal
rem A/B control: uses the original Lichii 130 eviction algorithm.
set "EDEN_NX2_PIPELINE_RETAIN=0"
set "EDEN_NX2_PRELOAD_ALL_PIPELINES=0"
set "EDEN_NX2_ASYNC_DISCARD=0"
cd /d "%~dp0"
start "" "%~dp0lichii.exe"
endlocal
