<#[CmdletBinding()]
    Fail-closed repository security gate for Phase 7.
#>
[CmdletBinding()]
param(
    [switch]$IncludeDeployment
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$failure = $false

# Windows PowerShell on Windows, PowerShell 7 (pwsh) on the Linux CI runner.
$shell = if (Get-Command powershell -ErrorAction SilentlyContinue) { "powershell" } else { "pwsh" }

function Invoke-Gate {
    param([string]$Path, [string[]]$Arguments)
    & $shell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root $Path) @Arguments
    if ($LASTEXITCODE -ne 0) {
        $script:failure = $true
        Write-Error "Security gate failed: $Path"
    }
}

Write-Host "== Security dependency and secret gates ==" -ForegroundColor Cyan
Invoke-Gate "scripts/check-dependencies.ps1" @()
$secretArgs = @()
if ($IncludeDeployment) { $secretArgs += "-IncludeDeployment" }
Invoke-Gate "scripts/check-secrets.ps1" $secretArgs

$settings = Get-Content -Raw (Join-Path $root "apps/api/config/settings.py")
foreach ($required in @(
    "SECURE_CONTENT_TYPE_NOSNIFF = True",
    'SECURE_REFERRER_POLICY = "same-origin"',
    'X_FRAME_OPTIONS = "DENY"',
    '"research": "60/min"',
    '"django.contrib.admin"'
)) {
    if ($settings -notmatch [regex]::Escape($required)) {
        Write-Error "Required security setting is missing: $required"
        $failure = $true
    }
}

$sourceFiles = Get-ChildItem -Path (Join-Path $root "apps/api") -Recurse -File -Include *.py
foreach ($file in $sourceFiles) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    foreach ($pattern in @(
        'auth\.change_user',
        'PLATFORM_ADMIN_FALLBACK_PERMISSION',
        'request\.COOKIES.*has_perm',
        'request\.(GET|POST).*has_perm',
        'cursor\.execute\s*\(\s*f'
    )) {
        if ($text -match $pattern) {
            Write-Error "Unsafe authorization or query pattern in $($file.FullName): $pattern"
            $failure = $true
        }
    }
}

$webRoot = Join-Path $root "apps/web"
if (Test-Path $webRoot) {
    $webFiles = Get-ChildItem -Path $webRoot -Recurse -File -Include *.ts,*.tsx
    foreach ($file in $webFiles) {
        # next.config.ts is the same-origin proxy boundary for Django Admin;
        # the administrative UI itself remains exclusively server-side.
        if ($file.Name -eq "next.config.ts") { continue }
        if ((Get-Content -LiteralPath $file.FullName -Raw) -match '(?i)(/admin/|PlatformAdminSite)') {
            Write-Error "Administrative surface must remain in Django Admin: $($file.FullName)"
            $failure = $true
        }
    }
}

if (-not (Test-Path (Join-Path $root ".github/workflows/quality-gates.yml"))) {
    Write-Error "Quality-gates workflow is missing."
    $failure = $true
}

if ($failure) {
    Write-Error "Security gate failed."
    exit 1
}
Write-Host "PASS: deterministic security checks completed." -ForegroundColor Green
exit 0
