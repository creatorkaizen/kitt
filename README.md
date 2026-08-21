# Kitt

**Kitt** is a native Ukrainian mnemonic keyboard layout for Windows, designed
for the Turkish Q physical keyboard. It lets you type Ukrainian using the key
whose Latin/Turkish letter sounds like the Ukrainian letter — no separate
Ukrainian physical keyboard, no on-screen keyboard app, no background
process.

Kitt installs like any other Windows keyboard layout. Once installed, it
shows up in the normal Windows language/input switcher next to your other
layouts. There is no tray icon, no daemon, and nothing running while you are
not typing.

## What Kitt is not

- not a keyboard-remapping application;
- not a background process or global keyboard hook;
- not a cloud service, and does not require a network connection;
- not an on-screen/virtual keyboard.

Kitt is a small native Windows keyboard-layout DLL plus a standard MSI
installer. See [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md) for the full
technical design.

## Supported Windows versions

- Windows 10 (x64)
- Windows 11 (x64)

x86/ARM64 are not built yet; see `KITT_ARCHITECTURE.md` section 23.

## Installation

1. Download the latest `kitt-<version>-x64.msi` from the project's
   [Releases](../../releases) page, along with its matching `.sha256`
   checksum file.
2. (Recommended) verify the checksum before installing:

   ```powershell
   Get-FileHash kitt-<version>-x64.msi -Algorithm SHA256
   ```

   Compare the output against the contents of the `.sha256` file.
3. Run the MSI. Windows will prompt for administrator elevation (UAC) —
   this is expected. Installing a keyboard layout writes to
   `HKEY_LOCAL_MACHINE` and `%ProgramFiles%`, both of which are
   machine-wide, admin-only locations.
4. Once installed, add Kitt through Windows' normal input settings:
   **Settings → Time & Language → Language & region → Add a keyboard**
   (or **Windows key + Space** to cycle through already-added layouts,
   see below for adding it the first time).

No Python, .NET, or other runtime is required on the end-user machine —
Kitt ships as a compiled native DLL.

## Usage

Once Kitt is added as an input method, switch to it the same way you switch
between any other Windows keyboard layouts:

- **Win + Space** — cycle to the next enabled input layout.
- Or click the language/layout indicator in the taskbar and pick **Kitt**.

Typing works like a normal alphabetic layout:

- `Shift + key` produces the uppercase Ukrainian letter.
- `Caps Lock` affects letters as expected.
- Familiar QWERTY punctuation is preserved wherever possible.
- Ukrainian iotated vowels (`я`, `ю`, `є`, `ї`) are typed as `Y` followed by
  the corresponding vowel key (`Y` alone types `й`), mirroring how they
  actually sound in Ukrainian.

See [`docs/mapping.md`](docs/mapping.md) for the complete, generated
key-by-key mapping reference.

## Uninstallation

Uninstall Kitt the same way as any other Windows program:
**Settings → Apps → Installed apps → Kitt → Uninstall**, or run the original
MSI with `msiexec /x kitt-<version>-x64.msi` from an elevated shell.
Uninstalling removes the installed DLL and Kitt's own registry entries only;
it does not touch other keyboard layouts or settings.

## Privacy

Kitt collects nothing. Specifically:

- no user data is collected, stored, or transmitted;
- no network connection is made, ever;
- no telemetry, analytics, or crash reporting;
- no account system;
- Kitt cannot see or log what you type — it is a static native keyboard
  layout, not an application sitting between you and the OS.

See `KITT_ARCHITECTURE.md` sections 16 ("Security Model") and 17
("Privacy") for the full rationale.

## Development

Kitt's mapping is defined once, in YAML, and everything else (native
Windows tables, documentation, tests) is generated or validated from it.
Start here:

- [`installer/README.md`](installer/README.md) — building and inspecting
  the WiX/MSI installer.
- [`tools/`](tools/) — `build.ps1` (compile `kittua.dll`), `package.ps1`
  (build the MSI), `clean.ps1` (remove build/dist output).
- [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md) — full architecture,
  build system, testing strategy, and versioning policy.

Quick local build loop:

```powershell
pip install -e ".[dev]"
python -m kittgen validate layout/kitt.uk-UA.yaml
python -m kittgen generate
pytest tests/ -v
./tools/build.ps1
./tools/package.ps1
```
