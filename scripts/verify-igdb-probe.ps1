<#
.SYNOPSIS
    Deterministic content gate for docs/verification/igdb-api-probe.md
    (Plan 01.1-01 Task 2, requirement DATA-04).

.DESCRIPTION
    Parses the probe evidence and independently requires that every
    load-bearing observation is present AS A RECORDED VALUE, not as a bare
    heading or an empty label. Fails closed: any missing timestamp,
    authenticated status, numeric count, or written conclusion exits non-zero.

    This gate does NOT contact the network. It only checks that the committed
    evidence file is complete and value-bearing, so a reviewer (or a later
    plan) can trust it without re-running the probe.
#>

[CmdletBinding()]
param(
    [string]$EvidencePath
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $EvidencePath) {
    $EvidencePath = Join-Path $RepoRoot "docs/verification/igdb-api-probe.md"
}

if (-not (Test-Path $EvidencePath -PathType Leaf)) {
    Write-Host "FAIL: evidence file not found: $EvidencePath" -ForegroundColor Red
    exit 1
}

$text = Get-Content -LiteralPath $EvidencePath -Raw
$failures = New-Object System.Collections.Generic.List[string]

function Require-Match {
    param(
        [string]$Label,
        [string]$Pattern,
        [string]$Expluanation = ""
    )
    if ($script:text -notmatch $Pattern) {
        $msg = "MISSING: $Label"
        if ($Expluanation) { $msg += " -- $Expluanation" }
        $script:failures.Add($msg)
        Write-Host "  [x] $Label" -ForegroundColor Red
    }
    else {
        Write-Host "  [ok] $Label" -ForegroundColor Green
    }
}

# A labelled conclusion must be followed by real prose on the same line:
# at least 40 non-newline characters after the colon.
function Require-Conclusion {
    param(
        [string]$Label,
        [string]$LabelPattern
    )
    $rx = $LabelPattern + '[^\r\n]{40,}'
    Require-Match -Label $Label -Pattern $rx -Expluanation "label present but no recorded value/conclusion text after it"
}

Write-Host "== verify-igdb-probe: $EvidencePath ==" -ForegroundColor Cyan

# The probe evidence prose is Spanish (project convention: thesis docs in
# Spanish, code in English). These patterns match the Spanish anchors; the
# verbatim IGDB terms quotes in section 5 stay in English, so their patterns
# (rate-limit numbers, URLs) are unchanged. Numbers/queries/field names are
# language-neutral and matched verbatim.

# 1. ISO-8601 UTC probe timestamp.
Require-Match -Label "ISO-8601 UTC probe timestamp" `
    -Pattern 'Sondeo ejecutado \(ISO-8601 UTC\):\*\*\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'

# 2. Authenticated response status (a real HTTP status, not a blank cell).
Require-Match -Label "Authenticated OAuth response status" `
    -Pattern 'Estado de la respuesta autenticada\s*\|\s*\*\*HTTP\s*200\*\*'

# 3. Numeric total games count.
Require-Match -Label "Numeric total games count" `
    -Pattern 'Juegos totales:\s*([1-9]\d{4,})'

# 4. Numeric eligible-category (primary) count.
Require-Match -Label "Numeric eligible primary game_type=0 count" `
    -Pattern 'Juegos primarios elegibles \(game_type = 0\):\s*([1-9]\d{4,})'

# 5. game_type breakdown sum reconciliation is stated.
Require-Match -Label "game_type breakdown reconciled to total" `
    -Pattern '(?i)suma\D+374555.*coincide con'

# 6. Quota conclusion -- must say there is no monthly quota, with words after it.
Require-Match -Label "Quota conclusion (no monthly quota)" `
    -Pattern '(?i)Conclusión de cuota:\s*NO existe ninguna cuota mensual'

# 7. Rate-limit numbers recorded (4 req/s, 8 concurrent) -- from the verbatim
#    English api-docs.igdb.com quote, kept in English.
Require-Match -Label "Rate-limit values (4 req/s, 8 concurrent)" `
    -Pattern '(?i)4 requests per second.*8 open requests'

# 8. Written conclusions -- each label must carry real text.
Require-Conclusion -Label "Caching conclusion" -LabelPattern '\*\*Conclusión sobre caché:\*\*\s*'
Require-Conclusion -Label "Attribution / redistribution conclusion" -LabelPattern '\*\*Conclusión sobre atribución / redistribución:\*\*\s*'
Require-Conclusion -Label "Hotlink-versus-mirror cover conclusion" -LabelPattern '\*\*Conclusión sobre hotlink vs\. mirror de portadas:\*\*\s*'

# 9. Both primary sources for the terms are cited by URL.
Require-Match -Label "Primary source cited: api-docs.igdb.com" -Pattern 'api-docs\.igdb\.com'
Require-Match -Label "Primary source cited: Twitch Developer Services Agreement" -Pattern 'legal\.twitch\.com/legal/developer-agreement'

# 10. Cover URL construction rule is recorded concretely.
Require-Match -Label "Cover image URL structure recorded" `
    -Pattern 'images\.igdb\.com/igdb/image/upload/t_\{size\}/\{hash\}\.jpg'

# 11. Secret-hygiene assertion is present (no credential/token written).
Require-Match -Label "Credential-handling statement" `
    -Pattern '(?i)No se imprimió.{0,90}ningún valor de credencial'

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "FAIL: $($failures.Count) required probe value(s) missing or empty:" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}
Write-Host "PASS: probe evidence is complete and value-bearing." -ForegroundColor Green
exit 0
