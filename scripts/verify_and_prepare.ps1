[CmdletBinding()]
param(
    [string]$RepoRoot = "$HOME\Documents\PyroGrove\pyrogrove-workflow-diagnostic",
    [switch]$InstallMissing,
    [string]$GitName = "",
    [string]$GitEmail = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$started = Get-Date
$results = [ordered]@{
    stage = "SATURDAY PREPARATION"
    started_at = $started.ToString("o")
    repo_root = $RepoRoot
    overall_status = "UNKNOWN"
    checks = [ordered]@{}
    blockers = @()
    warnings = @()
}

function Add-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Evidence
    )
    $results.checks[$Name] = [ordered]@{
        status = $Status
        evidence = $Evidence
    }
}

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3 -c "import sys; print(sys.executable)" | Out-Null
            return [ordered]@{ command = "py"; args = @("-3") }
        } catch {}
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            & python -c "import sys; print(sys.executable)" | Out-Null
            return [ordered]@{ command = "python"; args = @() }
        } catch {}
    }
    return $null
}

function Invoke-Python {
    param(
        [System.Collections.IDictionary]$PythonInfo,
        [string[]]$Arguments
    )
    & $PythonInfo.command @($PythonInfo.args) @Arguments
}

Write-Host ""
Write-Host "PyroGrove Saturday Preparation" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
Write-Host "No project-specific application logic will be created." -ForegroundColor Yellow
Write-Host ""

# 1. Required executables
$pythonInfo = Find-Python
if ($null -eq $pythonInfo) {
    Add-Check "python" "BLOCKED" "Neither 'py -3' nor 'python' is callable."
    $results.blockers += "Python 3 is not callable from PowerShell."
} else {
    $pyVersion = (Invoke-Python $pythonInfo @("--version") 2>&1 | Out-String).Trim()
    Add-Check "python" "PASS" "$pyVersion via $($pythonInfo.command) $($pythonInfo.args -join ' ')"
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = (git --version | Out-String).Trim()
    Add-Check "git" "PASS" $gitVersion
} else {
    Add-Check "git" "BLOCKED" "git is not callable."
    $results.blockers += "Git is not callable from PowerShell."
}

if (Get-Command code -ErrorAction SilentlyContinue) {
    $codeVersion = (code --version 2>&1 | Select-Object -First 1 | Out-String).Trim()
    Add-Check "vscode_cli" "PASS" $codeVersion
} else {
    Add-Check "vscode_cli" "WARNING" "'code' launcher is not on PATH."
    $results.warnings += "VS Code CLI launcher is unavailable. Open the repository manually in VS Code if the desktop app is installed."
}

if ($results.blockers.Count -gt 0) {
    $results["overall_status"] = "BLOCKED"
    $results["completed_at"] = (Get-Date).ToString("o")
    $fallback = Join-Path $HOME "pyrogrove-prep-blocked.json"
    $results | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $fallback
    Write-Host ""
    Write-Host "PREP BLOCKED" -ForegroundColor Red
    $results.blockers | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
    Write-Host "Evidence: $fallback"
    exit 2
}

# 2. Create repository and copy scaffold from the current pack.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$packRoot = Split-Path -Parent $scriptDir

New-Item -ItemType Directory -Force -Path $RepoRoot | Out-Null
$resolvedRepo = (Resolve-Path $RepoRoot).Path

Get-ChildItem -Force $packRoot | Where-Object {
    $_.Name -notin @("scripts")
} | ForEach-Object {
    Copy-Item -Force -Recurse $_.FullName $resolvedRepo
}
New-Item -ItemType Directory -Force -Path (Join-Path $resolvedRepo "scripts") | Out-Null
Copy-Item -Force $MyInvocation.MyCommand.Path (Join-Path $resolvedRepo "scripts\verify_and_prepare.ps1")

$requiredDirs = @(
    "src\pyrogrove_diagnostic",
    "tests",
    "data",
    "docs",
    "evidence\environment",
    "evidence\tests",
    "evidence\screenshots",
    "evidence\recording",
    "evidence\mulerun",
    "scripts"
)
foreach ($dir in $requiredDirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $resolvedRepo $dir) | Out-Null
}
Add-Check "repository_folder" "PASS" $resolvedRepo
Add-Check "evidence_folders" "PASS" "Required evidence directories exist."

# 3. Create isolated virtual environment.
$venvPath = Join-Path $resolvedRepo ".venv"
if (-not (Test-Path $venvPath)) {
    Invoke-Python $pythonInfo @("-m", "venv", $venvPath)
}
$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python was not created: $venvPython"
}
$venvVersion = (& $venvPython --version 2>&1 | Out-String).Trim()
Add-Check "virtual_environment" "PASS" "$venvVersion at $venvPath"

# 4. Verify/install free Python packages inside the venv.
$packages = @("pytest", "ruff", "streamlit", "pydantic")
$missing = @()
foreach ($pkg in $packages) {
    & $venvPython -m pip show $pkg *> $null
    if ($LASTEXITCODE -ne 0) {
        $missing += $pkg
    }
}

if ($missing.Count -gt 0 -and $InstallMissing) {
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
    & $venvPython -m pip install @missing
    if ($LASTEXITCODE -ne 0) { throw "Package installation failed: $($missing -join ', ')" }
}

foreach ($pkg in $packages) {
    & $venvPython -m pip show $pkg *> $null
    if ($LASTEXITCODE -eq 0) {
        $versionLine = (& $venvPython -m pip show $pkg | Where-Object { $_ -like "Version:*" } | Out-String).Trim()
        Add-Check $pkg "PASS" $versionLine
    } else {
        Add-Check $pkg "BLOCKED" "Missing from .venv. Re-run with -InstallMissing."
        $results.blockers += "$pkg is missing from the repository virtual environment."
    }
}

