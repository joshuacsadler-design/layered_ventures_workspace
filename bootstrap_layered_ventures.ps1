param(
  [string]$Root = "C:\Users\greas\Documents\layered_ventures",
  [switch]$InitGit
)

$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p) {
  if (!(Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Write-FileIfMissing([string]$path, [string]$content) {
  if (!(Test-Path $path)) {
    $dir = Split-Path $path -Parent
    Ensure-Dir $dir
    $content | Set-Content -Encoding UTF8 $path
  }
}

function Json-Pretty([string]$json) {
  try { return ($json | ConvertFrom-Json | ConvertTo-Json -Depth 20) }
  catch { return $json }
}

# ---- root folders ----
Ensure-Dir $Root
Ensure-Dir (Join-Path $Root "projects")
Ensure-Dir (Join-Path $Root "contracts")

# ---- migrate lv_ops -> ops (safe) ----
$oldLvOps = Join-Path $Root "lv_ops"
$newOps   = Join-Path $Root "ops"

if ((Test-Path $oldLvOps) -and !(Test-Path $newOps)) {
  Rename-Item -Path $oldLvOps -NewName "ops"
}

# if ops doesn't exist yet, create minimal ops structure
Ensure-Dir $newOps
Ensure-Dir (Join-Path $newOps "doctrine")
Ensure-Dir (Join-Path $newOps "tools")
Ensure-Dir (Join-Path $newOps "ops")
Ensure-Dir (Join-Path $newOps "ops\logs")
Ensure-Dir (Join-Path $newOps "ops\events")

# ---- seed ops core files (non-destructive) ----
$today = Get-Date -Format "yyyy-MM-dd"

Write-FileIfMissing (Join-Path $newOps "readme.md") @"
# ops (lv_ops)
This repo/folder is the Layered Ventures operational brain.

- doctrine/: global rules
- tools/: automation scripts
- ops/: capsule, decision log, logs/, events/
"@

Write-FileIfMissing (Join-Path $newOps "doctrine\naming.md") @"
# naming (global)

- linux-safe, cross-platform
- lowercase only
- no spaces
- allowed: a-z 0-9 hyphen (-) underscore (_)
- stable ids where relevant; do not rename casually
"@

Write-FileIfMissing (Join-Path $newOps "doctrine\workflow.md") @"
# workflow (global)

- automation-first
- premium output
- transparency (no false promises)

## code change workflow (non-negotiable)
1) full-file paste of every modified file
2) git commit + push command chain
3) verify/test each change before the next
4) minimal scope, deterministic outcomes
"@

Write-FileIfMissing (Join-Path $newOps "doctrine\lv-doctrine.md") @"
# lv-doctrine (source of truth)

## hierarchy
- lvcc: command center
- puremetalprints: fabrication + storefront
- layered-studios: production pipelines
- mechanick: diagnostic intelligence

## ops standard
- ops/ops/context-capsule.md is the carry-forward state
- ops/ops/decision-log.md is append-only
- ops/ops/logs/<project>/YYYY-MM-DD.md is raw transcript truth
- ops/ops/events/<project>/YYYY-MM-DD.md is extracted important events
"@

Write-FileIfMissing (Join-Path $newOps "ops\context-capsule.md") @"
# context-capsule
date: $today
timezone: america/new_york

## active-objective (one sentence)
Stand up LVCC (api+ui) reading ops artifacts, backed by projects registry.

## current-workstream
project: lvcc
repo_path: $Root
branch:

## what we finished last
- repo layout bootstrap

## current blockers / errors (verbatim)
- none

## decisions locked today
- each business is its own repo folder under projects/
- ops is separate and shared across all projects

## next actions (exact)
1) run lvcc api locally and confirm capsule/log listing works
2) wire future UIs to same ops endpoints/contract

## artifacts touched
- file: projects/projects-registry.json
- file: projects/lvcc/api/server.mjs
"@

Write-FileIfMissing (Join-Path $newOps "ops\decision-log.md") @"
# decision-log

## $today
- decision: each business lives as its own repo under projects/
  reason: scalability + sellability + isolation
  scope: global

- decision: ops is the shared operational brain (capsule/logs/events)
  reason: continuity + auditability
  scope: global
"@

