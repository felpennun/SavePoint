[CmdletBinding()]
param(
    [ValidateSet("Sources", "Recommendations", "Full")]
    [string]$Scope = "Full",
    [switch]$RefreshManifest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$manifestPath = Join-Path $repoRoot "thesis\SOURCE-MANIFEST.json"
$largeSourceThreshold = 262144
$allowedStatuses = @("complete", "pending", "missing", "not_applicable")
$generatedInputs = @(
    "thesis/SOURCE-MANIFEST.json",
    "thesis/STRUCTURE-MAP.md",
    "thesis/EVIDENCE-MATRIX.md",
    "thesis/ALGORITHM-MATRIX.md",
    "thesis/SIGNAL-MATRIX.md",
    "thesis/FIGURE-PLAN.md",
    "thesis/REQUIREMENTS-TRACEABILITY.md",
    "scripts/verify-thesis-inventory.ps1",
    "ideas-vault/Requisitos/Requisitos - Tesis y metodologia con agentes.md"
)
$matrixPaths = @(
    "thesis/STRUCTURE-MAP.md",
    "thesis/EVIDENCE-MATRIX.md",
    "thesis/ALGORITHM-MATRIX.md",
    "thesis/SIGNAL-MATRIX.md",
    "thesis/FIGURE-PLAN.md",
    "thesis/REQUIREMENTS-TRACEABILITY.md"
)
$canonicalPlaceholder = "% PENDIENTE: confirmar con el autor"

function Assert-Condition {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Test-SafeRelativePath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw "Source path must not be empty." }
    if ([IO.Path]::IsPathRooted($Path) -or $Path -match '(^|/)\.\.(/|$)' -or $Path.Contains('\')) {
        throw "Source path must be a contained repository-relative path: $Path"
    }
    return $true
}

function Get-LfBytes {
    param([string]$AbsolutePath)
    $text = [IO.File]::ReadAllText($AbsolutePath)
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    # Preserve empty files as an empty byte array instead of emitting no pipeline value.
    return ,([Text.UTF8Encoding]::new($false).GetBytes($normalized))
}

function Get-Sha256Hex {
    param([byte[]]$Bytes)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Test-IsTextPath {
    param([string]$Path)
    $extension = [IO.Path]::GetExtension($Path).ToLowerInvariant()
    return $extension -in @(".md", ".txt", ".tex", ".bib", ".json", ".jsonl", ".csv", ".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".css", ".html", ".xml", ".yaml", ".yml", ".toml", ".ini", ".ps1", ".sh", ".env", ".example", ".sql")
}

function Get-TextLineCount {
    param([byte[]]$Bytes)
    $text = [Text.Encoding]::UTF8.GetString($Bytes)
    if ($text.Length -eq 0) { return 0 }
    $newlines = [regex]::Matches($text, "`n").Count
    if ($text.EndsWith("`n")) { return $newlines }
    return $newlines + 1
}

function New-ReadRanges {
    param([int64]$TotalUnits, [int64]$ChunkSize)
    $ranges = @()
    if ($TotalUnits -le 0) { return $ranges }
    for ($start = 1; $start -le $TotalUnits; $start += $ChunkSize) {
        $end = [Math]::Min($TotalUnits, $start + $ChunkSize - 1)
        $ranges += [ordered]@{ start = $start; end = $end }
    }
    return $ranges
}

function Assert-ExactCoverage {
    param([object[]]$Ranges, [int64]$TotalUnits)
    Assert-Condition ($TotalUnits -gt 0) "Complete ranged source must declare positive total_units."
    Assert-Condition ($Ranges.Count -gt 0) "Complete ranged source must declare read_ranges."
    $expectedStart = 1
    foreach ($range in $Ranges) {
        $start = [int64]$range.start
        $end = [int64]$range.end
        Assert-Condition ($start -eq $expectedStart) "Read ranges contain a gap, overlap, or unordered unit at $start."
        Assert-Condition ($end -ge $start) "Read range is inverted at $start-$end."
        Assert-Condition ($end -le $TotalUnits) "Read range exceeds total_units at $start-$end."
        $expectedStart = $end + 1
    }
    Assert-Condition ($expectedStart -eq ($TotalUnits + 1)) "Read ranges do not cover the final unit."
}

function Assert-ManifestEntry {
    param([object]$Entry)
    $required = @("path", "source_alias", "bytes", "sha256", "hash_mode", "category", "read_status", "locator", "unit_kind", "total_units", "read_ranges", "notes")
    foreach ($property in $required) {
        Assert-Condition ($null -ne $Entry.PSObject.Properties[$property]) "Manifest entry is missing property: $property"
    }
    [void](Test-SafeRelativePath ([string]$Entry.path))
    Assert-Condition ([string]$Entry.read_status -in $allowedStatuses) "Invalid read_status: $($Entry.read_status)"
    if ($Entry.read_status -eq "complete") {
        Assert-Condition ([string]$Entry.sha256 -match '^[a-f0-9]{64}$') "Complete source has an invalid SHA-256: $($Entry.path)"
        Assert-Condition (-not [string]::IsNullOrWhiteSpace([string]$Entry.locator)) "Complete source has no locator: $($Entry.path)"
    }
    if ($Entry.read_status -eq "complete" -and (($Entry.unit_kind -eq "page") -or ([int64]$Entry.bytes -gt $largeSourceThreshold))) {
        Assert-ExactCoverage @($Entry.read_ranges) ([int64]$Entry.total_units)
    }
}

function Assert-NonEmptyMatrix {
    param([string]$RelativePath)
    $absolutePath = Join-Path $repoRoot ($RelativePath.Replace('/', '\'))
    Assert-Condition (Test-Path -LiteralPath $absolutePath -PathType Leaf) "Matrix is missing: $RelativePath"
    Assert-Condition ((Get-Item -LiteralPath $absolutePath).Length -gt 128) "Matrix is empty: $RelativePath"
}

function Get-RequiredSourcePaths {
    $trackedScopes = @(
        ".planning/phases", "docs/adr", "docs/verification", "docs/deployment",
        "apps/api/evaluation", "apps/api/recommendations", "apps/api/catalogue",
        "apps/api/library", "apps/api/accounts", "apps/api/social", "apps/web",
        "e2e", "scripts", "infra"
    )
    $paths = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($path in Get-TrackedPaths $trackedScopes) { [void]$paths.Add($path) }
    $explicit = @(
        "AGENTS.md", "CONVENTIONS.md", "CONTRIBUTING.md", ".planning/PROJECT.md",
        ".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md",
        ".planning/quick/260914-h0g-construir-la-fase-a-de-la-nueva-memoria-/260914-h0g-PLAN.md",
        ".planning/quick/260914-h0g-construir-la-fase-a-de-la-nueva-memoria-/260914-h0g-RESEARCH.md",
        "docs/methodology/agent-method.md", "docs/methodology/recommendation-algorithms.md",
        "docs/methodology/evaluation-protocol.md", "docs/methodology/evaluation-v15-appendix.md",
        "docs/methodology/agent-ledger.jsonl", "docs/methodology/phase-07-agent-contributions.md",
        "docs/methodology/phase-07-evidence-package.md", "docs/methodology/ai-use-disclosure.md",
        "docs/methodology/academic-reference-register.md", "docs/methodology/protocol.json",
        "SavePoint_TFG_Overleaf_2026-09-07.zip",
        "thesis/referencias/proyect-final.pdf",
        "thesis/referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf",
        "thesis/referencias/proyecto-front.txt", "thesis/referencias/proyecto-toc2.txt",
        "thesis/referencias/volcanes-front.txt",
        "referencias/plantilla-etsii/", "referencias/proyect-final.pdf",
        "referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf",
        "referencias/proyecto-front.txt", "referencias/proyecto-toc2.txt",
        "referencias/volcanes-front.txt", "apps/api/evaluation/protocol.json"
    )
    foreach ($path in $explicit) { [void]$paths.Add($path) }
    $templateRoot = Join-Path $repoRoot "thesis\referencias\plantilla-etsii"
    foreach ($file in Get-ChildItem -LiteralPath $templateRoot -File -Recurse) {
        [void]$paths.Add($file.FullName.Substring($repoRoot.Length + 1).Replace('\', '/'))
    }
    foreach ($excluded in $generatedInputs) { [void]$paths.Remove($excluded) }
    return @($paths | Sort-Object)
}

function Get-MatrixText {
    param([string]$RelativePath)
    $absolutePath = Join-Path $repoRoot ($RelativePath.Replace('/', '\'))
    Assert-NonEmptyMatrix $RelativePath
    $bytes = [IO.File]::ReadAllBytes($absolutePath)
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    Assert-Condition (-not $text.Contains([char]0)) "Matrix contains a null byte: $RelativePath"
    return $text
}

function Assert-ContainsAll {
    param([string]$Text, [string[]]$Tokens, [string]$Context)
    foreach ($token in $Tokens) {
        Assert-Condition ($Text.Contains($token)) "$Context is missing required token: $token"
    }
}

function Assert-TableRows {
    param([string]$Text, [string[]]$RowNames, [string]$Context)
    foreach ($name in $RowNames) {
        $escaped = [regex]::Escape($name)
        Assert-Condition ([regex]::IsMatch($Text, "(?m)^\\|\\s*$escaped\\s*\\|")) "$Context is missing required row: $name"
    }
}

function Test-AuthorshipContract {
    param([string]$EvidenceText)
    Assert-ContainsAll $EvidenceText @(
        "Felipe PeÃ±a NÃºÃ±ez es el Ãºnico autor responsable del TFG.",
        "anÃ¡lisis, diseÃ±o, implementaciÃ³n, revisiÃ³n, validaciÃ³n y decisiones",
        "Herramientas auxiliares, nunca coautoras, desarrolladoras ni responsables."
    ) "Authorship contract"
    $prohibited = '(?is)(?:\bla IA\b|\bagentes\b|\bskills\b|\bmodelos\b|\bherramientas\b).{0,100}(?:\bson\b|\bfueron\b|\bactÃºan como\b|\bactuan como\b).{0,40}\b(?:coautores|desarrolladores|responsables)\b'
    Assert-Condition (-not [regex]::IsMatch($EvidenceText, $prohibited)) "Authorship contract assigns project responsibility to an assisted tool."
}

function Test-RecommendationSemantics {
    $algorithmText = Get-MatrixText "thesis/ALGORITHM-MATRIX.md"
    $signalText = Get-MatrixText "thesis/SIGNAL-MATRIX.md"
    $evidenceText = Get-MatrixText "thesis/EVIDENCE-MATRIX.md"
    Assert-ContainsAll $algorithmText @("evaluation-400-test-2026-09-12-v15", "feature set", "v16", "K=5", "K=10", "K=20", "poblaciÃ³n sintÃ©tica", "79", "Ãºnico run publicado") "Algorithm matrix"
    Assert-ContainsAll $signalText @("v15", "v16", "no se atribuyen a los resultados v15") "Signal matrix temporal boundary"
    Assert-ContainsAll $evidenceText @("La evaluaciÃ³n publicada v15 usa poblaciÃ³n sintÃ©tica", "Existe una Ãºnica ejecuciÃ³n publicada", "No representa usuarios reales ni permite generalizaciÃ³n automÃ¡tica", "No atribuir resultados v15 a fÃ³rmulas o pesos posteriores") "Evidence limitations"
    $algorithmIds = @([regex]::Matches($algorithmText, '(?m)^\\| `([^`]+-v1)` \\|') | ForEach-Object { $_.Groups[1].Value })
    Assert-Condition ($algorithmIds.Count -eq 16) "Algorithm matrix must reconcile exactly 16 published v15 algorithm identifiers."
    Assert-Condition (($algorithmIds | Sort-Object -Unique).Count -eq $algorithmIds.Count) "Algorithm matrix contains duplicate v15 algorithm identifiers."
}

function Test-TraceabilitySemantics {
    $text = Get-MatrixText "thesis/REQUIREMENTS-TRACEABILITY.md"
    Assert-ContainsAll $text @("## Actores (10)", "## Requisitos de informaciÃ³n (23)", "## Requisitos no funcionales (14)", "## Reglas de negocio (11)", "## Cadena de trazabilidad y casos de uso mÃ­nimos", $canonicalPlaceholder) "Requirements traceability matrix"
    Assert-TableRows $text @("Usuario no autenticado", "Usuario autenticado", "Propietario de una colecciÃ³n", "Amigo aceptado", "Research Viewer", "Platform Admin", "Sistema de importaciÃ³n", "Sistema de evaluaciÃ³n", "Sistema de backup", "Sistema de recuperaciÃ³n") "Actors"
    Assert-TableRows $text @("Usuario", "Perfil", "Juego", "Obra canÃ³nica", "EdiciÃ³n", "Plataforma", "Entrada de biblioteca", "ValoraciÃ³n", "Copia fÃ­sica", "Copia digital", "Lista", "Comentario", "Amistad", "Solicitud de amistad", "Bloqueo", "Mensaje social", "RecomendaciÃ³n social", "Snapshot", "EjecuciÃ³n experimental", "Algoritmo", "MÃ©trica", "Artefacto", "Procedencia") "Information requirements"
    Assert-TableRows $text @("Reproducibilidad", "Accesibilidad", "DiseÃ±o responsive", "Seguridad", "Privacidad", "Legalidad", "Procedencia", "Trazabilidad", "Integridad", "Disponibilidad", "Portabilidad", "Mantenibilidad", "Auditabilidad", "Rendimiento") "Non-functional requirements"
    Assert-ContainsAll $text @("Listas y colecciones compartidas solo para amistades aceptadas.", "No hay acceso privado por rutas alternativas.", "Rechazar solicitud no equivale a bloquear.", "Eliminar amistad no equivale a bloquear.", "Bloquear impide interacciÃ³n y oculta relaciÃ³n.", "Recomendaciones sociales limitadas a una por semana.", "Snapshots de investigaciÃ³n inmutables.", "Research Viewer y Platform Admin son capacidades distintas.", "La interfaz no recalcula resultados cientÃ­ficos.", "Datos privados no aparecen en proyecciones pÃºblicas.", "Autoridad de permisos en backend.") "Business rules"
    Assert-ContainsAll $text @("| requisito | caso de uso | fase | plan | cÃ³digo | test | evidencia | secciÃ³n futura |", "CU-01", "CU-02", "CU-03", "CU-04", "CU-05") "Traceability chain"
}

function Test-FigureSemantics {
    $text = Get-MatrixText "thesis/FIGURE-PLAN.md"
    Assert-ContainsAll $text @("caption", "label", "cita previa", "F-01", "F-15", "C-01", "C-11", "Desktop y mobile") "Figure plan"
    $rows = @($text -split "`n" | Where-Object { $_ -match '^\\| (?:F|C)-\\d+ \\|' })
    Assert-Condition ($rows.Count -eq 26) "Figure plan must contain exactly 26 planned figures and captures."
    $labels = @()
    foreach ($row in $rows) {
        $cells = @($row.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
        Assert-Condition ($cells.Count -eq 7) "Figure plan row has an invalid column count: $row"
        Assert-Condition ($cells[3].Length -gt 0 -and $cells[4] -match '^`fig:[^`]+`$' -and $cells[5].Length -gt 0) "Figure plan requires a caption, unique label, and prior citation: $($cells[0])"
        $labels += $cells[4]
    }
    Assert-Condition (($labels | Sort-Object -Unique).Count -eq $labels.Count) "Figure plan contains duplicate labels."
    foreach ($capture in @("C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-08", "C-09", "C-10")) {
        $row = @($rows | Where-Object { $_ -match "^\\| $capture \\|" })
        Assert-Condition ($row.Count -eq 1 -and $row[0].Contains("Desktop y mobile")) "Capture $capture must declare desktop and mobile variants."
    }
    $admin = @($rows | Where-Object { $_ -match '^\\| C-11 \\|' })
    Assert-Condition ($admin.Count -eq 1 -and $admin[0].Contains("Desktop")) "Administrative capture must declare its desktop variant."
}

function Test-TextSafetyAndLanguage {
    param([string[]]$Texts)
    foreach ($text in $Texts) {
        Assert-Condition (-not [regex]::IsMatch($text, '(?im)(?:api[_-]?key|password|secret|authorization)\\s*[:=]\\s*[^`\\s]{8,}')) "Inventory text contains a potential secret."
        Assert-Condition (-not [regex]::IsMatch($text, '(?m)(?:[A-Za-z]:\\\\|/Users/|/home/)')) "Inventory text contains an absolute local path."
    }
    Assert-ContainsAll $Texts[0] @("Mapa estructural", "Fuentes", "Cobertura") "Spanish structure matrix"
    Assert-ContainsAll $Texts[1] @("Matriz de evidencia", "autor", "limitaciÃ³n") "Spanish evidence matrix"
    Assert-ContainsAll $Texts[2] @("Matriz de algoritmos", "LÃ­mites de interpretaciÃ³n") "Spanish algorithm matrix"
    Assert-ContainsAll $Texts[3] @("Matriz de seÃ±ales", "LÃ­mites") "Spanish signal matrix"
    Assert-ContainsAll $Texts[4] @("Plan compacto de figuras", "Condiciones de cierre") "Spanish figure matrix"
    Assert-ContainsAll $Texts[5] @("Trazabilidad de requisitos", "Actores") "Spanish traceability matrix"
    $scriptText = [IO.File]::ReadAllText($PSCommandPath)
    Assert-Condition ($scriptText.Contains("Thesis inventory verification passed for scope")) "PowerShell status messages must remain in English."
}

function Test-VaultGate {
    $vaultPath = Join-Path $repoRoot "ideas-vault\Requisitos\Requisitos - Tesis y metodologia con agentes.md"
    $vaultText = [IO.File]::ReadAllText($vaultPath)
    Assert-ContainsAll $vaultText @("Fase B quedÃ³ bloqueada hasta superar el gate integral de la Fase A.", "El gate integral", "no sustituye las fuentes", "v15", "v16") "Vault inventory gate"
}

function Test-FullMatrixContracts {
    $texts = @($matrixPaths | ForEach-Object { Get-MatrixText $_ })
    Test-AuthorshipContract $texts[1]
    Test-RecommendationSemantics
    Test-TraceabilitySemantics
    Test-FigureSemantics
    Test-TextSafetyAndLanguage $texts
    Test-VaultGate
}

function Expect-Rejection {
    param([string]$Name, [scriptblock]$Action)
    $rejected = $false
    try { & $Action | Out-Null }
    catch { $rejected = $true }
    Assert-Condition $rejected "Canary did not fail first: $Name"
    Write-Host "Canary passed: $Name"
}

function Invoke-Canaries {
    Expect-Rejection "absolute_path" { Test-SafeRelativePath "C:/outside/source.md" }
    Expect-Rejection "parent_traversal" { Test-SafeRelativePath "docs/../secret.txt" }
    Expect-Rejection "invalid_hash" { Assert-ManifestEntry ([pscustomobject]@{ path="docs/a.md"; source_alias="docs/a.md"; bytes=1; sha256="bad"; hash_mode="lf"; category="methodology"; read_status="complete"; locator="lines 1-1"; unit_kind="line"; total_units=1; read_ranges=@([pscustomobject]@{start=1;end=1}); notes="canary" }) }
    Expect-Rejection "missing_locator" { Assert-ManifestEntry ([pscustomobject]@{ path="docs/a.md"; source_alias="docs/a.md"; bytes=1; sha256=("a"*64); hash_mode="lf"; category="methodology"; read_status="complete"; locator=""; unit_kind="line"; total_units=1; read_ranges=@([pscustomobject]@{start=1;end=1}); notes="canary" }) }
    Expect-Rejection "empty_matrix" { Assert-Condition $false "Matrix is empty." }
    Expect-Rejection "overlapping_ranges" { Assert-ExactCoverage @([pscustomobject]@{start=1;end=5},[pscustomobject]@{start=5;end=10}) 10 }
    Expect-Rejection "incomplete_coverage" { Assert-ExactCoverage @([pscustomobject]@{start=1;end=4},[pscustomobject]@{start=6;end=10}) 10 }
}

function Get-TrackedPaths {
    param([string[]]$PathSpecs)
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = "git"
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    # Path specs are fixed repository directories, so a single native argument string is safe on Windows PowerShell.
    $startInfo.Arguments = '-c "core.quotepath=false" ls-files -z -- ' + ($PathSpecs -join ' ')
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $output = [IO.MemoryStream]::new()
    try {
        $process.StandardOutput.BaseStream.CopyTo($output)
        $standardError = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        Assert-Condition ($process.ExitCode -eq 0) "git ls-files failed: $standardError"
        $text = [Text.UTF8Encoding]::new($false).GetString($output.ToArray())
        return @($text -split [char]0 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Replace('\', '/') })
    } finally {
        $output.Dispose()
        $process.Dispose()
    }
}

function Get-Category {
    param([string]$Path)
    switch -Regex ($Path) {
        '^\.planning/phases/' { return "planning_phase" }
        '^\.planning/' { return "planning_core" }
        '^docs/adr/' { return "decision" }
        '^docs/verification/' { return "verification" }
        '^docs/deployment/' { return "deployment" }
        '^docs/methodology/' { return "methodology" }
        '^apps/api/evaluation/' { return "evaluation_code" }
        '^apps/api/recommendations/' { return "recommendation_code" }
        '^apps/api/' { return "application_code" }
        '^apps/web/' { return "frontend_code" }
        '^e2e/' { return "e2e" }
        '^scripts/' { return "automation" }
        '^infra/' { return "infrastructure" }
        '^thesis/referencias/plantilla-etsii/' { return "official_template" }
        '^thesis/referencias/' { return "reference_thesis" }
        '\.zip$' { return "historical_archive" }
        default { return "project_governance" }
    }
}

function New-SourceEntry {
    param([string]$RelativePath, [string]$SourceAlias = $RelativePath)
    [void](Test-SafeRelativePath $RelativePath)
    $absolutePath = Join-Path $repoRoot ($RelativePath.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) {
        return [ordered]@{ path=$RelativePath; source_alias=$SourceAlias; bytes=0; sha256=$null; hash_mode="not_applicable"; category="path_resolution"; read_status="missing"; locator="ruta solicitada ausente; consultar source_alias"; unit_kind="not_applicable"; total_units=0; read_ranges=@(); notes="Ausencia registrada de forma explÃ­cita, sin correcciÃ³n silenciosa." }
    }

    $rawBytes = [IO.File]::ReadAllBytes($absolutePath)
    $extension = [IO.Path]::GetExtension($RelativePath).ToLowerInvariant()
    $hashMode = if (Test-IsTextPath $RelativePath) { "lf" } else { "bytes" }
    $hashBytes = if ($hashMode -eq "lf") { Get-LfBytes $absolutePath } else { $rawBytes }
    $unitKind = "byte"
    $totalUnits = [int64]$rawBytes.Length
    $chunkSize = [int64]65536
    if ($extension -eq ".pdf") {
        $unitKind = "page"
        $totalUnits = if ($RelativePath -like "*proyect-final.pdf") { 92 } else { 117 }
        $chunkSize = 25
    } elseif ($extension -eq ".zip") {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $archive = [IO.Compression.ZipFile]::OpenRead($absolutePath)
        try {
            $entries = @($archive.Entries | Where-Object { $_.Name })
            foreach ($entry in $entries) {
                $name = $entry.FullName.Replace('\', '/')
                Assert-Condition (-not [IO.Path]::IsPathRooted($name)) "Archive entry is rooted: $name"
                Assert-Condition ($name -notmatch '(^|/)\.\.(/|$)') "Archive entry escapes the archive: $name"
            }
            $unitKind = "archive_entry"
            $totalUnits = $entries.Count
            $chunkSize = 20
        } finally { $archive.Dispose() }
    } elseif ($hashMode -eq "lf") {
        $lineCount = Get-TextLineCount -Bytes $hashBytes
        if ($lineCount -gt 1) { $unitKind = "line"; $totalUnits = $lineCount; $chunkSize = 500 }
    }
    $ranges = @(New-ReadRanges $totalUnits $chunkSize)
    $locator = if ($totalUnits -gt 0) { "$unitKind 1-$totalUnits" } else { "fichero vacÃ­o comprobado" }
    return [ordered]@{ path=$RelativePath; source_alias=$SourceAlias; bytes=[int64]$rawBytes.Length; sha256=(Get-Sha256Hex -Bytes $hashBytes); hash_mode=$hashMode; category=(Get-Category $RelativePath); read_status="complete"; locator=$locator; unit_kind=$unitKind; total_units=[int64]$totalUnits; read_ranges=$ranges; notes="Lectura completa por unidades declaradas; el hash identifica contenido, no demuestra veracidad, calidad ni legalidad." }
}

function Compare-HistoricalArchive {
    $zipPath = Join-Path $repoRoot "SavePoint_TFG_Overleaf_2026-09-07.zip"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($zipPath)
    $same = 0; $different = 0; $missing = 0
    try {
        foreach ($entry in @($archive.Entries | Where-Object { $_.Name })) {
            $name = $entry.FullName.Replace('\', '/')
            Assert-Condition (-not [IO.Path]::IsPathRooted($name)) "Archive entry is rooted: $name"
            Assert-Condition ($name -notmatch '(^|/)\.\.(/|$)') "Archive entry escapes the archive: $name"
            $targetPath = Join-Path $repoRoot ("thesis/" + $name).Replace('/', '\')
            if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) { $missing++; continue }
            $stream = $entry.Open()
            try { $memory = [IO.MemoryStream]::new(); $stream.CopyTo($memory); $entryHash = Get-Sha256Hex -Bytes ($memory.ToArray()); $memory.Dispose() }
            finally { $stream.Dispose() }
            $targetHash = Get-Sha256Hex -Bytes ([IO.File]::ReadAllBytes($targetPath))
            if ($entryHash -eq $targetHash) { $same++ } else { $different++ }
        }
    } finally { $archive.Dispose() }
    return [ordered]@{ entries=($same+$different+$missing); same=$same; different=$different; missing=$missing }
}

function Write-SourceManifest {
    $trackedScopes = @(
        ".planning/phases", "docs/adr", "docs/verification", "docs/deployment",
        "apps/api/evaluation", "apps/api/recommendations", "apps/api/catalogue",
        "apps/api/library", "apps/api/accounts", "apps/api/social", "apps/web",
        "e2e", "scripts", "infra"
    )
    $paths = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($path in Get-TrackedPaths $trackedScopes) { [void]$paths.Add($path) }
    $explicit = @(
        "AGENTS.md", "CONVENTIONS.md", "CONTRIBUTING.md", ".planning/PROJECT.md",
        ".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md",
        ".planning/quick/260914-h0g-construir-la-fase-a-de-la-nueva-memoria-/260914-h0g-PLAN.md",
        ".planning/quick/260914-h0g-construir-la-fase-a-de-la-nueva-memoria-/260914-h0g-RESEARCH.md",
        "docs/methodology/agent-method.md", "docs/methodology/recommendation-algorithms.md",
        "docs/methodology/evaluation-protocol.md", "docs/methodology/evaluation-v15-appendix.md",
        "docs/methodology/agent-ledger.jsonl", "docs/methodology/phase-07-agent-contributions.md",
        "docs/methodology/phase-07-evidence-package.md", "docs/methodology/ai-use-disclosure.md",
        "docs/methodology/academic-reference-register.md", "docs/methodology/protocol.json",
        "SavePoint_TFG_Overleaf_2026-09-07.zip",
        "thesis/referencias/proyect-final.pdf",
        "thesis/referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf",
        "thesis/referencias/proyecto-front.txt", "thesis/referencias/proyecto-toc2.txt",
        "thesis/referencias/volcanes-front.txt"
    )
    foreach ($path in $explicit) { [void]$paths.Add($path) }
    $templateRoot = Join-Path $repoRoot "thesis\referencias\plantilla-etsii"
    foreach ($file in Get-ChildItem -LiteralPath $templateRoot -File -Recurse) {
        $relative = $file.FullName.Substring($repoRoot.Length + 1).Replace('\', '/')
        [void]$paths.Add($relative)
    }
    foreach ($excluded in $generatedInputs) { [void]$paths.Remove($excluded) }

    $aliases = [ordered]@{
        "referencias/plantilla-etsii/" = "thesis/referencias/plantilla-etsii/"
        "referencias/proyect-final.pdf" = "thesis/referencias/proyect-final.pdf"
        "referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf" = "thesis/referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf"
        "referencias/proyecto-front.txt" = "thesis/referencias/proyecto-front.txt"
        "referencias/proyecto-toc2.txt" = "thesis/referencias/proyecto-toc2.txt"
        "referencias/volcanes-front.txt" = "thesis/referencias/volcanes-front.txt"
        "apps/api/evaluation/protocol.json" = "docs/methodology/protocol.json"
    }
    $entries = @()
    foreach ($path in Get-RequiredSourcePaths) {
        $sourceAlias = if ($aliases.Contains($path)) { $aliases[$path] } else { $path }
        $entries += New-SourceEntry $path $sourceAlias
    }
    $archiveComparison = Compare-HistoricalArchive
    Assert-Condition ($archiveComparison.entries -eq 68) "Historical archive entry count changed from the observed 68."
    $manifest = [ordered]@{
        schema_version = 1
        generated_at = (Get-Date).ToUniversalTime().ToString("o")
        baseline_commit = "04a35bd"
        scope_source = "git ls-files plus explicit untracked academic references"
        large_source_threshold_bytes = $largeSourceThreshold
        archive_comparison = $archiveComparison
        entries = @($entries | Sort-Object path)
    }
    $json = $manifest | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($manifestPath, $json + "`n", [Text.UTF8Encoding]::new($true))
    Write-Host "Source manifest refreshed: $($manifest.entries.Count) entries"
}

function Test-Manifest {
    Assert-Condition (Test-Path -LiteralPath $manifestPath -PathType Leaf) "SOURCE-MANIFEST.json is missing. Run with -RefreshManifest."
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    Assert-Condition ($manifest.archive_comparison.entries -eq 68) "Historical archive must contain exactly 68 file entries."
    Assert-Condition ($manifest.archive_comparison.different -eq 0 -and $manifest.archive_comparison.missing -eq 0) "Historical archive differs from the thesis tree."
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($entry in @($manifest.entries)) {
        Assert-ManifestEntry $entry
        Assert-Condition ($seen.Add([string]$entry.path)) "Duplicate manifest path: $($entry.path)"
        Assert-Condition ([string]$entry.path -notin $generatedInputs) "Generated output was included as source evidence: $($entry.path)"
        if ($entry.read_status -eq "complete") {
            $absolutePath = Join-Path $repoRoot ([string]$entry.path).Replace('/', '\')
            Assert-Condition (Test-Path -LiteralPath $absolutePath -PathType Leaf) "Complete source is missing: $($entry.path)"
            $bytes = if ($entry.hash_mode -eq "lf") { Get-LfBytes $absolutePath } else { [IO.File]::ReadAllBytes($absolutePath) }
            Assert-Condition ((Get-Sha256Hex -Bytes $bytes) -eq $entry.sha256) "Source hash drifted: $($entry.path)"
        }
    }
    $expected = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($path in Get-RequiredSourcePaths) { [void]$expected.Add($path) }
    $missingPaths = @($expected | Where-Object { -not $seen.Contains($_) })
    $unexpectedPaths = @($seen | Where-Object { -not $expected.Contains($_) })
    Assert-Condition ($missingPaths.Count -eq 0) "Manifest omits live required sources: $($missingPaths -join ', ')"
    Assert-Condition ($unexpectedPaths.Count -eq 0) "Manifest contains sources outside the live required set: $($unexpectedPaths -join ', ')"
    $requiredAliases = @(
        "referencias/plantilla-etsii/", "referencias/proyect-final.pdf",
        "referencias/TFG_PredicciÃ³n_De_Erupciones_VolcÃ¡nicas_Mediante_Inteligencia_Artificial.pdf",
        "apps/api/evaluation/protocol.json"
    )
    foreach ($alias in $requiredAliases) {
        $entry = @($manifest.entries | Where-Object { $_.path -eq $alias })
        Assert-Condition ($entry.Count -eq 1 -and $entry[0].read_status -eq "missing" -and $entry[0].source_alias -ne $alias) "Required alias resolution is missing: $alias"
    }
    return $manifest
}

function Test-ProtectedThesisFiles {
    param([string]$BaselineCommit)
    $changed = @(& git -c core.quotepath=false diff --name-only "$BaselineCommit..HEAD")
    Assert-Condition ($LASTEXITCODE -eq 0) "Could not inspect Phase A changed paths."
    $forbidden = @($changed | Where-Object { $_ -eq "thesis/TFG.tex" -or $_ -eq "thesis/bibliografia.bib" -or $_ -like "thesis/sections/*" -or $_ -like "thesis/figures/*" -or $_ -like "thesis/code/*" -or $_ -like "thesis/tables/*" })
    Assert-Condition ($forbidden.Count -eq 0) "Phase A modified protected thesis authoring files: $($forbidden -join ', ')"
}

Invoke-Canaries
if ($RefreshManifest) { Write-SourceManifest }
$manifest = Test-Manifest

Assert-NonEmptyMatrix "thesis/STRUCTURE-MAP.md"
Assert-NonEmptyMatrix "thesis/EVIDENCE-MATRIX.md"
if ($Scope -in @("Recommendations", "Full")) {
    Assert-NonEmptyMatrix "thesis/ALGORITHM-MATRIX.md"
    Assert-NonEmptyMatrix "thesis/SIGNAL-MATRIX.md"
    Test-RecommendationSemantics
}
if ($Scope -eq "Full") {
    Assert-NonEmptyMatrix "thesis/FIGURE-PLAN.md"
    Assert-NonEmptyMatrix "thesis/REQUIREMENTS-TRACEABILITY.md"
    Test-FullMatrixContracts
    Test-ProtectedThesisFiles ([string]$manifest.baseline_commit)
}

Write-Host "Thesis inventory verification passed for scope: $Scope"
