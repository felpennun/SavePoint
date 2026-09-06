param(
    [switch]$ADRs,
    [string]$LedgerPath = "docs/methodology/agent-ledger.jsonl"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$requiredHeadings = @("## Contexto", "## Alternativas consideradas", "## Decisión", "## Evidencia y fuentes", "## Consecuencias", "## Reversibilidad", "## Aprobación y revisión")
$adrFiles = @(Get-ChildItem (Join-Path $repoRoot "docs/adr") -Filter "ADR-*.md" -File)
if ($adrFiles.Count -eq 0) { throw "Evidence gate is vacuous: zero ADR files found" }
foreach ($file in $adrFiles) {
    $text = Get-Content -Raw $file.FullName
    foreach ($heading in $requiredHeadings) {
        if (-not $text.Contains($heading)) { throw "$($file.Name): missing required field '$heading'" }
    }
    if (-not $text.Contains("Autor de la decisi")) { throw "$($file.Name): missing decision author" }
    if ($text -notmatch "https://|\[EVIDENCIA:|\[FUENTE") { throw "$($file.Name): no citable evidence/source" }
}
Write-Host "PASS: $($adrFiles.Count) non-vacuous ADRs with required fields"
if ($ADRs) { exit 0 }

$allowedTypes = @("proposal", "automated-check", "author-decision")
$allowedResults = @("pass", "fail", "changed", "accepted", "rejected")
function Test-LedgerRecord($record, [switch]$Canary) {
    foreach ($field in @("timestamp", "type", "actor", "objective", "inputs", "outputs", "tools", "result", "limitations", "responsibility")) {
        if ($null -eq $record.$field) { throw "Ledger record missing '$field'" }
    }
    if ($record.timestamp -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$') { throw "Timestamp is not UTC second precision" }
    if ($record.type -notin $allowedTypes) { throw "Invalid ledger type: $($record.type)" }
    if ($record.result -notin $allowedResults) { throw "Invalid ledger result: $($record.result)" }
    if ($record.actor.kind -notin @("human", "agent")) { throw "Actor kind must be human or agent" }
    if (-not $record.actor.role) { throw "Actor role is required" }
    if ($record.type -eq "author-decision" -and $record.actor.kind -ne "human") { throw "author-decision requires a separate human actor" }
    if ($record.type -ne "author-decision" -and $record.actor.kind -eq "human") { throw "Human events must use author-decision" }
    if (@($record.tools).Count -eq 0 -or @($record.limitations).Count -eq 0) { throw "Tools and limitations must be non-empty" }
    foreach ($artifact in @($record.inputs) + @($record.outputs)) {
        if (-not $artifact.path -or $artifact.path -match '(^|[\\/])\.\.([\\/]|$)' -or [IO.Path]::IsPathRooted([string]$artifact.path)) { throw "Artifact path must be relative and contained" }
        if ($artifact.sha256 -notmatch '^[a-f0-9]{64}$') { throw "Invalid artifact SHA-256" }
        if (-not $Canary) {
            $full = Join-Path $repoRoot ([string]$artifact.path)
            if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Artifact does not exist: $($artifact.path)" }
            # Hash the content with CR bytes stripped, i.e. the LF form Git
            # stores and the form these ledger hashes were computed against.
            # Without this, every text artifact mismatches on a Windows
            # checkout where core.autocrlf has rewritten LF -> CRLF on disk.
            $raw = [System.IO.File]::ReadAllBytes($full)
            $lf = [byte[]]($raw | Where-Object { $_ -ne 13 })
            $sha = [System.Security.Cryptography.SHA256]::Create()
            try {
                $actual = ([System.BitConverter]::ToString($sha.ComputeHash($lf)) -replace '-', '').ToLowerInvariant()
            } finally { $sha.Dispose() }
            if ($actual -ne $artifact.sha256) { throw "Artifact hash mismatch: $($artifact.path)" }
        }
    }
}

# Fail-first: the gate is trusted only after both known-bad records are rejected.
$baseCanary = [pscustomobject]@{ timestamp="2026-09-04T00:00:00Z"; type="proposal"; actor=[pscustomobject]@{kind="agent";role="canary"}; objective="negative self-test"; inputs=@(); outputs=@(); tools=@("self-test"); result="fail"; limitations=@("synthetic record"); responsibility="checker only" }
$badType = $baseCanary.PSObject.Copy(); $badType.type = "success"
$badHash = $baseCanary.PSObject.Copy(); $badHash.inputs = @([pscustomobject]@{path="README.md";sha256="not-a-hash"})
foreach ($case in @($badType, $badHash)) {
    $rejected = $false
    try { Test-LedgerRecord $case -Canary } catch { $rejected = $true }
    if (-not $rejected) { throw "Fail-first canary was incorrectly accepted" }
}
Write-Host "PASS: fail-first canaries reject invalid type and hash"

$ledgerFull = Join-Path $repoRoot $LedgerPath
if (-not (Test-Path $ledgerFull -PathType Leaf)) { throw "Ledger not found: $LedgerPath" }
$lines = @(Get-Content -LiteralPath $ledgerFull | Where-Object { $_.Trim() })
if ($lines.Count -eq 0) { throw "Evidence gate is vacuous: zero ledger entries" }
$records = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
    try { $record = $lines[$i] | ConvertFrom-Json } catch { throw "Ledger line $($i + 1) is invalid JSON" }
    Test-LedgerRecord $record
    $records += $record
}
foreach ($type in $allowedTypes) { if (@($records | Where-Object type -eq $type).Count -eq 0) { throw "Ledger lacks type '$type'" } }
foreach ($role in @("gsd-phase-researcher", "gsd-ui-researcher", "gsd-planner", "gsd-executor")) {
    if (@($records | Where-Object { $_.actor.role -eq $role }).Count -eq 0) { throw "Ledger lacks role '$role'" }
}
if (@($records | Where-Object result -eq "fail").Count -eq 0 -or @($records | Where-Object result -eq "changed").Count -eq 0) { throw "Ledger must record failures and changes, not only successes" }

$evidenceText = (Get-Content -Raw $ledgerFull) + "`n" + (Get-Content -Raw (Join-Path $repoRoot "docs/methodology/agent-method.md"))
$secretPatterns = @(
    '(?i)-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    '(?i)(password|secret|api[_-]?key|access[_-]?token)\s*[=:]\s*["''][^"'']{8,}["'']',
    '(?i)bearer\s+[a-z0-9._~-]{16,}'
)
foreach ($pattern in $secretPatterns) { if ($evidenceText -match $pattern) { throw "Potential secret-like value in methodology evidence" } }
Write-Host "PASS: $($records.Count) ledger entries; schema, types, actors, paths, hashes, coverage and secret scan valid"
