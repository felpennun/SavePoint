#requires -Version 5.1
<#
.SYNOPSIS
  Plan 01.1-02 Task 3 -- prove the full-scale IGDB import on a genuinely empty,
  disposable PostgreSQL instance, with interrupt + resume + rerun convergence.

.DESCRIPTION
  Builds a throwaway API image from this worktree, starts a uniquely-named
  PostgreSQL container with an ANONYMOUS volume (no named volume, nothing that
  outlives the run), health-waits it, migrates an empty database, then:

    1. re-measures the live IGDB eligible count,
    2. starts the production `import_igdb_catalogue` command,
    3. hard-kills it (SIGKILL) after >= 1 committed batch,
    4. resumes it to completion,
    5. reruns it to prove counts + checksum converge,
    6. asserts the real-scale lower bound, provenance, cover accounting,
       checkpoint completion and source-id uniqueness,
    7. writes redacted aggregate evidence into
       docs/verification/igdb-catalogue-freeze.md (+ .sample.json).

  Secrets: IGDB_CLIENT_ID / IGDB_CLIENT_SECRET and the throwaway DATABASE_URL
  are passed to containers by NAME only (never on a command line), and every
  captured log line is redacted before it is written anywhere.

  The unique PostgreSQL container is always removed in `finally`. This is a
  full-scale acceptance run against the live IGDB API and takes tens of
  minutes; it takes no parameters.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# --- paths -------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir
$FreezeDoc = Join-Path $RepoRoot 'docs/verification/igdb-catalogue-freeze.md'
$SampleDoc = Join-Path $RepoRoot 'docs/verification/igdb-catalogue-freeze.sample.json'

# --- unique, collision-proof names -----------------------------------------
$Stamp     = Get-Date -Format 'yyyyMMddHHmmss'
$Uniq      = "$Stamp-$PID"
$PgName    = "savepoint-igdb-fresh-$Uniq"
$ImporterName = "savepoint-igdb-importer-$Uniq"
$NetName   = "savepoint-igdb-net-$Uniq"
$ImageTag  = "savepoint-igdb-fresh-img:$Uniq"
$OutDir    = Join-Path ([System.IO.Path]::GetTempPath()) "igdb-fresh-$Uniq"

# --- helpers ---------------------------------------------------------------
function Redact([string]$Text) {
  if ($null -eq $Text) { return '' }
  $t = $Text
  $t = [regex]::Replace($t, '(?i)(client_secret=)[^\s&"'']+', '${1}***')
  $t = [regex]::Replace($t, '(?i)(client_id=)[^\s&"'']+', '${1}***')
  $t = [regex]::Replace($t, '(?i)(Bearer\s+)[A-Za-z0-9._\-]+', '${1}***')
  $t = [regex]::Replace($t, '(?i)postgres(ql)?://[^\s"'']+', 'postgresql://***')
  $t = [regex]::Replace($t, '(?i)(access_token"?\s*[:=]\s*"?)[A-Za-z0-9._\-]+', '${1}***')
  return $t
}

function Fail([string]$Message) {
  Write-Host "FAIL: $Message" -ForegroundColor Red
  throw $Message
}

function Get-HeadCommit([string]$Root) {
  # Resolve HEAD without shelling out, so this script never invokes the VCS
  # binary (it runs inside an isolated worktree). Honours the
  # GSD_VERIFY_COMMIT override if the caller already knows the hash.
  if ($env:GSD_VERIFY_COMMIT) { return $env:GSD_VERIFY_COMMIT.Trim() }
  try {
    $dot = Join-Path $Root '.git'
    $gitDir = $dot
    if (Test-Path $dot -PathType Leaf) {
      $gitDir = ((Get-Content $dot -Raw) -replace '(?s)^gitdir:\s*', '').Trim()
    }
    $head = (Get-Content (Join-Path $gitDir 'HEAD') -Raw).Trim()
    if ($head -notmatch '^ref:\s*(.+)$') { return $head }  # detached: already a sha
    $ref = $Matches[1].Trim()
    $commonDir = $gitDir
    $commonFile = Join-Path $gitDir 'commondir'
    if (Test-Path $commonFile) {
      $commonDir = (Resolve-Path (Join-Path $gitDir ((Get-Content $commonFile -Raw).Trim()))).Path
    }
    $refFile = Join-Path $commonDir $ref
    if (Test-Path $refFile) { return (Get-Content $refFile -Raw).Trim() }
    $packed = Join-Path $commonDir 'packed-refs'
    if (Test-Path $packed) {
      foreach ($ln in Get-Content $packed) {
        if ($ln -match "^([0-9a-f]{40})\s+$([regex]::Escape($ref))$") { return $Matches[1] }
      }
    }
  } catch { }
  return 'unknown'
}

