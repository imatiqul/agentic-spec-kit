# Install agentic-spec-kit (slice 0.1) into an initialised Spec Kit project.
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
Invoke-Specify preset add --dev "$kit\presets\agentic-$Profile"
Invoke-Specify workflow step add agentic-gate --dev "$kit\steps\agentic-gate" --force
Invoke-Specify workflow add --dev "$kit\workflows\agentic-sdd"
$packArg = if ($Pack) { " --pack $Pack" } else { "" }
Write-Host ""
Write-Host "Installed. Next:"
Write-Host "  python .specify\extensions\agentic\scripts\agentic.py init --profile $Profile --repository <owner/name>$packArg"
Write-Host "  python .specify\extensions\agentic\scripts\agentic.py doctor"
