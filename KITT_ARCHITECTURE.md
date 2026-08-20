# Kitt — Technical Architecture

> **Project:** Kitt  
> **Purpose:** A native Ukrainian mnemonic keyboard layout for Windows.  
> **Primary goal:** Let a user with a Latin/QWERTY physical keyboard type Ukrainian characters through an intuitive mnemonic mapping, while behaving like a normal Windows keyboard layout.  
> **Target:** Windows 10/11, x64 first. ARM64 may be added later.  
> **Design rule:** Kitt is a keyboard layout, not a permanently running keyboard-remapping application.

---

## 1. Product Definition

Kitt installs a Ukrainian mnemonic keyboard layout into Windows so it appears alongside normal Windows input layouts. After installation, the user can select Kitt through the standard Windows language/input switcher and type Ukrainian without running a tray application or background daemon.

Kitt should feel like a normal operating-system keyboard layout:

- no always-running process;
- no global keyboard hooks;
- no cloud service;
- no account system;
- no telemetry by default;
- no network connection required;
- no database;
- no custom input box;
- no custom editor;
- no dependency on Python, Node.js, .NET, or another runtime on the end user's machine.

### Definition of Done for v1

Kitt v1 is complete when a user can:

1. install Kitt;
2. add/select the layout in Windows;
3. type the entire Ukrainian alphabet using the mnemonic mapping;
4. use Shift/Caps Lock correctly;
5. type punctuation and common symbols without surprising behavior;
6. switch between Kitt and other installed layouts using normal Windows controls;
7. reboot/sign out and still have the layout available;
8. uninstall Kitt cleanly.

Anything beyond this is optional and should not block v1.

---

## 2. Recommended Tech Stack

### 2.1 Runtime Layout

**Language:** C / C++ compatible Windows keyboard-layout source  
**Toolchain:** Microsoft Visual Studio Build Tools + Windows SDK + Windows Driver Kit (WDK)  
**Output:** Native keyboard-layout DLL

Why:

- Windows keyboard layouts are represented by native layout modules.
- A native layout integrates with the operating system instead of intercepting keystrokes from userspace.
- It introduces essentially zero idle CPU/RAM overhead because Kitt does not need a resident application.
- It works in normal desktop applications through the Windows text-input system.

The runtime component should contain only static layout tables and the small amount of code required by the Windows keyboard-layout interface.

### 2.2 Layout Definition / Source of Truth

**Format:** YAML

Recommended file:

`layout/kitt.uk-UA.yaml`

Why YAML:

- human-readable;
- easy to edit;
- comments are allowed;
- suitable for expressing base keys, Shift, AltGr, dead keys, metadata, and validation rules;
- avoids scattering Unicode literals across native C/C++ files.

The YAML file is the canonical source of truth. Generated C/C++ files are build artifacts and must not be edited manually.

### 2.3 Build Generator

**Language:** Python 3.12+

Python is recommended **only as a development/build-time tool**, not as part of the installed keyboard.

Responsibilities:

- parse the YAML layout specification;
- validate key definitions;
- validate Unicode code points;
- validate modifier layers;
- detect duplicate or unreachable mappings;
- generate native Windows layout tables/source;
- generate human-readable documentation from the same mapping;
- generate snapshot/test fixtures.

Useful libraries:

- `PyYAML` — YAML parsing;
- `pydantic` — optional typed schema validation;
- `pytest` — generator/layout tests;
- standard library `unicodedata` — Unicode validation and names.

Keep the generator dependency set intentionally small.

### 2.4 Installer

**Recommended:** WiX Toolset 5

Output:

- signed MSI or EXE/bootstrapper if desired later;
- native layout DLL installation;
- required registry configuration;
- uninstall registration;
- architecture-specific files.

Alternative for an early developer-only prototype: manually install/register the generated layout in a VM. Do not treat manual registry installation as the final user experience.

### 2.5 CI/CD

**Recommended:** GitHub Actions

CI responsibilities:

- YAML/schema validation;
- generator unit tests;
- deterministic generation check;
- native build for x64;
- installer build;
- optional ARM64 build later;
- artifact packaging;
- checksum generation;
- release creation after a version tag.