function Psql([string]$Sql) {
  # Passwordless: local unix socket inside the throwaway container -> trust.
  # POSTGRES_USER is the only superuser the image creates (no 'postgres' role
  # exists when POSTGRES_USER is overridden).
  $out = docker exec $PgName psql -U savepoint_fresh -d savepoint_fresh -tAX -c $Sql 2>&1
  if ($LASTEXITCODE -ne 0) { Fail "psql failed: $(Redact ([string]::Join(' ', $out)))" }
  return ([string]::Join("`n", $out)).Trim()
}

function Import-Run([string]$EvidenceHostPath, [string[]]$ExtraArgs) {
  # Evidence is streamed on stdout (--evidence-json -) and captured on the
  # host: a bind-mounted /out is not writable by the image's UID 10001.
  # Container stderr (progress) still streams to the console.
  $cmd = @(
    'run','--rm','--name',$ImporterName,'--network',$NetName,
    '-e','DATABASE_URL','-e','DJANGO_SECRET_KEY','-e','IGDB_CLIENT_ID','-e','IGDB_CLIENT_SECRET',
    $ImageTag,'python','apps/api/manage.py','import_igdb_catalogue','--page-size','500'
  )
  if ($EvidenceHostPath) { $cmd += @('--evidence-json', '-') }
  if ($ExtraArgs) { $cmd += $ExtraArgs }
  if ($EvidenceHostPath) {
    & docker @cmd | Out-File -FilePath $EvidenceHostPath -Encoding utf8
  } else {
    & docker @cmd
  }
  return $LASTEXITCODE
}

# --- state for cleanup ---------------------------------------------------
$script:CleanupDone = $false
function Invoke-Cleanup {
  if ($script:CleanupDone) { return }
  $script:CleanupDone = $true
  Write-Host "--- cleanup ---" -ForegroundColor DarkGray
  docker rm -f $ImporterName  2>&1 | Out-Null
  docker rm -f -v $PgName     2>&1 | Out-Null
  docker network rm $NetName  2>&1 | Out-Null
  docker image rm -f $ImageTag 2>&1 | Out-Null
  if ($env:DATABASE_URL) { Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue }
  if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir -ErrorAction SilentlyContinue }
  # Assert the uniquely-named container really is gone.
  $survivor = docker ps -aq --filter "name=^/$PgName$" 2>$null
  if ($survivor) { Write-Host "WARNING: throwaway container $PgName survived cleanup" -ForegroundColor Red }
  else { Write-Host "throwaway container $PgName removed" -ForegroundColor DarkGray }
}

