[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [string]$ManifestPath,
    [string]$ComposeFile,
    [string]$ApiUrl = "http://localhost:8000/health/",
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ($Help) {
    Write-Output "Usage: restore-disposable-db.ps1 -BackupRoot <private directory> [-ManifestPath <manifest.json>] [-ApiUrl <health URL>]"
    Write-Output "Creates a unique disposable database, restores into it, runs migrations and health smoke, then drops only that database."
    exit 0
}
if (-not $BackupRoot) { throw "BackupRoot is required." }
if (-not [IO.Path]::IsPathRooted($BackupRoot)) { throw "BackupRoot must be an absolute path." }
$root = [IO.Path]::GetFullPath($BackupRoot)
if (-not $ComposeFile) { $ComposeFile = Join-Path $repoRoot "infra/compose.yaml" }
if (-not $ManifestPath) { $ManifestPath = @(Get-ChildItem -LiteralPath $root -File -Filter "weekly-*.manifest.json" | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).FullName }
if (-not $ManifestPath) { throw "A weekly manifest is required for restore." }
$checker = Join-Path $PSScriptRoot "check-backup-manifest.ps1"
& powershell -ExecutionPolicy Bypass -File $checker -ManifestPath $ManifestPath -BackupRoot $root
if ($LASTEXITCODE -ne 0) { throw "Manifest validation failed." }
$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$dumpPath = Join-Path $root ([string]$manifest.dump_file)
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$dbName = "savepoint_restore_$stamp_$PID"
if ($dbName -notmatch "^savepoint_restore_[a-z0-9_]+$") { throw "Disposable database name failed validation." }
$containerDump = "/tmp/$dbName.dump"
$created = $false

function Invoke-Checked([string[]]$Arguments) {
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Disposable restore command failed." }
}

try {
    Invoke-Checked @("compose", "-f", $ComposeFile, "exec", "-T", "db", "createdb", "-U", "savepoint_test", $dbName)
    $created = $true
    Invoke-Checked @("compose", "-f", $ComposeFile, "cp", $dumpPath, "db:$containerDump")
    Invoke-Checked @("compose", "-f", $ComposeFile, "exec", "-T", "db", "pg_restore", "--no-owner", "--no-privileges", "-U", "savepoint_test", "-d", $dbName, $containerDump)
    Invoke-Checked @("compose", "-f", $ComposeFile, "run", "--rm", "-e", "DATABASE_URL=", "-e", "POSTGRES_DB=$dbName", "api", "python", "manage.py", "migrate", "--noinput")
    Invoke-Checked @("compose", "-f", $ComposeFile, "run", "--rm", "-e", "DATABASE_URL=", "-e", "POSTGRES_DB=$dbName", "api", "python", "manage.py", "check")
    $health = Invoke-WebRequest -UseBasicParsing -Uri $ApiUrl -TimeoutSec 10
    if ($health.StatusCode -lt 200 -or $health.StatusCode -ge 500) { throw "API health smoke failed." }
    Write-Output "PASS: disposable restore, migrations, constraints and API health smoke completed"
} finally {
    if ($created) {
        & docker compose -f $ComposeFile exec -T db rm -f $containerDump 2>$null | Out-Null
        & docker compose -f $ComposeFile exec -T db dropdb -U savepoint_test --if-exists $dbName 2>$null | Out-Null
    }
}
