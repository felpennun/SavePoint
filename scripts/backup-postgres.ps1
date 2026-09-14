<#[CmdletBinding()]
.SYNOPSIS
    Create a private PostgreSQL custom-format backup and a redacted manifest.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [ValidateSet("daily", "manual", "weekly")][string]$BackupKind = "manual",
    [string]$ComposeFile,
    [string[]]$ArtifactPath,
    [switch]$Native,
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ($Help) {
    Write-Output "Usage: backup-postgres.ps1 -BackupRoot <private absolute directory> [-BackupKind daily|manual|weekly] [-Native]"
    Write-Output "The manifest contains hashes and metadata only; credentials, cookies, connection strings, and logs are never copied."
    exit 0
}
if (-not $BackupRoot) { throw "BackupRoot is required." }
if (-not [IO.Path]::IsPathRooted($BackupRoot)) { throw "BackupRoot must be an absolute path." }
$backupRootFull = [IO.Path]::GetFullPath($BackupRoot)
New-Item -ItemType Directory -Force -Path $backupRootFull | Out-Null
if (-not $ComposeFile) { $ComposeFile = Join-Path $repoRoot "infra/compose.yaml" }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$prefix = "$BackupKind-$stamp-$PID"
$dumpPath = Join-Path $backupRootFull "$prefix.dump"
$manifestPath = Join-Path $backupRootFull "$prefix.manifest.json"
$checksumPath = Join-Path $backupRootFull "$prefix.dump.sha256"

function Assert-ContainedPath([string]$Path, [string]$Root) {
    $full = [IO.Path]::GetFullPath($Path)
    $rootWithSlash = $Root.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if ($full -ne $Root -and -not $full.StartsWith($rootWithSlash, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path must remain inside BackupRoot."
    }
    return $full
}

function Invoke-Checked([string]$FilePath, [string[]]$Arguments) {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Backup command failed: $FilePath" }
}

if ($Native) {
    Invoke-Checked "pg_dump" @("--format=custom", "--file=$dumpPath")
} else {
    $containerDump = "/tmp/$prefix.dump"
    Invoke-Checked "docker" @("compose", "-f", $ComposeFile, "exec", "-T", "db", "pg_dump", "--format=custom", "--file=$containerDump", "-U", "savepoint_test", "-d", "savepoint_test")
    try {
        Invoke-Checked "docker" @("compose", "-f", $ComposeFile, "cp", "db:$containerDump", $dumpPath)
    } finally {
        & docker compose -f $ComposeFile exec -T db rm -f $containerDump 2>$null | Out-Null
    }
}

$dumpPath = Assert-ContainedPath $dumpPath $backupRootFull
$dumpHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dumpPath).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksumPath -Value "$dumpHash  $([IO.Path]::GetFileName($dumpPath))" -Encoding ascii

$migrationFiles = @(Get-ChildItem (Join-Path $repoRoot "apps/api") -Recurse -File -Filter "*.py" | Where-Object { $_.FullName -match "migrations" } | Sort-Object FullName)
$migrationHashInput = ($migrationFiles | ForEach-Object { (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash }) -join "`n"
$migrationHash = if ($migrationHashInput) { $sha = [Security.Cryptography.SHA256]::Create(); try { ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($migrationHashInput))) -replace "-", "").ToLowerInvariant() } finally { $sha.Dispose() } } else { "" }
$countQuery = "SELECT 'users=' || count(*) FROM accounts_user UNION ALL SELECT 'works=' || count(*) FROM catalogue_gamework UNION ALL SELECT 'library_entries=' || count(*) FROM library_libraryentry UNION ALL SELECT 'owned_copies=' || count(*) FROM library_ownedcopy;"
if ($Native) { $countOutput = & psql -Atqc $countQuery } else { $countOutput = & docker compose -f $ComposeFile exec -T db psql -Atqc $countQuery -U savepoint_test -d savepoint_test }
if ($LASTEXITCODE -ne 0) { throw "Could not collect essential database counts." }
$essentialCounts = [ordered]@{}
foreach ($line in @($countOutput)) {
    $parts = ([string]$line).Split("=", 2)
    if ($parts.Count -eq 2 -and $parts[1] -match "^\d+$") { $essentialCounts[$parts[0]] = [int64]$parts[1] }
}
if ($essentialCounts.Count -ne 4) { throw "Essential database counts were incomplete." }
$artifactHashes = @()
foreach ($artifact in @($ArtifactPath)) {
    $artifactFull = [IO.Path]::GetFullPath($artifact)
    if (-not (Test-Path -LiteralPath $artifactFull -PathType Leaf)) { throw "Artifact not found: $artifact" }
    if ($artifactFull -match "(?i)(dump|log|secret|token|cookie|password)") { throw "Artifact path is not publishable." }
    $artifactHashes += [ordered]@{ path = $artifactFull.Substring($repoRoot.Length).TrimStart("\", "/") -replace "\\", "/"; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifactFull).Hash.ToLowerInvariant() }
}

$manifest = [ordered]@{
    schema_version = 1
    created_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    backup_kind = $BackupKind
    dump_file = [IO.Path]::GetFileName($dumpPath)
    dump_sha256 = $dumpHash
    checksum_file = [IO.Path]::GetFileName($checksumPath)
    git_commit = (& git -C $repoRoot rev-parse HEAD).Trim()
    corpus_version = if ($env:SAVEPOINT_CORPUS_VERSION) { $env:SAVEPOINT_CORPUS_VERSION } else { "not-declared" }
    protocol_version = if ($env:SAVEPOINT_PROTOCOL_VERSION) { $env:SAVEPOINT_PROTOCOL_VERSION } else { "not-declared" }
    migration_fingerprint = $migrationHash
    essential_counts = $essentialCounts
    artifact_hashes = @($artifactHashes)
    secrets_policy = "sin secretos: credentials, cookies, connection strings and raw logs are excluded"
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Backup created: $([IO.Path]::GetFileName($dumpPath))"
Write-Output "Manifest created: $([IO.Path]::GetFileName($manifestPath))"
