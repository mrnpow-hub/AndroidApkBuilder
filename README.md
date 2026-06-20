# Android APK Builder

Reusable GitHub Actions workflow for building Android debug APKs.

This was extracted from the `TextNowBlaster` build setup. The original project builds its debug APK with:

```sh
gradle clean assembleDebug
```

and uploads:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Use From Another Android Repo

Create this file in the Android app repo you want to build:

```yaml
# .github/workflows/build-apk.yml
name: Build APK

on:
  push:
  workflow_dispatch:

jobs:
  build:
    uses: mrnpow-hub/AndroidApkBuilder/.github/workflows/build-debug-apk.yml@main
    with:
      artifact-name: MyApp-debug
```

After pushing, open the workflow run in GitHub Actions and download the uploaded APK artifact.

## Custom Output Paths

Most single-module Android apps output debug APKs here:

```text
app/build/outputs/apk/debug/*.apk
```

If your module is named something else, override `apk-path`:

```yaml
jobs:
  build:
    uses: mrnpow-hub/AndroidApkBuilder/.github/workflows/build-debug-apk.yml@main
    with:
      artifact-name: MyOtherApp-debug
      apk-path: mobile/build/outputs/apk/debug/*.apk
```

## Custom Gradle Commands

The default command is:

```sh
clean assembleDebug
```

Override it when needed:

```yaml
jobs:
  build:
    uses: mrnpow-hub/AndroidApkBuilder/.github/workflows/build-debug-apk.yml@main
    with:
      gradle-command: :app:assembleDebug
```

## Manual Builds

You can also run this workflow manually from the `AndroidApkBuilder` repo. Use the `repository` input to build another public repo, for example:

```text
mrnpow-hub/TextNowBlaster
```

Private repositories need the usual GitHub token permissions for `actions/checkout`.

## Notes

- Uses Java 17 by default.
- Uses the repo's `gradlew` if present.
- Falls back to installed Gradle 8.2 if `gradlew` is not present.
- Uploads the APK as a GitHub Actions artifact, not a release asset.