# 5. Verify the secrets boundary.
$gitignorePath = Join-Path $resolvedRepo ".gitignore"
$envExamplePath = Join-Path $resolvedRepo ".env.example"
$disclosurePath = Join-Path $resolvedRepo "docs\practice-build-disclosure.md"

if ((Test-Path $gitignorePath) -and (Test-Path $envExamplePath) -and (Test-Path $disclosurePath)) {
    Add-Check "secrets_boundary" "PASS" ".gitignore, .env.example, and disclosure are present."
} else {
    Add-Check "secrets_boundary" "BLOCKED" "One or more required boundary files are missing."
    $results.blockers += "Secrets/disclosure boundary files are incomplete."
}

# 6. Initialise local Git repository and create an initial scaffold commit.
$gitIdentityReady = $false
Push-Location $resolvedRepo
try {
    if (-not (Test-Path (Join-Path $resolvedRepo ".git"))) {
        git init -b main | Out-Null
    }
    Add-Check "git_repository" "PASS" (git rev-parse --show-toplevel)

    # Optional explicit local identity. Otherwise use existing Git configuration.
    if ($GitName -and $GitEmail) {
        git config user.name $GitName
        git config user.email $GitEmail
    }

    $configuredName = (git config user.name 2>$null | Out-String).Trim()
    $configuredEmail = (git config user.email 2>$null | Out-String).Trim()

    if (-not $configuredName -or -not $configuredEmail) {
        Add-Check "git_identity" "BLOCKED" "Git user.name or user.email is not configured."
        $results.blockers += "Git identity is missing. Re-run with -GitName and -GitEmail, or configure Git manually."
    } else {
        $gitIdentityReady = $true
        Add-Check "git_identity" "PASS" "$configuredName <$configuredEmail>"

        git add .
        $hasHead = $true
        git rev-parse --verify HEAD *> $null
        if ($LASTEXITCODE -ne 0) { $hasHead = $false }

        $staged = (git diff --cached --name-only | Out-String).Trim()
        if ($staged) {
            if ($hasHead) {
                git commit -m "chore: refresh pre-hackathon preparation scaffold" | Out-Null
            } else {
                git commit -m "chore: create pre-hackathon preparation baseline" | Out-Null
            }
        }
        Add-Check "baseline_commit" "PASS" "Preparation scaffold committed; evidence will be included before final tag."
        Add-Check "baseline_tag" "PASS" "Tag will be placed on the finalized preparation baseline."
    }
}
finally {
    Pop-Location
}

# 7. Record evidence after all folders exist.
$results["completed_at"] = (Get-Date).ToString("o")
if ($results.blockers.Count -gt 0) {
    $results["overall_status"] = "PARTIAL"
} else {
    $results["overall_status"] = "PASS"
}

$evidenceDir = Join-Path $resolvedRepo "evidence\environment"
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
$jsonPath = Join-Path $evidenceDir "prep-verification.json"
$txtPath = Join-Path $evidenceDir "prep-verification.txt"

$results | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $jsonPath

$summary = @()
$summary += "Stage: $($results.stage)"
$summary += "Overall status: $($results.overall_status)"
$summary += "Started: $($results.started_at)"
$summary += "Completed: $($results.completed_at)"
$summary += "Repository: $resolvedRepo"
$summary += ""
$summary += "Checks:"
foreach ($entry in $results.checks.GetEnumerator()) {
    $summary += "- $($entry.Key): $($entry.Value.status) - $($entry.Value.evidence)"
}
if ($results.blockers.Count -gt 0) {
    $summary += ""
    $summary += "Blockers:"
    $results.blockers | ForEach-Object { $summary += "- $_" }
}
if ($results.warnings.Count -gt 0) {
    $summary += ""
    $summary += "Warnings:"
    $results.warnings | ForEach-Object { $summary += "- $_" }
}

$summary | Set-Content -Encoding UTF8 $txtPath

# 8. Finalize the preparation baseline so evidence is included and the worktree is clean.
$finalCommit = ""
$finalTagProof = ""
if ($gitIdentityReady -and $results.blockers.Count -eq 0) {
    Push-Location $resolvedRepo
    try {
        git add .
        $staged = (git diff --cached --name-only | Out-String).Trim()
        if ($staged) {
            git commit --amend --no-edit | Out-Null
        }

        if (git tag --list "pre-hackathon-baseline") {
            git tag -d "pre-hackathon-baseline" | Out-Null
        }
        git tag -a "pre-hackathon-baseline" -m "Practice baseline before project-specific Saturday implementation"

        $finalCommit = (git rev-parse --short HEAD | Out-String).Trim()
        $finalTagProof = (git show-ref --tags "pre-hackathon-baseline" | Out-String).Trim()

        $gitStatus = (git status --short | Out-String).Trim()
        if ($gitStatus) {
            throw "Working tree is not clean after baseline finalization: $gitStatus"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
if ($results.overall_status -eq "PASS") {
    Write-Host "START PREP: PASS" -ForegroundColor Green
} else {
    Write-Host "START PREP: PARTIAL" -ForegroundColor Yellow
}
Write-Host "Repository: $resolvedRepo"
Write-Host "Evidence: $jsonPath"
if ($finalCommit) {
    Write-Host "Baseline commit: $finalCommit"
    Write-Host "Baseline tag: pre-hackathon-baseline"
}
Write-Host ""
Write-Host "Do not implement application logic until Chee issues START PRACTICE BUILD." -ForegroundColor Yellow

exit $(if ($results.overall_status -eq "PASS") { 0 } else { 1 })
