<#
.SYNOPSIS
    Fail-first secret gate (SEC-02, Plan 01-11 Task 2).

.DESCRIPTION
    Self-tests against the synthetic canaries in e2e/fixtures/hostile.json
    (secretCanaries) FIRST -- if this scanner cannot detect its own known-bad
    values, a clean result against the real tree would not be trustworthy,
    so the whole run fails before any real scan happens (TDD: prove the test
    can fail before trusting it can pass).

    Then scans, non-emptily, the four surfaces from the Plan 01-11 threat
    model (T-06-01: Git/bundle/image/log):
      1. Every Git-tracked file (repo).
      2. The built Next.js static output + source maps (browser bundle),
         copied out of the running `web` container -- apps/web/.next lives
         only in that container's anonymous volume, never on the host.
      3. `docker history`/`docker inspect` of both built images (layers).
      4. Captured `docker compose logs` output.

    A match is only allowed through if its captured value is exactly one of
    the project's own documented, inert, local-dev-only placeholders
    (D-02) -- never by skipping a whole file or surface.

.NOTES
    Run after `docker compose -f infra/compose.yaml up --build --wait`
    (Task 1) -- the image/log/build surfaces require the stack to exist.
#>

[CmdletBinding()]
param(
    [switch]$IncludeDeployment
)

# "Continue", not "Stop": every native docker/git call below is checked
# explicitly via $LASTEXITCODE/output, and PowerShell 5.1 wraps a native
# command's stderr output as a terminating NativeCommandError under "Stop"
# even on a zero exit code (e.g. docker's own progress text) -- this script
# reports its own failures deliberately instead of relying on that.
$ErrorActionPreference = "Continue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ComposeFile = Join-Path $RepoRoot "infra/compose.yaml"
$ExitCode = 0