### 2.6 Optional Developer UI

**Do not build for v1.**

If Kitt later needs a visual keyboard preview/editor, use either:

- static generated HTML for documentation; or
- a tiny local developer-only UI.

Do not ship an Electron/Tauri desktop application merely to display a keyboard diagram unless a real product requirement appears.

---

## 3. High-Level Architecture

```text
                     ┌─────────────────────────┐
                     │  kitt.uk-UA.yaml        │
                     │  Canonical layout spec  │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ Python Layout Compiler  │
                     │ parse / validate / gen  │
                     └───────┬─────────┬───────┘
                             │         │
               generated C  │         │ generated docs/tests
                             ▼         ▼
              ┌──────────────────┐   ┌─────────────────┐
              │ Native Layout    │   │ Mapping docs /  │
              │ Source Tables    │   │ snapshots       │
              └────────┬─────────┘   └─────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ MSVC + WDK Build │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ kittua.dll       │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ WiX Installer    │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Windows Input    │
              │ Infrastructure   │
              └──────────────────┘
```

The most important architectural boundary is:

> **Layout semantics are platform-independent data. Windows implementation details are generated/adapted around that data.**

---

## 4. Repository Structure

```text
kitt/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── pyproject.toml
├── CMakeLists.txt                # optional orchestration layer
├── .editorconfig
├── .gitignore
│
├── layout/
│   ├── kitt.uk-UA.yaml           # canonical layout specification
│   └── schema/
│       └── layout.schema.json    # optional JSON Schema
│
├── src/
│   └── windows/
│       ├── kitt_layout.c         # generated or thin wrapper
│       ├── kitt_layout.h         # generated
│       ├── kitt.def              # export definitions if required
│       ├── resources.rc
│       └── CMakeLists.txt
│
├── generator/
│   └── kittgen/
│       ├── __init__.py
│       ├── cli.py
│       ├── model.py
│       ├── parser.py
│       ├── validation.py
│       ├── unicode.py
│       ├── windows.py
│       ├── docs.py
│       └── errors.py
│
├── installer/
│   ├── wix/
│   │   ├── Package.wxs
│   │   ├── Components.wxs
│   │   └── Localization.wxl
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── mapping.md                # generated
│   ├── installation.md
│   ├── development.md
│   ├── troubleshooting.md
│   └── decisions/
│       ├── 0001-native-layout.md
│       └── 0002-yaml-source-of-truth.md
│
├── tests/
│   ├── unit/
│   │   ├── test_parser.py
│   │   ├── test_validation.py
│   │   ├── test_unicode.py
│   │   └── test_generation.py
│   ├── layout/
│   │   ├── test_alphabet.py
│   │   ├── test_modifiers.py
│   │   ├── test_punctuation.py
│   │   └── test_invariants.py
│   ├── snapshots/
│   │   └── expected_mapping.json
│   └── integration/
│       └── README.md
│
├── tools/
│   ├── build.ps1
│   ├── test.ps1
│   ├── package.ps1
│   ├── clean.ps1
│   └── dev-install.ps1           # development VM only
│
├── build/                         # ignored
└── dist/                          # ignored
```

---

## 5. Layout Specification

The layout definition should describe *intent*, not Windows implementation details.

Example structure:

```yaml
schema_version: 1

layout:
  id: kitt-uk-ua
  name: Kitt
  description: Ukrainian mnemonic keyboard layout
  language: uk-UA
  version: 0.1.0

physical_layout:
  family: ansi-qwerty

modifiers:
  - base
  - shift
  - altgr
  - shift_altgr

keys:
  KeyA:
    base: "а"
    shift: "А"

  KeyB:
    base: "б"
    shift: "Б"

  KeyI:
    base: "і"
    shift: "І"

punctuation:
  preserve_qwerty_where_possible: true

behavior:
  caps_lock: letters_only
  normalize_unicode: NFC
```

The exact mappings above are examples only. Kitt's real mapping should be designed separately and then frozen through tests.

### Why use physical key identifiers?

