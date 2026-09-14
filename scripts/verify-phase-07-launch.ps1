[CmdletBinding()]
param(
    [string]$ComposeFile = "infra/compose.yaml",
    [string]$BaseUrl = "http://127.0.0.1:3000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composePath = (Resolve-Path (Join-Path $repoRoot $ComposeFile)).Path
$gateStarted = (Get-Date).ToUniversalTime()
$results = New-Object System.Collections.Generic.List[object]
$backupRoot = Join-Path ([IO.Path]::GetTempPath()) ("savepoint-phase-07-launch-" + [Guid]::NewGuid().ToString("N"))
$stackStarted = $false

function Get-CanonicalSha256([string]$RelativePath) {
    $full = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Required file is missing: $RelativePath" }
    $raw = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $full))
    $filtered = New-Object System.Collections.Generic.List[byte]
    foreach ($byte in $raw) { if ($byte -ne 13) { $filtered.Add($byte) } }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($filtered.ToArray())) -replace "-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Get-RawSha256([string]$RelativePath) {
    $full = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Required file is missing: $RelativePath" }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash.ToLowerInvariant()
}

function Invoke-Gate([string]$Name, [string]$FilePath, [string[]]$Arguments) {
    $displayArguments = @($Arguments | ForEach-Object {
            if ($_ -match "(?i)^(?<key>[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|KEY)[A-Z0-9_]*)=(?<value>.*)$") {
                "$($Matches.key)=[redacted]"
            } else {
                $_
            }
        })
    $command = (($FilePath -replace "\\", "/") + " " + ($displayArguments -join " ")).Trim()
    $exitCode = 1
    try {
        Push-Location $repoRoot
        try {
            # Native tools such as Git can emit non-fatal conversion warnings
            # on stderr. Capture them without turning a zero exit code into a
            # PowerShell exception; genuine failures still remain fail-closed
            # through LASTEXITCODE.
            $previousPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            try { & $FilePath @Arguments *> $null; $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE } }
            finally { $ErrorActionPreference = $previousPreference }
        }
        finally { Pop-Location }
    } catch { $exitCode = 1 }
    $passed = ($exitCode -eq 0)
    $results.Add([pscustomobject]@{ name = $Name; status = if ($passed) { "PASS" } else { "FAIL" }; command = $command; detail = if ($passed) { "exit 0" } else { "exit $exitCode" } })
    if (-not $passed) { throw "Launch gate failed: $Name ($exitCode)." }
}

function Invoke-Compose([string]$Name, [string[]]$Arguments) {
    Invoke-Gate $Name "docker" (@("compose", "-f", $composePath) + $Arguments)
}

function Invoke-HttpGate([string]$Name, [string]$Url, [switch]$Headers) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 15
        if ($response.StatusCode -ne 200) { throw "HTTP status is not 200" }
        $body = [string]$response.Content
        if ($body -match "(?i)password|secret|token|set-cookie|traceback") { throw "response contains a sensitive marker" }
        if ($Headers) {
            $required = @{
                "X-Content-Type-Options" = "nosniff"
                "Referrer-Policy" = "same-origin"
                "X-Frame-Options" = "DENY"
                "Permissions-Policy" = "camera=(), microphone=(), geolocation=()"
            }
            foreach ($header in $required.Keys) {
                if ($header -eq "Permissions-Policy") {
                    if ([string]$response.Headers[$header] -notmatch "camera=\(\), microphone=\(\), geolocation=\(\)") { throw "secure header missing required directives: $header" }
                } elseif ([string]$response.Headers[$header] -ne $required[$header]) {
                    throw "secure header missing or unexpected: $header"
                }
            }
            if ([string]$response.Headers["Content-Security-Policy"] -notmatch "default-src 'self'") { throw "CSP missing default-src self" }
        }
        $results.Add([pscustomobject]@{ name = $Name; status = "PASS"; command = "GET $Url"; detail = "HTTP 200; sensitive markers absent" })
        return $response
    } catch {
        $results.Add([pscustomobject]@{ name = $Name; status = "FAIL"; command = "GET $Url"; detail = "HTTP gate failed" })
        throw "Launch gate failed: $Name."
    }
}