# ---------------------------------------------------------------------------
# Patterns: generic shapes of real leaked-secret classes, not project-
# specific strings. Each has a matching synthetic canary in hostile.json's
# secretCanaries so the self-test phase below can prove every one actually
# fires before the real scan is trusted.
# ---------------------------------------------------------------------------
$Patterns = @(
    [PSCustomObject]@{ Name = "aws-access-key-id";        Regex = "AKIA[0-9A-Z]{16}" }
    [PSCustomObject]@{ Name = "generic-secret-key";        Regex = "sk-[A-Za-z0-9]{20,}" }
    [PSCustomObject]@{ Name = "private-key-header";        Regex = "-----BEGIN [A-Z ]*PRIVATE KEY-----" }
    # The value itself must contain a digit and avoid ()? -- excludes plain
    # dictionary/label words (e.g. a Spanish i18n dictionary's own
    # `password: "Contraseña"` entry) and minified-JS noise (e.g. a
    # coincidental `...cookie.split("=")...` fragment landing right after
    # the literal substring "token=") while still catching real secret-
    # shaped values including the CanarySecretValue1234! self-test canary.
    [PSCustomObject]@{ Name = "assigned-secret-value";     Regex = "(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[\'`"](?=[^\'`"]*\d)[^\'`"()?]{8,}[\'`"]" }
    [PSCustomObject]@{ Name = "bearer-token";              Regex = "(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}" }
    [PSCustomObject]@{ Name = "next-public-sensitive-name"; Regex = "(?i)NEXT_PUBLIC_[A-Z0-9_]*(PASSWORD|SECRET|TOKEN|API[_-]?KEY)[A-Z0-9_]*" }
    [PSCustomObject]@{ Name = "docker-arg-sensitive-name"; Regex = "(?im)^\s*ARG\s+[A-Za-z0-9_]*(PASSWORD|SECRET|TOKEN|API[_-]?KEY)[A-Za-z0-9_]*" }
)

# Exact values this project deliberately commits as inert, documented,
# local-dev-only placeholders (D-02: never a real infrastructure secret --
# see README.md "Configuracion" and .env.example). A match is allowed
# through only when its captured text CONTAINS one of these -- anything else
# matching the same shape still fails, including a real secret that happened
# to be assigned to the same variable name.
$KnownSafeValues = @(
    "local-development-only-not-a-secret-please-set-a-real-one-in-deploy"
    "local_test_only"
    "SavePoint-Demo-2026-Visit!"
    # Additional local-dev demo-account passwords in infra/compose.yaml's
    # DEMO_ACCOUNTS contract (AUTH-02 / SC3). Same D-02 spirit: inert local
    # placeholders, overridden with real values via `sync: false` in deploy.
    "SavePoint-Demo-2026-Critico!"
    "SavePoint-Demo-2026-Coleccion!"
)

function Test-Content {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Origin
    )
    $hits = New-Object System.Collections.Generic.List[object]
    foreach ($p in $Patterns) {
        foreach ($m in [regex]::Matches($Text, $p.Regex)) {
            $isSafe = $false
            foreach ($safe in $KnownSafeValues) {
                if ($m.Value.Contains($safe)) { $isSafe = $true; break }
            }
            if (-not $isSafe) {
                $snippet = $m.Value.Substring(0, [Math]::Min(60, $m.Value.Length))
                $hits.Add([PSCustomObject]@{ Origin = $Origin; Pattern = $p.Name; Snippet = $snippet })
            }
        }
    }
    return $hits
}

function Get-ExemptPatternNames {
    # Narrow, reviewed, path-based exemptions only -- never a blanket file
    # skip that would hide a real secret pasted into the same file.
    param([Parameter(Mandatory = $true)][string]$RelPath)
    $exempt = New-Object System.Collections.Generic.List[string]
    $normalized = $RelPath -replace "\\", "/"
    if ($normalized -eq "e2e/fixtures/hostile.json") {
        # This file's entire documented purpose (see its own secretCanaries
        # block) is holding synthetic values shaped exactly like these
        # patterns, so this scanner can self-test against them -- exempt
        # every pattern here, and only here.
        foreach ($p in $Patterns) { $exempt.Add($p.Name) }
        return $exempt
    }
    $isTestFile = ($normalized -match "(^|/)tests?/") -or ($normalized -match "\.(spec|test)\.tsx?$")
    if ($isTestFile) {
        # Synthetic, reviewed test-fixture passwords/tokens (Django test
        # users, Playwright fixtures) are a normal, expected pattern here --
        # still scanned for the other five higher-severity shapes (real
        # credential formats, sensitive NEXT_PUBLIC_/ARG names).
        $exempt.Add("assigned-secret-value")
        $exempt.Add("bearer-token")
    }
    return $exempt
}

function Write-Hits {
    param([System.Collections.Generic.List[object]]$Hits)
    foreach ($h in $Hits) {
        Write-Host ("  [{0}] {1}: {2}" -f $h.Pattern, $h.Origin, $h.Snippet) -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
# Phase 0: self-test against synthetic canaries (fail-first).
# ---------------------------------------------------------------------------
Write-Host "== Phase 0: self-test against e2e/fixtures/hostile.json canaries ==" -ForegroundColor Cyan

$hostilePath = Join-Path $RepoRoot "e2e/fixtures/hostile.json"
if (-not (Test-Path $hostilePath)) {
    Write-Host "FAIL: e2e/fixtures/hostile.json not found -- cannot self-test the scanner." -ForegroundColor Red
    exit 1
}
$hostile = Get-Content $hostilePath -Raw | ConvertFrom-Json
$canaries = $hostile.secretCanaries
if ($null -eq $canaries) {
    Write-Host "FAIL: hostile.json has no secretCanaries block -- cannot self-test the scanner." -ForegroundColor Red
    exit 1
}

$expectedCanaryPattern = [ordered]@{
    "aws-access-key-id"             = $canaries.awsAccessKeyId
    "generic-secret-key"            = $canaries.genericApiSecretKey
    "private-key-header"            = $canaries.privateKeyHeader
    "assigned-secret-value"         = $canaries.assignedSecretValue
    "bearer-token"                  = $canaries.bearerToken
    "next-public-sensitive-name"    = $canaries.nextPublicSensitiveName
    "docker-arg-sensitive-name"     = $canaries.dockerArgSensitiveName
}

$selfTestFailures = 0
foreach ($patternName in $expectedCanaryPattern.Keys) {
    $canaryValue = $expectedCanaryPattern[$patternName]
    if ([string]::IsNullOrWhiteSpace($canaryValue)) {
        Write-Host "FAIL (self-test): hostile.json is missing the canary value for '$patternName'." -ForegroundColor Red
        $selfTestFailures++
        continue
    }
    $hits = Test-Content -Text $canaryValue -Origin "self-test:$patternName"
    $matched = $hits | Where-Object { $_.Pattern -eq $patternName }
    if (-not $matched) {
        Write-Host "FAIL (self-test): pattern '$patternName' did NOT detect its own canary value -- scanner is not trustworthy." -ForegroundColor Red
        $selfTestFailures++
    }
}

if ($selfTestFailures -gt 0) {
    Write-Host "Self-test failed ($selfTestFailures pattern(s)) -- refusing to run the real scan." -ForegroundColor Red
    exit 1
}
Write-Host "Self-test passed: all $($expectedCanaryPattern.Keys.Count) patterns detected their own synthetic canary." -ForegroundColor Green

$allHits = New-Object System.Collections.Generic.List[object]

# ---------------------------------------------------------------------------
# Phase 1: every Git-tracked file.
# ---------------------------------------------------------------------------
Write-Host "`n== Phase 1: Git-tracked files ==" -ForegroundColor Cyan
Push-Location $RepoRoot
try {
    $trackedFiles = git ls-files
} finally {
    Pop-Location
}
$binaryExtensions = @(".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".pdf")
$gitScanned = 0
foreach ($relPath in $trackedFiles) {
    $fullPath = Join-Path $RepoRoot $relPath
    if (-not (Test-Path $fullPath -PathType Leaf)) { continue }
    $ext = [System.IO.Path]::GetExtension($relPath).ToLowerInvariant()
    if ($binaryExtensions -contains $ext) { continue }
    $text = Get-Content -LiteralPath $fullPath -Raw -ErrorAction SilentlyContinue
    if ($null -eq $text) { continue }
    $gitScanned++
    $exempt = Get-ExemptPatternNames -RelPath $relPath
    $hits = Test-Content -Text $text -Origin "git:$relPath" | Where-Object { $exempt -notcontains $_.Pattern }
    foreach ($h in $hits) { $allHits.Add($h) }
}
if ($gitScanned -eq 0) {
    Write-Host "FAIL: scanned 0 Git-tracked files -- surface not actually covered." -ForegroundColor Red
    $ExitCode = 1
} else {
    Write-Host "Scanned $gitScanned Git-tracked file(s)."
}

if ($IncludeDeployment) {
    Write-Host "`n== Phase 1b: deployment sources ==" -ForegroundColor Cyan
    $deploymentPaths = @(
        "infra/render.yaml",
        "neon.ts",
        "apps/web/vercel.json",
        "docs/deployment/public-demo.md",
        "docs/adr/ADR-005-deployment-parity.md",
        "e2e/deployed-smoke.spec.ts"
    )
    $deploymentScanned = 0
    foreach ($relPath in $deploymentPaths) {
        $fullPath = Join-Path $RepoRoot $relPath
        if (-not (Test-Path $fullPath -PathType Leaf)) { continue }
        $text = Get-Content -LiteralPath $fullPath -Raw
        $deploymentScanned++
        $exempt = Get-ExemptPatternNames -RelPath $relPath
        $hits = Test-Content -Text $text -Origin "deployment:$relPath" | Where-Object { $exempt -notcontains $_.Pattern }
        foreach ($h in $hits) { $allHits.Add($h) }
    }
    if ($deploymentScanned -ne $deploymentPaths.Count) {
        Write-Host "FAIL: deployment scan covered $deploymentScanned/$($deploymentPaths.Count) required file(s)." -ForegroundColor Red
        $ExitCode = 1
    } else {
        Write-Host "Scanned all $deploymentScanned deployment source file(s), including infra/render.yaml."
    }

    # Render tokenizes dockerCommand as argv rather than evaluating shell
    # control syntax. Keep the Blueprint command deliberately simple and
    # delegate sequencing/PORT expansion to the in-image POSIX script.
    $renderPath = Join-Path $RepoRoot "infra/render.yaml"
    $renderText = Get-Content -LiteralPath $renderPath -Raw
    $commandLines = @([regex]::Matches($renderText, "(?m)^\s*dockerCommand:\s*(.+?)\s*$"))
    $expectedCommand = "sh /workspace/apps/api/render-start.sh"
    if ($commandLines.Count -ne 1 -or $commandLines[0].Groups[1].Value -ne $expectedCommand) {
        Write-Host "FAIL: infra/render.yaml must contain exactly 'dockerCommand: $expectedCommand'." -ForegroundColor Red
        $ExitCode = 1
    }
    if ($commandLines.Count -eq 1 -and $commandLines[0].Groups[1].Value -match "&&|\$\{|sh\s+-c") {
        Write-Host "FAIL: Render dockerCommand contains shell-control syntax that Render will tokenize as arguments." -ForegroundColor Red
        $ExitCode = 1
    }
    $renderStartPath = Join-Path $RepoRoot "apps/api/render-start.sh"
    if (-not (Test-Path $renderStartPath -PathType Leaf)) {
        Write-Host "FAIL: apps/api/render-start.sh is missing." -ForegroundColor Red
        $ExitCode = 1
    }
}

# ---------------------------------------------------------------------------
# Phase 2: built Next.js static output + source maps (browser bundle).
# apps/web/.next only exists inside the `web` container's anonymous volume
# (infra/compose.yaml deliberately masks the host bind mount there so a
# stale host build never leaks in) -- copy it out to scan it.
# ---------------------------------------------------------------------------
Write-Host "`n== Phase 2: Next.js build output (browser bundle) ==" -ForegroundColor Cyan
$tempNextDir = Join-Path ([System.IO.Path]::GetTempPath()) ("savepoint-next-scan-" + [Guid]::NewGuid().ToString("N"))
$buildScanned = 0
try {
    docker compose -f $ComposeFile cp "web:/workspace/apps/web/.next" $tempNextDir | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tempNextDir)) {
        Write-Host "FAIL: could not copy apps/web/.next out of the 'web' container -- run 'docker compose -f infra/compose.yaml up --build --wait' first." -ForegroundColor Red
        $ExitCode = 1
    } else {
        $buildFiles = Get-ChildItem -Path $tempNextDir -Recurse -File -Include "*.js", "*.map", "*.html", "*.json" -ErrorAction SilentlyContinue
        foreach ($f in $buildFiles) {
            $text = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
            if ($null -eq $text) { continue }
            $buildScanned++
            $relLabel = $f.FullName.Substring($tempNextDir.Length).TrimStart("\", "/")
            $hits = Test-Content -Text $text -Origin "build:$relLabel"
            foreach ($h in $hits) { $allHits.Add($h) }
        }
        if ($buildScanned -eq 0) {
            Write-Host "FAIL: scanned 0 build-output files -- surface not actually covered." -ForegroundColor Red
            $ExitCode = 1
        } else {
            Write-Host "Scanned $buildScanned build-output file(s)."
        }
    }
} finally {
    if (Test-Path $tempNextDir) { Remove-Item -Recurse -Force $tempNextDir -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------------------
# Phase 3: Docker image history and inspect output (layers).
# ---------------------------------------------------------------------------
Write-Host "`n== Phase 3: Docker image history/layers ==" -ForegroundColor Cyan
$images = @("savepoint-api", "savepoint-web")
$imagesScanned = 0
foreach ($img in $images) {
    docker image inspect $img --format "{{.Id}}" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAIL: Docker image '$img' not found -- run 'docker compose -f infra/compose.yaml up --build --wait' first." -ForegroundColor Red
        $ExitCode = 1
        continue
    }
    $history = docker history --no-trunc $img | Out-String
    $inspect = docker inspect $img | Out-String
    $text = $history + "`n" + $inspect
    $imagesScanned++
    $hits = Test-Content -Text $text -Origin "image:$img"
    foreach ($h in $hits) { $allHits.Add($h) }
}
if ($imagesScanned -eq 0) {
    Write-Host "FAIL: scanned 0 Docker images -- surface not actually covered." -ForegroundColor Red
    $ExitCode = 1
} else {
    Write-Host "Scanned $imagesScanned Docker image(s)."
}

# ---------------------------------------------------------------------------
# Phase 4: captured `docker compose logs` output.
# ---------------------------------------------------------------------------
Write-Host "`n== Phase 4: captured docker compose logs ==" -ForegroundColor Cyan
$logsText = docker compose -f $ComposeFile logs --no-color | Out-String
if ([string]::IsNullOrWhiteSpace($logsText)) {
    Write-Host "FAIL: captured 0 bytes of docker compose logs -- is the stack running ('docker compose up --wait')?" -ForegroundColor Red
    $ExitCode = 1
} else {
    Write-Host ("Captured {0} byte(s) of log output." -f $logsText.Length)
    $hits = Test-Content -Text $logsText -Origin "logs"
    foreach ($h in $hits) { $allHits.Add($h) }
}

# ---------------------------------------------------------------------------
# Verdict.
# ---------------------------------------------------------------------------
Write-Host "`n== Result ==" -ForegroundColor Cyan
if ($allHits.Count -gt 0) {
    Write-Host "FAIL: $($allHits.Count) non-allowlisted secret-shaped match(es) found:" -ForegroundColor Red
    Write-Hits -Hits $allHits
    exit 1
}
if ($ExitCode -ne 0) {
    Write-Host "FAIL: one or more surfaces were not actually scanned (see above)." -ForegroundColor Red
    exit $ExitCode
}
Write-Host "PASS: all four surfaces scanned non-emptily, zero non-allowlisted secret-shaped matches." -ForegroundColor Green
exit 0
