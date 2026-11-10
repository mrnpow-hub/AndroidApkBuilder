@echo off
setlocal
rem Quality-first, same upstream settings except conservative pipeline retention.
set "EDEN_NX2_PIPELINE_RETAIN=1"
set "EDEN_NX2_PRELOAD_ALL_PIPELINES=0"
set "EDEN_NX2_ASYNC_DISCARD=0"
cd /d "%~dp0"
start "" "%~dp0lichii.exe"
endlocal