# ---- projects registry (source for UI discovery) ----
$registryPath = Join-Path $Root "projects\projects-registry.json"
if (!(Test-Path $registryPath)) {
  $registry = @"
{
  "version": "1.0.0",
  "projects": [
    { "id": "lvcc", "path": "projects/lvcc", "type": "internal", "enabled": true },
    { "id": "puremetalprints", "path": "projects/puremetalprints", "type": "business", "enabled": true },
    { "id": "layered-studios", "path": "projects/layered-studios", "type": "internal", "enabled": true },
    { "id": "mechanick", "path": "projects/mechanick", "type": "business", "enabled": true }
  ]
}
"@
  (Json-Pretty $registry) | Set-Content -Encoding UTF8 $registryPath
}

# ---- ensure project folders exist ----
Ensure-Dir (Join-Path $Root "projects\lvcc\api")
Ensure-Dir (Join-Path $Root "projects\lvcc\ui")
Ensure-Dir (Join-Path $Root "projects\puremetalprints")
Ensure-Dir (Join-Path $Root "projects\layered-studios")
Ensure-Dir (Join-Path $Root "projects\mechanick")

# ---- LVCC API config ----
Write-FileIfMissing (Join-Path $Root "projects\lvcc\api\lvcc.config.json") @"
{
  "root": "$Root",
  "ops_dir": "ops/ops",
  "registry_path": "projects/projects-registry.json",
  "static_ui_dir": "../ui",
  "port": 3344
}
"@

# ---- LVCC API (Node/Express) ----
Write-FileIfMissing (Join-Path $Root "projects\lvcc\api\package.json") @"
{
  "name": "lvcc-api",
  "private": true,
  "type": "module",
  "version": "0.1.0",
  "scripts": {
    "dev": "node server.mjs",
    "start": "node server.mjs"
  },
  "dependencies": {
    "express": "^4.19.2"
  }
}
"@

Write-FileIfMissing (Join-Path $Root "projects\lvcc\api\server.mjs") @"
import fs from "node:fs";
import path from "node:path";
import express from "express";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const cfgPath = path.join(__dirname, "lvcc.config.json");
if (!fs.existsSync(cfgPath)) {
  console.error("Missing lvcc.config.json at:", cfgPath);
  process.exit(1);
}
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));

const ROOT = cfg.root;
const OPS_DIR = path.resolve(ROOT, cfg.ops_dir);
const REGISTRY_PATH = path.resolve(ROOT, cfg.registry_path);
const STATIC_UI_DIR = path.resolve(__dirname, cfg.static_ui_dir);
const PORT = cfg.port || 3344;

function safeJoinOps(rel) {
  const target = path.resolve(OPS_DIR, rel);
  if (!target.startsWith(OPS_DIR)) throw new Error("path_outside_ops");
  return target;
}

function readText(p) {
  return fs.readFileSync(p, "utf8");
}

function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter(d => d.isFile())
    .map(d => d.name)
    .sort()
    .reverse();
}

const app = express();
app.disable("x-powered-by");

app.get("/api/health", (req, res) => res.json({ ok: true }));

app.get("/api/projects", (req, res) => {
  try {
    const reg = JSON.parse(readText(REGISTRY_PATH));
    res.json(reg);
  } catch (e) {
    res.status(500).json({ error: "registry_read_failed" });
  }
});

app.get("/api/capsule", (req, res) => {
  try {
    const p = safeJoinOps("context-capsule.md");
    res.type("text/markdown").send(readText(p));
  } catch (e) {
    res.status(500).json({ error: "capsule_read_failed" });
  }
});

app.get("/api/logs", (req, res) => {
  const project = (req.query.project || "").toString();
  if (!project) return res.status(400).json({ error: "missing_project" });

  try {
    const dir = safeJoinOps(path.join("logs", project));
    const files = listFiles(dir).slice(0, 50);
    res.json({ project, files, dir: path.relative(ROOT, dir) });
  } catch (e) {
    res.status(400).json({ error: "logs_list_failed" });
  }
});

app.get("/api/events", (req, res) => {
  const project = (req.query.project || "").toString();
  if (!project) return res.status(400).json({ error: "missing_project" });

  try {
    const dir = safeJoinOps(path.join("events", project));
    const files = listFiles(dir).slice(0, 50);
    res.json({ project, files, dir: path.relative(ROOT, dir) });
  } catch (e) {
    res.status(400).json({ error: "events_list_failed" });
  }
});

