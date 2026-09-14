[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [Parameter(Mandatory = $false)][ValidateSet("migration", "import", "deploy", "config")][string]$ChangeType,
    [string]$ComposeFile,
    [switch]$Native,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
if ($Help) {
    Write-Output "Usage: backup-before-change.ps1 -BackupRoot <directory> -ChangeType migration|import|deploy|config"
    exit 0
}
if (-not $BackupRoot -or -not $ChangeType) { throw "BackupRoot and ChangeType are required." }
$scriptPath = Join-Path $PSScriptRoot "backup-postgres.ps1"
$args = @("-BackupRoot", $BackupRoot, "-BackupKind", "manual")
if ($ComposeFile) { $args += @("-ComposeFile", $ComposeFile) }
if ($Native) { $args += "-Native" }
& powershell -ExecutionPolicy Bypass -File $scriptPath @args
if ($LASTEXITCODE -ne 0) { throw "Manual backup before $ChangeType failed." }
Write-Output "Manual backup completed before change type: $ChangeType"
