<#
.SYNOPSIS
    Kitt canonical packaging entrypoint (KITT_ARCHITECTURE.md
    section 11 "Build System" / section 10 "Installer Architecture").

.DESCRIPTION
    1. Calls tools/build.ps1 so kittua.dll is up to date with the
       current layout/kitt.uk-UA.yaml.
    2. Locates the WiX CLI (may not be on PATH) and invokes
       `wix build` against installer/wix/Package.wxs +
       installer/wix/Components.wxs, producing
       dist/kitt-<version>-x64.msi.
    3. Writes a SHA-256 checksum file next to the MSI
       (KITT_ARCHITECTURE.md section 11: "SHA-256 checksums are
       created").

    Does NOT require Administrator: this script only builds/compiles
    files on disk, it never runs msiexec or installs anything. See
    installer/README.md for why the resulting MSI should only be
    installed in a disposable test VM, never on a development
    machine.

.PARAMETER Configuration
    CMake/MSBuild configuration to build kittua.dll with. Default:
    Release.

.PARAMETER SkipBuild
    Skip calling tools/build.ps1 and package whatever kittua.dll
    already exists in build/windows. Useful for iterating on the WiX
    source without rebuilding the DLL every time.

.EXAMPLE
    ./tools/package.ps1
#>
[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",

    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BuildDir = Join-Path $RepoRoot "build\windows"
$DistDir = Join-Path $RepoRoot "dist"
$ProductVersion = "0.1.0" # keep in sync with layout/kitt.uk-UA.yaml layout.version and installer/wix/Package.wxs

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-Wix {
    # `wix` may not be on PATH even when installed as a dotnet global
    # tool (see architecture notes / dev session history for this
    # project). Prefer PATH, then fall back to the well-known dotnet
    # global tools location.
    $cmd = Get-Command wix -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidate = Join-Path $env:USERPROFILE ".dotnet\tools\wix.exe"
    if (Test-Path $candidate) {
        return $candidate
    }

    throw "wix CLI not found on PATH or at $candidate. Install it with: dotnet tool install --global wix"
}

# --- 1. Build kittua.dll ----------------------------------------------------

if (-not $SkipBuild) {
    Write-Step "Building kittua.dll via tools/build.ps1"
    & (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
    if ($LASTEXITCODE -ne 0) {
        throw "tools/build.ps1 failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Step "Skipping build (-SkipBuild); packaging existing kittua.dll"
}

$dllPath = Join-Path $BuildDir "src\windows\$Configuration\kittua.dll"
if (-not (Test-Path $dllPath)) {
    throw "kittua.dll not found at expected path: $dllPath. Run tools/build.ps1 first (or omit -SkipBuild)."
}
Write-Host "Using kittua.dll: $dllPath"

# --- 2. Locate WiX and build the MSI ----------------------------------------

Write-Step "Locating WiX CLI"
$wix = Find-Wix
Write-Host "Using wix: $wix"
Write-Host (& $wix --version)

# WiX Toolset v7 requires accepting the Open Source Maintenance Fee
# (OSMF) EULA before any real command will run. This is a licensing
# decision for a human to make once, not something this script should
# silently accept on your behalf. Detect it up front and fail with a
# clear instruction instead of a raw WIX7015 error mid-build.
$eulaMarker = Join-Path $env:USERPROFILE ".wix\wix7-osmf-eula.txt"
if (-not (Test-Path $eulaMarker)) {
    Write-Host ""
    Write-Host "WiX Toolset v7 requires accepting its EULA before it can build anything." -ForegroundColor Yellow
    Write-Host "This is a one-time, per-user decision. Review https://wixtoolset.org/osmf/" -ForegroundColor Yellow
    Write-Host "then run:" -ForegroundColor Yellow
    Write-Host "    wix eula accept wix7" -ForegroundColor Yellow
    throw "WiX EULA not yet accepted (expected marker at $eulaMarker)."
}

Write-Step "Ensuring WixToolset.UI.wixext extension is available"
$extList = & $wix extension list 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "wix extension list failed:`n$extList"
}
if ($extList -notmatch "WixToolset\.UI\.wixext") {
    Write-Host "Adding WixToolset.UI.wixext (required by Package.wxs WixUI reference)..."
    & $wix extension add WixToolset.UI.wixext
    if ($LASTEXITCODE -ne 0) {
        throw "wix extension add WixToolset.UI.wixext failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host "WixToolset.UI.wixext already present."
}

New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

$msiName = "kitt-$ProductVersion-x64.msi"
$msiPath = Join-Path $DistDir $msiName

Write-Step "Building $msiName with wix build"
$wixSources = @(
    (Join-Path $RepoRoot "installer\wix\Package.wxs"),
    (Join-Path $RepoRoot "installer\wix\Components.wxs")
)
$locFile = Join-Path $RepoRoot "installer\wix\Localization.wxl"

& $wix build `
    $wixSources `
    -loc $locFile `
    -ext WixToolset.UI.wixext `
    -arch x64 `
    -d "KittuaDllPath=$dllPath" `
    -out $msiPath

if ($LASTEXITCODE -ne 0) {
    throw "wix build failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path $msiPath)) {
    throw "wix build reported success but $msiPath was not found."
}

# --- 3. SHA-256 checksum -----------------------------------------------------

Write-Step "Writing SHA-256 checksum"
$hash = Get-FileHash -Path $msiPath -Algorithm SHA256
$checksumPath = "$msiPath.sha256"
# Standard `sha256sum`-style format: "<hash> *<filename>"
"$($hash.Hash.ToLowerInvariant())  $msiName" | Out-File -FilePath $checksumPath -Encoding ascii -NoNewline
Write-Host "Wrote $checksumPath"

# --- 4. Report ---------------------------------------------------------------

$size = (Get-Item $msiPath).Length
Write-Step "Package succeeded"
Write-Host "MSI: $msiPath ($size bytes)" -ForegroundColor Green
Write-Host "SHA-256: $($hash.Hash)" -ForegroundColor Green
Write-Host ""
Write-Host "Do not run msiexec /i on this MSI on your development machine." -ForegroundColor Yellow
Write-Host "Test it in a disposable Windows VM only (see installer/README.md)." -ForegroundColor Yellow
