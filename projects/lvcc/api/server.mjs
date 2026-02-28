import fs from "node:fs";
import path from "node:path";
import express from "express";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readText(p) {
  const s = fs.readFileSync(p, "utf8");
  return s.replace(/^\uFEFF/, "");
}

const cfgPath = path.join(__dirname, "lvcc.config.json");
if (!fs.existsSync(cfgPath)) {
  console.error("Missing lvcc.config.json at:", cfgPath);
  process.exit(1);
}

let cfg;
try {
  cfg = JSON.parse(readText(cfgPath));
} catch (e) {
  console.error("Failed to parse lvcc.config.json:", e?.message || e);
  process.exit(1);
}

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

function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((d) => d.isFile())
    .map((d) => d.name)
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

app.use("/", express.static(STATIC_UI_DIR));
app.get("*", (req, res) => res.sendFile(path.join(STATIC_UI_DIR, "index.html")));

app.listen(PORT, () => {
  console.log("LVCC API running:");
  console.log("  http://localhost:" + PORT);
  console.log("OPS_DIR:", OPS_DIR);
});