Use identifiers such as `KeyA`, `KeyB`, `Digit1`, `BracketLeft`, etc. instead of storing only literal Latin characters.

Reason:

A keyboard layout maps **physical/logical key positions and scan/virtual-key information**, not text strings to text strings. This avoids creating assumptions that later break when dealing with modifiers or non-US physical keyboards.

---

## 6. Internal Data Model

The Python generator should convert YAML into a strongly validated in-memory model.

Suggested model:

```text
LayoutSpec
├── schema_version
├── metadata
│   ├── id
│   ├── name
│   ├── language
│   └── version
├── physical_layout
├── modifier_model
├── keys[]
│   ├── physical_key
│   ├── base
│   ├── shift
│   ├── altgr
│   └── shift_altgr
├── dead_keys[]
├── ligatures[]
└── behavior
```

Use explicit types for outputs:

```text
Output
├── UnicodeScalar
├── DeadKey
├── None
└── SpecialBehavior
```

Avoid magic strings such as `"NONE"`, `"DEAD"`, or `"PASS"` throughout generator code.

---

## 7. Validation Layer

Validation should fail the build before native compilation if the layout is internally inconsistent.

### Required validations

#### Metadata

- schema version is supported;
- layout ID is stable and valid;
- version is valid semantic versioning;
- locale is `uk-UA` for the Ukrainian layout.

#### Key mappings

- every referenced physical key exists;
- no duplicate key declaration;
- every output contains valid Unicode;
- letters use valid uppercase/lowercase pairs where expected;
- Ukrainian required characters are all reachable;
- unsupported accidental control characters are rejected;
- outputs are normalized to NFC;
- modifier combinations are recognized.

#### Alphabet completeness

At minimum, tests should explicitly verify reachability of:

```text
А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я
а б в г ґ д е є ж з и і ї й к л м н о п р с т у ф х ц ч ш щ ь ю я
```

Also verify apostrophe behavior because Ukrainian uses an apostrophe frequently.

#### Safety invariants

- Ctrl shortcuts should not unexpectedly emit letters when Windows/application shortcut behavior is expected;
- Alt/AltGr behavior must be deterministic;
- no modifier combination produces an accidental null or control sequence;
- Enter, Backspace, Tab, Escape, arrows, function keys, and navigation keys remain normal.

---

## 8. Windows Native Layer

Kitt should use Windows' native keyboard-layout infrastructure.

The native layer is responsible for translating the validated Kitt model into the keyboard tables expected by Windows.

Conceptually:

```text
Physical key / scan code
        ↓
Virtual-key mapping
        ↓
Modifier-state resolution
        ↓
Character table
        ↓
Unicode output
```

### Native layer responsibilities

- scan-code to virtual-key table;
- modifier tables;
- virtual-key-to-character tables;
- dead-key tables if Kitt eventually uses dead keys;
- key names where necessary;
- layout descriptor export required by Windows;
- resource metadata.

### Native layer should NOT contain

- installer behavior;
- update checks;
- HTTP requests;
- logging framework;
- analytics;
- mutable application state;
- keyboard learning/prediction;
- global hook loops.

The final DLL should be boring. Boring is good.

---

## 9. No Global Keyboard Hook Architecture

Do **not** build Kitt v1 around `SetWindowsHookEx`, low-level keyboard hooks, AutoHotkey-style remapping, or a permanently running process.

Why:

- hooks add another process to maintain;
- elevated applications can create permission/integrity-level complications;
- secure input contexts can behave differently;
- games/anti-cheat/security tools may dislike input hooks;
- crashes can affect input behavior;
- startup configuration becomes necessary;
- latency and state bugs become possible;
- keyboard switching no longer behaves like a true installed layout.

A native layout is much closer to what Kitt actually is.

---

## 10. Installer Architecture

The installer is a separate concern from the layout itself.

### Installer responsibilities

1. detect architecture;
2. copy the correct native layout DLL;
3. register the layout with Windows;
4. create localized/display metadata;
5. make the layout available to the input system;
6. support repair/upgrade;
7. support complete uninstall;
8. preserve unrelated user keyboard settings.