function Add-IntegritySnapshot([hashtable]$Snapshot, [string]$Path) {
    $Snapshot[$Path] = Get-RawSha256 $Path
}

function Assert-IntegritySnapshot([hashtable]$Snapshot) {
    foreach ($path in $Snapshot.Keys) {
        $actual = Get-RawSha256 $path
        if ($actual -ne $Snapshot[$path]) { throw "Frozen source changed during launch gate: $path" }
    }
    if (Test-Path -LiteralPath (Join-Path $repoRoot "apps/api/.evaluation-test-run.json") -PathType Leaf) {
        $markerHash = Get-RawSha256 "apps/api/.evaluation-test-run.json"
        if ($markerHash -ne $Snapshot["apps/api/.evaluation-test-run.json"]) { throw "Evaluation marker changed during launch gate." }
    }
}

function Provision-LocalRoles {
    $env:DEMO_USERNAME = "demo-visitor"
    $env:DEMO_PASSWORD = "SavePoint-Demo-2026-Visit!"
    $env:RESEARCH_VIEWER_USERNAME = "phase7-research-viewer"
    $env:RESEARCH_VIEWER_PASSWORD = "Research-" + [Guid]::NewGuid().ToString("N") + "!"
    $env:PLATFORM_ADMIN_USERNAME = "phase7-platform-admin"
    $env:PLATFORM_ADMIN_PASSWORD = "Admin-" + [Guid]::NewGuid().ToString("N") + "!"
    $env:EXPECTED_COMMIT = ""
    $python = "import os;from django.contrib.auth import get_user_model;from accounts.models import AccountProfile;from django.core.management import call_command;U=get_user_model();specs=[('RESEARCH_VIEWER_USERNAME','RESEARCH_VIEWER_PASSWORD','Research Viewer'),('PLATFORM_ADMIN_USERNAME','PLATFORM_ADMIN_PASSWORD','Platform Admin')];users=[(U.objects.get_or_create(username=os.environ[un])[0],pw,g) for un,pw,g in specs];[(u.set_password(os.environ[pw]),setattr(u,'is_active',True),u.save(update_fields=['password','is_active'])) for u,pw,g in users];[call_command('bootstrap_phase7_roles',user_id=str(AccountProfile.objects.get_or_create(user=u)[0].admin_uuid),group=g) for u,pw,g in users]"
    Invoke-Gate "Provision local demo roles" "docker" (@("compose", "-f", $composePath, "exec", "-T", "-e", "RESEARCH_VIEWER_USERNAME=$env:RESEARCH_VIEWER_USERNAME", "-e", "RESEARCH_VIEWER_PASSWORD=$env:RESEARCH_VIEWER_PASSWORD", "-e", "PLATFORM_ADMIN_USERNAME=$env:PLATFORM_ADMIN_USERNAME", "-e", "PLATFORM_ADMIN_PASSWORD=$env:PLATFORM_ADMIN_PASSWORD", "api", "python", "manage.py", "shell", "-c", $python))
}

