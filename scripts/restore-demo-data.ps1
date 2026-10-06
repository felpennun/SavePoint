<#
.SYNOPSIS
    Restore the SavePoint demo data package (full catalogue + demo accounts) into the local
    Docker Compose database, then start the application.
.DESCRIPTION
    The package is a PostgreSQL custom-format dump published as an asset of the GitHub release.
    This replaces the contents of the local database.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/restore-demo-data.ps1 -Dump savepoint-demo-data-v1.0.0.dump
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Dump
)

$ErrorActionPreference = "Stop"
# Set COMPOSE_ARGS (space-separated) to use another compose file; COMPOSE_PROJECT_NAME selects another project.
$ComposeArgs = if ($env:COMPOSE_ARGS) { $env:COMPOSE_ARGS -split " " } else { @("-f", "infra/compose.yaml") }
$DbUser = "savepoint_test"
$DbName = "savepoint_test"
$InContainer = "/tmp/savepoint-demo-data.dump"

function Invoke-Compose {
    & docker compose @ComposeArgs @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose $($args -join ' ') failed (exit $LASTEXITCODE)" }
}

if (-not (Test-Path -LiteralPath $Dump -PathType Leaf)) { throw "File not found: $Dump" }
$Dump = (Resolve-Path -LiteralPath $Dump).Path

$checksumFile = "$Dump.sha256"
if (Test-Path -LiteralPath $checksumFile) {
    Write-Host "Checking the SHA-256 of the package..."
    $expected = ((Get-Content -LiteralPath $checksumFile -TotalCount 1) -split "\s+")[0].ToLowerInvariant()
    $actual = (Get-FileHash -LiteralPath $Dump -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($expected -ne $actual) { throw "SHA-256 mismatch: expected $expected, got $actual" }
}

Write-Host "Stopping the application (the database volume is kept)..."
Invoke-Compose down
Invoke-Compose up -d --wait db

Write-Host "Recreating the database..."
Invoke-Compose exec -T db dropdb -U $DbUser --if-exists $DbName
Invoke-Compose exec -T db createdb -U $DbUser $DbName

Write-Host "Restoring the package (this takes a few minutes)..."
Invoke-Compose cp $Dump "db:$InContainer"
Invoke-Compose exec -T db pg_restore -U $DbUser -d $DbName --no-owner --exit-on-error $InContainer
Invoke-Compose exec -T db rm -f $InContainer

Write-Host "Starting the application..."
Invoke-Compose up --build --wait
Write-Host "Done. Open http://localhost:3000/es"