try {
  foreach ($v in 'IGDB_CLIENT_ID','IGDB_CLIENT_SECRET') {
    if (-not [Environment]::GetEnvironmentVariable($v)) { Fail "$v is not set in the environment (precondition)" }
  }
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

  Write-Host "=== build throwaway API image from this worktree ===" -ForegroundColor Cyan
  docker build -f (Join-Path $RepoRoot 'apps/api/Dockerfile') -t $ImageTag $RepoRoot
  if ($LASTEXITCODE -ne 0) { Fail "image build failed" }

  Write-Host "=== start isolated PostgreSQL (anonymous volume, no named volume) ===" -ForegroundColor Cyan
  docker network create $NetName | Out-Null
  # A random throwaway password; only ever lives in this process + container env.
  [byte[]]$pgBytes = 1..24 | ForEach-Object { Get-Random -Maximum 256 }
  $pgPass = ([Convert]::ToBase64String($pgBytes) -replace '[^A-Za-z0-9]', '') + 'q7'
  docker run -d --name $PgName --network $NetName `
    --mount 'type=volume,dst=/var/lib/postgresql' `
    -e "POSTGRES_DB=savepoint_fresh" -e "POSTGRES_USER=savepoint_fresh" -e "POSTGRES_PASSWORD=$pgPass" `
    -e "POSTGRES_HOST_AUTH_METHOD=scram-sha-256" `
    --health-cmd 'pg_isready -U savepoint_fresh -d savepoint_fresh' --health-interval 2s --health-timeout 3s --health-retries 30 `
    postgres:18.6 | Out-Null
  if ($LASTEXITCODE -ne 0) { Fail "postgres container did not start" }

  # Prove no NAMED volume was created for this run.
  $named = docker volume ls --format '{{.Name}}' | Where-Object { $_ -like "*igdb-fresh*" -or $_ -eq $PgName }
  if ($named) { Fail "a named volume was created: $named" }

  Write-Host "=== wait for database health ===" -ForegroundColor Cyan
  $healthy = $false
  for ($i = 0; $i -lt 60; $i++) {
    $state = (docker inspect -f '{{.State.Health.Status}}' $PgName 2>$null)
    if ($state -eq 'healthy') { $healthy = $true; break }
    Start-Sleep -Seconds 2
  }
  if (-not $healthy) { Fail "database never became healthy" }

  # Connection string: process env only, passed to containers by NAME.
  $env:DATABASE_URL = "postgresql://savepoint_fresh:$pgPass@${PgName}:5432/savepoint_fresh"
  $env:DJANGO_SECRET_KEY = 'igdb-fresh-import-throwaway-key-not-a-secret-000000000000000000'

  Write-Host "=== migrate the empty database ===" -ForegroundColor Cyan
  docker run --rm --network $NetName -e DATABASE_URL -e DJANGO_SECRET_KEY $ImageTag python apps/api/manage.py migrate --noinput
  if ($LASTEXITCODE -ne 0) { Fail "migrate failed" }
  $preWorks = [int](Psql 'SELECT count(*) FROM catalogue_gamework;')
  if ($preWorks -ne 0) { Fail "database is not empty ($preWorks works)" }

  Write-Host "=== start import, then hard-kill after >= 1 committed batch ===" -ForegroundColor Cyan
  docker run -d --name $ImporterName --network $NetName `
    -e DATABASE_URL -e DJANGO_SECRET_KEY -e IGDB_CLIENT_ID -e IGDB_CLIENT_SECRET `
    -v "${OutDir}:/out" `
    $ImageTag python apps/api/manage.py import_igdb_catalogue --page-size 500 | Out-Null
  if ($LASTEXITCODE -ne 0) { Fail "importer container did not start" }

  $killed = $false
  $interruptCursor = 0
  for ($i = 0; $i -lt 900; $i++) {
    Start-Sleep -Seconds 2
    $running = docker ps -q --filter "name=^/$ImporterName$" 2>$null
    $batches = 0
    try { $batches = [int](Psql "SELECT coalesce(max(batches_committed),0) FROM catalogue_igdbimportrun;") } catch { $batches = 0 }
    if ($batches -ge 2) {
      $interruptCursor = [int](Psql "SELECT coalesce(max(last_committed_igdb_id),0) FROM catalogue_igdbimportrun;")
      docker kill $ImporterName 2>&1 | Out-Null
      $killed = $true
      break
    }
    if (-not $running) { Fail "importer exited before it committed 2 batches (see redacted log below)`n$(Redact (docker logs $ImporterName 2>&1 | Out-String))" }
  }
  if (-not $killed) { Fail "importer never reached 2 committed batches within the interrupt window" }
  $interruptLog = Redact (docker logs $ImporterName 2>&1 | Out-String)
  docker rm -f $ImporterName 2>&1 | Out-Null

  $afterKillWorks = [int](Psql 'SELECT count(*) FROM catalogue_gamework;')
  if ($afterKillWorks -le 0) { Fail "no rows survived the interrupt" }
  $killStatus = Psql "SELECT status FROM catalogue_igdbimportrun LIMIT 1;"
  Write-Host "interrupted after cursor=$interruptCursor works=$afterKillWorks status=$killStatus" -ForegroundColor Yellow

  Write-Host "=== resume to completion (this is the long run) ===" -ForegroundColor Cyan
  $rc = Import-Run -EvidenceHostPath (Join-Path $OutDir 'evidence-resume.json') -ExtraArgs @()
  if ($rc -ne 0) { Fail "resume run exited $rc" }
  $evResume = Get-Content (Join-Path $OutDir 'evidence-resume.json') -Raw | ConvertFrom-Json

  Write-Host "=== rerun to prove convergence ===" -ForegroundColor Cyan
  $rc = Import-Run -EvidenceHostPath (Join-Path $OutDir 'evidence-rerun.json') -ExtraArgs @()
  if ($rc -ne 0) { Fail "convergence rerun exited $rc" }
  $evRerun = Get-Content (Join-Path $OutDir 'evidence-rerun.json') -Raw | ConvertFrom-Json

  Write-Host "=== assertions ===" -ForegroundColor Cyan
  $works        = [int](Psql 'SELECT count(*) FROM catalogue_gamework;')
  $srcs         = [int](Psql "SELECT count(*) FROM catalogue_sourcerecord WHERE source='igdb';")
  $distinctSrcs = [int](Psql "SELECT count(DISTINCT source_id) FROM catalogue_sourcerecord WHERE source='igdb';")
  $noProv       = [int](Psql "SELECT count(*) FROM catalogue_gamework gw WHERE NOT EXISTS (SELECT 1 FROM catalogue_sourcerecord sr WHERE sr.work_id = gw.id AND sr.source='igdb');")
  $status       = Psql "SELECT status FROM catalogue_igdbimportrun LIMIT 1;"
  $cursor       = [int](Psql "SELECT last_committed_igdb_id FROM catalogue_igdbimportrun LIMIT 1;")
  $wi           = [int](Psql "SELECT works_imported FROM catalogue_igdbimportrun LIMIT 1;")
  $covPresent   = [int](Psql "SELECT covers_present FROM catalogue_igdbimportrun LIMIT 1;")
  $covFallback  = [int](Psql "SELECT covers_fallback FROM catalogue_igdbimportrun LIMIT 1;")
  $checksum     = Psql "SELECT checksum FROM catalogue_igdbimportrun LIMIT 1;"

  $eligible = [int]$evResume.eligible_count_live
  $floor = [Math]::Max(100000, [Math]::Floor(0.9 * $eligible))

  if ($works -lt $floor)            { Fail "imported $works primary works, below floor $floor (eligible $eligible)" }
  if ($srcs -ne $distinctSrcs)      { Fail "source_id not unique: $srcs rows / $distinctSrcs distinct" }
  if ($srcs -ne $works)            { Fail "provenance mismatch: $srcs igdb source rows / $works works" }
  if ($noProv -ne 0)               { Fail "$noProv works have no igdb provenance row" }
  if ($status -ne 'complete')       { Fail "checkpoint status is '$status', expected 'complete'" }
  if ($cursor -le 0)               { Fail "checkpoint cursor did not advance" }
  if (($covPresent + $covFallback) -ne $wi) { Fail "cover accounting: $covPresent + $covFallback != $wi" }
  if ($wi -ne $works)             { Fail "works_imported ($wi) != actual work count ($works)" }
  if ($evRerun.checksum_sha256 -ne $evResume.checksum_sha256) { Fail "rerun checksum changed: $($evResume.checksum_sha256) -> $($evRerun.checksum_sha256)" }
  if ([int]$evRerun.primary_works_imported -ne [int]$evResume.primary_works_imported) { Fail "rerun work count changed" }
  if ($checksum -ne $evResume.checksum_sha256) { Fail "DB checksum != evidence checksum" }

  $genreCount = @($evResume.genres).Count
  $ckShort = if ($checksum.Length -ge 12) { $checksum.Substring(0, 12) } else { $checksum }
  Write-Host "all assertions passed: $works primary works, checksum $ckShort..., eligible $eligible" -ForegroundColor Green

  # --- freeze evidence -----------------------------------------------------
  Copy-Item (Join-Path $OutDir 'evidence-resume.json') $SampleDoc -Force
  $commit = Get-HeadCommit $RepoRoot
  $commitShort = if ($commit.Length -ge 12) { $commit.Substring(0, 12) } else { $commit }
  $nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

  # This here-string writes into a Spanish thesis document (project convention:
  # docs in Spanish, code in English), so its emitted labels are Spanish. The
  # HTML MEASURED-EVIDENCE markers are load-bearing for the regex below and
  # stay verbatim.
  $measured = @"
<!-- MEASURED-EVIDENCE-START -->
| Campo | Valor |
|---|---|
| Marca de tiempo de la ejecución (UTC) | $nowUtc |
| Commit del repo | ``$commit`` |
| Frontera de consulta | ``$($evResume.where)`` (identidad ``$($evResume.query_identity)``) |
| Conteo elegible en vivo (``game_type = 0``, re-medido) | $eligible |
| Suelo de aceptación ``max(100000, 0.90 x eligible)`` | $floor |
| Obras primarias importadas | $works |
| ``source_id`` distintos == total importado | $distinctSrcs == $works (sí) |
| Portadas presentes / fallback de primera parte | $covPresent / $covFallback |
| Géneros vistos | $genreCount |
| Checksum de contenido (``sha256``) | ``$checksum`` |
| ``IgdbImportRun.status`` / ``last_committed_igdb_id`` | $status / $cursor |

### Observaciones de interrupción / reanudación

- La importación arrancó fresca contra una base de datos vacía, se mató en duro
  (SIGKILL) tras haber commiteado >= 2 batches en
  ``last_committed_igdb_id = $interruptCursor`` ($afterKillWorks obras ya
  durables, estado de la ejecución ``$killStatus``).
- La ejecución de reanudación continuó hacia delante desde el checkpoint
  commiteado (el trigger de cursor monótono garantiza que no pudo regresar) y
  llevó la importación a ``status = complete`` sin valores ``source_id``
  duplicados.

### Convergencia de la re-ejecución

- Una tercera invocación, con el checkpoint ya ``complete``, re-escaneó el
  catálogo completo desde id 0 y convergió:
  obras primarias ``$($evResume.primary_works_imported)`` -> ``$($evRerun.primary_works_imported)``,
  checksum ``$($evResume.checksum_sha256)`` sin cambios.

### Resultados de comandos redactados

``````
$($interruptLog.Trim())
``````
<!-- MEASURED-EVIDENCE-END -->
"@

  $doc = Get-Content $FreezeDoc -Raw
  $doc = [regex]::Replace(
    $doc,
    '(?s)<!-- MEASURED-EVIDENCE-START -->.*?<!-- MEASURED-EVIDENCE-END -->',
    { param($m) $measured.TrimEnd() }
  )
  $doc = $doc -replace '(?m)^\*\*Estado:\*\* (PENDING|PENDIENTE).*$', "**Estado:** CONGELADO ($nowUtc, commit $commitShort)"
  Set-Content -Path $FreezeDoc -Value $doc -NoNewline -Encoding UTF8

  Write-Host ""
  Write-Host "VERIFY-IGDB-FRESH-IMPORT: PASS" -ForegroundColor Green
  exit 0
}
catch {
  Write-Host ""
  Write-Host "VERIFY-IGDB-FRESH-IMPORT: FAIL -- $(Redact ($_ | Out-String))" -ForegroundColor Red
  exit 1
}
finally {
  Invoke-Cleanup
}
