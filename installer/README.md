# Kitt installer (WiX)

This directory contains the WiX Toolset source for Kitt's Windows
installer (MSI). See `KITT_ARCHITECTURE.md` section 10 ("Installer
Architecture") and section 35 ("Microsoft/Windows Implementation
Notes") for the design rationale.

## Files

- `wix/Package.wxs` — product identity (Name, Manufacturer, Version,
  UpgradeCode), upgrade policy (`MajorUpgrade`), and the install
  directory (`%ProgramFiles%\Kitt\`).
- `wix/Components.wxs` — the installed payload: `kittua.dll` and the
  Windows keyboard-layout registry registration under
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\`.
- `wix/Localization.wxl` — minimal English strings for the installer UI.

## Building

The canonical way to build the MSI is `tools/package.ps1` from the
repo root, which builds `kittua.dll` first and then invokes WiX with
the correct `-D` defines:

```powershell
./tools/package.ps1
```

To invoke WiX directly (e.g. for debugging a `.wxs` change), you need
the DLL path and product version as preprocessor variables:

```powershell
$env:Path += ";C:\Program Files\dotnet;$env:USERPROFILE\.dotnet\tools"
wix build `
  installer/wix/Package.wxs `
  installer/wix/Components.wxs `
  -loc installer/wix/Localization.wxl `
  -ext WixToolset.UI.wixext `
  -arch x64 `
  -d KittuaDllPath="build/windows/src/windows/Release/kittua.dll" `
  -out dist/kitt-0.1.0-x64.msi
```

### WiX Toolset v7 EULA

WiX Toolset v7 requires accepting the Open Source Maintenance Fee
(OSMF) EULA before any command (including `build`) will run. This is
a one-time, per-user decision — not something automated silently by
this repo's scripts. If `wix` fails with `WIX7015`, accept the EULA
yourself first (see https://wixtoolset.org/osmf/ for what you are
agreeing to):

```powershell
wix eula accept wix7
```

`tools/package.ps1` checks for this and prints the same instruction
if the EULA has not been accepted yet, rather than accepting it on
your behalf.

The `WixToolset.UI.wixext` extension (needed for the minimal install
UI referenced from `Package.wxs`) is added automatically by
`tools/package.ps1` if it is not already cached (`wix extension add
WixToolset.UI.wixext`).

## What this installer does

1. Copies `kittua.dll` into `%ProgramFiles%\Kitt\`.
2. Writes a keyboard-layout registration under
   `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
   (`Layout File`, `Layout Text`, `Layout Id` values — see the
   comments in `wix/Components.wxs` for the reasoning). The key name
   was confirmed against this machine's real registry: Microsoft's
   own in-box convention for a locale's non-default layout is
   `000N<LANGID>` with N counting up (Ukrainian's default sits at
   `00000422`, its "Enhanced" variant at `00020422`), so `00010422`
   is both free and consistent with Microsoft's own numbering, not a
   guessed vendor convention.
3. Registers upgrade behavior (`MajorUpgrade`) so future 0.x.y
   releases replace this installation instead of appearing as a
   duplicate/unrelated layout.

It does **not** run any custom action, script, or background process.
Everything above is implemented with native WiX/MSI primitives
(`Component`, `File`, `RegistryValue`), per `KITT_ARCHITECTURE.md`
section 16 ("use MSI/WiX primitives instead of hand-written
destructive registry scripts when possible").

## Administrator privileges

Installing (or uninstalling) this MSI writes to `HKEY_LOCAL_MACHINE`
and to `%ProgramFiles%`, both of which require Administrator
privileges. Windows will prompt for elevation (UAC) when you run the
MSI, or you can run `msiexec /i ... ` from an elevated shell.

**Building** the MSI (`tools/package.ps1` / `wix build`) does **not**
require Administrator — it only compiles files on disk.

## IMPORTANT — do not install on your development machine

**Only install/test this MSI in a disposable test VM, never on your
main development machine.** This matches `KITT_ARCHITECTURE.md`
section 10's "Development installation" guidance: real keyboard-layout
installation touches system-level, per-machine state
(`HKEY_LOCAL_MACHINE`, the Windows input-layout system). Installing it
on a machine you rely on for development risks leaving behind an
incorrect/orphaned keyboard-layout registration that is awkward to
clean up, or interfering with your own keyboard input while you're
trying to work — this holds regardless of how confident the registry
key naming is, simply because it has not yet been tested end-to-end
as an actual installed+selectable Windows input layout.

Recommended flow:

1. Build the MSI with `tools/package.ps1` on your dev machine (no
   elevation required).
2. Copy the resulting `dist/kitt-0.1.0-x64.msi` into a disposable
   Windows VM (snapshot it first).
3. Install it there (`msiexec /i kitt-0.1.0-x64.msi`, elevated), and
   run through the manual checklist in `KITT_ARCHITECTURE.md` section
   12.6 ("Installation Tests").
4. Discard/roll back the VM snapshot when done, or verify
   `msiexec /x kitt-0.1.0-x64.msi` cleanly uninstalls it.

## Verifying checksums

`tools/package.ps1` writes a `.sha256` file alongside the `.msi` in
`dist/` (`KITT_ARCHITECTURE.md` section 11: "SHA-256 checksums are
created"). Verify with:

```powershell
Get-FileHash dist/kitt-0.1.0-x64.msi -Algorithm SHA256
```

and compare against the contents of the matching `.sha256` file.
