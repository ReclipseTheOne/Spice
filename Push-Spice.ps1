#Requires -Version 5.1
<#
.SYNOPSIS
    Safe, ordered git push for the Spice superproject and its submodules.

.DESCRIPTION
    The Spice repo records the exact commit hash of each submodule (spice-lsp,
    spice-vscode). If you push the superproject while a submodule commit only
    exists locally, the superproject ends up pointing at a commit nobody else
    can fetch. This wrapper enforces the correct order:

        0. (Interactive, no -Message) Offer a version bump: sync the version
           across spice-lang (spicy), spice-lsp (+ its spicy>= floor) and
           spice-vscode, build a "vX.Y.Z - <changelog>" commit message, copy it
           to the clipboard, and let you override it with a custom message.
        1. For each submodule: show diff -> commit (optional) -> push.
        2. Stage the updated submodule pointers in the main repo.
        3. Refuse to continue if any staged pointer references an unpushed
           submodule commit.
        4. Commit and push the main repo (incl. the tracked spice-lang/ dir).

    Every commit and push is previewed (status + diff) and confirmed first.

.PARAMETER Message
    Commit message reused for every repo that needs a commit. Providing it skips
    the interactive version-bump step. If omitted (and not -Yes) you're offered a
    version bump first, otherwise prompted per repo.

.PARAMETER Yes
    Auto-confirm every prompt (diffs are still printed). Non-interactive.

.PARAMETER DryRun
    Show exactly what would run; perform no commits or pushes.

.PARAMETER SkipFetch
    Don't fetch remotes before computing ahead/behind.

.PARAMETER SubmodulesOnly
    Process the submodules but leave the main repo untouched.

.EXAMPLE
    ./Push-Spice.ps1
    # Interactive: offers a version bump, then walks submodules and main.

.EXAMPLE
    ./Push-Spice.ps1 -Message "Annotations + LSP/VSC sync"
    # Skips the bump; uses this message for every repo.

.EXAMPLE
    ./Push-Spice.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [string]$Message,
    [switch]$Yes,
    [switch]$DryRun,
    [switch]$SkipFetch,
    [switch]$SubmodulesOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = $PSScriptRoot

