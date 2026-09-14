[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [string]$TaskName = "SavePoint-Daily-Backup",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
if ($Help) { Write-Output "Usage: register-daily-backup-task.ps1 -BackupRoot <private directory>"; exit 0 }
if (-not $BackupRoot) { throw "BackupRoot is required." }
if (-not [IO.Path]::IsPathRooted($BackupRoot)) { throw "BackupRoot must be an absolute path." }
$script = Join-Path $PSScriptRoot "backup-postgres.ps1"
$taskCommand = "powershell.exe -ExecutionPolicy Bypass -File `"$script`" -BackupRoot `"$BackupRoot`" -BackupKind daily"
& schtasks.exe /Create /TN $TaskName /SC DAILY /ST 02:30 /TR $taskCommand /F
if ($LASTEXITCODE -ne 0) { throw "Could not register the daily backup task." }
Write-Output "Registered daily backup task: $TaskName"
