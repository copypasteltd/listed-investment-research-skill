[CmdletBinding()]
param(
    [string]$CodexSkillsRoot = '',
    [string]$DshSkillsRoot = '',
    [switch]$SkipCodex,
    [switch]$SkipDsh
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'This helper creates Windows directory junctions; on other systems add this folder to the host skill directory.' }
$skillRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$entry = Join-Path $skillRoot 'SKILL.md'
if (-not (Test-Path -LiteralPath $entry -PathType Leaf)) { throw 'SKILL.md is missing.' }
$skillName = 'ai-investment-research'
if (-not $CodexSkillsRoot) {
    $codexBase = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
    $CodexSkillsRoot = Join-Path $codexBase 'skills'
}
if (-not $DshSkillsRoot) {
    if ($env:DSH_HOME) { $DshSkillsRoot = Join-Path $env:DSH_HOME 'skills' }
    elseif ($env:DSH_PROFILE_DIR) { $DshSkillsRoot = Join-Path (Split-Path (Split-Path $env:DSH_PROFILE_DIR -Parent) -Parent) 'skills' }
}
$targets = @()
if (-not $SkipCodex) { $targets += $CodexSkillsRoot }
if (-not $SkipDsh) {
    if (-not $DshSkillsRoot) { throw 'DSH root cannot be inferred; specify -DshSkillsRoot or -SkipDsh.' }
    $targets += $DshSkillsRoot
}
# Preflight every target before creating any link. Existing skills are never replaced.
foreach ($root in $targets) {
    $link = Join-Path $root $skillName
    $item = Get-Item -Force -LiteralPath $link -ErrorAction SilentlyContinue
    if ($item) {
        if ($item.LinkType -notin @('Junction', 'SymbolicLink')) { throw "Existing real directory/file, refusing to replace: $link" }
        $actual = [IO.Path]::GetFullPath((@($item.Target) | Select-Object -First 1)).TrimEnd('\')
        if ($actual -ne $skillRoot.TrimEnd('\')) { throw "Link points to another source: $link -> $actual" }
    }
}
$result = foreach ($root in $targets) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { New-Item -ItemType Directory -Path $root -Force | Out-Null }
    $link = Join-Path $root $skillName
    $state = 'already linked'
    if (-not (Get-Item -Force -LiteralPath $link -ErrorAction SilentlyContinue)) {
        New-Item -ItemType Junction -Path $link -Target $skillRoot | Out-Null
        $state = 'created'
    }
    $installed = Get-Item -Force -LiteralPath $link
    [pscustomobject]@{ name = $skillName; canonical = $skillRoot; loader = $link; state = $state; linkType = $installed.LinkType; readable = (Test-Path -LiteralPath (Join-Path $link 'SKILL.md') -PathType Leaf) }
}
$result | ConvertTo-Json -Depth 3