Windows maintains keyboard-layout registrations under the system keyboard-layout registry. Installation logic should touch only Kitt-owned entries and should never rewrite the whole registry branch.

### Upgrade policy

Use stable component/product identifiers where required by WiX/MSI semantics.

Rules:

- patch/minor releases should upgrade Kitt rather than appear as random duplicate layouts;
- uninstall old Kitt-owned DLLs only when safe;
- never delete registry keys not created by Kitt;
- retain user choice of active/default layout where practical;
- if a reboot/sign-out is needed for a particular change, communicate it explicitly.

### Development installation

`tools/dev-install.ps1` may automate installation into a disposable Windows VM during development.

It should:

- require Administrator explicitly;
- print every system path/registry key it changes;
- support `-WhatIf` or dry-run if practical;
- have a matching `dev-uninstall.ps1` or guaranteed cleanup path.

Do not casually test raw installer/registry changes on the only working development environment if a VM is available.

---

## 11. Build System

Recommended build flow:

```text
1. Python validates layout YAML
2. Python generates native source + mapping docs
3. CMake/MSBuild configures native project
4. MSVC + WDK compile layout DLL
5. tests run
6. WiX builds installer
7. SHA-256 checksums are created
8. artifacts placed in dist/
```

Suggested commands:

```powershell
./tools/test.ps1
./tools/build.ps1
./tools/package.ps1
```

`build.ps1` should be the canonical local build entrypoint, even if it delegates to Python, CMake, MSBuild, and WiX internally.

### Deterministic generation

CI should run the generator and fail if generated committed files differ from repository state.

Example concept:

```text
python -m kittgen generate

git diff --exit-code
```

This prevents someone from editing YAML without regenerating the Windows tables/docs.

---

## 12. Testing Strategy

Kitt is small enough that exhaustive mapping tests are realistic.

### 12.1 Unit Tests

Test Python components individually:

- parser;
- schema/model construction;
- Unicode normalization;
- modifier expansion;
- Windows table generation;
- invalid configuration errors.

### 12.2 Layout Contract Tests

Every important key should have explicit expected output.

Example:

```python
@pytest.mark.parametrize(
    ("key", "mods", "expected"),
    [
        ("KeyA", set(), "а"),
        ("KeyA", {"shift"}, "А"),
    ],
)
def test_mapping(...):
    ...
```

Again, actual final mapping values should come from the approved Kitt specification.

### 12.3 Alphabet Coverage Test

Build a set containing every output reachable from supported key/modifier states and compare it against the required Ukrainian alphabet.

Failure example:

```text
Missing required characters:
- Ґ
- ї
```

This protects Kitt from accidentally losing a letter during future layout edits.

### 12.4 Snapshot Tests

Generate a normalized mapping representation such as JSON and snapshot it.

Any layout change then produces a visible diff:

```diff
- KeyG + AltGr => ґ
+ KeyG          => ґ
```

This is ideal for reviewing keyboard changes.

### 12.5 Native Build Tests

CI must compile the actual DLL, not merely test the YAML generator.

### 12.6 Installation Tests

Use a Windows VM for release candidates.

Manual/automated checklist:

- fresh install succeeds;
- Kitt appears as an input option;
- Kitt can be selected;
- sample Ukrainian text types correctly;
- Shift works;
- Caps Lock works;
- punctuation works;
- common Ctrl shortcuts work;
- Win+Space switching works;
- sign out/in preserves availability;
- reboot preserves availability;
- uninstall removes Kitt;
- reinstall works;
- upgrade from previous version works.

### 12.7 Application Compatibility Smoke Tests

Test at least:

- Notepad;
- browser text field;
- VS Code;
- terminal;
- Microsoft Office or LibreOffice if available;
- password field behavior where appropriate;
- elevated application if relevant.

The goal is not to test every application; it is to make sure Kitt behaves as a native layout rather than as an application-specific remapper.

---

## 13. CI Pipeline

Suggested GitHub Actions jobs:

