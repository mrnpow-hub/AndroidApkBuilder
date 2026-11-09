#!/usr/bin/env python3
"""Selective, immutable import of the Windows-only pacing and diagnostic parts of
zortos293/Lichii PR #1002 into our pinned OoT RenderGuard executable build.

Import ONLY seven unchanged-source translation units from the reviewed PR head.
Exclude unrelated profile-training (src/yuzu/main.cpp) and ZBIC CMake changes.

Prerequisites:
  emulator HEAD exactly b8e4638080c257b8a28bc083d5f2c831f8aea0d4
  git fetch of refs/pull/1002/head from zortos293/Lichii
  existing RenderGuard and pipeline retention patches already applied

Every source blob is checked against both the PR's preimage blob and the
pin's exact resulting blob SHA before writing. Fail closed on divergence.
"""
import subprocess
from pathlib import Path

ROOT = Path("emulator")
BASE = "b8e4638080c257b8a28bc083d5f2c831f8aea0d4"
UPSTREAM = "7a3b8657e51877753ba98b98e44d7087c86cc508"

# path : (blob SHA prefix in pinned base, blob SHA prefix in PR #1002 head)
FILES = {
    "src/common/thread.cpp": ("77bd42ec94", "4bc320672a"),
    "src/common/thread.h": ("f19c8caef6", "35b373247e"),
    "src/core/core_timing.cpp": ("dfc3f6f2a6", "4c20d819b6"),
    "src/core/core_timing.h": ("f54ffafd73", "1df7d6f9ec"),
    "src/core/perf_stats.cpp": ("1ca3fe488c", "5b852fe9b2"),
    "src/video_core/renderer_vulkan/vk_swapchain.cpp": ("2cbdcbef49", "bcb5f644cb"),
    "src/yuzu/main_window.cpp": ("27691e4fa4", "b96ea45402"),
}

def git(*args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout

base = git("rev-parse", "HEAD").decode().strip()
head = git("rev-parse", "FETCH_HEAD").decode().strip()
if base != BASE or head != UPSTREAM:
    raise RuntimeError(f"Unexpected emulator base/upstream head: base={base}, upstream={head}")

# Verify the existing fixes are still present before changing unrelated source files.
assert (ROOT / "src/video_core/renderer_vulkan/pipeline_eviction_policy.h").is_file()
guarded = (ROOT / "src/video_core/texture_cache/texture_cache.h").read_text(encoding="utf-8")
assert "image_view_id == NULL_IMAGE_VIEW_ID" in guarded
assert "if (entry.view != NULL_IMAGE_VIEW_ID)" in guarded

# Two-phase verification: validate every old/new blob BEFORE overwriting any file.
imports: dict[str, bytes] = {}
for path, (old_sha, new_sha) in FILES.items():
    current = (ROOT / path).read_bytes()
    actual_old_sha = git("hash-object", "--stdin", data=current).decode().strip()
    if not actual_old_sha.startswith(old_sha):
        raise RuntimeError(f"Base source unexpectedly modified: {path} {actual_old_sha} != {old_sha}")
    replacement = git("show", f"{UPSTREAM}:{path}")
    actual_new_sha = git("hash-object", "--stdin", data=replacement).decode().strip()
    if not actual_new_sha.startswith(new_sha):
        raise RuntimeError(f"Source blob hash mismatch: {path} {actual_new_sha} != {new_sha}")
    imports[path] = replacement

for path, replacement in imports.items():
    (ROOT / path).write_bytes(replacement)
    print(f"Imported verified Windows timing/diagnostics: {path}")

checks = {
    "src/common/thread.cpp": ("PinnedRole::Background", "Settings::values.pin_gpu_threads.GetValue()"),
    "src/common/thread.h": ("PinnedRole", "Background"),
    "src/core/core_timing.cpp": ("void CoreTiming::CoarseSleep(", "EDEN_NX2_TIMING_SLEEP"),
    "src/core/core_timing.h": ("void CoarseSleep(",),
    "src/core/perf_stats.cpp": ("EDEN_NX2_STUTTER_LOG", "RecordGameFrameInterval()"),
    "src/video_core/renderer_vulkan/vk_swapchain.cpp": ("EDEN_NX2_TARGET_FPS", "scheduler.Wait"),
    "src/yuzu/main_window.cpp": ("EDEN_NX2_FPS_LOG",),
}
for path, required in checks.items():
    source = (ROOT / path).read_text(encoding="utf-8")
    for token in required:
        if token not in source:
            raise RuntimeError(f"Source import verification failed {path}: {token}")

subprocess.run(["git", "-C", str(ROOT), "diff", "--check"], check=True)
subprocess.run(["git", "-C", str(ROOT), "diff", "--stat"], check=True)
print(
    "Windows host-timer coarse sleep, optional background thread pinning, "
    "opt-in frame pacing target, and opt-in 1% low/stutter logging installed. "
    "No shader or GPU quality settings modified. PR #1002 unmerged upstream."
)
