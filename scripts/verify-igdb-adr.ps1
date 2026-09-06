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
# ADR-006 prose is Spanish (project convention: thesis docs in Spanish, code in
# English); these patterns match the Spanish text. Language-neutral tokens
# (numbers, IDs, URLs, code) are matched verbatim.
Need "Candidate: IGDB"            'IGDB'
Need "Candidate: RAWG"            'RAWG'
Need "Candidate: scaled Wikidata" '(?i)scaled Wikidata'

# --- Seven DATA-04 axes, each present AS A TABLE ROW LABEL ----------------
Need "Axis: Coverage"    '\|\s*\*\*Cobertura\*\*\s*\|'
Need "Axis: Platforms"   '\|\s*\*\*Plataformas\*\*\s*\|'
Need "Axis: Licence"     '\|\s*\*\*Licencia\*\*\s*\|'
Need "Axis: Attribution" '\|\s*\*\*Atribución\*\*\s*\|'
Need "Axis: Quotas"      '\|\s*\*\*Cuotas\*\*\s*\|'
Need "Axis: Stability"   '\|\s*\*\*Estabilidad\*\*\s*\|'
Need "Axis: Cost"        '\|\s*\*\*Coste\*\*\s*\|'

# --- Axes carry recorded values, not empty cells -------------------------
Need "Coverage row has measured counts"      '(?m)^\|\s*\*\*Cobertura\*\*.*374,555.*312,418'
Need "Quotas row has the rate-limit numbers" '(?m)^\|\s*\*\*Cuotas\*\*.*4 requests/second.*8 concurrent'
Need "Cost row is stated for all candidates" '(?m)^\|\s*\*\*Coste\*\*.*\|.*\|.*\|.*\|'

# --- Decision content ---------------------------------------------------
Need "Chooses IGDB per D-05"                 '(?i)Adoptar IGDB v4 como la fuente del catálogo a escala real'
Need "Link to the authenticated probe"       '\.\./verification/igdb-api-probe\.md'
Need "Eligible-category boundary stated"     '(?i)Frontera de categoría elegible.*game_type\s*=\s*0.*312,418'
Need "game_type 1-14 excluded"               '(?i)game_type.{0,6}1.{0,6}14.*(exclu|no primari)'
Need "Cover delivery/storage rule"           '(?i)Regla de entrega / almacenamiento de portadas.*hotlink'
Need "Cover URL construction recorded"       'images\.igdb\.com/igdb/image/upload/t_\{size\}/\{hash\}\.jpg'
Need "Placeholder fallback for covers"       '(?i)placeholder de primera parte'
Need "Phase 1 offline corpus preserved"      '(?i)Preservar el corpus offline de la Fase 1.*conservan sin cambios'
Need "Request-time no-provider rule kept"    '(?i)CAT-06.*OPS-03.*no se llama a ningún proveedor en tiempo de petición'
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