```text
lint-and-test
├── setup Python
├── install generator deps
├── validate layout
├── run pytest
└── verify deterministic generation

build-windows-x64
├── setup MSVC/Windows SDK/WDK
├── generate source
├── build Release DLL
└── upload artifact

package-windows-x64
├── download DLL artifact
├── build WiX package
├── calculate SHA-256
└── upload installer artifact
```

Later:

```text
build-windows-arm64
package-windows-arm64
```

### Release trigger

Recommended:

```text
push tag: v*
```

Tag example:

```text
v0.1.0
```

Only tagged builds should become official downloadable releases.

---

## 14. Versioning

Use Semantic Versioning for the software package:

```text
MAJOR.MINOR.PATCH
```

Examples:

- `0.1.0` — first usable development release;
- `0.2.0` — changed/expanded mapping before stable v1;
- `1.0.0` — mapping and installation behavior considered stable;
- `1.0.1` — installer/build bug fix with no intended mapping change;
- `1.1.0` — backward-compatible functionality or deliberate mapping extension.

### Mapping stability rule after 1.0

After v1.0, moving an existing common letter to another key is a **breaking user-interface change** even if the program's APIs have not changed.

Keyboard muscle memory is an interface contract.

Treat major mapping changes seriously.

---

## 15. Logging and Diagnostics

The runtime keyboard DLL should not implement ordinary application logging.

Diagnostics belong in build and installation tools.

### Generator diagnostics

Good:

```text
ERROR KITT101: KeyG.altgr duplicates output already assigned to KeyH.altgr
ERROR KITT203: Required Ukrainian character 'ї' is unreachable
ERROR KITT301: Unsupported modifier name 'ctrl_shift_magic'
```

Use stable error codes if diagnostics grow beyond a few messages.

### Installer diagnostics

WiX/MSI logs should be sufficient for installation debugging.

Provide troubleshooting instructions showing how to generate a verbose installer log rather than inventing a custom logging service.

---

## 16. Security Model

Kitt has a naturally small attack surface if scope is controlled.

### Security principles

- no network access;
- no automatic code download;
- no background service;
- no global hook;
- no collection of typed text;
- no telemetry by default;
- no credential handling;
- no scripting engine;
- no plugin system;
- no self-updater in v1.

### Installer security

Installer elevation is sensitive because keyboard-layout installation affects system-level locations/configuration.

Rules:

- modify only Kitt-owned resources;
- validate architecture before installing binaries;
- quote file paths correctly;
- avoid invoking arbitrary shell strings;
- use MSI/WiX primitives instead of hand-written destructive registry scripts when possible;
- digitally sign public releases when feasible;
- publish SHA-256 checksums.

### Supply-chain security

- pin development dependencies appropriately;
- use Dependabot/Renovate only if useful, not because every project needs bots;
- keep third-party dependencies minimal;
- release from CI rather than random local binaries once the project is public/stable.

---

## 17. Privacy

Kitt should have effectively no user-data model.

It should never know what users type.

There is no reason for a static native layout to:

- record keystrokes;
- save text;
- transmit text;
- profile users;
- create an account;
- upload crash content containing typed data.

This should be stated explicitly in the README/privacy section because users are reasonably cautious about keyboard software.

---

## 18. Performance Requirements

Because Kitt is a native layout rather than a remapping daemon, performance requirements are simple.

Targets:

- no persistent background CPU usage;
- no persistent background process;
- no meaningful typing latency added by Kitt;
- tiny installed footprint;
- deterministic mapping;
- no allocation-heavy per-keystroke application logic.

Do not create a benchmark suite unless a real performance issue appears.

---

## 19. Documentation Architecture

### `README.md`

Keep this user-facing:

- what Kitt is;
- screenshot/diagram of mapping;
- supported Windows versions;
- install instructions;
- usage;
- uninstall;
- privacy statement;
- development link.

### `docs/mapping.md`

Generated from YAML.

Include:

- physical key;
- base output;
- Shift output;
- AltGr output if present;
- example mnemonic rationale.

Never maintain this table manually if the generator can produce it.

### `docs/development.md`

Include:

- required Visual Studio components;
- Windows SDK/WDK requirements;
- Python setup;
- WiX setup;
- commands;
- test VM recommendations;
- release process.

