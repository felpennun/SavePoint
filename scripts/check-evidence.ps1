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

if (-not (Test-Path (Join-Path $repoRoot $LedgerPath))) { throw "Ledger not found: $LedgerPath" }
Write-Host "PASS: ADR-only bootstrap complete; ledger validation enabled when methodology exists"