// guarded file read for ops-only content (read-only)
app.get("/api/file", (req, res) => {
  const rel = (req.query.path || "").toString();
  if (!rel) return res.status(400).json({ error: "missing_path" });

  try {
    const p = safeJoinOps(rel);
    res.type("text/plain").send(readText(p));
  } catch (e) {
    res.status(400).json({ error: "file_read_failed" });
  }
});

// serve UI
app.use("/", express.static(STATIC_UI_DIR));
app.get("*", (req, res) => res.sendFile(path.join(STATIC_UI_DIR, "index.html")));

app.listen(PORT, () => {
  console.log("LVCC API running:");
  console.log("  http://localhost:" + PORT);
  console.log("OPS_DIR:", OPS_DIR);
});
"@

# ---- LVCC UI (static) ----
Write-FileIfMissing (Join-Path $Root "projects\lvcc\ui\index.html") @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>lvcc</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; }
    header { padding: 14px 18px; border-bottom: 1px solid #ddd; display:flex; gap:12px; align-items:center; }
    main { padding: 18px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 14px; }
    pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; }
    select, button { padding: 8px 10px; border-radius: 10px; border: 1px solid #bbb; background: #fff; }
    ul { margin: 10px 0 0 18px; }
    a { color: inherit; }
    @media (max-width: 980px) { main { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <strong>lvcc</strong>
    <span style="opacity:.7">local-first command center</span>
    <span style="flex:1"></span>

    <label style="opacity:.8">project</label>
    <select id="project"></select>
    <button id="refresh">refresh</button>
  </header>

  <main>
    <section class="card">
      <h3 style="margin:0 0 10px 0;">context-capsule.md</h3>
      <pre id="capsule">(loading...)</pre>
    </section>

    <section class="card">
      <h3 style="margin:0 0 10px 0;">recent logs</h3>
      <div id="logs">(loading...)</div>
      <h3 style="margin:16px 0 10px 0;">recent events</h3>
      <div id="events">(loading...)</div>
    </section>

    <section class="card">
      <h3 style="margin:0 0 10px 0;">file viewer (ops-only)</h3>
      <div style="display:flex; gap:8px; align-items:center;">
        <input id="filepath" style="flex:1; padding:8px 10px; border-radius:10px; border:1px solid #bbb" placeholder="e.g. logs/lvcc/2026-02-28.md"/>
        <button id="openfile">open</button>
      </div>
      <pre id="filecontent" style="margin-top:12px; max-height: 360px; overflow:auto;"></pre>
    </section>

    <section class="card">
      <h3 style="margin:0 0 10px 0;">projects registry</h3>
      <pre id="registry" style="max-height: 360px; overflow:auto;"></pre>
    </section>
  </main>

  <script type="module" src="./main.js"></script>
</body>
</html>
"@

Write-FileIfMissing (Join-Path $Root "projects\lvcc\ui\main.js") @"
async function getText(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + " " + r.status);
  return await r.text();
}
async function getJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + " " + r.status);
  return await r.json();
}
function el(id){ return document.getElementById(id); }

async function loadRegistry() {
  const reg = await getJson("/api/projects");
  el("registry").textContent = JSON.stringify(reg, null, 2);

  const select = el("project");
  select.innerHTML = "";
  for (const p of reg.projects || []) {
    if (p.enabled === false) continue;
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.id;
    select.appendChild(opt);
  }
  if (!select.value && select.options.length) select.value = select.options[0].value;
}

async function loadCapsule() {
  el("capsule").textContent = await getText("/api/capsule");
}

function renderFileList(container, title, project, files, kind) {
  const div = document.createElement("div");
  const ul = document.createElement("ul");
  for (const f of files) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = "#";
    a.textContent = f;
    a.onclick = async (e) => {
      e.preventDefault();
      el("filepath").value = kind + "/" + project + "/" + f;
      el("openfile").click();
    };
    li.appendChild(a);
    ul.appendChild(li);
  }
  div.appendChild(ul);
  container.innerHTML = "";
  container.appendChild(div);
}

async function loadLists() {
  const project = el("project").value;

  const logs = await getJson("/api/logs?project=" + encodeURIComponent(project));
  renderFileList(el("logs"), "logs", project, logs.files || [], "logs");

  const events = await getJson("/api/events?project=" + encodeURIComponent(project));
  renderFileList(el("events"), "events", project, events.files || [], "events");
}

