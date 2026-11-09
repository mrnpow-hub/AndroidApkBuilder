#!/usr/bin/env python3
"""Three narrowly scoped upstream rendering/crash guards for the pinned OoT build.

Upstream references:
- Lichii #918: Log2Ceil(0) must not index past the staging pool.
- Lichii #921: never prepare the null texture view; break delta-draw reuse
  when InvalidateScale destroys image views.

This patch intentionally excludes bulk texture-cache, GPU scheduling,
shader-compiler and fast-draw rewrites. It requires the already-tested
retention patch and #910 null-view memo guard to have run first.
"""
from pathlib import Path
import subprocess

EXPECTED = "b8e4638080c257b8a28bc083d5f2c831f8aea0d4"
ROOT = Path("emulator")
actual = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
).strip()
if actual != EXPECTED:
    raise RuntimeError(f"Refusing to patch unreviewed emulator revision: {actual}")


def once(path: str, old: str, new: str) -> None:
    file = ROOT / path
    source = file.read_text(encoding="utf-8")
    hits = source.count(old)
    if hits != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}, got {hits}: {old[:80]!r}")
    file.write_text(source.replace(old, new, 1), encoding="utf-8")


once(
    "src/common/bit_util.h",
    "[[nodiscard]] constexpr T Log2Ceil(const T value) {\n"
    "    const T log2_f = Log2Floor<T>(value);",
    "[[nodiscard]] constexpr T Log2Ceil(const T value) {\n"
    "    // Lichii #918: zero-length staging requests belong to the smallest bucket.\n"
    "    if (value == T(0)) {\n"
    "        return T(0);\n"
    "    }\n"
    "    const T log2_f = Log2Floor<T>(value);",
)

once(
    "src/video_core/texture_cache/texture_cache.h",
    "void TextureCache<P>::InvalidateScale(Image& image) {\n"
    "    if (image.scale_tick <= frame_tick) {",
    "void TextureCache<P>::InvalidateScale(Image& image) {\n"
    "    // Lichii #921: deleted views must never be reused by a delta draw.\n"
    "    VideoCommon::Nx2FastDraw::Break(VideoCommon::Nx2FastDraw::Reason::Invalidation);\n"
    "    if (image.scale_tick <= frame_tick) {",
)

once(
    "src/video_core/texture_cache/texture_cache.h",
    "void TextureCache<P>::PrepareImageView(ImageViewId image_view_id, bool is_modification,\n"
    "                                       bool invalidate) {\n"
    "    if (!image_view_id) {",
    "void TextureCache<P>::PrepareImageView(ImageViewId image_view_id, bool is_modification,\n"
    "                                       bool invalidate) {\n"
    "    // Lichii #921: the null image has no valid format and must not upload.\n"
    "    if (!image_view_id || image_view_id == NULL_IMAGE_VIEW_ID) {",
)

tc = (ROOT / "src/video_core/texture_cache/texture_cache.h").read_text(encoding="utf-8")
bc = (ROOT / "src/common/bit_util.h").read_text(encoding="utf-8")
assert "if (entry.view != NULL_IMAGE_VIEW_ID)" in tc, "Missing prerequisite Lichii #910 guard"
assert "if (!image_view_id || image_view_id == NULL_IMAGE_VIEW_ID)" in tc
assert "VideoCommon::Nx2FastDraw::Break(VideoCommon::Nx2FastDraw::Reason::Invalidation);" in tc
assert "if (value == T(0))" in bc
assert (ROOT / "src/video_core/renderer_vulkan/pipeline_eviction_policy.h").is_file(), (
    "Missing prior VRAM-bounded retention patch"
)
subprocess.run(["git", "-C", str(ROOT), "diff", "--check"], check=True)
subprocess.run(["git", "-C", str(ROOT), "diff", "--stat"], check=True)
print("Applied three source-level safety guards; rendering quality and scheduling unchanged.")
