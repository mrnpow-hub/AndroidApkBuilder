// SPDX-License-Identifier: GPL-3.0-or-later
// Odin 2 Mini Pro profile integration for Lichii-Android.
// Intentionally conservative: never alters host thermal controls or GPU driver.

package org.yuzu.yuzu_emu.utils

import android.os.Build
import org.yuzu.yuzu_emu.NativeLibrary
import org.yuzu.yuzu_emu.features.settings.model.BooleanSetting
import org.yuzu.yuzu_emu.features.settings.model.IntSetting
import java.util.Locale

object Odin2MiniProfile {
    enum class Preset {
        BALANCED,
        QUALITY,
        MEMORY_SAFE
    }

    private fun normalized(value: String): String =
        value.lowercase(Locale.ROOT).filter { it.isLetterOrDigit() }

    fun isTargetDevice(): Boolean {
        val identity = listOf(Build.MODEL, Build.DEVICE, Build.PRODUCT).map(::normalized)
        val isOdinMini = identity.any { it.contains("odin2mini") }
        if (!isOdinMini) return false

        val ramGiB = MemoryUtil.totalMemory / MemoryUtil.Gb
        return ramGiB >= 9.5f && ramGiB < 14.0f
    }

    fun applyFirstRun() {
        if (isTargetDevice()) apply(Preset.BALANCED)
    }

    fun apply(preset: Preset): Boolean {
        if (!isTargetDevice() || NativeLibrary.isRunning()) return false

        // ResolutionSetup: 0=0.25x, 1=0.5x, 2=0.75x, 3=1.0x.
        val resolution = when (preset) {
            Preset.BALANCED -> 2
            Preset.QUALITY -> 3
            Preset.MEMORY_SAFE -> 1
        }
        IntSetting.RENDERER_RESOLUTION.setInt(resolution)

        // SceneMemoryCap: 0=Auto (Ocarina of Time only), 2=On.
        val sceneCap = if (preset == Preset.MEMORY_SAFE) 2 else 0
        IntSetting.SCENE_MEMORY_CAP.setInt(sceneCap)

        IntSetting.FRAMES_AHEAD.setInt(0)
        IntSetting.RENDERER_VRAM_USAGE_MODE.setInt(0)
        IntSetting.CPU_BACKEND.setInt(1) // NCE on ARM64.

        BooleanSetting.RENDERER_USE_DISK_SHADER_CACHE.setBoolean(true)
        BooleanSetting.RENDERER_ASYNCHRONOUS_GPU_EMULATION.setBoolean(true)
        // Asynchronous shaders can temporarily omit uncompiled effects.
        BooleanSetting.RENDERER_ASYNCHRONOUS_SHADERS.setBoolean(preset != Preset.QUALITY)
        BooleanSetting.RENDERER_FRAME_GEN.setBoolean(false)

        if (NativeConfig.isPerGameConfigLoaded()) {
            NativeConfig.savePerGameConfig()
        } else {
            NativeConfig.saveGlobalConfig()
        }
        return true
    }
}