### Architecture Decision Records

For decisions that would otherwise be repeatedly debated, use tiny ADRs.

Examples:

`0001-native-layout.md`

```text
Decision: implement Kitt as a native Windows layout rather than a key-hook daemon.
Reason: native integration, lower attack surface, no background process.
```

`0002-yaml-source-of-truth.md`

```text
Decision: store mapping semantics in YAML and generate platform code.
Reason: reviewability, testing, documentation generation, future portability.
```

Do not create an ADR for every trivial coding choice.

---

## 20. Developer Workflow

### First setup

```powershell
# Python build environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Validate layout
python -m kittgen validate layout/kitt.uk-UA.yaml

# Generate source/docs
python -m kittgen generate

# Tests
pytest

# Native build
./tools/build.ps1
```

Exact Visual Studio/WDK environment setup can be documented after the initial prototype chooses the final build invocation.

### Normal edit loop

```text
edit YAML
   ↓
validate
   ↓
generate
   ↓
unit/layout tests
   ↓
compile
   ↓
test in VM
```

Developers should rarely touch generated Windows mapping tables directly.

---

## 21. Mapping Design Process

The architecture should not decide the mnemonic mapping accidentally.

Create the mapping deliberately before freezing v1.

Recommended process:

### Phase A — obvious direct mappings

Assign Latin keys with strong visual/phonetic correspondence first.

### Phase B — Ukrainian-specific characters

Deliberately choose ergonomic positions for characters that do not have one obvious Latin equivalent, especially:

- `г`;
- `ґ`;
- `є`;
- `і`;
- `ї`;
- `и`;
- `й`;
- `ж`;
- `х`;
- `ц`;
- `ч`;
- `ш`;
- `щ`;
- `ь`;
- `ю`;
- `я`;
- apostrophe.

### Phase C — punctuation preservation

Preserve familiar QWERTY punctuation wherever possible.

A mnemonic layout should reduce mental translation, not create a second unrelated punctuation layout.

### Phase D — frequency/ergonomics check

Mnemonic logic is primary, but avoid putting very frequent Ukrainian characters behind awkward modifier chords if a reasonable direct key exists.

### Phase E — freeze and test

Once approved:

- snapshot layout;
- generate diagram;
- write exhaustive tests;
- avoid casual remapping.

---

## 22. Caps Lock and Modifier Semantics

Kitt should behave predictably like an ordinary alphabetic layout.

Recommended rules:

- `Shift + letter` → uppercase Ukrainian letter;
- `Caps Lock` affects letters;
- punctuation should not become weird merely because Caps Lock is active;
- Ctrl-based application shortcuts should continue to behave normally;
- AltGr should only be used when necessary and documented clearly;
- avoid multi-step dead-key sequences for common Ukrainian letters unless there is a compelling reason.

A mnemonic keyboard that requires frequent modifier gymnastics defeats its purpose.

---

## 23. Architecture-Specific Builds

### v1

Support:

```text
Windows x64
```

This covers the primary target and keeps initial testing manageable.

### Later

Add:

```text
Windows ARM64
```

Only after:

- x64 layout is stable;
- installer design is stable;
- CI can build/test ARM64 artifacts;
- there is a real need.

Avoid x86 unless a concrete supported-user requirement appears.

---

## 24. Future Portability

The YAML source-of-truth creates a clean possibility for other platforms later:

```text
                  Kitt LayoutSpec
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Windows        Linux         macOS
      backend        backend       backend
```

But this is an architectural possibility, **not a v1 roadmap commitment**.

If a Linux/macOS backend is ever added, platform adapters should consume the same normalized `LayoutSpec` rather than duplicating the mapping manually.

---

## 25. Features Explicitly Rejected for v1

Do not implement these unless the project's purpose changes:

- tray application;
- global keyboard hooks;
- AI autocomplete;
- spell checking;
- translation;
- transliteration engine;
- cloud synchronization;
- accounts;
- themes;
- plugin system;
- custom scripting;
- keyboard marketplace;
- analytics dashboard;
- automatic language detection;
- cross-device sync;
- mobile keyboard;
- browser extension;
- updater daemon;
- background service;
- n8n-style visual keyboard workflows;
- embedded database;
- web server.

