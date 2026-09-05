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

# 1. ISO-8601 UTC probe timestamp.
Require-Match -Label "ISO-8601 UTC probe timestamp" `
    -Pattern 'Probe run \(ISO-8601 UTC\):\*\*\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'

# 2. Authenticated response status (a real HTTP status, not a blank cell).
Require-Match -Label "Authenticated OAuth response status" `
    -Pattern 'Authenticated response status\s*\|\s*\*\*HTTP\s*200\*\*'

# 3. Numeric total games count.
Require-Match -Label "Numeric total games count" `
    -Pattern 'Total games:\s*([1-9]\d{4,})'

# 4. Numeric eligible-category (primary) count.
Require-Match -Label "Numeric eligible primary game_type=0 count" `
    -Pattern 'Eligible primary games \(game_type = 0\):\s*([1-9]\d{4,})'

# 5. game_type breakdown sum reconciliation is stated.
Require-Match -Label "game_type breakdown reconciled to total" `
    -Pattern '(?i)sum\D+374555.*matches unfiltered'

# 6. Quota conclusion -- must say there is no monthly quota, with words after it.
Require-Match -Label "Quota conclusion (no monthly quota)" `
    -Pattern '(?i)Quota conclusion:\s*there is\s*NO\s*monthly request quota'

# 7. Rate-limit numbers recorded (4 req/s, 8 concurrent).
Require-Match -Label "Rate-limit values (4 req/s, 8 concurrent)" `
    -Pattern '(?i)4 requests per second.*8 open requests'

# 8. Written conclusions -- each label must carry real text.
Require-Conclusion -Label "Caching conclusion" -LabelPattern '\*\*Caching conclusion:\*\*\s*'
Require-Conclusion -Label "Attribution / redistribution conclusion" -LabelPattern '\*\*Attribution / redistribution conclusion:\*\*\s*'
Require-Conclusion -Label "Hotlink-versus-mirror cover conclusion" -LabelPattern '\*\*Hotlink-versus-mirror cover conclusion:\*\*\s*'

# 9. Both primary sources for the terms are cited by URL.
Require-Match -Label "Primary source cited: api-docs.igdb.com" -Pattern 'api-docs\.igdb\.com'
Require-Match -Label "Primary source cited: Twitch Developer Services Agreement" -Pattern 'legal\.twitch\.com/legal/developer-agreement'

# 10. Cover URL construction rule is recorded concretely.
Require-Match -Label "Cover image URL structure recorded" `
    -Pattern 'images\.igdb\.com/igdb/image/upload/t_\{size\}/\{hash\}\.jpg'

# 11. Secret-hygiene assertion is present (no credential/token written).
Require-Match -Label "Credential-handling statement" `
    -Pattern '(?i)No credential value, OAuth token, or .+ was printed'

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "FAIL: $($failures.Count) required probe value(s) missing or empty:" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Red }
    exit 1
}
Write-Host "PASS: probe evidence is complete and value-bearing." -ForegroundColor Green
exit 0
