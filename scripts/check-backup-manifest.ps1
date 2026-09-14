[CmdletBinding()]
param(
    [string]$ManifestPath,
    [string]$BackupRoot,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
if ($Help) {
    Write-Output "Usage: check-backup-manifest.ps1 -ManifestPath <manifest.json> [-BackupRoot <private directory>]"
    Write-Output "Validates required metadata, containment, and the dump SHA-256 without reading dump contents."
    exit 0
}
if (-not $ManifestPath) { throw "ManifestPath is required unless -Help is used." }
$manifestFull = [IO.Path]::GetFullPath($ManifestPath)
if (-not (Test-Path -LiteralPath $manifestFull -PathType Leaf)) { throw "Manifest not found." }
if (-not $BackupRoot) { $BackupRoot = Split-Path -Parent $manifestFull }
$root = [IO.Path]::GetFullPath($BackupRoot)
$rootPrefix = $root.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
$raw = Get-Content -LiteralPath $manifestFull -Raw
$manifest = $raw | ConvertFrom-Json
foreach ($field in @("schema_version", "created_at_utc", "backup_kind", "dump_file", "dump_sha256", "git_commit", "corpus_version", "protocol_version", "migration_fingerprint", "essential_counts", "artifact_hashes", "secrets_policy")) {
    if ($null -eq $manifest.$field) { throw "Manifest missing required field: $field" }
}
if ([int]$manifest.schema_version -ne 1) { throw "Unsupported manifest schema." }
if ([string]$manifest.backup_kind -notin @("daily", "manual", "weekly")) { throw "Unsupported backup kind." }
if ([string]$manifest.dump_file -match "[\\/]|\.\.") { throw "Dump path must be a filename inside BackupRoot." }
$dumpFull = [IO.Path]::GetFullPath((Join-Path $root ([string]$manifest.dump_file)))
if (-not $dumpFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Dump path escaped BackupRoot." }
if (-not (Test-Path -LiteralPath $dumpFull -PathType Leaf)) { throw "Dump referenced by manifest is missing." }
if ([string]$manifest.dump_sha256 -notmatch "^[a-f0-9]{64}$") { throw "Invalid dump SHA-256." }
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $dumpFull).Hash.ToLowerInvariant()
if ($actual -ne [string]$manifest.dump_sha256) { throw "Dump SHA-256 does not match manifest." }
if ($raw -match "(?im)(password|passwd|token|cookie|connection[_ ]string)\s*[:=]\s*[^\r\n,}\]]+") { throw "Manifest contains a forbidden secret-shaped field." }
foreach ($artifact in @($manifest.artifact_hashes)) {
    if ($artifact.path -match "(^|[\\/])\.\.([\\/]|$)" -or [IO.Path]::IsPathRooted([string]$artifact.path)) { throw "Artifact path is not relative and contained." }
    if ([string]$artifact.sha256 -notmatch "^[a-f0-9]{64}$") { throw "Invalid artifact SHA-256." }
}
Write-Output "PASS: backup manifest and dump checksum are valid"