function Write-LaunchDocuments([string]$Status, [string]$Failure) {
    $date = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $table = ($results | ForEach-Object {
            $safeCommand = $_.command -replace "(?i)([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|KEY)[A-Z0-9_]*)=\S+", '$1=[redacted]'
            "| $($_.name) | $($_.status) | ``$safeCommand`` | $($_.detail) |"
        }) -join "`n"
    $failureText = if ($Failure) { $Failure } else { "Ninguno." }
    $gate = @"
---
fase: 07-research-panel-hardening-and-evidence-freeze
plan: 05
estado: $Status
fecha_utc: $date
---

# Gate de lanzamiento de la Fase 07

La gate final se ejecutó como un único orquestador fail-closed. No invoca el runner de evaluación, no recalcula métricas y protege por hash el artefacto v15, el snapshot de cohortes, el puntero de protocolo y el marker consumido.

## Resultado

**Estado:** $Status
**Fallo:** $failureText

| Comprobación | Estado | Comando | Evidencia resumida |
|---|---|---|---|
$table

## Alcance protegido

- Artefacto publicado: `evaluation-400-test-2026-09-12-v15`, protocolo 15, corpus `2026.09.2`, 400 usuarios solicitados, 79 evaluables y 16 algoritmos.
- El marker `apps/api/.evaluation-test-run.json` y las fuentes v15 se comparan antes/después; no se ejecuta ningún comando de evaluación.
- Las credenciales locales son variables de proceso efímeras; sus valores no se escriben en esta evidencia, trazas ni logs.
- El restore usa una base de datos desechable fuera de la base canónica y elimina únicamente ese destino.

## Limitaciones y revisión humana

El resultado automático no sustituye la revisión del autor sobre el recorrido visual en español/inglés, el reflow a 320 px y 400 %, ni la adecuación legal de la redistribución. El paquete v15 sigue siendo evidencia de simulación con una sola ejecución publicada, no evidencia de usuarios reales.
"@
    $signoff = @"
---
fase: 07-research-panel-hardening-and-evidence-freeze
plan: 05
estado: $Status
fecha_utc: $date
---

# Signoff técnico de la Fase 07

## Decisión técnica

La decisión automática es **$Status**. Solo una ejecución con todos los gates en `PASS` permite preparar el cierre de la issue #70. La aprobación académica y la revisión visual final siguen correspondiendo a Felipe.

## Evidencia

- Gate canónica: `scripts/verify-phase-07-launch.ps1`.
- Detalle de comandos y resultado: `docs/verification/phase-07-launch-gate.md`.
- Evidencia v15 congelada: `docs/verification/phase-07-evidence-manifest.json` y sus salidas saneadas.
- No se incluyen secretos, datos personales, dumps, trazas ni logs brutos.

## Requisitos cubiertos

`QUAL-01`, `QUAL-04`, `DOC-05`, `DOC-06`, `AGENT-05`, `AGENT-06`, `OPS-04`, `OPS-05` y `SEC-07` quedan trazados por las suites backend/frontend/browser, los checkers deterministas, el backup/restore y los documentos de evidencia.

## Pendientes honestos

$failureText

La simulación v15 conserva sus limitaciones declaradas: población sintética, un único run de test, 79 usuarios evaluables y ausencia de captura retrospectiva de CPU/SO. No se relanza la evaluación para cerrar esta gate.
"@
    $gate | Set-Content -LiteralPath (Join-Path $repoRoot "docs/verification/phase-07-launch-gate.md") -Encoding utf8
    $signoff | Set-Content -LiteralPath (Join-Path $repoRoot "docs/verification/phase-07-signoff.md") -Encoding utf8
}

$snapshots = @{}
foreach ($path in @("apps/api/evaluation-400-test-2026-09-12-v15.artifact.json", "docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.json", "docs/methodology/protocol.json", "apps/api/.evaluation-test-run.json")) { Add-IntegritySnapshot $snapshots $path }