Kitt's competitive advantage is that it is tiny, understandable, native, and reliable.

---

## 26. Scope Guardrails

Before adding a feature, ask:

> Does this make the Ukrainian mnemonic keyboard itself work better as a Windows keyboard layout?

If **yes**, consider it.

If **no**, it probably belongs somewhere else.

Examples:

| Idea | Decision |
|---|---|
| Better mapping for `ї` | Yes |
| ARM64 build | Later, reasonable |
| Generated keyboard diagram | Yes |
| Cleaner installer | Yes |
| Transliterate an entire paragraph | No |
| Ukrainian dictionary | No |
| AI grammar correction | No |
| User profiles | No |
| Cloud backup | No |
| Plugin SDK | Absolutely no |

---

## 27. Suggested Milestones

### M0 — Mapping Prototype

- define YAML schema;
- create first full Ukrainian mapping;
- validation for required characters;
- generated mapping table;
- no installer required yet.

Exit criterion: every Ukrainian character is intentionally reachable.

### M1 — Native Prototype

- generate Windows tables/source;
- compile x64 DLL with current WDK/MSVC;
- manually install in disposable Windows test environment;
- type test text successfully.

Exit criterion: Kitt works as a real Windows layout.

### M2 — Layout Stabilization

- resolve modifier behavior;
- Caps Lock tests;
- punctuation tests;
- Ctrl shortcut smoke tests;
- snapshot mapping;
- generated layout documentation.

Exit criterion: mapping is comfortable enough to stop redesigning every day.

### M3 — Installer

- WiX package;
- clean install/uninstall;
- upgrade behavior;
- reboot/sign-out test;
- troubleshooting documentation.

Exit criterion: another user can install Kitt without touching the registry manually.

### M4 — Release Engineering

- GitHub Actions;
- tagged releases;
- checksums;
- code signing if available;
- clean README;
- `v1.0.0` release candidate.

Exit criterion: reproducible public-quality build.

### M5 — Optional ARM64

Only after v1 is stable.

---

## 28. Recommended MVP File Count

Kitt does not need hundreds of modules.

A healthy early project could be approximately:

```text
1 layout YAML
5–10 Python generator modules
3–6 native Windows files/templates
2–4 WiX installer files
5–10 test files
5 documentation files
4 PowerShell helper scripts
```

If the architecture reaches dozens of runtime subsystems before the first working keyboard layout, scope has gone wrong.

---

## 29. Recommended Dependency Policy

### Build-time Python

Keep:

```text
PyYAML
pytest
pydantic (optional)
```

Do not add a package for a five-line utility that the standard library already handles well.

### Native runtime

Prefer:

```text
Windows system interfaces only
```

No third-party runtime library should be necessary for the keyboard-layout DLL.

### Installer

```text
WiX Toolset
```

This keeps the trust and maintenance surface small.

---

## 30. Naming Conventions

Project/product:

```text
Kitt
```

Repository:

```text
kitt
```

Python package:

```text
kittgen
```

Layout spec:

```text
kitt.uk-UA.yaml
```

Native DLL internal filename example:

```text
kittua.dll
```

Avoid spaces and decorative names in binary/internal identifiers.

User-visible display name:

```text
Kitt — Ukrainian Mnemonic
```

or simply:

```text
Kitt
```

The exact Windows display string can be finalized during installer integration.

---

## 31. Git Strategy

Kitt is small; use a simple workflow.

Recommended:

```text
main
feature/*
fix/*
```

Rules:

- `main` should build;
- short-lived branches only;
- no `develop` branch unless the project actually grows enough to justify it;
- release tags from `main`;
- mapping changes should be clearly described in commits/PRs.

Suggested commit styles:

```text
feat(layout): add mnemonic mapping for ї
fix(generator): reject duplicate modifier entries
build(wix): package x64 layout DLL
 test(layout): cover Ukrainian alphabet reachability
 docs: add installation guide
```

---

