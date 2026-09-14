[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
if ($Help) {
    Write-Output "Usage: rotate-backups.ps1 -BackupRoot <private directory>"
    Write-Output "Keeps the newest 7 daily and 4 weekly dump families."
    exit 0
}
if (-not $BackupRoot) { throw "BackupRoot is required." }
if (-not [IO.Path]::IsPathRooted($BackupRoot)) { throw "BackupRoot must be an absolute path." }
$root = [IO.Path]::GetFullPath($BackupRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "BackupRoot does not exist." }
$rootPrefix = $root.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

function Remove-Family([IO.FileInfo]$Dump) {
    $full = [IO.Path]::GetFullPath($Dump.FullName)
    if (-not $full.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw "Backup path escaped BackupRoot." }
    $stem = [IO.Path]::GetFileNameWithoutExtension($Dump.Name)
    foreach ($candidate in @($Dump.FullName, (Join-Path $root "$stem.manifest.json"), (Join-Path $root "$stem.dump.sha256"))) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { Remove-Item -LiteralPath $candidate -Force }
    }
}

foreach ($rule in @(@("daily", 7), @("weekly", 4))) {
    $kind = $rule[0]
    $keep = [int]$rule[1]
    $dumps = @(Get-ChildItem -LiteralPath $root -File -Filter "$kind-*.dump" | Sort-Object LastWriteTimeUtc -Descending)
    foreach ($old in @($dumps | Select-Object -Skip $keep)) { Remove-Family $old }
    Write-Output "$kind backups retained: $([Math]::Min($keep, $dumps.Count))"
}
