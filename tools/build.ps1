<#
.SYNOPSIS
    Kitt canonical local build entrypoint (KITT_ARCHITECTURE.md
    sections 11 and 20).

.DESCRIPTION
    1. Runs the Python generator (kittgen) so src/windows/kitt_tables.c
       and docs/mapping.md are up to date with layout/kitt.uk-UA.yaml.
    2. Configures and builds the native CMake project, producing
       src/windows -> build/windows -> kittua.dll.

    Does not require Administrator: this script only compiles, it
    does not install/register anything (KITT_ARCHITECTURE.md
    section 8: native layer should not do installer behavior).

.PARAMETER Configuration
    CMake/MSBuild configuration to build. Default: Release.

.PARAMETER SkipGenerate
    Skip the `python -m kittgen generate` step and build whatever
    kitt_tables.c currently exists on disk.

.EXAMPLE
    ./tools/build.ps1
.EXAMPLE
    ./tools/build.ps1 -Configuration Debug
#>
[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",

    [switch]$SkipGenerate
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BuildDir = Join-Path $RepoRoot "build\windows"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-CMake {
    $cmd = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe",
        "C:\Program Files\CMake\bin\cmake.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "cmake.exe not found. Install CMake or Visual Studio Build Tools' CMake component."
}

function Find-VsGenerator {
    # Prefer whatever Visual Studio / Build Tools version is actually
    # installed. A fixed list of "C:\...\2019\BuildTools" /
    # "...\2022\Community" style paths is not reliable: GitHub Actions'
    # windows-latest runner ships VS2022 Enterprise at a path this list
    # never checked, so `build.ps1` failed there with "No Visual Studio
    # / Build Tools installation found" despite VS actually being
    # present - confirmed by an actual CI run.
    #
    # vswhere.exe is the tool Microsoft ships specifically to answer
    # "what VS is installed and where" without guessing paths or
    # editions; it has shipped alongside every VS/Build Tools install
    # since VS2017, in a fixed location that itself never changes.
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -products * `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath 2>$null
        if ($installPath) {
            $versionYear = & $vswhere -latest -products * `
                -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
                -property catalog_productLineVersion 2>$null
            switch ($versionYear) {
                "2019" { return "Visual Studio 16 2019" }
                "2022" { return "Visual Studio 17 2022" }
                default {
                    # Fall through to the path-based fallback below rather
                    # than guess at a generator name for an unrecognized
                    # VS version.
                }
            }
        }
    }

    # Fallback for machines without vswhere.exe (older Build Tools-only
    # installs sometimes omit it) - same fixed-path probing as before.
    $vsRoots = @(
        @{ Path = "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools"; Generator = "Visual Studio 16 2019" },
        @{ Path = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community";  Generator = "Visual Studio 16 2019" },
        @{ Path = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional"; Generator = "Visual Studio 16 2019" },
        @{ Path = "C:\Program Files\Microsoft Visual Studio\2022\BuildTools"; Generator = "Visual Studio 17 2022" },
        @{ Path = "C:\Program Files\Microsoft Visual Studio\2022\Community"; Generator = "Visual Studio 17 2022" },
        @{ Path = "C:\Program Files\Microsoft Visual Studio\2022\Professional"; Generator = "Visual Studio 17 2022" },
        @{ Path = "C:\Program Files\Microsoft Visual Studio\2022\Enterprise"; Generator = "Visual Studio 17 2022" }
    )
    foreach ($root in $vsRoots) {
        if (Test-Path $root.Path) {
            return $root.Generator
        }
    }

    throw "No Visual Studio / Build Tools installation found. Install MSVC Build Tools with the C++ workload."
}

Write-Host "Kitt build" -ForegroundColor Green
Write-Host "Repo root: $RepoRoot"

# --- 1. Generate native source + docs from layout YAML -------------------

if (-not $SkipGenerate) {
    Write-Step "Generating kitt_tables.c / docs/mapping.md from layout/kitt.uk-UA.yaml"

    # Prefer the project venv (it has kittgen installed via
    # `pip install -e ".[dev]"` per KITT_ARCHITECTURE.md section 20);
    # fall back to whatever `python`/`py` is on PATH.
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pythonExe = $venvPython
    }
    else {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            $python = Get-Command py -ErrorAction SilentlyContinue
        }
        if (-not $python) {
            throw "Python not found. Activate/create the project venv (.venv) or install Python 3.12+."
        }
        $pythonExe = $python.Source
    }
    Write-Host "Using python: $pythonExe"

    Push-Location $RepoRoot
    try {
        & $pythonExe -m kittgen generate
        if ($LASTEXITCODE -ne 0) {
            throw "kittgen generate failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Step "Skipping generation (-SkipGenerate); using existing src/windows/kitt_tables.c"
}

# --- 2. Configure + build the native CMake project ------------------------

$cmake = Find-CMake
Write-Host "Using cmake: $cmake"

$generator = Find-VsGenerator
Write-Host "Using generator: $generator (x64)"

New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null

Write-Step "Configuring CMake project"
& $cmake -S $RepoRoot -B $BuildDir -G $generator -A x64
if ($LASTEXITCODE -ne 0) {
    throw "CMake configure failed with exit code $LASTEXITCODE"
}

Write-Step "Building kittua ($Configuration)"
& $cmake --build $BuildDir --config $Configuration --target kittua
if ($LASTEXITCODE -ne 0) {
    throw "CMake build failed with exit code $LASTEXITCODE"
}

# --- 3. Report result -------------------------------------------------------

$dllPath = Join-Path $BuildDir "src\windows\$Configuration\kittua.dll"
if (Test-Path $dllPath) {
    $size = (Get-Item $dllPath).Length
    Write-Step "Build succeeded"
    Write-Host "kittua.dll: $dllPath ($size bytes)" -ForegroundColor Green
}
else {
    throw "Build reported success but kittua.dll was not found at expected path: $dllPath"
}
