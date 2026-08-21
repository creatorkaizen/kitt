# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(see `KITT_ARCHITECTURE.md` section 14 for Kitt's specific versioning policy).

## [Unreleased]

Work so far corresponds to milestones M0–M3 of
`KITT_ARCHITECTURE.md` section 27 ("Suggested Milestones"). No
tagged release has been published yet.

### Added

- **Layout (M0):** canonical Ukrainian mnemonic layout
  (`layout/kitt.uk-UA.yaml`), mapped to Turkish Q physical keyboard
  positions, with a dead key on `Y` for the iotated vowels
  (я/ю/є/ї).
- **Generator (M0):** `kittgen` Python package (parser, validation,
  Unicode checks, Windows table generation, Markdown docs generation,
  CLI) with `python -m kittgen validate` and
  `python -m kittgen generate` commands. All 66 required Ukrainian
  letters confirmed reachable.
- **Native layer (M1):** `kittgen` generates a Windows `KBDTABLES` C
  source file (`src/windows/kitt_tables.c`) from the YAML layout,
  including `VK_TO_WCHARS2`, dead-key/`DEADTRANS`, the scan-code
  table, and the `KbdLayerDescriptor` export, following the WDK
  keyboard-layout DLL contract. Turkish-Q-specific `VK_OEM_*`
  assignments and scan codes were verified against the real
  Windows-shipped Turkish Q driver (`KBDTUQ.DLL`).
- **Native build (M2):** CMake build system (`CMakeLists.txt`,
  `src/windows/CMakeLists.txt`, `kitt.def`, `resources.rc`) producing
  `kittua.dll`, plus `tools/build.ps1` as the canonical local build
  entrypoint (regenerates native source from YAML, then configures
  and builds via CMake/MSVC) and `tools/clean.ps1`.
- **Installer (M3):** WiX Toolset source
  (`installer/wix/Package.wxs`, `Components.wxs`, `Localization.wxl`)
  and `tools/package.ps1`, producing
  `dist/kitt-<version>-x64.msi` with a SHA-256 checksum file. Installs
  `kittua.dll` and registers the layout under
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
  using native WiX/MSI primitives only (no custom actions).
- **Tests:** pytest suite covering unit, layout/contract, and
  snapshot tests (246 tests as of this writing), including full
  Ukrainian alphabet reachability and deterministic-generation
  coverage.
- **CI/CD:** GitHub Actions `ci.yml` (lint-and-test,
  build-windows-x64, package-windows-x64, matching
  `KITT_ARCHITECTURE.md` section 13) and `release.yml`
  (tag-triggered `v*` build, package, and GitHub Release publication
  with version-consistency check against `layout.version`, per
  section 14).
- **Docs:** user-facing `README.md`; generated mapping reference
  (`docs/mapping.md`).

### Fixed

- CMake install rules were missing `ARCHIVE DESTINATION`, silently
  dropping `kittua.lib` from an installed/packaged tree; and
  `kitt.def` was referenced in two independent places that could
  have silently diverged. Both corrected during M2 review.
