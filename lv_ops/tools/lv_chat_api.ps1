param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern("^[a-z0-9_-]+$")]
  [string]$Project,

  [switch]$AutoCommit,

  [string]$Root = "C:\Users\greas\Documents\layered_ventures"
)

$ErrorActionPreference = "Stop"

function Git-AutoCommit([string]$RootPath, [string]$ProjectName) {
  if (!(Test-Path (Join-Path $RootPath ".git"))) {
    Write-Host "No git repo found at root. Skipping autocommit." -ForegroundColor DarkYellow
    return
  }

  Push-Location $RootPath
  git add lv_ops 2>$null

  $status = git status --porcelain
  if ($status) {
    $ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $msg = "opslog: $ProjectName session $ts"
    git commit -m $msg | Out-Null
    Write-Host "Autocommit created: $msg" -ForegroundColor Yellow
  } else {
    Write-Host "No changes detected. Nothing committed." -ForegroundColor DarkGray
  }
  Pop-Location
}

Write-Host ""
Write-Host "Project: $Project"
Write-Host "Root:    $Root"
Write-Host ""

Write-Host "Type your message. End with ::end on its own line." -ForegroundColor Cyan
$lines = New-Object System.Collections.Generic.List[string]
while ($true) {
  $line = Read-Host
  if ($line -eq "::end") { break }
  $lines.Add($line)
}
$prompt = ($lines -join "`n").Trim()
if (-not $prompt) { throw "Empty prompt." }

$py = Join-Path $PSScriptRoot "lv_chat_client.py"
if (!(Test-Path $py)) { throw "Missing client: $py" }

# call python client (no copy/paste of assistant response required)
$prompt | py $py $Root $Project

if ($AutoCommit) {
  Git-AutoCommit -RootPath $Root -ProjectName $Project
}

Write-Host "`nDone." -ForegroundColor Green