## 32. Code Quality Rules

### Python

- type hints on public/internal boundary functions;
- pure functions for mapping transformations where possible;
- no giant utility module;
- no global mutable state;
- errors should mention source key/path;
- formatter/linter can be Ruff if desired.

### Native code

- generated tables clearly marked as generated;
- warning-clean build where practical;
- no unnecessary heap ownership;
- no application framework;
- platform-specific code isolated under `src/windows`.

### General

Prefer:

```text
boring > clever
explicit > magical
static data > mutable runtime state
build-time complexity > runtime complexity
```

For Kitt, moving complexity into validated generation is an excellent trade because users then install a tiny deterministic native artifact.

---

## 33. Error Philosophy

Most Kitt failures should happen **before release**, not while a user types.

Examples:

Bad architecture:

```text
User presses key → runtime discovers invalid mapping → logs error → fallback behavior
```

Good architecture:

```text
Developer defines invalid mapping → generator refuses to build
```

A keyboard mapping is almost completely static, so compile-time/build-time validation should be aggressive.

---

## 34. Why Not MSKLC as the Core Architecture?

Microsoft Keyboard Layout Creator can be useful for experiments, but Kitt should not make an old GUI layout-authoring application its architectural source of truth.

Better long-term design:

```text
Kitt YAML
   ↓
Kitt generator
   ↓
current native Windows build toolchain
```

Benefits:

- mapping is reviewable in Git;
- tests can verify every character;
- docs can be generated automatically;
- build can run in CI;
- platform backends can be added later;
- Kitt is not dependent on manual GUI editing.

A temporary MSKLC prototype is fine if it helps confirm behavior, but its project file should not become the only authoritative representation of Kitt.

---

## 35. Microsoft/Windows Implementation Notes

Microsoft's current keyboard-layout sample documentation shows native keyboard-layout samples being built with Visual Studio/WDK/MSBuild. Windows also maintains keyboard-layout registration under:

```text
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts
```

Kitt's installer should use supported installer/system mechanisms around this model rather than creating a permanent remapping application.

Windows refers to the active input locale/layout through an `HKL` and exposes APIs for querying/loading keyboard layouts. Kitt normally does not need to call these APIs from a resident app because the operating system handles selection and activation once the native layout is installed.

---

## 36. Final Architecture Decision

### Kitt v1 architecture

```text
YAML layout specification
        ↓
Python validation/generator
        ↓
Generated native Windows keyboard tables
        ↓
C/C++ keyboard-layout DLL compiled with MSVC + WDK
        ↓
WiX installer
        ↓
Normal Windows input-layout system
```

### Runtime processes

```text
0 Kitt background processes
```

### Runtime network requests

```text
0
```

### Runtime database

```text
none
```

### Primary state

```text
static keyboard mapping
```

### Primary engineering risk

```text
Windows installation/integration + correct modifier/mapping semantics
```

### Primary product risk

```text
choosing a mnemonic layout that feels intuitive enough to keep using
```

---

## 37. What to Build First

Do **not** begin with the installer or native DLL.

Start with these files:

```text
layout/kitt.uk-UA.yaml
generator/kittgen/model.py
generator/kittgen/parser.py
generator/kittgen/validation.py
tests/layout/test_alphabet.py
docs/mapping.md  # generated
```

First milestone command:

```powershell
python -m kittgen validate layout/kitt.uk-UA.yaml
```

Desired output:

```text
Kitt layout valid.
33 Ukrainian letters reachable.
Required punctuation reachable.
0 duplicate mappings.
0 invalid Unicode outputs.
```

Then generate a human-readable keyboard map and review the ergonomics **before writing the Windows backend**.

That order prevents spending hours compiling/installing a layout whose actual key mapping is still changing every ten minutes.

---

# One-Sentence Architecture Summary

**Kitt is a data-driven, build-time-generated native Windows keyboard layout: a YAML mnemonic mapping is validated by a small Python compiler, converted into native Windows keyboard tables, compiled with the Microsoft WDK/MSVC toolchain, and shipped through a WiX installer with no background process, network service, database, or global keyboard hook.**
