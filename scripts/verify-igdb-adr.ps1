<#
.SYNOPSIS
    Deterministic content gate for docs/adr/ADR-006-igdb-source.md
    (Plan 01.1-01 Task 3, requirement DATA-04).

.DESCRIPTION
    Independently parses ADR-006 and requires that the DATA-04 decision is
    actually argued, not just titled: all three candidates, all seven
    comparison axes with recorded values, a link to the authenticated probe,
    the eligible-category import boundary, the cover delivery/storage rule,
    the Phase 1 offline-corpus preservation rule, and the exact requests pin.

    Network-free. Fails closed on any missing element.
#>

[CmdletBinding()]
param(
    [string]$AdrPath
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $AdrPath) { $AdrPath = Join-Path $RepoRoot "docs/adr/ADR-006-igdb-source.md" }

if (-not (Test-Path $AdrPath -PathType Leaf)) {
    Write-Host "FAIL: ADR not found: $AdrPath" -ForegroundColor Red
    exit 1
}

$text = Get-Content -LiteralPath $AdrPath -Raw
$failures = New-Object System.Collections.Generic.List[string]

function Need {
    param([string]$Label, [string]$Pattern)
    if ($script:text -notmatch $Pattern) {
        $script:failures.Add($Label)
        Write-Host "  [x] $Label" -ForegroundColor Red
    } else {
        Write-Host "  [ok] $Label" -ForegroundColor Green
    }
}

Write-Host "== verify-igdb-adr: $AdrPath ==" -ForegroundColor Cyan

# --- Three candidates -------------------------------------------------------
Need "Candidate: IGDB"            'IGDB'
Need "Candidate: RAWG"            'RAWG'
Need "Candidate: scaled Wikidata" '(?i)scaled Wikidata'

# --- Seven DATA-04 axes, each present AS A TABLE ROW LABEL ----------------
Need "Axis: Coverage"    '\|\s*\*\*Coverage\*\*\s*\|'
Need "Axis: Platforms"   '\|\s*\*\*Platforms\*\*\s*\|'
Need "Axis: Licence"     '\|\s*\*\*Licence\*\*\s*\|'
Need "Axis: Attribution" '\|\s*\*\*Attribution\*\*\s*\|'
Need "Axis: Quotas"      '\|\s*\*\*Quotas\*\*\s*\|'
Need "Axis: Stability"   '\|\s*\*\*Stability\*\*\s*\|'
Need "Axis: Cost"        '\|\s*\*\*Cost\*\*\s*\|'

# --- Axes carry recorded values, not empty cells -------------------------
Need "Coverage row has measured counts"      '(?m)^\|\s*\*\*Coverage\*\*.*374,555.*312,418'
Need "Quotas row has the rate-limit numbers" '(?m)^\|\s*\*\*Quotas\*\*.*4 requests/second.*8 concurrent'
Need "Cost row is stated for all candidates" '(?m)^\|\s*\*\*Cost\*\*.*\|.*\|.*\|.*\|'

# --- Decision content ---------------------------------------------------
Need "Chooses IGDB per D-05"                 '(?i)Adopt IGDB v4 as the real-scale catalogue source'
Need "Link to the authenticated probe"       '\.\./verification/igdb-api-probe\.md'
Need "Eligible-category boundary stated"     '(?i)Eligible-category boundary.*game_type\s*=\s*0.*312,418'
Need "game_type 1-14 excluded"               '(?i)game_type.{0,6}1.{0,4}14.*(excluded|non-primary)'
Need "Cover delivery/storage rule"           '(?i)Cover delivery / storage rule.*hotlinked'
Need "Cover URL construction recorded"       'images\.igdb\.com/igdb/image/upload/t_\{size\}/\{hash\}\.jpg'
Need "Placeholder fallback for covers"       '(?i)first-party placeholder'
Need "Phase 1 offline corpus preserved"      '(?i)Preserve the Phase 1 offline corpus.*retained unchanged'
Need "Request-time no-provider rule kept"    '(?i)CAT-06.*OPS-03.*no provider is called at request time'
Need "Exact requests pin recorded"           'requests==2\.34\.2'
Need "allauth / dj-rest-auth explicitly rejected" '(?i)Do not\*\*? add .*django-allauth.*dj-rest-auth'

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "FAIL: $($failures.Count) required ADR element(s) missing:" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}
Write-Host "PASS: ADR-006 covers all DATA-04 axes, cites the probe, and fixes the import boundary + cover rule." -ForegroundColor Green
exit 0
