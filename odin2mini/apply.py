#!/usr/bin/env python3
"""Apply the pinned Odin 2 Mini Pro patch to a clean Lichii-Android checkout.

This script intentionally does not overwrite game data or existing settings.
It fails rather than patching a different upstream revision.
"""
from pathlib import Path
import subprocess
import sys

BASE_SHA = "3f664b3fa03257e5e81bca32f9690ac7740bc1ff"
KIT = Path(__file__).resolve().parent
GRADLE = "src/android/app/build.gradle.kts"
DIRECTORY = "src/android/app/src/main/java/org/yuzu/yuzu_emu/utils/DirectoryInitialization.kt"
PRESENTER = "src/android/app/src/main/java/org/yuzu/yuzu_emu/features/settings/ui/SettingsFragmentPresenter.kt"

def replace_once(content: str, before: str, after: str, path: str) -> str:
    count = content.count(before)
    if count != 1:
        raise RuntimeError(f"{path}: expected one anchor, found {count}")
    return content.replace(before, after, 1)

def patch_gradle(text: str) -> str:
    path = GRADLE
    for before, after in (
        ('applicationId = "dev.lichii.android"', 'applicationId = "dev.lichii.odin2mini"'),
        ('manifestPlaceholders += mapOf("appNameBase" to "Lichii")',
         'manifestPlaceholders += mapOf("appNameBase" to "Lichii Odin 2 Mini Pro")'),
        ('resValue("string", "app_name_suffixed", "Lichii")',
         'resValue("string", "app_name_suffixed", "Lichii Odin 2 Mini Pro")'),
        ('resValue("string", "app_name", "Eden$suffix")',
         'resValue("string", "app_name", "$currentName$suffix")'),
    ):
        text = replace_once(text, before, after, path)
    return text

def patch_directory(text: str) -> str:
    path = DIRECTORY
    text = replace_once(text, "import java.io.IOException\n",
                        "import java.io.File\nimport java.io.IOException\n", path)
    text = replace_once(text,
        "            initializeInternalStorage()\n            NativeConfig.initializeGlobalConfig()",
        "            initializeInternalStorage()\n"
        "            val freshInstall = userPath?.let { !File(it, \"config/config.ini\").exists() } == true\n"
        "            NativeConfig.initializeGlobalConfig()", path)
    text = replace_once(text,
        "            migrateSettings()\n            areDirectoriesReady = true",
        "            migrateSettings()\n"
        "            if (freshInstall) Odin2MiniProfile.applyFirstRun()\n"
        "            areDirectoriesReady = true", path)
    return text

def preset_row(title: str, description: str, mode: str) -> str:
    return (
        "                add(\n"
        "                    RunnableSetting(\n"
        f"                        titleId = R.string.odin2mini_{title},\n"
        f"                        descriptionId = R.string.odin2mini_{description},\n"
        "                        isRunnable = !NativeLibrary.isRunning()\n"
        "                    ) {\n"
        f"                        if (Odin2MiniProfile.apply(Odin2MiniProfile.Preset.{mode})) {{\n"
        "                            Toast.makeText(context, R.string.odin2mini_applied, Toast.LENGTH_SHORT).show()\n"
        "                            settingsViewModel.setReloadListAndNotifyDataset(true)\n"
        "                        }\n"
        "                    }\n"
        "                )\n"
    )

def patch_presenter(text: str) -> str:
    path = PRESENTER
    text = replace_once(text,
        "import org.yuzu.yuzu_emu.utils.NativeConfig\n",
        "import org.yuzu.yuzu_emu.utils.NativeConfig\n"
        "import org.yuzu.yuzu_emu.utils.Odin2MiniProfile\n", path)
    rows = (
        "            if (Odin2MiniProfile.isTargetDevice()) {\n"
        "                add(HeaderSetting(R.string.odin2mini_profile_header))\n"
        + preset_row("balanced", "balanced_desc", "BALANCED")
        + preset_row("quality", "quality_desc", "QUALITY")
        + preset_row("memory_safe", "memory_safe_desc", "MEMORY_SAFE")
        + "            }\n"
    )
    old = ("    private fun addGraphicsSettings(sl: ArrayList<SettingsItem>) {\n"
           "        sl.apply {\n"
           "            add(IntSetting.RENDERER_RESOLUTION.key)")
    new = ("    private fun addGraphicsSettings(sl: ArrayList<SettingsItem>) {\n"
           "        sl.apply {\n" + rows +
           "            add(IntSetting.RENDERER_RESOLUTION.key)")
    return replace_once(text, old, new, path)

def main() -> int:
    if len(sys.argv) != 2:
        raise RuntimeError("usage: apply.py PATH_TO_LICHII_CHECKOUT")
    source = Path(sys.argv[1]).resolve()
    if not (source / ".git").exists():
        raise RuntimeError("Expected a Git checkout")
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=source, text=True).strip()
    head = git("rev-parse", "HEAD")
    if head != BASE_SHA:
        raise RuntimeError(f"Upstream commit mismatch: {head} != {BASE_SHA}")
    if git("status", "--porcelain"):
        raise RuntimeError("Source checkout is dirty; refusing to patch")

    transforms = {GRADLE: patch_gradle, DIRECTORY: patch_directory, PRESENTER: patch_presenter}
    changes = {}
    for rel, transform in transforms.items():
        dest = source / rel
        changes[dest] = transform(dest.read_text(encoding="utf-8"))
    for file in (KIT / "overlay").rglob("*"):
        if file.is_file():
            dest = source / file.relative_to(KIT / "overlay")
            if dest.exists():
                raise RuntimeError(f"Target already exists: {dest}")
            changes[dest] = file.read_text(encoding="utf-8")
    if len(changes) != 5:
        raise RuntimeError(f"Expected five modified/new files, found {len(changes)}")
    for dest, text in changes.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    print(f"Patched Lichii {head}; files: {len(changes)}", flush=True)
    print(git("diff", "--stat"), flush=True)
    subprocess.check_call(["git", "diff", "--check"], cwd=source)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
