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

# No -G here: let CMake auto-detect the installed Visual Studio
# generator itself, rather than this script guessing a generator
# string from a fixed list of install paths. A hand-maintained path
# list is not reliable across machines/CI images - GitHub Actions'
# windows-latest runner ships VS2022 Enterprise at a path an earlier
# version of this script never checked, and even querying
# vswhere.exe for the "VC.Tools.x86.x64" component came back empty
# there, confirmed by an actual CI run. CMake's own generator
# detection is exactly the mechanism `cmake --help` documents for
# "pick whatever's installed" and needs no guesswork here.
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null

Write-Step "Configuring CMake project"
& $cmake -S $RepoRoot -B $BuildDir -A x64
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
