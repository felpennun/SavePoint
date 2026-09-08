$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$image = "ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"

docker run --rm --network none `
    --volume "${repoRoot}:/repo:ro" `
    --workdir /repo `
    $image `
    git /repo --no-banner --redact --log-opts=--all

if ($LASTEXITCODE -ne 0) {
    throw "Gitleaks found a secret-shaped value in Git history."
}

Write-Host "Full Git history secret scan passed."