try {
    Invoke-Gate "Git diff check" "git" @("diff", "--check")
    Invoke-Compose "Compose configuration" @("config")
    # The launch gate exercises the web/API/database path only. Starting every
    # recommendation worker here exhausts the small local PostgreSQL connection
    # budget before the disposable checks can run.
    Invoke-Compose "Local stack setup" @("up", "--build", "--wait", "db", "api", "web")
    $stackStarted = $true
    Provision-LocalRoles
    Invoke-Compose "Migration drift check" @("run", "--rm", "api", "python", "manage.py", "migrate", "--check")
    Invoke-Compose "Django deploy checks" @("run", "--rm", "-e", "DJANGO_DEPLOY_ENV=production", "api", "python", "manage.py", "check", "--deploy")
    Invoke-Compose "Backend phase 7 contract API admin portability operations" @("run", "--rm", "api", "pytest", "apps/api/evaluation/tests/test_phase7_contract.py", "apps/api/evaluation/tests/test_phase7_api.py", "apps/api/tests/test_phase7_admin_security.py", "apps/api/library/tests/test_portability.py", "apps/api/tests/test_phase7_operations.py", "-q")
    Invoke-Gate "Vitest" "corepack" @("pnpm", "--dir", "apps/web", "exec", "vitest", "run")
    Invoke-Gate "TypeScript" "corepack" @("pnpm", "--dir", "apps/web", "exec", "tsc", "--noEmit")
    Invoke-Gate "Playwright and axe Chromium" "corepack" @("pnpm", "exec", "playwright", "test", "e2e/research-panel.spec.ts", "e2e/admin-security.spec.ts", "e2e/a11y.spec.ts", "e2e/deployed-smoke.spec.ts", "--project=chromium")
    # Browser journeys open many short-lived Django connections against the
    # deliberately small local PostgreSQL budget. Recreate only API so those
    # idle sessions are released before backup/restore checks.
    Invoke-Compose "Post-browser idle connection cleanup" @("exec", "-T", "db", "psql", "-U", "savepoint_test", "-d", "postgres", "-v", "ON_ERROR_STOP=1", "-c", "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND state = 'idle';")
    Invoke-Compose "API connection reset before recovery gates" @("restart", "api")
    Invoke-Compose "API ready after connection reset" @("up", "-d", "--wait", "api")
    Invoke-Gate "Secrets scan" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-secrets.ps1")
    Invoke-Gate "Dependency scan" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-dependencies.ps1")
    Invoke-Gate "Security scan" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-security.ps1", "-IncludeDeployment")
    Invoke-Gate "Evidence scan" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-evidence.ps1")
    Invoke-Gate "Backup manifest help contract" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-backup-manifest.ps1", "-Help")
    Invoke-Gate "Weekly backup" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/backup-postgres.ps1", "-BackupRoot", $backupRoot, "-BackupKind", "weekly", "-ArtifactPath", "docs/verification/phase-07-evidence-manifest.json")
    $manifest = @(Get-ChildItem -LiteralPath $backupRoot -Filter "weekly-*.manifest.json" -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).FullName
    if (-not $manifest) { throw "Weekly backup did not produce a manifest." }
    Invoke-Gate "Backup manifest validation" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/check-backup-manifest.ps1", "-ManifestPath", $manifest, "-BackupRoot", $backupRoot)
    Invoke-Gate "Disposable monthly restore" "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts/restore-disposable-db.ps1", "-BackupRoot", $backupRoot, "-ManifestPath", $manifest, "-ComposeFile", $composePath, "-ApiUrl", "http://127.0.0.1:8000/health/")
    $health = Invoke-HttpGate "Same-origin health" "$BaseUrl/health/"
    $healthJson = $health.Content | ConvertFrom-Json
    if ($env:EXPECTED_COMMIT -and $healthJson.commit -ne $env:EXPECTED_COMMIT) { throw "Health commit does not match EXPECTED_COMMIT." }
    Invoke-HttpGate "Secure headers" "$BaseUrl/es" -Headers | Out-Null
    Assert-IntegritySnapshot $snapshots
    Write-LaunchDocuments "PASS" ""
    Write-Output "PASS: Phase 7 launch gate complete; all checks passed."
} catch {
    $failure = $_.Exception.Message
    try { Write-LaunchDocuments "FAIL" $failure } catch { }
    Write-Error $failure
    exit 1
} finally {
    Remove-Item -LiteralPath $backupRoot -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($name in @("RESEARCH_VIEWER_USERNAME", "RESEARCH_VIEWER_PASSWORD", "PLATFORM_ADMIN_USERNAME", "PLATFORM_ADMIN_PASSWORD", "DEMO_USERNAME", "DEMO_PASSWORD", "EXPECTED_COMMIT")) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
}
