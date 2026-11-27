# Install agentic-spec-kit into an initialised Spec Kit project.
# Usage: scripts\install.ps1 -Project <dir> -Profile <lite|standard|regulated> [-Pack hipaa]
param(
  [Parameter(Mandatory = $true)][string]$Project,
  [Parameter(Mandatory = $true)][ValidateSet("lite", "standard", "regulated")][string]$Profile,
  [string]$Pack = ""
)
$ErrorActionPreference = "Stop"
$kit = Split-Path -Parent $PSScriptRoot
Set-Location $Project
if (-not (Test-Path ".specify")) { throw "Run 'specify init' in $Project first." }
function Invoke-Specify { specify @args; if ($LASTEXITCODE -ne 0) { throw "specify $args failed" } }
Invoke-Specify extension add --dev "$kit\extensions\agentic" --force
if ($Pack) { Invoke-Specify extension add --dev "$kit\extensions\agentic-$Pack" --force }
if ($Profile -ne "lite") {
    Invoke-Specify extension add --dev "$kit\extensions\agentic-system" --force
    Invoke-Specify extension add --dev "$kit\extensions\agentic-quality" --force
    Invoke-Specify extension add --dev "$kit\extensions\agentic-product" --force
    Invoke-Specify extension add --dev "$kit\extensions\agentic-connect" --force
}
Invoke-Specify extension add --dev "$kit\extensions\agentic-team" --force
Invoke-Specify preset add --dev "$kit\presets\agentic-$Profile"
Invoke-Specify workflow step add agentic-gate --dev "$kit\steps\agentic-gate" --force
foreach ($wf in "agentic-sdd", "agentic-sdd-team", "agentic-sdd-sequential") { Invoke-Specify workflow add --dev "$kit\workflows\$wf" }
# Python compiles the kit's code where it runs. Those files are per machine and do not belong in the repository (LIV-9).
if (-not (Test-Path ".specify\extensions\.gitignore")) {
    $ignore = Join-Path (Get-Location).Path ".specify\extensions\.gitignore"
    [System.IO.File]::WriteAllText($ignore, "# Python compiles the kit's code where it runs. The compiled files are per machine and are not kept.`n__pycache__/`n")
}
$packArg = if ($Pack) { " --pack $Pack" } else { "" }
Write-Host ""
Write-Host "Installed. Next:"
Write-Host "  python .specify\extensions\agentic\scripts\agentic.py init --profile $Profile --repository <owner/name>$packArg"
Write-Host "  python .specify\extensions\agentic\scripts\agentic.py team init --runtimes <claude,copilot,sequential>"
Write-Host "  python .specify\extensions\agentic\scripts\agentic.py doctor"
if (-not (Test-Path ".specify\init-options.json")) {  # LIV-10
    Write-Host ""
    Write-Host "Note: Spec Kit was never set up in this project (there is no .specify\init-options.json)."
    Write-Host "  The kit's code is installed and its checks run. No coding agent has the kit's commands,"
    Write-Host "  and CK-UPSTREAM-PIN cannot run, until 'specify init' has run here."
}
