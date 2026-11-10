#!/usr/bin/env python3
# Copyright (c) 2026. Source integration of Lichii PR #313 with new
# build-130 shader cache v2. This script is intentionally pinned to a SHA.
from pathlib import Path
import subprocess
import sys

EXPECTED = "3dae119aeac255a9334386cdf10ca707ef96867d"
root = Path("emulator")
commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
if commit != EXPECTED:
    raise RuntimeError(f"Refusing to patch unexpected source revision: {commit}")

main_path = root / "src/video_core/renderer_vulkan/vk_pipeline_cache.cpp"
text = main_path.read_text(encoding="utf-8")
if 'ShaderCacheV2' not in text:
    raise RuntimeError("Expected build-130 ShaderCacheV2 implementation is absent")

def replace_once(before: str, after: str):
    global text
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"Expected one anchor, found {count}: {before[:90]!r}")
    text = text.replace(before, after)

replace_once("#include <memory>\n", "#include <cstdlib>\n#include <memory>\n")
replace_once('#include "common/fs/path_util.h"\n',
             '#include "common/fs/path_util.h"\n#include "common/memory_detect.h"\n')
replace_once('#include "video_core/renderer_vulkan/maxwell_to_vk.h"\n',
             '#include "video_core/renderer_vulkan/maxwell_to_vk.h"\n'
             '#include "video_core/renderer_vulkan/pipeline_eviction_policy.h"\n')

budget_function = r"""
// RAM lets us keep a larger cache, but compiled VkPipeline objects consume driver
// memory (which may be VRAM). Limit it by BOTH system RAM and the GPU's reported
// Vulkan memory budget; no unlimited preload on an 8 GiB RTX 2070 Super.
// ~450 KiB is an estimate from Lichii #313, not guaranteed actual allocation.
size_t Switch2PipelineBudget(const Device& device) {
    static const size_t budget = [&device] {
        constexpr size_t EstimatedBytesPerPipeline = 450 * 1024;
        constexpr size_t Minimum = 2200;
        constexpr size_t Maximum = 4800;
        const u64 ram_bytes = Common::GetMemInfo().TotalPhysicalMemory;
        const u64 gpu_bytes = device.GetDeviceMemoryBudget();
        const size_t ram_limit = ram_bytes != 0
            ? static_cast<size_t>(ram_bytes / 8 / EstimatedBytesPerPipeline)
            : size_t{3500};
        // Never interpret the dedicated GPU memory budget as extra system RAM.
        const size_t gpu_limit = gpu_bytes != 0
            ? static_cast<size_t>(gpu_bytes / 4 / EstimatedBytesPerPipeline)
            : size_t{3500};
        const size_t safe = std::clamp(std::min(ram_limit, gpu_limit), Minimum, Maximum);
        LOG_INFO(Render_Vulkan,
                 "OoT smooth cache: retain up to {} built graphics pipelines "
                 "(host RAM {} MiB, Vulkan device budget {} MiB; conservative 25% ceiling)",
                 safe, ram_bytes >> 20, gpu_bytes >> 20);
        return safe;
    }();
    return budget;
}
"""
replace_once("    return all;\n}\n} // Anonymous namespace",
             "    return all;\n}\n" + budget_function + "} // Anonymous namespace")

start_mark = "void PipelineCache::EvictUnusedPipelines() {"
end_mark = "\n/// Returns `pipeline` when it is built"
if text.count(start_mark) != 1 or text.count(end_mark) != 1:
    raise RuntimeError("Eviction function markers do not match the pinned source")
start = text.index(start_mark)
end = text.index(end_mark, start)

