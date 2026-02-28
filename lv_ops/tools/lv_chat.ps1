param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern("^[a-z0-9_-]+$")]
  [string]$Project,

  [switch]$AutoCommit,

  [string]$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
)

$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Read-Block([string]$Prompt, [ConsoleColor]$Color) {
  Write-Host $Prompt -ForegroundColor $Color
  Write-Host "End input with ::end (can be appended like 'text::end')." -ForegroundColor DarkGray

  $lines = New-Object System.Collections.Generic.List[string]

  while ($true) {
    $line = Read-Host
    if ($null -eq $line) { continue }

    $idx = $line.IndexOf("::end")
    if ($idx -ge 0) {
      $before = $line.Substring(0, $idx)
      if ($before.Trim().Length -gt 0) { $lines.Add($before) }
      break
    }

    $lines.Add($line)
  }

  return ($lines -join "`n").Trim()
}

function Extract-Block([string]$Text, [string]$StartMarker, [string]$EndMarker) {
  $pattern = "(?s)$([regex]::Escape($StartMarker))\s*(.*?)\s*$([regex]::Escape($EndMarker))"
  if ($Text -match $pattern) { return $Matches[1].Trim() }
  return $null
}

function Append-Events([string]$OpsRoot, [string]$ProjectName, [string]$Today, [string]$AssistantText) {
  $events = Extract-Block -Text $AssistantText -StartMarker "---opslog-events---" -EndMarker "---end-opslog-events---"
  if (-not $events) { return }

  $eventsRoot = Join-Path $OpsRoot "events"
  $projDir = Join-Path $eventsRoot $ProjectName
  Ensure-Dir $eventsRoot
  Ensure-Dir $projDir

  $eventsFile = Join-Path $projDir "$Today.md"

  if (!(Test-Path $eventsFile)) {
    "# opslog events: $ProjectName ($Today)`n" | Set-Content -Encoding UTF8 $eventsFile
  }

  "`n---`n$events`n" | Add-Content -Encoding UTF8 $eventsFile
  Write-Host "Appended opslog events to: $eventsFile" -ForegroundColor Yellow
}

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
  }
  else {
    Write-Host "No changes detected. Nothing committed." -ForegroundColor DarkGray
  }

  Pop-Location
}

# paths
$opsRoot = Join-Path $Root "lv_ops\ops"
$logsDir = Join-Path $opsRoot (Join-Path "logs" $Project)
Ensure-Dir $opsRoot
Ensure-Dir (Join-Path $opsRoot "logs")
Ensure-Dir $logsDir

$today = Get-Date -Format "yyyy-MM-dd"
$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

$logFile      = Join-Path $logsDir "$today.md"
$capsuleFile  = Join-Path $opsRoot "context-capsule.md"
$decisionFile = Join-Path $opsRoot "decision-log.md"

# seed
if (!(Test-Path $capsuleFile)) {
@"
# context-capsule
date: $today
timezone: america/new_york

## active-objective (one sentence)

## current-workstream
project: $Project
repo_path: $Root
branch:

## what we finished last

## current blockers / errors (verbatim)

## decisions locked today

## next actions (exact)
1)

## artifacts touched
- file:
"@ | Set-Content -Encoding UTF8 $capsuleFile
}

if (!(Test-Path $decisionFile)) { "# decision-log`n" | Set-Content -Encoding UTF8 $decisionFile }

# session header
"`n---`n# session $ts`n" | Add-Content -Encoding UTF8 $logFile

Write-Host ""
Write-Host "Project: $Project"
Write-Host "Log file: $logFile"
Write-Host "Capsule:  $capsuleFile"
Write-Host ""

# user
$userMsg = Read-Block -Prompt "Paste YOUR MESSAGE now." -Color Cyan
"`n## user`n" | Add-Content -Encoding UTF8 $logFile
$userMsg | Add-Content -Encoding UTF8 $logFile

# assistant
Write-Host ""
$asstMsg = Read-Block -Prompt "Paste ASSISTANT RESPONSE now." -Color Green
"`n## assistant`n" | Add-Content -Encoding UTF8 $logFile
$asstMsg | Add-Content -Encoding UTF8 $logFile

# update capsule/decisions from assistant markers (assistant is responsible for generating these)
$capsule = Extract-Block -Text $asstMsg -StartMarker "---context-capsule---" -EndMarker "---end-context-capsule---"
if ($capsule) {
  $capsule | Set-Content -Encoding UTF8 $capsuleFile
  Write-Host "`nUpdated capsule from assistant markers." -ForegroundColor Yellow
}

$dec = Extract-Block -Text $asstMsg -StartMarker "---decision-log---" -EndMarker "---end-decision-log---"
if ($dec) {
  "`n## $today`n$dec`n" | Add-Content -Encoding UTF8 $decisionFile
  Write-Host "Appended decisions to decision-log." -ForegroundColor Yellow
}

# append important events
Append-Events -OpsRoot $opsRoot -ProjectName $Project -Today $today -AssistantText $asstMsg

# git autocommit (lv_ops only)
if ($AutoCommit) {
  Git-AutoCommit -RootPath $Root -ProjectName $Project
}

Write-Host "`nDone." -ForegroundColor Green