async function openFile() {
  const rel = el("filepath").value.trim();
  if (!rel) return;
  el("filecontent").textContent = "(loading...)";
  try {
    const txt = await getText("/api/file?path=" + encodeURIComponent(rel));
    el("filecontent").textContent = txt;
  } catch (e) {
    el("filecontent").textContent = "error: " + e.message;
  }
}

async function main() {
  await loadRegistry();
  await loadCapsule();
  await loadLists();

  el("refresh").onclick = async () => {
    await loadRegistry();
    await loadCapsule();
    await loadLists();
  };
  el("project").onchange = loadLists;
  el("openfile").onclick = openFile;
}

main().catch(e => {
  console.error(e);
  alert("LVCC failed: " + e.message);
});
"@

# ---- helper: lv_project.ps1 (registry management) ----
Write-FileIfMissing (Join-Path $newOps "tools\lv_project.ps1") @"
param(
  [Parameter(Mandatory=\$true)]
  [ValidateSet('list','add','remove','enable','disable')]
  [string]\$Cmd,

  [string]\$Id,
  [string]\$Path,
  [ValidateSet('internal','business','client')]
  [string]\$Type = 'business',

  [string]\$Root = '$Root'
)

\$ErrorActionPreference = 'Stop'
\$regPath = Join-Path \$Root 'projects\projects-registry.json'
if (!(Test-Path \$regPath)) { throw \"missing registry: \$regPath\" }

\$reg = Get-Content \$regPath -Raw | ConvertFrom-Json

function Save-Reg(\$obj) {
  (\$obj | ConvertTo-Json -Depth 20) | Set-Content -Encoding UTF8 \$regPath
}

switch(\$Cmd) {
  'list' {
    \$reg.projects | Sort-Object id | Format-Table id,type,enabled,path -AutoSize
  }
  'add' {
    if (!\$Id -or !\$Path) { throw 'add requires -Id and -Path' }
    if (\$reg.projects | Where-Object { \$_.id -eq \$Id }) { throw \"project exists: \$Id\" }
    \$reg.projects += [pscustomobject]@{ id=\$Id; path=\$Path; type=\$Type; enabled=\$true }
    Save-Reg \$reg
    Write-Host \"added: \$Id\" -ForegroundColor Green
  }
  'remove' {
    if (!\$Id) { throw 'remove requires -Id' }
    \$reg.projects = @(\$reg.projects | Where-Object { \$_.id -ne \$Id })
    Save-Reg \$reg
    Write-Host \"removed: \$Id\" -ForegroundColor Yellow
  }
  'enable' {
    if (!\$Id) { throw 'enable requires -Id' }
    foreach(\$p in \$reg.projects){ if(\$p.id -eq \$Id){ \$p.enabled = \$true } }
    Save-Reg \$reg
    Write-Host \"enabled: \$Id\" -ForegroundColor Green
  }
  'disable' {
    if (!\$Id) { throw 'disable requires -Id' }
    foreach(\$p in \$reg.projects){ if(\$p.id -eq \$Id){ \$p.enabled = \$false } }
    Save-Reg \$reg
    Write-Host \"disabled: \$Id\" -ForegroundColor Yellow
  }
}
"@

# ---- root readme ----
Write-FileIfMissing (Join-Path $Root "readme.md") @"
# layered_ventures

Scalable multi-repo workspace layout:

- ops/        operational brain (doctrine, tools, capsule, logs, events)
- contracts/  shared contracts (optional repo)
- projects/   each business/tool is its own repo folder
- projects/projects-registry.json is the discovery source for LVCC

To run LVCC locally:
- cd projects/lvcc/api
- npm install
- npm run dev
"@

# ---- init git (optional) ----
if ($InitGit) {
  if (!(Test-Path (Join-Path $Root ".git"))) {
    Push-Location $Root
    git init | Out-Null
    Pop-Location
  }
}

Write-Host ""
Write-Host "DONE: bootstrapped layered_ventures at:" -ForegroundColor Green
Write-Host "  $Root" -ForegroundColor Green
Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  1) cd $Root\projects\lvcc\api" -ForegroundColor Cyan
Write-Host "  2) npm install" -ForegroundColor Cyan
Write-Host "  3) npm run dev" -ForegroundColor Cyan
Write-Host "  4) open http://localhost:3344" -ForegroundColor Cyan
