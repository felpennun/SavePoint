param(
    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"

if (-not $RepositoryRoot) {
    $RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
} else {
    $RepositoryRoot = (Resolve-Path $RepositoryRoot).Path
}

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$Invariant = [System.Globalization.CultureInfo]::InvariantCulture
$KValues = @(5, 10, 20)
$RunId = "evaluation-400-test-2026-09-12-v15"
$PackageId = "phase-07-evidence-v1"

$ArtifactPath = "apps/api/evaluation-400-test-2026-09-12-v15.artifact.json"
$CohortPath = "docs/verification/evaluation-cohorts-400-test-2026-09-12-v15.json"
$ProtocolPath = "docs/methodology/protocol.json"

function Get-RelativeFullPath([string]$RelativePath) {
    if ([System.IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains("..")) {
        throw "Input path is not relative and allowlisted: $RelativePath"
    }
    $full = Join-Path $RepositoryRoot ($RelativePath -replace "/", [System.IO.Path]::DirectorySeparatorChar)
    $resolved = (Resolve-Path -LiteralPath $full -ErrorAction Stop).Path
    $rootWithSeparator = $RepositoryRoot.TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Input path escapes repository root: $RelativePath"
    }
    return $resolved
}

function Get-Sha256([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (([System.BitConverter]::ToString($sha.ComputeHash($Bytes))) -replace "-", "").ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Read-Source([pscustomobject]$Spec) {
    $full = Get-RelativeFullPath $Spec.path
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $actual = Get-Sha256 $bytes
    if ($actual -ne $Spec.sha256) {
        throw "Source checksum drifted before generation: $($Spec.path)"
    }
    $text = $Utf8NoBom.GetString($bytes)
    return [pscustomobject]@{
        path = $Spec.path
        role = $Spec.role
        sha256 = $actual
        bytes = $bytes
        text = $text
    }
}

function Read-JsonSource([pscustomobject]$Spec) {
    $source = Read-Source $Spec
    try {
        $parsed = $source.text.TrimStart([char]0xFEFF) | ConvertFrom-Json
    } catch {
        throw "Allowlisted JSON source is invalid: $($Spec.path)"
    }
    return [pscustomobject]@{
        path = $source.path
        role = $source.role
        sha256 = $source.sha256
        bytes = $source.bytes
        text = $source.text
        data = $parsed
    }
}

function Get-PropertyValue($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Require-Equal($Actual, $Expected, [string]$Name) {
    if ($Actual -ne $Expected) {
        throw "Published identity mismatch for $Name"
    }
}

function Require-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Format-Number($Value) {
    if ($null -eq $Value) { return "" }
    if ($Value -is [double] -or $Value -is [single] -or $Value -is [decimal]) {
        return ([double]$Value).ToString("G17", $Invariant)
    }
    return ([string]$Value)
}

function Quote-Csv([string]$Value) {
    if ($null -eq $Value) { $Value = "" }
    return '"' + ($Value -replace '"', '""') + '"'
}

function Write-DeterministicText([string]$RelativePath, [string]$Text) {
    $full = Join-Path $RepositoryRoot ($RelativePath -replace "/", [System.IO.Path]::DirectorySeparatorChar)
    $resolvedParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $full))
    $rootWithSeparator = $RepositoryRoot.TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolvedParent.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Output path escapes repository root: $RelativePath"
    }
    $parent = Split-Path -Parent $full
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($full, ($Text.TrimEnd("`r", "`n") + "`n"), $Utf8NoBom)
}

function Escape-Xml([string]$Value) {
    if ($null -eq $Value) { return "" }
    return [System.Security.SecurityElement]::Escape($Value)
}

# Every source is explicit.  The hashes are the publication boundary and make
# accidental use of a newer or unrelated document fail closed.
$SourceSpecs = @(
    [pscustomobject]@{ path = $ArtifactPath; role = "published_v15_artifact"; sha256 = "5fd46ebed2814fca62fdf094a744671383abf66f7d822caeb873ea44be67b8ab" },
    [pscustomobject]@{ path = $CohortPath; role = "published_cohort_snapshot"; sha256 = "7417c29ffa02de5e512bc8f2aeb4ba9a992a53d50f85af76dc441cf1a555aab0" },
    [pscustomobject]@{ path = $ProtocolPath; role = "current_protocol_pointer_anchors_only"; sha256 = "f4b19005f3b45018e34e614c0ff8a86ad22438fdfd01f823304871525fa3e1e4" },
    [pscustomobject]@{ path = "pyproject.toml"; role = "python_environment_declaration"; sha256 = "1d757df28246af887657e8a4f23cf4aa0529253d613521d3e84d00aaf78efd80" },
    [pscustomobject]@{ path = "uv.lock"; role = "python_dependency_lock"; sha256 = "161ede18c48e70bf281ec6a483bb2087c7e8abe0ada95492bd07a33b6dae69f9" },
    [pscustomobject]@{ path = "package.json"; role = "node_environment_declaration"; sha256 = "0cacf29f609414c3b6b6333e43fbd3294aff403e634c5bdcde29cbb8a5430cb7" },
    [pscustomobject]@{ path = "pnpm-lock.yaml"; role = "node_dependency_lock"; sha256 = "66229cd8b371f77fefdea23dec8f250c3b55dfb7f09020628b0cdfce437a9284" },
    [pscustomobject]@{ path = "apps/web/package.json"; role = "frontend_package_declaration"; sha256 = "7052c7dc80d441b2b8bca6fc570e41185c46dfa1b113966c2547284b8491ec20" },
    [pscustomobject]@{ path = "infra/compose.yaml"; role = "local_runtime_declaration"; sha256 = "3c2a633c9bd3319fde3d14792d006c567f2090f1d0093aa9aaaa0750e889e9e8" },
    [pscustomobject]@{ path = "docs/verification/phase-07-evidence-contract.md"; role = "panel_publication_contract"; sha256 = "5e5f4f903e3be4d62a820e58980ac5d93f5873f2ccd7fa3c15e4929cdab4c01a" },
    [pscustomobject]@{ path = "docs/verification/igdb-catalogue-freeze.md"; role = "catalogue_provenance_and_licence"; sha256 = "150f3aab21f4e3749e53610d65eba0f97d05cb55ad2b30781e2633ae03ea6871" },
    [pscustomobject]@{ path = "docs/adr/ADR-006-igdb-source.md"; role = "source_decision_and_licence"; sha256 = "b9b54b886e6483699e9576a6818ea99739f05c588f97f903fe447638f12f9dd5" },
    [pscustomobject]@{ path = "docs/deployment/public-demo.md"; role = "cost_and_runtime_provenance"; sha256 = "272d5fe1cd47898c678f157d2f3ded2cc74d2e13eb07c855047c5686839e29c4" },
    [pscustomobject]@{ path = "docs/methodology/agent-method.md"; role = "agent_methodology"; sha256 = "893e06d711612cf7009fdd304d410ebaae66aeefccbd5df52d9751a558b0a021" },
    [pscustomobject]@{ path = "docs/methodology/agent-methodology-controls.md"; role = "agent_controls"; sha256 = "d19514b3f83259a19de1a4d71156bd85e0814cb201b01dbee38a2c1dba52a890" },
    [pscustomobject]@{ path = "thesis/README.md"; role = "thesis_format_and_delivery_rules"; sha256 = "e38c0abd89a6b9f76bdc8a662617e4f239973225a987da54dd3319f3a140065b" }
)

$Sources = @{}
foreach ($spec in $SourceSpecs) {
    if ($Sources.ContainsKey($spec.path)) { throw "Duplicate allowlisted source: $($spec.path)" }
    $Sources[$spec.path] = Read-Source $spec
}
$ArtifactSource = Read-JsonSource ($SourceSpecs | Where-Object path -eq $ArtifactPath)
$CohortSource = Read-JsonSource ($SourceSpecs | Where-Object path -eq $CohortPath)
$ProtocolSource = Read-JsonSource ($SourceSpecs | Where-Object path -eq $ProtocolPath)
$Artifact = $ArtifactSource.data
$Cohorts = $CohortSource.data
$Protocol = $ProtocolSource.data

# Validate identity and shared protocol anchors before any output is written.
Require-Equal $Artifact.status "succeeded" "artifact.status"
Require-Equal $Artifact.protocol_version 15 "artifact.protocol_version"
Require-Equal $Artifact.protocol_sha256 "d492cfe305287428566b4ae02c4c8f9a86ac38dcf53d33ccbc8748ae27905b1a" "artifact.protocol_sha256"
Require-Equal $Artifact.corpus_version "2026.09.2" "artifact.corpus_version"
Require-Equal $Artifact.snapshot_sha256 "c42f46a42d091e11cd894c3f942b8979b77f611ac7a4b048d8d152bebe8ce3cc" "artifact.snapshot_sha256"
Require-Equal $Artifact.popscore_snapshot_sha256 "16de92f28fa5b3dd1b387110628561eb6330b271ed2b1e76a69a7e0f03083097" "artifact.popscore_snapshot_sha256"
Require-Equal $Artifact.split "test" "artifact.split"
Require-True ($Artifact.simulation -eq $true) "Artifact simulation flag drifted"
Require-Equal $Artifact.evaluation_population.split_total 400 "artifact.evaluation_population.split_total"
Require-Equal $Artifact.evaluation_population.active_user_count 400 "artifact.evaluation_population.active_user_count"
Require-Equal $Artifact.evaluation_population.evaluated_user_count 79 "artifact.evaluation_population.evaluated_user_count"
Require-Equal $Artifact.evaluation_population.skipped_user_count 1 "artifact.evaluation_population.skipped_user_count"
Require-True ($null -ne $Artifact.algorithms) "Artifact algorithms are missing"

Require-Equal $Cohorts.artifact_protocol_version 15 "cohorts.artifact_protocol_version"
Require-Equal $Cohorts.artifact_protocol_sha256 $Artifact.protocol_sha256 "cohorts.artifact_protocol_sha256"
Require-Equal $Cohorts.corpus_version $Artifact.corpus_version "cohorts.corpus_version"
Require-Equal $Cohorts.split $Artifact.split "cohorts.split"
Require-Equal $Cohorts.population_count 400 "cohorts.population_count"
Require-Equal $Cohorts.artifact_evaluated_user_count 79 "cohorts.artifact_evaluated_user_count"
$cohortIds = @($Cohorts.cohorts.PSObject.Properties | ForEach-Object { $_.Name })
Require-True (($cohortIds -join ",") -eq "active_history_10_to_20,no_history") "Cohort order or allowlist drifted"

Require-True ($Protocol.protocol_version -ge 15) "Current protocol pointer predates publication"
Require-True ($Protocol.simulation -eq $true) "Current protocol simulation flag drifted"
Require-Equal $Protocol.corpus_version $Artifact.corpus_version "protocol.corpus_version"
Require-Equal $Protocol.snapshot_sha256 $Artifact.snapshot_sha256 "protocol.snapshot_sha256"
Require-Equal $Protocol.popscore_snapshot_sha256 $Artifact.popscore_snapshot_sha256 "protocol.popscore_snapshot_sha256"
Require-Equal ($Protocol.k_values -join ",") "5,10,20" "protocol.k_values"
Require-Equal $Protocol.headline "ndcg@10" "protocol.headline"
Require-Equal $Protocol.split.strategy "leave_fraction_out_dominant_tag_per_user" "protocol.split.strategy"
Require-Equal $Protocol.split.seed 20260907 "protocol.split.seed"
Require-Equal $Protocol.user_split.seed 20260908 "protocol.user_split.seed"

$algorithmIds = @($Artifact.algorithms.PSObject.Properties | ForEach-Object { $_.Name })
Require-Equal $algorithmIds.Count 16 "artifact algorithm count"
foreach ($cohortId in $cohortIds) {
    $cohort = $Cohorts.cohorts.PSObject.Properties[$cohortId].Value
    $cohortAlgorithms = @($cohort.algorithms.PSObject.Properties | ForEach-Object { $_.Name })
    Require-True ((($cohortAlgorithms | Sort-Object) -join ",") -eq (($algorithmIds | Sort-Object) -join ",")) "Cohort algorithm allowlist drifted: $cohortId"
}

$Rows = New-Object System.Collections.Generic.List[object]
foreach ($cohortId in $cohortIds) {
    $cohort = $Cohorts.cohorts.PSObject.Properties[$cohortId].Value
    foreach ($algorithmId in $algorithmIds) {
        $algorithm = $Artifact.algorithms.PSObject.Properties[$algorithmId].Value
        $cohortAlgorithm = $cohort.algorithms.PSObject.Properties[$algorithmId].Value
        foreach ($k in $KValues) {
            $summary = $cohortAlgorithm.summary_by_k.PSObject.Properties[[string]$k].Value
            $metrics = [ordered]@{}
            foreach ($metric in @("precision", "recall", "ndcg", "map")) {
                $metrics[$metric] = Get-PropertyValue $summary.metrics $metric
            }
            foreach ($metric in @("intra_list_diversity", "novelty", "recommended_count")) {
                $metrics[$metric] = Get-PropertyValue (Get-PropertyValue $summary.beyond_accuracy $metric) "value"
            }
            foreach ($metric in @("catalogue_coverage", "concentration_hhi", "prediction_coverage")) {
                $metrics[$metric] = $null
            }
            $Rows.Add([pscustomobject][ordered]@{
                run_id = $RunId
                protocol_version = 15
                corpus_version = $Artifact.corpus_version
                split = $Artifact.split
                algorithm_id = $algorithmId
                cohort_id = $cohortId
                k = $k
                evaluable_count = $summary.user_count
                population_count = $cohort.population_user_count
                not_evaluable_count = $cohortAlgorithm.not_evaluable_user_count
                metrics = $metrics
                duration_seconds = $algorithm.duration_seconds
                timing_scope = "algorithm_wall_clock_seconds"
                not_evaluable_reason = Get-PropertyValue $cohort "not_evaluable_reason"
                run_level_metric_note = "No se desagrega: el JSON de cohortes declara esta métrica solo a nivel de ejecución."
            })
        }
    }
}
Require-Equal $Rows.Count 96 "public row count"

$TimingRows = New-Object System.Collections.Generic.List[object]
foreach ($algorithmId in $algorithmIds) {
    $algorithm = $Artifact.algorithms.PSObject.Properties[$algorithmId].Value
    $worker = @($Artifact.worker_timings | Where-Object algorithm_id -eq $algorithmId | Select-Object -First 1)
    Require-Equal $worker.Count 1 "worker timing count: $algorithmId"
    $TimingRows.Add([pscustomobject][ordered]@{
        algorithm_id = $algorithmId
        status = $worker[0].status
        duration_seconds = $algorithm.duration_seconds
        started_at = $worker[0].started_at
        finished_at = $worker[0].finished_at
    })
}

$rootPackage = $Sources["package.json"].text | ConvertFrom-Json
$pyprojectText = $Sources["pyproject.toml"].text
$composeText = $Sources["infra/compose.yaml"].text
$pythonDeclaration = if ($pyprojectText -match 'requires-python\s*=\s*"([^"]+)"') { $Matches[1] } else { "unknown" }
$uvDeclaration = if ($pyprojectText -match 'required-version\s*=\s*"([^"]+)"') { $Matches[1] } else { "unknown" }
$postgresImage = if ($composeText -match '(?m)^\s*image:\s*(postgres:[^\r\n]+)') { $Matches[1].Trim() } else { "unknown" }
$Environment = [ordered]@{
    captured_runtime = $false
    runtime_capture_reason = "El artefacto v15 no registró CPU, sistema operativo ni versiones observadas en ejecución; no se rellenan retrospectivamente."
    declared_toolchain = [ordered]@{
        python = $pythonDeclaration
        uv = $uvDeclaration
        node = Get-PropertyValue $rootPackage.engines "node"
        pnpm = $rootPackage.packageManager
        next = $rootPackage.dependencies.next
        react = $rootPackage.dependencies.react
        typescript = $rootPackage.devDependencies.typescript
        playwright = $rootPackage.devDependencies."@playwright/test"
        postgres_image = $postgresImage
    }
    lockfiles = @("pyproject.toml", "uv.lock", "package.json", "pnpm-lock.yaml", "apps/web/package.json")
}

$StatisticalComparison = $null
$headlineStats = Get-PropertyValue $Artifact.statistical_comparisons "ndcg@10"
if ($null -ne $headlineStats) {
    $StatisticalComparison = [ordered]@{
        family = $headlineStats.family
        statistics_version = $headlineStats.statistics_version
        user_count = $headlineStats.user_count
        algorithm_order = @($headlineStats.algorithm_order)
        configuration = $headlineStats.configuration
        friedman = $headlineStats.friedman
        pairwise = $headlineStats.pairwise
        input_sha256 = $headlineStats.input_sha256
    }
}

$Provenance = [ordered]@{
    publication = [ordered]@{
        run_id = $RunId
        artifact_sha256 = $ArtifactSource.sha256
        cohort_sha256 = $CohortSource.sha256
        protocol_version = 15
        protocol_sha256 = $Artifact.protocol_sha256
        corpus_version = $Artifact.corpus_version
        snapshot_sha256 = $Artifact.snapshot_sha256
        popscore_snapshot_sha256 = $Artifact.popscore_snapshot_sha256
        split = $Artifact.split
        split_manifest_sha256 = $Artifact.split_manifest_sha256
        code_commit = $Artifact.code_commit
    }
    current_protocol_pointer = [ordered]@{
        path = $ProtocolPath
        sha256 = $ProtocolSource.sha256
        protocol_version = $Protocol.protocol_version
        use = "Solo se validan anclajes compartidos; no produce ni reinterpreta las métricas v15."
    }
    source_paths = @($ArtifactPath, $CohortPath, $ProtocolPath)
    derivation = "Lectura UTF-8, validación de SHA-256 y proyección allowlisted de agregados publicados; no se importa el runner ni se consulta la base de datos."
}

$Limitations = @(
    $Artifact.limitation,
    $Cohorts.limitations.explanation,
    "La ejecución de test es un único run publicado; las semillas identifican partición y población, no un estudio de sensibilidad multi-semilla.",
    "Los 79 usuarios evaluables proceden de una población solicitada de 400; el artefacto conserva además requested_user_count=80 para el subconjunto de evaluación y se mantiene como metadato, sin reinterpretarlo.",
    "No hay captura histórica de CPU, sistema operativo ni entorno completo; los tiempos conservados son wall-clock del artefacto.",
    "La evidencia es simulación sobre arquetipos sintéticos y no evidencia sobre usuarios reales.",
    "La validez legal de los términos externos requiere revisión del autor antes de redistribuir cualquier dato; el paquete no incluye el corpus ni volcados privados."
)

$Licences = @(
    [pscustomobject][ordered]@{ subject = "IGDB structured metadata"; basis = "Twitch Developer Services Agreement y FAQ de IGDB documentados en ADR-006"; cost = "0 EUR para el uso académico declarado"; redistribution = "No se redistribuye el dataset en bloque; se conserva atribución visible a IGDB.com."; source_path = "docs/adr/ADR-006-igdb-source.md" },
    [pscustomobject][ordered]@{ subject = "IGDB cover images"; basis = "Regla de hotlink y ventana de imágenes documentada en la congelación del catálogo"; cost = "0 EUR"; redistribution = "No se replican portadas en este paquete."; source_path = "docs/verification/igdb-catalogue-freeze.md" },
    [pscustomobject][ordered]@{ subject = "Research evidence outputs"; basis = "Agregados derivados del artefacto v15 y saneados"; cost = "0 EUR recurrente; no se añade servicio de pago"; redistribution = "Solo se publican estas salidas agregadas cuando el autor confirme su adecuación."; source_path = "docs/verification/phase-07-evidence-contract.md" }
)

$Contributions = @(
    [pscustomobject][ordered]@{ actor = "Felipe"; kind = "human"; role = "author"; contribution = "Define alcance, revisa fuentes, licencias, resultados e interpretación y conserva la responsabilidad académica final."; status = "author-review-required" },
    [pscustomobject][ordered]@{ actor = "gsd-phase-researcher / gsd-planner"; kind = "agent"; role = "research-and-planning"; contribution = "Aporta contexto, restricciones y criterios de evidencia en los artefactos de planificación; no aprueba decisiones académicas."; status = "proposal" },
    [pscustomobject][ordered]@{ actor = "gsd-executor"; kind = "agent"; role = "implementation"; contribution = "Implementa este generador, proyecta salidas allowlisted y redacta documentación; no se presenta como revisión independiente."; status = "automated-output" },
    [pscustomobject][ordered]@{ actor = "deterministic checkers"; kind = "tool"; role = "automated-verification"; contribution = "Comprueban hashes, esquema documental, ausencia de cambios de diff y reproducibilidad del paquete."; status = "automated-check" }
)

$MetricDefinitions = @(
    [pscustomobject][ordered]@{ metric_id = "precision"; unit = "ratio"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "recall"; unit = "ratio"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "ndcg"; unit = "ratio"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "map"; unit = "ratio"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "intra_list_diversity"; unit = "ratio"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "novelty"; unit = "score"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "recommended_count"; unit = "count"; higher_is_better = $true; source = "cohort summary_by_k" },
    [pscustomobject][ordered]@{ metric_id = "catalogue_coverage"; unit = "ratio"; higher_is_better = $true; source = "run-level-only; null by cohort" },
    [pscustomobject][ordered]@{ metric_id = "concentration_hhi"; unit = "ratio"; higher_is_better = $false; source = "run-level-only; null by cohort" },
    [pscustomobject][ordered]@{ metric_id = "prediction_coverage"; unit = "ratio"; higher_is_better = $true; source = "run-level-only; null by cohort" }
)

$Configuration = [ordered]@{
    feature_set_version = $Artifact.feature_set_version
    k_values = $KValues
    headline = "ndcg@10"
    seeds = [ordered]@{
        leave_one_out = $Artifact.seeds.leave_one_out
        user_split = $Artifact.seeds.user_split
        synthetic_population = $Protocol.synthetic_population.seed
    }
    split = $Artifact.split
    evaluation_population = $Artifact.evaluation_population
    algorithm_count = $algorithmIds.Count
    parallel_execution = [ordered]@{
        process_per_algorithm = $Artifact.parallel_execution.process_per_algorithm
        max_workers = $Artifact.parallel_execution.max_workers
        worker_count = $Artifact.parallel_execution.worker_count
        serial_tail = $Artifact.parallel_execution.serial_tail
    }
    tuning_pointer = [ordered]@{
        source = $ProtocolPath
        current_protocol_version = $Protocol.protocol_version
        grid_size = @($Protocol.tuning.grid).Count
        not_used_for_v15_metrics = $true
    }
}

$SanitisedRows = @($Rows | ForEach-Object {
    [pscustomobject][ordered]@{
        run_id = $_.run_id
        protocol_version = $_.protocol_version
        corpus_version = $_.corpus_version
        split = $_.split
        algorithm_id = $_.algorithm_id
        cohort_id = $_.cohort_id
        k = $_.k
        evaluable_count = $_.evaluable_count
        population_count = $_.population_count
        not_evaluable_count = $_.not_evaluable_count
        metrics = $_.metrics
        timing = [ordered]@{
            duration_seconds = $_.duration_seconds
            scope = $_.timing_scope
        }
        not_evaluable_reason = $_.not_evaluable_reason
        run_level_metric_note = $_.run_level_metric_note
    }
})

$ResultPayload = [ordered]@{
    schema_version = 1
    package_id = $PackageId
    generated_from = "published_v15_snapshot"
    run = $Provenance.publication
    configuration = $Configuration
    metric_definitions = $MetricDefinitions
    rows = $SanitisedRows
    timings = [ordered]@{
        suite = [ordered]@{
            max_workers = $Artifact.parallel_execution.max_workers
            process_per_algorithm = $Artifact.parallel_execution.process_per_algorithm
            worker_count = $Artifact.parallel_execution.worker_count
            sum_worker_duration_seconds = $Artifact.parallel_execution.sum_worker_duration_seconds
            wall_duration_seconds = $Artifact.parallel_execution.wall_duration_seconds
            wall_started_at = $Artifact.parallel_execution.wall_started_at
            wall_finished_at = $Artifact.parallel_execution.wall_finished_at
        }
        algorithms = $TimingRows.ToArray()
        cpu_time = $null
        cpu_time_unavailable_reason = "No registrado por el artefacto v15."
    }
    statistical_comparison = $StatisticalComparison
    environment = $Environment
    provenance = $Provenance
    licences = $Licences
    limitations = $Limitations
    contributions = $Contributions
    sanitisation = [ordered]@{
        includes_aggregate_rows = $true
        includes_individual_user_data = $false
        includes_raw_logs = $false
        includes_private_dumps = $false
        includes_secrets = $false
        includes_absolute_paths = $false
        recalculates_metrics = $false
    }
}

$OutputJsonPath = "docs/verification/phase-07-results.json"
$OutputCsvPath = "docs/verification/phase-07-results.csv"
$OutputSvgPath = "docs/verification/phase-07-comparison.svg"
$ManifestPath = "docs/verification/phase-07-evidence-manifest.json"

$jsonText = $ResultPayload | ConvertTo-Json -Depth 20
Write-DeterministicText $OutputJsonPath $jsonText

$csvColumns = @("run_id", "protocol_version", "corpus_version", "split", "algorithm_id", "cohort_id", "k", "evaluable_count", "population_count", "not_evaluable_count", "precision", "recall", "ndcg", "map", "intra_list_diversity", "novelty", "recommended_count", "catalogue_coverage", "concentration_hhi", "prediction_coverage", "duration_seconds", "timing_scope", "not_evaluable_reason", "run_level_metric_note")
$csvLines = New-Object System.Collections.Generic.List[string]
$csvLines.Add(($csvColumns | ForEach-Object { Quote-Csv $_ }) -join ",")
foreach ($row in $Rows) {
    $values = @(
        $row.run_id, $row.protocol_version, $row.corpus_version, $row.split,
        $row.algorithm_id, $row.cohort_id, $row.k, $row.evaluable_count,
        $row.population_count, $row.not_evaluable_count,
        $row.metrics.precision, $row.metrics.recall, $row.metrics.ndcg,
        $row.metrics.map, $row.metrics.intra_list_diversity, $row.metrics.novelty,
        $row.metrics.recommended_count, $row.metrics.catalogue_coverage,
        $row.metrics.concentration_hhi, $row.metrics.prediction_coverage,
        $row.duration_seconds, $row.timing_scope, $row.not_evaluable_reason,
        $row.run_level_metric_note
    )
    $csvLines.Add(($values | ForEach-Object { Quote-Csv (Format-Number $_) }) -join ",")
}
Write-DeterministicText $OutputCsvPath (($csvLines -join "`n"))

# A fixed 0..1 scale is used for headline nDCG@10. Bar widths are a visual
# encoding of the published value; no ranking, aggregation, or metric is made.
$chartRows = @($Rows | Where-Object { $_.cohort_id -eq "active_history_10_to_20" -and $_.k -eq 10 })
$svgHeight = 100 + ($chartRows.Count * 34)
$svgLines = New-Object System.Collections.Generic.List[string]
$svgLines.Add('<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 760 ' + $svgHeight + '">')
$svgLines.Add('  <title id="title">nDCG@10 por algoritmo — cohorte active_history_10_to_20</title>')
$svgLines.Add('  <desc id="desc">Comparación derivada del snapshot v15. Escala fija de 0 a 1; cada etiqueta incluye el valor exacto publicado.</desc>')
$svgLines.Add('  <rect width="760" height="' + $svgHeight + '" fill="#161826"/>')
$svgLines.Add('  <text x="12" y="24" fill="#f7f7fa" font-family="sans-serif" font-size="16">nDCG@10 · active_history_10_to_20 · v15</text>')
$svgLines.Add('  <text x="640" y="24" text-anchor="end" fill="#c7c9d9" font-family="monospace" font-size="12">escala 0–1</text>')
$chartIndex = 0
foreach ($row in $chartRows) {
    $y = 52 + ($chartIndex * 34)
    $valueText = Format-Number $row.metrics.ndcg
    $width = if ($null -eq $row.metrics.ndcg) { 0 } else { [Math]::Round(([double]$row.metrics.ndcg) * 560, 3) }
    $label = Escape-Xml $row.algorithm_id
    $aria = Escape-Xml ("{0}: nDCG@10 = {1}" -f $row.algorithm_id, $valueText)
    $svgLines.Add('  <text x="12" y="' + ($y + 14) + '" fill="#f7f7fa" font-family="monospace" font-size="11">' + $label + '</text>')
    $svgLines.Add('  <rect x="178" y="' + $y + '" width="560" height="20" fill="#292b31" stroke="#5d5294" stroke-width="1"/>')
    if ($width -gt 0) { $svgLines.Add('  <rect x="178" y="' + $y + '" width="' + $width + '" height="20" fill="#9184d9"><title>' + $aria + '</title></rect>') }
    $svgLines.Add('  <text x="748" y="' + ($y + 14) + '" text-anchor="end" fill="#f7f7fa" font-family="monospace" font-size="11">' + (Escape-Xml $valueText) + '</text>')
    $chartIndex++
}
$svgLines.Add('  <text x="178" y="' + ($svgHeight - 12) + '" fill="#c7c9d9" font-family="monospace" font-size="11">0</text>')
$svgLines.Add('  <text x="738" y="' + ($svgHeight - 12) + '" text-anchor="end" fill="#c7c9d9" font-family="monospace" font-size="11">1</text>')
$svgLines.Add('</svg>')
Write-DeterministicText $OutputSvgPath (($svgLines -join "`n"))

$outputSpecs = @(
    [pscustomobject]@{ path = $OutputJsonPath; role = "sanitised_thesis_ready_json" },
    [pscustomobject]@{ path = $OutputCsvPath; role = "thesis_ready_csv" },
    [pscustomobject]@{ path = $OutputSvgPath; role = "accessible_headline_figure" }
)
$outputRecords = @()
foreach ($output in $outputSpecs) {
    $full = Get-RelativeFullPath $output.path
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $outputRecords += [pscustomobject][ordered]@{
        path = $output.path
        role = $output.role
        sha256 = Get-Sha256 $bytes
        bytes = $bytes.Length
    }
}

$sourceRecords = @($SourceSpecs | ForEach-Object {
    [pscustomobject][ordered]@{ path = $_.path; role = $_.role; sha256 = $Sources[$_.path].sha256 }
})
$Manifest = [ordered]@{
    schema_version = 1
    package_id = $PackageId
    manifest_policy = "Este manifiesto no se auto-hash-ea; su identidad está cubierta por el commit que lo versiona."
    publication = $Provenance.publication
    protocol = [ordered]@{
        published_version = 15
        published_sha256 = $Artifact.protocol_sha256
        current_pointer_version = $Protocol.protocol_version
        current_pointer_sha256 = $ProtocolSource.sha256
        pointer_usage = "Anclajes compartidos únicamente; no se usa para recalcular ni reinterpretar v15."
    }
    corpus = [ordered]@{
        version = $Artifact.corpus_version
        snapshot_sha256 = $Artifact.snapshot_sha256
        popscore_snapshot_sha256 = $Artifact.popscore_snapshot_sha256
        split = $Artifact.split
        split_manifest_sha256 = $Artifact.split_manifest_sha256
    }
    seeds = $Configuration.seeds
    configuration = $Configuration
    population = [ordered]@{
        requested_population_users = $Artifact.evaluation_population.expected_user_count
        active_users = $Artifact.evaluation_population.active_user_count
        evaluable_users = $Artifact.evaluation_population.evaluated_user_count
        skipped_users = $Artifact.evaluation_population.skipped_user_count
        evaluation_subset_requested_users = $Artifact.evaluation_population.requested_user_count
        split_total = $Artifact.evaluation_population.split_total
    }
    metrics = [ordered]@{
        row_count = $Rows.Count
        algorithms = $algorithmIds
        cohorts = $cohortIds
        k_values = $KValues
        headline = "ndcg@10"
        definitions = $MetricDefinitions
        statistical_comparison = $StatisticalComparison
    }
    timings = $ResultPayload.timings
    environment = $Environment
    limitations = $Limitations
    provenance = $Provenance
    licences = $Licences
    contributions = $Contributions
    source_inputs = $sourceRecords
    generated_outputs = $outputRecords
    sanitisation = $ResultPayload.sanitisation
}
Write-DeterministicText $ManifestPath ($Manifest | ConvertTo-Json -Depth 20)

Write-Output ("PASS: generated {0}; rows={1}; outputs={2}; source hashes verified before write" -f $PackageId, $Rows.Count, $outputRecords.Count)