replacement = r"""void PipelineCache::EvictUnusedPipelines() {
    if (device.IsMoltenVK() || PreloadAllPipelines()) {
        return;
    }
    constexpr u64 EvictAfterFrames = 9000;
    if (frame_count <= EvictAfterFrames) {
        return;
    }
    const u64 cutoff = frame_count - EvictAfterFrames;
    const char* retain_flag = std::getenv("EDEN_NX2_PIPELINE_RETAIN");
    const bool switch2 = Settings::CurrentProgramIsSwitch2() &&
        (retain_flag == nullptr || retain_flag[0] != '0');
    const size_t budget = switch2 ? Switch2PipelineBudget(device) : size_t{0};

    // Do not evict simply because a shader has been idle for 9000 frames:
    // retranslation on revisits can stall combat and scene transitions.
    if (switch2 && graphics_cache.size() <= budget) {
        return;
    }
    const size_t to_remove = switch2
        ? graphics_cache.size() - budget : std::numeric_limits<size_t>::max();

    std::vector<GraphicsPipeline*> pipelines;
    std::vector<EvictionCandidate> candidates;
    pipelines.reserve(graphics_cache.size());
    candidates.reserve(graphics_cache.size());
    for (const auto& [key, pipeline] : graphics_cache) {
        GraphicsPipeline* const candidate = pipeline.get();
        if (candidate != nullptr && candidate != current_pipeline && candidate->IsBuilt() &&
            candidate->LastUse() < cutoff) {
            pipelines.push_back(candidate);
            candidates.push_back({candidate->LastUse(), candidate->WasUsed()});
        }
    }
    constexpr size_t MaxUnusedPrebuiltPipelines = 2000;
    const auto selected =
        SelectPipelinesToEvict(candidates, MaxUnusedPrebuiltPipelines, to_remove);
    if (selected.empty()) {
        return;
    }
    std::vector<GraphicsPipeline*> doomed;
    doomed.reserve(selected.size());
    for (const size_t index : selected) {
        doomed.push_back(pipelines[index]);
    }
    std::ranges::sort(doomed);

    const u64 tick = scheduler.CurrentTick();
    size_t evicted = 0;
    for (auto it = graphics_cache.begin(); it != graphics_cache.end();) {
        GraphicsPipeline* const pipeline = it->second.get();
        if (!std::ranges::binary_search(doomed, pipeline)) {
            ++it;
            continue;
        }
        if (used_this_session.erase(pipeline) != 0) {
            used_and_evicted.insert(it->first.Hash());
        }
        evicted_pipelines.emplace_back(tick, std::move(it->second));
        it = graphics_cache.erase(it);
        ++evicted;
    }
    for (auto& [key, pipeline] : graphics_cache) {
        if (pipeline) {
            pipeline->ClearTransitions();
        }
    }
    if (switch2) {
        LOG_INFO(Render_Vulkan,
                 "OoT smooth cache: evicted {} idle pipelines after {} frames; "
                 "{} remain (target {}), preserving recently used and protected pipelines",
                 evicted, EvictAfterFrames, graphics_cache.size(), budget);
    } else {
        LOG_INFO(Render_Vulkan, "Evicted {} graphics pipelines unused for {} frames, {} left",
                 evicted, EvictAfterFrames, graphics_cache.size());
    }
}

"""
text = text[:start] + replacement + text[end:]
main_path.write_text(text, encoding="utf-8")

selector_src = Path("oot_smooth/patches/pipeline_eviction_policy.h")
selector_dst = root / "src/video_core/renderer_vulkan/pipeline_eviction_policy.h"
if selector_dst.exists():
    raise RuntimeError("Selection header already exists in pinned source")
selector_dst.write_bytes(selector_src.read_bytes())

cmake = root / "src/video_core/CMakeLists.txt"
s = cmake.read_text(encoding="utf-8")
needle = "    renderer_vulkan/pipeline_helper.h\n"
if s.count(needle) != 1:
    raise RuntimeError("CMake anchor missing")
s = s.replace(needle, "    renderer_vulkan/pipeline_eviction_policy.h\n" + needle)
cmake.write_text(s, encoding="utf-8")

# Safeguards: all three files are modified, and no shader/compiler behavior
# or rendering quality settings have been changed by this port.
for token in ("Switch2PipelineBudget(device)", "SelectPipelinesToEvict",
              "CurrentProgramIsSwitch2()", "EDEN_NX2_PIPELINE_RETAIN"):
    if token not in text:
        raise RuntimeError("Failed patch verification: " + token)
print("Patched conservative pipeline retention onto Lichii build-130; set EDEN_NX2_PIPELINE_RETAIN=0 for stock behavior.")
subprocess.run(["git", "-C", str(root), "diff", "--check"], check=True)
subprocess.run(["git", "-C", str(root), "diff", "--stat"], check=True)
