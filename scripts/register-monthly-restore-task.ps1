[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$BackupRoot,
    [string]$TaskName = "SavePoint-Monthly-Disposable-Restore",
    [switch]$Help
)

$ErrorActionPreference = "Stop"
if ($Help) { Write-Output "Usage: register-monthly-restore-task.ps1 -BackupRoot <private directory>"; exit 0 }
if (-not $BackupRoot) { throw "BackupRoot is required." }
if (-not [IO.Path]::IsPathRooted($BackupRoot)) { throw "BackupRoot must be an absolute path." }
$script = Join-Path $PSScriptRoot "restore-disposable-db.ps1"
$taskCommand = "powershell.exe -ExecutionPolicy Bypass -File `"$script`" -BackupRoot `"$BackupRoot`""
& schtasks.exe /Create /TN $TaskName /SC MONTHLY /D 1 /ST 04:00 /TR $taskCommand /F
if ($LASTEXITCODE -ne 0) { throw "Could not register the monthly restore task." }
Write-Output "Registered monthly disposable restore task: $TaskName"
