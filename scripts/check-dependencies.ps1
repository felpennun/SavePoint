[CmdletBinding()]
param(
    [string]$CanaryPackage
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$approvedNpm = [ordered]@{
    "@neon/config" = "1.2.0"
    "@neon/env" = "1.2.0"
    "next" = "16.3.4"
    "react" = "19.2.7"
    "react-dom" = "19.2.7"
    "@playwright/test" = "1.62.1"
    "@tailwindcss/postcss" = "4.3.3"
    "@testing-library/react" = "16.3.3"
    "@types/node" = "24.13.0"
    "@types/react" = "19.2.18"
    "@types/react-dom" = "19.2.7"
    "axe-core" = "4.13.0"
    "tailwindcss" = "4.3.3"
    "typescript" = "6.0.3"
    "vitest" = "5.0.0"
}
$approvedPython = [ordered]@{
    "Django" = "5.2.17"
    "djangorestframework" = "3.18.0"
    "psycopg[binary]" = "3.3.5"
    "pytest" = "9.1.1"
    "pytest-django" = "4.14.0"
}

function Test-ExactVersion([string]$version) {
    return $version -match '^\d+\.\d+\.\d+$'
}

# Fail-first controls: values commonly used to bypass reproducible pins must
# remain rejected even if a future manifest change accidentally introduces one.
foreach ($floatingVersion in @("latest", "^16.3.4", "~16.3.4", "16.x")) {
    if (Test-ExactVersion $floatingVersion) {
        throw "Floating-version negative control was unexpectedly accepted: $floatingVersion"
    }
}

if ($CanaryPackage) {
    if (-not $approvedNpm.Contains($CanaryPackage) -and -not $approvedPython.Contains($CanaryPackage)) {
        Write-Error "Rejected unapproved dependency canary: $CanaryPackage"
    }
}

$package = Get-Content -Raw (Join-Path $root "package.json") | ConvertFrom-Json
$workspace = Get-Content -Raw (Join-Path $root "pnpm-workspace.yaml")
function Get-CatalogVersion([string]$name) {
    $escaped = [regex]::Escape($name)
    $match = [regex]::Match($workspace, "(?m)^\s{2}'?$escaped'?:\s*([^\s#]+)\s*$")
    if (-not $match.Success) { throw "Catalog dependency missing: $name" }
    return $match.Groups[1].Value
}
$actualNpm = [ordered]@{}
foreach ($section in @("dependencies", "devDependencies")) {
    foreach ($property in $package.$section.PSObject.Properties) {
        $actualNpm[$property.Name] = [string]$property.Value
    }
}
foreach ($entry in $actualNpm.GetEnumerator()) {
    if (-not $approvedNpm.Contains($entry.Key)) { throw "Unapproved npm dependency: $($entry.Key)" }
    $resolvedVersion = if ($entry.Value -eq "catalog:") { Get-CatalogVersion $entry.Key } else { $entry.Value }
    if ($approvedNpm[$entry.Key] -ne $resolvedVersion -or -not (Test-ExactVersion $resolvedVersion)) {
        throw "npm dependency is not exactly approved: $($entry.Key)@$($entry.Value)"
    }
}
foreach ($entry in $approvedNpm.GetEnumerator()) {
    if (-not $actualNpm.Contains($entry.Key)) { throw "Approved npm dependency missing: $($entry.Key)" }
}
if ($package.packageManager -ne "pnpm@11.25.0") { throw "pnpm must be fixed at 11.25.0" }
if ($package.engines.node -ne "24.13.0") { throw "Node must be fixed at 24.13.0" }

$toml = Get-Content -Raw (Join-Path $root "pyproject.toml")
foreach ($entry in $approvedPython.GetEnumerator()) {
    $escaped = [regex]::Escape("$($entry.Key)==$($entry.Value)")
    if ($toml -notmatch $escaped) { throw "Approved Python dependency missing or not exact: $($entry.Key)" }
}
if ($toml -notmatch 'requires-python\s*=\s*"==3\.13\.\*"') { throw "Python must be constrained to 3.13.x" }
if ($toml -notmatch 'required-version\s*=\s*"==0\.12\.9"') { throw "uv must be fixed at 0.12.9" }

foreach ($lock in @("pnpm-lock.yaml", "uv.lock")) {
    if (-not (Test-Path (Join-Path $root $lock))) { throw "Missing generated lockfile: $lock" }
}

$pnpmLock = Get-Content -Raw (Join-Path $root "pnpm-lock.yaml")
foreach ($entry in $approvedNpm.GetEnumerator()) {
    $escapedName = [regex]::Escape($entry.Key)
    $escapedVersion = [regex]::Escape($entry.Value)
    $declaredVersion = $actualNpm[$entry.Key]
    $specifier = if ($declaredVersion -eq "catalog:") { "'catalog:'" } else { $escapedVersion }
    if ($pnpmLock -notmatch "(?ms)^\s{6}'?$escapedName'?:\s*\r?\n\s{8}specifier:\s*$specifier\s*\r?\n\s{8}version:\s*$escapedVersion(?:\(|\s*$)") {
        throw "pnpm lock importer missing exact approved pin: $($entry.Key)@$($entry.Value)"
    }
}
if ($pnpmLock -match '(?m)^\s+specifier:\s*(latest|[~^*]|\d+\.x)') {
    throw "pnpm lock contains a floating direct specifier"
}

$uvLock = Get-Content -Raw (Join-Path $root "uv.lock")
foreach ($entry in $approvedPython.GetEnumerator()) {
    $normalizedName = $entry.Key -replace '\[binary\]', ''
    $escapedName = [regex]::Escape($normalizedName.ToLowerInvariant())
    $escapedVersion = [regex]::Escape($entry.Value)
    $lockPattern = '(?ms)^name = "{0}"\s*\r?\nversion = "{1}"' -f $escapedName, $escapedVersion
    if ($uvLock -notmatch $lockPattern) {
        throw "uv lock missing exact approved package: $normalizedName==$($entry.Value)"
    }
}

$docs = Get-Content -Raw (Join-Path $root "docs/verification/dependency-legitimacy.md")
foreach ($needle in @(
    "sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689",
    "sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f",
    "sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280",
    "sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e"
)) {
    if (-not $docs.Contains($needle)) { throw "Approved OCI digest missing from evidence: $needle" }
}

Write-Host "Dependency allowlist and immutable OCI references validated."