# ---------- output helpers ----------
function Write-Head([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Write-Info([string]$t) { Write-Host "  $t" -ForegroundColor Gray }
function Write-Ok([string]$t)   { Write-Host "  $t" -ForegroundColor Green }
function Write-Warn([string]$t) { Write-Host "  $t" -ForegroundColor Yellow }
function Write-Err([string]$t)  { Write-Host "  $t" -ForegroundColor Red }

# ---------- git helpers ----------
# Read-only: returns trimmed stdout, swallows failures (e.g. no upstream).
function GitOut {
    param([string]$Dir, [string[]]$GitArgs)
    $out = & git -C $Dir @GitArgs 2>$null
    if ($null -eq $out) { return '' }
    # Join with LF (Out-String would inject CRLF and leave stray \r after -split).
    return (($out -join "`n")).Trim()
}

# Mutating: previews under -DryRun, otherwise runs and throws on failure.
function GitRun {
    param([string]$Dir, [string[]]$GitArgs)
    $shown = $GitArgs | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }
    $pretty = "git -C `"$Dir`" $($shown -join ' ')"
    if ($DryRun) { Write-Info "[dry-run] $pretty"; return }
    Write-Info "> $pretty"
    & git -C $Dir @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $pretty" }
}

# Display-only (lets git's own coloring through).
function GitShow {
    param([string]$Dir, [string[]]$GitArgs)
    & git -C $Dir --no-pager @GitArgs
}

function Confirm-Step([string]$Question) {
    if ($DryRun) { Write-Info "(dry-run) would ask: $Question"; return $true }
    if ($Yes)    { Write-Info "(auto-yes) $Question"; return $true }
    $ans = Read-Host "  $Question [y/N]"
    return ($ans -match '^(y|yes)$')
}

function Get-CommitMessage([string]$Label) {
    if ($Message) { return $Message }
    if ($DryRun)  { return "<message entered interactively>" }
    $m = Read-Host "  Commit message for $Label"
    if ([string]::IsNullOrWhiteSpace($m)) { throw "Empty commit message; aborting." }
    return $m
}

# Returns @{ Upstream; Ahead; Behind } or $null when no upstream is configured.
function Get-AheadBehind([string]$Dir) {
    $u = GitOut $Dir @('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
    if (-not $u) { return $null }
    $counts = GitOut $Dir @('rev-list', '--left-right', '--count', '@{u}...HEAD')
    $parts = $counts -split '\s+'
    if ($parts.Count -lt 2) { return $null }
    return [pscustomobject]@{
        Upstream = $u
        Behind   = [int]$parts[0]
        Ahead    = [int]$parts[1]
    }
}

function Get-SubmodulePaths {
    $gm = Join-Path $RepoRoot '.gitmodules'
    if (-not (Test-Path $gm)) { return @() }
    $lines = GitOut $RepoRoot @('config', '--file', '.gitmodules', '--get-regexp', 'path')
    if (-not $lines) { return @() }
    return @($lines -split "`n" | ForEach-Object { (($_.Trim()) -split '\s+')[-1] } | Where-Object { $_ })
}

# ---------- version bump ----------
# spice-lang/pyproject.toml is the source of truth for the language version.
$VersionFiles = @{
    Lang = Join-Path $RepoRoot 'spice-lang/pyproject.toml'   # spicy
    Lsp  = Join-Path $RepoRoot 'spice-lsp/pyproject.toml'    # spice-lsp (+ spicy>= floor)
    Vsc  = Join-Path $RepoRoot 'spice-vscode/package.json'   # extension
}

function Get-CurrentVersion {
    if (-not (Test-Path $VersionFiles.Lang)) { return $null }
    $content = Get-Content -Raw -LiteralPath $VersionFiles.Lang
    $m = [regex]::Match($content, '(?m)^\s*version\s*=\s*"([^"]+)"')
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

# Replace the first /(group1)<version>(group2)/ match, preserving the rest of the file byte-for-byte.
function Set-VersionInFile {
    param([string]$Path, [string]$Pattern, [string]$Value)
    if (-not (Test-Path $Path)) { Write-Warn "version: missing $Path (skipped)"; return }
    $content = Get-Content -Raw -LiteralPath $Path
    $re = [regex]$Pattern
    if (-not $re.IsMatch($content)) { Write-Warn "version: no match in $(Split-Path -Leaf $Path) (skipped)"; return }
    # Single-quoted group refs so PowerShell doesn't expand $1/$2 as its own variables.
    $replacement = '${1}' + $Value + '${2}'
    [System.IO.File]::WriteAllText($Path, $re.Replace($content, $replacement, 1))
    Write-Info "set v$Value in $(Split-Path -Leaf $Path)"
}

function Set-AllVersions {
    param([string]$NewVersion)
    Set-VersionInFile $VersionFiles.Lang '(?m)^(\s*version\s*=\s*")[^"]+(")' $NewVersion
    Set-VersionInFile $VersionFiles.Lsp  '(?m)^(\s*version\s*=\s*")[^"]+(")' $NewVersion
    # Keep the LSP's spicy>= floor pinned to the language it imports.
    Set-VersionInFile $VersionFiles.Lsp  '("spicy>=)[^"]+(")' $NewVersion
    Set-VersionInFile $VersionFiles.Vsc  '("version"\s*:\s*")[^"]+(")' $NewVersion
}

function Set-ClipboardSafe([string]$Text) {
    try { Set-Clipboard -Value $Text; return $true }
    catch { Write-Warn "Couldn't copy to clipboard: $($_.Exception.Message)"; return $false }
}

# Runs first on interactive runs. Returns the commit message to reuse, or $null.
function Invoke-VersionBump {
    Write-Head "Version"
    $current = Get-CurrentVersion
    if ($current) { Write-Info "Current: v$current" }
    else { Write-Warn "Couldn't read current version from spice-lang/pyproject.toml." }

    if (-not (Confirm-Step "Bump version and sync spice-lang / spice-lsp / spice-vscode?")) {
        Write-Info "No version bump."
        return $null
    }

    $new = $null
    while (-not $new) {
        $entered = (Read-Host "  New version (X.Y.Z)").Trim()
        if ($entered -match '^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$') { $new = $entered }
        else { Write-Warn "Not a valid version: '$entered' (expected X.Y.Z). Ctrl+C to abort." }
    }

    $changelog = (Read-Host "  Quick changelog (one line)").Trim()

    if ($DryRun) {
        Write-Info "[dry-run] would sync spice-lang, spice-lsp (+ spicy floor) and spice-vscode to v$new"
    }
    else {
        Set-AllVersions -NewVersion $new
        Write-Ok "Synced all projects to v$new"
    }

    $default = if ($changelog) { "v$new - $changelog" } else { "v$new" }

    if ($DryRun) {
        Write-Info "[dry-run] default commit message (would copy to clipboard):"
    }
    elseif (Set-ClipboardSafe $default) {
        Write-Ok "Default commit message copied to clipboard:"
    }
    else {
        Write-Info "Default commit message:"
    }
    Write-Host "    $default" -ForegroundColor White

    $custom = (Read-Host "  Press Enter to use it, or type a custom message").Trim()
    if ($custom) {
        if (-not $DryRun) { Set-ClipboardSafe $custom | Out-Null }
        return $custom
    }
    return $default
}

# ---------- per-submodule flow ----------
function Invoke-Submodule {
    param([string]$Path)

    $dir = Join-Path $RepoRoot $Path
    Write-Head "Submodule: $Path"

    if (-not (Test-Path (Join-Path $dir '.git'))) {
        Write-Warn "Not initialized (no .git). Run 'git submodule update --init $Path'. Skipping."
        return
    }

    $branch = GitOut $dir @('rev-parse', '--abbrev-ref', 'HEAD')
    if ($branch -eq 'HEAD') {
        Write-Warn "Detached HEAD - can't push a branch. Check out a branch first. Skipping."
        return
    }
    Write-Info "branch: $branch"

    if (-not $SkipFetch) {
        Write-Info "fetching $Path ..."
        & git -C $dir fetch --quiet 2>$null
    }

    # 1) Commit working-tree changes, if any.
    $dirty = GitOut $dir @('status', '--porcelain')
    if ($dirty) {
        Write-Warn "Uncommitted changes:"
        GitShow $dir @('status', '--short')
        Write-Host ""
        GitShow $dir @('diff', '--stat')
        if (Confirm-Step "Commit these changes in $Path ?") {
            $msg = Get-CommitMessage $Path
            GitRun $dir @('add', '-A')
            GitRun $dir @('commit', '-m', $msg)
        }
        else {
            Write-Warn "Skipped committing $Path. Its working changes won't be published."
        }
    }
    else {
        Write-Ok "Working tree clean."
    }

    # 2) Push outstanding commits.
    $ab = Get-AheadBehind $dir
    if ($null -eq $ab) {
        Write-Warn "No upstream set for '$branch'; cannot push automatically."
        return
    }
    if ($ab.Behind -gt 0) {
        Write-Warn "Behind $($ab.Upstream) by $($ab.Behind) commit(s). Consider pulling/rebasing first."
    }
    if ($ab.Ahead -gt 0) {
        Write-Info "$($ab.Ahead) commit(s) to push -> $($ab.Upstream):"
        GitShow $dir @('log', '--oneline', '@{u}..HEAD')
        if (Confirm-Step "Push $Path to $($ab.Upstream) ?") {
            GitRun $dir @('push')
        }
        else {
            Write-Warn "Skipped pushing $Path."
        }
    }
    else {
        Write-Ok "Up to date with $($ab.Upstream)."
    }
}

# ---------- main-repo flow ----------
function Invoke-MainRepo {
    param([string[]]$SubPaths)

    Write-Head "Main repository"

    # Stage the (possibly bumped) submodule pointers. No-op if unchanged.
    foreach ($p in $SubPaths) {
        GitRun $RepoRoot @('add', '--', $p)
    }

    # Safety gate: never record a pointer to a commit that isn't on the remote.
    $stagedRaw = GitOut $RepoRoot @('diff', '--cached', '--name-only')
    $staged = @()
    if ($stagedRaw) { $staged = @($stagedRaw -split "`n") }

    foreach ($p in $SubPaths) {
        if ($staged -notcontains $p) { continue }
        $ab = Get-AheadBehind (Join-Path $RepoRoot $p)
        if ($null -ne $ab -and $ab.Ahead -gt 0) {
            Write-Err "Submodule '$p' has $($ab.Ahead) unpushed commit(s)."
            Write-Err "Refusing to commit a main pointer to a commit absent from $($ab.Upstream)."
            throw "Aborting: push submodule '$p' before the main repo."
        }
    }

    Write-Info "Status:"
    GitShow $RepoRoot @('status', '--short')

    # Offer to stage everything else (e.g. spice-lang/ changes).
    $unstaged = GitOut $RepoRoot @('status', '--porcelain')
    $hasUnstaged = $false
    if ($unstaged) {
        foreach ($line in ($unstaged -split "`n")) {
            # Column 2 (worktree) non-space => something not yet staged.
            if ($line.Length -ge 2 -and $line[1] -ne ' ') { $hasUnstaged = $true; break }
        }
    }
    if ($hasUnstaged) {
        if (Confirm-Step "Stage all remaining changes (git add -A) ?") {
            GitRun $RepoRoot @('add', '-A')
        }
    }

    # Anything staged to commit?
    & git -C $RepoRoot diff --cached --quiet
    $hasStaged = ($LASTEXITCODE -ne 0)
    if ($DryRun -and -not $hasStaged) {
        Write-Info "(dry-run) nothing currently staged; a real run may have staged more above."
    }

    if ($hasStaged -or $DryRun) {
        Write-Info "Staged diff:"
        GitShow $RepoRoot @('diff', '--cached', '--stat')
        if (Confirm-Step "Commit the main repo ?") {
            $msg = Get-CommitMessage 'main repo'
            GitRun $RepoRoot @('commit', '-m', $msg)
        }
        else {
            Write-Warn "Skipped main commit."
        }
    }
    else {
        Write-Ok "Nothing staged to commit."
    }

    # Push main.
    $ab = Get-AheadBehind $RepoRoot
    if ($null -eq $ab) {
        Write-Warn "Main repo has no upstream; not pushing."
        return
    }
    if ($ab.Behind -gt 0) {
        Write-Warn "Behind $($ab.Upstream) by $($ab.Behind) commit(s). Consider pulling/rebasing first."
    }
    if ($ab.Ahead -gt 0) {
        Write-Info "$($ab.Ahead) commit(s) to push -> $($ab.Upstream):"
        GitShow $RepoRoot @('log', '--oneline', '@{u}..HEAD')
        if (Confirm-Step "Push main repo to $($ab.Upstream) ?") {
            GitRun $RepoRoot @('push')
        }
        else {
            Write-Warn "Skipped pushing main repo."
        }
    }
    else {
        Write-Ok "Main repo up to date with $($ab.Upstream)."
    }
}

# ---------- main ----------
try {
    Push-Location $RepoRoot

    if ($DryRun) { Write-Host "DRY RUN - no commits or pushes will be made." -ForegroundColor Magenta }

    # Step 0: version bump (interactive only). -Message means the message is
    # already chosen; -Yes is non-interactive so there's nothing to type.
    if (-not $Message -and -not $Yes) {
        $bumpMessage = Invoke-VersionBump
        if ($bumpMessage) { $Message = $bumpMessage }
    }

    $subPaths = @(Get-SubmodulePaths)
    if ($subPaths.Count -eq 0) {
        Write-Warn "No submodules found in .gitmodules."
    }
    else {
        Write-Info "Submodules: $($subPaths -join ', ')"
        foreach ($p in $subPaths) { Invoke-Submodule -Path $p }
    }

    if ($SubmodulesOnly) {
        Write-Head "Done (submodules only)"
    }
    else {
        Invoke-MainRepo -SubPaths $subPaths
        Write-Head "Done"
    }
}
catch {
    Write-Host ""
    Write-Err $_.Exception.Message
    exit 1
}
finally {
    Pop-Location
}
